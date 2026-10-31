from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def lay_de_nghi_cho_thanh_toan() -> list:
    """Lấy danh sách các đề nghị đã tiếp nhận hàng hóa (da_nhan) đang chờ thanh toán."""
    db = get_db()
    rows = db.execute(
        """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        WHERE d.trang_thai = 'da_nhan'
        ORDER BY d.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_thanh_toan(de_nghi_id: int) -> dict:
    """Lấy thông tin đề nghị, hàng hóa và các giao dịch thanh toán liên quan."""
    from app.services.mua_sam import lay_chi_tiet_de_nghi
    return lay_chi_tiet_de_nghi(de_nghi_id)

def ghi_nhan_thanh_toan(de_nghi_id: int, du_lieu: dict, nguoi_thanh_toan_id: int) -> dict:
    """
    Ghi nhận thanh toán cho một đề nghị mua sắm.
    Cập nhật trạng thái đề nghị sang 'hoan_tat'.
    """
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] != "da_nhan":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể ghi nhận thanh toán cho đề nghị đã tiếp nhận hàng.")

    ngay_thanh_toan = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO thanh_toan (
            de_nghi_id, so_tien, ngay_thanh_toan, nguoi_thanh_toan_id,
            phuong_thuc, so_hoa_don, ghi_chu
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            de_nghi_id,
            du_lieu["so_tien"],
            ngay_thanh_toan,
            nguoi_thanh_toan_id,
            du_lieu.get("phuong_thuc", "chuyen_khoan"),
            du_lieu.get("so_hoa_don", ""),
            du_lieu.get("ghi_chu", "")
        )
    )

    db.execute(
        "UPDATE de_nghi_mua_sam SET trang_thai = 'hoan_tat', ngay_cap_nhat = ? WHERE id = ?",
        (ngay_thanh_toan, de_nghi_id)
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "de_nghi_id": de_nghi_id,
        "so_tien": du_lieu["so_tien"],
        "ngay_thanh_toan": ngay_thanh_toan
    }

def lay_lich_su_thanh_toan() -> list:
    """Lấy toàn bộ lịch sử các giao dịch thanh toán."""
    db = get_db()
    rows = db.execute(
        """
        SELECT tt.*,
               d.ma_de_nghi, d.tieu_de, d.don_vi_de_nghi,
               u.ho_ten AS nguoi_thanh_toan_ten
        FROM thanh_toan tt
        JOIN de_nghi_mua_sam d ON tt.de_nghi_id = d.id
        LEFT JOIN nguoi_dung u ON tt.nguoi_thanh_toan_id = u.id
        ORDER BY tt.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]

