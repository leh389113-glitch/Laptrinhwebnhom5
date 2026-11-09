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

    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát nhu cầu tủ tài liệu",
        "ket_luan": "phu_hop"
    })
    for nha_cung_cap in ("NCC A", "NCC B", "NCC C"):
        client.post("/mua-sam/de-nghi/1/bao-gia", data={
            "nha_cung_cap": nha_cung_cap,
            "tong_gia": "2500000"
        })
    client.post("/mua-sam/de-nghi/1/chon-bao-gia/1")

    auth.login(vai_tro="quan_tri")
    client.post("/mua-sam/de-nghi/1/phe-duyet", data={})

    # Nghiệm thu kỹ thuật BM04 đạt yêu cầu trước khi nhập kho
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/nghiem-thu", data={
        "ket_qua": "dat",
        "dai_dien_ben_mua": "BP Mua sắm",
        "y_kien_danh_gia": "Đạt yêu cầu nghiệm thu kỹ thuật"
    })

    # Tiếp nhận hàng hóa vào kho là trách nhiệm của Quản lý tài sản (M09)
    auth.login(vai_tro="quan_ly_kho")
    client.post("/tai-san/tiep-nhan/1", data={"ghi_chu": "Nhập kho"})

    # Mua sắm lập phiếu đề nghị thanh toán để Kế toán nhận xử lý.
    auth.login(vai_tro="mua_sam")
    res_phieu = client.post("/mua-sam/de-nghi/1/de-nghi-thanh-toan", data={
        "noi_dung_thanh_toan": "Thanh toán tiền mua tủ tài liệu"
    }, follow_redirects=True)
    assert res_phieu.status_code == 200
    assert "gửi phiếu thanh toán" in res_phieu.text.lower()

    # 2. Kế toán truy cập danh sách chờ thanh toán
    auth.login(vai_tro="ke_toan")
    res_list = client.get("/ke-toan/")
    assert res_list.status_code == 200
    assert "Thanh toán tiền mua tủ tài liệu" in res_list.text
    assert "TT-" in res_list.text

    # Admin chỉ có quyền xem, không được trực tiếp xác nhận thanh toán
    auth.login(vai_tro="quan_tri")
    res_admin_tt = client.post("/ke-toan/de-nghi/1/thanh-toan", data={
        "so_tien": "2500000",
        "so_hoa_don": "HD-TEST-ADMIN",
        "phuong_thuc": "chuyen_khoan"
    })
    assert res_admin_tt.status_code == 403

    # 3. Kế toán ghi nhận thanh toán thành công
    auth.login(vai_tro="ke_toan")
    res_tt = client.post("/ke-toan/de-nghi/1/thanh-toan", data={
        "so_tien": "2500000",
        "so_hoa_don": "HD-TEST-001",
        "phuong_thuc": "chuyen_khoan",
        "ghi_chu": "Đã chuyển khoản kho bạc"
    }, follow_redirects=True)
    assert res_tt.status_code == 200
    assert "Ghi nhận thanh toán thành công" in res_tt.text
