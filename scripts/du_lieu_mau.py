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
        db.execute("DELETE FROM ho_so_mua_sam")
        db.execute("DELETE FROM chi_tiet_tiep_nhan")
        db.execute("DELETE FROM tiep_nhan_hang")
        db.execute("DELETE FROM thanh_toan")
        db.execute("DELETE FROM lich_su_ban_giao")
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

        # 4 nhóm tài khoản chuẩn xác:
        # 1. Admin: quan_tri
        # 2. Bộ phận Mua sắm: mua_sam
        # 3. Bộ phận Quản lý kho: quan_ly_kho
        # 4. Kế toán: ke_toan
        users = [
            ("Quản trị viên Hệ thống", "admin@neu.edu.vn", "admin", "admin123", "quan_tri"),
            ("Cán bộ Bộ phận Mua sắm", "muasam@neu.edu.vn", "cb_muasam", "password123", "mua_sam"),
            ("Cán bộ Quản lý kho", "kho@neu.edu.vn", "cb_kho", "password123", "quan_ly_kho"),
            ("Cán bộ Kế toán Thanh toán", "ketoan@neu.edu.vn", "cb_ketoan", "password123", "ke_toan"),
        ]

        user_ids = {}
        for ho_ten, email, username, password, vai_tro in users:
            pw_hash = generate_password_hash(password)
            cursor = db.execute(
                """
                INSERT INTO nguoi_dung (ho_ten, email, ten_dang_nhap, mat_khau_hash, vai_tro, ngay_tao, trang_thai)
                VALUES (?, ?, ?, ?, ?, ?, 'hoat_dong')
                """,
                (ho_ten, email, username, pw_hash, vai_tro, hien_tai)
            )
            user_ids[username] = cursor.lastrowid

        print("-> Đang khởi tạo các gói đề xuất mua sắm và dữ liệu kho mẫu...")
        from app.services.mua_sam import tao_de_nghi, phe_duyet_de_nghi, tiep_nhan_hang_hoa
        from app.services.ke_toan import ghi_nhan_thanh_toan
        from app.services.tai_san import ban_giao_tai_san
        from app.services.bao_cao_hu_hai import gui_bao_cao

        # 1. Đề nghị 1: Mua sắm thiết bị -> Admin duyệt -> Bộ phận kho tiếp nhận -> Kế toán thanh toán xong
        dn1 = tao_de_nghi({
            "tieu_de": "Trang bị máy chiếu và màn chiếu tự động cho phòng học A1-502",
            "don_vi_de_nghi": "Khoa Tin học Kinh tế",
            "mo_ta": "Nâng cấp cơ sở vật chất giảng đường thông minh phục vụ năm học mới.",
            "items": [
                {"ten_hang_hoa": "Máy chiếu Panasonic Laser PT-VMZ51", "don_vi_tinh": "Bộ", "so_luong": 1, "don_gia_du_kien": 35000000, "ghi_chu": "Độ sáng 5200 ANSI Lumens"},
                {"ten_hang_hoa": "Màn chiếu điện tử 150 inch", "don_vi_tinh": "Chiếc", "so_luong": 1, "don_gia_du_kien": 6500000, "ghi_chu": "Điều khiển từ xa"}
            ]
        }, user_ids["cb_muasam"])

        # Admin duyệt
        phe_duyet_de_nghi(dn1["id"], user_ids["admin"], "Đồng ý trang bị phục vụ giảng đường A1.")

        # Bộ phận kho tiếp nhận hàng vào kho
        tiep_nhan_hang_hoa(dn1["id"], {"ghi_chu": "Đã nghiệm thu thiết bị nguyên đai nguyên kiện."}, user_ids["cb_kho"])

        # Kế toán thanh toán
        ghi_nhan_thanh_toan(dn1["id"], {
            "so_tien": 41500000,
            "so_hoa_don": "HD-2026-NEU-001",
            "phuong_thuc": "chuyen_khoan",
            "ghi_chu": "Thanh toán đợt 1 hợp đồng mua sắm"
        }, user_ids["cb_ketoan"])

        # 2. Đề nghị 2: Bộ phận mua sắm đang lập, đang chờ Admin duyệt
        tao_de_nghi({
            "tieu_de": "Mua sắm hệ thống điều hòa Inverter cho Hội trường B2",
            "don_vi_de_nghi": "Phòng Quản trị Thiết bị",
            "mo_ta": "Thay thế hệ thống điều hòa cũ thường xuyên hỏng hóc.",
            "items": [
                {"ten_hang_hoa": "Điều hòa tủ đứng Daikin 50.000 BTU", "don_vi_tinh": "Bộ", "so_luong": 2, "don_gia_du_kien": 52000000, "ghi_chu": "Kèm gói lắp đặt"}
            ]
        }, user_ids["cb_muasam"])

        # 3. Đề nghị 3: Đã được Admin duyệt, đang trong quá trình mua sắm
        dn3 = tao_de_nghi({
            "tieu_de": "Trang bị bàn ghế phòng hội đồng Khoa Kinh tế học",
            "don_vi_de_nghi": "Khoa Kinh tế học",
            "mo_ta": "Bổ sung bàn ghế hội đồng phục vụ bảo vệ khóa luận và luận văn.",
            "items": [
                {"ten_hang_hoa": "Bàn họp gỗ tự nhiên 4m x 1.6m", "don_vi_tinh": "Chiếc", "so_luong": 1, "don_gia_du_kien": 18000000, "ghi_chu": "Gỗ sồi cao cấp"},
                {"ten_hang_hoa": "Ghế xoay da cao cấp", "don_vi_tinh": "Chiếc", "so_luong": 12, "don_gia_du_kien": 1500000, "ghi_chu": "Màu đen"}
            ]
        }, user_ids["cb_muasam"])
        phe_duyet_de_nghi(dn3["id"], user_ids["admin"], "Đã duyệt kinh phí hội đồng.")

        # 4. Báo cáo hư hại mẫu từ cộng đồng sinh viên / giảng viên
        gui_bao_cao({
            "ho_ten": "Lê Hải Đăng (Sinh viên K64)",
            "lien_he": "0988776655",
            "ten_vat_chat": "Máy chiếu phòng C-201 không lên đèn hình",
            "vi_tri": "Phòng C-201, Giảng đường C",
            "muc_do": "nghiem_trong",
            "mo_ta_chi_tiet": "Đang học thì máy chiếu chớp đỏ rồi tắt ngóm, bật lại không lên.",
            "thoi_gian_phat_hien": hien_tai
        })

        gui_bao_cao({
            "ho_ten": "Nguyễn Hoàng Nam",
            "lien_he": "nam.nh@neu.edu.vn",
            "ten_vat_chat": "Quạt trần phòng A1-304 phát tiếng kêu lớn",
            "vi_tri": "Phòng A1-304, Tòa nhà A1",
            "muc_do": "trung_binh",
            "mo_ta_chi_tiet": "Quạt bị rung lắc mạnh khi quay số 3, gây ồn ảnh hưởng lớp học.",
            "thoi_gian_phat_hien": hien_tai
        })

        db.commit()
        print("-> Nạp dữ liệu mẫu thành công!")
        print("="*65)
        print("DANH SÁCH TÀI KHOẢN ĐĂNG NHẬP THEO PHÂN QUYỀN MỚI:")
        print("1. Quản trị viên (Admin):    admin       / admin123    (Toàn quyền)")
        print("2. Bộ phận Mua sắm:          cb_muasam   / password123 (Truy cập M08)")
        print("3. Bộ phận Quản lý kho:      cb_kho      / password123 (Truy cập M09)")
        print("4. Kế toán:                  cb_ketoan   / password123 (Thanh toán M08)")
        print("="*65)

if __name__ == "__main__":
    nap_du_lieu()
