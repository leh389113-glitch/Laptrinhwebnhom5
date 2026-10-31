import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def dang_ky(du_lieu: dict) -> dict:
    """
    Đăng ký tài khoản người dùng mới.
    Vai trò được chọn từ form đăng ký (mặc định 'mua_sam').
    """
    db = get_db()
    ten_dang_nhap = du_lieu["ten_dang_nhap"]
    email = du_lieu["email"]
    ho_ten = du_lieu["ho_ten"]
    mat_khau = du_lieu["mat_khau"]
    vai_tro = du_lieu.get("vai_tro", "mua_sam")
    if vai_tro not in ["mua_sam", "quan_ly_kho", "ke_toan", "quan_tri"]:
        vai_tro = "mua_sam"

    # Kiểm tra tên đăng nhập đã tồn tại
    row = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = ?", (ten_dang_nhap,)).fetchone()
    if row:
        raise LoiNghiepVu("TAI_KHOAN_DA_TON_TAI", "Tên đăng nhập đã tồn tại trong hệ thống.")

    # Kiểm tra email đã tồn tại
    row_email = db.execute("SELECT id FROM nguoi_dung WHERE email = ?", (email,)).fetchone()
    if row_email:
        raise LoiNghiepVu("EMAIL_DA_TON_TAI", "Email đã tồn tại trong hệ thống.")

    mat_khau_hash = generate_password_hash(mat_khau)
    ngay_tao = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO nguoi_dung (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, ngay_tao, trang_thai)
        VALUES (?, ?, ?, ?, ?, ?, 'hoat_dong')
        """,
        (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, ngay_tao)
    )
    db.commit()

    nguoi_dung_id = cursor.lastrowid
    return {
        "id": nguoi_dung_id,
        "ho_ten": ho_ten,
        "email": email,
        "ten_dang_nhap": ten_dang_nhap,
        "vai_tro": vai_tro
    }

def dang_nhap(ten_dang_nhap: str, mat_khau: str) -> dict:
    """
    Xác thực thông tin đăng nhập của người dùng.
    """
    db = get_db()
    user = db.execute(
        "SELECT id, ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, trang_thai FROM nguoi_dung WHERE ten_dang_nhap = ?",
        (ten_dang_nhap,)
    ).fetchone()

    if not user:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Tài khoản hoặc mật khẩu không chính xác.")

    if user["trang_thai"] != "hoat_dong":
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Tài khoản của bạn đã bị khóa hoặc ngừng hoạt động.")

    if not check_password_hash(user["mat_khau_hash"], mat_khau):
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Tài khoản hoặc mật khẩu không chính xác.")

    return {
        "id": user["id"],
        "ho_ten": user["ho_ten"],
        "email": user["email"],
        "ten_dang_nhap": user["ten_dang_nhap"],
        "vai_tro": user["vai_tro"]
    }

def lay_nguoi_dung(nguoi_dung_id: int) -> dict:
    """Lấy thông tin người dùng theo ID."""
    db = get_db()
    user = db.execute(
        "SELECT id, ho_ten, email, ten_dang_nhap, vai_tro, trang_thai, ngay_tao FROM nguoi_dung WHERE id = ?",
        (nguoi_dung_id,)
    ).fetchone()

    if not user:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Người dùng không tồn tại.")

    return dict(user)

def lay_danh_sach_nguoi_dung() -> list:
    """Lấy danh sách toàn bộ người dùng trong hệ thống (dành cho Admin)."""
    db = get_db()
    users = db.execute(
        "SELECT id, ho_ten, email, ten_dang_nhap, vai_tro, trang_thai, ngay_tao FROM nguoi_dung ORDER BY id ASC"
    ).fetchall()
    return [dict(u) for u in users]

def doi_vai_tro(nguoi_dung_id: int, vai_tro_moi: str) -> dict:
    """Thay đổi vai trò của người dùng (Admin)."""
    cac_vai_tro_hop_le = ["mua_sam", "quan_ly_kho", "ke_toan", "quan_tri"]
    if vai_tro_moi not in cac_vai_tro_hop_le:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", f"Vai trò '{vai_tro_moi}' không hợp lệ.")

    db = get_db()
    user = db.execute("SELECT id FROM nguoi_dung WHERE id = ?", (nguoi_dung_id,)).fetchone()
    if not user:
        raise LoiNghiepVu("TAI_KHOAN_KHONG_TON_TAI", "Người dùng không tồn tại.")

    db.execute("UPDATE nguoi_dung SET vai_tro = ? WHERE id = ?", (vai_tro_moi, nguoi_dung_id))
    db.commit()

    return {"id": nguoi_dung_id, "vai_tro": vai_tro_moi}
