from app.db import get_db

def test_mua_sam_khong_duoc_truy_cap_tai_san(client, auth):
    """Test bộ phận mua sắm không có quyền truy cập module M09 - Quản lý tài sản."""
    auth.login(vai_tro="mua_sam")
    res = client.get("/tai-san/")
    assert res.status_code == 403

def test_quan_ly_kho_truy_cap_tai_san(client, auth):
    """Test bộ phận quản lý tài sản truy cập thành công danh sách tài sản."""
    auth.login(vai_tro="quan_ly_kho")
    res = client.get("/tai-san/")
    assert res.status_code == 200
    assert "M09 - QUẢN LÝ TÀI SẢN" in res.text

def test_ban_giao_tai_san(client, auth, app):
    """Test bộ phận quản lý tài sản thực hiện bàn giao tài sản."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (ma_tai_san, ten_tai_san, vi_tri, phong_ban, gia_tri, ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat)
            VALUES ('TS-2026-TEST-001', 'Laptop Dell XPS', 'Kho', 'Ban Quản lý Tòa A1', 25000000, '2026-01-01', 'cho_ban_giao', '2026-01-01', '2026-01-01')
            """
        )
        tai_san_id = cur.lastrowid
        user_row = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_don_vi'").fetchone()
        user_id = user_row["id"]
        existing_user = db.execute(
            "SELECT mat_khau_hash FROM nguoi_dung WHERE id = ?", (user_id,)
        ).fetchone()
        cur = db.execute(
            """
            INSERT INTO nguoi_dung (
                ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, don_vi,
                ngay_tao, trang_thai
            ) VALUES ('Cán bộ A2', 'a2@neu.test', 'user_bql_a2', ?, 'don_vi',
                      'Ban Quản lý Tòa A2', '2026-01-01', 'hoat_dong')
            """,
            (existing_user["mat_khau_hash"],)
        )
        user_a2_id = cur.lastrowid
        mua_sam_id = db.execute(
            "SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_mua_sam'"
        ).fetchone()["id"]
        db.commit()

    auth.login(vai_tro="quan_ly_kho")
    invalid = client.post(f"/tai-san/{tai_san_id}/ban-giao", data={
        "nguoi_nhan_id": mua_sam_id
    }, follow_redirects=True)
    assert "Chỉ cán bộ thuộc Ban Quản lý".encode("utf-8") in invalid.data

    res_bg = client.post(f"/tai-san/{tai_san_id}/ban-giao", data={
        "nguoi_nhan_id": user_id,
        "ghi_chu": "Bàn giao máy tính xách tay"
    }, follow_redirects=True)
    assert res_bg.status_code == 200
    assert "Bàn giao tài sản thành công" in res_bg.text
    res_detail = client.get(f"/tai-san/{tai_san_id}")
    assert "Ban Quản lý Tòa A2".encode("utf-8") not in res_detail.data
    assert "chỉ được bàn giao một lần".encode("utf-8") in res_detail.data
    assert b"X\xc3\xa1c nh\xe1\xba\xadn b\xc3\xa0n giao" not in res_detail.data
    assert b"Ghi nh\xe1\xba\xadn b\xe1\xba\xa3o tr\xc3\xac" not in res_detail.data

    res_ban_giao_lan_hai = client.post(f"/tai-san/{tai_san_id}/ban-giao", data={
        "nguoi_nhan_id": user_id,
        "ghi_chu": "Thử bàn giao lần hai trong cùng đơn vị"
    }, follow_redirects=True)
    assert "chỉ được bàn giao một lần".encode("utf-8") in res_ban_giao_lan_hai.data
    res_chuyen_don_vi = client.post(f"/tai-san/{tai_san_id}/ban-giao", data={
        "nguoi_nhan_id": user_a2_id,
        "ghi_chu": "Thử bàn giao lần hai sang đơn vị khác"
    }, follow_redirects=True)
    assert "chỉ được bàn giao một lần".encode("utf-8") in res_chuyen_don_vi.data
    with app.app_context():
        db = get_db()
        assert db.execute(
            "SELECT COUNT(*) FROM lich_su_ban_giao WHERE tai_san_id = ?", (tai_san_id,)
        ).fetchone()[0] == 1
        assert db.execute(
            "SELECT nguoi_su_dung_id FROM tai_san WHERE id = ?", (tai_san_id,)
        ).fetchone()["nguoi_su_dung_id"] == user_id

def test_ghi_nhan_bao_tri_tai_san(client, auth, app):
    """Test bộ phận quản lý tài sản ghi nhận sửa chữa, bảo trì cho tài sản."""
    with app.app_context():
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO tai_san (ma_tai_san, ten_tai_san, vi_tri, phong_ban, gia_tri, ngay_tiep_nhan, trang_thai, ngay_tao, ngay_cap_nhat)
            VALUES ('TS-2026-TEST-002', 'Máy chiếu Sony', 'Phòng B-201', 'Phòng QTTB', 15000000, '2026-01-01', 'dang_su_dung', '2026-01-01', '2026-01-01')
            """
        )
        tai_san_id = cur.lastrowid
        db.commit()

    auth.login(vai_tro="quan_ly_kho")
    res = client.post(f"/tai-san/{tai_san_id}/bao-tri", data={
        "noi_dung": "Thay quạt tản nhiệt",
        "chi_phi": "500000",
        "don_vi_thuc_hien": "Trung tâm bảo hành Sony",
        "ghi_chu": "Bảo hành 6 tháng",
        "trang_thai_moi": "dang_su_dung"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Ghi nhận bảo trì/sửa chữa tài sản thành công" in res.text

def test_quan_ly_kho_khong_duoc_truy_cap_mua_sam(client, auth):
    """Test RBAC: Cán bộ quản lý tài sản tuyệt đối không được truy cập phân hệ M08 mua sắm."""
    auth.login(vai_tro="quan_ly_kho")

    # Không vào được danh sách đề nghị mua sắm M08
    res_list = client.get("/mua-sam/")
    assert res_list.status_code == 403

    # Không vào được form tạo đề nghị mua sắm M08
    res_create = client.get("/mua-sam/de-nghi/tao")
    assert res_create.status_code == 403

    # Không vào được chi tiết đề nghị mua sắm M08
    res_detail = client.get("/mua-sam/de-nghi/1")
    assert res_detail.status_code == 403

    # Nhưng truy cập chức năng tiếp nhận trong phân hệ M09 thành công
    res_tiep_nhan = client.get("/tai-san/tiep-nhan")
    assert res_tiep_nhan.status_code == 200
    assert "TIẾP NHẬN TÀI SẢN MỚI TỪ MUA SẮM" in res_tiep_nhan.text

def test_lien_ket_m08_tu_phuong_an_sua_chua(client, auth, app):
    """Nhu cầu M09 chỉ được chuyển sang M08 sau khi Admin duyệt phương án."""
    from app.services import tai_san as ts_svc

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM nguoi_dung WHERE vai_tro = 'don_vi'").fetchone()
        yc = ts_svc.tao_yeu_cau_sua_chua({
            "don_vi": "Ban Quản lý Tòa A1",
            "ten_vat_chat": "Máy bơm",
            "vi_tri": "Phòng bơm A1",
            "noi_dung": "Máy bơm không hoạt động"
        }, user["id"])
        yc_id = yc["id"]

    auth.login(vai_tro="quan_tri")
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/tiep-nhan",
        data={"hanh_dong": "tiep_nhan"}
    ).status_code == 403

    auth.login(vai_tro="quan_ly_kho")
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/tiep-nhan",
        data={"hanh_dong": "tiep_nhan"}
    ).status_code == 302
    assert client.post(f"/tai-san/sua-chua/{yc_id}/khao-sat/bat-dau").status_code == 302
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/khao-sat",
        data={
            "thanh_phan_khao_sat": "QTTB, Ban quản lý",
            "phan_loai_yeu_cau": "thiet_bi",
            "hien_trang": "Máy bơm bị cháy",
            "muc_do_hu_hong": "nghiem_trong",
            "khoi_luong_cong_viec": "Thay máy bơm"
        }
    ).status_code == 302
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/phuong-an",
        data={
            "phuong_an": "thay_the",
            "phuong_an_chi_tiet": "Mua và lắp máy bơm mới",
            "chi_phi_du_kien": "5000000",
            "can_mua_sam": "1"
        }
    ).status_code == 302

    auth.login(vai_tro="quan_tri")
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/phe-duyet-phuong-an",
        data={"ghi_chu": "Duyệt"}
    ).status_code == 302

    auth.login(vai_tro="quan_ly_kho")
    assert client.post(f"/tai-san/sua-chua/{yc_id}/lien-ket-m08").status_code == 302
    with app.app_context():
        db = get_db()
        yc = db.execute("SELECT trang_thai, de_nghi_mua_sam_id FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["trang_thai"] == "cho_thu_tuc_m08"
        proposal = db.execute(
            "SELECT yeu_cau_sua_chua_id, trang_thai FROM de_nghi_mua_sam WHERE id = ?",
            (yc["de_nghi_mua_sam_id"],)
        ).fetchone()
        assert proposal["yeu_cau_sua_chua_id"] == yc_id
        assert proposal["trang_thai"] == "cho_phe_duyet"

    res_start = client.post(f"/tai-san/sua-chua/{yc_id}/bat-dau", follow_redirects=True)
    assert "chưa được duyệt khắc phục".encode("utf-8") in res_start.data

def test_tra_lai_yeu_cau_va_don_vi_bo_sung(client, auth, app):
    """QTTB trả phiếu bổ sung; đơn vị bổ sung xong phiếu trở về chờ tiếp nhận."""
    from app.services import tai_san as ts_svc

    with app.app_context():
        db = get_db()
        user = db.execute("SELECT id FROM nguoi_dung WHERE vai_tro = 'don_vi'").fetchone()
        yc = ts_svc.tao_yeu_cau_sua_chua({
            "don_vi": "Ban Quản lý Tòa A1",
            "ten_vat_chat": "Cửa",
            "vi_tri": "Tầng 2",
            "noi_dung": "Cần kiểm tra cửa"
        }, user["id"])
        yc_id = yc["id"]

    auth.login(vai_tro="quan_ly_kho")
    assert client.post(
        f"/tai-san/sua-chua/{yc_id}/tiep-nhan",
        data={"hanh_dong": "tra_lai", "noi_dung": "Bổ sung vị trí chính xác"}
    ).status_code == 302

    auth.login(vai_tro="don_vi")
    assert client.post(
        f"/don-vi/sua-chua/{yc_id}/bo-sung",
        data={"noi_dung": "Cửa tầng 2, lối thoát hiểm"}
    ).status_code == 302
    with app.app_context():
        yc = get_db().execute("SELECT trang_thai, noi_dung FROM yeu_cau_sua_chua WHERE id = ?", (yc_id,)).fetchone()
        assert yc["trang_thai"] == "cho_tiep_nhan"
        assert yc["noi_dung"] == "Cửa tầng 2, lối thoát hiểm"

def test_chi_hien_thi_de_nghi_da_nghiem_thu_dat_de_tiep_nhan(client, auth, app):
    """Test chức năng Tiếp nhận M09: Chỉ hiển thị đề nghị đã nghiệm thu đạt BM04, đủ điều kiện tiếp nhận."""
    from app.services import mua_sam as ms_svc
    from app.services import tai_san as ts_svc

    auth.login(vai_tro="quan_ly_kho")
    # 1. Kiểm tra trên trang Danh mục tài sản (/tai-san/):
    # Phải có nút 'TIẾP NHẬN TÀI SẢN MỚI TỪ MUA SẮM', không có nút 'Đề xuất mua sắm'
    res_ds = client.get("/tai-san/")
    assert res_ds.status_code == 200
    assert "TIẾP NHẬN TÀI SẢN MỚI TỪ MUA SẮM" in res_ds.text
    assert "/mua-sam/de-nghi/tao" not in res_ds.text

    # 2. Tạo 2 gói đề nghị:
    # Gói A: Đã phê duyệt nhưng CHƯA nghiệm thu (da_nghiem_thu = 0)
    # Gói B: Đã phê duyệt và ĐÃ nghiệm thu kỹ thuật đạt BM04 (da_nghiem_thu = 1)
    with app.app_context():
        db = get_db()
        u_row = db.execute("SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_mua_sam'").fetchone()
        u_id = u_row["id"]
        truong_bo_phan_row = db.execute(
            "SELECT id FROM nguoi_dung WHERE ten_dang_nhap = 'user_truong_mua_sam'"
        ).fetchone()
        truong_bo_phan_id = truong_bo_phan_row["id"]

        dn_a = ms_svc.tao_de_nghi({
            "tieu_de": "Gói A chưa nghiệm thu",
            "don_vi_de_nghi": "Ban Quản lý Tòa A1",
            "items": [{"ten_hang_hoa": "Màn hình Dell", "so_luong": 1, "don_gia_du_kien": 5000000}]
        }, u_id)
        ms_svc.tao_khao_sat(dn_a["id"], {"noi_dung": "Khảo sát gói A", "ket_luan": "phu_hop"})
        ms_svc.phe_duyet_de_nghi(dn_a["id"], truong_bo_phan_id, "Duyệt", vai_tro="mua_sam")

        dn_b = ms_svc.tao_de_nghi({
            "tieu_de": "Gói B đã nghiệm thu đạt",
            "don_vi_de_nghi": "Ban Quản lý Tòa A2",
            "items": [{"ten_hang_hoa": "Máy in Canon LBP", "so_luong": 1, "don_gia_du_kien": 6000000}]
        }, u_id)
        # Khảo sát BM02 -> Báo giá -> Chọn báo giá -> Phê duyệt -> Nghiệm thu BM04 cho Gói B
        ms_svc.tao_khao_sat(dn_b["id"], {"noi_dung": "Khảo sát", "ket_luan": "phu_hop"})
        ms_svc.them_bao_gia(dn_b["id"], {"nha_cung_cap": "NCC B", "tong_gia": 6000000})
        ms_svc.them_bao_gia(dn_b["id"], {"nha_cung_cap": "NCC B2", "tong_gia": 6100000})
        ms_svc.them_bao_gia(dn_b["id"], {"nha_cung_cap": "NCC B3", "tong_gia": 6200000})
        bg_row = db.execute("SELECT id FROM bao_gia WHERE de_nghi_id = ?", (dn_b["id"],)).fetchone()
        ms_svc.chon_bao_gia(dn_b["id"], bg_row["id"])
        ms_svc.phe_duyet_de_nghi(dn_b["id"], truong_bo_phan_id, "Duyệt", vai_tro="mua_sam")
        ms_svc.lap_bien_ban_nghiem_thu(dn_b["id"], {
            "dai_dien_ben_mua": "BP Mua sắm",
            "dai_dien_nha_cung_cap": "NCC B",
            "ket_qua": "dat",
            "y_kien_danh_gia": "Đạt yêu cầu kỹ thuật"
        })

    # 3. Vào trang Tiếp nhận tài sản mới (/tai-san/tiep-nhan):
    res_tn = client.get("/tai-san/tiep-nhan")
    assert res_tn.status_code == 200
    # Gói B đã nghiệm thu đạt -> PHẢI hiển thị
    assert dn_b["ma_de_nghi"] in res_tn.text
    assert "Nghiệm thu ĐẠT" in res_tn.text
    # Gói A chưa nghiệm thu -> TUYỆT ĐỐI KHÔNG được hiển thị
    assert dn_a["ma_de_nghi"] not in res_tn.text

    # 4. Cố tình truy cập trực tiếp form tiếp nhận của Gói A chưa nghiệm thu -> Bị chặn
    res_direct_a = client.get(f"/tai-san/tiep-nhan/{dn_a['id']}", follow_redirects=True)
    assert "chưa có Biên bản nghiệm thu kỹ thuật (BM04) đạt yêu cầu" in res_direct_a.text
