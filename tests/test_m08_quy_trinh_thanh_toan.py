from app.db import get_db
import sqlite3

from app.db import init_db


def test_m08_quy_trinh_khoa_cac_buoc_va_gui_phieu_sang_ke_toan(client, auth, app):
    auth.login(vai_tro="mua_sam")
    client.post("/mua-sam/de-nghi/tao", data={
        "tieu_de": "Mua thiết bị trình chiếu",
        "don_vi_de_nghi": "Khoa Công nghệ Thông tin",
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

    auth.login(vai_tro="quan_tri")
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
