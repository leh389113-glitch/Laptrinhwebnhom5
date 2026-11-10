import pytest
from app.db import get_db

def test_routes_bao_cao_hu_hai_da_duoc_go_bo(client):
    """Đảm bảo các endpoint báo cáo hư hại không còn được đăng ký."""
    for path in (
        "/bao-cao-hu-hai",
        "/bao-cao-hu-hai/cam-on",
        "/tai-san/bao-cao-hu-hai",
        "/admin/bao-cao-hu-hai",
    ):
        assert client.get(path).status_code == 404

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
    assert "Ban Quản lý Tòa A1".encode("utf-8") in res.data
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
        yc = db.execute("SELECT * FROM yeu_cau_sua_chua WHERE ten_vat_chat = 'Máy chiếu Panasonic PT-LB386'").fetchone()
        assert yc is not None
        assert yc["ma_yeu_cau"].startswith("YC-")
        assert yc["nguoi_tao_id"] is not None
        assert yc["don_vi"] == "Ban Quản lý Tòa A1"
        assert yc["noi_dung"] == "Bóng đèn máy chiếu bị mờ nhạt không đọc được văn bản."
        assert yc["do_khan_cap"] == "can_som"

def test_gui_yeu_cau_sua_chua_co_tai_san_don_vi(client, auth, app):
    """Chọn tài sản trong danh mục đơn vị phải lưu được mà không phụ thuộc JS tự điền."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, vi_tri, phong_ban, don_vi_su_dung,
                ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat
            )
            VALUES (
                'TS-2026-DONVI-01', 'Điều hòa Ban A1', 'Phòng A1-201',
                'Ban Quản lý Tòa A1', 'Ban Quản lý Tòa A1',
                '2026-01-01', 'dang_su_dung', '2026-01-01', '2026-01-01'
            )
            """
        )
        tai_san_id = cur.lastrowid
        db.commit()

    auth.login(vai_tro="don_vi")
    form = client.get("/don-vi/sua-chua/tao")
    assert form.status_code == 200
    assert b"TS-2026-DONVI-01" in form.data

    response = client.post(
        "/don-vi/sua-chua/tao",
        data={
            "tai_san_id": str(tai_san_id),
            "loai_yeu_cau": "sua_chua_thiet_bi",
            "do_khan_cap": "can_som",
            "muc_do": "trung_binh",
            "mo_ta_chi_tiet": "Điều hòa không làm mát."
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "Đã gửi thành công Yêu cầu sửa chữa".encode("utf-8") in response.data

    with app.app_context():
        db = get_db()
        yc = db.execute(
            "SELECT tai_san_id, ten_vat_chat, vi_tri FROM yeu_cau_sua_chua WHERE tai_san_id = ?",
            (tai_san_id,)
        ).fetchone()
        assert yc is not None
        assert yc["tai_san_id"] == tai_san_id
        assert yc["ten_vat_chat"] == "Điều hòa Ban A1"
        assert yc["vi_tri"] == "Phòng A1-201"

def test_tai_san_ban_giao_hien_thi_cho_don_vi_va_danh_muc_tu_dong_cap_nhat(client, auth, app):
    with app.app_context():
        db = get_db()
        a1 = db.execute(
            "SELECT id, mat_khau_hash FROM nguoi_dung WHERE ten_dang_nhap = 'user_don_vi'"
        ).fetchone()
        cursor = db.execute(
            """
            INSERT INTO nguoi_dung (
                ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, don_vi,
                ngay_tao, trang_thai
            ) VALUES (
                'Cán bộ Ban Quản lý A2', 'bql-a2@neu.test', 'user_bql_a2',
                ?, 'don_vi', 'Ban Quản lý Tòa A2', '2026-01-01', 'hoat_dong'
            )
            """,
            (a1["mat_khau_hash"],)
        )
        a2_id = cursor.lastrowid
        cursor = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, vi_tri, phong_ban, don_vi_su_dung,
                nguoi_su_dung_id, ngay_tiep_nhan, trang_thai,
                xac_nhan_ban_giao_don_vi, ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-A2-NHAN-001', 'Máy chiếu A2', 'Phòng A2-101',
                'Kho QTTB', 'Kho QTTB', ?, '2026-01-01', 'dang_su_dung',
                0, '2026-01-01', '2026-01-01'
            )
            """,
            (a2_id,)
        )
        tai_san_id = cursor.lastrowid
        db.commit()

    auth.login(username="user_bql_a2")
    form = client.get("/don-vi/sua-chua/tao")
    assert form.status_code == 200
    assert b"TS-A2-NHAN-001" in form.data
    assert "tự làm mới mỗi 30 giây".encode("utf-8") in form.data
    assert client.get("/don-vi/tai-san").status_code == 200
    assert "TS-A2-NHAN-001".encode("utf-8") in client.get("/don-vi/tai-san").data
    chi_tiet = client.get(f"/don-vi/tai-san/{tai_san_id}")
    assert chi_tiet.status_code == 200
    assert "Máy chiếu A2".encode("utf-8") in chi_tiet.data

    with app.app_context():
        db = get_db()
        db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, vi_tri, phong_ban, don_vi_su_dung,
                nguoi_su_dung_id, ngay_tiep_nhan, trang_thai,
                xac_nhan_ban_giao_don_vi, ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-A2-NHAN-002', 'Máy in A2', 'Văn phòng A2',
                'Kho QTTB', 'Kho QTTB', ?, '2026-01-01', 'dang_su_dung',
                0, '2026-01-01', '2026-01-01'
            )
            """,
            (a2_id,)
        )
        db.commit()

    danh_muc = client.get("/don-vi/sua-chua/danh-muc-tai-san")
    assert danh_muc.status_code == 200
    ma_tai_san_moi = {tai_san["ma_tai_san"] for tai_san in danh_muc.json}
    assert {"TS-A2-NHAN-001", "TS-A2-NHAN-002"} <= ma_tai_san_moi

    assert client.post(
        f"/don-vi/tai-san/{tai_san_id}/xac-nhan-ban-giao",
        data={"ghi_chu": "Đã nhận"}
    ).status_code == 302
    with app.app_context():
        tai_san = get_db().execute(
            "SELECT nguoi_su_dung_id, xac_nhan_ban_giao_don_vi FROM tai_san WHERE id = ?",
            (tai_san_id,)
        ).fetchone()
        assert tai_san["nguoi_su_dung_id"] == a2_id
        assert tai_san["xac_nhan_ban_giao_don_vi"] == 1

    auth.login(vai_tro="don_vi")
    assert b"TS-A2-NHAN-001" not in client.get("/don-vi/tai-san").data
    forbidden_detail = client.get(f"/don-vi/tai-san/{tai_san_id}")
    assert forbidden_detail.status_code == 302

def test_khong_cho_chon_tai_san_don_vi_khac(client, auth, app):
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, vi_tri, phong_ban, don_vi_su_dung,
                ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat
            )
            VALUES (
                'TS-2026-DONVI-02', 'Máy tính Ban A2', 'Phòng A2-101',
                'Ban Quản lý Tòa A2', 'Ban Quản lý Tòa A2',
                '2026-01-01', 'dang_su_dung', '2026-01-01', '2026-01-01'
            )
            """
        )
        tai_san_id = cur.lastrowid
        db.commit()

    auth.login(vai_tro="don_vi")
    response = client.post(
        "/don-vi/sua-chua/tao",
        data={
            "tai_san_id": str(tai_san_id),
            "loai_yeu_cau": "sua_chua_thiet_bi",
            "ten_vat_chat": "Máy tính Ban A2",
            "vi_tri": "Phòng A2-101",
            "mo_ta_chi_tiet": "Không khởi động."
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert "không thuộc danh mục quản lý".encode("utf-8") in response.data
    with app.app_context():
        assert get_db().execute(
            "SELECT 1 FROM yeu_cau_sua_chua WHERE tai_san_id = ?", (tai_san_id,)
        ).fetchone() is None

def test_xac_nhan_khao_sat_va_nghiem_thu_sua_chua(client, auth, app):
    """Kiểm tra luồng tiếp nhận, BM03, duyệt phương án và nghiệm thu M09."""
    with app.app_context():
        db = get_db()
        u = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_don_vi'").fetchone()
        cur = db.execute(
            """
            INSERT INTO yeu_cau_sua_chua (
                ma_yeu_cau, nguoi_tao_id, don_vi, ten_vat_chat, vi_tri,
                loai_sua_chua, noi_dung, ngay_tiep_nhan, trang_thai, ghi_chu
            ) VALUES ('YC-TEST-001', ?, 'Ban Quản lý Tòa A1', 'Điều hòa Daikin', 'Phòng A1-201',
                     'sua_chua_thiet_bi', 'Không mát', '2026-11-09 08:00:00', 'cho_tiep_nhan', '')
            """,
            (u["id"],)
        )
        db.commit()
        yc_id = cur.lastrowid

    auth.login(vai_tro="quan_ly_kho")
    res_tiep_nhan = client.post(
        f"/tai-san/sua-chua/{yc_id}/tiep-nhan",
        data={"hanh_dong": "tiep_nhan", "noi_dung": "Đã kiểm tra thông tin ban đầu"},
        follow_redirects=True
    )
    assert res_tiep_nhan.status_code == 200
    assert client.post(f"/tai-san/sua-chua/{yc_id}/khao-sat/bat-dau").status_code == 302

    from io import BytesIO
    res_khao_sat = client.post(
        f"/tai-san/sua-chua/{yc_id}/khao-sat",
        data={
            "thanh_phan_khao_sat": "Kỹ thuật viên QTTB, đại diện đơn vị",
            "tinh_trang_bao_hanh": "Còn bảo hành",
            "phan_loai_yeu_cau": "thiet_bi",
            "hien_trang": "Máy không làm lạnh",
            "nguyen_nhan_du_kien": "Lỗi máy nén",
            "muc_do_hu_hong": "nghiem_trong",
            "anh_huong_an_toan": "Không ảnh hưởng an toàn",
            "khoi_luong_cong_viec": "Kiểm tra và thay máy nén",
            "hinh_anh": (BytesIO(b"\x89PNG\r\n\x1a\nimage"), "khao-sat.png")
        },
        content_type="multipart/form-data",
        follow_redirects=True
    )
    assert res_khao_sat.status_code == 200
    assert "Biên bản khảo sát hiện trạng (BM03)".encode("utf-8") in res_khao_sat.data

    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT trang_thai FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["trang_thai"] == "dang_khao_sat"
        tep = db.execute("SELECT id FROM yeu_cau_sua_chua_tep").fetchone()
        tep_id = tep["id"]

    res_anh = client.get(f"/tai-san/sua-chua/tep/{tep_id}")
    assert res_anh.status_code == 200
    assert res_anh.mimetype == "image/png"
    res_khao_sat_lan_hai = client.post(
        f"/tai-san/sua-chua/{yc_id}/khao-sat",
        data={
            "thanh_phan_khao_sat": "QTTB",
            "phan_loai_yeu_cau": "thiet_bi",
            "hien_trang": "Khảo sát lặp",
            "muc_do_hu_hong": "nhe"
        },
        follow_redirects=True
    )
    assert "đã được lập, không thể lập lại".encode("utf-8") in res_khao_sat_lan_hai.data
    with app.app_context():
        db = get_db()
        assert db.execute(
            "SELECT COUNT(*) FROM yeu_cau_sua_chua_lich_su WHERE yeu_cau_id = ? AND loai_su_kien = 'khao_sat'",
            (yc_id,)
        ).fetchone()[0] == 1

    auth.login(vai_tro="don_vi")
    res_ks = client.post(
        f"/don-vi/sua-chua/{yc_id}/xac-nhan-khao-sat",
        data={"ghi_chu": "Đồng ý hiện trạng máy hỏng lốc"},
        follow_redirects=True
    )
    assert res_ks.status_code == 200

    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT * FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["xac_nhan_khao_sat_don_vi"] == 1

    auth.login(vai_tro="quan_ly_kho")
    res_phuong_an = client.post(
        f"/tai-san/sua-chua/{yc_id}/phuong-an",
        data={
            "phuong_an": "sua_chua",
            "phuong_an_chi_tiet": "Thay máy nén",
            "chi_phi_du_kien": "2500000"
        },
        follow_redirects=True
    )
    assert res_phuong_an.status_code == 200
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/phe-duyet-phuong-an",
        data={"ghi_chu": "Duyệt"},
        follow_redirects=True
    ).status_code == 403

    auth.login(vai_tro="quan_tri")
    res_admin_duyet = client.post(
        f"/tai-san/sua-chua/{yc_id}/phe-duyet-phuong-an",
        data={"ghi_chu": "Đồng ý phương án"},
        follow_redirects=True
    )
    assert res_admin_duyet.status_code == 200

    auth.login(vai_tro="quan_ly_kho")
    res_lap_bb = client.post(
        f"/tai-san/sua-chua/{yc_id}/nghiem-thu",
        data={"chi_phi_thuc_te": "2400000", "ghi_chu": "Đã chạy thử"},
        follow_redirects=True
    )
    assert res_lap_bb.status_code == 200
    assert "chờ đơn vị xác nhận".encode("utf-8") in res_lap_bb.data

    auth.login(vai_tro="don_vi")
    res_khong_dat = client.post(
        f"/don-vi/sua-chua/{yc_id}/nghiem-thu",
        data={"ket_qua": "khong_dat", "ghi_chu": "Máy vẫn chưa đủ lạnh"},
        follow_redirects=True
    )
    assert res_khong_dat.status_code == 200
    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT trang_thai FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["trang_thai"] == "khong_dat_yeu_cau"

    auth.login(vai_tro="quan_ly_kho")
    assert client.post(f"/tai-san/sua-chua/{yc_id}/bat-dau", follow_redirects=True).status_code == 200
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/nghiem-thu",
        data={"chi_phi_thuc_te": "2400000", "ghi_chu": "Đã khắc phục"},
        follow_redirects=True
    ).status_code == 200

    auth.login(vai_tro="don_vi")
    res_nt = client.post(
        f"/don-vi/sua-chua/{yc_id}/nghiem-thu",
        data={"ket_qua": "dat", "ghi_chu": "Thiết bị hoạt động tốt"},
        follow_redirects=True
    )
    assert res_nt.status_code == 200

    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT * FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["xac_nhan_nghiem_thu_don_vi"] == 1
        assert yc["trang_thai"] == "cho_lap_ho_so_thanh_toan"

    auth.login(vai_tro="quan_ly_kho")
    draft = client.post(f"/tai-san/sua-chua/{yc_id}/ho-so-thanh-toan", data={
        "nguoi_de_nghi_ten": "Cán bộ QTTB",
        "hanh_dong": "luu"
    }, follow_redirects=True)
    assert draft.status_code == 200
    with app.app_context():
        db = get_db()
        assert db.execute(
            "SELECT trang_thai FROM thanh_toan_sua_chua WHERE yeu_cau_sua_chua_id = ?",
            (yc_id,)
        ).fetchone()["trang_thai"] == "nhap"
    auth.login(vai_tro="ke_toan")
    assert "YC-TEST-001" not in client.get("/ke-toan/").text

    auth.login(vai_tro="quan_ly_kho")
    res_gui = client.post(f"/tai-san/sua-chua/{yc_id}/ho-so-thanh-toan", data={
        "nguoi_de_nghi_ten": "Cán bộ QTTB",
        "don_vi": "Phòng Quản trị thiết bị",
        "ve_khoan": "Sửa chữa điều hòa",
        "hop_dong_so": "HD-SC-01",
        "hop_dong_ngay": "2026-11-09",
        "so_tien": "2400000",
        "so_tien_bang_chu": "Hai triệu bốn trăm nghìn đồng",
        "don_vi_thu_huong": "Đơn vị sửa chữa A",
        "so_tai_khoan": "123456789",
        "ngan_hang": "Ngân hàng A",
        "ho_so_kem_theo": ["bien_ban_nghiem_thu", "hoa_don"],
        "ho_so_khac": "Biên bản khối lượng",
        "tai_lieu": (BytesIO(b"%PDF-1.4 test invoice"), "hoa-don.pdf"),
        "hanh_dong": "gui"
    }, follow_redirects=True)
    assert res_gui.status_code == 200
    assert "Đã gửi hồ sơ thanh toán sang Kế toán".encode("utf-8") in res_gui.data

    auth.login(vai_tro="ke_toan")
    danh_sach = client.get("/ke-toan/")
    assert danh_sach.status_code == 200
    assert "YC-TEST-001" in danh_sach.text
    chi_tiet = client.get(f"/ke-toan/sua-chua/{yc_id}")
    assert chi_tiet.status_code == 200
    assert "Đơn vị sửa chữa A" in chi_tiet.text
    assert "hoa-don.pdf" in chi_tiet.text
    with app.app_context():
        file_id = get_db().execute(
            "SELECT id FROM thanh_toan_sua_chua_tep WHERE ten_tep = 'hoa-don.pdf'"
        ).fetchone()["id"]
    tep_thanh_toan = client.get(
        f"/tai-san/sua-chua/ho-so-thanh-toan/tep/{file_id}"
    )
    assert tep_thanh_toan.status_code == 200
    assert tep_thanh_toan.data == b"%PDF-1.4 test invoice"
    print_giay = client.get(f"/tai-san/sua-chua/{yc_id}/ho-so-thanh-toan/in")
    assert print_giay.status_code == 200
    assert "GIẤY ĐỀ NGHỊ THANH TOÁN" in print_giay.text

    auth.login(vai_tro="quan_tri")
    assert client.post(
        f"/ke-toan/sua-chua/{yc_id}/xac-nhan-thanh-toan",
        data={"ghi_chu": "Admin không được thanh toán"}
    ).status_code == 403

    auth.login(vai_tro="ke_toan")
    assert client.post(f"/ke-toan/sua-chua/{yc_id}/tiep-nhan").status_code == 302
    assert client.post(
        f"/ke-toan/sua-chua/{yc_id}/bo-sung",
        data={"ghi_chu": "Bổ sung hóa đơn hợp lệ"}
    ).status_code == 302

    auth.login(vai_tro="quan_ly_kho")
    res_bo_sung = client.post(f"/tai-san/sua-chua/{yc_id}/ho-so-thanh-toan", data={
        "nguoi_de_nghi_ten": "Cán bộ QTTB",
        "don_vi": "Phòng Quản trị thiết bị",
        "ve_khoan": "Sửa chữa điều hòa",
        "hop_dong_so": "HD-SC-01",
        "hop_dong_ngay": "2026-11-09",
        "so_tien": "2400000",
        "so_tien_bang_chu": "Hai triệu bốn trăm nghìn đồng",
        "don_vi_thu_huong": "Đơn vị sửa chữa A",
        "so_tai_khoan": "123456789",
        "ngan_hang": "Ngân hàng A",
        "ho_so_kem_theo": ["bien_ban_nghiem_thu", "hoa_don"],
        "ho_so_khac": "Đã bổ sung hóa đơn",
        "hanh_dong": "gui"
    }, follow_redirects=True)
    assert res_bo_sung.status_code == 200

    auth.login(vai_tro="ke_toan")
    assert "YC-TEST-001" not in client.get("/ke-toan/lich-su").text
    assert client.post(f"/ke-toan/sua-chua/{yc_id}/tiep-nhan").status_code == 302
    assert client.post(
        f"/ke-toan/sua-chua/{yc_id}/xac-nhan-thanh-toan",
        data={"ghi_chu": "Đã chuyển khoản"}
    ).status_code == 302
    lich_su = client.get("/ke-toan/lich-su")
    assert lich_su.status_code == 200
    assert "Lịch sử thanh toán sửa chữa M09" in lich_su.text
    assert "YC-TEST-001" in lich_su.text
    assert "Đơn vị sửa chữa A" in lich_su.text
    assert "Ke Toan Test" in lich_su.text
    auth.login(vai_tro="quan_ly_kho")
    assert "Hoàn tất" in client.get(f"/tai-san/sua-chua/{yc_id}").text
    auth.login(vai_tro="ke_toan")
    assert "Trạng thái:</strong> Hoàn tất" in client.get(
        f"/ke-toan/sua-chua/{yc_id}"
    ).text
    with app.app_context():
        db = get_db()
        yc = db.execute(
            "SELECT trang_thai FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)
        ).fetchone()
        ho_so = db.execute(
            "SELECT trang_thai, ghi_chu_ke_toan FROM thanh_toan_sua_chua WHERE yeu_cau_sua_chua_id = ?",
            (yc_id,)
        ).fetchone()
        assert yc["trang_thai"] == "da_thanh_toan"
        assert ho_so["trang_thai"] == "da_thanh_toan"
        assert ho_so["ghi_chu_ke_toan"] == "Đã chuyển khoản"

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
        assert dn["don_vi_de_nghi"] == "Ban Quản lý Tòa A1"
        assert dn["tong_du_toan"] == (10 * 30000000) + (10 * 5000000)
        assert dn["trang_thai"] == "cho_lanh_dao_duyet"  # >= 100tr

def test_tai_san_don_vi_va_xac_nhan_ban_giao(client, auth, app):
    """Kiểm tra danh mục tài sản đơn vị và thao tác ký nhận bàn giao BM03."""
    with app.app_context():
        db = get_db()
        nguoi_nhan_id = db.execute(
            "SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_don_vi'"
        ).fetchone()["id"]
        cur = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, nguoi_su_dung_id, ngay_tiep_nhan, trang_thai, xac_nhan_ban_giao_don_vi,
                ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-TEST-999', 'Máy chủ AI Server', 'Máy chủ', 'tai_san_co_dinh',
                'binh_thuong', 'Lab 501', 'Ban Quản lý Tòa A1', 'Ban Quản lý Tòa A1',
                120000000, ?, '2026-11-09', 'dang_su_dung', 0,
                '2026-11-09 08:00:00', '2026-11-09 08:00:00'
            )
            """,
            (nguoi_nhan_id,)
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
        
        # Tạo tài sản của Ban Quản lý Tòa A1
        cur_ts = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, xac_nhan_ban_giao_don_vi,
                ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-KK-001', 'Máy in HP LaserJet', 'Máy in', 'cong_cu_dung_cu',
                'binh_thuong', 'Văn phòng Ban Quản lý Tòa A1', 'Ban Quản lý Tòa A1', 'Ban Quản lý Tòa A1',
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
