from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu

# Ngưỡng kinh phí phân cấp phê duyệt theo Yêu cầu 1.docx:
# - Đơn dưới 100 triệu: Trưởng bộ phận mua sắm phê duyệt (hoặc Lãnh đạo)
# - Đơn từ 100 triệu trở lên: Bắt buộc Lãnh đạo (Admin) phê duyệt
NGUONG_PHE_DUYET_LANH_DAO = 100_000_000.0

def _khao_sat_phu_hop(ket_luan: str) -> bool:
    ket_luan_chuan_hoa = (ket_luan or "").strip().casefold()
    return ket_luan_chuan_hoa in {
        "phu_hop",
        "phù hợp và cần thiết để tổ chức thực hiện".casefold()
    }

def sinh_ma_de_nghi() -> str:
    """Sinh mã đề nghị mua sắm tự động theo dạng DN-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"DN-{ngay_str}-"

    row = db.execute(
        "SELECT ma_de_nghi FROM de_nghi_mua_sam WHERE ma_de_nghi LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_de_nghi"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def sinh_ma_khao_sat() -> str:
    """Sinh mã phiếu khảo sát tự động KS-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"KS-{ngay_str}-"

    row = db.execute(
        "SELECT ma_khao_sat FROM khao_sat_nhu_cau WHERE ma_khao_sat LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_khao_sat"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def sinh_ma_nghiem_thu() -> str:
    """Sinh mã biên bản nghiệm thu tự động NT-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"NT-{ngay_str}-"

    row = db.execute(
        "SELECT ma_nghiem_thu FROM nghiem_thu_mua_sam WHERE ma_nghiem_thu LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row:
        phan_duoi = row["ma_nghiem_thu"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def sinh_ma_thanh_toan() -> str:
    """Sinh mã phiếu đề nghị thanh toán tự động TT-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"TT-{ngay_str}-"

    row = db.execute(
        "SELECT ma_thanh_toan FROM thanh_toan WHERE ma_thanh_toan LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row and row["ma_thanh_toan"]:
        phan_duoi = row["ma_thanh_toan"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def tao_de_nghi(du_lieu: dict, nguoi_de_nghi_id: int) -> dict:
    """Tạo mới một đề nghị mua sắm kèm các hạng mục hàng hóa theo chuẩn BM01."""
    db = get_db()
    ma_de_nghi = sinh_ma_de_nghi()
    ngay_hien_tai = clock.now().isoformat()

    items = du_lieu.get("items", [])
    tong_du_toan = du_lieu.get("tong_du_toan")
    if tong_du_toan is None:
        tong_du_toan = sum(float(it.get("thanh_tien", it.get("so_luong", 0) * it.get("don_gia_du_kien", 0))) for it in items)

    trang_thai_khoi_tao = "cho_lanh_dao_duyet" if float(tong_du_toan) >= NGUONG_PHE_DUYET_LANH_DAO else "cho_phe_duyet"

    cursor = db.execute(
        """
        INSERT INTO de_nghi_mua_sam (
            ma_de_nghi, tieu_de, mo_ta, don_vi_de_nghi,
            nguoi_de_nghi_id, tong_du_toan, trang_thai,
            muc_do_uu_tien, nguon_kinh_phi, thoi_gian_can_hang,
            dia_diem_su_dung, ly_do_su_can_thiet, nguon_goc,
            bao_cao_hu_hai_id, ngay_tao, ngay_cap_nhat
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ma_de_nghi,
            du_lieu["tieu_de"],
            du_lieu.get("mo_ta", ""),
            du_lieu["don_vi_de_nghi"],
            nguoi_de_nghi_id,
            tong_du_toan,
            trang_thai_khoi_tao,
            du_lieu.get("muc_do_uu_tien", "binh_thuong"),
            du_lieu.get("nguon_kinh_phi", "Nguồn thu hợp pháp của Trường"),
            du_lieu.get("thoi_gian_can_hang", ""),
            du_lieu.get("dia_diem_su_dung", ""),
            du_lieu.get("ly_do_su_can_thiet", ""),
            du_lieu.get("nguon_goc", "moi"),
            du_lieu.get("bao_cao_hu_hai_id"),
            ngay_hien_tai,
            ngay_hien_tai
        )
    )
    de_nghi_id = cursor.lastrowid

    for item in items:
        so_luong = int(item.get("so_luong", 1))
        don_gia = float(item.get("don_gia_du_kien", 0))
        thanh_tien = float(item.get("thanh_tien", so_luong * don_gia))
        db.execute(
            """
            INSERT INTO chi_tiet_de_nghi (
                de_nghi_id, ten_hang_hoa, don_vi_tinh,
                so_luong, don_gia_du_kien, thanh_tien,
                vi_tri_su_dung, ly_do_muc_dich, ghi_chu
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                de_nghi_id,
                item["ten_hang_hoa"],
                item.get("don_vi_tinh", "Bộ"),
                so_luong,
                don_gia,
                thanh_tien,
                item.get("vi_tri_su_dung", ""),
                item.get("ly_do_muc_dich", ""),
                item.get("ghi_chu", "")
            )
        )

    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def lay_danh_sach_de_nghi(trang_thai: str = None) -> list:
    """Lấy danh sách đề nghị mua sắm, có thể lọc theo trạng thái."""
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
    """
    params = []
    if trang_thai:
        query += " WHERE d.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_de_nghi(de_nghi_id: int) -> dict:
    """Lấy thông tin chi tiết một đề nghị mua sắm bao gồm các hạng mục và hồ sơ liên quan."""
    db = get_db()
    row = db.execute(
        """
        SELECT d.*,
               u1.ho_ten AS nguoi_de_nghi_ten,
               u2.ho_ten AS nguoi_phe_duyet_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u1 ON d.nguoi_de_nghi_id = u1.id
        LEFT JOIN nguoi_dung u2 ON d.nguoi_phe_duyet_id = u2.id
        WHERE d.id = ?
        """,
        (de_nghi_id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    de_nghi = dict(row)

    items = db.execute(
        "SELECT * FROM chi_tiet_de_nghi WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchall()
    de_nghi["items"] = [dict(it) for it in items]

    khao_sat = db.execute(
        "SELECT * FROM khao_sat_nhu_cau WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    de_nghi["khao_sat"] = dict(khao_sat) if khao_sat else None
    de_nghi["khao_sat_phu_hop"] = bool(
        khao_sat and _khao_sat_phu_hop(khao_sat["ket_luan"])
    )

    bao_gia = db.execute(
        "SELECT * FROM bao_gia WHERE de_nghi_id = ? ORDER BY tong_gia ASC",
        (de_nghi_id,)
    ).fetchall()
    de_nghi["bao_gia"] = [dict(bg) for bg in bao_gia]
    de_nghi["bao_gia_da_chon"] = next(
        (bg for bg in de_nghi["bao_gia"] if bg["duoc_chon"]),
        None
    )

    nghiem_thu = db.execute(
        "SELECT * FROM nghiem_thu_mua_sam WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    de_nghi["nghiem_thu"] = dict(nghiem_thu) if nghiem_thu else None

    ho_so = db.execute(
        "SELECT * FROM ho_so_mua_sam WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchall()
    de_nghi["ho_so"] = [dict(hs) for hs in ho_so]

    tiep_nhan = db.execute(
        """
        SELECT tn.*, u.ho_ten AS nguoi_tiep_nhan_ten
        FROM tiep_nhan_hang tn
        LEFT JOIN nguoi_dung u ON tn.nguoi_tiep_nhan_id = u.id
        WHERE tn.de_nghi_id = ?
        """,
        (de_nghi_id,)
    ).fetchall()
    de_nghi["tiep_nhan"] = [dict(tn) for tn in tiep_nhan]

    thanh_toan = db.execute(
        """
        SELECT tt.*, u.ho_ten AS nguoi_thanh_toan_ten
        FROM thanh_toan tt
        LEFT JOIN nguoi_dung u ON tt.nguoi_thanh_toan_id = u.id
        WHERE tt.de_nghi_id = ?
        """,
        (de_nghi_id,)
    ).fetchall()
    de_nghi["thanh_toan"] = [dict(tt) for tt in thanh_toan]
    de_nghi["de_nghi_thanh_toan"] = next(
        (tt for tt in de_nghi["thanh_toan"] if tt.get("ma_thanh_toan")),
        None
    )

    return de_nghi

def phe_duyet_de_nghi(de_nghi_id: int, nguoi_phe_duyet_id: int, ghi_chu: str = "", vai_tro: str = "quan_tri") -> dict:
    """
    Phê duyệt đề nghị mua sắm theo phân cấp Yêu cầu 1.docx:
    - Đơn < 100 triệu: Trưởng bộ phận mua sắm ('mua_sam') hoặc Lãnh đạo/Admin ('quan_tri') phê duyệt.
    - Đơn >= 100 triệu: Bắt buộc Lãnh đạo/Admin ('quan_tri') phê duyệt.
    """
    db = get_db()
    row = db.execute("SELECT id, trang_thai, tong_du_toan, ma_de_nghi FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] not in ["cho_phe_duyet", "cho_lanh_dao_duyet"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể phê duyệt đề nghị đang chờ phê duyệt.")

    # Bắt buộc phải có khảo sát BM02 và kết luận "phù hợp và cần thiết để tổ chức thực hiện"
    khao_sat = db.execute(
        "SELECT ket_luan FROM khao_sat_nhu_cau WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    if not khao_sat:
        raise LoiNghiepVu("CHUA_KHAO_SAT", "Bắt buộc phải khảo sát nhu cầu mua sắm thực tế (BM02) trước khi phê duyệt đề nghị.")
    if not _khao_sat_phu_hop(khao_sat["ket_luan"]):
        raise LoiNghiepVu("KHAO_SAT_CHUA_PHU_HOP", "Chỉ được phê duyệt đề nghị khi kết luận khảo sát BM02 là 'Phù hợp và cần thiết để tổ chức thực hiện'.")

    tong_tien = float(row["tong_du_toan"] or 0)
    if tong_tien >= NGUONG_PHE_DUYET_LANH_DAO and vai_tro != "quan_tri":
        raise LoiNghiepVu(
            "KHONG_DU_QUYEN",
            f"Đề nghị mua sắm có kinh phí {tong_tien:,.0f} đ (≥ 100 triệu) thuộc thẩm quyền phê duyệt của Lãnh đạo (Admin).",
            status_code=403
        )

    thoi_gian = clock.now().isoformat()
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET trang_thai = 'da_phe_duyet',
            nguoi_phe_duyet_id = ?,
            ghi_chu_phe_duyet = ?,
            ngay_phe_duyet = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_phe_duyet_id, ghi_chu, thoi_gian, thoi_gian, de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tu_choi_de_nghi(de_nghi_id: int, nguoi_phe_duyet_id: int, ghi_chu: str = "", vai_tro: str = "quan_tri") -> dict:
    """
    Từ chối đề nghị mua sắm theo phân cấp:
    - Đơn < 100 triệu: Trưởng bộ phận mua sắm hoặc Lãnh đạo từ chối.
    - Đơn >= 100 triệu: Chỉ Lãnh đạo/Admin từ chối.
    """
    db = get_db()
    row = db.execute("SELECT id, trang_thai, tong_du_toan FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] not in ["cho_phe_duyet", "cho_lanh_dao_duyet"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể từ chối đề nghị đang chờ phê duyệt.")

    tong_tien = float(row["tong_du_toan"] or 0)
    if tong_tien >= NGUONG_PHE_DUYET_LANH_DAO and vai_tro != "quan_tri":
        raise LoiNghiepVu(
            "KHONG_DU_QUYEN",
            f"Đề nghị mua sắm có kinh phí {tong_tien:,.0f} đ (≥ 100 triệu) thuộc thẩm quyền của Lãnh đạo (Admin).",
            status_code=403
        )

    thoi_gian = clock.now().isoformat()
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET trang_thai = 'tu_choi',
            nguoi_phe_duyet_id = ?,
            ghi_chu_phe_duyet = ?,
            ngay_phe_duyet = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (nguoi_phe_duyet_id, ghi_chu, thoi_gian, thoi_gian, de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tao_khao_sat(de_nghi_id: int, du_lieu: dict) -> dict:
    """Lập biên bản khảo sát nhu cầu mua sắm thực tế BM02."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")
    if row["trang_thai"] in ["tu_choi", "da_nhan", "hoan_tat"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Không thể khảo sát đề nghị đã bị từ chối hoặc đã hoàn tất.")
    if db.execute(
        "SELECT 1 FROM bao_gia WHERE de_nghi_id = ? LIMIT 1", (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Không thể lập lại khảo sát sau khi đã ghi nhận báo giá.")

    khao_sat_hien_tai = db.execute(
        "SELECT ket_luan FROM khao_sat_nhu_cau WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    if khao_sat_hien_tai and _khao_sat_phu_hop(khao_sat_hien_tai["ket_luan"]):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Đề nghị đã có kết luận khảo sát phù hợp.")

    ma_khao_sat = sinh_ma_khao_sat()
    ngay_hien_tai = clock.now().isoformat()

    db.execute(
        """
        INSERT INTO khao_sat_nhu_cau (
            ma_khao_sat, de_nghi_id, noi_dung, ngay_khao_sat,
            dia_diem, can_bo_khao_sat, dai_dien_don_vi,
            ket_qua_danh_gia, kiem_tra_kho, doi_chieu_dinh_muc,
            muc_do_can_thiet, phuong_an_de_xuat, ket_luan, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ma_khao_sat,
            de_nghi_id,
            du_lieu["noi_dung"],
            ngay_hien_tai,
            du_lieu.get("dia_diem", ""),
            du_lieu.get("can_bo_khao_sat", ""),
            du_lieu.get("dai_dien_don_vi", ""),
            du_lieu.get("ket_qua_danh_gia", ""),
            du_lieu.get("kiem_tra_kho", ""),
            du_lieu.get("doi_chieu_dinh_muc", ""),
            du_lieu.get("muc_do_can_thiet", "can_thiet"),
            du_lieu.get("phuong_an_de_xuat", "mua_bo_sung"),
            du_lieu.get("ket_luan", "phu_hop"),
            ngay_hien_tai
        )
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def them_bao_gia(de_nghi_id: int, du_lieu: dict) -> dict:
    """Thêm một báo giá cạnh tranh cho đề nghị mua sắm."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")
    if row["trang_thai"] in ["tu_choi", "da_nhan", "hoan_tat"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Không thể thêm báo giá cho đề nghị đã bị từ chối hoặc đã hoàn tất.")

    khao_sat = db.execute(
        "SELECT ket_luan FROM khao_sat_nhu_cau WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    if not khao_sat:
        raise LoiNghiepVu("CHUA_KHAO_SAT", "Cần lập Biên bản khảo sát nhu cầu BM02 trước khi nhập báo giá.")
    if not _khao_sat_phu_hop(khao_sat["ket_luan"]):
        raise LoiNghiepVu("KHAO_SAT_CHUA_PHU_HOP", "Chỉ được nhập báo giá khi kết luận khảo sát BM02 là phù hợp.")
    if db.execute(
        "SELECT 1 FROM bao_gia WHERE de_nghi_id = ? AND duoc_chon = 1 LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("DA_CHON_NHA_CUNG_CAP", "Đã chốt nhà cung cấp; không thể thêm hoặc thay đổi báo giá.")
    nha_cung_cap_da_bao_gia = db.execute(
        "SELECT nha_cung_cap FROM bao_gia WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchall()
    ten_ncc_moi = du_lieu["nha_cung_cap"].strip().casefold()
    if any(row["nha_cung_cap"].strip().casefold() == ten_ncc_moi for row in nha_cung_cap_da_bao_gia):
        raise LoiNghiepVu("NHA_CUNG_CAP_DA_BAO_GIA", "Mỗi báo giá phải đến từ một nhà cung cấp độc lập, không trùng tên.")

    ngay_hien_tai = clock.now().isoformat()
    db.execute(
        """
        INSERT INTO bao_gia (
            de_nghi_id, nha_cung_cap, ma_so_thue, lien_he,
            tong_gia, ngay_bao_gia, hieu_luc, ghi_chu
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            de_nghi_id,
            du_lieu["nha_cung_cap"],
            du_lieu.get("ma_so_thue", ""),
            du_lieu.get("lien_he", ""),
            du_lieu["tong_gia"],
            ngay_hien_tai,
            du_lieu.get("hieu_luc", "30 ngày"),
            du_lieu.get("ghi_chu", "")
        )
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def chon_bao_gia(de_nghi_id: int, bao_gia_id: int) -> dict:
    """Chọn nhà cung cấp trúng thầu từ các báo giá."""
    db = get_db()
    de_nghi = db.execute(
        "SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?",
        (de_nghi_id,)
    ).fetchone()
    if not de_nghi:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")
    if de_nghi["trang_thai"] in ["tu_choi", "da_nhan", "hoan_tat"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Không thể chọn nhà cung cấp cho đề nghị đã bị từ chối hoặc đã hoàn tất.")

    khao_sat = db.execute(
        "SELECT ket_luan FROM khao_sat_nhu_cau WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    if not khao_sat or not _khao_sat_phu_hop(khao_sat["ket_luan"]):
        raise LoiNghiepVu("KHAO_SAT_CHUA_PHU_HOP", "Chỉ được chọn nhà cung cấp sau khi khảo sát BM02 có kết luận phù hợp.")

    so_bao_gia = db.execute(
        "SELECT COUNT(*) AS so_luong FROM bao_gia WHERE de_nghi_id = ?",
        (de_nghi_id,)
    ).fetchone()["so_luong"]
    if so_bao_gia < 3:
        raise LoiNghiepVu("CHUA_DU_BAO_GIA", "Cần tối thiểu 3 báo giá cạnh tranh trước khi chọn nhà cung cấp.")

    if db.execute(
        "SELECT 1 FROM bao_gia WHERE de_nghi_id = ? AND duoc_chon = 1 LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("DA_CHON_NHA_CUNG_CAP", "Nhà cung cấp đã được chốt và không thể chọn lại.")

    bg = db.execute("SELECT * FROM bao_gia WHERE id = ? AND de_nghi_id = ?", (bao_gia_id, de_nghi_id)).fetchone()
    if not bg:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Báo giá không tồn tại.")

    cursor = db.execute(
        """
        UPDATE bao_gia
        SET duoc_chon = 1
        WHERE id = ? AND de_nghi_id = ?
          AND NOT EXISTS (
              SELECT 1 FROM bao_gia bg_chon
              WHERE bg_chon.de_nghi_id = ? AND bg_chon.duoc_chon = 1
          )
        """,
        (bao_gia_id, de_nghi_id, de_nghi_id)
    )
    if cursor.rowcount != 1:
        raise LoiNghiepVu("DA_CHON_NHA_CUNG_CAP", "Nhà cung cấp đã được chốt và không thể chọn lại.")

    # Update provider info into de_nghi_mua_sam
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET nha_cung_cap = ?,
            gia_tri_hop_dong = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (bg["nha_cung_cap"], bg["tong_gia"], clock.now().isoformat(), de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tao_ho_so_mua_sam(de_nghi_id: int, nha_cung_cap: str, so_hop_dong: str, gia_tri: float, ghi_chu: str = "") -> dict:
    """Tạo hồ sơ mua sắm & hợp đồng cho đề nghị đã được duyệt."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    ngay_tao = clock.now().isoformat()
    cursor = db.execute(
        """
        INSERT INTO ho_so_mua_sam (de_nghi_id, nha_cung_cap, so_hop_dong, gia_tri_hop_dong, ngay_tao, ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (de_nghi_id, nha_cung_cap, so_hop_dong, gia_tri, ngay_tao, ghi_chu)
    )
    
    # Cập nhật số hợp đồng và nhà cung cấp vào đề nghị mua sắm
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET so_hop_dong = ?,
            nha_cung_cap = ?,
            gia_tri_hop_dong = ?,
            trang_thai = CASE WHEN trang_thai = 'da_phe_duyet' THEN 'dang_mua' ELSE trang_thai END,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (so_hop_dong, nha_cung_cap, gia_tri, ngay_tao, de_nghi_id)
    )
    db.commit()
    return {"id": cursor.lastrowid, "de_nghi_id": de_nghi_id}

def lap_bien_ban_nghiem_thu(de_nghi_id: int, du_lieu: dict) -> dict:
    """Lập biên bản kiểm tra, nghiệm thu hàng hóa trước khi bàn giao cho M09."""
    db = get_db()
    row = db.execute("SELECT id, trang_thai FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")
    if row["trang_thai"] not in ("da_phe_duyet", "dang_mua"):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ được nghiệm thu hàng hóa sau khi đề nghị đã được phê duyệt.")
    if not db.execute(
        "SELECT 1 FROM bao_gia WHERE de_nghi_id = ? AND duoc_chon = 1 LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("CHUA_CHON_NHA_CUNG_CAP", "Cần chốt nhà cung cấp trước khi lập biên bản nghiệm thu.")
    if db.execute(
        "SELECT 1 FROM nghiem_thu_mua_sam WHERE de_nghi_id = ? AND ket_qua = 'dat' LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("DA_NGHIEM_THU", "Biên bản nghiệm thu đạt đã được lập; không thể lập lại.")
    if du_lieu.get("ket_qua", "dat") not in ("dat", "khong_dat"):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kết quả nghiệm thu không hợp lệ.")

    ma_nghiem_thu = sinh_ma_nghiem_thu()
    ngay_hien_tai = clock.now().isoformat()

    db.execute(
        """
        INSERT INTO nghiem_thu_mua_sam (
            ma_nghiem_thu, de_nghi_id, ngay_nghiem_thu,
            dai_dien_ben_mua, dai_dien_nha_cung_cap, dai_dien_don_vi_su_dung,
            ket_qua, y_kien_danh_gia, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ma_nghiem_thu,
            de_nghi_id,
            ngay_hien_tai,
            du_lieu.get("dai_dien_ben_mua", ""),
            du_lieu.get("dai_dien_nha_cung_cap", ""),
            du_lieu.get("dai_dien_don_vi_su_dung", ""),
            du_lieu.get("ket_qua", "dat"),
            du_lieu.get("y_kien_danh_gia", ""),
            ngay_hien_tai
        )
    )

    da_nghiem_thu = 1 if du_lieu.get("ket_qua", "dat") == "dat" else 0
    db.execute(
        """
        UPDATE de_nghi_mua_sam
        SET da_nghiem_thu = ?,
            ngay_nghiem_thu = ?,
            ghi_chu_nghiem_thu = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (da_nghiem_thu, ngay_hien_tai, du_lieu.get("y_kien_danh_gia", ""), ngay_hien_tai, de_nghi_id)
    )
    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tiep_nhan_hang_hoa(de_nghi_id: int, du_lieu: dict, nguoi_tiep_nhan_id: int) -> dict:
    """
    Ghi nhận tiếp nhận hàng hóa từ đề nghị mua sắm theo biên bản giao nhận/nghiệm thu.
    Quy tắc tích hợp M08 -> M09:
    - Chuyển đề nghị sang 'da_nhan'.
    - Tự động phân loại tài sản:
        + Nếu đơn giá >= 10 triệu: 'tai_san_co_dinh' (Mã: TS-YYYY-XXXX).
        + Nếu đơn giá < 10 triệu: 'cong_cu_dung_cu' (Mã: CCDC-YYYY-XXXX).
    - Tạo các bản ghi tài sản mới vào kho M09 với trạng thái 'cho_ban_giao'.
    - Nếu đề nghị gắn liền với báo cáo hư hại (thay thế), cập nhật báo cáo hư hại sang 'da_xu_ly'.
    """
    db = get_db()
    row = db.execute("SELECT * FROM de_nghi_mua_sam WHERE id = ?", (de_nghi_id,)).fetchone()
    if not row:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")

    if row["trang_thai"] not in ["da_phe_duyet", "dang_mua"]:
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Chỉ có thể tiếp nhận hàng cho đề nghị đã phê duyệt hoặc đang mua.")

    nghiem_thu = db.execute(
        "SELECT ket_qua FROM nghiem_thu_mua_sam WHERE de_nghi_id = ? ORDER BY id DESC LIMIT 1",
        (de_nghi_id,)
    ).fetchone()
    if not row["da_nghiem_thu"] or not nghiem_thu or nghiem_thu["ket_qua"] != "dat":
        raise LoiNghiepVu("CHUA_NGHIEM_THU", "Hàng hóa chưa có Biên bản nghiệm thu kỹ thuật (BM04) đạt yêu cầu. Chưa đủ điều kiện tiếp nhận vào kho M09.")
    if not db.execute(
        "SELECT 1 FROM bao_gia WHERE de_nghi_id = ? AND duoc_chon = 1 LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("CHUA_CHON_NHA_CUNG_CAP", "Chưa chốt nhà cung cấp cho đề nghị mua sắm.")
    if db.execute(
        "SELECT 1 FROM tiep_nhan_hang WHERE de_nghi_id = ? LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("DA_TIEP_NHAN", "Hàng hóa của đề nghị này đã được tiếp nhận vào kho M09.")

    ngay_hien_tai = clock.now().isoformat()

    cursor = db.execute(
        """
        INSERT INTO tiep_nhan_hang (de_nghi_id, ngay_tiep_nhan, nguoi_tiep_nhan_id, ghi_chu)
        VALUES (?, ?, ?, ?)
        """,
        (de_nghi_id, ngay_hien_tai, nguoi_tiep_nhan_id, du_lieu.get("ghi_chu", ""))
    )
    tiep_nhan_id = cursor.lastrowid

    hang_hoa_rows = db.execute("SELECT * FROM chi_tiet_de_nghi WHERE de_nghi_id = ?", (de_nghi_id,)).fetchall()

    from app.services import tai_san as tai_san_svc

    for hang_row in hang_hoa_rows:
        hang = dict(hang_row)
        so_luong_nhan = hang["so_luong"]
        don_gia = float(hang["don_gia_du_kien"] or 0)
        phan_loai = "tai_san_co_dinh" if don_gia >= 10_000_000 else "cong_cu_dung_cu"

        db.execute(
            """
            INSERT INTO chi_tiet_tiep_nhan (tiep_nhan_id, ten_hang_hoa, so_luong_thuc_nhan, don_vi_tinh, tinh_trang, ghi_chu)
            VALUES (?, ?, ?, ?, 'tot', ?)
            """,
            (tiep_nhan_id, hang["ten_hang_hoa"], so_luong_nhan, hang["don_vi_tinh"], "Tiếp nhận từ đề nghị " + row["ma_de_nghi"])
        )

        for _ in range(so_luong_nhan):
            ma_tai_san = tai_san_svc.sinh_ma_tai_san(phan_loai=phan_loai)
            db.execute(
                """
                INSERT INTO tai_san (
                    ma_tai_san, ten_tai_san, mo_ta, loai_tai_san,
                    phan_loai, tinh_trang_ky_thuat,
                    vi_tri, phong_ban, don_vi_su_dung, gia_tri, ngay_tiep_nhan,
                    trang_thai, de_nghi_id, ngay_tao, ngay_cap_nhat
                )
                VALUES (?, ?, ?, ?, ?, 'binh_thuong', ?, ?, ?, ?, ?, 'cho_ban_giao', ?, ?, ?)
                """,
                (
                    ma_tai_san,
                    hang["ten_hang_hoa"],
                    f"Mua theo đề nghị {row['ma_de_nghi']}. {hang.get('ghi_chu', '')}",
                    "Thiết bị cơ sở vật chất",
                    phan_loai,
                    hang.get("vi_tri_su_dung") or "Kho trung tâm",
                    row["don_vi_de_nghi"],
                    row["don_vi_de_nghi"],
                    don_gia,
                    ngay_hien_tai,
                    de_nghi_id,
                    ngay_hien_tai,
                    ngay_hien_tai
                )
            )

    # Chuyển trạng thái đề nghị sang 'da_nhan'
    db.execute(
        "UPDATE de_nghi_mua_sam SET trang_thai = 'da_nhan', ngay_cap_nhat = ? WHERE id = ?",
        (ngay_hien_tai, de_nghi_id)
    )

    # Nếu đề nghị này giải quyết cho một báo cáo hư hại, cập nhật báo cáo hư hại sang 'da_xu_ly'
    if row["bao_cao_hu_hai_id"]:
        db.execute(
            """
            UPDATE bao_cao_hu_hai
            SET trang_thai = 'da_xu_ly',
                nguoi_xu_ly_id = ?,
                ngay_xu_ly = ?,
                ghi_chu_xu_ly = 'Đã hoàn tất mua sắm thay thế và nhập kho M09'
            WHERE id = ?
            """,
            (nguoi_tiep_nhan_id, ngay_hien_tai, row["bao_cao_hu_hai_id"])
        )

    db.commit()
    return lay_chi_tiet_de_nghi(de_nghi_id)

def tao_de_nghi_thanh_toan(de_nghi_id: int, du_lieu: dict, nguoi_de_nghi_id: int) -> dict:
    """Lập phiếu đề nghị thanh toán sau khi M09 đã tiếp nhận hàng."""
    db = get_db()
    de_nghi = db.execute(
        "SELECT id, ma_de_nghi, tieu_de, trang_thai FROM de_nghi_mua_sam WHERE id = ?",
        (de_nghi_id,)
    ).fetchone()
    if not de_nghi:
        raise LoiNghiepVu("DE_NGHI_KHONG_TON_TAI", "Đề nghị mua sắm không tồn tại trong hệ thống.")
    if de_nghi["trang_thai"] != "da_nhan":
        raise LoiNghiepVu("CHUA_TIEP_NHAN", "Chỉ được lập hồ sơ thanh toán sau khi M09 đã tiếp nhận hàng hóa.")
    if db.execute(
        "SELECT 1 FROM tiep_nhan_hang WHERE de_nghi_id = ? LIMIT 1",
        (de_nghi_id,)
    ).fetchone() is None:
        raise LoiNghiepVu("CHUA_TIEP_NHAN", "Chưa có phiếu tiếp nhận hàng hóa vào kho M09.")
    if db.execute(
        "SELECT 1 FROM thanh_toan WHERE de_nghi_id = ? AND ma_thanh_toan IS NOT NULL LIMIT 1",
        (de_nghi_id,)
    ).fetchone():
        raise LoiNghiepVu("DA_CO_DE_NGHI_THANH_TOAN", "Đề nghị này đã có hồ sơ thanh toán.")

    bao_gia = db.execute(
        """
        SELECT nha_cung_cap, tong_gia
        FROM bao_gia
        WHERE de_nghi_id = ? AND duoc_chon = 1
        """,
        (de_nghi_id,)
    ).fetchone()
    nghiem_thu = db.execute(
        """
        SELECT ma_nghiem_thu
        FROM nghiem_thu_mua_sam
        WHERE de_nghi_id = ? AND ket_qua = 'dat'
        ORDER BY id DESC LIMIT 1
        """,
        (de_nghi_id,)
    ).fetchone()
    if not bao_gia or not nghiem_thu:
        raise LoiNghiepVu("THIEU_HO_SO_THANH_TOAN", "Hồ sơ cần có nhà cung cấp đã chọn và biên bản nghiệm thu đạt.")

    gia_tri_de_nghi = float(bao_gia["tong_gia"] or 0)
    if gia_tri_de_nghi <= 0:
        raise LoiNghiepVu("THIEU_HO_SO_THANH_TOAN", "Giá trị báo giá đã chọn không hợp lệ để lập thanh toán.")

    ngay_de_nghi = clock.now().isoformat()
    ma_thanh_toan = sinh_ma_thanh_toan()
    ho_so_dinh_kem = "\n".join([
        f"Đề nghị mua sắm đã được phê duyệt: {de_nghi['ma_de_nghi']}",
        f"Báo giá và căn cứ xác định giá: {bao_gia['nha_cung_cap']}",
        "Hồ sơ lựa chọn nhà cung cấp (nếu áp dụng)",
        "Hợp đồng hoặc hồ sơ giao dịch tương ứng",
        f"Biên bản giao nhận, nghiệm thu: {nghiem_thu['ma_nghiem_thu']}",
        "Phiếu tiếp nhận hàng hóa vào kho M09",
        "Hóa đơn điện tử và chứng từ liên quan (Kế toán đối chiếu)"
    ])
    cursor = db.execute(
        """
        INSERT INTO thanh_toan (
            ma_thanh_toan, de_nghi_id, nha_cung_cap, noi_dung_thanh_toan,
            gia_tri_de_nghi, gia_tri_da_thanh_toan, so_tien_con_lai,
            ma_nghiem_thu, ho_so_dinh_kem, trang_thai, so_tien,
            ngay_de_nghi, nguoi_de_nghi_id, ghi_chu
        )
        VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 'cho_kiem_tra', 0, ?, ?, ?)
        """,
        (
            ma_thanh_toan,
            de_nghi_id,
            bao_gia["nha_cung_cap"],
            du_lieu["noi_dung_thanh_toan"],
            gia_tri_de_nghi,
            gia_tri_de_nghi,
            nghiem_thu["ma_nghiem_thu"],
            ho_so_dinh_kem,
            ngay_de_nghi,
            nguoi_de_nghi_id,
            du_lieu.get("ghi_chu", "")
        )
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "ma_thanh_toan": ma_thanh_toan,
        "de_nghi_id": de_nghi_id,
        "gia_tri_de_nghi": gia_tri_de_nghi
    }

def lay_danh_sach_ho_so() -> list:
    """Lấy danh sách các hồ sơ mua sắm."""
    db = get_db()
    rows = db.execute(
        """
        SELECT hs.*, d.ma_de_nghi, d.tieu_de, d.don_vi_de_nghi
        FROM ho_so_mua_sam hs
        JOIN de_nghi_mua_sam d ON hs.de_nghi_id = d.id
        ORDER BY hs.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]
