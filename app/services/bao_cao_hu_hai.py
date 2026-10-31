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
    """Cập nhật trạng thái xử lý của báo cáo hư hại (Admin / Quản lý)."""
    cac_trang_thai = ["chua_xu_ly", "dang_xu_ly", "da_xu_ly"]
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

