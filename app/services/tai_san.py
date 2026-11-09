from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def sinh_ma_tai_san(phan_loai: str = "tai_san_co_dinh") -> str:
    """
    Sinh mã định danh tài sản tự động:
    - Tài sản cố định (>= 10 triệu): TS-YYYY-XXXX
    - Công cụ dụng cụ (< 10 triệu): CCDC-YYYY-XXXX
    """
    db = get_db()
    nam_str = clock.now().strftime("%Y")
    prefix = f"TS-{nam_str}-" if phan_loai == "tai_san_co_dinh" else f"CCDC-{nam_str}-"

    row = db.execute(
        "SELECT ma_tai_san FROM tai_san WHERE ma_tai_san LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_tai_san"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:04d}"

def sinh_ma_phieu_kiem_ke() -> str:
    """Sinh mã phiếu kiểm kê tự động KK-YYYY-XXXX."""
    db = get_db()
    nam_str = clock.now().strftime("%Y")
    prefix = f"KK-{nam_str}-"

    row = db.execute(
        "SELECT ma_phieu FROM phieu_kiem_ke WHERE ma_phieu LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_phieu"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:04d}"

def sinh_ma_yeu_cau_sua_chua() -> str:
    """Sinh mã yêu cầu sửa chữa tự động SC-YYYY-XXXX."""
    db = get_db()
    nam_str = clock.now().strftime("%Y")
    prefix = f"SC-{nam_str}-"

    row = db.execute(
        "SELECT ma_yeu_cau FROM yeu_cau_sua_chua WHERE ma_yeu_cau LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_yeu_cau"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:04d}"

def tao_tai_san_thu_cong(du_lieu: dict) -> dict:
    """Tạo mới một tài sản thủ công vào kho M09."""
    db = get_db()
    phan_loai = du_lieu.get("phan_loai") or ("tai_san_co_dinh" if float(du_lieu.get("gia_tri", 0)) >= 10_000_000 else "cong_cu_dung_cu")
    ma_tai_san = sinh_ma_tai_san(phan_loai=phan_loai)
    ngay_hien_tai = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO tai_san (
            ma_tai_san, ten_tai_san, mo_ta, loai_tai_san,
            phan_loai, tinh_trang_ky_thuat, vi_tri, phong_ban,
            don_vi_su_dung, gia_tri, ngay_tiep_nhan,
            so_serial, model, hang_san_xuat, thoi_han_bao_hanh,
            trang_thai, ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'cho_ban_giao', ?, ?)
        """,
        (
            ma_tai_san,
            du_lieu["ten_tai_san"],
            du_lieu.get("mo_ta", ""),
            du_lieu.get("loai_tai_san", "Cơ sở vật chất"),
            phan_loai,
            du_lieu.get("tinh_trang_ky_thuat", "binh_thuong"),
            du_lieu.get("vi_tri", "Kho"),
            du_lieu.get("phong_ban", ""),
            du_lieu.get("don_vi_su_dung") or du_lieu.get("phong_ban", ""),
            du_lieu.get("gia_tri", 0),
            ngay_hien_tai,
            du_lieu.get("so_serial", ""),
            du_lieu.get("model", ""),
            du_lieu.get("hang_san_xuat", ""),
            du_lieu.get("thoi_han_bao_hanh", ""),
            ngay_hien_tai,
            ngay_hien_tai
        )
    )
    db.commit()
    return lay_chi_tiet_tai_san(cursor.lastrowid)

def lay_danh_sach_tai_san(trang_thai: str = None, tu_khoa: str = None, phan_loai: str = None, tinh_trang_ky_thuat: str = None) -> list:
    """Lấy danh sách tất cả tài sản trong hệ thống với các bộ lọc."""
    db = get_db()
    query = """
        SELECT t.*, u.ho_ten AS nguoi_su_dung_ten
        FROM tai_san t
        LEFT JOIN nguoi_dung u ON t.nguoi_su_dung_id = u.id
        WHERE 1=1
    """
    params = []
    if trang_thai:
        query += " AND t.trang_thai = ?"
        params.append(trang_thai)

    if phan_loai:
        query += " AND t.phan_loai = ?"
        params.append(phan_loai)

    if tinh_trang_ky_thuat:
        query += " AND t.tinh_trang_ky_thuat = ?"
        params.append(tinh_trang_ky_thuat)

    if tu_khoa:
        query += " AND (t.ma_tai_san LIKE ? OR t.ten_tai_san LIKE ? OR t.vi_tri LIKE ? OR t.phong_ban LIKE ?)"
        like_str = f"%{tu_khoa}%"
        params.extend([like_str, like_str, like_str, like_str])

    query += " ORDER BY t.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_tai_san_cua_toi(nguoi_dung_id: int) -> list:
    """Lấy danh sách tài sản đang được bàn giao cho người dùng này sử dụng."""
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM tai_san
        WHERE nguoi_su_dung_id = ?
        ORDER BY id DESC
        """,
        (nguoi_dung_id,)
    ).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_tai_san(tai_san_id: int) -> dict:
    """Lấy thông tin chi tiết tài sản kèm lịch sử bàn giao và bảo trì."""
    db = get_db()
    row = db.execute(
        """
        SELECT t.*, u.ho_ten AS nguoi_su_dung_ten, d.ma_de_nghi
        FROM tai_san t
        LEFT JOIN nguoi_dung u ON t.nguoi_su_dung_id = u.id
        LEFT JOIN de_nghi_mua_sam d ON t.de_nghi_id = d.id
        WHERE t.id = ?
        """,
        (tai_san_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    tai_san = dict(row)

    ban_giao = db.execute(
        """
        SELECT bg.*,
               un.ho_ten AS nguoi_nhan_ten,
               ubg.ho_ten AS nguoi_ban_giao_ten
        FROM lich_su_ban_giao bg
        LEFT JOIN nguoi_dung un ON bg.nguoi_nhan_id = un.id
        LEFT JOIN nguoi_dung ubg ON bg.nguoi_ban_giao_id = ubg.id
        WHERE bg.tai_san_id = ?
        ORDER BY bg.id DESC
        """,
        (tai_san_id,)
    ).fetchall()
    tai_san["lich_su_ban_giao"] = [dict(bg) for bg in ban_giao]

    bao_tri = db.execute(
        """
        SELECT bt.*, u.ho_ten AS nguoi_ghi_nhan_ten
        FROM bao_tri bt
        LEFT JOIN nguoi_dung u ON bt.nguoi_ghi_nhan_id = u.id
        WHERE bt.tai_san_id = ?
        ORDER BY bt.id DESC
        """,
        (tai_san_id,)
    ).fetchall()
    tai_san["lich_su_bao_tri"] = [dict(bt) for bt in bao_tri]

    return tai_san

def cap_nhat_tai_san(tai_san_id: int, du_lieu: dict) -> dict:
    """Cập nhật thông tin tài sản."""
    db = get_db()
    row = db.execute("SELECT id FROM tai_san WHERE id = ?", (tai_san_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    ngay_cap_nhat = clock.now().isoformat()
    db.execute(
        """
        UPDATE tai_san
        SET ten_tai_san = ?,
            mo_ta = ?,
            loai_tai_san = ?,
            phan_loai = ?,
            tinh_trang_ky_thuat = ?,
            vi_tri = ?,
            phong_ban = ?,
            don_vi_su_dung = ?,
            gia_tri = ?,
            so_serial = ?,
            model = ?,
            hang_san_xuat = ?,
            thoi_han_bao_hanh = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (
            du_lieu["ten_tai_san"],
            du_lieu.get("mo_ta", ""),
            du_lieu.get("loai_tai_san", ""),
            du_lieu.get("phan_loai", "tai_san_co_dinh"),
            du_lieu.get("tinh_trang_ky_thuat", "binh_thuong"),
            du_lieu.get("vi_tri", ""),
            du_lieu.get("phong_ban", ""),
            du_lieu.get("don_vi_su_dung", ""),
            du_lieu.get("gia_tri", 0),
            du_lieu.get("so_serial", ""),
            du_lieu.get("model", ""),
            du_lieu.get("hang_san_xuat", ""),
            du_lieu.get("thoi_han_bao_hanh", ""),
            ngay_cap_nhat,
            tai_san_id
        )
    )
    db.commit()
    return lay_chi_tiet_tai_san(tai_san_id)

def ban_giao_tai_san(tai_san_id: int, nguoi_nhan_id: int, nguoi_ban_giao_id: int, ghi_chu: str = "") -> dict:
    """Bàn giao tài sản cho người dùng / phòng ban sử dụng."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM tai_san WHERE id = ?", (tai_san_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    nguoi_nhan = db.execute("SELECT id, ho_ten FROM nguoi_dung WHERE id = ?", (nguoi_nhan_id,)).fetchone()
    if not nguoi_nhan:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Người nhận bàn giao không tồn tại.")

    ngay_ban_giao = clock.now().isoformat()

    db.execute(
        """
        INSERT INTO lich_su_ban_giao (tai_san_id, nguoi_nhan_id, nguoi_ban_giao_id, ngay_ban_giao, ghi_chu)
        VALUES (?, ?, ?, ?, ?)
        """,
        (tai_san_id, nguoi_nhan_id, nguoi_ban_giao_id, ngay_ban_giao, ghi_chu)
    )

    db.execute(
        """
        UPDATE tai_san
        SET nguoi_su_dung_id = ?,
            trang_thai = 'dang_su_dung',
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_nhan_id, ngay_ban_giao, tai_san_id)
    )
    db.commit()
    return lay_chi_tiet_tai_san(tai_san_id)

def ghi_nhan_bao_tri(tai_san_id: int, du_lieu: dict, nguoi_ghi_nhan_id: int) -> dict:
    """Ghi nhận lịch sử bảo trì, sửa chữa tài sản."""
    db = get_db()
    row = db.execute("SELECT id FROM tai_san WHERE id = ?", (tai_san_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    ngay_hien_tai = clock.now().isoformat()

    db.execute(
        """
        INSERT INTO bao_tri (tai_san_id, ngay_bao_tri, noi_dung, chi_phi, don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tai_san_id,
            ngay_hien_tai,
            du_lieu["noi_dung"],
            du_lieu.get("chi_phi", 0),
            du_lieu.get("don_vi_thuc_hien", ""),
            nguoi_ghi_nhan_id,
            du_lieu.get("ghi_chu", "")
        )
    )

    trang_thai_moi = du_lieu.get("trang_thai_moi")
    if trang_thai_moi:
        db.execute(
            "UPDATE tai_san SET trang_thai = ?, ngay_cap_nhat = ? WHERE id = ?",
            (trang_thai_moi, ngay_hien_tai, tai_san_id)
        )

    db.commit()
    return lay_chi_tiet_tai_san(tai_san_id)

# =========================================================================
# QUY TRÌNH SỬA CHỮA M09 (PHẦN III CỦA QUY TRÌNH & YÊU CẦU 1)
# =========================================================================

def tao_yeu_cau_sua_chua(du_lieu: dict, nguoi_tao_id: int) -> dict:
    """Tạo phiếu yêu cầu sửa chữa tại M09."""
    db = get_db()
    ma_yeu_cau = sinh_ma_yeu_cau_sua_chua()
    ngay_hien_tai = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO yeu_cau_sua_chua (
            ma_yeu_cau, tai_san_id, bao_cao_hu_hai_id, loai_sua_chua,
            noi_dung, hien_trang, chi_phi_du_kien, don_vi_thuc_hien,
            nguoi_phu_trach_id, ngay_tiep_nhan, trang_thai, ghi_chu
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'dang_sua_chua', ?)
        """,
        (
            ma_yeu_cau,
            du_lieu.get("tai_san_id"),
            du_lieu.get("bao_cao_hu_hai_id"),
            du_lieu.get("loai_sua_chua", "sua_chua_nho"),
            du_lieu["noi_dung"],
            du_lieu.get("hien_trang", ""),
            du_lieu.get("chi_phi_du_kien", 0),
            du_lieu.get("don_vi_thuc_hien", "Tổ kỹ thuật QTTB"),
            nguoi_tao_id,
            ngay_hien_tai,
            du_lieu.get("ghi_chu", "")
        )
    )
    yeu_cau_id = cursor.lastrowid

    # Cập nhật trạng thái tài sản nếu có
    if du_lieu.get("tai_san_id"):
        db.execute(
            """
            UPDATE tai_san
            SET trang_thai = 'dang_sua_chua',
                tinh_trang_ky_thuat = 'co_hu_hong',
                ngay_cap_nhat = ?
            WHERE id = ?
            """,
            (ngay_hien_tai, du_lieu["tai_san_id"])
        )

    # Cập nhật trạng thái báo cáo sự cố nếu có
    if du_lieu.get("bao_cao_hu_hai_id"):
        db.execute(
            """
            UPDATE bao_cao_hu_hai
            SET trang_thai = 'dang_sua_chua',
                phuong_an_xu_ly = 'sua_chua',
                nguoi_xu_ly_id = ?,
                ngay_xu_ly = ?
            WHERE id = ?
            """,
            (nguoi_tao_id, ngay_hien_tai, du_lieu["bao_cao_hu_hai_id"])
        )

    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def lay_danh_sach_sua_chua(trang_thai: str = None) -> list:
    """Lấy danh sách các yêu cầu sửa chữa tại M09."""
    db = get_db()
    query = """
        SELECT sc.*, ts.ma_tai_san, ts.ten_tai_san, u.ho_ten AS nguoi_phu_trach_ten
        FROM yeu_cau_sua_chua sc
        LEFT JOIN tai_san ts ON sc.tai_san_id = ts.id
        LEFT JOIN nguoi_dung u ON sc.nguoi_phu_trach_id = u.id
        WHERE 1=1
    """
    params = []
    if trang_thai:
        query += " AND sc.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY sc.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_sua_chua(yeu_cau_id: int) -> dict:
    """Lấy thông tin chi tiết một yêu cầu sửa chữa."""
    db = get_db()
    row = db.execute(
        """
        SELECT sc.*, ts.ma_tai_san, ts.ten_tai_san, ts.vi_tri AS tai_san_vi_tri,
               u.ho_ten AS nguoi_phu_trach_ten,
               hh.ho_ten AS nguoi_bao_cao_ten, hh.vi_tri AS vi_tri_su_co
        FROM yeu_cau_sua_chua sc
        LEFT JOIN tai_san ts ON sc.tai_san_id = ts.id
        LEFT JOIN nguoi_dung u ON sc.nguoi_phu_trach_id = u.id
        LEFT JOIN bao_cao_hu_hai hh ON sc.bao_cao_hu_hai_id = hh.id
        WHERE sc.id = ?
        """,
        (yeu_cau_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu sửa chữa không tồn tại.")
    return dict(row)

def nghiem_thu_sua_chua(yeu_cau_id: int, du_lieu: dict, nguoi_nghiem_thu_id: int) -> dict:
    """Nghiệm thu hoàn tất sửa chữa M09, ghi lịch sử bảo trì và đưa tài sản về trạng thái hoạt động."""
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    ngay_hien_tai = clock.now().isoformat()
    chi_phi_thuc_te = float(du_lieu.get("chi_phi_thuc_te", sc["chi_phi_du_kien"] or 0))

    db.execute(
        """
        UPDATE yeu_cau_sua_chua
        SET chi_phi_thuc_te = ?,
            ket_qua_nghiem_thu = 'dat',
            trang_thai = 'da_hoan_thanh',
            ngay_hoan_thanh = ?,
            ghi_chu = ?
        WHERE id = ?
        """,
        (chi_phi_thuc_te, ngay_hien_tai, du_lieu.get("ghi_chu", ""), yeu_cau_id)
    )

    # Cập nhật tài sản và ghi vào lịch sử bảo trì
    if sc["tai_san_id"]:
        db.execute(
            """
            INSERT INTO bao_tri (tai_san_id, ngay_bao_tri, noi_dung, chi_phi, don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sc["tai_san_id"],
                ngay_hien_tai,
                sc["noi_dung"],
                chi_phi_thuc_te,
                sc["don_vi_thuc_hien"] or "Tổ kỹ thuật QTTB",
                nguoi_nghiem_thu_id,
                f"Nghiệm thu yêu cầu {sc['ma_yeu_cau']}: Đạt"
            )
        )
        db.execute(
            """
            UPDATE tai_san
            SET trang_thai = 'dang_su_dung',
                tinh_trang_ky_thuat = 'binh_thuong',
                ngay_cap_nhat = ?
            WHERE id = ?
            """,
            (ngay_hien_tai, sc["tai_san_id"])
        )

    # Nếu có báo cáo hư hại gắn kèm, chuyển báo cáo sang đã xử lý
    if sc["bao_cao_hu_hai_id"]:
        db.execute(
            """
            UPDATE bao_cao_hu_hai
            SET trang_thai = 'da_xu_ly',
                nguoi_xu_ly_id = ?,
                ngay_xu_ly = ?,
                ghi_chu_xu_ly = ?
            WHERE id = ?
            """,
            (nguoi_nghiem_thu_id, ngay_hien_tai, f"Đã hoàn thành sửa chữa mã {sc['ma_yeu_cau']}", sc["bao_cao_hu_hai_id"])
        )

    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

# =========================================================================
# KIỂM KÊ TÀI SẢN
# =========================================================================

def tao_phieu_kiem_ke(du_lieu: dict, nguoi_kiem_ke_id: int) -> dict:
    """Tạo phiếu kiểm kê và đối chiếu số lượng thực tế vs hệ thống."""
    db = get_db()
    ma_phieu = sinh_ma_phieu_kiem_ke()
    ngay_hien_tai = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO phieu_kiem_ke (ma_phieu, ngay_kiem_ke, nguoi_kiem_ke_id, trang_thai, ghi_chu, ngay_tao)
        VALUES (?, ?, ?, 'hoan_thanh', ?, ?)
        """,
        (ma_phieu, ngay_hien_tai, nguoi_kiem_ke_id, du_lieu.get("ghi_chu", ""), ngay_hien_tai)
    )
    phieu_id = cursor.lastrowid

    for item in du_lieu.get("chi_tiet", []):
        so_luong_he_thong = int(item.get("so_luong_he_thong", 1))
        so_luong_thuc_te = int(item.get("so_luong_thuc_te", 1))
        chenh_lech = so_luong_thuc_te - so_luong_he_thong

        db.execute(
            """
            INSERT INTO chi_tiet_kiem_ke (
                phieu_kiem_ke_id, tai_san_id, tinh_trang_thuc_te,
                so_luong_he_thong, so_luong_thuc_te, chenh_lech, ghi_chu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                phieu_id,
                item["tai_san_id"],
                item.get("tinh_trang", "tot"),
                so_luong_he_thong,
                so_luong_thuc_te,
                chenh_lech,
                item.get("ghi_chu", "")
            )
        )

    db.commit()
    return {"id": phieu_id, "ma_phieu": ma_phieu}

def lay_danh_sach_kiem_ke() -> list:
    """Lấy danh sách các đợt kiểm kê tài sản."""
    db = get_db()
    rows = db.execute(
        """
        SELECT kk.*, u.ho_ten AS nguoi_kiem_ke_ten
        FROM phieu_kiem_ke kk
        LEFT JOIN nguoi_dung u ON kk.nguoi_kiem_ke_id = u.id
        ORDER BY kk.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]

def lay_danh_sach_de_nghi_cho_tiep_nhan(trang_thai: str = None) -> list:
    """
    Lấy danh sách các gói mua sắm đã có Biên bản nghiệm thu kỹ thuật (BM04) ĐẠT YÊU CẦU,
    đủ điều kiện để Bộ phận Quản lý tài sản kiểm tra và tiếp nhận nhập kho M09.
    """
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten,
               nt.id AS nghiem_thu_id,
               nt.ma_nghiem_thu,
               nt.ngay_nghiem_thu,
               nt.ket_qua AS ket_qua_nghiem_thu,
               nt.y_kien_danh_gia AS y_kien_nghiem_thu,
               nt.dai_dien_ben_mua,
               nt.dai_dien_nha_cung_cap,
               nt.dai_dien_don_vi_su_dung
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        INNER JOIN nghiem_thu_mua_sam nt
            ON nt.de_nghi_id = d.id
           AND nt.id = (
               SELECT MAX(nt_moi.id)
               FROM nghiem_thu_mua_sam nt_moi
               WHERE nt_moi.de_nghi_id = d.id
           )
           AND nt.ket_qua = 'dat'
        WHERE d.da_nghiem_thu = 1
          AND EXISTS (
              SELECT 1 FROM bao_gia bg
              WHERE bg.de_nghi_id = d.id AND bg.duoc_chon = 1
          )
    """
    params = []
    if trang_thai == "cho_tiep_nhan":
        query += " AND d.trang_thai IN ('da_phe_duyet', 'dang_mua')"
    elif trang_thai in ["da_tiep_nhan", "da_nhan"]:
        query += " AND d.trang_thai IN ('da_nhan', 'hoan_tat')"
    elif trang_thai:
        query += " AND d.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]
