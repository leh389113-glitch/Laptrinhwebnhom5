from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def sinh_ma_de_nghi() -> str:
    """Sinh mã đề nghị mua sắm tự động theo dạng DN-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"DN-{ngay_str}-"

    row = db.execute(
        "SELECT ma_de_nghi FROM de_nghi_mua_sam WHERE ma_de_nghi LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_de_nghi"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def tao_de_nghi(du_lieu: dict, nguoi_de_nghi_id: int) -> dict:
    """Tạo mới một đề nghị mua sắm kèm các hạng mục hàng hóa."""
    db = get_db()
    ma_de_nghi = sinh_ma_de_nghi()
    ngay_hien_tai = clock.now().isoformat()

    items = du_lieu.get("items", [])
    tong_du_toan = du_lieu.get("tong_du_toan")
    if tong_du_toan is None:
        tong_du_toan = sum(float(it.get("thanh_tien", it.get("so_luong", 0) * it.get("don_gia_du_kien", 0))) for it in items)

    cursor = db.execute(
        """
        INSERT INTO de_nghi_mua_sam (
            ma_de_nghi, tieu_de, mo_ta, don_vi_de_nghi,
            nguoi_de_nghi_id, tong_du_toan, trang_thai,
            ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, ?, 'cho_phe_duyet', ?, ?)
        """,
        (
            ma_de_nghi,
            du_lieu["tieu_de"],
            du_lieu.get("mo_ta", ""),
            du_lieu["don_vi_de_nghi"],
            nguoi_de_nghi_id,
            tong_du_toan,
            ngay_hien_tai,
            ngay_hien_tai
        )
    )
    de_nghi_id = cursor.lastrowid

    for item in items:
        so_luong = int(item.get("so_luong", 1))
        don_gia = float(item.get("don_gia_du_kien", 0))
        thanh_tien = float(item.get("thanh_tien", so_luong * don_gia))
        db.execute(
            """
            INSERT INTO chi_tiet_de_nghi (
                de_nghi_id, ten_hang_hoa, don_vi_tinh,
                so_luong, don_gia_du_kien, thanh_tien, ghi_chu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                de_nghi_id,
                item["ten_hang_hoa"],
                item.get("don_vi_tinh", "Bộ"),
                so_luong,
                don_gia,
                thanh_tien,
                item.get("ghi_chu", "")
            )
        )

    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def lay_danh_sach_de_nghi(trang_thai: str = None) -> list:
    """Lấy danh sách đề nghị mua sắm, có thể lọc theo trạng thái."""
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
    """
    params = []
    if trang_thai:
        query += " WHERE d.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_de_nghi(de_nghi_id: int) -> dict:
    """Lấy thông tin chi tiết một đề nghị mua sắm bao gồm các hạng mục và hồ sơ liên quan."""
    db = get_db()
    row = db.execute(
        """
        SELECT d.*,
               u1.ho_ten AS nguoi_de_nghi_ten,
               u2.ho_ten AS nguoi_phe_duyet_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u1 ON d.nguoi_de_nghi_id = u1.id
        LEFT JOIN nguoi_dung u2 ON d.nguoi_phe_duyet_id = u2.id
        WHERE d.id = ?
        """,
        (de_nghi_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    de_nghi = dict(row)

    items = db.execute(
        "SELECT * FROM chi_tiet_de_nghi WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchall()
    de_nghi["items"] = [dict(it) for it in items]

    ho_so = db.execute(
        "SELECT * FROM ho_so_mua_sam WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchall()
    de_nghi["ho_so"] = [dict(hs) for hs in ho_so]

    tiep_nhan = db.execute(
        """
        SELECT tn.*, u.ho_ten AS nguoi_tiep_nhan_ten
        FROM tiep_nhan_hang tn
        LEFT JOIN nguoi_dung u ON tn.nguoi_tiep_nhan_id = u.id
        WHERE tn.de_nghi_id = ?
        """,
        (de_nghi_id,)
    ).fetchall()
    de_nghi["tiep_nhan"] = [dict(tn) for tn in tiep_nhan]

    thanh_toan = db.execute(
        """
        SELECT tt.*, u.ho_ten AS nguoi_thanh_toan_ten
        FROM thanh_toan tt
        LEFT JOIN nguoi_dung u ON tt.nguoi_thanh_toan_id = u.id
        WHERE tt.de_nghi_id = ?
        """,
        (de_nghi_id,)
    ).fetchall()
    de_nghi["thanh_toan"] = [dict(tt) for tt in thanh_toan]

    return de_nghi

def phe_duyet_de_nghi(de_nghi_id: int, nguoi_phe_duyet_id: int, ghi_chu: str = "") -> dict:
    """Phê duyệt đề nghị mua sắm (Admin/Lãnh đạo)."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] != "cho_phe_duyet":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể phê duyệt đề nghị đang chờ phê duyệt.")

    thoi_gian = clock.now().isoformat()
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET trang_thai = 'da_phe_duyet',
            nguoi_phe_duyet_id = ?,
            ghi_chu_phe_duyet = ?,
            ngay_phe_duyet = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_phe_duyet_id, ghi_chu, thoi_gian, thoi_gian, de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tu_choi_de_nghi(de_nghi_id: int, nguoi_phe_duyet_id: int, ghi_chu: str = "") -> dict:
    """Từ chối đề nghị mua sắm (Admin/Lãnh đạo)."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] != "cho_phe_duyet":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể từ chối đề nghị đang chờ phê duyệt.")

    thoi_gian = clock.now().isoformat()
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET trang_thai = 'tu_choi',
            nguoi_phe_duyet_id = ?,
            ghi_chu_phe_duyet = ?,
            ngay_phe_duyet = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_phe_duyet_id, ghi_chu, thoi_gian, thoi_gian, de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tao_ho_so_mua_sam(de_nghi_id: int, nha_cung_cap: str, so_hop_dong: str, gia_tri: float, ghi_chu: str = "") -> dict:
    """Tạo hồ sơ mua sắm cho đề nghị đã được duyệt."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    ngay_tao = clock.now().isoformat()
    cursor = db.execute(
        """
        INSERT INTO ho_so_mua_sam (de_nghi_id, nha_cung_cap, so_hop_dong, gia_tri_hop_dong, ngay_tao, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (de_nghi_id, nha_cung_cap, so_hop_dong, gia_tri, ngay_tao, ghi_chu)
    )
    # Cập nhật trạng thái sang 'dang_mua' nếu đang là 'da_phe_duyet'
    if row["trang_thai"] == "da_phe_duyet":
        db.execute(
            "UPDATE de_nghi_mua_sam SET trang_thai = 'dang_mua', ngay_cap_nhat = ? WHERE id = ?",
            (ngay_tao, de_nghi_id)
        )
    db.commit()
    return {"id": cursor.lastrowid, "de_nghi_id": de_nghi_id}

def tiep_nhan_hang_hoa(de_nghi_id: int, du_lieu: dict, nguoi_tiep_nhan_id: int) -> dict:
    """
    Ghi nhận tiếp nhận hàng hóa từ đề nghị mua sắm.
    Quy tắc tích hợp: Tự động chuyển đề nghị sang 'da_nhan' và tạo các bản ghi tài sản mới trong M09!
    """
    db = get_db()
    row = db.execute("SELECT * FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] not in ["da_phe_duyet", "dang_mua"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể tiếp nhận hàng cho đề nghị đã phê duyệt hoặc đang mua.")

    ngay_hien_tai = clock.now().isoformat()

    # Tạo bản ghi tiếp nhận hàng
    cursor = db.execute(
        """
        INSERT INTO tiep_nhan_hang (de_nghi_id, ngay_tiep_nhan, nguoi_tiep_nhan_id, ghi_chu)
        VALUES (?, ?, ?, ?)
        """,
        (de_nghi_id, ngay_hien_tai, nguoi_tiep_nhan_id, du_lieu.get("ghi_chu", ""))
    )
    tiep_nhan_id = cursor.lastrowid

    # Lấy danh sách hàng hóa của đề nghị
    hang_hoa_rows = db.execute("SELECT * FROM chi_tiet_de_nghi WHERE de_nghi_id = ?", (de_nghi_id,)).fetchall()

    from app.services import tai_san as tai_san_svc

    # Ghi chi tiết tiếp nhận và tự động tạo tài sản trong kho (M09)
    for hang in hang_hoa_rows:
        so_luong_nhan = hang["so_luong"]
        db.execute(
            """
            INSERT INTO chi_tiet_tiep_nhan (tiep_nhan_id, ten_hang_hoa, so_luong_thuc_nhan, don_vi_tinh, tinh_trang, ghi_chu)
            VALUES (?, ?, ?, ?, 'tot', ?)
            """,
            (tiep_nhan_id, hang["ten_hang_hoa"], so_luong_nhan, hang["don_vi_tinh"], "Tiếp nhận từ đề nghị " + row["ma_de_nghi"])
        )

        # Tạo từng tài sản hoặc lô tài sản vào M09
        for i in range(so_luong_nhan):
            ma_tai_san = tai_san_svc.sinh_ma_tai_san()
            db.execute(
                """
                INSERT INTO tai_san (
                    ma_tai_san, ten_tai_san, mo_ta, loai_tai_san,
                    vi_tri, phong_ban, gia_tri, ngay_tiep_nhan,
                    trang_thai, de_nghi_id, ngay_tao, ngay_cap_nhat
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'cho_ban_giao', ?, ?, ?)
                """,
                (
                    ma_tai_san,
                    hang["ten_hang_hoa"],
                    f"Mua theo đề nghị {row['ma_de_nghi']}",
                    "Thiết bị cơ sở vật chất",
                    "Kho trung tâm",
                    row["don_vi_de_nghi"],
                    hang["don_gia_du_kien"],
                    ngay_hien_tai,
                    de_nghi_id,
                    ngay_hien_tai,
                    ngay_hien_tai
                )
            )

    # Chuyển trạng thái đề nghị sang 'da_nhan'
    db.execute(
        "UPDATE de_nghi_mua_sam SET trang_thai = 'da_nhan', ngay_cap_nhat = ? WHERE id = ?",
        (ngay_hien_tai, de_nghi_id)
    )
    db.commit()

    return lay_chi_tiet_de_nghi(de_nghi_id)

def lay_danh_sach_ho_so() -> list:
    """Lấy danh sách các hồ sơ mua sắm."""
    db = get_db()
    rows = db.execute(
        """
        SELECT hs.*, d.ma_de_nghi, d.tieu_de, d.don_vi_de_nghi
        FROM ho_so_mua_sam hs
        JOIN de_nghi_mua_sam d ON hs.de_nghi_id = d.id
        ORDER BY hs.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]
