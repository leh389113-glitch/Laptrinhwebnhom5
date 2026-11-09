import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc vào sys.path để import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from werkzeug.security import generate_password_hash
from app.db import get_db, init_db
from app import tao_app, clock

def nap_du_lieu():
    app = tao_app()
    with app.app_context():
        db = get_db()
        init_db(db)

        # Xóa dữ liệu cũ theo thứ tự ràng buộc khóa ngoại
        db.execute("PRAGMA foreign_keys = OFF")
        db.execute("DELETE FROM chi_tiet_de_nghi")
        db.execute("DELETE FROM khao_sat_nhu_cau")
        db.execute("DELETE FROM bao_gia")
        db.execute("DELETE FROM nghiem_thu_mua_sam")
        db.execute("DELETE FROM ho_so_mua_sam")
        db.execute("DELETE FROM chi_tiet_tiep_nhan")
        db.execute("DELETE FROM tiep_nhan_hang")
        db.execute("DELETE FROM thanh_toan")
        db.execute("DELETE FROM lich_su_ban_giao")
        db.execute("DELETE FROM yeu_cau_sua_chua")
        db.execute("DELETE FROM bao_tri")
        db.execute("DELETE FROM chi_tiet_kiem_ke")
        db.execute("DELETE FROM phieu_kiem_ke")
        db.execute("DELETE FROM tai_san")
        db.execute("DELETE FROM de_nghi_mua_sam")
        db.execute("DELETE FROM bao_cao_hu_hai")
        db.execute("DELETE FROM nguoi_dung")
        db.execute("PRAGMA foreign_keys = ON")
        db.commit()

        print("-> Đang khởi tạo các tài khoản theo đúng 4 nhóm phân quyền:")
        hien_tai = clock.now().isoformat()

        # Danh sách tài khoản mẫu thuận tiện kiểm thử theo quy chuẩn phân quyền:
        # 1. Admin: quan_tri
        # 2. Trưởng BP Mua sắm: mua_sam (duyệt gói < 100tr)
        # 3. Cán bộ Mua sắm: mua_sam (lập đề xuất, khảo sát, báo giá)
        # 4. Quản lý tài sản: quan_ly_kho (tiếp nhận kho M09, sửa chữa, kiểm kê)
        # 5. Kế toán: ke_toan (thanh toán giải ngân M08)
        # 6. Đơn vị sử dụng 1: don_vi (Khoa Công nghệ Thông tin)
        # 7. Đơn vị sử dụng 2: don_vi (Khoa Quản trị Kinh doanh)
        users = [
            ("Lãnh đạo Trường (Admin)", "admin@neu.edu.vn", "admin", "admin123", "quan_tri", "Lãnh đạo", "Ban Giám hiệu", "02436280280"),
            ("Trưởng BP Mua sắm", "truongmuasam@neu.edu.vn", "truongmuasam", "muasam1234", "mua_sam", "Trưởng bộ phận", "Bộ phận Mua sắm", "02436280281"),
            ("Cán bộ Bộ phận Mua sắm", "muasam@neu.edu.vn", "cb_muasam", "password123", "mua_sam", "Chuyên viên", "Bộ phận Mua sắm", "0912111222"),
            ("Cán bộ Quản lý tài sản", "kho@neu.edu.vn", "cb_kho", "password123", "quan_ly_kho", "Chuyên viên QLTS", "Bộ phận Quản lý tài sản", "0913222333"),
            ("Cán bộ Kế toán Thanh toán", "ketoan@neu.edu.vn", "cb_ketoan", "password123", "ke_toan", "Kế toán viên", "Phòng Tài chính - Kế toán", "0914333444"),
            ("TS. Nguyễn Văn Khoa", "khoa.nv@neu.edu.vn", "gv_khoacntt", "password123", "don_vi", "Phó Trưởng Khoa", "Khoa Công nghệ Thông tin", "0912345678"),
            ("ThS. Lê Minh Tú", "tu.lm@neu.edu.vn", "gv_khoaqtkd", "password123", "don_vi", "Giảng viên", "Khoa Quản trị Kinh doanh", "0987654321"),
        ]

        user_ids = {}
        for ho_ten, email, username, password, vai_tro, chuc_danh, don_vi, sdt in users:
            pw_hash = generate_password_hash(password)
            cursor = db.execute(
                """
                INSERT INTO nguoi_dung (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, chuc_danh, don_vi, so_dien_thoai, ngay_tao, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'hoat_dong')
                """,
                (ho_ten, email, username, pw_hash, vai_tro, chuc_danh, don_vi, sdt, hien_tai)
            )
            user_ids[username] = cursor.lastrowid

        print("-> Đang khởi tạo các gói đề xuất mua sắm, báo giá, nghiệm thu và dữ liệu M09...")
        from app.services.mua_sam import (
            tao_de_nghi, phe_duyet_de_nghi, tao_khao_sat,
            them_bao_gia, chon_bao_gia, lap_bien_ban_nghiem_thu,
            tao_ho_so_mua_sam, tiep_nhan_hang_hoa
        )
        from app.services.ke_toan import ghi_nhan_thanh_toan
        from app.services.tai_san import ban_giao_tai_san, tao_yeu_cau_sua_chua, tao_phieu_kiem_ke
        from app.services.bao_cao_hu_hai import gui_bao_cao, xac_minh_danh_gia, tao_yeu_cau_thay_the_sang_m08

        # 1. Đề nghị 1: Mua sắm thiết bị TSCĐ -> Lãnh đạo duyệt (>= 100tr) -> Đã nghiệm thu & tiếp nhận M09 -> Kế toán thanh toán xong
        dn1 = tao_de_nghi({
            "tieu_de": "Trang bị hệ thống máy chủ và lưu trữ đám mây cho Trung tâm CNTT",
            "don_vi_de_nghi": "Trung tâm Ứng dụng CNTT",
            "mo_ta": "Nâng cấp hạ tầng máy chủ phục vụ cổng thông tin đào tạo và học tập trực tuyến toàn trường.",
            "muc_do_uu_tien": "can_som",
            "nguon_kinh_phi": "Kinh phí tự chủ của Trường",
            "dia_diem_su_dung": "Phòng Data Center Nhà A1",
            "ly_do_su_can_thiet": "Máy chủ hiện tại đã khai thác 7 năm, quá tải giờ đăng ký tín chỉ",
            "items": [
                {"ten_hang_hoa": "Máy chủ Dell PowerEdge R750", "don_vi_tinh": "Bộ", "so_luong": 2, "don_gia_du_kien": 95000000, "vi_tri_su_dung": "Rack 1 - DC A1", "ly_do_muc_dich": "Chạy máy chủ Database", "ghi_chu": "2x Intel Xeon Gold, 128GB RAM"},
                {"ten_hang_hoa": "Hệ thống lưu trữ SAN Storage 40TB", "don_vi_tinh": "Hệ", "so_luong": 1, "don_gia_du_kien": 75000000, "vi_tri_su_dung": "Rack 2 - DC A1", "ly_do_muc_dich": "Lưu trữ dữ liệu portal", "ghi_chu": "Bảo hành 36 tháng tận nơi"}
            ]
        }, user_ids["cb_muasam"])

        # Khảo sát BM02
        tao_khao_sat(dn1["id"], {
            "noi_dung": "Khảo sát hạ tầng phòng Data Center và định mức thiết bị CNTT",
            "dia_diem": "Phòng DC Nhà A1",
            "can_bo_khao_sat": "Phòng QTTB & Trung tâm CNTT",
            "dai_dien_don_vi": "Giám đốc TT CNTT",
            "ket_qua_danh_gia": "Nhu cầu cấp thiết, phù hợp quy hoạch hạ tầng số",
            "kiem_tra_kho": "Kho hiện không có máy chủ cùng chủng loại",
            "doi_chieu_dinh_muc": "Phù hợp định mức trang bị thiết bị chuyên dùng",
            "muc_do_can_thiet": "can_thiet",
            "phuong_an_de_xuat": "mua_bo_sung",
            "ket_luan": "Phù hợp và cần thiết để tổ chức thực hiện"
        })

        # Báo giá
        them_bao_gia(dn1["id"], {"nha_cung_cap": "Công ty TNHH Hệ thống Thông tin FPT", "ma_so_thue": "0101234567", "tong_gia": 268000000, "hieu_luc": "30 ngày"})
        bg_cmc = them_bao_gia(dn1["id"], {"nha_cung_cap": "Công ty CP Công nghệ CMC", "ma_so_thue": "0107654321", "tong_gia": 265000000, "hieu_luc": "45 ngày"})
        bg_all = them_bao_gia(dn1["id"], {"nha_cung_cap": "Tập đoàn Công nghệ HPT", "ma_so_thue": "0301122334", "tong_gia": 270000000, "hieu_luc": "30 ngày"})
        cmc_id = [bg["id"] for bg in bg_all["bao_gia"] if "CMC" in bg["nha_cung_cap"]][0]
        chon_bao_gia(dn1["id"], cmc_id)

        # Lãnh đạo duyệt (>= 100 triệu)
        phe_duyet_de_nghi(dn1["id"], user_ids["admin"], "Đồng ý chủ trương mua sắm nâng cấp hạ tầng số.", vai_tro="quan_tri")

        # Hợp đồng
        tao_ho_so_mua_sam(dn1["id"], "Công ty CP Công nghệ CMC", "HĐ-2026-IT-01", 265000000, "Bảo hành 36 tháng")

        # Nghiệm thu hàng hóa
        lap_bien_ban_nghiem_thu(dn1["id"], {
            "dai_dien_ben_mua": "Trưởng BP Mua sắm",
            "dai_dien_nha_cung_cap": "Đại diện CMC",
            "dai_dien_don_vi_su_dung": "Đại diện TT CNTT",
            "ket_qua": "dat",
            "y_kien_danh_gia": "Thiết bị nguyên đai nguyên kiện, kiểm tra thông số CO/CQ đầy đủ"
        })

        # Bộ phận Quản lý tài sản tiếp nhận hàng vào kho M09 (Tự động sinh TSCĐ)
        tiep_nhan_hang_hoa(dn1["id"], {"ghi_chu": "Đã tiếp nhận đầy đủ vào kho tài sản M09."}, user_ids["cb_kho"])

        # M08 lập phiếu đề nghị thanh toán để Kế toán kiểm tra và giải ngân
        from app.services.mua_sam import tao_de_nghi_thanh_toan
        tao_de_nghi_thanh_toan(dn1["id"], {
            "noi_dung_thanh_toan": "Thanh toán gói máy chủ và lưu trữ cho Trung tâm CNTT",
            "ghi_chu": "Hồ sơ minh họa quy trình liên thông M08-M09-Kế toán"
        }, user_ids["cb_muasam"])

        # Kế toán ghi nhận giải ngân sau khi nhận phiếu thanh toán từ M08
        ghi_nhan_thanh_toan(dn1["id"], {
            "so_tien": 265000000,
            "so_hoa_don": "HD-2026-NEU-001",
            "phuong_thuc": "chuyen_khoan",
            "ghi_chu": "Thanh toán gói máy chủ qua Kho bạc Nhà nước"
        }, user_ids["cb_ketoan"])

        # Bàn giao 1 máy chủ cho chuyên viên quản lý
        db_cur = db.execute("SELECT id FROM tai_san WHERE de_nghi_id = ? LIMIT 1", (dn1["id"],)).fetchone()
        if db_cur:
            ban_giao_tai_san(db_cur["id"], user_ids["cb_kho"], user_ids["cb_kho"], "Bàn giao quản lý vận hành phòng Server")

        # 2. Đề nghị 2: Gói < 100 triệu -> Trưởng BP Mua sắm duyệt theo Yêu cầu 1.docx
        dn2 = tao_de_nghi({
            "tieu_de": "Mua sắm máy chiếu đa năng phục vụ giảng đường D2",
            "don_vi_de_nghi": "Ban Quản lý Giảng đường D2",
            "mo_ta": "Trang bị bổ sung máy chiếu cho các phòng học thực hành tin học",
            "muc_do_uu_tien": "can_som",
            "nguon_kinh_phi": "Kinh phí đào tạo",
            "dia_diem_su_dung": "Giảng đường D2",
            "ly_do_su_can_thiet": "Tăng cường trang thiết bị giảng dạy",
            "items": [
                {"ten_hang_hoa": "Máy chiếu Sony Laser VPL-CWZ10", "don_vi_tinh": "Bộ", "so_luong": 2, "don_gia_du_kien": 28000000, "vi_tri_su_dung": "Phòng D2-401, D2-402", "ghi_chu": "Độ sáng cao"}
            ]
        }, user_ids["cb_muasam"])

        # Khảo sát nhu cầu BM02 cho dn2 (bắt buộc trước khi duyệt)
        tao_khao_sat(dn2["id"], {
            "noi_dung": "Khảo sát thực tế nhu cầu trang bị máy chiếu Giảng đường D2",
            "dia_diem": "Giảng đường D2 - Phòng 401, 402",
            "can_bo_khao_sat": "Cán bộ Bộ phận Mua sắm",
            "dai_dien_don_vi": "Ban Quản lý Giảng đường D2",
            "ket_qua_danh_gia": "Phòng học chưa có máy chiếu, giảng viên phải dùng bảng phụ",
            "kiem_tra_kho": "Trong kho hiện không còn máy chiếu công suất lớn",
            "doi_chieu_dinh_muc": "Đúng định mức phòng học 80 chỗ",
            "muc_do_can_thiet": "cap_thiet",
            "phuong_an_de_xuat": "mua_moi",
            "ket_luan": "phu_hop"
        })

        # Trưởng BP Mua sắm duyệt (< 100 triệu) sau khi khảo sát đạt yêu cầu
        phe_duyet_de_nghi(dn2["id"], user_ids["truongmuasam"], "Trưởng BP Mua sắm duyệt gói < 100 triệu.", vai_tro="mua_sam")

        # 3 Báo giá cạnh tranh cho dn2
        them_bao_gia(dn2["id"], {
            "nha_cung_cap": "Công ty Cổ phần Máy tính Phúc Anh",
            "ma_so_thue": "0101987654",
            "lien_he": "02438561234 - kinhdoanh@phucanh.vn",
            "tong_gia": 57000000,
            "hieu_luc": "30 ngày",
            "ghi_chu": "Bảo hành 24 tháng chính hãng"
        })
        them_bao_gia(dn2["id"], {
            "nha_cung_cap": "Công ty TNHH Thiết bị Nghe nhìn Hà Việt",
            "ma_so_thue": "0103456789",
            "lien_he": "02439876543 - contact@haviet.com.vn",
            "tong_gia": 56000000,
            "hieu_luc": "30 ngày",
            "ghi_chu": "Bảo hành 24 tháng"
        })
        bg_res2 = them_bao_gia(dn2["id"], {
            "nha_cung_cap": "Công ty TNHH Thương mại LOGICO",
            "ma_so_thue": "0102345678",
            "lien_he": "02437654321 - sales@logico.com.vn",
            "tong_gia": 55000000,
            "hieu_luc": "30 ngày",
            "ghi_chu": "Báo giá chính hãng Sony, bảo hành 24 tháng tận nơi"
        })

        # Chọn LOGICO trúng thầu
        logico_id = [bg["id"] for bg in bg_res2["bao_gia"] if "LOGICO" in bg["nha_cung_cap"]][0]
        chon_bao_gia(dn2["id"], logico_id)

        # Lập Biên bản nghiệm thu kỹ thuật BM04 (kết quả ĐẠT)
        lap_bien_ban_nghiem_thu(dn2["id"], {
            "dai_dien_ben_mua": "Cán bộ Bộ phận Mua sắm",
            "dai_dien_nha_cung_cap": "Công ty TNHH Thương mại LOGICO",
            "dai_dien_don_vi_su_dung": "Ban Quản lý Giảng đường D2",
            "ket_qua": "dat",
            "y_kien_danh_gia": "02 máy chiếu Sony Laser nguyên đai nguyên kiện, chạy thử hình ảnh sắc nét, đúng cấu hình hợp đồng."
        })

        # M09 tiếp nhận hàng hóa vào kho (Trạng thái: Đang nghiệm thu)
        tiep_nhan_hang_hoa(dn2["id"], {"ghi_chu": "Đã tiếp nhận 02 máy chiếu Sony Laser vào kho M09."}, user_ids["cb_kho"])

        # M08 lập Giấy đề nghị thanh toán chuyển khoản cho nhà cung cấp (Trạng thái chuyển: Chờ thanh toán)
        tao_de_nghi_thanh_toan(dn2["id"], {
            "noi_dung_thanh_toan": "Thanh toán tiền mua 02 máy chiếu Sony Laser VPL-CWZ10 phục vụ giảng đường D2",
            "ve_khoan": "Thanh toán tiền mua 02 máy chiếu Sony Laser VPL-CWZ10 phục vụ giảng đường D2",
            "hop_dong_so": "HĐ-2026-SONY-02",
            "hop_dong_ngay": "10/11/2026",
            "don_vi_thu_huong": "Công ty TNHH Thương mại LOGICO",
            "so_tai_khoan": "0241000688999",
            "ngan_hang": "Ngân hàng TMCP Ngoại thương Việt Nam (Vietcombank) - CN Hà Nội",
            "ho_so_kem_theo": "Hợp đồng kinh tế, Biên bản nghiệm thu BM04, Bảng xác định giá trị, Hóa đơn điện tử",
            "ghi_chu": "Chuyển Kế toán kiểm tra và giải ngân chuyển khoản"
        }, user_ids["cb_muasam"])

        # 3. Đề nghị 3: Gói >= 100 triệu đang chờ Lãnh đạo Trường duyệt
        tao_de_nghi({
            "tieu_de": "Trang bị bàn ghế phòng học thông minh Tòa nhà A2",
            "don_vi_de_nghi": "Phòng Quản trị Thiết bị",
            "mo_ta": "Trang bị 8 phòng học thông minh phục vụ chương trình chất lượng cao.",
            "muc_do_uu_tien": "binh_thuong",
            "nguon_kinh_phi": "Quỹ phát triển hoạt động sự nghiệp",
            "dia_diem_su_dung": "Tòa nhà Thế Kỷ A2",
            "ly_do_su_can_thiet": "Đầu tư cơ sở vật chất chuẩn quốc tế",
            "items": [
                {"ten_hang_hoa": "Bàn học sinh viên nhóm ghép thông minh", "don_vi_tinh": "Bộ", "so_luong": 80, "don_gia_du_kien": 1200000, "ghi_chu": "Bàn xếp di động"},
                {"ten_hang_hoa": "Ghế lưới xoay cao cấp", "don_vi_tinh": "Chiếc", "so_luong": 160, "don_gia_du_kien": 850000, "ghi_chu": "Chống mỏi lưng"}
            ]
        }, user_ids["cb_muasam"])

        # 4. Báo cáo hư hại mẫu & Luồng xử lý M09 theo 8 giai đoạn chuẩn
        # Báo cáo 1: Đang sửa chữa (Đã khảo sát BM03 và duyệt phương án)
        bc1 = gui_bao_cao({
            "ma_bao_cao": "YC-20261109-002",
            "ho_ten": "Nguyễn Hoàng Nam (Giảng viên Khoa Marketing)",
            "lien_he": "nam.nh@neu.edu.vn",
            "don_vi": "Khoa Marketing",
            "ten_vat_chat": "Máy điều hòa phòng A1-304 chảy nước và kêu to",
            "vi_tri": "Phòng A1-304, Tòa nhà A1",
            "muc_do": "trung_binh",
            "mo_ta_chi_tiet": "Điều hòa bị đọng nước nhỏ giọt xuống dãy bàn học, phát tiếng ồn khi chạy.",
            "thoi_gian_phat_hien": hien_tai
        })
        # Lập khảo sát BM03 và duyệt phương án
        from app.services.bao_cao_hu_hai import tiep_nhan_yeu_cau, lap_khao_sat_bm03, lap_phuong_an_trinh_duyet, phe_duyet_phuong_an
        tiep_nhan_yeu_cau(bc1["id"], user_ids["cb_kho"])
        lap_khao_sat_bm03(bc1["id"], {
            "thanh_phan_khao_sat": "Cán bộ QTTB, Đại diện Khoa Marketing, Kỹ thuật viên điện lạnh",
            "hien_trang_thuc_te": "Máng thoát nước điều hòa bị tắc bụi bẩn, quạt gió khô dầu phát tiếng kêu",
            "nguyen_nhan_hu_hong": "Bụi bẩn tích tụ sau 1 năm sử dụng chưa bảo dưỡng",
            "muc_do_hu_hong": "trung_binh",
            "anh_huong_an_toan": "Nước nhỏ giọt gây trơn trượt nền nhà",
            "khoi_luong_du_kien": "Thông tắc máng xả nước, nạp bổ sung gas R410A, bảo dưỡng quạt lồng sóc",
            "nhom_sua_chua": "sua_chua_nho",
            "tinh_trang_bao_hanh": "het_bao_hanh"
        }, user_ids["cb_kho"])
        lap_phuong_an_trinh_duyet(bc1["id"], {
            "phuong_an_chi_tiet": "Thông tắc máng thoát nước, bảo dưỡng vệ sinh dàn lạnh và nạp gas bổ sung",
            "kinh_phi_du_kien": 650000,
            "nguon_kinh_phi_sua_chua": "Kinh phí bảo dưỡng thường xuyên",
            "yeu_cau_m08": 0
        }, user_ids["cb_kho"])
        phe_duyet_phuong_an(bc1["id"], {"y_kien_lanh_dao": "Duyệt phương án bảo dưỡng điều hòa A1-304"}, user_ids["truongmuasam"])

        # Báo cáo 2: Cần thay thế -> Chờ thủ tục M08
        bc2 = gui_bao_cao({
            "ma_bao_cao": "YC-20261109-003",
            "ho_ten": "Trần Thị Mai (Cán bộ Viện CNTT)",
            "lien_he": "0912345678",
            "don_vi": "Viện Công nghệ Thông tin",
            "ten_vat_chat": "Máy chiếu phòng Lab 501 cháy nguồn không lên",
            "vi_tri": "Phòng Lab 501, Nhà D2",
            "muc_do": "nghiem_trong",
            "mo_ta_chi_tiet": "Thiết bị cũ hỏng bo nguồn và bóng đèn laser, không có linh kiện thay thế.",
            "thoi_gian_phat_hien": hien_tai
        })
        lap_khao_sat_bm03(bc2["id"], {
            "thanh_phan_khao_sat": "Cán bộ QTTB, Viện CNTT, Kỹ thuật viên hãng",
            "hien_trang_thuc_te": "Cháy bo nguồn cao áp, nứt thấu kính laser",
            "nguyen_nhan_hu_hong": "Sét lan truyền trên đường dây điện nguồn",
            "muc_do_hu_hong": "nghiem_trong",
            "nhom_sua_chua": "sua_chua_thiet_bi"
        }, user_ids["cb_kho"])
        lap_phuong_an_trinh_duyet(bc2["id"], {
            "phuong_an_chi_tiet": "Mua sắm máy chiếu mới thay thế do chi phí sửa chữa vượt 80% giá trị máy",
            "kinh_phi_du_kien": 10000000,
            "yeu_cau_m08": 1
        }, user_ids["cb_kho"])
        phe_duyet_phuong_an(bc2["id"], {"y_kien_lanh_dao": "Duyệt mua sắm thay thế qua Module M08"}, user_ids["admin"])
        from app.services.bao_cao_hu_hai import lien_ket_m08_mua_sam
        lien_ket_m08_mua_sam(bc2["id"], user_ids["cb_kho"])

        # Báo cáo 3: Mới gửi chờ tiếp nhận
        gui_bao_cao({
            "ma_bao_cao": "YC-20261109-004",
            "ho_ten": "Lê Hải Đăng (Sinh viên K64)",
            "lien_he": "0988776655",
            "don_vi": "Lớp Quản trị Khách sạn K64",
            "ten_vat_chat": "Bóng đèn tuýp LED hàng ghế cuối nhấp nháy",
            "vi_tri": "Phòng C-201, Giảng đường C",
            "muc_do": "nhe",
            "mo_ta_chi_tiet": "Đèn chớp tắt liên tục làm lóa mắt sinh viên ngồi phía sau.",
            "thoi_gian_phat_hien": hien_tai
        })

        # 5. Khởi tạo tài sản phân bổ cho Đơn vị sử dụng (Khoa Công nghệ Thông tin)
        cur_ts1 = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, mo_ta, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, so_serial, model, hang_san_xuat,
                thoi_han_bao_hanh, xac_nhan_ban_giao_don_vi, ngay_tao, ngay_cap_nhat
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "TS-2026-0101", "Máy chiếu Laser EPSON EB-L520U", "Máy chiếu độ sáng cao 5200 ANSI Lumens", "Máy chiếu",
                "tai_san_co_dinh", "co_hu_hong", "Phòng Lab 502, Nhà D2", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Thông tin",
                38500000, hien_tai[:10], "dang_su_dung", "EPSON-L520-8899", "EB-L520U", "EPSON", "24 tháng", 1, hien_tai, hien_tai
            )
        )
        ts_cntt_1_id = cur_ts1.lastrowid

        cur_ts2 = db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, mo_ta, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, so_serial, model, hang_san_xuat,
                thoi_han_bao_hanh, xac_nhan_ban_giao_don_vi, ngay_tao, ngay_cap_nhat
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "TS-2026-0102", "Bộ máy tính All-in-One Dell OptiPlex 7400", "Máy tính để bàn cán bộ VP Khoa", "Máy tính",
                "tai_san_co_dinh", "binh_thuong", "Văn phòng Khoa CNTT, Nhà A1", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Thông tin",
                26000000, hien_tai[:10], "dang_su_dung", "DELL-AIO-7400-01", "OptiPlex 7400", "DELL", "36 tháng", 1, hien_tai, hien_tai
            )
        )
        ts_cntt_2_id = cur_ts2.lastrowid

        # Tài sản mới cấp phát đang chờ Khoa CNTT xác nhận bàn giao (BM03)
        db.execute(
            """
            INSERT INTO tai_san (
                ma_tai_san, ten_tai_san, mo_ta, loai_tai_san, phan_loai,
                tinh_trang_ky_thuat, vi_tri, phong_ban, don_vi_su_dung,
                gia_tri, ngay_tiep_nhan, trang_thai, so_serial, model, hang_san_xuat,
                thoi_han_bao_hanh, xac_nhan_ban_giao_don_vi, ngay_tao, ngay_cap_nhat
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "CCDC-2026-0103", "Bộ chuyển mạch Switch Cisco Catalyst 24 Port Gigabit", "Switch mạng phòng Lab mạng máy tính", "Thiết bị mạng",
                "cong_cu_dung_cu", "binh_thuong", "Phòng Lab 501, Nhà D2", "Khoa Công nghệ Thông tin", "Khoa Công nghệ Thông tin",
                8500000, hien_tai[:10], "cho_ban_giao", "CS-C1000-24T", "Catalyst 1000", "Cisco", "12 tháng", 0, hien_tai, hien_tai
            )
        )

        # 6. Yêu cầu sửa chữa thiết bị của Cán bộ Khoa CNTT (TS. Nguyễn Văn Khoa)
        db.execute(
            """
            INSERT INTO bao_cao_hu_hai (
                ma_bao_cao, nguoi_gui_id, ho_ten, lien_he, don_vi,
                ten_vat_chat, vi_tri, loai_yeu_cau, do_khan_cap, muc_do,
                mo_ta_chi_tiet, tai_san_id, trang_thai, thoi_gian_phat_hien,
                xac_nhan_khao_sat_don_vi, xac_nhan_nghiem_thu_don_vi, ngay_tao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "YC-20261109-001", user_ids["gv_khoacntt"], "TS. Nguyễn Văn Khoa", "0912345678", "Khoa Công nghệ Thông tin",
                "Máy chiếu Laser EPSON EB-L520U", "Phòng Lab 502, Nhà D2", "sua_chua_thiet_bi", "can_som", "trung_binh",
                "Máy chiếu mờ bóng, quạt tản nhiệt kêu to và tự tắt sau 30 phút hoạt động trong giờ giảng.",
                ts_cntt_1_id, "dang_xu_ly", hien_tai, 1, 0, hien_tai
            )
        )

        # 7. Đề xuất mua sắm mới từ Đơn vị Khoa CNTT (BM01)
        dn_cntt = tao_de_nghi({
            "tieu_de": "Đề xuất nâng cấp 30 bộ máy tính thực hành Lab 501 Khoa CNTT",
            "don_vi_de_nghi": "Khoa Công nghệ Thông tin",
            "mo_ta": "Trang bị dàn máy tính cấu hình cao phục vụ các học phần Trí tuệ nhân tạo và Khoa học dữ liệu.",
            "muc_do_uu_tien": "can_som",
            "nguon_kinh_phi": "Kinh phí tự chủ của Trường",
            "dia_diem_su_dung": "Phòng Lab 501, Nhà D2",
            "ly_do_su_can_thiet": "Dàn máy tính cũ đã sử dụng 6 năm, không chạy được các mô hình Deep Learning trong chương trình mới.",
            "items": [
                {
                    "ten_hang_hoa": "Máy tính Dell OptiPlex Tower (Intel Core i7, 32GB RAM, 1TB SSD, RTX 4060)",
                    "don_vi_tinh": "Bộ",
                    "so_luong": 30,
                    "don_gia_du_kien": 24500000,
                    "vi_tri_su_dung": "Phòng Lab 501, Nhà D2",
                    "ly_do_muc_dich": "Thực hành AI & Data Science",
                    "ghi_chu": "Bảo hành 36 tháng tận nơi"
                }
            ]
        }, user_ids["gv_khoacntt"])

        # 8. Đợt kiểm kê tài sản có tài sản của Khoa CNTT
        cur_kk = db.execute(
            """
            INSERT INTO phieu_kiem_ke (ma_phieu, ngay_kiem_ke, nguoi_kiem_ke_id, ghi_chu, ngay_tao)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "KK-2026-Q1", hien_tai[:10], user_ids["cb_kho"],
                "Kiểm kê toàn diện cơ sở vật chất các Khoa và Phòng thí nghiệm đầu năm học 2026 (Quý I/2026).", hien_tai
            )
        )
        kk_id = cur_kk.lastrowid

        db.execute(
            """
            INSERT INTO chi_tiet_kiem_ke (phieu_kiem_ke_id, tai_san_id, tinh_trang_thuc_te, so_luong_he_thong, so_luong_thuc_te, chenh_lech, ghi_chu)
            VALUES (?, ?, ?, 1, 1, 0, ?)
            """,
            (kk_id, ts_cntt_1_id, "Có hư hỏng (quạt kêu)", "Máy chiếu có hiện tượng mờ bóng, đã lập YC sửa chữa")
        )
        db.execute(
            """
            INSERT INTO chi_tiet_kiem_ke (phieu_kiem_ke_id, tai_san_id, tinh_trang_thuc_te, so_luong_he_thong, so_luong_thuc_te, chenh_lech, ghi_chu)
            VALUES (?, ?, ?, 1, 1, 0, ?)
            """,
            (kk_id, ts_cntt_2_id, "Lệch vị trí phòng", "Máy tính AIO ghi nhận tại VP Khoa A1 nhưng thực tế đang mượn tại Lab 501")
        )

        db.commit()
        print("-> Nạp dữ liệu mẫu hoàn tất thành công!")
        print("="*75)
        print("DANH SÁCH TÀI KHOẢN ĐĂNG NHẬP THEO QUY CHUẨN NGHIỆP VỤ:")
        print("1. Quản trị viên (Admin):    admin          / admin123  (Duyệt >= 100tr, Giám sát M17)")
        print("2. Trưởng BP Mua sắm:        truongmuasam   / muasam1234 (Duyệt < 100tr, Quản lý M08)")
        print("3. Cán bộ Mua sắm:           cb_muasam      / password123 (Lập đề xuất, Khảo sát, Báo giá)")
        print("4. Quản lý tài sản:          cb_kho         / password123 (Tiếp nhận kho M09, Sửa chữa, Kiểm kê)")
        print("5. Kế toán:                  cb_ketoan      / password123 (Thanh toán giải ngân M08)")
        print("6. Đơn vị sử dụng (Khoa CNTT): gv_khoacntt    / password123 (Theo dõi sửa chữa, đề xuất, tài sản)")
        print("7. Đơn vị sử dụng (Khoa QTKD): gv_khoaqtkd    / password123 (Đơn vị sử dụng 2)")
        print("="*75)

if __name__ == "__main__":
    nap_du_lieu()
