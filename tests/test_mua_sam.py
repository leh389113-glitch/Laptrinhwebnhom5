def test_lap_de_nghi_mua_sam_thanh_cong(client, auth):
    """Test cán bộ bộ phận mua sắm lập đề nghị mua sắm hợp lệ."""
    auth.login(vai_tro="mua_sam")
    res = client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Trang bị màn chiếu giảng đường A1",
        "don_vi_de_nghi": "Khoa Tin học Kinh tế",
        "mo_ta": "Màn chiếu phục vụ đồ án sinh viên",
        "ten_hang_hoa[]": ["Màn chiếu 120 inch"],
        "don_vi_tinh[]": ["Chiếc"],
        "so_luong[]": ["2"],
        "don_gia_du_kien[]": ["4000000"],
        "ghi_chu[]": ["Lắp đặt cố định"]
    }, follow_redirects=False)

    assert res.status_code == 302
    assert "/mua-sam/de-nghi/" in res.location

def test_phe_duyet_de_nghi_khong_du_quyen(client, auth):
    """Test bộ phận mua sắm không được duyệt đề xuất >= 100 triệu (chỉ Lãnh đạo/Admin được duyệt)."""
    auth.login(vai_tro="mua_sam")
    # Lập đề nghị quy mô lớn: 100 bộ máy tính x 15.000.000 = 1.500.000.000đ (>= 100 triệu)
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Đề nghị kiểm tra quyền duyệt hạn mức",
        "don_vi_de_nghi": "Khoa Kinh tế",
        "ten_hang_hoa[]": ["Máy tính đồng bộ"],
        "don_vi_tinh[]": ["Bộ"],
        "so_luong[]": ["100"],
        "don_gia_du_kien[]": ["15000000"]
    })

    # Cán bộ mua sắm cố gắng phê duyệt đề nghị id 1 (>= 100 triệu) -> phải bị 403 Forbidden
    res = client.post("/mua-sam/de-nghi/1/phe-duyet", headers={"Accept": "application/json"})
    assert res.status_code == 403
    assert res.json["loi"] == "KHONG_DU_QUYEN"

    # Lãnh đạo / Admin phê duyệt thì thành công
    auth.login(vai_tro="quan_tri")
    res_admin = client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Lãnh đạo phê duyệt"}, follow_redirects=True)
    assert res_admin.status_code == 200
    assert "Đã phê duyệt đề nghị" in res_admin.text

def test_phe_duyet_va_tiep_nhan_hang_sinh_tai_san(client, auth):
    """Test phê duyệt đề nghị và tiếp nhận hàng -> Tự động sinh tài sản trong M09."""
    # 1. Mua sắm lập đề nghị
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Mua máy in văn phòng",
        "don_vi_de_nghi": "Phòng Đào tạo",
        "ten_hang_hoa[]": ["Máy in Canon 2900"],
        "don_vi_tinh[]": ["Chiếc"],
        "so_luong[]": ["1"],
        "don_gia_du_kien[]": ["3500000"]
    })

    # 2. Admin phê duyệt
    auth.login(vai_tro="quan_tri")
    res_duyet = client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Duyệt cấp máy in"}, follow_redirects=True)
    assert res_duyet.status_code == 200

    # 3. Bộ phận quản lý tài sản tiếp nhận hàng vào kho
    auth.login(vai_tro="quan_ly_kho")
    res_nhan = client.post("/mua-sam/de-nghi/1/tiep-nhan", data={"ghi_chu": "Đã nhận máy in"}, follow_redirects=True)
    assert res_nhan.status_code == 200
    assert "Tiếp nhận hàng hóa thành công" in res_nhan.text

    # 4. Bộ phận quản lý tài sản kiểm tra danh mục tài sản M09 đã có máy in
    res_ts = client.get("/tai-san/")
    assert res_ts.status_code == 200
    assert "Máy in Canon 2900" in res_ts.text
