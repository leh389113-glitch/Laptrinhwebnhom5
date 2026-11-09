import os
from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

def sinh_ma_yeu_cau() -> str:
    """Sinh mã yêu cầu sửa chữa / báo cáo hư hại tự động: YC-YYYYMMDD-XXX"""
    db = get_db()
    prefix = f"YC-{clock.now().strftime('%Y%m%d')}-"
    row = db.execute(
        "SELECT ma_bao_cao FROM bao_cao_hu_hai WHERE ma_bao_cao LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    if row and row["ma_bao_cao"]:
        try:
            stt = int(row["ma_bao_cao"].split("-")[-1]) + 1
        except Exception:
            stt = 1
    else:
        stt = 1
    return f"{prefix}{stt:03d}"

def sinh_ma_khao_sat_bm03() -> str:
    """Sinh mã biên bản khảo sát hiện trạng: BM03-YYYYMMDD-XXX"""
    db = get_db()
    prefix = f"BM03-{clock.now().strftime('%Y%m%d')}-"
    row = db.execute(
        "SELECT ma_khao_sat FROM bao_cao_hu_hai WHERE ma_khao_sat LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    if row and row["ma_khao_sat"]:
        try:
            stt = int(row["ma_khao_sat"].split("-")[-1]) + 1
        except Exception:
            stt = 1
    else:
        stt = 1
    return f"{prefix}{stt:03d}"

def sinh_ma_nghiem_thu_sc() -> str:
    """Sinh mã biên bản nghiệm thu sửa chữa: NTSC-YYYYMMDD-XXX"""
    db = get_db()
    prefix = f"NTSC-{clock.now().strftime('%Y%m%d')}-"
    row = db.execute(
        "SELECT ma_nghiem_thu FROM bao_cao_hu_hai WHERE ma_nghiem_thu LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    if row and row["ma_nghiem_thu"]:
        try:
            stt = int(row["ma_nghiem_thu"].split("-")[-1]) + 1
        except Exception:
            stt = 1
    else:
        stt = 1
    return f"{prefix}{stt:03d}"

def gui_bao_cao(du_lieu: dict) -> dict:
    """
    Tiếp nhận báo cáo hư hại vật chất từ form công khai hoặc đơn vị gửi.
    Mặc định trạng thái khởi tạo là 'cho_tiep_nhan'.
    """
    db = get_db()
    ngay_tao = clock.now().isoformat()
    thoi_gian_phat_hien = du_lieu.get("thoi_gian_phat_hien") or ngay_tao
    ma_bao_cao = du_lieu.get("ma_bao_cao") or sinh_ma_yeu_cau()

    cursor = db.execute(
        """
        INSERT INTO bao_cao_hu_hai (
            ma_bao_cao, ho_ten, lien_he, ten_vat_chat, vi_tri,
            muc_do, mo_ta_chi_tiet, thoi_gian_phat_hien,
            trang_thai, ngay_tao, loai_yeu_cau, do_khan_cap,
            don_vi, hinh_anh, tai_san_id, nguoi_gui_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'cho_tiep_nhan', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ma_bao_cao,
            du_lieu["ho_ten"],
            du_lieu["lien_he"],
            du_lieu["ten_vat_chat"],
            du_lieu["vi_tri"],
            du_lieu.get("muc_do", "trung_binh"),
            du_lieu.get("mo_ta_chi_tiet", ""),
            thoi_gian_phat_hien,
            ngay_tao,
            du_lieu.get("loai_yeu_cau", "sua_chua_thiet_bi"),
            du_lieu.get("do_khan_cap", "binh_thuong"),
            du_lieu.get("don_vi", ""),
            du_lieu.get("hinh_anh", ""),
            du_lieu.get("tai_san_id"),
            du_lieu.get("nguoi_gui_id")
        )
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "ma_bao_cao": ma_bao_cao,
        "ho_ten": du_lieu["ho_ten"],
        "ten_vat_chat": du_lieu["ten_vat_chat"],
        "ngay_tao": ngay_tao
    }

def lay_danh_sach_bao_cao(trang_thai: str = None) -> list:
    """
    Lấy danh sách các báo cáo hư hại vật chất theo luồng tiến độ chuẩn M09.
    Đính kèm thông tin tài sản từ M09 và thông tin người xử lý.
    """
    db = get_db()
    query = """
        SELECT hh.*, 
               u.ho_ten AS nguoi_xu_ly_ten,
               ts.ma_tai_san, ts.ten_tai_san, ts.thoi_han_bao_hanh, ts.trang_thai AS trang_thai_tai_san,
               ts.vi_tri AS vi_tri_tai_san, ts.don_vi_su_dung AS don_vi_tai_san,
               dn.ma_de_nghi, dn.trang_thai AS trang_thai_de_nghi
        FROM bao_cao_hu_hai hh
        LEFT JOIN nguoi_dung u ON hh.nguoi_xu_ly_id = u.id
        LEFT JOIN tai_san ts ON hh.tai_san_id = ts.id
        LEFT JOIN de_nghi_mua_sam dn ON hh.de_nghi_mua_sam_id = dn.id
        WHERE 1=1
    """
    params = []
    if trang_thai:
        if trang_thai == "cho_tiep_nhan":
            query += " AND hh.trang_thai IN ('cho_tiep_nhan', 'chua_xu_ly')"
        elif trang_thai == "dang_khao_sat":
            query += " AND hh.trang_thai IN ('dang_khao_sat', 'dang_xu_ly')"
        elif trang_thai == "da_nghiem_thu":
            query += " AND hh.trang_thai IN ('da_nghiem_thu', 'da_xu_ly')"
        elif trang_thai == "cho_thu_tuc_m08":
            query += " AND hh.trang_thai IN ('cho_thu_tuc_m08', 'can_thay_the')"
        else:
            query += " AND hh.trang_thai = ?"
            params.append(trang_thai)

    query += " ORDER BY hh.id DESC"
    rows = db.execute(query, params).fetchall()
    
    result = []
    today = clock.now().strftime("%Y-%m-%d")
    for r in rows:
        d = dict(r)
        # Đánh giá hạn bảo hành
        if d.get("thoi_han_bao_hanh"):
            d["con_han_bao_hanh"] = str(d["thoi_han_bao_hanh"]) >= today
        else:
            d["con_han_bao_hanh"] = False
        result.append(d)

    return result

def lay_chi_tiet_bao_cao(bao_cao_id: int) -> dict:
    """Lấy chi tiết một báo cáo hư hại kèm toàn bộ dữ liệu lịch sử khảo sát, phương án, nghiệm thu."""
    db = get_db()
    row = db.execute(
        """
        SELECT hh.*, 
               u.ho_ten AS nguoi_xu_ly_ten,
               nd.ho_ten AS nguoi_gui_ten, nd.email AS nguoi_gui_email, nd.so_dien_thoai AS nguoi_gui_sdt,
               ts.ma_tai_san, ts.ten_tai_san, ts.thoi_han_bao_hanh, ts.trang_thai AS trang_thai_tai_san,
               ts.vi_tri AS vi_tri_tai_san, ts.don_vi_su_dung AS don_vi_tai_san, ts.gia_tri AS gia_tri_tai_san,
               ts.phan_loai AS phan_loai_tai_san, ts.so_serial, ts.model, ts.hang_san_xuat,
               dn.ma_de_nghi, dn.tieu_de AS de_nghi_tieu_de, dn.trang_thai AS trang_thai_de_nghi,
               dn.tong_du_toan AS de_nghi_tong_du_toan
        FROM bao_cao_hu_hai hh
        LEFT JOIN nguoi_dung u ON hh.nguoi_xu_ly_id = u.id
        LEFT JOIN nguoi_dung nd ON hh.nguoi_gui_id = nd.id
        LEFT JOIN tai_san ts ON hh.tai_san_id = ts.id
        LEFT JOIN de_nghi_mua_sam dn ON hh.de_nghi_mua_sam_id = dn.id
        WHERE hh.id = ?
        """,
        (bao_cao_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo cáo hư hại không tồn tại.")
    
    bc = dict(row)
    today = clock.now().strftime("%Y-%m-%d")
    if bc.get("thoi_han_bao_hanh"):
        bc["con_han_bao_hanh"] = str(bc["thoi_han_bao_hanh"]) >= today
    else:
        bc["con_han_bao_hanh"] = False

    return bc

# =========================================================================
# CÁC HÀM XỬ LÝ TIẾN ĐỘ THEO WORKFLOW CHUẨN M09 (8 GIAI ĐOẠN)
# =========================================================================

def tiep_nhan_yeu_cau(bao_cao_id: int, nguoi_xu_ly_id: int) -> dict:
    """Nút 📥 Tiếp nhận: Phòng QTTB tiếp nhận phiếu, chuyển sang trạng thái 'dang_khao_sat'."""
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = 'dang_khao_sat',
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = 'Phòng QTTB đã tiếp nhận yêu cầu và phân công cán bộ kiểm tra khảo sát hiện trường'
        WHERE id = ?
        """,
        (nguoi_xu_ly_id, ngay_hien_tai, bao_cao_id)
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def tra_lai_yeu_cau(bao_cao_id: int, ly_do: str, nguoi_xu_ly_id: int) -> dict:
    """Nút ↩️ Trả lại: Trả lại yêu cầu để đơn vị bổ sung thông tin."""
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = 'tra_lai',
            ly_do_tra_lai = ?,
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = ?
        WHERE id = ?
        """,
        (ly_do, nguoi_xu_ly_id, ngay_hien_tai, f"Trả lại yêu cầu: {ly_do}", bao_cao_id)
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def lap_khao_sat_bm03(bao_cao_id: int, du_lieu: dict, nguoi_xu_ly_id: int) -> dict:
    """
    Nút 📋 Lập khảo sát (BM03):
    Ghi nhận biên bản khảo sát hiện trạng hư hỏng, nguyên nhân, hình ảnh và phân loại 3 nhóm sửa chữa.
    Chuyển phiếu sang trạng thái 'cho_duyet_phuong_an'.
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ma_khao_sat = bc.get("ma_khao_sat") or sinh_ma_khao_sat_bm03()
    ngay_khao_sat = clock.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET ma_khao_sat = ?,
            ngay_khao_sat = ?,
            thanh_phan_khao_sat = ?,
            hien_trang_thuc_te = ?,
            nguyen_nhan_hu_hong = ?,
            muc_do_hu_hong = ?,
            anh_huong_an_toan = ?,
            khoi_luong_du_kien = ?,
            nhom_sua_chua = ?,
            tinh_trang_bao_hanh = ?,
            hinh_anh_khao_sat = COALESCE(NULLIF(?, ''), hinh_anh_khao_sat),
            trang_thai = 'cho_duyet_phuong_an',
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = 'Đã hoàn tất khảo sát hiện trường BM03, đang trình duyệt phương án xử lý'
        WHERE id = ?
        """,
        (
            ma_khao_sat,
            ngay_khao_sat,
            du_lieu.get("thanh_phan_khao_sat", "Cán bộ QTTB & Đại diện đơn vị"),
            du_lieu.get("hien_trang_thuc_te", bc.get("mo_ta_chi_tiet", "")),
            du_lieu.get("nguyen_nhan_hu_hong", "Hao mòn tự nhiên trong quá trình vận hành"),
            du_lieu.get("muc_do_hu_hong", bc.get("muc_do", "trung_binh")),
            du_lieu.get("anh_huong_an_toan", "Ảnh hưởng cục bộ hoạt động giảng dạy"),
            du_lieu.get("khoi_luong_du_kien", "Kiểm tra, thay thế linh kiện hỏng, chạy thử"),
            du_lieu.get("nhom_sua_chua", bc.get("loai_yeu_cau", "sua_chua_thiet_bi")),
            du_lieu.get("tinh_trang_bao_hanh", "het_bao_hanh"),
            du_lieu.get("hinh_anh_khao_sat", ""),
            nguoi_xu_ly_id,
            clock.now().isoformat(),
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def lap_phuong_an_trinh_duyet(bao_cao_id: int, du_lieu: dict, nguoi_xu_ly_id: int) -> dict:
    """
    Nút 📄 Lập phương án trình duyệt:
    Nhập phương án xử lý, kinh phí dự kiến, nguồn kinh phí và trình lãnh đạo phê duyệt.
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_trinh = clock.now().strftime("%Y-%m-%d %H:%M:%S")

    yeu_cau_m08 = 1 if du_lieu.get("yeu_cau_m08") in ["1", 1, "on", "true", True] else 0

    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET phuong_an_chi_tiet = ?,
            kinh_phi_du_kien = ?,
            nguon_kinh_phi_sua_chua = ?,
            yeu_cau_m08 = ?,
            ngay_trinh_duyet = ?,
            trang_thai = 'cho_duyet_phuong_an',
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = 'Đã lập phương án sửa chữa và dự toán kinh phí, chờ lãnh đạo phê duyệt'
        WHERE id = ?
        """,
        (
            du_lieu.get("phuong_an_chi_tiet", "Phương án sửa chữa phục hồi"),
            float(du_lieu.get("kinh_phi_du_kien", 0)),
            du_lieu.get("nguon_kinh_phi_sua_chua", "Kinh phí bảo dưỡng thường xuyên"),
            yeu_cau_m08,
            ngay_trinh,
            nguoi_xu_ly_id,
            clock.now().isoformat(),
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def phe_duyet_phuong_an(bao_cao_id: int, du_lieu: dict, nguoi_duyet_id: int) -> dict:
    """
    Phê duyệt phương án xử lý:
    - Nếu có phát sinh mua vật tư/thuê dịch vụ ngoài (yeu_cau_m08 = 1) -> Chuyển sang 'cho_thu_tuc_m08'
    - Nếu tự sửa chữa / đơn vị thi công xử lý ngay -> Chuyển sang 'dang_sua_chua'
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_duyet = clock.now().strftime("%Y-%m-%d %H:%M:%S")
    y_kien = du_lieu.get("y_kien_lanh_dao", "Đồng ý phê duyệt phương án và dự toán kinh phí.")

    # Xác định trạng thái tiếp theo
    if bc.get("yeu_cau_m08") == 1:
        trang_thai_moi = "cho_thu_tuc_m08"
        ghi_chu = "Phương án đã được duyệt, chuyển sang làm thủ tục mua sắm vật tư tại Phân hệ M08"
    else:
        trang_thai_moi = "dang_sua_chua"
        ghi_chu = "Phương án đã được duyệt, đơn vị sửa chữa bắt đầu triển khai khắc phục"

    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = ?,
            nguoi_duyet_phuong_an_id = ?,
            ngay_duyet_phuong_an = ?,
            y_kien_lanh_dao = ?,
            ngay_bat_dau_sua = CASE WHEN ? = 'dang_sua_chua' THEN ? ELSE ngay_bat_dau_sua END,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = ?
        WHERE id = ?
        """,
        (
            trang_thai_moi,
            nguoi_duyet_id,
            ngay_duyet,
            y_kien,
            trang_thai_moi,
            ngay_duyet,
            clock.now().isoformat(),
            ghi_chu,
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def lien_ket_m08_mua_sam(bao_cao_id: int, nguoi_xu_ly_id: int) -> dict:
    """
    Nút 🔗 Liên kết M08 (Mua sắm):
    Khi phương án có phát sinh mua vật tư/thiết bị hoặc thuê dịch vụ ngoài:
    Tự động đẩy dữ liệu sang Module M08, tạo gói đề nghị mua sắm liên kết.
    Sau đó chuyển trạng thái sang 'dang_sua_chua' (hoặc giữ 'cho_thu_tuc_m08' chờ M08 xong).
    """
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    from app.services import mua_sam as ms_svc

    kinh_phi = bc.get("kinh_phi_du_kien") or 10_000_000
    du_lieu_m08 = {
        "tieu_de": f"Mua sắm vật tư/thiết bị khắc phục sự cố: {bc['ten_vat_chat']} ({bc['ma_bao_cao'] or 'YC-' + str(bc['id'])})",
        "don_vi_de_nghi": bc.get("don_vi") or "Bộ phận Quản lý tài sản",
        "mo_ta": f"Hồ sơ mua sắm vật tư linh kiện theo Phiếu sửa chữa {bc['ma_bao_cao'] or bc['id']}: {bc['ten_vat_chat']} tại {bc['vi_tri']}. Phương án: {bc.get('phuong_an_chi_tiet', 'Mua linh kiện thay thế/sửa chữa')}.",
        "nguon_goc": "thay_the_hu_hai",
        "bao_cao_hu_hai_id": bao_cao_id,
        "muc_do_uu_tien": "khan_cap" if bc.get("muc_do") == "nghiem_trong" else "can_som",
        "dia_diem_su_dung": bc.get("vi_tri", ""),
        "ly_do_su_can_thiet": f"Cần trang bị vật tư để khắc phục sự cố theo Biên bản khảo sát {bc.get('ma_khao_sat', 'BM03')}",
        "items": [
            {
                "ten_hang_hoa": f"Vật tư/Linh kiện sửa chữa: {bc['ten_vat_chat']}",
                "don_vi_tinh": "Bộ",
                "so_luong": 1,
                "don_gia_du_kien": kinh_phi,
                "vi_tri_su_dung": bc.get("vi_tri", ""),
                "ly_do_muc_dich": f"Phục vụ sửa chữa theo phiếu {bc['ma_bao_cao'] or bc['id']}",
                "ghi_chu": f"Liên kết tự động từ M09: {bc.get('nhom_sua_chua', 'Sửa chữa')}"
            }
        ]
    }
    de_nghi = ms_svc.tao_de_nghi(du_lieu_m08, nguoi_xu_ly_id)

    db = get_db()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET de_nghi_mua_sam_id = ?,
            trang_thai = 'dang_sua_chua',
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = ?
        WHERE id = ?
        """,
        (
            de_nghi["id"],
            clock.now().isoformat(),
            f"Đã liên kết thành công sang M08 (Mã gói mua sắm: {de_nghi['ma_de_nghi']}), đơn vị thi công đang tiếp nhận khắc phục",
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def cap_nhat_tien_do(bao_cao_id: int, du_lieu: dict, nguoi_xu_ly_id: int) -> dict:
    """
    Nút 📝 Cập nhật tiến độ:
    Nhập nhật ký thi công, đơn vị thi công và đính kèm hình ảnh trong quá trình Đang sửa chữa.
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    nhat_ky_moi = du_lieu.get("nhat_ky_thi_cong", "")
    nhat_ky_cu = bc.get("nhat_ky_thi_cong") or ""
    thoi_diem = clock.now().strftime("%d/%m/%Y %H:%M")
    
    nhat_ky_tong = f"[{thoi_diem}] {nhat_ky_moi}\n{nhat_ky_cu}".strip()

    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET don_vi_thi_cong = COALESCE(NULLIF(?, ''), don_vi_thi_cong),
            nhat_ky_thi_cong = ?,
            hinh_anh_thi_cong = COALESCE(NULLIF(?, ''), hinh_anh_thi_cong),
            trang_thai = 'dang_sua_chua',
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = ?
        WHERE id = ?
        """,
        (
            du_lieu.get("don_vi_thi_cong", ""),
            nhat_ky_tong,
            du_lieu.get("hinh_anh_thi_cong", ""),
            clock.now().isoformat(),
            f"Cập nhật tiến độ sửa chữa: {nhat_ky_moi[:80]}...",
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def lap_bien_ban_nghiem_thu(bao_cao_id: int, du_lieu: dict, nguoi_xu_ly_id: int) -> dict:
    """
    Nút 🏁 Lập biên bản nghiệm thu:
    Khi sửa chữa hoàn thành, tạo phiếu nghiệm thu để chuyển sang trạng thái 'cho_nghiem_thu'.
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ma_nt = bc.get("ma_nghiem_thu") or sinh_ma_nghiem_thu_sc()
    ngay_nt = clock.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET ma_nghiem_thu = ?,
            ngay_nghiem_thu = ?,
            trang_thai = 'cho_nghiem_thu',
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = 'Sửa chữa hoàn thành, chờ đại diện các bên kiểm tra khả năng hoạt động và ký nghiệm thu'
        WHERE id = ?
        """,
        (
            ma_nt,
            ngay_nt,
            clock.now().isoformat(),
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def danh_gia_nghiem_thu(bao_cao_id: int, ket_qua: str, y_kien: str, yeu_cau_khac_phuc: str, nguoi_xu_ly_id: int) -> dict:
    """
    Đánh giá nghiệm thu sau khi sửa chữa:
    - ket_qua == 'dat': Chuyển 'da_nghiem_thu' (Hoàn thành), khôi phục tài sản 'dang_su_dung', ghi lịch sử bảo trì.
    - ket_qua == 'khong_dat': Chuyển 'khong_dat', yêu cầu đơn vị thi công khắc phục lại.
    """
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_hien_tai = clock.now().isoformat()
    ngay_gio_vn = clock.now().strftime("%d/%m/%Y %H:%M")

    if ket_qua == "dat":
        db.execute(
            """
            UPDATE bao_cao_hu_hai
            SET trang_thai = 'da_nghiem_thu',
                ket_qua_nghiem_thu = 'dat',
                y_kien_nghiem_thu = ?,
                ngay_xu_ly = ?,
                ghi_chu_xu_ly = 'Nghiệm thu ĐẠT yêu cầu. Sự cố đã được khắc phục hoàn tất, tài sản hoạt động tốt'
            WHERE id = ?
            """,
            (y_kien, ngay_hien_tai, bao_cao_id)
        )

        # Cập nhật trạng thái tài sản về bình thường & ghi nhận vào sổ bảo trì
        if bc.get("tai_san_id"):
            db.execute(
                """
                UPDATE tai_san
                SET trang_thai = 'dang_su_dung',
                    tinh_trang_ky_thuat = 'binh_thuong',
                    ngay_cap_nhat = ?
                WHERE id = ?
                """,
                (ngay_hien_tai, bc["tai_san_id"])
            )
            # Thêm lịch sử bảo trì
            db.execute(
                """
                INSERT INTO bao_tri (tai_san_id, ngay_bao_tri, noi_dung, chi_phi, don_vi_thuc_hien, nguoi_ghi_nhan_id, ghi_chu)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bc["tai_san_id"],
                    ngay_gio_vn,
                    f"Sửa chữa hoàn tất theo phiếu {bc['ma_bao_cao'] or bc['id']}: {bc.get('phuong_an_chi_tiet') or bc['ten_vat_chat']}",
                    bc.get("kinh_phi_du_kien", 0),
                    bc.get("don_vi_thi_cong", "Tổ kỹ thuật QTTB"),
                    nguoi_xu_ly_id,
                    f"Biên bản nghiệm thu: {bc.get('ma_nghiem_thu', 'NTSC')} - Kết quả: ĐẠT"
                )
            )

    else:
        # Không đạt yêu cầu
        db.execute(
            """
            UPDATE bao_cao_hu_hai
            SET trang_thai = 'khong_dat',
                ket_qua_nghiem_thu = 'khong_dat',
                y_kien_nghiem_thu = ?,
                yeu_cau_khac_phuc = ?,
                ngay_xu_ly = ?,
                ghi_chu_xu_ly = ?
            WHERE id = ?
            """,
            (
                y_kien,
                yeu_cau_khac_phuc,
                ngay_hien_tai,
                f"Kiểm tra không đạt: {yeu_cau_khac_phuc}",
                bao_cao_id
            )
        )

    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

def khac_phuc_lai(bao_cao_id: int, ghi_chu: str, nguoi_xu_ly_id: int) -> dict:
    """Chuyển phiếu từ 'khong_dat' quay lại 'dang_sua_chua' để tiếp tục thi công khắc phục."""
    db = get_db()
    bc = lay_chi_tiet_bao_cao(bao_cao_id)
    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        UPDATE bao_cao_hu_hai
        SET trang_thai = 'dang_sua_chua',
            nguoi_xu_ly_id = ?,
            ngay_xu_ly = ?,
            ghi_chu_xu_ly = ?
        WHERE id = ?
        """,
        (
            nguoi_xu_ly_id,
            ngay_hien_tai,
            f"Đang thi công khắc phục lại: {ghi_chu}",
            bao_cao_id
        )
    )
    db.commit()
    return lay_chi_tiet_bao_cao(bao_cao_id)

# Giữ tương thích ngược với các module cũ
def xac_minh_danh_gia(bao_cao_id: int, phuong_an: str, ghi_chu: str = "", nguoi_xu_ly_id: int = None) -> dict:
    """Hàm tương thích ngược."""
    if phuong_an == "sua_chua":
        return tiep_nhan_yeu_cau(bao_cao_id, nguoi_xu_ly_id or 1)
    elif phuong_an == "thay_the":
        return lien_ket_m08_mua_sam(bao_cao_id, nguoi_xu_ly_id or 1)
    elif phuong_an == "da_xu_ly":
        return danh_gia_nghiem_thu(bao_cao_id, "dat", ghi_chu or "Hoàn tất xử lý", "", nguoi_xu_ly_id or 1)
    return lay_chi_tiet_bao_cao(bao_cao_id)

def tao_yeu_cau_thay_the_sang_m08(bao_cao_id: int, nguoi_xu_ly_id: int) -> dict:
    """Tương thích ngược."""
    return lien_ket_m08_mua_sam(bao_cao_id, nguoi_xu_ly_id)
