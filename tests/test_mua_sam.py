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

    # Cán bộ mua sắm lập khảo sát BM02 phù hợp
    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát nhu cầu máy tính đồng bộ",
        "ket_luan": "phu_hop"
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

    # 2. Khảo sát BM02 phù hợp trước khi phê duyệt
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát nhu cầu máy in",
        "ket_luan": "phu_hop"
    })
    for nha_cung_cap in ("NCC A", "NCC B", "NCC C"):
        client.post("/mua-sam/de-nghi/1/bao-gia", data={
            "nha_cung_cap": nha_cung_cap,
            "tong_gia": "3500000"
        })
    client.post("/mua-sam/de-nghi/1/chon-bao-gia/1")

    # 3. Sau khi khảo sát phù hợp -> Admin phê duyệt đề nghị
    auth.login(vai_tro="quan_tri")
    res_duyet = client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Duyệt cấp máy in"}, follow_redirects=True)
    assert res_duyet.status_code == 200

    # 4. Lập biên bản nghiệm thu kỹ thuật BM04 đạt yêu cầu sau khi duyệt và chốt NCC.
    auth.login(vai_tro="mua_sam")
    res_nt = client.post("/mua-sam/de-nghi/1/nghiem-thu", data={
        "ket_qua": "dat",
        "dai_dien_ben_mua": "BP Mua sắm",
        "dai_dien_nha_cung_cap": "NCC Canon",
        "y_kien_danh_gia": "Máy in nguyên seal, thử in rõ nét đạt yêu cầu"
    }, follow_redirects=True)
    assert res_nt.status_code == 200

    # 5. Bộ phận quản lý tài sản tiếp nhận hàng vào kho
    auth.login(vai_tro="quan_ly_kho")
    res_nhan = client.post("/tai-san/tiep-nhan/1", data={"ghi_chu": "Đã nhận máy in"}, follow_redirects=True)
    assert res_nhan.status_code == 200
    assert "Tiếp nhận hàng hóa thành công" in res_nhan.text

    # 4. Bộ phận quản lý tài sản kiểm tra danh mục tài sản M09 đã có máy in
    res_ts = client.get("/tai-san/")
    assert res_ts.status_code == 200
    assert "Máy in Canon 2900" in res_ts.text


def test_bat_buoc_khao_sat_phu_hop_moi_hien_thi_nut_duyet(client, auth):
    """
    Test quy tắc:
    1. Chưa khảo sát: Ẩn nút phê duyệt trên giao diện, cố tình POST bị lỗi CHUA_KHAO_SAT.
    2. Khảo sát chưa kết luận 'phù hợp và cần thiết để tổ chức thực hiện' (chua_du): Ẩn nút phê duyệt, cố tình POST bị lỗi KHAO_SAT_CHUA_PHU_HOP.
    3. Trong mục kết luận chỉ có 2 lựa chọn: 'Phù hợp và cần thiết để tổ chức thực hiện' và 'Chưa đủ cơ sở để tổ chức thực hiện'.
    4. Khảo sát xong và kết luận 'phù hợp và cần thiết để tổ chức thực hiện': Nút phê duyệt hiển thị và duyệt thành công.
    """
    # 1. Tạo đề nghị mới
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Mua bàn ghế phòng đọc thư viện",
        "don_vi_de_nghi": "Thư viện NEU",
        "ten_hang_hoa[]": ["Bàn đọc gỗ"],
        "don_vi_tinh[]": ["Bộ"],
        "so_luong[]": ["10"],
        "don_gia_du_kien[]": ["2000000"]
    })

    # Đăng nhập Admin hoặc Trưởng BP Mua sắm xem chi tiết
    auth.login(vai_tro="quan_tri")
    res_view1 = client.get("/mua-sam/de-nghi/1")
    assert res_view1.status_code == 200
    # Khi chưa khảo sát: Không có nút/form Phê duyệt đề nghị
    assert "/mua-sam/de-nghi/1/phe-duyet" not in res_view1.text
    assert "Chưa thể phê duyệt" in res_view1.text

    # Cố tình gọi API phê duyệt khi chưa khảo sát -> 400 CHUA_KHAO_SAT
    res_duyet_fail1 = client.post("/mua-sam/de-nghi/1/phe-duyet", headers={"Accept": "application/json"})
    assert res_duyet_fail1.status_code == 400
    assert res_duyet_fail1.json["loi"] == "CHUA_KHAO_SAT"

    # Kiểm tra modal khảo sát chỉ có 2 lựa chọn kết luận
    assert "Phù hợp và cần thiết để tổ chức thực hiện" in res_view1.text
    assert "Chưa đủ cơ sở để tổ chức thực hiện" in res_view1.text
    assert "Cần điều chỉnh số lượng" not in res_view1.text

    # 2. Thực hiện khảo sát nhưng kết luận là 'chua_du' (Chưa đủ cơ sở để tổ chức thực hiện)
    auth.login(vai_tro="mua_sam")
    res_ks_chua_du = client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát hiện trạng thư viện",
        "ket_luan": "chua_du"
    }, follow_redirects=True)
    assert res_ks_chua_du.status_code == 200

    # Xem lại trang chi tiết: Nút duyệt vẫn BỊ ẨN
    auth.login(vai_tro="quan_tri")
    res_view2 = client.get("/mua-sam/de-nghi/1")
    assert "/mua-sam/de-nghi/1/phe-duyet" not in res_view2.text
    assert "Chưa thể phê duyệt" in res_view2.text

    # Cố tình gọi API phê duyệt khi kết luận chưa phù hợp -> 400 KHAO_SAT_CHUA_PHU_HOP
    res_duyet_fail2 = client.post("/mua-sam/de-nghi/1/phe-duyet", headers={"Accept": "application/json"})
    assert res_duyet_fail2.status_code == 400
    assert res_duyet_fail2.json["loi"] == "KHAO_SAT_CHUA_PHU_HOP"

    # 3. Khảo sát lại với kết luận 'phu_hop' (Phù hợp và cần thiết để tổ chức thực hiện)
    auth.login(vai_tro="mua_sam")
    res_ks_ok = client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát bổ sung nhu cầu thư viện",
        "ket_luan": "phu_hop"
    }, follow_redirects=True)
    assert res_ks_ok.status_code == 200

    # Xem lại trang chi tiết: NÚT DUYỆT ĐÃ HIỂN THỊ
    auth.login(vai_tro="quan_tri")
    res_view3 = client.get("/mua-sam/de-nghi/1")
    assert "/mua-sam/de-nghi/1/phe-duyet" in res_view3.text

    # Bấm phê duyệt thành công
    res_duyet_ok = client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Duyệt mua bàn ghế"}, follow_redirects=True)
    assert res_duyet_ok.status_code == 200
    assert "Đã phê duyệt đề nghị" in res_duyet_ok.text

