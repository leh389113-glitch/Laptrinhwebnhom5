from app.db import get_db

def test_mua_sam_khong_duoc_truy_cap_tai_san(client, auth):
    """Test bộ phận mua sắm không có quyền truy cập module M09 - Kho & Tài sản."""
    auth.login(vai_tro="mua_sam")
    res = client.get("/tai-san/")
    assert res.status_code == 403

def test_quan_ly_kho_truy_cap_tai_san(client, auth):
    """Test bộ phận quản lý kho truy cập thành công danh sách tài sản."""
    auth.login(vai_tro="quan_ly_kho")
    res = client.get("/tai-san/")
    assert res.status_code == 200
    assert "M09 - QUẢN LÝ KHO & TÀI SẢN" in res.text

def test_ban_giao_tai_san(client, auth, app):
    """Test bộ phận quản lý kho thực hiện bàn giao tài sản."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (ma_tai_san, ten_tai_san, vi_tri, phong_ban, gia_tri, ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat)
            VALUES ('TS-2026-TEST-001', 'Laptop Dell XPS', 'Kho', 'Khoa CNTT', 25000000, '2026-01-01', 'cho_ban_giao', '2026-01-01', '2026-01-01')
            """
        )
        tai_san_id = cur.lastrowid
        user_row = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_mua_sam'").fetchone()
        user_id = user_row["id"]
        db.commit()

    auth.login(vai_tro="quan_ly_kho")
    res_bg = client.post(f"/tai-san/{tai_san_id}/ban-giao", data={
        "nguoi_nhan_id": user_id,
        "ghi_chu": "Bàn giao máy tính xách tay"
    }, follow_redirects=True)
    assert res_bg.status_code == 200
    assert "Bàn giao tài sản thành công" in res_bg.text

def test_ghi_nhan_bao_tri_tai_san(client, auth, app):
    """Test bộ phận quản lý kho ghi nhận sửa chữa, bảo trì cho tài sản."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (ma_tai_san, ten_tai_san, vi_tri, phong_ban, gia_tri, ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat)
            VALUES ('TS-2026-TEST-002', 'Máy chiếu Sony', 'Phòng B-201', 'Phòng QTTB', 15000000, '2026-01-01', 'dang_su_dung', '2026-01-01', '2026-01-01')
            """
        )
        tai_san_id = cur.lastrowid
        db.commit()

    auth.login(vai_tro="quan_ly_kho")
    res = client.post(f"/tai-san/{tai_san_id}/bao-tri", data={
        "noi_dung": "Thay quạt tản nhiệt",
        "chi_phi": "500000",
        "don_vi_thuc_hien": "Trung tâm bảo hành Sony",
        "ghi_chu": "Bảo hành 6 tháng",
        "trang_thai_moi": "dang_su_dung"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Ghi nhận bảo trì/sửa chữa tài sản thành công" in res.text
