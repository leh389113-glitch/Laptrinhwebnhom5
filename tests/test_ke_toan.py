def test_ke_toan_thanh_toan_thanh_cong(client, auth):
    """Test kế toán thực hiện thanh toán đề nghị đã nhận hàng."""
    # 1. Lập đề nghị và phê duyệt, tiếp nhận hàng
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Trang bị tủ tài liệu",
        "don_vi_de_nghi": "Khoa Luật",
        "ten_hang_hoa[]": ["Tủ sắt Hòa Phát"],
        "don_vi_tinh[]": ["Chiếc"],
        "so_luong[]": ["1"],
        "don_gia_du_kien[]": ["2500000"]
    })

    auth.login(vai_tro="quan_tri")
    client.post("/mua-sam/de-nghi/1/phe-duyet", data={})

    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/tiep-nhan", data={})

    # 2. Kế toán truy cập danh sách chờ thanh toán
    auth.login(vai_tro="ke_toan")
    res_list = client.get("/ke-toan/")
    assert res_list.status_code == 200
    assert "Trang bị tủ tài liệu" in res_list.text

    # 3. Kế toán ghi nhận thanh toán
    res_tt = client.post("/ke-toan/de-nghi/1/thanh-toan", data={
        "so_tien": "2500000",
        "so_hoa_don": "HD-TEST-001",
        "phuong_thuc": "chuyen_khoan",
        "ghi_chu": "Đã chuyển khoản kho bạc"
    }, follow_redirects=True)
    assert res_tt.status_code == 200
    assert "Ghi nhận thanh toán thành công" in res_tt.text

