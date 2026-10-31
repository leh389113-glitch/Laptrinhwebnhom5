def test_dang_nhap_mua_sam_redirect(client):
    """Bộ phận mua sắm đăng nhập redirect đúng /mua-sam/"""
    res = client.post("/dang-nhap", data={
        "ten_dang_nhap": "user_mua_sam",
        "mat_khau": "password123"
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/mua-sam" in res.location

def test_dang_nhap_quan_ly_kho_redirect(client):
    """Bộ phận quản lý kho đăng nhập redirect đúng /tai-san/"""
    res = client.post("/dang-nhap", data={
        "ten_dang_nhap": "user_kho",
        "mat_khau": "password123"
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/tai-san" in res.location

def test_dang_nhap_ke_toan_redirect(client):
    """Kế toán đăng nhập redirect đúng /ke-toan/"""
    res = client.post("/dang-nhap", data={
        "ten_dang_nhap": "user_ke_toan",
        "mat_khau": "password123"
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/ke-toan" in res.location

def test_dang_nhap_admin_redirect(client):
    """Admin đăng nhập redirect đúng /admin/"""
    res = client.post("/dang-nhap", data={
        "ten_dang_nhap": "user_admin",
        "mat_khau": "password123"
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/admin" in res.location

def test_truy_cap_trang_bao_ve_chua_dang_nhap(client):
    """Test truy cập trang bảo vệ khi chưa đăng nhập -> redirect về đăng nhập."""
    res = client.get("/mua-sam/", follow_redirects=False)
    assert res.status_code == 302
    assert "/dang-nhap" in res.location

def test_dang_ky_thanh_cong(client):
    """Test đăng ký tài khoản cán bộ mới thành công."""
    res = client.post("/dang-ky", data={
        "ho_ten": "Cán bộ Mới",
        "email": "canbo.moi@neu.edu.vn",
        "ten_dang_nhap": "cb_moi",
        "mat_khau": "password123",
        "xac_nhan_mat_khau": "password123",
        "vai_tro": "quan_ly_kho"
    }, follow_redirects=False)
    assert res.status_code == 302
    assert "/dang-nhap" in res.location
