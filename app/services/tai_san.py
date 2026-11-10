import sqlite3
import json

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
    """Sinh mã yêu cầu sửa chữa tự động YC-YYYYMMDD-XXX."""
    db = get_db()
    ngay_str = clock.now().strftime("%Y%m%d")
    prefix = f"YC-{ngay_str}-"

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

    return f"{prefix}{so_tt:03d}"

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
        SELECT t.*, u.ho_ten AS nguoi_su_dung_ten,
               u.don_vi AS nguoi_su_dung_don_vi, d.ma_de_nghi
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
               un.don_vi AS don_vi_nguoi_nhan,
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

def lay_danh_sach_nguoi_nhan_ban_giao(tai_san_id: int) -> list:
    """Lấy cán bộ thuộc ba Ban quản lý được phép nhận tài sản."""
    db = get_db()
    tai_san = db.execute(
        "SELECT nguoi_su_dung_id FROM tai_san WHERE id = ?", (tai_san_id,)
    ).fetchone()
    if not tai_san:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    if tai_san["nguoi_su_dung_id"]:
        return []

    da_ban_giao = db.execute(
        "SELECT 1 FROM lich_su_ban_giao WHERE tai_san_id = ? LIMIT 1",
        (tai_san_id,)
    ).fetchone()
    if da_ban_giao:
        return []

    allowed_units = ("Ban Quản lý Tòa A1", "Ban Quản lý Tòa A2", "Ban Quản lý Tòa BCD")
    placeholders = ", ".join("?" for _ in allowed_units)
    query = f"""
        SELECT id, ho_ten, ten_dang_nhap, don_vi
        FROM nguoi_dung
        WHERE vai_tro = 'don_vi' AND trang_thai = 'hoat_dong'
          AND don_vi IN ({placeholders})
    """
    params = list(allowed_units)
    query += " ORDER BY don_vi, ho_ten"
    return [dict(row) for row in db.execute(query, params).fetchall()]

def ban_giao_tai_san(tai_san_id: int, nguoi_nhan_id: int, nguoi_ban_giao_id: int, ghi_chu: str = "") -> dict:
    """Bàn giao tài sản cho người dùng / phòng ban sử dụng."""
    db = get_db()
    row = db.execute(
        "SELECT id, trang_thai, nguoi_su_dung_id FROM tai_san WHERE id = ?",
        (tai_san_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản không tồn tại trong hệ thống.")

    nguoi_nhan = db.execute(
        "SELECT id, ho_ten, vai_tro, don_vi, trang_thai FROM nguoi_dung WHERE id = ?",
        (nguoi_nhan_id,)
    ).fetchone()
    if not nguoi_nhan:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Người nhận bàn giao không tồn tại.")
    if (
        nguoi_nhan["vai_tro"] != "don_vi"
        or nguoi_nhan["trang_thai"] != "hoat_dong"
        or nguoi_nhan["don_vi"] not in (
            "Ban Quản lý Tòa A1", "Ban Quản lý Tòa A2", "Ban Quản lý Tòa BCD"
        )
    ):
        raise LoiNghiepVu(
            "NGUOI_NHAN_BAN_GIAO_KHONG_HOP_LE",
            "Chỉ cán bộ thuộc Ban Quản lý Tòa A1, A2 hoặc BCD được nhận bàn giao tài sản."
        )

    da_ban_giao = db.execute(
        "SELECT 1 FROM lich_su_ban_giao WHERE tai_san_id = ? LIMIT 1",
        (tai_san_id,)
    ).fetchone()
    if da_ban_giao or row["nguoi_su_dung_id"]:
        raise LoiNghiepVu(
            "TAI_SAN_DA_BAN_GIAO",
            "Tài sản chỉ được bàn giao một lần và đã được tiếp nhận."
        )
    if row["trang_thai"] not in ("cho_ban_giao", "dang_su_dung"):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Tài sản hiện không đủ điều kiện bàn giao.")

    ngay_ban_giao = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO lich_su_ban_giao
            (tai_san_id, nguoi_nhan_id, nguoi_ban_giao_id, ngay_ban_giao, ghi_chu)
        SELECT ?, ?, ?, ?, ?
        WHERE EXISTS (
            SELECT 1 FROM tai_san
            WHERE id = ? AND nguoi_su_dung_id IS NULL
        )
          AND NOT EXISTS (
            SELECT 1 FROM lich_su_ban_giao WHERE tai_san_id = ?
        )
        """,
        (
            tai_san_id, nguoi_nhan_id, nguoi_ban_giao_id, ngay_ban_giao, ghi_chu,
            tai_san_id, tai_san_id
        )
    )
    if cursor.rowcount != 1:
        raise LoiNghiepVu(
            "TAI_SAN_DA_BAN_GIAO",
            "Tài sản chỉ được bàn giao một lần và đã được tiếp nhận."
        )

    db.execute(
        """
        UPDATE tai_san
        SET nguoi_su_dung_id = ?,
            trang_thai = 'dang_su_dung',
            xac_nhan_ban_giao_don_vi = 0,
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
    tai_san_id = du_lieu.get("tai_san_id")
    if tai_san_id not in (None, ""):
        try:
            tai_san_id = int(tai_san_id)
        except (ValueError, TypeError) as exc:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tài sản được chọn không hợp lệ.") from exc

        requester = db.execute(
            "SELECT vai_tro FROM nguoi_dung WHERE id = ?",
            (nguoi_tao_id,)
        ).fetchone()
        don_vi = (du_lieu.get("don_vi") or "").strip()
        if requester and requester["vai_tro"] == "don_vi":
            asset_query = """
                SELECT ts.id, ts.ten_tai_san, ts.vi_tri
                FROM tai_san ts
                LEFT JOIN nguoi_dung nguoi_nhan ON nguoi_nhan.id = ts.nguoi_su_dung_id
                WHERE ts.id = ?
                  AND (
                      ts.don_vi_su_dung LIKE ?
                      OR ts.phong_ban LIKE ?
                      OR nguoi_nhan.don_vi LIKE ?
                  )
            """
            asset_params = (tai_san_id, f"%{don_vi}%", f"%{don_vi}%", f"%{don_vi}%")
        else:
            asset_query = "SELECT id, ten_tai_san, vi_tri FROM tai_san WHERE id = ?"
            asset_params = (tai_san_id,)
        tai_san = db.execute(
            asset_query,
            asset_params
        ).fetchone()
        if not tai_san:
            raise LoiNghiepVu(
                "TAI_SAN_KHONG_THUOC_DON_VI",
                "Tài sản đã chọn không thuộc danh mục quản lý của đơn vị."
            )
        du_lieu["ten_vat_chat"] = tai_san["ten_tai_san"]
        du_lieu["vi_tri"] = (du_lieu.get("vi_tri") or "").strip() or tai_san["vi_tri"] or ""
    else:
        tai_san_id = None

    required_fields = {
        "ten_vat_chat": ("Vui lòng nhập tên thiết bị hoặc hạng mục cần sửa.", "ten_vat_chat"),
        "vi_tri": ("Vui lòng nhập vị trí cụ thể của yêu cầu sửa chữa.", "vi_tri"),
        "mo_ta_chi_tiet": ("Vui lòng mô tả hiện trạng và nội dung cần sửa chữa.", "mo_ta_chi_tiet"),
    }
    if not du_lieu.get("ten_vat_chat") and du_lieu.get("noi_dung"):
        du_lieu["ten_vat_chat"] = du_lieu["noi_dung"]
    if not du_lieu.get("vi_tri") and du_lieu.get("hien_trang"):
        du_lieu["vi_tri"] = du_lieu["hien_trang"]
    if not du_lieu.get("mo_ta_chi_tiet") and du_lieu.get("noi_dung"):
        du_lieu["mo_ta_chi_tiet"] = du_lieu["noi_dung"]
    for field, (message, _) in required_fields.items():
        if not str(du_lieu.get(field) or "").strip():
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", message)

    cursor = db.execute(
        """
        INSERT INTO yeu_cau_sua_chua (
            ma_yeu_cau, tai_san_id, nguoi_tao_id, don_vi, ten_vat_chat,
            vi_tri, do_khan_cap, muc_do, thoi_gian_phat_hien, hinh_anh,
            xac_nhan_khao_sat_don_vi, xac_nhan_nghiem_thu_don_vi, loai_sua_chua,
            noi_dung, hien_trang, chi_phi_du_kien, don_vi_thuc_hien,
            nguoi_phu_trach_id, ngay_tiep_nhan, trang_thai, ghi_chu
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, NULL, ?, 'cho_tiep_nhan', ?)
        """,
        (
            ma_yeu_cau,
            tai_san_id,
            nguoi_tao_id,
            du_lieu.get("don_vi", ""),
            du_lieu.get("ten_vat_chat", ""),
            du_lieu.get("vi_tri", ""),
            du_lieu.get("do_khan_cap", "binh_thuong"),
            du_lieu.get("muc_do", "trung_binh"),
            du_lieu.get("thoi_gian_phat_hien") or ngay_hien_tai,
            du_lieu.get("hinh_anh", ""),
            du_lieu.get("loai_sua_chua", du_lieu.get("loai_yeu_cau", "sua_chua_nho")),
            du_lieu.get("mo_ta_chi_tiet") or du_lieu.get("noi_dung", ""),
            du_lieu.get("hien_trang", ""),
            du_lieu.get("chi_phi_du_kien", 0),
            du_lieu.get("don_vi_thuc_hien", "Tổ kỹ thuật QTTB"),
            ngay_hien_tai,
            du_lieu.get("ghi_chu", "")
        )
    )
    yeu_cau_id = cursor.lastrowid

    ghi_lich_su_sua_chua(
        yeu_cau_id, "tao_yeu_cau", "Đã gửi yêu cầu sửa chữa",
        du_lieu.get("mo_ta_chi_tiet") or du_lieu.get("noi_dung", ""),
        nguoi_tao_id, trang_thai="cho_tiep_nhan"
    )
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def ghi_lich_su_sua_chua(yeu_cau_id: int, loai_su_kien: str, tieu_de: str,
                         noi_dung: str, nguoi_tao_id: int, du_lieu: dict = None,
                         trang_thai: str = None, tep_dinh_kem: list = None) -> int:
    """Ghi nhật ký nghiệp vụ và các ảnh đính kèm của một yêu cầu sửa chữa."""
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO yeu_cau_sua_chua_lich_su
            (yeu_cau_id, loai_su_kien, tieu_de, noi_dung, du_lieu, trang_thai, nguoi_tao_id, ngay_tao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (yeu_cau_id, loai_su_kien, tieu_de, noi_dung,
         json.dumps(du_lieu or {}, ensure_ascii=False), trang_thai, nguoi_tao_id,
         clock.now().isoformat())
    )
    lich_su_id = cursor.lastrowid
    for tep in tep_dinh_kem or []:
        db.execute(
            """
            INSERT INTO yeu_cau_sua_chua_tep (lich_su_id, ten_tep, mime_type, noi_dung)
            VALUES (?, ?, ?, ?)
            """,
            (lich_su_id, tep["ten_tep"], tep["mime_type"], tep["noi_dung"])
        )
    return lich_su_id

def _doi_trang_thai_sua_chua(yeu_cau_id: int, trang_thai_hien_tai: str,
                             trang_thai_moi: str, loai_su_kien: str, tieu_de: str,
                             noi_dung: str, nguoi_tao_id: int, du_lieu: dict = None,
                             tep_dinh_kem: list = None) -> dict:
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != trang_thai_hien_tai:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu không ở trạng thái phù hợp để thực hiện thao tác này.")
    db.execute("UPDATE yeu_cau_sua_chua SET trang_thai = ? WHERE id = ?", (trang_thai_moi, yeu_cau_id))
    ghi_lich_su_sua_chua(
        yeu_cau_id, loai_su_kien, tieu_de, noi_dung, nguoi_tao_id,
        du_lieu=du_lieu, trang_thai=trang_thai_moi, tep_dinh_kem=tep_dinh_kem
    )
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def tiep_nhan_yeu_cau_sua_chua(yeu_cau_id: int, nguoi_tiep_nhan_id: int,
                               chap_nhan: bool, noi_dung: str = "") -> dict:
    """QTTB tiếp nhận phiếu hoặc trả lại để đơn vị bổ sung thông tin."""
    db = get_db()
    result = _doi_trang_thai_sua_chua(
        yeu_cau_id, "cho_tiep_nhan", "cho_khao_sat" if chap_nhan else "tra_lai",
        "tiep_nhan" if chap_nhan else "tra_lai",
        "QTTB đã tiếp nhận yêu cầu" if chap_nhan else "Yêu cầu bổ sung thông tin",
        noi_dung, nguoi_tiep_nhan_id
    )
    if not chap_nhan:
        db.execute("UPDATE yeu_cau_sua_chua SET ly_do_tra_lai = ? WHERE id = ?", (noi_dung, yeu_cau_id))
        db.commit()
        return lay_chi_tiet_sua_chua(yeu_cau_id)
    return result

def bat_dau_khao_sat_sua_chua(yeu_cau_id: int, nguoi_khao_sat_id: int) -> dict:
    """QTTB bắt đầu khảo sát BM03 sau khi đã tiếp nhận phiếu."""
    return _doi_trang_thai_sua_chua(
        yeu_cau_id, "cho_khao_sat", "dang_khao_sat", "bat_dau_khao_sat",
        "Bắt đầu khảo sát hiện trạng (BM03)", "", nguoi_khao_sat_id
    )

def cap_nhat_khao_sat_sua_chua(yeu_cau_id: int, du_lieu: dict,
                               nguoi_khao_sat_id: int, tep_dinh_kem: list = None) -> dict:
    """Lưu BM03 trong nhật ký khảo sát."""
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "dang_khao_sat":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể lập BM03 khi yêu cầu đang được khảo sát.")
    if sc["da_khao_sat"]:
        raise LoiNghiepVu("DA_LAP_BIEN_BAN_KHAO_SAT", "Biên bản khảo sát BM03 đã được lập, không thể lập lại.")
    if du_lieu.get("phan_loai_yeu_cau") not in ("sua_chua_nho", "thiet_bi", "cong_trinh"):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng phân loại yêu cầu sửa chữa.")
    try:
        db.execute(
            """
            UPDATE yeu_cau_sua_chua
            SET tinh_trang_bao_hanh = ?, hien_trang = ?, muc_do = ?, phuong_an_chi_tiet = ?, loai_sua_chua = ?
            WHERE id = ?
            """,
            (du_lieu.get("tinh_trang_bao_hanh", ""), du_lieu.get("hien_trang", ""),
             du_lieu.get("muc_do_hu_hong", ""), du_lieu.get("khoi_luong_cong_viec", ""),
             du_lieu["phan_loai_yeu_cau"], yeu_cau_id)
        )
        ghi_lich_su_sua_chua(
            yeu_cau_id, "khao_sat", "Biên bản khảo sát hiện trạng (BM03)",
            du_lieu.get("hien_trang", ""), nguoi_khao_sat_id, du_lieu=du_lieu,
            trang_thai="dang_khao_sat", tep_dinh_kem=tep_dinh_kem
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        if db.execute(
            "SELECT 1 FROM yeu_cau_sua_chua_lich_su WHERE yeu_cau_id = ? AND loai_su_kien = 'khao_sat'",
            (yeu_cau_id,)
        ).fetchone():
            raise LoiNghiepVu("DA_LAP_BIEN_BAN_KHAO_SAT", "Biên bản khảo sát BM03 đã được lập, không thể lập lại.")
        raise
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def trinh_phuong_an_sua_chua(yeu_cau_id: int, du_lieu: dict, nguoi_trinh_id: int) -> dict:
    """QTTB trình phương án và dự toán để lãnh đạo phê duyệt."""
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "dang_khao_sat":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể trình phương án sau khi tiếp nhận và khảo sát.")
    if not any(event["loai_su_kien"] == "khao_sat" for event in sc["lich_su"]):
        raise LoiNghiepVu("CHUA_CO_BIEN_BAN_KHAO_SAT", "Vui lòng lập biên bản khảo sát BM03 trước khi trình phương án.")
    if not du_lieu.get("phuong_an"):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng chọn phương án xử lý.")
    try:
        chi_phi = float(du_lieu.get("chi_phi_du_kien") or 0)
    except (TypeError, ValueError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kinh phí dự kiến không hợp lệ.")
    if chi_phi < 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kinh phí dự kiến không được âm.")

    can_mua_sam = bool(du_lieu.get("can_mua_sam"))
    db.execute(
        """
        UPDATE yeu_cau_sua_chua
        SET phuong_an = ?, phuong_an_chi_tiet = ?, chi_phi_du_kien = ?, can_mua_sam = ?
        WHERE id = ?
        """,
        (du_lieu["phuong_an"], du_lieu.get("phuong_an_chi_tiet", ""),
         chi_phi, int(can_mua_sam), yeu_cau_id)
    )
    ghi_lich_su_sua_chua(
        yeu_cau_id, "trinh_phuong_an", "Trình duyệt phương án sửa chữa",
        du_lieu.get("phuong_an_chi_tiet", ""), nguoi_trinh_id, du_lieu=du_lieu,
        trang_thai="cho_duyet_phuong_an"
    )
    db.execute("UPDATE yeu_cau_sua_chua SET trang_thai = 'cho_duyet_phuong_an' WHERE id = ?", (yeu_cau_id,))
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def phe_duyet_phuong_an_sua_chua(yeu_cau_id: int, nguoi_phe_duyet_id: int,
                                 vai_tro: str, ghi_chu: str = "") -> dict:
    """Admin chỉ phê duyệt phương án, không thực hiện tác nghiệp M09 khác."""
    db = get_db()
    if vai_tro != "quan_tri":
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Chỉ Lãnh đạo (Admin) được duyệt phương án sửa chữa.")
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "cho_duyet_phuong_an":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu không chờ phê duyệt phương án.")
    trang_thai_moi = "cho_thu_tuc_m08" if sc["can_mua_sam"] else "dang_sua_chua"
    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE yeu_cau_sua_chua
        SET trang_thai = ?, nguoi_phe_duyet_phuong_an_id = ?, ngay_phe_duyet_phuong_an = ?
        WHERE id = ?
        """,
        (trang_thai_moi, nguoi_phe_duyet_id, ngay_hien_tai, yeu_cau_id)
    )
    ghi_lich_su_sua_chua(
        yeu_cau_id, "phe_duyet_phuong_an", "Lãnh đạo đã duyệt phương án",
        ghi_chu, nguoi_phe_duyet_id, trang_thai=trang_thai_moi
    )
    if trang_thai_moi == "dang_sua_chua":
        _cap_nhat_tai_san_dang_sua(db, sc, ngay_hien_tai)
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def _cap_nhat_tai_san_dang_sua(db, sc: dict, ngay_hien_tai: str) -> None:
    if sc["tai_san_id"]:
        db.execute(
            """
            UPDATE tai_san
            SET trang_thai = 'dang_sua_chua', tinh_trang_ky_thuat = 'co_hu_hong', ngay_cap_nhat = ?
            WHERE id = ?
            """,
            (ngay_hien_tai, sc["tai_san_id"])
        )

def tao_de_nghi_mua_sam_tu_sua_chua(yeu_cau_id: int, nguoi_tao_id: int) -> dict:
    """Liên kết nhu cầu vật tư/dịch vụ đã duyệt sang quy trình M08."""
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "cho_thu_tuc_m08" or not sc["can_mua_sam"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Phương án chưa được duyệt để liên kết thủ tục M08.")
    if sc.get("de_nghi_mua_sam_id"):
        raise LoiNghiepVu("DA_TON_TAI", "Yêu cầu sửa chữa đã được liên kết với đề nghị M08.")
    from app.services import mua_sam as ms_svc
    ten_hang_hoa = sc.get("phuong_an_chi_tiet") or sc.get("ten_vat_chat") or sc["noi_dung"]
    de_nghi = ms_svc.tao_de_nghi({
        "tieu_de": f"Mua sắm phục vụ yêu cầu sửa chữa {sc['ma_yeu_cau']}",
        "mo_ta": sc.get("phuong_an_chi_tiet") or sc["noi_dung"],
        "don_vi_de_nghi": sc.get("don_vi") or "Phòng Quản trị thiết bị",
        "tong_du_toan": sc.get("chi_phi_du_kien") or 0,
        "muc_do_uu_tien": sc.get("do_khan_cap") or "binh_thuong",
        "dia_diem_su_dung": sc.get("vi_tri") or "",
        "ly_do_su_can_thiet": f"Phục vụ xử lý {sc['ma_yeu_cau']}",
        "nguon_goc": "sua_chua_m09",
        "items": [{
            "ten_hang_hoa": ten_hang_hoa,
            "don_vi_tinh": "Gói",
            "so_luong": 1,
            "don_gia_du_kien": sc.get("chi_phi_du_kien") or 0,
            "thanh_tien": sc.get("chi_phi_du_kien") or 0,
            "vi_tri_su_dung": sc.get("vi_tri") or "",
            "ly_do_muc_dich": f"Liên kết từ yêu cầu {sc['ma_yeu_cau']}"
        }]
    }, nguoi_tao_id)
    db.execute(
        "UPDATE de_nghi_mua_sam SET yeu_cau_sua_chua_id = ? WHERE id = ?",
        (yeu_cau_id, de_nghi["id"])
    )
    db.execute(
        "UPDATE yeu_cau_sua_chua SET de_nghi_mua_sam_id = ? WHERE id = ?",
        (de_nghi["id"], yeu_cau_id)
    )
    ghi_lich_su_sua_chua(
        yeu_cau_id, "lien_ket_m08", "Đã tạo đề nghị M08",
        f"Đề nghị {de_nghi['ma_de_nghi']} đang được xử lý.", nguoi_tao_id,
        du_lieu={"de_nghi_mua_sam_id": de_nghi["id"], "ma_de_nghi": de_nghi["ma_de_nghi"]},
        trang_thai="cho_thu_tuc_m08"
    )
    db.commit()
    return de_nghi

def bat_dau_sua_chua(yeu_cau_id: int, nguoi_thuc_hien_id: int) -> dict:
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] == "khong_dat_yeu_cau":
        trang_thai_cho_phep = True
    elif sc["trang_thai"] == "cho_thu_tuc_m08" and sc.get("de_nghi_mua_sam_id"):
        de_nghi = db.execute(
            "SELECT trang_thai FROM de_nghi_mua_sam WHERE id = ?", (sc["de_nghi_mua_sam_id"],)
        ).fetchone()
        trang_thai_cho_phep = bool(de_nghi and de_nghi["trang_thai"] in ("da_nhan", "hoan_tat"))
    else:
        trang_thai_cho_phep = False
    if not trang_thai_cho_phep:
        raise LoiNghiepVu("CHUA_HOAN_TAT_M08", "Yêu cầu chưa được duyệt khắc phục hoặc chưa hoàn tất thủ tục M08.")
    ngay_hien_tai = clock.now().isoformat()
    db.execute("UPDATE yeu_cau_sua_chua SET trang_thai = ? WHERE id = ?", ("dang_sua_chua", yeu_cau_id))
    _cap_nhat_tai_san_dang_sua(db, sc, ngay_hien_tai)
    ghi_lich_su_sua_chua(
        yeu_cau_id, "bat_dau_thi_cong", "Bắt đầu sửa chữa sau thủ tục M08",
        "", nguoi_thuc_hien_id, trang_thai="dang_sua_chua"
    )
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def ghi_nhat_ky_sua_chua(yeu_cau_id: int, noi_dung: str, nguoi_tao_id: int,
                         tep_dinh_kem: list = None) -> dict:
    if not noi_dung.strip():
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng nhập nội dung nhật ký thi công.")
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "dang_sua_chua":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ cập nhật tiến độ khi đang thi công sửa chữa.")
    ghi_lich_su_sua_chua(
        yeu_cau_id, "cap_nhat_tien_do", "Cập nhật tiến độ thi công",
        noi_dung, nguoi_tao_id, tep_dinh_kem=tep_dinh_kem
    )
    get_db().commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def lap_bien_ban_nghiem_thu_sua_chua(yeu_cau_id: int, du_lieu: dict,
                                     nguoi_lap_id: int) -> dict:
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] not in ("dang_sua_chua", "khong_dat_yeu_cau"):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ lập biên bản nghiệm thu sau khi sửa chữa hoặc khắc phục.")
    try:
        chi_phi = float(du_lieu.get("chi_phi_thuc_te") or 0)
    except (TypeError, ValueError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Chi phí thực tế không hợp lệ.")
    if chi_phi < 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Chi phí thực tế không được âm.")
    db.execute(
        "UPDATE yeu_cau_sua_chua SET chi_phi_thuc_te = ?, trang_thai = 'cho_nghiem_thu', ket_qua_nghiem_thu = 'cho_nghiem_thu' WHERE id = ?",
        (chi_phi, yeu_cau_id)
    )
    ghi_lich_su_sua_chua(
        yeu_cau_id, "lap_nghiem_thu", "Lập biên bản nghiệm thu",
        du_lieu.get("ghi_chu", ""), nguoi_lap_id, du_lieu=du_lieu,
        trang_thai="cho_nghiem_thu"
    )
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def xac_nhan_nghiem_thu_sua_chua(yeu_cau_id: int, du_lieu: dict,
                                 nguoi_xac_nhan_id: int) -> dict:
    db = get_db()
    sc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if sc["trang_thai"] != "cho_nghiem_thu":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Yêu cầu chưa ở trạng thái chờ nghiệm thu.")
    dat_yeu_cau = du_lieu.get("ket_qua") == "dat"
    trang_thai = "cho_lap_ho_so_thanh_toan" if dat_yeu_cau else "khong_dat_yeu_cau"
    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE yeu_cau_sua_chua
        SET trang_thai = ?, ket_qua_nghiem_thu = ?, ngay_hoan_thanh = ?,
            xac_nhan_nghiem_thu_don_vi = ?
        WHERE id = ?
        """,
        (trang_thai, "dat" if dat_yeu_cau else "khong_dat", ngay_hien_tai,
         int(dat_yeu_cau), yeu_cau_id)
    )
    ghi_lich_su_sua_chua(
        yeu_cau_id, "nghiem_thu", "Biên bản nghiệm thu",
        du_lieu.get("ghi_chu", ""), nguoi_xac_nhan_id,
        du_lieu=du_lieu, trang_thai=trang_thai
    )
    if dat_yeu_cau:
        if sc["tai_san_id"]:
            db.execute(
                """
                UPDATE tai_san
                SET trang_thai = 'dang_su_dung', tinh_trang_ky_thuat = 'binh_thuong', ngay_cap_nhat = ?
                WHERE id = ?
                """,
                (ngay_hien_tai, sc["tai_san_id"])
            )
            db.execute(
                """
                INSERT INTO bao_tri (tai_san_id, ngay_bao_tri, noi_dung, chi_phi, don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sc["tai_san_id"], ngay_hien_tai, sc["noi_dung"], sc["chi_phi_thuc_te"] or 0,
                 sc["don_vi_thuc_hien"] or "Tổ kỹ thuật QTTB", nguoi_xac_nhan_id,
                 f"Nghiệm thu yêu cầu {sc['ma_yeu_cau']}: Đạt")
            )
    db.commit()
    return lay_chi_tiet_sua_chua(yeu_cau_id)

def lay_ho_so_thanh_toan_sua_chua(yeu_cau_id: int) -> dict:
    row = get_db().execute(
        "SELECT * FROM thanh_toan_sua_chua WHERE yeu_cau_sua_chua_id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if not row:
        return None
    ho_so = dict(row)
    ho_so["ho_so_kem_theo"] = json.loads(ho_so["ho_so_kem_theo"] or "[]")
    ho_so["tep_dinh_kem"] = [
        dict(tep) for tep in get_db().execute(
            """
            SELECT id, ten_tep, mime_type, ngay_tao
            FROM thanh_toan_sua_chua_tep
            WHERE ho_so_id = ?
            ORDER BY id
            """,
            (ho_so["id"],)
        ).fetchall()
    ]
    return ho_so

def luu_ho_so_thanh_toan_sua_chua(yeu_cau_id: int, du_lieu: dict,
                                  nguoi_lap_id: int, gui: bool = False,
                                  tep_dinh_kem: list = None) -> dict:
    db = get_db()
    yc = lay_chi_tiet_sua_chua(yeu_cau_id)
    if not yc["xac_nhan_nghiem_thu_don_vi"] or yc["ket_qua_nghiem_thu"] != "dat":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ lập hồ sơ thanh toán sau khi biên bản nghiệm thu được xác nhận đạt.")
    if yc["trang_thai"] not in (
        "cho_lap_ho_so_thanh_toan", "da_nghiem_thu", "yeu_cau_bo_sung_ho_so"
    ):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Hồ sơ thanh toán hiện không thể chỉnh sửa hoặc gửi.")

    try:
        so_tien = float(du_lieu.get("so_tien") or 0)
    except (TypeError, ValueError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số tiền đề nghị thanh toán không hợp lệ.")
    if so_tien < 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số tiền đề nghị thanh toán không được âm.")

    required = {
        "nguoi_de_nghi_ten": "Người đề nghị thanh toán",
        "don_vi": "Đơn vị",
        "ve_khoan": "Nội dung khoản thanh toán",
        "so_tien_bang_chu": "Số tiền viết bằng chữ",
        "don_vi_thu_huong": "Đơn vị thụ hưởng",
        "so_tai_khoan": "Số tài khoản",
        "ngan_hang": "Tên ngân hàng"
    }
    if gui:
        missing = [label for field, label in required.items() if not str(du_lieu.get(field) or "").strip()]
        if missing:
            raise LoiNghiepVu(
                "DU_LIEU_DAU_VAO_KHONG_HOP_LE",
                "Vui lòng bổ sung: " + ", ".join(missing) + "."
            )
        if so_tien <= 0:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số tiền đề nghị thanh toán phải lớn hơn 0.")

    hien_tai = clock.now().isoformat()
    hien_co = db.execute(
        "SELECT * FROM thanh_toan_sua_chua WHERE yeu_cau_sua_chua_id = ?",
        (yeu_cau_id,)
    ).fetchone()
    if hien_co and hien_co["trang_thai"] not in ("nhap", "yeu_cau_bo_sung_ho_so"):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể chỉnh sửa hồ sơ nháp hoặc hồ sơ được yêu cầu bổ sung.")

    fields = (
        "nguoi_de_nghi_ten", "don_vi", "ve_khoan", "hop_dong_so", "hop_dong_ngay",
        "so_tien_bang_chu", "don_vi_thu_huong", "so_tai_khoan", "ngan_hang", "ho_so_khac"
    )
    values = {field: str(du_lieu.get(field) or "").strip() for field in fields}
    ho_so_kem_theo = json.dumps(du_lieu.get("ho_so_kem_theo") or [], ensure_ascii=False)
    if hien_co:
        db.execute(
            """
            UPDATE thanh_toan_sua_chua
            SET trang_thai = ?, nguoi_de_nghi_ten = ?, don_vi = ?, ve_khoan = ?,
                hop_dong_so = ?, hop_dong_ngay = ?, so_tien = ?, so_tien_bang_chu = ?,
                don_vi_thu_huong = ?, so_tai_khoan = ?, ngan_hang = ?, ho_so_kem_theo = ?,
                ho_so_khac = ?, ngay_cap_nhat = ?, ngay_gui = ?
            WHERE yeu_cau_sua_chua_id = ?
            """,
            (
                "cho_thanh_toan" if gui else hien_co["trang_thai"],
                values["nguoi_de_nghi_ten"], values["don_vi"], values["ve_khoan"],
                values["hop_dong_so"], values["hop_dong_ngay"], so_tien,
                values["so_tien_bang_chu"], values["don_vi_thu_huong"], values["so_tai_khoan"],
                values["ngan_hang"], ho_so_kem_theo, values["ho_so_khac"], hien_tai,
                hien_tai if gui else hien_co["ngay_gui"], yeu_cau_id
            )
        )
    else:
        db.execute(
            """
            INSERT INTO thanh_toan_sua_chua (
                yeu_cau_sua_chua_id, trang_thai, nguoi_de_nghi_ten, don_vi, ve_khoan,
                hop_dong_so, hop_dong_ngay, so_tien, so_tien_bang_chu, don_vi_thu_huong,
                so_tai_khoan, ngan_hang, ho_so_kem_theo, ho_so_khac, nguoi_lap_id,
                ngay_tao, ngay_cap_nhat, ngay_gui
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                yeu_cau_id, "cho_thanh_toan" if gui else "nhap",
                values["nguoi_de_nghi_ten"], values["don_vi"], values["ve_khoan"],
                values["hop_dong_so"], values["hop_dong_ngay"], so_tien,
                values["so_tien_bang_chu"], values["don_vi_thu_huong"], values["so_tai_khoan"],
                values["ngan_hang"], ho_so_kem_theo, values["ho_so_khac"], nguoi_lap_id,
                hien_tai, hien_tai, hien_tai if gui else None
            )
        )

    ho_so_id = hien_co["id"] if hien_co else db.execute(
        "SELECT id FROM thanh_toan_sua_chua WHERE yeu_cau_sua_chua_id = ?",
        (yeu_cau_id,)
    ).fetchone()["id"]
    for tep in tep_dinh_kem or []:
        db.execute(
            """
            INSERT INTO thanh_toan_sua_chua_tep
                (ho_so_id, ten_tep, mime_type, noi_dung, ngay_tao)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ho_so_id, tep["ten_tep"], tep["mime_type"], tep["noi_dung"],
                hien_tai
            )
        )

    if gui:
        db.execute(
            "UPDATE yeu_cau_sua_chua SET trang_thai = 'cho_thanh_toan' WHERE id = ?",
            (yeu_cau_id,)
        )
        ghi_lich_su_sua_chua(
            yeu_cau_id, "gui_ho_so_thanh_toan", "Đã gửi hồ sơ thanh toán sang Kế toán",
            f"Số tiền đề nghị: {so_tien:,.0f} VNĐ", nguoi_lap_id,
            du_lieu={"so_tien": so_tien}, trang_thai="cho_thanh_toan"
        )
    db.commit()
    return lay_ho_so_thanh_toan_sua_chua(yeu_cau_id)

def lay_tep_ho_so_thanh_toan_sua_chua(tep_id: int) -> dict:
    row = get_db().execute(
        "SELECT * FROM thanh_toan_sua_chua_tep WHERE id = ?",
        (tep_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tài liệu thanh toán không tồn tại.")
    return dict(row)

def lay_danh_sach_ho_so_thanh_toan_sua_chua() -> list:
    rows = get_db().execute(
        """
        SELECT hs.*, yc.ma_yeu_cau, yc.don_vi AS don_vi_su_dung,
               yc.noi_dung AS noi_dung_sua_chua, yc.chi_phi_thuc_te,
               yc.ngay_tiep_nhan, u.ho_ten AS nguoi_lap_ten
        FROM thanh_toan_sua_chua hs
        JOIN yeu_cau_sua_chua yc ON yc.id = hs.yeu_cau_sua_chua_id
        LEFT JOIN nguoi_dung u ON u.id = hs.nguoi_lap_id
        WHERE hs.trang_thai IN (
            'cho_thanh_toan', 'dang_xu_ly_thanh_toan', 'yeu_cau_bo_sung_ho_so'
        )
        ORDER BY hs.ngay_cap_nhat DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]

def lay_lich_su_thanh_toan_sua_chua() -> list:
    """Lấy các hồ sơ sửa chữa đã được Kế toán xác nhận thanh toán."""
    rows = get_db().execute(
        """
        SELECT hs.yeu_cau_sua_chua_id, hs.so_tien, hs.don_vi_thu_huong,
               hs.so_tai_khoan, hs.ngan_hang, hs.ngay_thanh_toan,
               hs.ghi_chu_ke_toan, yc.ma_yeu_cau, yc.noi_dung AS noi_dung_sua_chua,
               yc.don_vi AS don_vi_su_dung, nguoi_thanh_toan.ho_ten AS nguoi_thanh_toan_ten
        FROM thanh_toan_sua_chua hs
        JOIN yeu_cau_sua_chua yc ON yc.id = hs.yeu_cau_sua_chua_id
        LEFT JOIN nguoi_dung nguoi_thanh_toan ON nguoi_thanh_toan.id = hs.nguoi_thanh_toan_id
        WHERE hs.trang_thai = 'da_thanh_toan'
        ORDER BY hs.ngay_thanh_toan DESC, hs.id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]

def cap_nhat_ho_so_thanh_toan_sua_chua(yeu_cau_id: int, hanh_dong: str,
                                       nguoi_thanh_toan_id: int, ghi_chu: str = "") -> dict:
    db = get_db()
    ho_so = lay_ho_so_thanh_toan_sua_chua(yeu_cau_id)
    if not ho_so or ho_so["trang_thai"] not in (
        "cho_thanh_toan", "dang_xu_ly_thanh_toan"
    ):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Hồ sơ chưa được gửi hoặc không còn chờ xử lý.")

    if hanh_dong == "tiep_nhan":
        if ho_so["trang_thai"] != "cho_thanh_toan":
            raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Hồ sơ không ở trạng thái chờ tiếp nhận.")
        trang_thai = "dang_xu_ly_thanh_toan"
        tieu_de = "Kế toán tiếp nhận hồ sơ thanh toán"
    elif hanh_dong == "bo_sung":
        if ho_so["trang_thai"] != "dang_xu_ly_thanh_toan":
            raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ yêu cầu bổ sung khi đang kiểm tra hồ sơ.")
        if not ghi_chu.strip():
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng nêu rõ hồ sơ cần bổ sung.")
        trang_thai = "yeu_cau_bo_sung_ho_so"
        tieu_de = "Kế toán yêu cầu bổ sung hồ sơ thanh toán"
    elif hanh_dong == "da_thanh_toan":
        if ho_so["trang_thai"] != "dang_xu_ly_thanh_toan":
            raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Kế toán cần tiếp nhận hồ sơ trước khi xác nhận thanh toán.")
        trang_thai = "da_thanh_toan"
        tieu_de = "Kế toán xác nhận đã thanh toán"
    else:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Thao tác thanh toán không hợp lệ.")

    hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE thanh_toan_sua_chua
        SET trang_thai = ?, ghi_chu_ke_toan = ?,
            nguoi_thanh_toan_id = ?, ngay_cap_nhat = ?,
            ngay_thanh_toan = ?
        WHERE yeu_cau_sua_chua_id = ?
        """,
        (
            trang_thai, ghi_chu.strip() or ho_so.get("ghi_chu_ke_toan"),
            nguoi_thanh_toan_id if hanh_dong == "da_thanh_toan" else ho_so.get("nguoi_thanh_toan_id"),
            hien_tai, hien_tai if hanh_dong == "da_thanh_toan" else None, yeu_cau_id
        )
    )
    db.execute("UPDATE yeu_cau_sua_chua SET trang_thai = ? WHERE id = ?", (trang_thai, yeu_cau_id))
    ghi_lich_su_sua_chua(
        yeu_cau_id, f"thanh_toan_{hanh_dong}", tieu_de,
        ghi_chu.strip(), nguoi_thanh_toan_id, trang_thai=trang_thai
    )
    db.commit()
    return lay_ho_so_thanh_toan_sua_chua(yeu_cau_id)

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
               ts.thoi_han_bao_hanh, ts.ngay_tiep_nhan AS ngay_tiep_nhan_tai_san,
               ms.ma_de_nghi AS ma_de_nghi_m08, ms.trang_thai AS trang_thai_m08,
               u.ho_ten AS nguoi_phu_trach_ten,
               tao.ho_ten AS nguoi_tao_ten, tao.email AS nguoi_tao_email,
               tao.so_dien_thoai AS nguoi_tao_dien_thoai
        FROM yeu_cau_sua_chua sc
        LEFT JOIN tai_san ts ON sc.tai_san_id = ts.id
        LEFT JOIN de_nghi_mua_sam ms ON ms.id = sc.de_nghi_mua_sam_id
        LEFT JOIN nguoi_dung u ON sc.nguoi_phu_trach_id = u.id
        LEFT JOIN nguoi_dung tao ON sc.nguoi_tao_id = tao.id
        WHERE sc.id = ?
        """,
        (yeu_cau_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Yêu cầu sửa chữa không tồn tại.")
    detail = dict(row)
    history = db.execute(
        """
        SELECT ls.*, u.ho_ten AS nguoi_tao_ten
        FROM yeu_cau_sua_chua_lich_su ls
        LEFT JOIN nguoi_dung u ON u.id = ls.nguoi_tao_id
        WHERE ls.yeu_cau_id = ?
        ORDER BY ls.id
        """,
        (yeu_cau_id,)
    ).fetchall()
    detail["lich_su"] = []
    for item in history:
        event = dict(item)
        event["du_lieu"] = json.loads(event["du_lieu"] or "{}")
        event["tep_dinh_kem"] = [
            dict(tep) for tep in db.execute(
                "SELECT id, ten_tep, mime_type FROM yeu_cau_sua_chua_tep WHERE lich_su_id = ?",
                (event["id"],)
            ).fetchall()
        ]
        detail["lich_su"].append(event)
    detail["da_khao_sat"] = any(event["loai_su_kien"] == "khao_sat" for event in detail["lich_su"])
    if detail.get("tai_san_id"):
        row = db.execute(
            """
            SELECT COUNT(*) AS so_luong FROM yeu_cau_sua_chua
            WHERE tai_san_id = ? AND id != ?
              AND trang_thai NOT IN (
                  'da_nghiem_thu', 'da_thanh_toan', 'da_hoan_thanh', 'da_xu_ly', 'tra_lai'
              )
            """,
            (detail["tai_san_id"], yeu_cau_id)
        ).fetchone()
        detail["so_yeu_cau_dang_xu_ly"] = row["so_luong"]
    else:
        detail["so_yeu_cau_dang_xu_ly"] = 0
    return detail

def lay_tep_sua_chua(tep_id: int) -> dict:
    db = get_db()
    row = db.execute(
        """
        SELECT t.*, sc.nguoi_tao_id, sc.don_vi
        FROM yeu_cau_sua_chua_tep t
        JOIN yeu_cau_sua_chua_lich_su ls ON ls.id = t.lich_su_id
        JOIN yeu_cau_sua_chua sc ON sc.id = ls.yeu_cau_id
        WHERE t.id = ?
        """,
        (tep_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Ảnh đính kèm không tồn tại.")
    return dict(row)

def nghiem_thu_sua_chua(yeu_cau_id: int, du_lieu: dict, nguoi_nghiem_thu_id: int) -> dict:
    """Tương thích endpoint cũ: QTTB lập biên bản, đơn vị ký nghiệm thu."""
    return lap_bien_ban_nghiem_thu_sua_chua(yeu_cau_id, du_lieu, nguoi_nghiem_thu_id)

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
