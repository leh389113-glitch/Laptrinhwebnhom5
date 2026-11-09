import os
import sys
import tempfile
import pytest

# Thêm thư mục gốc dự án vào sys.path để pytest tìm thấy app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from werkzeug.security import generate_password_hash
from app import tao_app
from app.db import init_db, get_db

@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["CSV_DB"] = db_path

    app = tao_app({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key"
    })

    with app.app_context():
        init_db()
        db = get_db()
        pw_hash = generate_password_hash("password123")
        db.execute(
            """
            INSERT INTO nguoi_dung (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, don_vi, so_dien_thoai, ngay_tao, trang_thai)
            VALUES 
            ('Admin Test', 'admin@neu.test', 'user_admin', ?, 'quan_tri', 'Ban Giám hiệu', '02436280280', '2026-01-01T00:00:00', 'hoat_dong'),
            ('Mua Sam Test', 'muasam@neu.test', 'user_mua_sam', ?, 'mua_sam', 'Bộ phận Mua sắm', '0912111222', '2026-01-01T00:00:00', 'hoat_dong'),
            ('Quan Ly Kho Test', 'kho@neu.test', 'user_kho', ?, 'quan_ly_kho', 'Bộ phận Quản lý tài sản', '0913222333', '2026-01-01T00:00:00', 'hoat_dong'),
            ('Ke Toan Test', 'ketoan@neu.test', 'user_ke_toan', ?, 'ke_toan', 'Phòng Kế toán', '0914333444', '2026-01-01T00:00:00', 'hoat_dong'),
            ('Don Vi Test', 'donvi@neu.test', 'user_don_vi', ?, 'don_vi', 'Khoa Công nghệ Thông tin', '0912345678', '2026-01-01T00:00:00', 'hoat_dong')
            """,
            (pw_hash, pw_hash, pw_hash, pw_hash, pw_hash)
        )
        db.commit()

    yield app

    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="user_admin", password="password123", vai_tro=None):
        self.logout()
        if vai_tro:
            mapping = {
                "quan_tri": "user_admin",
                "mua_sam": "user_mua_sam",
                "quan_ly_kho": "user_kho",
                "ke_toan": "user_ke_toan",
                "don_vi": "user_don_vi"
            }
            username = mapping.get(vai_tro, username)

        return self._client.post(
            "/dang-nhap",
            data={"ten_dang_nhap": username, "mat_khau": password},
            follow_redirects=False
        )

    def logout(self):
        return self._client.get("/dang-xuat", follow_redirects=False)

@pytest.fixture
def auth(client):
    return AuthActions(client)
