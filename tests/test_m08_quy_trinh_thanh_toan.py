from app.db import get_db
import sqlite3

from app.db import init_db


def test_m08_quy_trinh_khoa_cac_buoc_va_gui_phieu_sang_ke_toan(client, auth, app):
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Mua thiết bị trình chiếu",
        "don_vi_de_nghi": "Ban Quản lý Tòa A1",
        "ten_hang_hoa[]": ["Máy chiếu"],
        "don_vi_tinh[]": ["Chiếc"],
        "so_luong[]": ["1"],
        "don_gia_du_kien[]": ["55000000"]
    })

    res_bao_gia_som = client.post(
        "/mua-sam/de-nghi/1/bao-gia",
        data={"nha_cung_cap": "NCC sớm", "tong_gia": "55000000"},
        follow_redirects=True
    )
    assert "khảo sát nhu cầu BM02 trước" in res_bao_gia_som.text

    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát hiện trạng",
        "ket_luan": "chua_du"
    })
    res_bao_gia_khong_phu_hop = client.post(
        "/mua-sam/de-nghi/1/bao-gia",
        data={"nha_cung_cap": "NCC", "tong_gia": "55000000"},
        follow_redirects=True
    )
    assert "kết luận khảo sát BM02 là phù hợp" in res_bao_gia_khong_phu_hop.text

    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát bổ sung",
        "ket_luan": "phu_hop"
    })
    for ten_ncc in ("NCC A", "NCC B", "NCC C"):
        client.post("/mua-sam/de-nghi/1/bao-gia", data={
            "nha_cung_cap": ten_ncc,
            "tong_gia": "55000000"
        })
    res_ncc_trung = client.post(
        "/mua-sam/de-nghi/1/bao-gia",
        data={"nha_cung_cap": "ncc a", "tong_gia": "54000000"},
        follow_redirects=True
    )
    assert "nhà cung cấp độc lập" in res_ncc_trung.text.lower()

    res_chon_thieu = client.post(
        "/mua-sam/de-nghi/1/chon-bao-gia/1",
        follow_redirects=True
    )
    assert "tối thiểu 3 báo giá" in res_chon_thieu.text

    client.post("/mua-sam/de-nghi/1/chon-bao-gia/2")
    res_chon_lai = client.post(
        "/mua-sam/de-nghi/1/chon-bao-gia/3",
        follow_redirects=True
    )
    assert "đã được chốt và không thể chọn lại" in res_chon_lai.text
    res_them_sau_chot = client.post(
        "/mua-sam/de-nghi/1/bao-gia",
        data={"nha_cung_cap": "NCC D", "tong_gia": "54000000"},
        follow_redirects=True
    )
    assert "đã chốt nhà cung cấp" in res_them_sau_chot.text.lower()

    res_nghiem_thu_chua_duyet = client.post(
        "/mua-sam/de-nghi/1/nghiem-thu",
        data={"ket_qua": "dat"},
        follow_redirects=True
    )
    assert "sau khi đề nghị đã được phê duyệt" in res_nghiem_thu_chua_duyet.text

    auth.login(username="user_truong_mua_sam")
    client.post("/mua-sam/de-nghi/1/phe-duyet")
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/nghiem-thu", data={
        "ket_qua": "dat",
        "y_kien_danh_gia": "Đạt yêu cầu"
    })
    res_de_nghi_som = client.post(
        "/mua-sam/de-nghi/1/de-nghi-thanh-toan",
        data={"noi_dung_thanh_toan": "Chưa tiếp nhận"},
        follow_redirects=True
    )
    assert "sau khi M09 đã tiếp nhận" in res_de_nghi_som.text

    auth.login(vai_tro="quan_ly_kho")
    res_m09 = client.get("/tai-san/tiep-nhan")
    assert "DN-" in res_m09.text
    client.post("/tai-san/tiep-nhan/1", data={"ghi_chu": "Đã nhận"})

    auth.login(vai_tro="mua_sam")
    res_tao_phieu = client.post(
        "/mua-sam/de-nghi/1/de-nghi-thanh-toan",
        data={"noi_dung_thanh_toan": "Thanh toán tiền mua máy chiếu"},
        follow_redirects=True
    )
    assert "gửi phiếu thanh toán TT-" in res_tao_phieu.text
    res_trung_phieu = client.post(
        "/mua-sam/de-nghi/1/de-nghi-thanh-toan",
        data={"noi_dung_thanh_toan": "Tạo phiếu trùng"},
        follow_redirects=True
    )
    assert "đã có hồ sơ thanh toán" in res_trung_phieu.text

    auth.login(vai_tro="ke_toan")
    res_danh_sach = client.get("/ke-toan/")
    assert "Chờ kế toán kiểm tra" in res_danh_sach.text
    assert "Thanh toán tiền mua máy chiếu" in res_danh_sach.text
    res_chi_tiet = client.get("/ke-toan/de-nghi/1")
    assert "55.000.000" in res_chi_tiet.text
    assert "Biên bản nghiệm thu" in res_chi_tiet.text

    res_thanh_toan = client.post("/ke-toan/de-nghi/1/thanh-toan", data={
        "so_tien": "55000000",
        "so_hoa_don": "HD-001",
        "phuong_thuc": "chuyen_khoan"
    }, follow_redirects=True)
    assert "Ghi nhận thanh toán thành công" in res_thanh_toan.text

    with app.app_context():
        db = get_db()
        phieu = db.execute(
            "SELECT ma_thanh_toan, gia_tri_de_nghi, gia_tri_da_thanh_toan, so_tien_con_lai, trang_thai FROM thanh_toan WHERE de_nghi_id = 1"
        ).fetchone()
        de_nghi = db.execute(
            "SELECT trang_thai FROM de_nghi_mua_sam WHERE id = 1"
        ).fetchone()

    assert phieu["ma_thanh_toan"].startswith("TT-")
    assert phieu["gia_tri_de_nghi"] == 55_000_000
    assert phieu["gia_tri_da_thanh_toan"] == 55_000_000
    assert phieu["so_tien_con_lai"] == 0
    assert phieu["trang_thai"] == "da_thanh_toan"
    assert de_nghi["trang_thai"] == "hoan_tat"


def test_migration_thanh_toan_giu_lich_su_va_cho_phep_phieu_chua_giai_ngan():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE thanh_toan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            de_nghi_id INTEGER NOT NULL,
            so_tien REAL NOT NULL,
            ngay_thanh_toan TEXT NOT NULL,
            nguoi_thanh_toan_id INTEGER NOT NULL,
            phuong_thuc TEXT DEFAULT 'chuyen_khoan',
            so_hoa_don TEXT,
            ghi_chu TEXT
        )
        """
    )
    conn.execute(
        """
        INSERT INTO thanh_toan
            (de_nghi_id, so_tien, ngay_thanh_toan, nguoi_thanh_toan_id, so_hoa_don)
        VALUES (7, 1200, '2026-01-02T00:00:00', 3, 'HD-OLD')
        """
    )

    init_db(conn)

    columns = {
        row["name"]: row for row in conn.execute("PRAGMA table_info(thanh_toan)")
    }
    payment = conn.execute("SELECT * FROM thanh_toan WHERE id = 1").fetchone()
    assert columns["ngay_thanh_toan"]["notnull"] == 0
    assert columns["nguoi_thanh_toan_id"]["notnull"] == 0
    assert payment["trang_thai"] == "da_thanh_toan"
    assert payment["gia_tri_da_thanh_toan"] == 1200
    assert payment["so_tien_con_lai"] == 0
    conn.close()


def test_trang_thai_dang_nghiem_thu_va_cho_thanh_toan(client, auth):
    """
    Test yêu cầu:
    1. Đổi 'Đã tiếp nhận' thành 'Đang nghiệm thu'.
    2. Thêm trạng thái 'Chờ thanh toán' khi lập Giấy đề nghị thanh toán gửi cho M08/Kế toán.
    3. Kiểm tra nội dung văn bản nộp:
       - 'ĐẠI HỌC KINH TẾ QUỐC DÂN'
       - 'GIẤY ĐỀ NGHỊ THANH TOÁN'
       - 'CHUYỂN KHOẢN CHO NHÀ CUNG CẤP'
       - 'Kính gửi: Ban Giám đốc Đại học Kinh tế Quốc dân'
       - Các chữ ký: BAN GIÁM ĐỐC, KẾ TOÁN TRƯỞNG, XÁC NHẬN ĐƠN VỊ, NGƯỜI ĐỀ NGHỊ THANH TOÁN
    """
    auth.login(vai_tro="mua_sam")
    # Kiểm tra danh sách có nút lọc 'Đang nghiệm thu' và 'Chờ thanh toán'
    res_ds = client.get("/mua-sam/")
    assert res_ds.status_code == 200
    assert "Đang nghiệm thu" in res_ds.text
    assert "Chờ thanh toán" in res_ds.text

    # Tạo đề nghị mới
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Mua hệ thống âm thanh hội thảo",
        "don_vi_de_nghi": "Ban Quản lý Tòa A2",
        "ten_hang_hoa[]": ["Loa hội thảo"],
        "don_vi_tinh[]": ["Bộ"],
        "so_luong[]": ["2"],
        "don_gia_du_kien[]": ["12000000"]
    })

    # Khảo sát BM02 phù hợp
    client.post("/mua-sam/de-nghi/1/khao-sat", data={
        "noi_dung": "Khảo sát nhu cầu âm thanh",
        "ket_luan": "phu_hop"
    })

    # Báo giá
    for ncc in ("NCC 1", "NCC 2", "NCC 3"):
        client.post("/mua-sam/de-nghi/1/bao-gia", data={
            "nha_cung_cap": ncc,
            "tong_gia": "24000000"
        })
    client.post("/mua-sam/de-nghi/1/chon-bao-gia/1")

    # Phê duyệt đề nghị
    auth.login(username="user_truong_mua_sam")
    client.post("/mua-sam/de-nghi/1/phe-duyet", data={"ghi_chu": "Duyệt âm thanh"})

    # Nghiệm thu BM04
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/1/nghiem-thu", data={
        "ket_qua": "dat",
        "y_kien_danh_gia": "Âm thanh trong trẻo, không rè"
    })

    # M09 tiếp nhận hàng -> Đổi trạng thái sang 'Đang nghiệm thu'
    auth.login(vai_tro="quan_ly_kho")
    client.post("/tai-san/tiep-nhan/1", data={"ghi_chu": "Đã tiếp nhận vào kho"})

    # Xem chi tiết đề nghị: Trạng thái hiển thị là 'Đang nghiệm thu'
    auth.login(vai_tro="mua_sam")
    res_view_nghiem_thu = client.get("/mua-sam/de-nghi/1")
    assert res_view_nghiem_thu.status_code == 200
    assert "Đang nghiệm thu" in res_view_nghiem_thu.text

    # M08 lập Giấy đề nghị thanh toán
    res_lap_phieu = client.post("/mua-sam/de-nghi/1/de-nghi-thanh-toan", data={
        "ve_khoan": "Thanh toán tiền mua hệ thống âm thanh hội thảo",
        "hop_dong_so": "HĐ-2026-AT-01",
        "don_vi_thu_huong": "Công ty Âm thanh Ánh sáng",
        "so_tai_khoan": "0241000888999",
        "ngan_hang": "Vietcombank - Chi nhánh Hoàn Kiếm"
    }, follow_redirects=True)
    assert res_lap_phieu.status_code == 200

    # Sau khi lập giấy đề nghị thanh toán -> Đề nghị chuyển sang trạng thái 'Chờ thanh toán'
    assert "Chờ thanh toán" in res_lap_phieu.text

    # Kiểm tra nội dung văn bản nộp hiển thị đúng mẫu chuẩn NEU:
    assert "ĐẠI HỌC KINH TẾ QUỐC DÂN" in res_lap_phieu.text
    assert "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in res_lap_phieu.text
    assert "GIẤY ĐỀ NGHỊ THANH TOÁN" in res_lap_phieu.text
    assert "CHUYỂN KHOẢN CHO NHÀ CUNG CẤP" in res_lap_phieu.text
    assert "Kính gửi: Ban Giám đốc Đại học Kinh tế Quốc dân" in res_lap_phieu.text
    assert "Người đề nghị thanh toán:" in res_lap_phieu.text
    assert "Căn cứ hợp đồng số:" in res_lap_phieu.text
    assert "Số tiền đề nghị thanh toán:" in res_lap_phieu.text
    assert "Viết bằng chữ:" in res_lap_phieu.text
    assert "Đơn vị thụ hưởng:" in res_lap_phieu.text
    assert "Hồ sơ kèm theo:" in res_lap_phieu.text
    assert "BAN GIÁM ĐỐC" in res_lap_phieu.text
    assert "KẾ TOÁN TRƯỞNG" in res_lap_phieu.text
    assert "XÁC NHẬN ĐƠN VỊ" in res_lap_phieu.text
    assert "NGƯỜI ĐỀ NGHỊ THANH TOÁN" in res_lap_phieu.text
