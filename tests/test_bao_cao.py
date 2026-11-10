def test_admin_dashboard_hien_thi_dung(client, auth):
    """Test trang Dashboard M17 truy cập được bởi Admin và hiển thị đầy đủ thẻ KPI."""
    auth.login(vai_tro="quan_tri")
    res = client.get("/admin/")
    assert res.status_code == 200
    assert "M17 - TỔNG QUAN HỆ THỐNG CƠ SỞ VẬT CHẤT" in res.text
    assert "Đề nghị chờ phê duyệt" in res.text

def test_xuat_pdf_mua_sam_va_tai_san_theo_mau(client, auth, app):
    """Xuất báo cáo mua sắm và tài sản thành PDF theo biểu mẫu."""
    auth.login(vai_tro="quan_tri")

    with app.app_context():
        from app.db import get_db

        db = get_db()
        nguoi_de_nghi = db.execute(
            "SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_mua_sam'"
        ).fetchone()["id"]
        cur = db.execute(
            """
            INSERT INTO de_nghi_mua_sam (
                ma_de_nghi, tieu_de, don_vi_de_nghi, nguoi_de_nghi_id,
                tong_du_toan, trang_thai, ngay_tao, ngay_cap_nhat
            ) VALUES (
                'DN-PDF-001', 'Mua thiết bị kiểm thử', 'Ban Quản lý Tòa A1', ?,
                25000000, 'da_phe_duyet', '2026-11-10T00:00:00', '2026-11-10T00:00:00'
            )
            """,
            (nguoi_de_nghi,)
        )
        db.execute(
            """
            INSERT INTO chi_tiet_de_nghi (
                de_nghi_id, ten_hang_hoa, don_vi_tinh, so_luong,
                don_gia_du_kien, thanh_tien
            ) VALUES (?, 'Máy tính kiểm thử', 'bộ', 1, 25000000, 25000000)
            """,
            (cur.lastrowid,)
        )
        db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, gia_tri, ngay_tiep_nhan,
                de_nghi_id, ngay_tao, ngay_cap_nhat
            ) VALUES (
                'TS-PDF-001', 'Máy tính tài sản kiểm thử', 25000000,
                '2026-11-10', ?, '2026-11-10T00:00:00', '2026-11-10T00:00:00'
            )
            """,
            (cur.lastrowid,)
        )
        db.commit()

    page = client.get("/admin/bao-cao")
    assert page.status_code == 200
    assert "Xuất PDF Mua sắm" in page.text
    assert "Xuất PDF Tài sản" in page.text
    assert "Xuất CSV" not in page.text

    res_ms = client.get("/admin/bao-cao/xuat-pdf-mua-sam")
    assert res_ms.status_code == 200
    assert res_ms.mimetype == "application/pdf"
    assert res_ms.data.startswith(b"%PDF-")
    assert b"FontFile2" in res_ms.data
    assert b"595.2756" in res_ms.data
    assert "bao_cao_mua_sam_the_tai_san.pdf" in res_ms.headers["Content-Disposition"]

    res_ts = client.get("/admin/bao-cao/xuat-pdf-tai-san")
    assert res_ts.status_code == 200
    assert res_ts.mimetype == "application/pdf"
    assert res_ts.data.startswith(b"%PDF-")
    assert b"FontFile2" in res_ts.data
    assert b"595.2756" in res_ts.data
    assert "bao_cao_tai_san_mau_06.pdf" in res_ts.headers["Content-Disposition"]

    assert client.get("/admin/bao-cao/xuat-csv-mua-sam").status_code == 404
    assert client.get("/admin/bao-cao/xuat-csv-tai-san").status_code == 404

    auth.login(vai_tro="mua_sam")
    assert client.get("/admin/bao-cao/xuat-pdf-mua-sam").status_code == 403
    assert client.get("/admin/bao-cao/xuat-pdf-tai-san").status_code == 403
