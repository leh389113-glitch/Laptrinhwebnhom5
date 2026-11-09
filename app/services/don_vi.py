import sqlite3
from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu
from app.services import mua_sam as ms_svc
from app.services import tai_san as ts_svc

def sinh_ma_yeu_cau() -> str:
    """Sinh mã yêu cầu sửa chữa / báo cáo hư hại tự động YC-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"YC-{ngay_str}-"

    row = db.execute(
        "SELECT ma_bao_cao FROM bao_cao_hu_hai WHERE ma_bao_cao LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row and row["ma_bao_cao"]:
        phan_duoi = row["ma_bao_cao"].split("-")[-1]
        try:
            so_tt = int(phan_duoi) + 1
        except ValueError:
            so_tt = 1
    else:
        so_tt = 1

    return f"{prefix}{so_tt:03d}"

def lay_thong_ke_don_vi(don_vi: str, nguoi_dung_id: int = None) -> dict:
    """Thống kê tổng quan dành cho Dashboard của Đơn vị sử dụng."""
    db = get_db()
    
    # Tài sản của đơn vị
    cur_ts = db.execute(
        """
        SELECT 
            COUNT(*) AS tong_so,
            COALESCE(SUM(gia_tri), 0) AS tong_gia_tri,
            SUM(CASE WHEN tinh_trang_ky_thuat = 'co_hu_hong' THEN 1 ELSE 0 END) AS so_hu_hong,
            SUM(CASE WHEN trang_thai = 'dang_sua_chua' THEN 1 ELSE 0 END) AS so_dang_sua,
            SUM(CASE WHEN xac_nhan_ban_giao_don_vi = 0 THEN 1 ELSE 0 END) AS cho_ban_giao
        FROM tai_san
        WHERE don_vi_su_dung LIKE ? OR phong_ban LIKE ?
        """,
        (f"%{don_vi}%", f"%{don_vi}%")
    )
    thong_ke_ts = cur_ts.fetchone()

    # Yêu cầu sửa chữa của đơn vị
    cur_sc = db.execute(
        """
        SELECT 
            COUNT(*) AS tong_sc,
            SUM(CASE WHEN trang_thai IN ('cho_tiep_nhan', 'dang_xu_ly') THEN 1 ELSE 0 END) AS dang_xu_ly,
            SUM(CASE WHEN trang_thai = 'da_xu_ly' THEN 1 ELSE 0 END) AS da_hoan_thanh
        FROM bao_cao_hu_hai
        WHERE don_vi LIKE ? OR nguoi_gui_id = ?
        """,
        (f"%{don_vi}%", nguoi_dung_id)
    )
    thong_ke_sc = cur_sc.fetchone()

    # Đề xuất mua sắm của đơn vị
    cur_ms = db.execute(
        """
        SELECT 
            COUNT(*) AS tong_ms,
            SUM(CASE WHEN trang_thai IN ('cho_phe_duyet', 'cho_lanh_dao_duyet') THEN 1 ELSE 0 END) AS cho_duyet,
            SUM(CASE WHEN trang_thai IN ('da_phe_duyet', 'dang_mua') THEN 1 ELSE 0 END) AS dang_trien_khai,
            SUM(CASE WHEN trang_thai = 'hoan_tat' THEN 1 ELSE 0 END) AS da_hoan_tat
        FROM de_nghi_mua_sam
        WHERE don_vi_de_nghi LIKE ? OR nguoi_de_nghi_id = ?
        """,
        (f"%{don_vi}%", nguoi_dung_id)
    )
    thong_ke_ms = cur_ms.fetchone()

    return {
        "tai_san": dict(thong_ke_ts) if thong_ke_ts else {},
        "sua_chua": dict(thong_ke_sc) if thong_ke_sc else {},
        "mua_sam": dict(thong_ke_ms) if thong_ke_ms else {}
    }

# =========================================================================
# NHÓM 1: YÊU CẦU SỬA CHỮA & BÁO CÁO HƯ HẠI
# =========================================================================

def tao_yeu_cau_sua_chua(du_lieu: dict, user: dict) -> dict:
    """Tạo phiếu báo cáo hư hại / Yêu cầu sửa chữa từ tài khoản Đơn vị sử dụng."""
    db = get_db()
    ma_yc = sinh_ma_yeu_cau()
    ngay_tao = clock.now().strftime("%Y-%m-%d %H:%M:%S")

    ho_ten = user.get("ho_ten", "")
    lien_he = user.get("so_dien_thoai") or user.get("email") or ""
    don_vi = user.get("don_vi") or du_lieu.get("don_vi") or ""
    
    tai_san_id = du_lieu.get("tai_san_id")
    if tai_san_id:
        try:
            tai_san_id = int(tai_san_id)
        except ValueError:
            tai_san_id = None

    cursor = db.execute(
        """
        INSERT INTO bao_cao_hu_hai (
            ma_bao_cao, nguoi_gui_id, ho_ten, lien_he, don_vi,
            ten_vat_chat, vi_tri, loai_yeu_cau, do_khan_cap,
            muc_do, mo_ta_chi_tiet, tai_san_id, trang_thai,
            thoi_gian_phat_hien, hinh_anh, ngay_tao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'cho_tiep_nhan', ?, ?, ?)
        """,
        (
            ma_yc,
            user.get("id"),
            ho_ten,
            lien_he,
            don_vi,
            du_lieu.get("ten_vat_chat", ""),
            du_lieu.get("vi_tri", ""),
            du_lieu.get("loai_yeu_cau", "sua_chua_thiet_bi"),
            du_lieu.get("do_khan_cap", "binh_thuong"),
            du_lieu.get("muc_do", "trung_binh"),
            du_lieu.get("mo_ta_chi_tiet", ""),
            tai_san_id,
            du_lieu.get("thoi_gian_phat_hien") or ngay_tao,
            du_lieu.get("hinh_anh", ""),
            ngay_tao
        )
    )

    # Nếu có gắn với tài sản cụ thể, đánh dấu tài sản có hư hỏng
    if tai_san_id:
        db.execute(
            "UPDATE tai_san SET tinh_trang_ky_thuat = 'co_hu_hong', ngay_cap_nhat = ? WHERE id = ?",
            (ngay_tao, tai_san_id)
        )

    db.commit()
    report_id = cursor.lastrowid
    return lay_chi_tiet_sua_chua(report_id)

def lay_danh_sach_sua_chua_don_vi(don_vi: str, nguoi_dung_id: int = None, trang_thai: str = None) -> list:
    """Lấy danh sách các yêu cầu sửa chữa thuộc đơn vị."""
    db = get_db()
    query = """
        SELECT b.*, t.ma_tai_san, t.ten_tai_san AS ten_tai_san_goc
        FROM bao_cao_hu_hai b
        LEFT JOIN tai_san t ON b.tai_san_id = t.id
        WHERE (b.don_vi LIKE ? OR b.nguoi_gui_id = ?)
    """
    params = [f"%{don_vi}%", nguoi_dung_id]

    if trang_thai:
        query += " AND b.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY b.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_sua_chua(id: int) -> dict:
    """Xem chi tiết một phiếu sửa chữa và tiến trình thực hiện."""
    db = get_db()
    row = db.execute(
        """
        SELECT b.*, t.ma_tai_san, t.ten_tai_san, t.loai_tai_san,
               u_gui.ho_ten AS nguoi_gui_ten, u_gui.email AS nguoi_gui_email,
               u_xl.ho_ten AS nguoi_xu_ly_ten
        FROM bao_cao_hu_hai b
        LEFT JOIN tai_san t ON b.tai_san_id = t.id
        LEFT JOIN nguoi_dung u_gui ON b.nguoi_gui_id = u_gui.id
        LEFT JOIN nguoi_dung u_xl ON b.nguoi_xu_ly_id = u_xl.id
        WHERE b.id = ?
        """,
        (id,)
    ).fetchone()

    if not row:
        raise LoiNghiepVu("YEU_CAU_KHONG_TON_TAI", "Không tìm thấy yêu cầu sửa chữa.")

    res = dict(row)

    # Lấy thông tin ca sửa chữa thực tế M09 nếu đã có
    sc_row = db.execute(
        "SELECT * FROM yeu_cau_sua_chua WHERE bao_cao_hu_hai_id = ? ORDER BY id DESC LIMIT 1",
        (id,)
    ).fetchone()
    res["ca_sua_chua"] = dict(sc_row) if sc_row else None

    return res

def xac_nhan_khao_sat_sua_chua(id: int, nguoi_dung_id: int, ghi_chu: str = "") -> dict:
    """Đơn vị ký/xác nhận kết quả khảo sát hiện trạng hư hỏng (BM03)."""
    db = get_db()
    db.execute(
        "UPDATE bao_cao_hu_hai SET xac_nhan_khao_sat_don_vi = 1, ghi_chu_xu_ly = COALESCE(ghi_chu_xu_ly, '') || ? WHERE id = ?",
        (f" [Đơn vị xác nhận khảo sát: {ghi_chu}]", id)
    )
    db.commit()
    return lay_chi_tiet_sua_chua(id)

def xac_nhan_nghiem_thu_sua_chua(id: int, nguoi_dung_id: int, ghi_chu: str = "") -> dict:
    """Đơn vị ký/xác nhận biên bản nghiệm thu sửa chữa hoàn thành."""
    db = get_db()
    db.execute(
        "UPDATE bao_cao_hu_hai SET xac_nhan_nghiem_thu_don_vi = 1, trang_thai = 'da_xu_ly', ghi_chu_xu_ly = COALESCE(ghi_chu_xu_ly, '') || ? WHERE id = ?",
        (f" [Đơn vị nghiệm thu đạt yêu cầu: {ghi_chu}]", id)
    )
    db.commit()
    return lay_chi_tiet_sua_chua(id)

# =========================================================================
# NHÓM 2: ĐỀ XUẤT MUA SẮM CỦA ĐƠN VỊ
# =========================================================================

def lay_danh_sach_de_xuat_don_vi(don_vi: str, nguoi_dung_id: int = None, trang_thai: str = None) -> list:
    """Lấy danh sách đề xuất mua sắm do đơn vị này lập."""
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        WHERE (d.don_vi_de_nghi LIKE ? OR d.nguoi_de_nghi_id = ?)
    """
    params = [f"%{don_vi}%", nguoi_dung_id]

    if trang_thai:
        query += " AND d.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def xac_nhan_khao_sat_mua_sam(de_nghi_id: int, nguoi_dung_id: int, ghi_chu: str = "") -> None:
    """Đơn vị ký/xác nhận biên bản khảo sát nhu cầu mua sắm thực tế (BM02)."""
    db = get_db()
    db.execute(
        "UPDATE de_nghi_mua_sam SET xac_nhan_khao_sat_don_vi = 1 WHERE id = ?",
        (de_nghi_id,)
    )
    db.commit()

def xac_nhan_nghiem_thu_mua_sam(de_nghi_id: int, nguoi_dung_id: int, ghi_chu: str = "") -> None:
    """Đại diện đơn vị ký xác nhận tham gia nghiệm thu hàng hóa mua sắm."""
    db = get_db()
    db.execute(
        "UPDATE de_nghi_mua_sam SET xac_nhan_nghiem_thu_don_vi = 1 WHERE id = ?",
        (de_nghi_id,)
    )
    db.commit()

# =========================================================================
# NHÓM 3: DANH MỤC TÀI SẢN CỦA ĐƠN VỊ
# =========================================================================

def lay_danh_sach_tai_san_don_vi(don_vi: str, tu_khoa: str = None, vi_tri: str = None, tinh_trang: str = None, cho_xac_nhan: bool = False) -> list:
    """Lấy danh sách tài sản được gán cho đơn vị."""
    db = get_db()
    query = """
        SELECT t.*
        FROM tai_san t
        WHERE (t.don_vi_su_dung LIKE ? OR t.phong_ban LIKE ?)
    """
    params = [f"%{don_vi}%", f"%{don_vi}%"]

    if tu_khoa:
        query += " AND (t.ten_tai_san LIKE ? OR t.ma_tai_san LIKE ?)"
        params.extend([f"%{tu_khoa}%", f"%{tu_khoa}%"])

    if vi_tri:
        query += " AND t.vi_tri LIKE ?"
        params.append(f"%{vi_tri}%")

    if tinh_trang:
        query += " AND t.tinh_trang_ky_thuat = ?"
        params.append(tinh_trang)

    if cho_xac_nhan:
        query += " AND t.xac_nhan_ban_giao_don_vi = 0"

    query += " ORDER BY t.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def xac_nhan_ban_giao_tai_san(tai_san_id: int, user: dict, ghi_chu: str = "") -> None:
    """Đơn vị xác nhận tiếp nhận bàn giao tài sản mới từ Phòng QTTB."""
    db = get_db()
    ngay_gio = clock.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        """
        UPDATE tai_san 
        SET xac_nhan_ban_giao_don_vi = 1,
            trang_thai = 'dang_su_dung',
            nguoi_su_dung_id = ?,
            ngay_cap_nhat = ?
        WHERE id = ?
        """,
        (user.get("id"), ngay_gio, tai_san_id)
    )
    db.commit()

# =========================================================================
# NHÓM 4: KIỂM KÊ & GIẢI TRÌNH CHÊNH LỆCH
# =========================================================================

def lay_danh_sach_kiem_ke_don_vi(don_vi: str) -> list:
    """Lấy danh sách các đợt kiểm kê có liên quan đến tài sản của đơn vị."""
    db = get_db()
    query = """
        SELECT DISTINCT p.*, u.ho_ten AS nguoi_kiem_ke_ten
        FROM phieu_kiem_ke p
        JOIN chi_tiet_kiem_ke c ON p.id = c.phieu_kiem_ke_id
        JOIN tai_san t ON c.tai_san_id = t.id
        LEFT JOIN nguoi_dung u ON p.nguoi_kiem_ke_id = u.id
        WHERE (t.don_vi_su_dung LIKE ? OR t.phong_ban LIKE ?)
        ORDER BY p.id DESC
    """
    rows = db.execute(query, (f"%{don_vi}%", f"%{don_vi}%")).fetchall()
    
    result = []
    for r in rows:
        d = dict(r)
        # Lấy chi tiết tài sản của đơn vị trong đợt kiểm kê này
        cur_ct = db.execute(
            """
            SELECT c.*, t.ma_tai_san, t.ten_tai_san, t.vi_tri
            FROM chi_tiet_kiem_ke c
            JOIN tai_san t ON c.tai_san_id = t.id
            WHERE c.phieu_kiem_ke_id = ? AND (t.don_vi_su_dung LIKE ? OR t.phong_ban LIKE ?)
            """,
            (d["id"], f"%{don_vi}%", f"%{don_vi}%")
        )
        d["chi_tiet"] = [dict(ct) for ct in cur_ct.fetchall()]
        result.append(d)

    return result

def gui_giai_trinh_kiem_ke(chi_tiet_id: int, noi_dung: str) -> None:
    """Gửi phản hồi / giải trình chênh lệch kiểm kê tài sản."""
    db = get_db()
    db.execute(
        """
        UPDATE chi_tiet_kiem_ke
        SET giai_trinh_don_vi = ?, trang_thai_giai_trinh = 'da_giai_trinh'
        WHERE id = ?
        """,
        (noi_dung, chi_tiet_id)
    )
    db.commit()

