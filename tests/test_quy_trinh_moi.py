from app.db import get_db

def test_khao_sat_va_bao_gia_va_nghiem_thu(client, auth):
    """Test chu trình M08: Khảo sát BM02, 3 báo giá cạnh tranh, nghiệm thu hàng hóa."""
    auth.login(vai_tro="mua_sam")
    
    # 1. Lập đề nghị mua sắm < 100 triệu
    res = client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Trang bị máy in văn phòng",
        "don_vi_de_nghi": "Ban Quản lý Tòa A2",
        "mo_ta": "Phục vụ in ấn tài liệu",
        "muc_do_uu_tien": "can_som",
        "nguon_kinh_phi": "Kinh phí đào tạo",
        "dia_diem_su_dung": "Phòng A1-205",
        "ly_do_su_can_thiet": "Nhu cầu in bài thi học kỳ",
        "ten_hang_hoa[]": ["Máy in HP LaserJet Pro"],
        "don_vi_tinh[]": ["Chiếc"],
        "so_luong[]": ["2"],
        "don_gia_du_kien[]": ["8000000"],
        "vi_tri_su_dung[]": ["Phòng A1-205"],
        "ly_do_muc_dich[]": ["In bài thi"]
    }, follow_redirects=True)
    assert res.status_code == 200

    # 2. Khảo sát nhu cầu BM02
    res_ks = client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát thực tế nhu cầu máy in",
        "dia_diem": "Phòng A1-205",
        "can_bo_khao_sat": "Cán bộ Mua sắm",
        "dai_dien_don_vi": "Đại diện Ban Quản lý Tòa A2",
        "ket_qua_danh_gia": "Nhu cầu chính xác",
        "kiem_tra_kho": "Kho không còn máy in phù hợp",
        "doi_chieu_dinh_muc": "Phù hợp tiêu chuẩn định mức",
        "muc_do_can_thiet": "can_thiet",
        "phuong_an_de_xuat": "mua_bo_sung",
        "ket_luan": "phu_hop"
    }, follow_redirects=True)
    assert res_ks.status_code == 200
    assert "biên bản khảo sát" in res_ks.text.lower()

    # 3. Thêm 3 báo giá cạnh tranh
    res_bg1 = client.post("/mua-sam/de-nghi/1/bao-gia", data={
        "nha_cung_cap": "Công ty TNHH Tin học Sao Mai",
        "ma_so_thue": "0109988776",
        "tong_gia": "16500000",
        "hieu_luc": "30 ngày"
    }, follow_redirects=True)
    assert res_bg1.status_code == 200

    res_bg2 = client.post("/mua-sam/de-nghi/1/bao-gia", data={
        "nha_cung_cap": "Công ty CP Công nghệ Ánh Dương",
        "ma_so_thue": "0108877665",
        "tong_gia": "15800000",
        "hieu_luc": "45 ngày"
    }, follow_redirects=True)
    assert res_bg2.status_code == 200

    res_bg3 = client.post("/mua-sam/de-nghi/1/bao-gia", data={
        "nha_cung_cap": "Công ty Thiết bị Văn phòng Hà Nội",
        "ma_so_thue": "0107766554",
        "tong_gia": "16000000",
        "hieu_luc": "30 ngày"
    }, follow_redirects=True)
    assert res_bg3.status_code == 200
    assert "Công ty CP Công nghệ Ánh Dương" in res_bg3.text

    # 4. Chọn nhà cung cấp trúng thầu (Ánh Dương - id 2)
    res_chon = client.post("/mua-sam/de-nghi/1/chon-bao-gia/2", follow_redirects=True)
    assert res_chon.status_code == 200
    assert "lựa chọn nhà cung cấp trúng thầu" in res_chon.text.lower()

    # 5. Phê duyệt đề nghị (< 100 triệu: chỉ Trưởng BP Mua sắm duyệt thành công)
    auth.login(username="user_truong_mua_sam")
    res_duyet = client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Trưởng BP duyệt"}, follow_redirects=True)
    assert res_duyet.status_code == 200
    assert "phê duyệt đề nghị" in res_duyet.text.lower()

    # 6. Lập biên bản kiểm tra & nghiệm thu hàng hóa
    res_nt = client.post("/mua-sam/de-nghi/1/nghiem-thu", data={
        "dai_dien_ben_mua": "Phòng QTTB",
        "dai_dien_nha_cung_cap": "Đại diện Ánh Dương",
        "dai_dien_don_vi_su_dung": "Đại diện Ban Quản lý Tòa A2",
        "ket_qua": "dat",
        "y_kien_danh_gia": "Máy in mới 100%, bảo hành 24 tháng chính hãng"
    }, follow_redirects=True)
    assert res_nt.status_code == 200
    assert "nghiệm thu" in res_nt.text.lower()

    # 7. Bộ phận Quản lý tài sản tiếp nhận hàng hóa vào M09
    auth.login(vai_tro="quan_ly_kho")
    res_nhan = client.post("/tai-san/tiep-nhan/1", data={"ghi_chu": "Đã nhận 2 máy in vào kho"}, follow_redirects=True)
    assert res_nhan.status_code == 200
    assert "tiếp nhận hàng hóa thành công" in res_nhan.text.lower()

    # 8. Kiểm tra phân loại: Đơn giá 8.000.000 < 10 triệu -> Tự động phân loại là Công cụ dụng cụ (CCDC)
    res_ts = client.get("/tai-san/")
    assert res_ts.status_code == 200
    assert "CCDC-" in res_ts.text
    assert "Máy in HP LaserJet Pro" in res_ts.text

def test_sua_chua_tai_san_m09(client, auth, app):
    """Test luồng sửa chữa M09: Tạo yêu cầu sửa chữa, thực hiện và nghiệm thu."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (ma_tai_san, ten_tai_san, phan_loai, vi_tri, phong_ban, gia_tri, ngay_tiep_nhan, trang_thai, tinh_trang_ky_thuat, ngay_tao, ngay_cap_nhat)
            VALUES ('TS-2026-TEST-SC', 'Máy điều hòa Daikin', 'tai_san_co_dinh', 'Phòng C1-302', 'Viện CNTT', 18000000, '2026-01-01', 'dang_su_dung', 'binh_thuong', '2026-01-01', '2026-01-01')
            """
        )
        tai_san_id = cur.lastrowid
        db.commit()

    # Quản lý tài sản truy cập trang sửa chữa
    auth.login(vai_tro="quan_ly_kho")
    res_sc_list = client.get("/tai-san/sua-chua")
    assert res_sc_list.status_code == 200

    from app.services import tai_san as ts_svc
    with app.app_context():
        db_new = get_db()
        user = db_new.execute("SELECT id FROM nguoi_dung WHERE vai_tro = 'quan_ly_kho'").fetchone()
        yc = ts_svc.tao_yeu_cau_sua_chua({
            "tai_san_id": tai_san_id,
            "don_vi": "Ban Quản lý Tòa A1",
            "noi_dung": "Nạp ga và sửa dàn lạnh điều hòa Daikin",
            "hien_trang": "Điều hòa không mát, báo lỗi nháy đèn",
            "loai_sua_chua": "thiet_bi",
            "chi_phi_du_kien": 1200000,
            "don_vi_thuc_hien": "Trung tâm Điện lạnh Hà Nội"
        }, user["id"])
        yc_id = yc["id"]

    # Tài sản chỉ chuyển trạng thái khi phương án đã được duyệt.
    res_detail = client.get(f"/tai-san/{tai_san_id}")
    assert res_detail.status_code == 200
    assert "Đang sử dụng" in res_detail.text

    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/tiep-nhan",
        data={"hanh_dong": "tiep_nhan"},
        follow_redirects=True
    ).status_code == 200
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/khao-sat/bat-dau",
        follow_redirects=True
    ).status_code == 200
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/khao-sat",
        data={
            "thanh_phan_khao_sat": "QTTB",
            "phan_loai_yeu_cau": "thiet_bi",
            "hien_trang": "Điều hòa không mát",
            "muc_do_hu_hong": "trung_binh",
            "khoi_luong_cong_viec": "Nạp ga"
        },
        follow_redirects=True
    ).status_code == 200
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/phuong-an",
        data={
            "phuong_an": "sua_chua",
            "phuong_an_chi_tiet": "Nạp ga và sửa dàn lạnh",
            "chi_phi_du_kien": "1200000"
        },
        follow_redirects=True
    ).status_code == 200

    auth.login(vai_tro="quan_tri")
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/phe-duyet-phuong-an",
        data={"ghi_chu": "Duyệt phương án"},
        follow_redirects=True
    ).status_code == 200
    res_detail = client.get(f"/tai-san/{tai_san_id}")
    assert "Đang sửa chữa" in res_detail.text

    auth.login(vai_tro="quan_ly_kho")
    res_nt_sc = client.post(
        f"/tai-san/sua-chua/{yc_id}/nghiem-thu",
        data={"chi_phi_thuc_te": "1150000", "ghi_chu": "Đã chạy thử"},
        follow_redirects=True
    )
    assert res_nt_sc.status_code == 200
    assert "chờ đơn vị xác nhận" in res_nt_sc.text.lower()

    auth.login(vai_tro="don_vi")
    assert client.post(
        f"/don-vi/sua-chua/{yc_id}/nghiem-thu",
        data={"ket_qua": "dat", "ghi_chu": "Đạt yêu cầu"},
        follow_redirects=True
    ).status_code == 200

    # Kiểm tra tài sản đã trở lại trạng thái đang sử dụng
    auth.login(vai_tro="quan_ly_kho")
    res_ts_after = client.get(f"/tai-san/{tai_san_id}")
    assert "Đang sử dụng" in res_ts_after.text
