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

def test_admin_xu_ly_bao_cao_hu_hai(client, auth):
    """Test Admin xem và cập nhật trạng thái xử lý báo cáo hư hại."""
    # 1. Gửi 1 báo cáo trước
    client.post("/bao-cao-hu-hai", data={
        "ho_ten": "Giảng viên phản ánh",
        "lien_he": "0912345678",
        "vi_tri": "Hội trường A",
        "muc_do": "nghiem_trong",
        "ten_vat_chat": "Micro không dây mất tiếng"
    })

    # 2. Admin vào xem danh sách báo cáo
    auth.login(vai_tro="quan_tri")
    res_list = client.get("/admin/bao-cao-hu-hai")
    assert res_list.status_code == 200
    assert "Micro không dây mất tiếng" in res_list.text

    # 3. Admin cập nhật trạng thái đã xử lý
    res_update = client.post("/admin/bao-cao-hu-hai/1/xu-ly", data={"trang_thai": "da_xu_ly"}, follow_redirects=True)
    assert res_update.status_code == 200
    assert "Đã cập nhật trạng thái xử lý báo cáo hư hại" in res_update.text

