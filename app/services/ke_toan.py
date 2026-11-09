from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu


def lay_de_nghi_cho_thanh_toan() -> list:
    """Lấy các phiếu thanh toán M08 đang chờ Kế toán kiểm tra."""
    db = get_db()
    rows = db.execute(
        """
        SELECT tt.*, d.id AS de_nghi_id, d.ma_de_nghi, d.tieu_de, d.don_vi_de_nghi,
               u.ho_ten AS nguoi_de_nghi_ten
        FROM thanh_toan tt
        JOIN de_nghi_mua_sam d ON tt.de_nghi_id = d.id
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        WHERE tt.ma_thanh_toan IS NOT NULL
          AND tt.trang_thai = 'cho_kiem_tra'
        ORDER BY tt.id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def lay_chi_tiet_thanh_toan(de_nghi_id: int) -> dict:
    """Lấy hồ sơ đề nghị thanh toán và các chứng từ mua sắm liên quan."""
    from app.services.mua_sam import lay_chi_tiet_de_nghi

    de_nghi = lay_chi_tiet_de_nghi(de_nghi_id)
    row = get_db().execute(
        """
        SELECT * FROM thanh_toan
        WHERE de_nghi_id = ? AND ma_thanh_toan IS NOT NULL
          AND trang_thai = 'cho_kiem_tra'
        ORDER BY id DESC LIMIT 1
        """,
        (de_nghi_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_CO_DE_NGHI_THANH_TOAN", "Đề nghị chưa có phiếu thanh toán chờ Kế toán kiểm tra.")

    de_nghi["de_nghi_thanh_toan"] = dict(row)
    return de_nghi


def ghi_nhan_thanh_toan(de_nghi_id: int, du_lieu: dict, nguoi_thanh_toan_id: int) -> dict:
    """Kế toán ghi nhận giải ngân cho phiếu thanh toán M08 đã lập."""
    db = get_db()
    row = db.execute(
        """
        SELECT tt.*, d.trang_thai AS trang_thai_de_nghi
        FROM thanh_toan tt
        JOIN de_nghi_mua_sam d ON d.id = tt.de_nghi_id
        WHERE tt.de_nghi_id = ? AND tt.ma_thanh_toan IS NOT NULL
        ORDER BY tt.id DESC LIMIT 1
        """,
        (de_nghi_id,)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_CO_DE_NGHI_THANH_TOAN", "Đề nghị chưa có phiếu thanh toán do M08 lập.")
    if row["trang_thai"] != "cho_kiem_tra":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Phiếu thanh toán không còn ở trạng thái chờ Kế toán kiểm tra.")
    if row["trang_thai_de_nghi"] != "da_nhan":
        raise LoiNghiepVu("CHUA_TIEP_NHAN", "Chỉ thanh toán khi đề nghị đã được M09 tiếp nhận hàng hóa.")

    so_tien = float(du_lieu["so_tien"])
    so_tien_con_lai = float(row["so_tien_con_lai"] or 0)
    if round(so_tien, 2) != round(so_tien_con_lai, 2):
        raise LoiNghiepVu(
            "SO_TIEN_THANH_TOAN_KHONG_KHOP",
            f"Số tiền giải ngân phải bằng số còn phải thanh toán ({so_tien_con_lai:,.0f} VNĐ)."
        )

    ngay_thanh_toan = clock.now().isoformat()
    db.execute(
        """
        UPDATE thanh_toan
        SET so_tien = ?,
            gia_tri_da_thanh_toan = gia_tri_de_nghi,
            so_tien_con_lai = 0,
            trang_thai = 'da_thanh_toan',
            ngay_thanh_toan = ?,
            nguoi_thanh_toan_id = ?,
            phuong_thuc = ?,
            so_hoa_don = ?,
            ghi_chu = ?
        WHERE id = ?
        """,
        (
            so_tien,
            ngay_thanh_toan,
            nguoi_thanh_toan_id,
            du_lieu.get("phuong_thuc", "chuyen_khoan"),
            du_lieu["so_hoa_don"],
            du_lieu.get("ghi_chu", ""),
            row["id"]
        )
    )
    db.execute(
        "UPDATE de_nghi_mua_sam SET trang_thai = 'hoan_tat', ngay_cap_nhat = ? WHERE id = ?",
        (ngay_thanh_toan, de_nghi_id)
    )
    db.commit()
    return {
        "id": row["id"],
        "ma_thanh_toan": row["ma_thanh_toan"],
        "de_nghi_id": de_nghi_id,
        "so_tien": so_tien,
        "ngay_thanh_toan": ngay_thanh_toan
    }


def lay_lich_su_thanh_toan() -> list:
    """Lấy các phiếu thanh toán đã giải ngân."""
    db = get_db()
    rows = db.execute(
        """
        SELECT tt.*,
               d.ma_de_nghi, d.tieu_de, d.don_vi_de_nghi,
               u.ho_ten AS nguoi_thanh_toan_ten
        FROM thanh_toan tt
        JOIN de_nghi_mua_sam d ON tt.de_nghi_id = d.id
        LEFT JOIN nguoi_dung u ON tt.nguoi_thanh_toan_id = u.id
        WHERE tt.trang_thai = 'da_thanh_toan'
        ORDER BY tt.id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]
