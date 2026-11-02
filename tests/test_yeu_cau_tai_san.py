import sqlite3

from app.db import get_db, init_db


def _tao_tai_san(app, ma, nguoi_su_dung_id=None):
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, vi_tri, phong_ban, gia_tri,
                ngay_tiep_nhan, nguoi_su_dung_id, trang_thai, ngay_tao, ngay_cap_nhat
            )
            VALUES (?, 'Máy chiếu', 'Phòng A1-101', 'Khoa CNTT', 10000000,
                    '2026-01-01', ?, 'dang_su_dung', '2026-01-01', '2026-01-01')
            """,
            (ma, nguoi_su_dung_id)
        )
        db.commit()
        return cursor.lastrowid


def _nguoi_dung_id(app, ten_dang_nhap):
    with app.app_context():
        return get_db().execute(
            "SELECT id FROM nguoi_dung WHERE ten_dang_nhap = ?",
            (ten_dang_nhap,)
        ).fetchone()["id"]

def _dang_nhap(client, app, ten_dang_nhap, vai_tro):
    with app.app_context():
        nguoi_dung = get_db().execute(
            "SELECT id, ho_ten, ten_dang_nhap FROM nguoi_dung WHERE ten_dang_nhap = ?",
            (ten_dang_nhap,)
        ).fetchone()
    with client.session_transaction() as session:
        session["nguoi_dung_id"] = nguoi_dung["id"]
        session["vai_tro"] = vai_tro
        session["ho_ten"] = nguoi_dung["ho_ten"]
        session["ten_dang_nhap"] = nguoi_dung["ten_dang_nhap"]


def _gui_yeu_cau(client, tai_san_id):
    return client.post(
        f"/tai-san/{tai_san_id}/bao-hong",
        data={
            "mo_ta_tinh_trang": "Máy không lên nguồn",
            "muc_do": "nghiem_trong",
            "thoi_gian_phat_hien": "2026-11-03T08:00"
        },
        follow_redirects=False
    )


def test_nguoi_duoc_ban_giao_tao_yeu_cau_va_chi_xem_tai_san_cua_minh(client, app):
    owner_id = _nguoi_dung_id(app, "user_mua_sam")
    tai_san_id = _tao_tai_san(app, "TS-OWNER-001", owner_id)
    _dang_nhap(client, app, "user_mua_sam", "mua_sam")

    res = _gui_yeu_cau(client, tai_san_id)
    assert res.status_code == 302
    assert client.get("/tai-san/cua-toi").status_code == 200
    assert client.get(f"/tai-san/{tai_san_id}").status_code == 200
    with app.app_context():
        yeu_cau = get_db().execute(
            "SELECT id, trang_thai, nguoi_tao_id FROM yeu_cau_xu_ly_tai_san"
        ).fetchone()
        assert yeu_cau["trang_thai"] == "cho_xac_minh"
        assert yeu_cau["nguoi_tao_id"] == owner_id
        yeu_cau_id = yeu_cau["id"]
    assert client.get(f"/tai-san/yeu-cau/{yeu_cau_id}").status_code == 200


def test_nguoi_khong_duoc_ban_giao_khong_xem_hoac_bao_hong_tai_san(client, app):
    owner_id = _nguoi_dung_id(app, "user_mua_sam")
    tai_san_id = _tao_tai_san(app, "TS-OWNER-002", owner_id)
    _dang_nhap(client, app, "user_ke_toan", "ke_toan")

    assert client.get(f"/tai-san/{tai_san_id}").status_code == 403
    assert _gui_yeu_cau(client, tai_san_id).status_code == 302
    with app.app_context():
        so_yeu_cau = get_db().execute(
            "SELECT COUNT(*) FROM yeu_cau_xu_ly_tai_san"
        ).fetchone()[0]
        assert so_yeu_cau == 0


def test_quy_trinh_sua_chua_phan_cong_thuc_hien_va_kiem_tra(client, app):
    owner_id = _nguoi_dung_id(app, "user_mua_sam")
    manager_id = _nguoi_dung_id(app, "user_kho")
    tai_san_id = _tao_tai_san(app, "TS-REPAIR-001", owner_id)
    _dang_nhap(client, app, "user_mua_sam", "mua_sam")
    _gui_yeu_cau(client, tai_san_id)

    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    yeu_cau_id = 1
    assert client.get("/tai-san/yeu-cau").status_code == 200
    assert client.get(f"/tai-san/yeu-cau/{yeu_cau_id}").status_code == 200
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/xac-minh",
        data={"phuong_an": "sua_chua", "ket_qua_xac_minh": "Có thể thay bộ nguồn."}
    ).status_code == 302
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/phan-cong",
        data={"nguoi_duoc_phan_cong_id": owner_id}
    ).status_code == 302

    _dang_nhap(client, app, "user_mua_sam", "mua_sam")
    assert client.post(f"/tai-san/yeu-cau/{yeu_cau_id}/bat-dau").status_code == 302
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/hoan-thanh",
        data={
            "noi_dung_thuc_hien": "Thay bộ nguồn",
            "chi_phi": "250000",
            "don_vi_thuc_hien": "Tổ kỹ thuật",
            "ghi_chu": "Đã chạy thử"
        }
    ).status_code == 302

    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/kiem-tra",
        data={"ket_qua_kiem_tra": "chua_dat", "ghi_chu": "Nguồn vẫn chưa ổn định"}
    ).status_code == 302
    with app.app_context():
        assert get_db().execute(
            "SELECT trang_thai FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
            (yeu_cau_id,)
        ).fetchone()["trang_thai"] == "dang_thuc_hien"

    _dang_nhap(client, app, "user_mua_sam", "mua_sam")
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/hoan-thanh",
        data={
            "noi_dung_thuc_hien": "Thay bộ nguồn lần hai",
            "chi_phi": "250000",
            "don_vi_thuc_hien": "Tổ kỹ thuật",
            "ghi_chu": "Đã chạy thử ổn định"
        }
    ).status_code == 302

    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    assert client.post(
        f"/tai-san/yeu-cau/{yeu_cau_id}/kiem-tra",
        data={"ket_qua_kiem_tra": "dat", "ghi_chu": "Hoạt động bình thường"}
    ).status_code == 302
    assert client.get(f"/tai-san/yeu-cau/{yeu_cau_id}").status_code == 200
    with app.app_context():
        db = get_db()
        yeu_cau = db.execute(
            "SELECT trang_thai, ghi_chu_thuc_hien, nguoi_kiem_tra_id FROM yeu_cau_xu_ly_tai_san WHERE id = ?",
            (yeu_cau_id,)
        ).fetchone()
        tai_san = db.execute(
            "SELECT trang_thai FROM tai_san WHERE id = ?",
            (tai_san_id,)
        ).fetchone()
        so_bao_tri = db.execute(
            "SELECT COUNT(*) FROM bao_tri WHERE tai_san_id = ?",
            (tai_san_id,)
        ).fetchone()[0]
        so_su_kien = db.execute(
            "SELECT COUNT(*) FROM lich_su_yeu_cau_su_co WHERE yeu_cau_id = ?",
            (yeu_cau_id,)
        ).fetchone()[0]
        nguoi_phan_cong = db.execute(
            """
            SELECT nguoi_thuc_hien_id FROM lich_su_yeu_cau_su_co
            WHERE yeu_cau_id = ? AND hanh_dong = 'phan_cong'
            """,
            (yeu_cau_id,)
        ).fetchone()["nguoi_thuc_hien_id"]
        assert yeu_cau["trang_thai"] == "sua_chua_hoan_tat"
        assert yeu_cau["ghi_chu_thuc_hien"] == "Đã chạy thử ổn định"
        assert yeu_cau["nguoi_kiem_tra_id"] is not None
        assert tai_san["trang_thai"] == "dang_su_dung"
        assert so_bao_tri == 1
        assert so_su_kien == 8
        assert nguoi_phan_cong == manager_id


def test_de_nghi_thay_the_lien_ket_va_chi_cho_thanh_ly_sau_khi_nhan(client, app):
    owner_id = _nguoi_dung_id(app, "user_mua_sam")
    tai_san_id = _tao_tai_san(app, "TS-REPLACE-001", owner_id)
    _dang_nhap(client, app, "user_mua_sam", "mua_sam")
    _gui_yeu_cau(client, tai_san_id)

    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    assert client.get("/tai-san/bao-cao-cong-khai").status_code == 200
    assert client.post(
        "/tai-san/yeu-cau/1/xac-minh",
        data={
            "phuong_an": "thay_the",
            "ket_qua_xac_minh": "Thiết bị hỏng bo mạch, không thể sửa.",
            "ten_hang_thay_the": "Máy chiếu mới",
            "don_vi_tinh": "Cái",
            "so_luong": "1",
            "don_gia_du_kien": "12000000",
            "don_vi_de_nghi": "Khoa CNTT"
        }
    ).status_code == 302
    with app.app_context():
        db = get_db()
        de_nghi = db.execute(
            "SELECT id, su_co_tai_san_id FROM de_nghi_mua_sam"
        ).fetchone()
        trang_thai_cu = db.execute(
            "SELECT trang_thai FROM tai_san WHERE id = ?",
            (tai_san_id,)
        ).fetchone()["trang_thai"]
        assert de_nghi["su_co_tai_san_id"] == 1
        assert trang_thai_cu == "dang_su_dung"
        de_nghi_id = de_nghi["id"]

    _dang_nhap(client, app, "user_admin", "quan_tri")
    assert client.post(
        f"/mua-sam/de-nghi/{de_nghi_id}/phe-duyet", data={"ghi_chu": "Đồng ý"}
    ).status_code == 302
    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    assert client.post(
        f"/mua-sam/de-nghi/{de_nghi_id}/tiep-nhan", data={"ghi_chu": "Đã nhận đủ"}
    ).status_code == 302

    with app.app_context():
        db = get_db()
        issue = db.execute(
            "SELECT trang_thai FROM yeu_cau_xu_ly_tai_san WHERE id = 1"
        ).fetchone()
        asset = db.execute(
            "SELECT trang_thai FROM tai_san WHERE id = ?",
            (tai_san_id,)
        ).fetchone()
        new_asset = db.execute(
            "SELECT COUNT(*) FROM tai_san WHERE de_nghi_id = ?",
            (de_nghi_id,)
        ).fetchone()[0]
        assert issue["trang_thai"] == "da_nhan_tai_san_thay_the"
        assert asset["trang_thai"] == "cho_thanh_ly"
        assert new_asset == 1


def test_khach_gui_phan_anh_co_the_chon_tai_san_cong_khai(client, app):
    tai_san_id = _tao_tai_san(app, "TS-PUBLIC-001")
    assert client.get("/bao-cao-hu-hai").status_code == 200
    res = client.post(
        "/bao-cao-hu-hai",
        data={
            "ho_ten": "Khách tham quan",
            "lien_he": "khach@example.test",
            "tai_san_id": str(tai_san_id),
            "muc_do": "trung_binh",
            "mo_ta_chi_tiet": "Không hoạt động."
        }
    )
    assert res.status_code == 302
    with app.app_context():
        report = get_db().execute(
            "SELECT tai_san_id, ten_vat_chat, vi_tri FROM bao_cao_hu_hai"
        ).fetchone()
        assert report["tai_san_id"] == tai_san_id
        assert report["ten_vat_chat"] == "TS-PUBLIC-001 - Máy chiếu"
        assert report["vi_tri"] == "Phòng A1-101"
        report_id = get_db().execute(
            "SELECT id FROM bao_cao_hu_hai"
        ).fetchone()["id"]

    manager_id = _nguoi_dung_id(app, "user_kho")
    _dang_nhap(client, app, "user_kho", "quan_ly_kho")
    assert client.post(
        f"/tai-san/bao-cao-cong-khai/{report_id}/tao-yeu-cau",
        data={"tai_san_id": str(tai_san_id)}
    ).status_code == 302
    response = client.get("/tai-san/bao-cao-cong-khai")
    assert response.status_code == 200
    assert b"/tai-san/yeu-cau/1" in response.data
    with app.app_context():
        db = get_db()
        issue = db.execute(
            "SELECT bao_cao_hu_hai_id, nguoi_tao_id FROM yeu_cau_xu_ly_tai_san"
        ).fetchone()
        event = db.execute(
            "SELECT nguoi_thuc_hien_id FROM lich_su_yeu_cau_su_co"
        ).fetchone()
        assert issue["bao_cao_hu_hai_id"] == report_id
        assert issue["nguoi_tao_id"] == manager_id
        assert event["nguoi_thuc_hien_id"] == manager_id


def test_phien_ban_cu_duoc_migrate_ma_khong_mat_bao_cao(tmp_path):
    db_path = tmp_path / "csvc-cu.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE de_nghi_mua_sam (
            id INTEGER PRIMARY KEY,
            ma_de_nghi TEXT,
            tieu_de TEXT,
            mo_ta TEXT,
            don_vi_de_nghi TEXT,
            nguoi_de_nghi_id INTEGER,
            tong_du_toan REAL,
            trang_thai TEXT,
            ghi_chu_phe_duyet TEXT,
            nguoi_phe_duyet_id INTEGER,
            ngay_tao TEXT,
            ngay_phe_duyet TEXT,
            ngay_cap_nhat TEXT
        );
        CREATE TABLE bao_cao_hu_hai (
            id INTEGER PRIMARY KEY,
            ho_ten TEXT NOT NULL,
            lien_he TEXT NOT NULL,
            ten_vat_chat TEXT NOT NULL,
            vi_tri TEXT NOT NULL,
            muc_do TEXT NOT NULL,
            mo_ta_chi_tiet TEXT,
            thoi_gian_phat_hien TEXT,
            trang_thai TEXT,
            ngay_tao TEXT NOT NULL
        );
        CREATE TABLE yeu_cau_xu_ly_tai_san (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tai_san_id INTEGER NOT NULL,
            nguoi_tao_id INTEGER NOT NULL,
            bao_cao_hu_hai_id INTEGER UNIQUE,
            mo_ta_tinh_trang TEXT NOT NULL,
            muc_do TEXT NOT NULL,
            thoi_gian_phat_hien TEXT,
            trang_thai TEXT NOT NULL DEFAULT 'cho_xac_minh',
            phuong_an TEXT,
            ket_qua_xac_minh TEXT,
            nguoi_xac_minh_id INTEGER,
            ngay_xac_minh TEXT,
            nguoi_duoc_phan_cong_id INTEGER,
            noi_dung_thuc_hien TEXT,
            chi_phi REAL NOT NULL DEFAULT 0,
            don_vi_thuc_hien TEXT,
            ket_qua_kiem_tra TEXT,
            de_nghi_mua_sam_id INTEGER,
            ngay_tao TEXT NOT NULL,
            ngay_cap_nhat TEXT NOT NULL
        );
        INSERT INTO bao_cao_hu_hai
            (ho_ten, lien_he, ten_vat_chat, vi_tri, muc_do, ngay_tao)
        VALUES ('Khách cũ', 'cu@example.test', 'Đèn', 'A1', 'nhe', '2026-01-01');
        INSERT INTO yeu_cau_xu_ly_tai_san (
            tai_san_id, nguoi_tao_id, mo_ta_tinh_trang, muc_do,
            ngay_tao, ngay_cap_nhat
        )
        VALUES (12, 4, 'Hỏng cũ', 'trung_binh', '2026-01-01', '2026-01-01');
        """
    )
    init_db(conn)
    report = conn.execute("SELECT ho_ten, tai_san_id FROM bao_cao_hu_hai").fetchone()
    request_columns = {row[1] for row in conn.execute("PRAGMA table_info(de_nghi_mua_sam)")}
    issue_columns = {row[1] for row in conn.execute("PRAGMA table_info(yeu_cau_xu_ly_tai_san)")}
    assert report == ("Khách cũ", None)
    assert conn.execute(
        "SELECT id, mo_ta_tinh_trang FROM yeu_cau_xu_ly_tai_san"
    ).fetchone() == (1, "Hỏng cũ")
    assert "su_co_tai_san_id" in request_columns
    assert {"ghi_chu_thuc_hien", "nguoi_kiem_tra_id", "ngay_kiem_tra"} <= issue_columns
    assert conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'lich_su_yeu_cau_su_co'"
    ).fetchone() is not None
    conn.close()
