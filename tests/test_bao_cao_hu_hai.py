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


def test_quy_trinh_8_buoc_m09_sua_chua(client, auth):
    """
    Test luồng xử lý phiếu hư hại 8 bước chuẩn của Phân hệ M09 (Phòng QTTB):
    1. Chờ tiếp nhận -> Tiếp nhận (chuyển sang Khảo sát BM03)
    2. Lập khảo sát BM03 (chuyển sang Chờ duyệt phương án)
    3. Lập phương án & phê duyệt (chuyển sang Đang sửa chữa)
    4. Cập nhật tiến độ thi công
    5. Lập biên bản nghiệm thu (chuyển sang Chờ nghiệm thu)
    6. Đánh giá nghiệm thu đạt -> Hoàn thành (cập nhật tài sản bình thường)
    """
    # 1. Cán bộ đơn vị gửi báo cáo sự cố
    auth.login(vai_tro="don_vi")
    res_tao = client.post("/don-vi/sua-chua/tao", data={
        "ten_vat_chat": "Điều hòa Daikin phòng 302 không mát",
        "vi_tri": "Phòng A1-302",
        "do_khan_cap": "trung_binh",
        "muc_do": "trung_binh",
        "loai_yeu_cau": "sua_chua_thiet_bi",
        "mo_ta_chi_tiet": "Bật 16 độ nhưng chỉ có gió, không mát"
    }, follow_redirects=True)
    assert res_tao.status_code == 200

    # Lấy ID phiếu vừa tạo
    auth.login(vai_tro="quan_ly_kho")
    res_list = client.get("/tai-san/bao-cao-hu-hai")
    assert res_list.status_code == 200
    assert "Điều hòa Daikin phòng 302 không mát" in res_list.text

    # Giả sử phiếu vừa tạo có id
    with client.application.app_context():
        from app.db import get_db
        bc = get_db().execute("SELECT id FROM bao_cao_hu_hai WHERE vi_tri = 'Phòng A1-302'").fetchone()
    bc_id = bc["id"]

    # Bước 1: Tiếp nhận yêu cầu
    res_tn = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/tiep-nhan", follow_redirects=True)
    assert res_tn.status_code == 200

    # Bước 2: Lập biên bản khảo sát BM03
    res_ks = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/khao-sat", data={
        "thanh_phan_khao_sat": "Nguyễn Văn Kho (QTTB), Lê Văn Đơn Vị",
        "hien_trang_thuc_te": "Hết gas làm lạnh, ống đồng rò rỉ nhẹ",
        "nguyen_nhan_hu_hong": "Sử dụng lâu năm hở van",
        "muc_do_hu_hong": "trung_binh",
        "nhom_sua_chua": "sua_chua_nho",
        "tinh_trang_bao_hanh": "het_han",
        "anh_huong_an_toan": "Không gây nguy hiểm, chỉ ảnh hưởng phòng học",
        "khoi_luong_du_kien": "Hàn ống đồng và nạp đầy gas R32"
    }, follow_redirects=True)
    assert res_ks.status_code == 200

    # Bước 3: Lập phương án trình duyệt
    res_pa = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/phuong-an", data={
        "phuong_an_chi_tiet": "Thuê thợ bảo dưỡng ngoài nạp gas",
        "kinh_phi_du_kien": "1200000",
        "nguon_kinh_phi": "Kinh phí thường xuyên",
        "yeu_cau_m08": "0"
    }, follow_redirects=True)
    assert res_pa.status_code == 200

    # Phê duyệt phương án
    res_duyet_pa = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/phe-duyet-phuong-an", data={
        "y_kien": "Đồng ý phương án sửa chữa",
        "don_vi_thi_cong": "Công ty Cơ điện Lạnh Hà Nội"
    }, follow_redirects=True)
    assert res_duyet_pa.status_code == 200

    # Bước 4: Cập nhật nhật ký tiến độ
    res_td = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/tien-do", data={
        "nhat_ky": "Đã hàn ống đồng, nạp 1.2kg gas R32, máy bắt đầu chạy lạnh 18 độ"
    }, follow_redirects=True)
    assert res_td.status_code == 200

    # Bước 5: Lập biên bản nghiệm thu
    res_lap_nt = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/lap-nghiem-thu", data={
        "y_kien": "Điều hòa hoạt động mát sâu, áp suất gas ổn định"
    }, follow_redirects=True)
    assert res_lap_nt.status_code == 200

    # Bước 6: Đánh giá nghiệm thu ĐẠT
    res_dg = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/danh-gia-nghiem-thu", data={
        "ket_qua": "dat",
        "y_kien_nghiem_thu": "Nghiệm thu đạt yêu cầu vận hành"
    }, follow_redirects=True)
    assert res_dg.status_code == 200
    assert "Nghiệm thu ĐẠT" in res_dg.text

    assert "/bao-cao-hu-hai" not in res_muasam.text


def test_quy_trinh_8_buoc_m09_sua_chua(client, auth):
    """
    Test luồng xử lý phiếu hư hại 8 bước chuẩn của Phân hệ M09 (Phòng QTTB):
    1. Chờ tiếp nhận -> Tiếp nhận (chuyển sang Khảo sát BM03)
    2. Lập khảo sát BM03 (chuyển sang Chờ duyệt phương án)
    3. Lập phương án & phê duyệt (chuyển sang Đang sửa chữa)
    4. Cập nhật tiến độ thi công
    5. Lập biên bản nghiệm thu (chuyển sang Chờ nghiệm thu)
    6. Đánh giá nghiệm thu đạt -> Hoàn thành (cập nhật tài sản bình thường)
    """
    # 1. Cán bộ đơn vị gửi báo cáo sự cố
    auth.login(vai_tro="don_vi")
    res_tao = client.post("/don-vi/sua-chua/tao", data={
        "ten_vat_chat": "Điều hòa Daikin phòng 302 không mát",
        "vi_tri": "Phòng A1-302",
        "do_khan_cap": "trung_binh",
        "muc_do": "trung_binh",
        "loai_yeu_cau": "sua_chua_thiet_bi",
        "mo_ta_chi_tiet": "Bật 16 độ nhưng chỉ có gió, không mát"
    }, follow_redirects=True)
    assert res_tao.status_code == 200

    # Lấy ID phiếu vừa tạo
    auth.login(vai_tro="quan_ly_kho")
    res_list = client.get("/tai-san/bao-cao-hu-hai")
    assert res_list.status_code == 200
    assert "Điều hòa Daikin phòng 302 không mát" in res_list.text

    # Giả sử phiếu vừa tạo có id
    with client.application.app_context():
        from app.db import get_db
        bc = get_db().execute("SELECT id FROM bao_cao_hu_hai WHERE vi_tri = 'Phòng A1-302'").fetchone()
    bc_id = bc["id"]

    # Bước 1: Tiếp nhận yêu cầu
    res_tn = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/tiep-nhan", follow_redirects=True)
    assert res_tn.status_code == 200

    # Bước 2: Lập biên bản khảo sát BM03
    res_ks = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/khao-sat", data={
        "thanh_phan_khao_sat": "Nguyễn Văn Kho (QTTB), Lê Văn Đơn Vị",
        "hien_trang_thuc_te": "Hết gas làm lạnh, ống đồng rò rỉ nhẹ",
        "nguyen_nhan_hu_hong": "Sử dụng lâu năm hở van",
        "muc_do_hu_hong": "trung_binh",
        "nhom_sua_chua": "sua_chua_nho",
        "tinh_trang_bao_hanh": "het_han",
        "anh_huong_an_toan": "Không gây nguy hiểm, chỉ ảnh hưởng phòng học",
        "khoi_luong_du_kien": "Hàn ống đồng và nạp đầy gas R32"
    }, follow_redirects=True)
    assert res_ks.status_code == 200

    # Bước 3: Lập phương án trình duyệt
    res_pa = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/phuong-an", data={
        "phuong_an_chi_tiet": "Thuê thợ bảo dưỡng ngoài nạp gas",
        "kinh_phi_du_kien": "1200000",
        "nguon_kinh_phi": "Kinh phí thường xuyên",
        "yeu_cau_m08": "0"
    }, follow_redirects=True)
    assert res_pa.status_code == 200

    # Phê duyệt phương án
    res_duyet_pa = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/phe-duyet-phuong-an", data={
        "y_kien": "Đồng ý phương án sửa chữa",
        "don_vi_thi_cong": "Công ty Cơ điện Lạnh Hà Nội"
    }, follow_redirects=True)
    assert res_duyet_pa.status_code == 200

    # Bước 4: Cập nhật nhật ký tiến độ
    res_td = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/tien-do", data={
        "nhat_ky": "Đã hàn ống đồng, nạp 1.2kg gas R32, máy bắt đầu chạy lạnh 18 độ"
    }, follow_redirects=True)
    assert res_td.status_code == 200

    # Bước 5: Lập biên bản nghiệm thu
    res_lap_nt = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/lap-nghiem-thu", data={
        "y_kien": "Điều hòa hoạt động mát sâu, áp suất gas ổn định"
    }, follow_redirects=True)
    assert res_lap_nt.status_code == 200

    # Bước 6: Đánh giá nghiệm thu ĐẠT
    res_dg = client.post(f"/tai-san/bao-cao-hu-hai/{bc_id}/danh-gia-nghiem-thu", data={
        "ket_qua": "dat",
        "y_kien_nghiem_thu": "Nghiệm thu đạt yêu cầu vận hành"
    }, follow_redirects=True)
    assert res_dg.status_code == 200
    assert "Nghiệm thu ĐẠT" in res_dg.text

