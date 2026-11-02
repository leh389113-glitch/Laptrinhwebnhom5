def test_bao_cao_hu_hai_khong_can_dang_nhap(client):
    """Test form báo cáo hư hại truy cập được mà không cần đăng nhập."""
    res = client.get("/bao-cao-hu-hai")
    assert res.status_code == 200
    assert "BÁO CÁO SỰ CỐ HƯ HẠI CƠ SỞ VẬT CHẤT" in res.text

def test_gui_bao_cao_hu_hai_thanh_cong(client):
    """Test gửi thành công báo cáo hư hại hợp lệ và chuyển hướng đến trang cảm ơn."""
    res = client.post("/bao-cao-hu-hai", data={
        "ho_ten": "Nguyễn Văn Sinh Viên",
        "lien_he": "sv@neu.edu.vn",
        "vi_tri": "Phòng A1-401",
        "muc_do": "trung_binh",
        "ten_vat_chat": "Đèn tuýp LED nhấp nháy",
        "mo_ta_chi_tiet": "Đèn ở dãy bàn đầu bị chớp liên tục gây mỏi mắt"
    }, follow_redirects=False)

    assert res.status_code == 302
    assert "/bao-cao-hu-hai/cam-on" in res.location

    # Kiểm tra trang cảm ơn
    res_cam_on = client.get("/bao-cao-hu-hai/cam-on")
    assert res_cam_on.status_code == 200
    assert "CẢM ƠN BẠN ĐÃ GỬI BÁO CÁO" in res_cam_on.text

def test_quan_ly_tai_san_xu_ly_bao_cao_hu_hai(client, auth):
    """Test Bộ phận Quản lý tài sản tiếp nhận, xác minh hiện trường và xử lý sự cố hư hại."""
    # 1. Công chúng / sinh viên gửi 1 báo cáo sự cố hư hại
    client.post("/bao-cao-hu-hai", data={
        "ho_ten": "Giảng viên phản ánh",
        "lien_he": "0912345678",
        "vi_tri": "Hội trường A",
        "muc_do": "nghiem_trong",
        "ten_vat_chat": "Micro không dây mất tiếng",
        "mo_ta_chi_tiet": "Micro bị rè và không lên nguồn"
    })

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
    # 1. Báo cáo sự cố
    client.post("/bao-cao-hu-hai", data={
        "ho_ten": "Ban quản lý giảng đường",
        "lien_he": "0987654321",
        "vi_tri": "Phòng D2-501",
        "muc_do": "nghiem_trong",
        "ten_vat_chat": "Máy chiếu hỏng bo mạch chính",
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


def test_nut_bao_cao_hu_hai_hien_thi_dung(client, auth):
    """Test nút báo cáo hư hại chỉ hiển thị trên trang chủ khi chưa đăng nhập, sau khi đăng nhập bị xóa hoàn toàn."""
    # 1. Khi chưa đăng nhập:
    res_home = client.get("/")
    assert res_home.status_code == 200
    # Trang chủ có nút Báo cáo hư hại vật chất
    assert "Báo cáo hư hại vật chất" in res_home.text
    # Trên trang đăng nhập không có nút báo cáo hư hại
    res_login = client.get("/dang-nhap")
    assert "/bao-cao-hu-hai" not in res_login.text

    # 2. Sau khi đăng nhập (ví dụ cán bộ mua sắm):
    auth.login(vai_tro="mua_sam")
    res_home_auth = client.get("/")
    assert res_home_auth.status_code == 200
    # Nút báo cáo hư hại đã bị xóa hoàn toàn khỏi trang chủ
    assert "Báo cáo hư hại vật chất" not in res_home_auth.text
    assert "/bao-cao-hu-hai" not in res_home_auth.text

    # Các trang nội bộ cũng không có nút báo cáo hư hại
    res_muasam = client.get("/mua-sam/")
    assert "/bao-cao-hu-hai" not in res_muasam.text

