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

        # 5 tài khoản thuận tiện kiểm thử:
        # 1. Admin: quan_tri
        # 2. Trưởng BP Mua sắm: mua_sam (duyệt gói < 100tr)
        # 3. Cán bộ Mua sắm: mua_sam (lập đề xuất, khảo sát, báo giá)
        # 4. Quản lý tài sản: quan_ly_kho
        # 5. Kế toán: ke_toan
        users = [
            ("Lãnh đạo Trường (Admin)", "admin@neu.edu.vn", "admin", "admin123", "quan_tri", "Lãnh đạo"),
            ("Trưởng BP Mua sắm", "truongmuasam@neu.edu.vn", "truongmuasam", "muasam1234", "mua_sam", "Trưởng bộ phận"),
            ("Cán bộ Bộ phận Mua sắm", "muasam@neu.edu.vn", "cb_muasam", "password123", "mua_sam", "Chuyên viên"),
            ("Cán bộ Quản lý tài sản", "kho@neu.edu.vn", "cb_kho", "password123", "quan_ly_kho", "Chuyên viên QLTS"),
            ("Cán bộ Kế toán Thanh toán", "ketoan@neu.edu.vn", "cb_ketoan", "password123", "ke_toan", "Kế toán viên"),
        ]

        user_ids = {}
        for ho_ten, email, username, password, vai_tro, chuc_danh in users:
            pw_hash = generate_password_hash(password)
            cursor = db.execute(
                """
                INSERT INTO nguoi_dung (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, chuc_danh, ngay_tao, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'hoat_dong')
                """,
                (ho_ten, email, username, pw_hash, vai_tro, chuc_danh, hien_tai)
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
        bg2 = them_bao_gia(dn1["id"], {"nha_cung_cap": "Công ty CP Công nghệ CMC", "ma_so_thue": "0107654321", "tong_gia": 265000000, "hieu_luc": "45 ngày"})
        them_bao_gia(dn1["id"], {"nha_cung_cap": "Tập đoàn Công nghệ HPT", "ma_so_thue": "0301122334", "tong_gia": 270000000, "hieu_luc": "30 ngày"})
        chon_bao_gia(dn1["id"], bg2["bao_gia"][1]["id"])

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

        # Kế toán thanh toán
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

        # Trưởng BP Mua sắm duyệt (< 100 triệu)
        phe_duyet_de_nghi(dn2["id"], user_ids["truongmuasam"], "Trưởng BP Mua sắm duyệt gói < 100 triệu.", vai_tro="mua_sam")

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

        # 4. Báo cáo hư hại mẫu & Luồng xử lý M09
        # Báo cáo 1: Sửa chữa được -> M09 tạo yêu cầu sửa chữa
        bc1 = gui_bao_cao({
            "ho_ten": "Nguyễn Hoàng Nam (Giảng viên Khoa Marketing)",
            "lien_he": "nam.nh@neu.edu.vn",
            "ten_vat_chat": "Máy điều hòa phòng A1-304 chảy nước và kêu to",
            "vi_tri": "Phòng A1-304, Tòa nhà A1",
            "muc_do": "trung_binh",
            "mo_ta_chi_tiet": "Điều hòa bị đọng nước nhỏ giọt xuống dãy bàn học, phát tiếng ồn khi chạy.",
            "thoi_gian_phat_hien": hien_tai
        })
        xac_minh_danh_gia(bc1["id"], "sua_chua", ghi_chu="Đã cử thợ điện lạnh đến kiểm tra máng thoát nước", nguoi_xu_ly_id=user_ids["cb_kho"])

        # Báo cáo 2: Cần thay thế -> M09 chuyển sang đề xuất mua sắm M08
        bc2 = gui_bao_cao({
            "ho_ten": "Trần Thị Mai (Cán bộ Viện CNTT)",
            "lien_he": "0912345678",
            "ten_vat_chat": "Máy chiếu phòng Lab 501 cháy nguồn không lên",
            "vi_tri": "Phòng Lab 501, Nhà D2",
            "muc_do": "nghiem_trong",
            "mo_ta_chi_tiet": "Thiết bị cũ hỏng bo nguồn và bóng đèn laser, không có linh kiện thay thế.",
            "thoi_gian_phat_hien": hien_tai
        })
        tao_yeu_cau_thay_the_sang_m08(bc2["id"], user_ids["cb_kho"])

        # Báo cáo 3: Mới gửi chưa xử lý
        gui_bao_cao({
            "ho_ten": "Lê Hải Đăng (Sinh viên K64)",
            "lien_he": "0988776655",
            "ten_vat_chat": "Bóng đèn tuýp LED hàng ghế cuối nhấp nháy",
            "vi_tri": "Phòng C-201, Giảng đường C",
            "muc_do": "nhe",
            "mo_ta_chi_tiet": "Đèn chớp tắt liên tục làm lóa mắt sinh viên ngồi phía sau.",
            "thoi_gian_phat_hien": hien_tai
        })

        # 5. Đợt kiểm kê tài sản
        ts_cur = db.execute("SELECT id FROM tai_san LIMIT 3").fetchall()
        if ts_cur:
            tao_phieu_kiem_ke({
                "ghi_chu": "Kiểm kê định kỳ trang thiết bị giảng đường và phòng máy đầu năm 2026",
                "chi_tiet": [
                    {"tai_san_id": ts["id"], "tinh_trang": "tot", "so_luong_he_thong": 1, "so_luong_thuc_te": 1, "ghi_chu": "Khớp số lượng hiện vật"}
                    for ts in ts_cur
                ]
            }, user_ids["cb_kho"])

        db.commit()
        print("-> Nạp dữ liệu mẫu hoàn tất thành công!")
        print("="*68)
        print("DANH SÁCH TÀI KHOẢN ĐĂNG NHẬP THEO QUY CHUẨN NGHIỆP VỤ:")
        print("1. Quản trị viên (Admin):    admin          / admin123  (Duyệt >= 100tr, Giám sát M17)")
        print("2. Trưởng BP Mua sắm:        truongmuasam   / muasam1234 (Duyệt < 100tr, Quản lý M08)")
        print("3. Cán bộ Mua sắm:           cb_muasam      / password123 (Lập đề xuất, Khảo sát, Báo giá)")
        print("4. Quản lý tài sản:          cb_kho         / password123 (Tiếp nhận kho M09, Sửa chữa, Kiểm kê)")
        print("5. Kế toán:                  cb_ketoan      / password123 (Thanh toán giải ngân M08)")
        print("="*68)

if __name__ == "__main__":
    nap_du_lieu()
