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

def lay_tai_san_cong_khai() -> list:
    """Lấy thông tin tối thiểu của tài sản còn hoạt động để khách chọn khi báo hư hại."""
    db = get_db()
    rows = db.execute(
        """
        SELECT id, ma_tai_san, ten_tai_san, vi_tri
        FROM tai_san
        WHERE trang_thai != 'da_thanh_ly'
        ORDER BY ten_tai_san, ma_tai_san
        """
    ).fetchall()
    return [dict(row) for row in rows]

def ghi_nhan_su_kien_yeu_cau(db, yeu_cau_id: int, nguoi_thuc_hien_id: int, hanh_dong: str, noi_dung: str, thoi_gian: str = None):
    """Lưu một bước xử lý vào lịch sử yêu cầu tài sản."""
    db.execute(
        """
        INSERT INTO lich_su_yeu_cau_su_co (
            yeu_cau_id, nguoi_thuc_hien_id, hanh_dong, noi_dung, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (yeu_cau_id, nguoi_thuc_hien_id, hanh_dong, noi_dung, thoi_gian or clock.now().isoformat())
    )

def tao_yeu_cau_su_co(tai_san_id: int, du_lieu: dict, nguoi_tao_id: int) -> dict:
    """Tạo yêu cầu xử lý gắn với tài sản được bàn giao cho người gửi."""
    db = get_db()
    tai_san = db.execute(
        "SELECT id, nguoi_su_dung_id, trang_thai FROM tai_san WHERE id = ?",
        (tai_san_id,)
    ).fetchone()
    if not tai_san or tai_san["trang_thai"] == "da_thanh_ly":
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại hoặc đã thanh lý.")

    nguoi_gui = db.execute(
        "SELECT vai_tro FROM nguoi_dung WHERE id = ? AND trang_thai = 'hoat_dong'",
        (nguoi_tao_id,)
    ).fetchone()
    if not nguoi_gui:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Tài khoản không tồn tại hoặc đã ngừng hoạt động.")
    if (
        nguoi_gui["vai_tro"] not in ["quan_ly_kho", "quan_tri"]
        and tai_san["nguoi_su_dung_id"] != nguoi_tao_id
    ):
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Bạn chỉ có thể gửi yêu cầu cho tài sản đang được bàn giao cho mình.")

    now = clock.now().isoformat()
    cursor = db.execute(
        """
        INSERT INTO yeu_cau_xu_ly_tai_san (
            tai_san_id, nguoi_tao_id, mo_ta_tinh_trang, muc_do,
            thoi_gian_phat_hien, trang_thai, ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, 'cho_xac_minh', ?, ?)
        """,
        (
            tai_san_id, nguoi_tao_id, du_lieu["mo_ta_tinh_trang"],
            du_lieu["muc_do"], du_lieu.get("thoi_gian_phat_hien") or now,
            now, now
        )
    )
    ghi_nhan_su_kien_yeu_cau(
        db, cursor.lastrowid, nguoi_tao_id, "tao_yeu_cau",
        du_lieu["mo_ta_tinh_trang"], now
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(cursor.lastrowid)

def lay_danh_sach_yeu_cau_su_co(trang_thai: str = None, nguoi_tao_id: int = None) -> list:
    """Lấy danh sách yêu cầu xử lý, có thể giới hạn theo người gửi hoặc trạng thái."""
    db = get_db()
    query = """
        SELECT y.*, t.ma_tai_san, t.ten_tai_san, u.ho_ten AS nguoi_tao_ten,
               p.ho_ten AS nguoi_phan_cong_ten
        FROM yeu_cau_xu_ly_tai_san y
        JOIN tai_san t ON t.id = y.tai_san_id
        JOIN nguoi_dung u ON u.id = y.nguoi_tao_id
        LEFT JOIN nguoi_dung p ON p.id = y.nguoi_duoc_phan_cong_id
        WHERE 1 = 1
    """
    params = []
    if trang_thai:
        query += " AND y.trang_thai = ?"
        params.append(trang_thai)
    if nguoi_tao_id is not None:
        query += " AND y.nguoi_tao_id = ?"
        params.append(nguoi_tao_id)
    query += " ORDER BY y.id DESC"
    return [dict(row) for row in db.execute(query, params).fetchall()]

def lay_chi_tiet_yeu_cau_su_co(yeu_cau_id: int) -> dict:
    """Lấy chi tiết yêu cầu xử lý cùng thông tin tài sản và đề nghị mua thay thế."""
    db = get_db()
    row = db.execute(
        """
        SELECT y.*, t.ma_tai_san, t.ten_tai_san, t.vi_tri,
               u.ho_ten AS nguoi_tao_ten,
               x.ho_ten AS nguoi_xac_minh_ten,
               p.ho_ten AS nguoi_phan_cong_ten,
               k.ho_ten AS nguoi_kiem_tra_ten,
               d.ma_de_nghi, b.ho_ten AS nguoi_bao_cao,
               b.lien_he AS lien_he_nguoi_bao_cao
        FROM yeu_cau_xu_ly_tai_san y
        JOIN tai_san t ON t.id = y.tai_san_id
        JOIN nguoi_dung u ON u.id = y.nguoi_tao_id
        LEFT JOIN nguoi_dung x ON x.id = y.nguoi_xac_minh_id
        LEFT JOIN nguoi_dung p ON p.id = y.nguoi_duoc_phan_cong_id
        LEFT JOIN nguoi_dung k ON k.id = y.nguoi_kiem_tra_id
        LEFT JOIN de_nghi_mua_sam d ON d.id = y.de_nghi_mua_sam_id
        LEFT JOIN bao_cao_hu_hai b ON b.id = y.bao_cao_hu_hai_id
        WHERE y.id = ?
        """,
        (yeu_cau_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    yeu_cau = dict(row)
    lich_su = db.execute(
        """
        SELECT l.*, u.ho_ten AS nguoi_thuc_hien_ten
        FROM lich_su_yeu_cau_su_co l
        JOIN nguoi_dung u ON u.id = l.nguoi_thuc_hien_id
        WHERE l.yeu_cau_id = ?
        ORDER BY l.id
        """,
        (yeu_cau_id,)
    ).fetchall()
    yeu_cau["lich_su"] = [dict(event) for event in lich_su]
    return yeu_cau

def xac_minh_yeu_cau_su_co(yeu_cau_id: int, du_lieu: dict, nguoi_xac_minh_id: int) -> dict:
    """Ghi nhận kết quả xác minh và mở nhánh sửa chữa hoặc mua tài sản thay thế."""
    if du_lieu["phuong_an"] == "thay_the":
        from app.services import mua_sam as mua_sam_svc
        return mua_sam_svc.tao_de_nghi_thay_the(yeu_cau_id, du_lieu, nguoi_xac_minh_id)

    db = get_db()
    yeu_cau = db.execute(
        "SELECT id, tai_san_id, trang_thai FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if not yeu_cau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    if yeu_cau["trang_thai"] != "cho_xac_minh":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu này đã được xác minh hoặc xử lý.")

    now = clock.now().isoformat()
    db.execute(
        """
        UPDATE yeu_cau_xu_ly_tai_san
        SET trang_thai = 'cho_phan_cong', phuong_an = 'sua_chua',
            ket_qua_xac_minh = ?, nguoi_xac_minh_id = ?,
            ngay_xac_minh = ?, ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (
            du_lieu["ket_qua_xac_minh"], nguoi_xac_minh_id,
            now, now, yeu_cau_id
        )
    )
    ghi_nhan_su_kien_yeu_cau(
        db, yeu_cau_id, nguoi_xac_minh_id, "xac_minh",
        du_lieu["ket_qua_xac_minh"], now
    )
    db.execute(
        "UPDATE tai_san SET trang_thai = 'dang_sua_chua', ngay_cap_nhat = ? WHERE id = ?",
        (now, yeu_cau["tai_san_id"])
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(yeu_cau_id)

def phan_cong_yeu_cau_su_co(
    yeu_cau_id: int,
    nguoi_duoc_phan_cong_id: int,
    nguoi_phan_cong_id: int
) -> dict:
    """Phân công yêu cầu sửa chữa cho tài khoản đang hoạt động."""
    db = get_db()
    yeu_cau = db.execute(
        "SELECT trang_thai, phuong_an FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if not yeu_cau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    if yeu_cau["trang_thai"] != "cho_phan_cong" or yeu_cau["phuong_an"] != "sua_chua":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu hiện tại không chờ phân công sửa chữa.")
    nguoi_thuc_hien = db.execute(
        "SELECT id, ho_ten FROM nguoi_dung WHERE id = ? AND trang_thai = 'hoat_dong'",
        (nguoi_duoc_phan_cong_id,)
    ).fetchone()
    if not nguoi_thuc_hien:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Người được phân công không tồn tại hoặc đã ngừng hoạt động.")

    db.execute(
        """
        UPDATE yeu_cau_xu_ly_tai_san
        SET trang_thai = 'da_phan_cong', nguoi_duoc_phan_cong_id = ?, ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_duoc_phan_cong_id, clock.now().isoformat(), yeu_cau_id)
    )
    ghi_nhan_su_kien_yeu_cau(
        db, yeu_cau_id, nguoi_phan_cong_id, "phan_cong",
        f"Đã phân công cho {nguoi_thuc_hien['ho_ten']}."
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(yeu_cau_id)

def bat_dau_sua_chua(yeu_cau_id: int, nguoi_thuc_hien_id: int) -> dict:
    """Chuyển yêu cầu đã phân công sang trạng thái đang thực hiện."""
    db = get_db()
    yeu_cau = db.execute(
        "SELECT trang_thai, nguoi_duoc_phan_cong_id FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if not yeu_cau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    if yeu_cau["trang_thai"] != "da_phan_cong" or yeu_cau["nguoi_duoc_phan_cong_id"] != nguoi_thuc_hien_id:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Chỉ người được phân công mới có thể bắt đầu sửa chữa.")
    db.execute(
        """
        UPDATE yeu_cau_xu_ly_tai_san
        SET trang_thai = 'dang_thuc_hien', ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (clock.now().isoformat(), yeu_cau_id)
    )
    ghi_nhan_su_kien_yeu_cau(
        db, yeu_cau_id, nguoi_thuc_hien_id, "bat_dau",
        "Bắt đầu thực hiện sửa chữa."
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(yeu_cau_id)

def hoan_tat_sua_chua(yeu_cau_id: int, du_lieu: dict, nguoi_thuc_hien_id: int) -> dict:
    """Ghi nhận kết quả thực hiện và chuyển yêu cầu sang bước kiểm tra."""
    db = get_db()
    yeu_cau = db.execute(
        "SELECT trang_thai, nguoi_duoc_phan_cong_id FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if not yeu_cau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    if yeu_cau["trang_thai"] != "dang_thuc_hien" or yeu_cau["nguoi_duoc_phan_cong_id"] != nguoi_thuc_hien_id:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Chỉ người được phân công mới có thể ghi nhận kết quả sửa chữa.")

    db.execute(
        """
        UPDATE yeu_cau_xu_ly_tai_san
        SET trang_thai = 'cho_kiem_tra', noi_dung_thuc_hien = ?,
            don_vi_thuc_hien = ?, chi_phi = ?, ghi_chu_thuc_hien = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (
            du_lieu["noi_dung_thuc_hien"], du_lieu["don_vi_thuc_hien"],
            du_lieu["chi_phi"], du_lieu["ghi_chu"], clock.now().isoformat(),
            yeu_cau_id
        )
    )
    ghi_nhan_su_kien_yeu_cau(
        db, yeu_cau_id, nguoi_thuc_hien_id, "hoan_tat_thuc_hien",
        f"{du_lieu['noi_dung_thuc_hien']} - {du_lieu['ghi_chu']}".strip(" - ")
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(yeu_cau_id)

def kiem_tra_sua_chua(yeu_cau_id: int, du_lieu: dict, nguoi_kiem_tra_id: int) -> dict:
    """Kiểm tra kết quả sửa chữa, ghi nhật ký bảo trì khi đạt yêu cầu."""
    db = get_db()
    yeu_cau = db.execute(
        """
        SELECT y.*, u.vai_tro
        FROM yeu_cau_xu_ly_tai_san y
        JOIN nguoi_dung u ON u.id = ?
        WHERE y.id = ?
        """,
        (nguoi_kiem_tra_id, yeu_cau_id)
    ).fetchone()
    if not yeu_cau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu xử lý tài sản không tồn tại.")
    if yeu_cau["trang_thai"] != "cho_kiem_tra":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu chưa có kết quả sửa chữa cần kiểm tra.")
    if yeu_cau["vai_tro"] not in ["quan_ly_kho", "quan_tri"]:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Chỉ bộ phận Quản lý tài sản hoặc Admin mới được kiểm tra kết quả.")

    now = clock.now().isoformat()
    if du_lieu["ket_qua_kiem_tra"] == "dat":
        db.execute(
            """
            INSERT INTO bao_tri (
                tai_san_id, ngay_bao_tri, noi_dung, chi_phi,
                don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                yeu_cau["tai_san_id"], now, yeu_cau["noi_dung_thuc_hien"],
                yeu_cau["chi_phi"], yeu_cau["don_vi_thuc_hien"],
                nguoi_kiem_tra_id, du_lieu["ghi_chu"]
            )
        )
        trang_thai_moi = "sua_chua_hoan_tat"
        db.execute(
            "UPDATE tai_san SET trang_thai = 'dang_su_dung', ngay_cap_nhat = ? WHERE id = ?",
            (now, yeu_cau["tai_san_id"])
        )
        if yeu_cau["bao_cao_hu_hai_id"]:
            db.execute(
                "UPDATE bao_cao_hu_hai SET trang_thai = 'da_xu_ly' WHERE id = ?",
                (yeu_cau["bao_cao_hu_hai_id"],)
            )
    else:
        trang_thai_moi = "dang_thuc_hien"

    db.execute(
        """
        UPDATE yeu_cau_xu_ly_tai_san
        SET trang_thai = ?, ket_qua_kiem_tra = ?, nguoi_kiem_tra_id = ?,
            ngay_kiem_tra = ?, ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (trang_thai_moi, du_lieu["ghi_chu"], nguoi_kiem_tra_id, now, now, yeu_cau_id)
    )
    ghi_nhan_su_kien_yeu_cau(
        db, yeu_cau_id, nguoi_kiem_tra_id, "kiem_tra",
        f"{du_lieu['ket_qua_kiem_tra']}: {du_lieu['ghi_chu']}".strip(": ")
    )
    db.commit()
    return lay_chi_tiet_yeu_cau_su_co(yeu_cau_id)

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

    yeu_cau = db.execute(
        """
        SELECT y.id, y.muc_do, y.mo_ta_tinh_trang, y.trang_thai, y.ngay_tao,
               u.ho_ten AS nguoi_tao_ten
        FROM yeu_cau_xu_ly_tai_san y
        JOIN nguoi_dung u ON u.id = y.nguoi_tao_id
        WHERE y.tai_san_id = ?
        ORDER BY y.id DESC
        """,
        (tai_san_id,)
    ).fetchall()
    tai_san["yeu_cau_su_co"] = [dict(row) for row in yeu_cau]

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
