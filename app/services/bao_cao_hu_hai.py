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
    tai_san_id = du_lieu.get("tai_san_id")
    if tai_san_id:
        tai_san = db.execute(
            """
            SELECT ma_tai_san, ten_tai_san, vi_tri
            FROM tai_san
            WHERE id = ? AND trang_thai != 'da_thanh_ly'
            """,
            (tai_san_id,)
        ).fetchone()
        if not tai_san:
            raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản được chọn không tồn tại hoặc đã thanh lý.")
        ten_vat_chat = f"{tai_san['ma_tai_san']} - {tai_san['ten_tai_san']}"
        vi_tri = tai_san["vi_tri"] or du_lieu["vi_tri"]
    else:
        ten_vat_chat = du_lieu["ten_vat_chat"]
        vi_tri = du_lieu["vi_tri"]

    cursor = db.execute(
        """
        INSERT INTO bao_cao_hu_hai (
            ho_ten, lien_he, ten_vat_chat, vi_tri, tai_san_id,
            muc_do, mo_ta_chi_tiet, thoi_gian_phat_hien,
            trang_thai, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'chua_xu_ly', ?)
        """,
        (
            du_lieu["ho_ten"],
            du_lieu["lien_he"],
            ten_vat_chat,
            vi_tri,
            tai_san_id,
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
        SELECT b.*, t.ma_tai_san, t.ten_tai_san AS ten_tai_san_danh_muc,
               y.id AS yeu_cau_id
        FROM bao_cao_hu_hai b
        LEFT JOIN tai_san t ON t.id = b.tai_san_id
        LEFT JOIN yeu_cau_xu_ly_tai_san y ON y.bao_cao_hu_hai_id = b.id
    """
    params = []
    if trang_thai:
        query += " WHERE b.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY b.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def tao_yeu_cau_tu_bao_cao(bao_cao_id: int, tai_san_id: int, nguoi_tiep_nhan_id: int) -> dict:
    """Đối chiếu phản ánh công khai với tài sản trường và chuyển thành yêu cầu nội bộ."""
    db = get_db()
    bao_cao = db.execute(
        "SELECT * FROM bao_cao_hu_hai WHERE id = ?",
        (bao_cao_id,)
    ).fetchone()
    if not bao_cao:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")

    yeu_cau_cu = db.execute(
        "SELECT id FROM yeu_cau_xu_ly_tai_san WHERE bao_cao_hu_hai_id = ?",
        (bao_cao_id,)
    ).fetchone()
    if yeu_cau_cu:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Báo cáo này đã được chuyển thành yêu cầu xử lý.")

    tai_san = db.execute(
        "SELECT id, trang_thai FROM tai_san WHERE id = ?",
        (tai_san_id,)
    ).fetchone()
    if not tai_san or tai_san["trang_thai"] == "da_thanh_ly":
        raise LoiNghiepVu("TAI_SAN_KHONG_TON_TAI", "Tài sản được đối chiếu không tồn tại hoặc đã thanh lý.")

    now = clock.now().isoformat()
    cursor = db.execute(
        """
        INSERT INTO yeu_cau_xu_ly_tai_san (
            tai_san_id, nguoi_tao_id, bao_cao_hu_hai_id,
            mo_ta_tinh_trang, muc_do, thoi_gian_phat_hien,
            trang_thai, ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, ?, 'cho_xac_minh', ?, ?)
        """,
        (
            tai_san_id, nguoi_tiep_nhan_id, bao_cao_id,
            f"{bao_cao['ten_vat_chat']}: {bao_cao['mo_ta_chi_tiet'] or 'Chưa có mô tả thêm.'}",
            bao_cao["muc_do"], bao_cao["thoi_gian_phat_hien"] or bao_cao["ngay_tao"],
            now, now
        )
    )
    from app.services.tai_san import ghi_nhan_su_kien_yeu_cau
    ghi_nhan_su_kien_yeu_cau(
        db, cursor.lastrowid, nguoi_tiep_nhan_id, "doi_chieu_bao_cao_cong_khai",
        f"Đã chuyển báo cáo công khai #{bao_cao_id} thành yêu cầu xử lý."
    )
    db.execute(
        "UPDATE bao_cao_hu_hai SET tai_san_id = ?, trang_thai = 'dang_xu_ly' WHERE id = ?",
        (tai_san_id, bao_cao_id)
    )
    db.commit()
    return {"id": cursor.lastrowid, "tai_san_id": tai_san_id}

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
