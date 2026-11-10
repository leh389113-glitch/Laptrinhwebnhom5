from app.db import get_db
from app import clock
from app.errors import LoiNghiepVu
from app.services import mua_sam as ms_svc
from app.services import tai_san as ts_svc

def sinh_ma_yeu_cau() -> str:
    """Sinh mã yêu cầu sửa chữa tự động YC-YYYYMMDD-XXX."""
    db = get_db()
    hien_tai = clock.now()
    ngay_str = hien_tai.strftime("%Y%m%d")
    prefix = f"YC-{ngay_str}-"

    row = db.execute(
        "SELECT ma_yeu_cau FROM yeu_cau_sua_chua WHERE ma_yeu_cau LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()

    if row and row["ma_yeu_cau"]:
        phan_duoi = row["ma_yeu_cau"].split("-")[-1]
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
            SUM(CASE WHEN trang_thai IN (
                'cho_tiep_nhan', 'tra_lai', 'cho_khao_sat', 'dang_khao_sat', 'cho_duyet_phuong_an',
                'cho_thu_tuc_m08', 'dang_sua_chua', 'cho_nghiem_thu', 'khong_dat_yeu_cau',
                'cho_lap_ho_so_thanh_toan', 'cho_thanh_toan', 'dang_xu_ly_thanh_toan',
                'yeu_cau_bo_sung_ho_so'
            ) THEN 1 ELSE 0 END) AS dang_xu_ly,
            SUM(CASE WHEN trang_thai IN ('da_thanh_toan', 'da_hoan_thanh', 'da_xu_ly') THEN 1 ELSE 0 END) AS da_hoan_thanh
        FROM yeu_cau_sua_chua
        WHERE don_vi LIKE ? OR nguoi_tao_id = ?
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

def lay_danh_sach_sua_chua_don_vi(don_vi: str, nguoi_dung_id: int = None, trang_thai: str = None) -> list:
    """Lấy danh sách các yêu cầu sửa chữa thuộc đơn vị."""
    db = get_db()
    query = """
        SELECT sc.*, t.ma_tai_san, t.ten_tai_san AS ten_tai_san_goc
        FROM yeu_cau_sua_chua sc
        LEFT JOIN tai_san t ON sc.tai_san_id = t.id
        WHERE (sc.don_vi LIKE ? OR sc.nguoi_tao_id = ?)
    """
    params = [f"%{don_vi}%", nguoi_dung_id]

    if trang_thai:
        query += " AND sc.trang_thai = ?"
        params.append(trang_thai)

    query += " ORDER BY sc.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def lay_chi_tiet_sua_chua(id: int) -> dict:
    """Xem chi tiết một phiếu sửa chữa và tiến trình thực hiện."""
    return ts_svc.lay_chi_tiet_sua_chua(id)

def lay_chi_tiet_tai_san_don_vi(tai_san_id: int, don_vi: str) -> dict:
    """Chỉ trả chi tiết tài sản được gán cho hoặc bàn giao tới đơn vị."""
    row = get_db().execute(
        """
        SELECT 1
        FROM tai_san t
        LEFT JOIN nguoi_dung nguoi_nhan ON nguoi_nhan.id = t.nguoi_su_dung_id
        WHERE t.id = ?
          AND (
              t.don_vi_su_dung LIKE ?
              OR t.phong_ban LIKE ?
              OR nguoi_nhan.don_vi LIKE ?
          )
        """,
        (tai_san_id, f"%{don_vi}%", f"%{don_vi}%", f"%{don_vi}%")
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Tài sản không thuộc danh mục quản lý của đơn vị.")
    return ts_svc.lay_chi_tiet_tai_san(tai_san_id)

def lay_chi_tiet_sua_chua_cua_don_vi(id: int, don_vi: str, nguoi_dung_id: int) -> dict:
    """Chỉ cho phép đơn vị xem phiếu do đơn vị hoặc cán bộ của mình tạo."""
    db = get_db()
    row = db.execute(
        """
        SELECT 1 FROM yeu_cau_sua_chua
        WHERE id = ? AND (don_vi = ? OR nguoi_tao_id = ?)
        """,
        (id, don_vi, nguoi_dung_id)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Bạn không có quyền xem yêu cầu sửa chữa này.")
    return ts_svc.lay_chi_tiet_sua_chua(id)

def xac_nhan_khao_sat_sua_chua(id: int, nguoi_dung_id: int, ghi_chu: str = "",
                               don_vi: str = None) -> dict:
    """Đơn vị ký/xác nhận kết quả khảo sát yêu cầu sửa chữa (BM03)."""
    db = get_db()
    row = db.execute(
        "SELECT trang_thai FROM yeu_cau_sua_chua WHERE id = ? AND (nguoi_tao_id = ? OR don_vi = ?)",
        (id, nguoi_dung_id, don_vi)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Bạn không có quyền xác nhận yêu cầu sửa chữa này.")
    if row["trang_thai"] not in ("dang_khao_sat", "cho_duyet_phuong_an", "cho_thu_tuc_m08", "dang_sua_chua", "cho_nghiem_thu"):
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Biên bản khảo sát chưa sẵn sàng để xác nhận.")
    db.execute("UPDATE yeu_cau_sua_chua SET xac_nhan_khao_sat_don_vi = 1 WHERE id = ?", (id,))
    ts_svc.ghi_lich_su_sua_chua(
        id, "xac_nhan_khao_sat", "Đơn vị xác nhận biên bản khảo sát (BM03)",
        ghi_chu, nguoi_dung_id
    )
    db.commit()
    return lay_chi_tiet_sua_chua(id)

def xac_nhan_nghiem_thu_sua_chua(id: int, nguoi_dung_id: int, ghi_chu: str = "",
                                 ket_qua: str = "dat", don_vi: str = None) -> dict:
    """Đơn vị ký nghiệm thu đạt hoặc yêu cầu thi công khắc phục lại."""
    db = get_db()
    row = db.execute(
        "SELECT 1 FROM yeu_cau_sua_chua WHERE id = ? AND (nguoi_tao_id = ? OR don_vi = ?)",
        (id, nguoi_dung_id, don_vi)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Bạn không có quyền nghiệm thu yêu cầu sửa chữa này.")
    if ket_qua not in ("dat", "khong_dat"):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kết quả nghiệm thu không hợp lệ.")
    return ts_svc.xac_nhan_nghiem_thu_sua_chua(
        id, {"ghi_chu": ghi_chu, "ket_qua": ket_qua}, nguoi_dung_id
    )

def bo_sung_yeu_cau_sua_chua(id: int, nguoi_dung_id: int, noi_dung: str,
                             don_vi: str = None) -> dict:
    db = get_db()
    row = db.execute(
        "SELECT trang_thai FROM yeu_cau_sua_chua WHERE id = ? AND (nguoi_tao_id = ? OR don_vi = ?)",
        (id, nguoi_dung_id, don_vi)
    ).fetchone()
    if not row:
        raise LoiNghiepVu("KHONG_DU_QUYEN", "Bạn không có quyền bổ sung yêu cầu sửa chữa này.")
    if row["trang_thai"] != "tra_lai":
        raise LoiNghiepVu("TRANG_THAI_KHONG_HOP_LE", "Phiếu hiện không chờ bổ sung thông tin.")
    if not noi_dung.strip():
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng nhập thông tin bổ sung.")
    db.execute(
        """
        UPDATE yeu_cau_sua_chua
        SET trang_thai = 'cho_tiep_nhan', noi_dung = ?, ly_do_tra_lai = NULL
        WHERE id = ?
        """,
        (noi_dung.strip(), id)
    )
    ts_svc.ghi_lich_su_sua_chua(
        id, "bo_sung_thong_tin", "Đơn vị đã bổ sung thông tin",
        noi_dung.strip(), nguoi_dung_id, trang_thai="cho_tiep_nhan"
    )
    db.commit()
    return lay_chi_tiet_sua_chua(id)

# =========================================================================
# ĐỀ XUẤT MUA SẮM CỦA ĐƠN VỊ
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
        SELECT DISTINCT t.*
        FROM tai_san t
        LEFT JOIN nguoi_dung nguoi_nhan ON nguoi_nhan.id = t.nguoi_su_dung_id
        WHERE (
            t.don_vi_su_dung LIKE ?
            OR t.phong_ban LIKE ?
            OR nguoi_nhan.don_vi LIKE ?
        )
    """
    params = [f"%{don_vi}%", f"%{don_vi}%", f"%{don_vi}%"]

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
    cursor = db.execute(
        """
        UPDATE tai_san 
        SET xac_nhan_ban_giao_don_vi = 1,
            ngay_cap_nhat = ?
        WHERE id = ?
          AND xac_nhan_ban_giao_don_vi = 0
          AND EXISTS (
              SELECT 1
              FROM nguoi_dung nguoi_nhan
              WHERE nguoi_nhan.id = tai_san.nguoi_su_dung_id
                AND nguoi_nhan.vai_tro = 'don_vi'
                AND nguoi_nhan.don_vi = ?
          )
        """,
        (ngay_gio, tai_san_id, user.get("don_vi"))
    )
    if cursor.rowcount != 1:
        raise LoiNghiepVu(
            "KHONG_DU_QUYEN",
            "Tài sản này chưa được bàn giao cho đơn vị của bạn hoặc đã được xác nhận."
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
