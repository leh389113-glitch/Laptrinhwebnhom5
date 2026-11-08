import io
import csv
from app.db import get_db
from app import clock

def thong_ke_tong_quan() -> dict:
    """
    Tổng hợp các chỉ số KPI và dữ liệu cho Dashboard M17 (Admin).
    Dữ liệu được truy vấn trực tiếp từ bảng M08 và M09, không lưu cache cứng.
    """
    db = get_db()
    hien_tai = clock.now()
    thang_hien_tai_prefix = hien_tai.strftime("%Y-%m")

    # 1. Số đề nghị chờ duyệt (cả đơn < 100tr và đơn >= 100tr chờ lãnh đạo)
    row = db.execute("SELECT COUNT(*) AS cnt FROM de_nghi_mua_sam WHERE trang_thai IN ('cho_phe_duyet', 'cho_lanh_dao_duyet')").fetchone()
    so_de_nghi_cho_duyet = row["cnt"] if row else 0

    # 2. Số tài sản đang sử dụng
    row = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE trang_thai = 'dang_su_dung'").fetchone()
    so_tai_san_dang_su_dung = row["cnt"] if row else 0

    # 3. Phân loại tài sản: TSCĐ vs CCDC
    row_tscd = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE phan_loai = 'tai_san_co_dinh'").fetchone()
    so_tscd = row_tscd["cnt"] if row_tscd else 0
    row_ccdc = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE phan_loai = 'cong_cu_dung_cu'").fetchone()
    so_ccdc = row_ccdc["cnt"] if row_ccdc else 0

    # 4. Chi tiêu tháng này (từ bảng thanh_toan)
    row = db.execute(
        "SELECT SUM(so_tien) AS tong FROM thanh_toan WHERE ngay_thanh_toan LIKE ?",
        (f"{thang_hien_tai_prefix}%",)
    ).fetchone()
    chi_tieu_thang_nay = row["tong"] if (row and row["tong"]) else 0.0

    # 5. Số báo cáo hư hại chưa xử lý
    row = db.execute("SELECT COUNT(*) AS cnt FROM bao_cao_hu_hai WHERE trang_thai = 'chua_xu_ly'").fetchone()
    so_bao_cao_chua_xu_ly = row["cnt"] if row else 0

    # 6. Số yêu cầu sửa chữa đang xử lý (M09)
    try:
        row_sc = db.execute("SELECT COUNT(*) AS cnt FROM yeu_cau_sua_chua WHERE trang_thai = 'dang_sua_chua'").fetchone()
        so_sua_chua_dang_xu_ly = row_sc["cnt"] if row_sc else 0
    except Exception:
        so_sua_chua_dang_xu_ly = 0

    # 7. Phân bổ tình trạng tài sản (vẽ biểu đồ tròn)
    rows_trang_thai = db.execute(
        "SELECT trang_thai, COUNT(*) AS so_luong FROM tai_san GROUP BY trang_thai"
    ).fetchall()
    phan_bo_tai_san = {r["trang_thai"]: r["so_luong"] for r in rows_trang_thai}

    # 8. Biểu đồ tình hình mua sắm theo tháng (dựa trên ngân sách đề nghị đã tạo)
    rows_thang = db.execute(
        """
        SELECT substr(ngay_tao, 1, 7) AS thang,
               COUNT(*) AS so_de_nghi,
               SUM(tong_du_toan) AS tong_tien
        FROM de_nghi_mua_sam
        GROUP BY thang
        ORDER BY thang DESC
        LIMIT 6
        """
    ).fetchall()
    bieu_do_mua_sam = [dict(r) for r in reversed(rows_thang)]

    # 9. Đề nghị mua sắm gần đây
    rows_dn_moi = db.execute(
        """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        ORDER BY d.id DESC LIMIT 5
        """
    ).fetchall()
    de_nghi_gan_day = [dict(r) for r in rows_dn_moi]

    # 10. Tài sản mới tiếp nhận
    rows_ts_moi = db.execute(
        "SELECT * FROM tai_san ORDER BY id DESC LIMIT 5"
    ).fetchall()
    tai_san_gan_day = [dict(r) for r in rows_ts_moi]

    return {
        "so_de_nghi_cho_duyet": so_de_nghi_cho_duyet,
        "so_tai_san_dang_su_dung": so_tai_san_dang_su_dung,
        "so_tscd": so_tscd,
        "so_ccdc": so_ccdc,
        "chi_tieu_thang_nay": chi_tieu_thang_nay,
        "so_bao_cao_chua_xu_ly": so_bao_cao_chua_xu_ly,
        "so_sua_chua_dang_xu_ly": so_sua_chua_dang_xu_ly,
        "phan_bo_tai_san": phan_bo_tai_san,
        "bieu_do_mua_sam": bieu_do_mua_sam,
        "de_nghi_gan_day": de_nghi_gan_day,
        "tai_san_gan_day": tai_san_gan_day
    }

def bao_cao_mua_sam(tu_ngay: str = None, den_ngay: str = None) -> list:
    """Báo cáo danh sách mua sắm theo khoảng thời gian."""
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        WHERE 1=1
    """
    params = []
    if tu_ngay:
        query += " AND d.ngay_tao >= ?"
        params.append(tu_ngay)
    if den_ngay:
        query += " AND d.ngay_tao <= ?"
        params.append(den_ngay + "T23:59:59")

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def bao_cao_tai_san(trang_thai: str = None, phong_ban: str = None) -> list:
    """Báo cáo danh sách tài sản theo trạng thái và phòng ban."""
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
    if phong_ban:
        query += " AND t.phong_ban LIKE ?"
        params.append(f"%{phong_ban}%")

    query += " ORDER BY t.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def xuat_csv_mua_sam() -> str:
    """Xuất danh sách đề nghị mua sắm ra định dạng CSV (UTF-8 có BOM hỗ trợ tiếng Việt trong Excel)."""
    de_nghi_list = bao_cao_mua_sam()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Mã đề nghị", "Tiêu đề", "Đơn vị đề nghị", "Người đề nghị",
        "Tổng dự toán (VNĐ)", "Trạng thái", "Ngày tạo"
    ])

    for dn in de_nghi_list:
        writer.writerow([
            dn.get("ma_de_nghi", ""),
            dn.get("tieu_de", ""),
            dn.get("don_vi_de_nghi", ""),
            dn.get("nguoi_de_nghi_ten", ""),
            dn.get("tong_du_toan", 0),
            dn.get("trang_thai", ""),
            dn.get("ngay_tao", "")
        ])

    return "\ufeff" + output.getvalue()

def xuat_csv_tai_san() -> str:
    """Xuất danh sách tài sản ra định dạng CSV (UTF-8 có BOM hỗ trợ tiếng Việt trong Excel)."""
    tai_san_list = bao_cao_tai_san()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Mã tài sản", "Tên tài sản", "Phân loại", "Loại tài sản", "Vị trí",
        "Phòng ban", "Giá trị (VNĐ)", "Trạng thái", "Tình trạng kỹ thuật", "Người sử dụng", "Ngày tiếp nhận"
    ])

    for ts in tai_san_list:
        writer.writerow([
            ts.get("ma_tai_san", ""),
            ts.get("ten_tai_san", ""),
            ts.get("phan_loai", ""),
            ts.get("loai_tai_san", ""),
            ts.get("vi_tri", ""),
            ts.get("phong_ban", ""),
            ts.get("gia_tri", 0),
            ts.get("trang_thai", ""),
            ts.get("tinh_trang_ky_thuat", ""),
            ts.get("nguoi_su_dung_ten", ""),
            ts.get("ngay_tiep_nhan", "")
        ])

    return "\ufeff" + output.getvalue()
