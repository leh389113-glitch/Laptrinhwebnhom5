import os
import sqlite3
from flask import g, current_app

SCHEMA_SQL = """
-- Bảng người dùng
CREATE TABLE IF NOT EXISTS nguoi_dung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    ten_dang_nhap TEXT UNIQUE NOT NULL,
    mat_khau_hash TEXT NOT NULL,
    vai_tro TEXT NOT NULL DEFAULT 'nguoi_dung',
    chuc_danh TEXT,
    don_vi TEXT,
    so_dien_thoai TEXT,
    ngay_tao TEXT NOT NULL,
    trang_thai TEXT NOT NULL DEFAULT 'hoat_dong'
);

-- Bảng đề nghị mua sắm (M08)
CREATE TABLE IF NOT EXISTS de_nghi_mua_sam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_de_nghi TEXT UNIQUE NOT NULL,
    tieu_de TEXT NOT NULL,
    mo_ta TEXT,
    don_vi_de_nghi TEXT NOT NULL,
    nguoi_de_nghi_id INTEGER NOT NULL,
    tong_du_toan REAL NOT NULL DEFAULT 0,
    trang_thai TEXT NOT NULL DEFAULT 'cho_phe_duyet',
    ghi_chu_phe_duyet TEXT,
    nguoi_phe_duyet_id INTEGER,
    ngay_tao TEXT NOT NULL,
    ngay_phe_duyet TEXT,
    ngay_cap_nhat TEXT NOT NULL,
    nguon_goc TEXT DEFAULT 'moi',
    bao_cao_hu_hai_id INTEGER,
    muc_do_uu_tien TEXT DEFAULT 'binh_thuong',
    nguon_kinh_phi TEXT DEFAULT 'Nguồn thu hợp pháp của Trường',
    thoi_gian_can_hang TEXT,
    dia_diem_su_dung TEXT,
    ly_do_su_can_thiet TEXT,
    so_hop_dong TEXT,
    nha_cung_cap TEXT,
    gia_tri_hop_dong REAL DEFAULT 0,
    da_nghiem_thu INTEGER DEFAULT 0,
    ngay_nghiem_thu TEXT,
    ghi_chu_nghiem_thu TEXT,
    FOREIGN KEY (nguoi_de_nghi_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (nguoi_phe_duyet_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (bao_cao_hu_hai_id) REFERENCES bao_cao_hu_hai(id)
);

-- Bảng chi tiết đề nghị mua sắm (hạng mục hàng hóa)
CREATE TABLE IF NOT EXISTS chi_tiet_de_nghi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    ten_hang_hoa TEXT NOT NULL,
    don_vi_tinh TEXT NOT NULL,
    so_luong INTEGER NOT NULL,
    don_gia_du_kien REAL NOT NULL DEFAULT 0,
    thanh_tien REAL NOT NULL DEFAULT 0,
    vi_tri_su_dung TEXT,
    ly_do_muc_dich TEXT,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng biên bản khảo sát nhu cầu mua sắm (BM02 / BM01C)
CREATE TABLE IF NOT EXISTS khao_sat_nhu_cau (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_khao_sat TEXT UNIQUE NOT NULL,
    de_nghi_id INTEGER NOT NULL,
    noi_dung TEXT,
    ngay_khao_sat TEXT NOT NULL,
    dia_diem TEXT,
    can_bo_khao_sat TEXT,
    dai_dien_don_vi TEXT,
    ket_qua_danh_gia TEXT,
    kiem_tra_kho TEXT,
    doi_chieu_dinh_muc TEXT,
    muc_do_can_thiet TEXT DEFAULT 'can_thiet',
    phuong_an_de_xuat TEXT DEFAULT 'mua_bo_sung',
    ket_luan TEXT DEFAULT 'phu_hop',
    ngay_tao TEXT NOT NULL,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng báo giá cạnh tranh (tối thiểu 3 báo giá)
CREATE TABLE IF NOT EXISTS bao_gia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    nha_cung_cap TEXT NOT NULL,
    ma_so_thue TEXT,
    lien_he TEXT,
    tong_gia REAL NOT NULL DEFAULT 0,
    ngay_bao_gia TEXT NOT NULL,
    hieu_luc TEXT,
    duoc_chon INTEGER DEFAULT 0,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng hồ sơ mua sắm & hợp đồng
CREATE TABLE IF NOT EXISTS ho_so_mua_sam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    nha_cung_cap TEXT,
    so_hop_dong TEXT,
    gia_tri_hop_dong REAL DEFAULT 0,
    ngay_tao TEXT NOT NULL,
    dieu_khoan_thanh_toan TEXT,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng biên bản kiểm tra & nghiệm thu mua sắm
CREATE TABLE IF NOT EXISTS nghiem_thu_mua_sam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_nghiem_thu TEXT UNIQUE NOT NULL,
    de_nghi_id INTEGER NOT NULL,
    ngay_nghiem_thu TEXT NOT NULL,
    dai_dien_ben_mua TEXT,
    dai_dien_nha_cung_cap TEXT,
    dai_dien_don_vi_su_dung TEXT,
    ket_qua TEXT DEFAULT 'dat',
    y_kien_danh_gia TEXT,
    ngay_tao TEXT NOT NULL,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng tiếp nhận hàng hóa vào kho
CREATE TABLE IF NOT EXISTS tiep_nhan_hang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    ngay_tiep_nhan TEXT NOT NULL,
    nguoi_tiep_nhan_id INTEGER NOT NULL,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id),
    FOREIGN KEY (nguoi_tiep_nhan_id) REFERENCES nguoi_dung(id)
);

-- Bảng chi tiết tiếp nhận hàng
CREATE TABLE IF NOT EXISTS chi_tiet_tiep_nhan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tiep_nhan_id INTEGER NOT NULL,
    ten_hang_hoa TEXT NOT NULL,
    so_luong_thuc_nhan INTEGER NOT NULL,
    don_vi_tinh TEXT NOT NULL,
    tinh_trang TEXT DEFAULT 'tot',
    ghi_chu TEXT,
    FOREIGN KEY (tiep_nhan_id) REFERENCES tiep_nhan_hang(id)
);

-- Bảng thanh toán (Kế toán - M08)
CREATE TABLE IF NOT EXISTS thanh_toan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_thanh_toan TEXT UNIQUE,
    de_nghi_id INTEGER NOT NULL,
    nha_cung_cap TEXT,
    noi_dung_thanh_toan TEXT,
    gia_tri_de_nghi REAL DEFAULT 0,
    gia_tri_da_thanh_toan REAL DEFAULT 0,
    so_tien_con_lai REAL DEFAULT 0,
    ma_nghiem_thu TEXT,
    ho_so_dinh_kem TEXT,
    trang_thai TEXT DEFAULT 'cho_kiem_tra',
    so_tien REAL NOT NULL DEFAULT 0,
    ngay_de_nghi TEXT,
    nguoi_de_nghi_id INTEGER,
    ngay_thanh_toan TEXT,
    nguoi_thanh_toan_id INTEGER,
    phuong_thuc TEXT DEFAULT 'chuyen_khoan',
    so_hoa_don TEXT,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id),
    FOREIGN KEY (nguoi_de_nghi_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (nguoi_thanh_toan_id) REFERENCES nguoi_dung(id)
);

-- Bảng tài sản (M09 - Quản lý tài sản)
CREATE TABLE IF NOT EXISTS tai_san (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_tai_san TEXT UNIQUE NOT NULL,
    ten_tai_san TEXT NOT NULL,
    mo_ta TEXT,
    loai_tai_san TEXT,
    phan_loai TEXT DEFAULT 'tai_san_co_dinh',
    tinh_trang_ky_thuat TEXT DEFAULT 'binh_thuong',
    vi_tri TEXT,
    phong_ban TEXT,
    don_vi_su_dung TEXT,
    gia_tri REAL DEFAULT 0,
    ngay_tiep_nhan TEXT NOT NULL,
    nguoi_su_dung_id INTEGER,
    trang_thai TEXT NOT NULL DEFAULT 'cho_ban_giao',
    so_serial TEXT,
    model TEXT,
    hang_san_xuat TEXT,
    thoi_han_bao_hanh TEXT,
    de_nghi_id INTEGER,
    ngay_tao TEXT NOT NULL,
    ngay_cap_nhat TEXT NOT NULL,
    FOREIGN KEY (nguoi_su_dung_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng lịch sử bàn giao tài sản
CREATE TABLE IF NOT EXISTS lich_su_ban_giao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tai_san_id INTEGER NOT NULL,
    nguoi_nhan_id INTEGER NOT NULL,
    nguoi_ban_giao_id INTEGER NOT NULL,
    ngay_ban_giao TEXT NOT NULL,
    ghi_chu TEXT,
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id),
    FOREIGN KEY (nguoi_nhan_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (nguoi_ban_giao_id) REFERENCES nguoi_dung(id)
);

-- Bảng yêu cầu sửa chữa & bảo trì tài sản (M09 - Phần III)
CREATE TABLE IF NOT EXISTS yeu_cau_sua_chua (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_yeu_cau TEXT UNIQUE NOT NULL,
    tai_san_id INTEGER,
    bao_cao_hu_hai_id INTEGER,
    loai_sua_chua TEXT DEFAULT 'sua_chua_nho',
    noi_dung TEXT NOT NULL,
    hien_trang TEXT,
    chi_phi_du_kien REAL DEFAULT 0,
    chi_phi_thuc_te REAL DEFAULT 0,
    don_vi_thuc_hien TEXT,
    nguoi_phu_trach_id INTEGER,
    ngay_tiep_nhan TEXT NOT NULL,
    ngay_hoan_thanh TEXT,
    ket_qua_nghiem_thu TEXT DEFAULT 'cho_nghiem_thu',
    trang_thai TEXT DEFAULT 'dang_sua_chua',
    ghi_chu TEXT,
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id),
    FOREIGN KEY (bao_cao_hu_hai_id) REFERENCES bao_cao_hu_hai(id),
    FOREIGN KEY (nguoi_phu_trach_id) REFERENCES nguoi_dung(id)
);

-- Bảng lịch sử bảo trì tài sản
CREATE TABLE IF NOT EXISTS bao_tri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tai_san_id INTEGER NOT NULL,
    ngay_bao_tri TEXT NOT NULL,
    noi_dung TEXT NOT NULL,
    chi_phi REAL DEFAULT 0,
    don_vi_thuc_hien TEXT,
    nguoi_ghi_nhan_id INTEGER NOT NULL,
    ghi_chu TEXT,
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id),
    FOREIGN KEY (nguoi_ghi_nhan_id) REFERENCES nguoi_dung(id)
);

-- Bảng phiếu kiểm kê
CREATE TABLE IF NOT EXISTS phieu_kiem_ke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_phieu TEXT UNIQUE NOT NULL,
    ngay_kiem_ke TEXT NOT NULL,
    nguoi_kiem_ke_id INTEGER NOT NULL,
    trang_thai TEXT DEFAULT 'dang_kiem_ke',
    ghi_chu TEXT,
    ngay_tao TEXT NOT NULL,
    FOREIGN KEY (nguoi_kiem_ke_id) REFERENCES nguoi_dung(id)
);

-- Bảng chi tiết phiếu kiểm kê
CREATE TABLE IF NOT EXISTS chi_tiet_kiem_ke (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phieu_kiem_ke_id INTEGER NOT NULL,
    tai_san_id INTEGER NOT NULL,
    tinh_trang_thuc_te TEXT NOT NULL,
    so_luong_he_thong INTEGER DEFAULT 1,
    so_luong_thuc_te INTEGER DEFAULT 1,
    chenh_lech INTEGER DEFAULT 0,
    ghi_chu TEXT,
    FOREIGN KEY (phieu_kiem_ke_id) REFERENCES phieu_kiem_ke(id),
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id)
);

-- Bảng báo cáo hư hại vật chất (Public - không cần đăng nhập)
CREATE TABLE IF NOT EXISTS bao_cao_hu_hai (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_bao_cao TEXT,
    ho_ten TEXT NOT NULL,
    lien_he TEXT NOT NULL,
    ten_vat_chat TEXT NOT NULL,
    vi_tri TEXT NOT NULL,
    muc_do TEXT NOT NULL,
    mo_ta_chi_tiet TEXT,
    thoi_gian_phat_hien TEXT,
    trang_thai TEXT DEFAULT 'cho_tiep_nhan',
    phuong_an_xu_ly TEXT,
    nguoi_xu_ly_id INTEGER,
    ngay_xu_ly TEXT,
    ghi_chu_xu_ly TEXT,
    de_nghi_mua_sam_id INTEGER,
    tai_san_id INTEGER,
    ngay_tao TEXT NOT NULL,
    nguoi_gui_id INTEGER,
    loai_yeu_cau TEXT DEFAULT 'sua_chua_thiet_bi',
    do_khan_cap TEXT DEFAULT 'binh_thuong',
    don_vi TEXT,
    hinh_anh TEXT,
    xac_nhan_khao_sat_don_vi INTEGER DEFAULT 0,
    xac_nhan_nghiem_thu_don_vi INTEGER DEFAULT 0,
    ma_khao_sat TEXT,
    ngay_khao_sat TEXT,
    thanh_phan_khao_sat TEXT,
    hien_trang_thuc_te TEXT,
    nguyen_nhan_hu_hong TEXT,
    muc_do_hu_hong TEXT,
    anh_huong_an_toan TEXT,
    khoi_luong_du_kien TEXT,
    hinh_anh_khao_sat TEXT,
    nhom_sua_chua TEXT DEFAULT 'sua_chua_thiet_bi',
    tinh_trang_bao_hanh TEXT DEFAULT 'het_bao_hanh',
    phuong_an_chi_tiet TEXT,
    kinh_phi_du_kien REAL DEFAULT 0,
    nguon_kinh_phi_sua_chua TEXT,
    ngay_trinh_duyet TEXT,
    nguoi_duyet_phuong_an_id INTEGER,
    ngay_duyet_phuong_an TEXT,
    y_kien_lanh_dao TEXT,
    yeu_cau_m08 INTEGER DEFAULT 0,
    don_vi_thi_cong TEXT,
    ngay_bat_dau_sua TEXT,
    nhat_ky_thi_cong TEXT,
    hinh_anh_thi_cong TEXT,
    ma_nghiem_thu TEXT,
    ngay_nghiem_thu TEXT,
    ket_qua_nghiem_thu TEXT,
    y_kien_nghiem_thu TEXT,
    yeu_cau_khac_phuc TEXT,
    ly_do_tra_lai TEXT,
    FOREIGN KEY (nguoi_xu_ly_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (de_nghi_mua_sam_id) REFERENCES de_nghi_mua_sam(id),
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id)
);
"""

def get_db_path():
    return os.environ.get("CSV_DB", "csvc.db")

def get_db():
    """Lấy kết nối SQLite từ Flask application context."""
    db_path = get_db_path()
    if "db" not in g:
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Đóng kết nối SQLite khi kết thúc request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def _migrate_db(conn):
    """Thêm các cột mới vào các bảng hiện có nếu chưa có (migration an toàn không làm mất dữ liệu)."""
    cur = conn.cursor()
    
    # Bảng nguoi_dung
    try:
        cur.execute("PRAGMA table_info(nguoi_dung)")
        cols = [r[1] for r in cur.fetchall()]
        if "chuc_danh" not in cols:
            cur.execute("ALTER TABLE nguoi_dung ADD COLUMN chuc_danh TEXT")
        if "don_vi" not in cols:
            cur.execute("ALTER TABLE nguoi_dung ADD COLUMN don_vi TEXT")
        if "so_dien_thoai" not in cols:
            cur.execute("ALTER TABLE nguoi_dung ADD COLUMN so_dien_thoai TEXT")
    except Exception:
        pass

    # Bảng de_nghi_mua_sam
    try:
        cur.execute("PRAGMA table_info(de_nghi_mua_sam)")
        cols = [r[1] for r in cur.fetchall()]
        new_cols = [
            ("nguon_goc", "TEXT DEFAULT 'moi'"),
            ("bao_cao_hu_hai_id", "INTEGER"),
            ("muc_do_uu_tien", "TEXT DEFAULT 'binh_thuong'"),
            ("nguon_kinh_phi", "TEXT DEFAULT 'Nguồn thu hợp pháp của Trường'"),
            ("thoi_gian_can_hang", "TEXT"),
            ("dia_diem_su_dung", "TEXT"),
            ("ly_do_su_can_thiet", "TEXT"),
            ("so_hop_dong", "TEXT"),
            ("nha_cung_cap", "TEXT"),
            ("gia_tri_hop_dong", "REAL DEFAULT 0"),
            ("da_nghiem_thu", "INTEGER DEFAULT 0"),
            ("ngay_nghiem_thu", "TEXT"),
            ("ghi_chu_nghiem_thu", "TEXT"),
        ]
        for col_name, col_def in new_cols:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE de_nghi_mua_sam ADD COLUMN {col_name} {col_def}")
    except Exception:
        pass

    # Bảng chi_tiet_de_nghi
    try:
        cur.execute("PRAGMA table_info(chi_tiet_de_nghi)")
        cols = [r[1] for r in cur.fetchall()]
        if "vi_tri_su_dung" not in cols:
            cur.execute("ALTER TABLE chi_tiet_de_nghi ADD COLUMN vi_tri_su_dung TEXT")
        if "ly_do_muc_dich" not in cols:
            cur.execute("ALTER TABLE chi_tiet_de_nghi ADD COLUMN ly_do_muc_dich TEXT")
    except Exception:
        pass

    # Bảng tai_san
    try:
        cur.execute("PRAGMA table_info(tai_san)")
        cols = [r[1] for r in cur.fetchall()]
        new_ts_cols = [
            ("phan_loai", "TEXT DEFAULT 'tai_san_co_dinh'"),
            ("tinh_trang_ky_thuat", "TEXT DEFAULT 'binh_thuong'"),
            ("don_vi_su_dung", "TEXT"),
            ("so_serial", "TEXT"),
            ("model", "TEXT"),
            ("hang_san_xuat", "TEXT"),
            ("thoi_han_bao_hanh", "TEXT"),
            ("xac_nhan_ban_giao_don_vi", "INTEGER DEFAULT 1"),
        ]
        for col_name, col_def in new_ts_cols:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE tai_san ADD COLUMN {col_name} {col_def}")
    except Exception:
        pass

    # Bảng bao_cao_hu_hai
    try:
        cur.execute("PRAGMA table_info(bao_cao_hu_hai)")
        cols = [r[1] for r in cur.fetchall()]
        new_hh_cols = [
            ("ma_bao_cao", "TEXT"),
            ("nguoi_gui_id", "INTEGER"),
            ("loai_yeu_cau", "TEXT DEFAULT 'sua_chua_thiet_bi'"),
            ("do_khan_cap", "TEXT DEFAULT 'binh_thuong'"),
            ("don_vi", "TEXT"),
            ("hinh_anh", "TEXT"),
            ("xac_nhan_khao_sat_don_vi", "INTEGER DEFAULT 0"),
            ("xac_nhan_nghiem_thu_don_vi", "INTEGER DEFAULT 0"),
            ("phuong_an_xu_ly", "TEXT"),
            ("nguoi_xu_ly_id", "INTEGER"),
            ("ngay_xu_ly", "TEXT"),
            ("ghi_chu_xu_ly", "TEXT"),
            ("de_nghi_mua_sam_id", "INTEGER"),
            ("tai_san_id", "INTEGER"),
            ("ma_khao_sat", "TEXT"),
            ("ngay_khao_sat", "TEXT"),
            ("thanh_phan_khao_sat", "TEXT"),
            ("hien_trang_thuc_te", "TEXT"),
            ("nguyen_nhan_hu_hong", "TEXT"),
            ("muc_do_hu_hong", "TEXT"),
            ("anh_huong_an_toan", "TEXT"),
            ("khoi_luong_du_kien", "TEXT"),
            ("hinh_anh_khao_sat", "TEXT"),
            ("nhom_sua_chua", "TEXT DEFAULT 'sua_chua_thiet_bi'"),
            ("tinh_trang_bao_hanh", "TEXT DEFAULT 'het_bao_hanh'"),
            ("phuong_an_chi_tiet", "TEXT"),
            ("kinh_phi_du_kien", "REAL DEFAULT 0"),
            ("nguon_kinh_phi_sua_chua", "TEXT"),
            ("ngay_trinh_duyet", "TEXT"),
            ("nguoi_duyet_phuong_an_id", "INTEGER"),
            ("ngay_duyet_phuong_an", "TEXT"),
            ("y_kien_lanh_dao", "TEXT"),
            ("yeu_cau_m08", "INTEGER DEFAULT 0"),
            ("don_vi_thi_cong", "TEXT"),
            ("ngay_bat_dau_sua", "TEXT"),
            ("nhat_ky_thi_cong", "TEXT"),
            ("hinh_anh_thi_cong", "TEXT"),
            ("ma_nghiem_thu", "TEXT"),
            ("ngay_nghiem_thu", "TEXT"),
            ("ket_qua_nghiem_thu", "TEXT"),
            ("y_kien_nghiem_thu", "TEXT"),
            ("yeu_cau_khac_phuc", "TEXT"),
            ("ly_do_tra_lai", "TEXT"),
        ]
        for col_name, col_def in new_hh_cols:
            if col_name not in cols:
                cur.execute(f"ALTER TABLE bao_cao_hu_hai ADD COLUMN {col_name} {col_def}")
    except Exception:
        pass

    # Bảng de_nghi_mua_sam
    try:
        cur.execute("PRAGMA table_info(de_nghi_mua_sam)")
        cols = [r[1] for r in cur.fetchall()]
        if "xac_nhan_khao_sat_don_vi" not in cols:
            cur.execute("ALTER TABLE de_nghi_mua_sam ADD COLUMN xac_nhan_khao_sat_don_vi INTEGER DEFAULT 0")
        if "xac_nhan_nghiem_thu_don_vi" not in cols:
            cur.execute("ALTER TABLE de_nghi_mua_sam ADD COLUMN xac_nhan_nghiem_thu_don_vi INTEGER DEFAULT 0")
    except Exception:
        pass

    # Bảng chi_tiet_kiem_ke
    try:
        cur.execute("PRAGMA table_info(chi_tiet_kiem_ke)")
        cols = [r[1] for r in cur.fetchall()]
        if "so_luong_he_thong" not in cols:
            cur.execute("ALTER TABLE chi_tiet_kiem_ke ADD COLUMN so_luong_he_thong INTEGER DEFAULT 1")
        if "so_luong_thuc_te" not in cols:
            cur.execute("ALTER TABLE chi_tiet_kiem_ke ADD COLUMN so_luong_thuc_te INTEGER DEFAULT 1")
        if "chenh_lech" not in cols:
            cur.execute("ALTER TABLE chi_tiet_kiem_ke ADD COLUMN chenh_lech INTEGER DEFAULT 0")
        if "giai_trinh_don_vi" not in cols:
            cur.execute("ALTER TABLE chi_tiet_kiem_ke ADD COLUMN giai_trinh_don_vi TEXT")
        if "trang_thai_giai_trinh" not in cols:
            cur.execute("ALTER TABLE chi_tiet_kiem_ke ADD COLUMN trang_thai_giai_trinh TEXT")
    except Exception:
        pass

    cur.execute("PRAGMA table_info(thanh_toan)")
    cols = [row[1] for row in cur.fetchall()]
    new_tt_cols = [
        ("ma_thanh_toan", "TEXT"),
        ("nha_cung_cap", "TEXT"),
        ("noi_dung_thanh_toan", "TEXT"),
        ("gia_tri_de_nghi", "REAL DEFAULT 0"),
        ("gia_tri_da_thanh_toan", "REAL DEFAULT 0"),
        ("so_tien_con_lai", "REAL DEFAULT 0"),
        ("ma_nghiem_thu", "TEXT"),
        ("ho_so_dinh_kem", "TEXT"),
        ("trang_thai", "TEXT DEFAULT 'cho_kiem_tra'"),
        ("ngay_de_nghi", "TEXT"),
        ("nguoi_de_nghi_id", "INTEGER"),
    ]
    for col_name, col_def in new_tt_cols:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE thanh_toan ADD COLUMN {col_name} {col_def}")

    # Keep historical payments marked as paid and permit new rows to remain unpaid
    # until M08 submits them to Accounting.
    cur.execute(
        """
        UPDATE thanh_toan
        SET trang_thai = 'da_thanh_toan',
            gia_tri_de_nghi = CASE WHEN gia_tri_de_nghi = 0 THEN so_tien ELSE gia_tri_de_nghi END,
            gia_tri_da_thanh_toan = CASE WHEN gia_tri_da_thanh_toan = 0 THEN so_tien ELSE gia_tri_da_thanh_toan END,
            so_tien_con_lai = 0
        WHERE ma_thanh_toan IS NULL
          AND ngay_thanh_toan IS NOT NULL
          AND ngay_thanh_toan != ''
          AND nguoi_thanh_toan_id IS NOT NULL
        """
    )

    cur.execute("PRAGMA table_info(thanh_toan)")
    payment_columns = {row[1]: row for row in cur.fetchall()}
    if payment_columns["ngay_thanh_toan"][3] or payment_columns["nguoi_thanh_toan_id"][3]:
        cur.execute(
            """
            CREATE TABLE thanh_toan_migration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ma_thanh_toan TEXT UNIQUE,
                de_nghi_id INTEGER NOT NULL,
                nha_cung_cap TEXT,
                noi_dung_thanh_toan TEXT,
                gia_tri_de_nghi REAL DEFAULT 0,
                gia_tri_da_thanh_toan REAL DEFAULT 0,
                so_tien_con_lai REAL DEFAULT 0,
                ma_nghiem_thu TEXT,
                ho_so_dinh_kem TEXT,
                trang_thai TEXT DEFAULT 'cho_kiem_tra',
                so_tien REAL NOT NULL DEFAULT 0,
                ngay_de_nghi TEXT,
                nguoi_de_nghi_id INTEGER,
                ngay_thanh_toan TEXT,
                nguoi_thanh_toan_id INTEGER,
                phuong_thuc TEXT DEFAULT 'chuyen_khoan',
                so_hoa_don TEXT,
                ghi_chu TEXT,
                FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id),
                FOREIGN KEY (nguoi_de_nghi_id) REFERENCES nguoi_dung(id),
                FOREIGN KEY (nguoi_thanh_toan_id) REFERENCES nguoi_dung(id)
            )
            """
        )
        cur.execute(
            """
            INSERT INTO thanh_toan_migration (
                id, ma_thanh_toan, de_nghi_id, nha_cung_cap, noi_dung_thanh_toan,
                gia_tri_de_nghi, gia_tri_da_thanh_toan, so_tien_con_lai,
                ma_nghiem_thu, ho_so_dinh_kem, trang_thai, so_tien,
                ngay_de_nghi, nguoi_de_nghi_id, ngay_thanh_toan,
                nguoi_thanh_toan_id, phuong_thuc, so_hoa_don, ghi_chu
            )
            SELECT
                id, ma_thanh_toan, de_nghi_id, nha_cung_cap, noi_dung_thanh_toan,
                gia_tri_de_nghi, gia_tri_da_thanh_toan, so_tien_con_lai,
                ma_nghiem_thu, ho_so_dinh_kem, trang_thai, so_tien,
                ngay_de_nghi, nguoi_de_nghi_id, ngay_thanh_toan,
                nguoi_thanh_toan_id, phuong_thuc, so_hoa_don, ghi_chu
            FROM thanh_toan
            """
        )
        cur.execute("DROP TABLE thanh_toan")
        cur.execute("ALTER TABLE thanh_toan_migration RENAME TO thanh_toan")

    # Bổ sung các cột hồ sơ thanh toán công vụ cho bảng thanh_toan
    try:
        cur.execute("PRAGMA table_info(thanh_toan)")
        tt_cols = [r[1] for r in cur.fetchall()]
        new_tt_cols = [
            ("so_tien_bang_chu", "TEXT"),
            ("don_vi_thu_huong", "TEXT"),
            ("so_tai_khoan", "TEXT"),
            ("ngan_hang", "TEXT"),
            ("hop_dong_so", "TEXT"),
            ("hop_dong_ngay", "TEXT"),
            ("nguoi_de_nghi_ten", "TEXT"),
            ("don_vi", "TEXT"),
            ("ve_khoan", "TEXT"),
            ("ho_so_kem_theo", "TEXT")
        ]
        for col_name, col_def in new_tt_cols:
            if col_name not in tt_cols:
                cur.execute(f"ALTER TABLE thanh_toan ADD COLUMN {col_name} {col_def}")
    except Exception:
        pass

    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_thanh_toan_ma
        ON thanh_toan(ma_thanh_toan)
        WHERE ma_thanh_toan IS NOT NULL
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_thanh_toan_de_nghi
        ON thanh_toan(de_nghi_id)
        WHERE ma_thanh_toan IS NOT NULL
        """
    )

def init_db(db_conn=None):
    """Khởi tạo toàn bộ bảng nếu chưa tồn tại và chạy migration cập nhật cấu trúc."""
    conn = db_conn or get_db()
    conn.executescript(SCHEMA_SQL)
    _migrate_db(conn)
    conn.commit()
