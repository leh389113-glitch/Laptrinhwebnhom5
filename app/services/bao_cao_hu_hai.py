from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def gui_bao_cao(du_lieu: dict) -> dict:
    """
    Tiếp nhận báo cáo hư hại vật chất từ form công khai (không cần đăng nhập).
    """
    db = get_db()
    ngay_tao = clock.now().isoformat()
    thoi_gian_phat_hien = du_lieu.get("thoi_gian_phat_hien") or ngay_tao

    cursor = db.execute(
        """
        INSERT INTO bao_cao_hu_hai (
            ho_ten, lien_he, ten_vat_chat, vi_tri,
            muc_do, mo_ta_chi_tiet, thoi_gian_phat_hien,
            trang_thai, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'chua_xu_ly', ?)
        """,
        (
            du_lieu["ho_ten"],
            du_lieu["lien_he"],
            du_lieu["ten_vat_chat"],
            du_lieu["vi_tri"],
            du_lieu.get("muc_do", "trung_binh"),
            du_lieu.get("mo_ta_chi_tiet", ""),
            thoi_gian_phat_hien,
            ngay_tao
        )
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "ho_ten": du_lieu["ho_ten"],
        "ten_vat_chat": du_lieu["ten_vat_chat"],
        "ngay_tao": ngay_tao
    }

def lay_danh_sach_bao_cao(trang_thai: str = None) -> list:
    """Lấy danh sách các báo cáo hư hại vật chất."""
    db = get_db()
    query = "SELECT * FROM bao_cao_hu_hai"
    params = []
    if trang_thai:
        query += " WHERE trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_bao_cao(bao_cao_id: int) -> dict:
    """Lấy chi tiết một báo cáo hư hại."""
    db = get_db()
    row = db.execute("SELECT * FROM bao_cao_hu_hai WHERE id = ?", (bao_cao_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")
    return dict(row)

def cap_nhat_trang_thai(bao_cao_id: int, trang_thai_moi: str) -> dict:
    """Cập nhật trạng thái xử lý của báo cáo hư hại (Bộ phận Quản lý tài sản)."""
    cac_trang_thai = ["chua_xu_ly", "dang_xu_ly", "dang_sua_chua", "can_thay_the", "da_xu_ly"]
    if trang_thai_moi not in cac_trang_thai:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Trạng thái báo cáo không hợp lệ.")

    db = get_db()
    row = db.execute("SELECT id FROM bao_cao_hu_hai WHERE id = ?", (bao_cao_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")

    db.execute(
        "UPDATE bao_cao_hu_hai SET trang_thai = ? WHERE id = ?",
        (trang_thai_moi, bao_cao_id)
    )
    db.commit()
    return {"id": bao_cao_id, "trang_thai": trang_thai_moi}

def xac_minh_danh_gia(bao_cao_id: int, phuong_an: str, ghi_chu: str = "", nguoi_xu_ly_id: int = None) -> dict:
    """
    Bộ phận Quản lý tài sản xác minh thực tế và đánh giá tình trạng hư hỏng theo Yêu cầu 1.docx:
    - phuong_an == 'sua_chua': Trường hợp sửa chữa được -> Chuyển sang trạng thái 'dang_sua_chua'
    - phuong_an == 'thay_the': Trường hợp cần thay thế -> Chuyển sang trạng thái 'can_thay_the'
    - phuong_an == 'da_xu_ly': Đã hoàn tất xử lý / khắc phục
    """
    ban_do_trang_thai = {
        "sua_chua": "dang_sua_chua",
        "thay_the": "can_thay_the",
        "da_xu_ly": "da_xu_ly",
        "dang_xu_ly": "dang_xu_ly"
    }
    trang_thai_moi = ban_do_trang_thai.get(phuong_an, phuong_an)
    return cap_nhat_trang_thai(bao_cao_id, trang_thai_moi)

def tao_yeu_cau_thay_the_sang_m08(bao_cao_id: int, nguoi_xu_ly_id: int) -> dict:
    """
    Trường hợp cần thay thế:
    Lập biên bản đánh giá -> Tạo yêu cầu mua sắm thay thế chuyển M08 (theo Yêu cầu 1.docx).
    """
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    from app.services import mua_sam as ms_svc
    
    du_lieu_mua_sam = {
        "tieu_de": f"Mua sắm thay thế: {bc['ten_vat_chat']} tại {bc['vi_tri']}",
        "don_vi_de_nghi": "Bộ phận Quản lý tài sản",
        "mo_ta": f"Mua sắm thay thế theo Báo cáo sự cố #{bc['id']}: Thiết bị '{bc['ten_vat_chat']}' tại '{bc['vi_tri']}' bị hư hỏng (Mức độ: {bc['muc_do']}). Đánh giá thực tế: Không thể sửa chữa, cần mua mới thay thế.",
        "items": [
            {
                "ten_hang_hoa": bc["ten_vat_chat"],
                "don_vi_tinh": "Bộ",
                "so_luong": 1,
                "don_gia_du_kien": 10_000_000,
                "ghi_chu": f"Thay thế cho vị trí {bc['vi_tri']}"
            }
        ]
    }
    de_nghi = ms_svc.tao_de_nghi(du_lieu_mua_sam, nguoi_xu_ly_id)
    cap_nhat_trang_thai(bao_cao_id, "can_thay_the")
    return de_nghi

