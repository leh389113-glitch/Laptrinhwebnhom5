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
    FOREIGN KEY (nguoi_de_nghi_id) REFERENCES nguoi_dung(id),
    FOREIGN KEY (nguoi_phe_duyet_id) REFERENCES nguoi_dung(id)
);

-- Bảng chi tiết đề nghị mua sắm
CREATE TABLE IF NOT EXISTS chi_tiet_de_nghi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    ten_hang_hoa TEXT NOT NULL,
    don_vi_tinh TEXT NOT NULL,
    so_luong INTEGER NOT NULL,
    don_gia_du_kien REAL NOT NULL DEFAULT 0,
    thanh_tien REAL NOT NULL DEFAULT 0,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng hồ sơ mua sắm
CREATE TABLE IF NOT EXISTS ho_so_mua_sam (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    de_nghi_id INTEGER NOT NULL,
    nha_cung_cap TEXT,
    so_hop_dong TEXT,
    gia_tri_hop_dong REAL DEFAULT 0,
    ngay_tao TEXT NOT NULL,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id)
);

-- Bảng tiếp nhận hàng
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
    de_nghi_id INTEGER NOT NULL,
    so_tien REAL NOT NULL,
    ngay_thanh_toan TEXT NOT NULL,
    nguoi_thanh_toan_id INTEGER NOT NULL,
    phuong_thuc TEXT DEFAULT 'chuyen_khoan',
    so_hoa_don TEXT,
    ghi_chu TEXT,
    FOREIGN KEY (de_nghi_id) REFERENCES de_nghi_mua_sam(id),
    FOREIGN KEY (nguoi_thanh_toan_id) REFERENCES nguoi_dung(id)
);

-- Bảng tài sản (M09)
CREATE TABLE IF NOT EXISTS tai_san (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ma_tai_san TEXT UNIQUE NOT NULL,
    ten_tai_san TEXT NOT NULL,
    mo_ta TEXT,
    loai_tai_san TEXT,
    vi_tri TEXT,
    phong_ban TEXT,
    gia_tri REAL DEFAULT 0,
    ngay_tiep_nhan TEXT NOT NULL,
    nguoi_su_dung_id INTEGER,
    trang_thai TEXT NOT NULL DEFAULT 'cho_ban_giao',
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

-- Bảng bảo trì / sửa chữa tài sản
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
    ghi_chu TEXT,
    FOREIGN KEY (phieu_kiem_ke_id) REFERENCES phieu_kiem_ke(id),
    FOREIGN KEY (tai_san_id) REFERENCES tai_san(id)
);

-- Bảng báo cáo hư hại vật chất (Public - không cần đăng nhập)
CREATE TABLE IF NOT EXISTS bao_cao_hu_hai (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ho_ten TEXT NOT NULL,
    lien_he TEXT NOT NULL,
    ten_vat_chat TEXT NOT NULL,
    vi_tri TEXT NOT NULL,
    muc_do TEXT NOT NULL,
    mo_ta_chi_tiet TEXT,
    thoi_gian_phat_hien TEXT,
    trang_thai TEXT DEFAULT 'chua_xu_ly',
    ngay_tao TEXT NOT NULL
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

def init_db(db_conn=None):
    """Khởi tạo toàn bộ bảng nếu chưa tồn tại."""
    conn = db_conn or get_db()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
