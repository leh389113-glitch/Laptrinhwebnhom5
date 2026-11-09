import pytest
from app.db import get_db

def test_login_redirect_don_vi(client, auth):
    """Kiểm tra đăng nhập vai trò don_vi tự động chuyển hướng đến /don-vi/."""
    res = auth.login(vai_tro="don_vi")
    assert res.status_code == 302
    assert "/don-vi/" in res.headers["Location"]

def test_dashboard_don_vi(client, auth):
    """Kiểm tra truy cập Dashboard Đơn vị sử dụng hiển thị đúng danh tính và đơn vị."""
    auth.login(vai_tro="don_vi")
    res = client.get("/don-vi/dashboard")
    assert res.status_code == 200
    assert "Khoa Công nghệ Thông tin".encode("utf-8") in res.data
    assert "BẢNG ĐIỀU KHIỂN ĐƠN VỊ SỬ DỤNG".encode("utf-8") in res.data

def test_sua_chua_tu_dong_dinh_danh(client, auth, app):
    """Kiểm tra lập phiếu sửa chữa: tự động lấy thông tin người gửi, sinh mã YC-..."""
    auth.login(vai_tro="don_vi")
    
    # Gửi yêu cầu sửa chữa
    res = client.post(
        "/don-vi/sua-chua/tao",
        data={
            "loai_yeu_cau": "sua_chua_thiet_bi",
            "ten_vat_chat": "Máy chiếu Panasonic PT-LB386",
            "vi_tri": "Phòng D2-501",
            "do_khan_cap": "can_som",
            "muc_do": "trung_binh",
            "thoi_gian_phat_hien": "2026-11-09 08:30:00",
            "mo_ta_chi_tiet": "Bóng đèn máy chiếu bị mờ nhạt không đọc được văn bản."
        },
        follow_redirects=True
    )
    assert res.status_code == 200
    assert "Máy chiếu Panasonic PT-LB386".encode("utf-8") in res.data
    
    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT * FROM bao_cao_hu_hai WHERE ten_vat_chat = 'Máy chiếu Panasonic PT-LB386'").fetchone()
        assert yc is not None
        assert yc["ma_bao_cao"].startswith("YC-")
        assert yc["ho_ten"] == "Don Vi Test"
        assert yc["don_vi"] == "Khoa Công nghệ Thông tin"
        assert yc["lien_he"] == "0912345678"
        assert yc["do_khan_cap"] == "can_som"

def test_xac_nhan_khao_sat_va_nghiem_thu_sua_chua(client, auth, app):
    """Kiểm tra đơn vị ký xác nhận khảo sát BM03 và ký nghiệm thu sửa chữa."""
    auth.login(vai_tro="don_vi")

    # Tạo trước 1 báo cáo
    with app.app_context():
        db = get_db()
        u = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_don_vi'").fetchone()
        cur = db.execute(
            """
            INSERT INTO bao_cao_hu_hai (
                ma_bao_cao, nguoi_gui_id, ho_ten, lien_he, don_vi,
                ten_vat_chat, vi_tri, loai_yeu_cau, do_khan_cap, muc_do,
                mo_ta_chi_tiet, trang_thai, ngay_tao
            ) VALUES ('YC-TEST-001', ?, 'Don Vi Test', '0912345678', 'Khoa Công nghệ Thông tin',
                     'Điều hòa Daikin', 'Phòng A1-201', 'sua_chua_thiet_bi', 'binh_thuong', 'trung_binh',
                     'Không mát', 'dang_xu_ly', '2026-11-09 08:00:00')
            """,
            (u["id"],)
        )
        db.commit()
        yc_id = cur.lastrowid

    # 1. Ký xác nhận khảo sát
    res_ks = client.post(
        f"/don-vi/sua-chua/{yc_id}/xac-nhan-khao-sat",
        data={"ghi_chu": "Đồng ý hiện trạng máy hỏng lốc"},
        follow_redirects=True
    )
    assert res_ks.status_code == 200
    assert "Đơn vị đã ký xác nhận khảo sát".encode("utf-8") in res_ks.data

    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT * FROM bao_cao_hu_hai WHERE id = ?", (yc_id,)).fetchone()
        assert yc["xac_nhan_khao_sat_don_vi"] == 1

    # 2. Ký nghiệm thu hoàn thành
    res_nt = client.post(
        f"/don-vi/sua-chua/{yc_id}/nghiem-thu",
        data={"ghi_chu": "Điều hòa đã lạnh sâu, chạy êm"},
        follow_redirects=True
    )
    assert res_nt.status_code == 200
    assert "Nghiệm thu hoàn tất".encode("utf-8") in res_nt.data

    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT * FROM bao_cao_hu_hai WHERE id = ?", (yc_id,)).fetchone()
        assert yc["xac_nhan_nghiem_thu_don_vi"] == 1
        assert yc["trang_thai"] == "da_xu_ly"

def test_tao_de_xuat_mua_sam_bm01(client, auth, app):
    """Kiểm tra đơn vị lập đề xuất mua sắm BM01: tự động gán đơn vị đề nghị."""
    auth.login(vai_tro="don_vi")

    res = client.post(
        "/don-vi/mua-sam/tao",
        data={
            "tieu_de": "Đề xuất mua sắm 10 máy tính thực hành AI",
            "muc_do_uu_tien": "can_gap",
            "dia_diem_su_dung": "Lab 501 Nhà D2",
            "thoi_gian_can_hang": "2026-12-01",
            "ly_do_su_can_thiet": "Phục vụ khóa học thị giác máy tính",
            "ten_hang_hoa[]": ["Máy tính AI Workstation", "Màn hình 27 inch"],
            "don_vi_tinh[]": ["Bộ", "Chiếc"],
            "so_luong[]": ["10", "10"],
            "don_gia_du_kien[]": ["30000000", "5000000"],
            "vi_tri_su_dung[]": ["Lab 501", "Lab 501"],
            "ly_do_muc_dich[]": ["Thực hành", "Hiển thị"],
            "ghi_chu[]": ["GPU RTX 4070", "IPS 144Hz"]
        },
        follow_redirects=True
    )
    assert res.status_code == 200
    assert "Đề xuất mua sắm 10 máy tính thực hành AI".encode("utf-8") in res.data

    with app.app_context():
        db = get_db()
        dn = db.execute("SELECT * FROM de_nghi_mua_sam WHERE tieu_de LIKE '%10 máy tính thực hành AI%'").fetchone()
        assert dn is not None
        assert dn["don_vi_de_nghi"] == "Khoa Công nghệ Thông tin"
        assert dn["tong_du_toan"] == (10 * 30000000) + (10 * 5000000)
        assert dn["trang_thai"] == "cho_lanh_dao_duyet"  # >= 100tr

def test_tai_san_don_vi_va_xac_nhan_ban_giao(client, auth, app):
    """Kiểm tra danh mục tài sản đơn vị và thao tác ký nhận bàn giao BM03."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, xac_nhan_ban_giao_don_vi,
                ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-TEST-999', 'Máy chủ AI Server', 'Máy chủ', 'tai_san_co_dinh',
                'binh_thuong', 'Lab 501', 'Khoa Công nghệ Thông tin', 'Khoa Công nghệ Thông tin',
                120000000, '2026-11-09', 'cho_ban_giao', 0,
                '2026-11-09 08:00:00', '2026-11-09 08:00:00'
            )
            """
        )
        db.commit()
        ts_id = cur.lastrowid

    auth.login(vai_tro="don_vi")
    
    # 1. Xem danh sách tài sản
    res = client.get("/don-vi/tai-san")
    assert res.status_code == 200
    assert "TS-TEST-999".encode("utf-8") in res.data

    # 2. Xem chi tiết tài sản
    res_ct = client.get(f"/don-vi/tai-san/{ts_id}")
    assert res_ct.status_code == 200
    assert "Máy chủ AI Server".encode("utf-8") in res_ct.data

    # 3. Ký xác nhận tiếp nhận bàn giao
    res_bg = client.post(
        f"/don-vi/tai-san/{ts_id}/xac-nhan-ban-giao",
        data={"ghi_chu": "Đã tiếp nhận đủ linh kiện"},
        follow_redirects=True
    )
    assert res_bg.status_code == 200
    assert "Đơn vị đã xác nhận tiếp nhận bàn giao".encode("utf-8") in res_bg.data

    with app.app_context():
        db = get_db()
        ts = db.execute("SELECT * FROM tai_san WHERE id = ?", (ts_id,)).fetchone()
        assert ts["xac_nhan_ban_giao_don_vi"] == 1
        assert ts["trang_thai"] == "dang_su_dung"

def test_kiem_ke_va_giai_trinh(client, auth, app):
    """Kiểm tra đơn vị phối hợp kiểm kê và gửi giải trình chênh lệch số liệu."""
    with app.app_context():
        db = get_db()
        u_kho = db.execute("SELECT id FROM nguoi_dung WHERE vai_tro = 'quan_ly_kho'").fetchone()
        
        # Tạo tài sản của Khoa CNTT
        cur_ts = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, xac_nhan_ban_giao_don_vi,
                ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-KK-001', 'Máy in HP LaserJet', 'Máy in', 'cong_cu_dung_cu',
                'binh_thuong', 'VP Khoa CNTT', 'Khoa Công nghệ Thông tin', 'Khoa Công nghệ Thông tin',
                7500000, '2026-11-09', 'dang_su_dung', 1,
                '2026-11-09 08:00:00', '2026-11-09 08:00:00'
            )
            """
        )
        ts_id = cur_ts.lastrowid

        # Tạo phiếu kiểm kê
        cur_kk = db.execute(
            "INSERT INTO phieu_kiem_ke (ma_phieu, ngay_kiem_ke, nguoi_kiem_ke_id, ghi_chu, ngay_tao) VALUES ('KK-T11', '2026-11-09', ?, 'Đợt kiểm kê', '2026-11-09')",
            (u_kho["id"],)
        )
        kk_id = cur_kk.lastrowid

        # Tạo chi tiết có chênh lệch
        cur_ct = db.execute(
            "INSERT INTO chi_tiet_kiem_ke (phieu_kiem_ke_id, tai_san_id, tinh_trang_thuc_te, so_luong_he_thong, so_luong_thuc_te, chenh_lech, ghi_chu) VALUES (?, ?, 'Thiếu 01 máy', 1, 0, -1, 'Chưa thấy hiện vật')",
            (kk_id, ts_id)
        )
        db.commit()
        ct_id = cur_ct.lastrowid

    auth.login(vai_tro="don_vi")
    
    # Xem trang kiểm kê
    res_kk = client.get("/don-vi/kiem-ke")
    assert res_kk.status_code == 200
    assert "KK-T11".encode("utf-8") in res_kk.data

    # Gửi giải trình chênh lệch
    res_gt = client.post(
        f"/don-vi/kiem-ke/{ct_id}/giai-trinh",
        data={"noi_dung_giai_trinh": "Máy in đang được mang đi bảo dưỡng định kỳ tại trung tâm bảo hành"},
        follow_redirects=True
    )
    assert res_gt.status_code == 200
    assert "Đã gửi giải trình:".encode("utf-8") in res_gt.data

    with app.app_context():
        db = get_db()
        ct = db.execute("SELECT * FROM chi_tiet_kiem_ke WHERE id = ?", (ct_id,)).fetchone()
        assert ct["trang_thai_giai_trinh"] == "da_giai_trinh"
        assert "bảo dưỡng định kỳ" in ct["giai_trinh_don_vi"]

def test_phan_quyen_rbac_don_vi(client, auth):
    """Kiểm tra phân quyền chặt chẽ (RBAC Matrix): Đơn vị sử dụng chỉ có quyền xem/phối hợp, bị chặn các phân hệ khác."""
    auth.login(vai_tro="don_vi")

    # 1. Bị chặn truy cập quản lý mua sắm M08 nội bộ
    res_ms = client.get("/mua-sam/")
    assert res_ms.status_code == 403

    # 2. Bị chặn tác nghiệp kho M09 (tiếp nhận hàng)
    res_tn = client.get("/tai-san/tiep-nhan")
    assert res_tn.status_code == 403

    # 3. Bị chặn thanh toán kế toán
    res_kt = client.get("/ke-toan/")
    assert res_kt.status_code == 403

    # 4. Bị chặn quản lý tài khoản admin
    res_adm = client.get("/admin/tai-khoan")
    assert res_adm.status_code == 403

    # Ngược lại: Cán bộ mua sắm không được vào phân hệ của đơn vị
    auth.login(vai_tro="mua_sam")
    res_dv = client.get("/don-vi/")
    assert res_dv.status_code == 403
