def test_admin_dashboard_hien_thi_dung(client, auth):
    """Test trang Dashboard M17 truy cập được bởi Admin và hiển thị đầy đủ thẻ KPI."""
    auth.login(vai_tro="quan_tri")
    res = client.get("/admin/")
    assert res.status_code == 200
    assert "M17 - TỔNG QUAN HỆ THỐNG CƠ SỞ VẬT CHẤT" in res.text
    assert "Đề nghị chờ phê duyệt" in res.text

def test_xuat_csv_mua_sam_va_tai_san(client, auth):
    """Test chức năng xuất dữ liệu báo cáo ra tệp CSV."""
    auth.login(vai_tro="quan_tri")
    
    # 1. Xuất CSV mua sắm
    res_ms = client.get("/admin/bao-cao/xuat-csv-mua-sam")
    assert res_ms.status_code == 200
    assert res_ms.mimetype == "text/csv"
    assert "Mã đề nghị" in res_ms.text

    # 2. Xuất CSV tài sản
    res_ts = client.get("/admin/bao-cao/xuat-csv-tai-san")
    assert res_ts.status_code == 200
    assert res_ts.mimetype == "text/csv"
    assert "Mã tài sản" in res_ts.text

