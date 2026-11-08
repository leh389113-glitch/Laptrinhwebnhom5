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
    query = """
        SELECT hh.*, u.ho_ten AS nguoi_xu_ly_ten, dn.ma_de_nghi
        FROM bao_cao_hu_hai hh
        LEFT JOIN nguoi_dung u ON hh.nguoi_xu_ly_id = u.id
        LEFT JOIN de_nghi_mua_sam dn ON hh.de_nghi_mua_sam_id = dn.id
    """
    params = []
    if trang_thai:
        query += " WHERE hh.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY hh.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_bao_cao(bao_cao_id: int) -> dict:
    """Lấy chi tiết một báo cáo hư hại."""
    db = get_db()
    row = db.execute(
        """
        SELECT hh.*, u.ho_ten AS nguoi_xu_ly_ten, dn.ma_de_nghi
        FROM bao_cao_hu_hai hh
        LEFT JOIN nguoi_dung u ON hh.nguoi_xu_ly_id = u.id
        LEFT JOIN de_nghi_mua_sam dn ON hh.de_nghi_mua_sam_id = dn.id
        WHERE hh.id = ?
        """,
        (bao_cao_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")
    return dict(row)

def cap_nhat_trang_thai(bao_cao_id: int, trang_thai_moi: str, nguoi_xu_ly_id: int = None, ghi_chu: str = "") -> dict:
    """Cập nhật trạng thái xử lý của báo cáo hư hại (Bộ phận Quản lý tài sản)."""
    cac_trang_thai = ["chua_xu_ly", "dang_xu_ly", "dang_sua_chua", "can_thay_the", "da_xu_ly"]
    if trang_thai_moi not in cac_trang_thai:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Trạng thái báo cáo không hợp lệ.")

    db = get_db()
    row = db.execute("SELECT id FROM bao_cao_hu_hai WHERE id = ?", (bao_cao_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")

    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = ?,
            nguoi_xu_ly_id = COALESCE(?, nguoi_xu_ly_id),
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = CASE WHEN ? != '' THEN ? ELSE ghi_chu_xu_ly END
        WHERE id = ?
        """,
        (trang_thai_moi, nguoi_xu_ly_id, ngay_hien_tai, ghi_chu, ghi_chu, bao_cao_id)
    )
    db.commit()
    return {"id": bao_cao_id, "trang_thai": trang_thai_moi}

def xac_minh_danh_gia(bao_cao_id: int, phuong_an: str, ghi_chu: str = "", nguoi_xu_ly_id: int = None) -> dict:
    """
    Bộ phận Quản lý tài sản xác minh thực tế và đánh giá tình trạng hư hỏng theo Yêu cầu 1.docx:
    - phuong_an == 'sua_chua': Trường hợp sửa chữa được -> Tạo yêu cầu sửa chữa M09, chuyển trạng thái 'dang_sua_chua'
    - phuong_an == 'thay_the': Trường hợp cần thay thế -> Chuyển sang trạng thái 'can_thay_the'
    - phuong_an == 'da_xu_ly': Đã hoàn tất xử lý / khắc phục
    """
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ban_do_trang_thai = {
        "sua_chua": "dang_sua_chua",
        "thay_the": "can_thay_the",
        "da_xu_ly": "da_xu_ly",
        "dang_xu_ly": "dang_xu_ly"
    }
    trang_thai_moi = ban_do_trang_thai.get(phuong_an, phuong_an)

    # Nếu chọn sửa chữa được: tạo luôn phiếu yêu cầu sửa chữa trong M09
    if phuong_an == "sua_chua":
        from app.services import tai_san as ts_svc
        du_lieu_sc = {
            "noi_dung": f"Sửa chữa sự cố: {bc['ten_vat_chat']} tại {bc['vi_tri']}",
            "hien_trang": bc.get("mo_ta_chi_tiet") or f"Mức độ ảnh hưởng: {bc.get('muc_do')}",
            "loai_sua_chua": "sua_chua_nho",
            "bao_cao_hu_hai_id": bao_cao_id,
            "tai_san_id": bc.get("tai_san_id"),
            "ghi_chu": ghi_chu
        }
        ts_svc.tao_yeu_cau_sua_chua(du_lieu_sc, nguoi_xu_ly_id or 1)

    return cap_nhat_trang_thai(bao_cao_id, trang_thai_moi, nguoi_xu_ly_id, ghi_chu)

def tao_yeu_cau_thay_the_sang_m08(bao_cao_id: int, nguoi_xu_ly_id: int) -> dict:
    """
    Trường hợp cần thay thế theo Yêu cầu 1.docx:
    Lập biên bản đánh giá hư hỏng không thể sửa chữa -> Tạo yêu cầu mua sắm thay thế chuyển M08.
    """
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    from app.services import mua_sam as ms_svc
    
    du_lieu_mua_sam = {
        "tieu_de": f"Mua sắm thay thế: {bc['ten_vat_chat']} tại {bc['vi_tri']}",
        "don_vi_de_nghi": "Bộ phận Quản lý tài sản",
        "mo_ta": f"Mua sắm thay thế theo Báo cáo sự cố #{bc['id']}: Thiết bị '{bc['ten_vat_chat']}' tại '{bc['vi_tri']}' bị hư hỏng (Mức độ: {bc['muc_do']}). Đánh giá thực tế: Không thể khắc phục sửa chữa, lập biên bản cần mua sắm thay thế.",
        "nguon_goc": "thay_the_hu_hai",
        "bao_cao_hu_hai_id": bao_cao_id,
        "muc_do_uu_tien": "khan_cap" if bc["muc_do"] == "nghiem_trong" else "can_som",
        "dia_diem_su_dung": bc["vi_tri"],
        "ly_do_su_can_thiet": f"Thiết bị '{bc['ten_vat_chat']}' tại '{bc['vi_tri']}' hỏng hóc nghiêm trọng không thể sửa chữa, cần trang bị thay thế đảm bảo giảng dạy và làm việc.",
        "items": [
            {
                "ten_hang_hoa": bc["ten_vat_chat"],
                "don_vi_tinh": "Bộ",
                "so_luong": 1,
                "don_gia_du_kien": 10_000_000,
                "vi_tri_su_dung": bc["vi_tri"],
                "ly_do_muc_dich": f"Thay thế thiết bị hư hỏng theo Báo cáo #{bc['id']}",
                "ghi_chu": f"Thay thế cho vị trí {bc['vi_tri']}"
            }
        ]
    }
    de_nghi = ms_svc.tao_de_nghi(du_lieu_mua_sam, nguoi_xu_ly_id)

    # Cập nhật liên kết đề nghị mua sắm vào báo cáo hư hại
    db = get_db()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = 'can_thay_the',
            phuong_an_xu_ly = 'can_thay_the',
            de_nghi_mua_sam_id = ?,
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?
        WHERE id = ?
        """,
        (de_nghi["id"], nguoi_xu_ly_id, clock.now().isoformat(), bao_cao_id)
    )
    db.commit()

    return de_nghi
