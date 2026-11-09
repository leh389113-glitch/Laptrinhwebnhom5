def test_bao_cao_hu_hai_chua_dang_nhap_chuyen_huong(client):
    """Test truy cập form báo cáo khi chưa đăng nhập sẽ chuyển hướng sang đăng nhập."""
    res = client.get("/bao-cao-hu-hai", follow_redirects=False)
    assert res.status_code == 302
    assert "/dang-nhap" in res.headers["Location"]
    assert "next=" in res.headers["Location"]

def test_bao_cao_hu_hai_da_dang_nhap_don_vi_chuyen_huong(client, auth):
    """Test cán bộ đơn vị khi vào /bao-cao-hu-hai được chuyển thẳng tới trang tạo yêu cầu sửa chữa nội bộ."""
    auth.login(vai_tro="don_vi")
    res = client.get("/bao-cao-hu-hai", follow_redirects=False)
    assert res.status_code == 302
    assert "/don-vi/sua-chua/tao" in res.headers["Location"]

def test_quan_ly_tai_san_xu_ly_bao_cao_hu_hai(client, auth):
    """Test Bộ phận Quản lý tài sản tiếp nhận, xác minh hiện trường và xử lý sự cố hư hại từ đơn vị."""
    # 1. Cán bộ đơn vị gửi báo cáo sự cố qua /don-vi/sua-chua/tao
    auth.login(vai_tro="don_vi")
    res_post = client.post("/don-vi/sua-chua/tao", data={
        "ten_vat_chat": "Micro không dây mất tiếng",
        "vi_tri": "Hội trường A",
        "do_khan_cap": "khan_cap",
        "muc_do": "nghiem_trong",
        "loai_yeu_cau": "sua_chua_thiet_bi",
        "mo_ta_chi_tiet": "Micro bị rè và không lên nguồn"
    }, follow_redirects=True)
    assert res_post.status_code == 200

    # 2. Admin vào xem / giám sát danh sách báo cáo
    auth.login(vai_tro="quan_tri")
    res_admin_list = client.get("/admin/bao-cao-hu-hai")
    assert res_admin_list.status_code == 200
    assert "Micro không dây mất tiếng" in res_admin_list.text

    # 3. Quản lý tài sản kiểm tra thực tế và xác nhận sửa chữa
    auth.login(vai_tro="quan_ly_kho")
    res_qlts_list = client.get("/tai-san/bao-cao-hu-hai")
    assert res_qlts_list.status_code == 200
    assert "Micro không dây mất tiếng" in res_qlts_list.text

    # Quản lý tài sản cập nhật phương án sửa chữa
    res_update = client.post("/tai-san/bao-cao-hu-hai/1/xu-ly", data={
        "phuong_an": "sua_chua",
        "ghi_chu": "Đã điều kỹ thuật viên kiểm tra nguồn và thay pin micro"
    }, follow_redirects=True)
    assert res_update.status_code == 200
    assert "Đã cập nhật kết quả xác minh và phương án xử lý" in res_update.text


def test_chuyen_hu_hai_khong_the_sua_sang_mua_sam(client, auth):
    """Test hư hại không thể sửa chữa -> Quản lý tài sản chuyển sang đề xuất mua sắm M08."""
    # 1. Cán bộ đơn vị gửi báo cáo sự cố
    auth.login(vai_tro="don_vi")
    client.post("/don-vi/sua-chua/tao", data={
        "ten_vat_chat": "Máy chiếu hỏng bo mạch chính",
        "vi_tri": "Phòng D2-501",
        "do_khan_cap": "khan_cap",
        "muc_do": "nghiem_trong",
        "loai_yeu_cau": "sua_chua_thiet_bi",
        "mo_ta_chi_tiet": "Thiết bị cũ, chập cháy bo mạch chính không thể sửa"
    })

    # 2. Quản lý tài sản đánh giá cần thay thế và gửi sang M08
    auth.login(vai_tro="quan_ly_kho")
    res_chuyen = client.post("/tai-san/bao-cao-hu-hai/1/tao-mua-sam", data={
        "don_vi_de_nghi": "Ban Quản trị Thiết bị",
        "don_gia_du_kien": "18000000",
        "ghi_chu": "Lập đề xuất mua thay thế máy chiếu mới"
    }, follow_redirects=True)
    assert res_chuyen.status_code == 200
    assert "Đã lập yêu cầu mua sắm thay thế" in res_chuyen.text

    # 3. Bộ phận mua sắm thấy đề xuất này trong M08
    auth.login(vai_tro="mua_sam")
    res_m08 = client.get("/mua-sam/")
    assert res_m08.status_code == 200
    assert "Máy chiếu hỏng bo mạch chính" in res_m08.text


def test_nut_bao_cao_hu_hai_da_xoa_khoi_trang_chu(client, auth):
    """Test nút báo cáo hư hại công khai đã bị xóa hoàn toàn khỏi trang chủ cả khi chưa đăng nhập và sau khi đăng nhập."""
    # 1. Khi chưa đăng nhập:
    res_home = client.get("/")
    assert res_home.status_code == 200
    # Trang chủ không còn nút Báo cáo hư hại vật chất công khai
    assert "Báo cáo hư hại vật chất" not in res_home.text

    # Trên trang đăng nhập cũng không có
    res_login = client.get("/dang-nhap")
    assert "/bao-cao-hu-hai" not in res_login.text

    # 2. Sau khi đăng nhập (ví dụ cán bộ mua sắm):
    auth.login(vai_tro="mua_sam")
    res_home_auth = client.get("/")
    assert res_home_auth.status_code == 200
    assert "Báo cáo hư hại vật chất" not in res_home_auth.text
    assert "/bao-cao-hu-hai" not in res_home_auth.text

    # Các trang nội bộ cũng không có nút báo cáo hư hại ngoài luồng
    res_muasam = client.get("/mua-sam/")
    assert "/bao-cao-hu-hai" not in res_muasam.text
    assert "/bao-cao-hu-hai" not in res_muasam.text
