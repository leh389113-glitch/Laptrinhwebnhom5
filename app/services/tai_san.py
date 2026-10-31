from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def sinh_ma_tai_san() -> str:
    """Sinh mã tài sản tự động theo định dạng TS-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"TS-{ngay_str}-"

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

    return f"{prefix}{so_tt:03d}"

def sinh_ma_phieu_kiem_ke() -> str:
    """Sinh mã phiếu kiểm kê tự động KK-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"KK-{ngay_str}-"

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

    return f"{prefix}{so_tt:03d}"

def tao_tai_san_thu_cong(du_lieu: dict) -> dict:
    """Tạo mới một tài sản thủ công (không qua M08)."""
    db = get_db()
    ma_tai_san = sinh_ma_tai_san()
    ngay_hien_tai = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO tai_san (
            ma_tai_san, ten_tai_san, mo_ta, loai_tai_san,
            vi_tri, phong_ban, gia_tri, ngay_tiep_nhan,
            trang_thai, ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'cho_ban_giao', ?, ?)
        """,
        (
            ma_tai_san,
            du_lieu["ten_tai_san"],
            du_lieu.get("mo_ta", ""),
            du_lieu.get("loai_tai_san", "Cơ sở vật chất"),
            du_lieu.get("vi_tri", "Kho"),
            du_lieu.get("phong_ban", ""),
            du_lieu.get("gia_tri", 0),
            ngay_hien_tai,
            ngay_hien_tai,
            ngay_hien_tai
        )
    )
    db.commit()
    return lay_chi_tiet_tai_san(cursor.lastrowid)

def lay_danh_sach_tai_san(trang_thai: str = None, tu_khoa: str = None) -> list:
    """Lấy danh sách tất cả tài sản trong hệ thống."""
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

    # Lịch sử bàn giao
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

    # Lịch sử bảo trì
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
            vi_tri = ?,
            phong_ban = ?,
            gia_tri = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (
            du_lieu["ten_tai_san"],
            du_lieu.get("mo_ta", ""),
            du_lieu.get("loai_tai_san", ""),
            du_lieu.get("vi_tri", ""),
            du_lieu.get("phong_ban", ""),
            du_lieu.get("gia_tri", 0),
            ngay_cap_nhat,
            tai_san_id
        )
    )
    db.commit()
    return lay_chi_tiet_tai_san(tai_san_id)

def ban_giao_tai_san(tai_san_id: int, nguoi_nhan_id: int, nguoi_ban_giao_id: int, ghi_chu: str = "") -> dict:
    """Bàn giao tài sản cho người dùng nội bộ sử dụng."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM tai_san WHERE id = ?", (tai_san_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    # Kiểm tra người nhận
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
    """Ghi nhận hoạt động sửa chữa, bảo trì cho tài sản."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM tai_san WHERE id = ?", (tai_san_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    ngay_bao_tri = clock.now().isoformat()

    db.execute(
        """
        INSERT INTO bao_tri (tai_san_id, ngay_bao_tri, noi_dung, chi_phi, don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tai_san_id,
            ngay_bao_tri,
            du_lieu["noi_dung"],
            du_lieu.get("chi_phi", 0),
            du_lieu.get("don_vi_thuc_hien", ""),
            nguoi_ghi_nhan_id,
            du_lieu.get("ghi_chu", "")
        )
    )

    trang_thai_moi = du_lieu.get("trang_thai_moi")
    if trang_thai_moi in ["dang_su_dung", "dang_sua_chua", "cho_thanh_ly", "da_thanh_ly"]:
        db.execute(
            "UPDATE tai_san SET trang_thai = ?, ngay_cap_nhat = ? WHERE id = ?",
            (trang_thai_moi, ngay_bao_tri, tai_san_id)
        )

    db.commit()
    return lay_chi_tiet_tai_san(tai_san_id)

def tao_phieu_kiem_ke(du_lieu: dict, nguoi_kiem_ke_id: int) -> dict:
    """Tạo phiếu kiểm kê định kỳ."""
    db = get_db()
    ma_phieu = sinh_ma_phieu_kiem_ke()
    ngay_kiem_ke = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO phieu_kiem_ke (ma_phieu, ngay_kiem_ke, nguoi_kiem_ke_id, trang_thai, ghi_chu, ngay_tao)
        VALUES (?, ?, ?, 'hoan_tat', ?, ?)
        """,
        (ma_phieu, ngay_kiem_ke, nguoi_kiem_ke_id, du_lieu.get("ghi_chu", ""), ngay_kiem_ke)
    )
    phieu_id = cursor.lastrowid

    chi_tiet = du_lieu.get("chi_tiet", [])
    for ct in chi_tiet:
        db.execute(
            """
            INSERT INTO chi_tiet_kiem_ke (phieu_kiem_ke_id, tai_san_id, tinh_trang_thuc_te, ghi_chu)
            VALUES (?, ?, ?, ?)
            """,
            (phieu_id, ct["tai_san_id"], ct.get("tinh_trang", "tot"), ct.get("ghi_chu", ""))
        )

    db.commit()
    return {"id": phieu_id, "ma_phieu": ma_phieu}

def lay_danh_sach_kiem_ke() -> list:
    """Lấy danh sách các phiếu kiểm kê."""
    db = get_db()
    rows = db.execute(
        """
        SELECT pk.*, u.ho_ten AS nguoi_kiem_ke_ten,
               (SELECT COUNT(*) FROM chi_tiet_kiem_ke WHERE phieu_kiem_ke_id = pk.id) AS so_tai_san
        FROM phieu_kiem_ke pk
        LEFT JOIN nguoi_dung u ON pk.nguoi_kiem_ke_id = u.id
        ORDER BY pk.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]

