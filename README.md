# HỆ THỐNG QUẢN LÝ CƠ SỞ VẬT CHẤT — ĐẠI HỌC KINH TẾ QUỐC DÂN (NEU)

> Hệ thống số hóa toàn diện quy trình quản lý cơ sở vật chất từ **Đề xuất mua sắm &rarr; Phê duyệt &rarr; Nhập kho & Bàn giao tài sản &rarr; Kế toán thanh toán &rarr; Kiểm kê, bảo trì &rarr; Dashboard & Báo cáo thống kê**, được thiết kế theo chuẩn nhận diện thương hiệu trường **Đại học Kinh tế Quốc dân (NEU)**.

---

## 📌 1. Giới thiệu tổng quan

* **Mục tiêu**: Giảm thiểu sai sót thủ công, chuẩn hóa quy trình mua sắm, quản lý tài sản tập trung và hỗ trợ lãnh đạo ra quyết định dựa trên dữ liệu thời gian thực.
* **Công nghệ sử dụng**:
  * **Backend**: Python 3.13, Flask 3.1.1, Werkzeug 3.1.3
  * **Database**: SQLite3 (với `Row` factory và ràng buộc khóa ngoại `PRAGMA foreign_keys = ON`)
  * **Frontend**: HTML5, CSS3, JavaScript, Jinja2, Bootstrap 5.3, Font Awesome 6.5, Chart.js 4.4
  * **Kiểm thử tự động**: pytest 8.3.5
* **Giao diện nhận diện NEU**:
  * Logo chính thức của NEU (`neu_logo.webp`) hiển thị tại thanh điều hướng, favicon và chân trang.
  * Phông chữ chuẩn `Source Sans Pro`.
  * Màu sắc chủ đạo: Xanh Navy (`#002D62`), Xanh dương (`#0B4F9C`), Đỏ điểm xuyết (`#C41230`) và Vàng gold (`#F5A623`).

---

## 👥 2. Các phân hệ và đối tượng người dùng

Hệ thống được thiết kế với **5 vai trò tài khoản nội bộ** và cổng thông tin công khai:

| Nhóm tài khoản | Mã vai trò | Phân hệ được phép truy cập | Chức năng chính |
|---|---|---|---|
| **Khách vãng lai** | *(Chưa đăng nhập)* | Trang chủ, đăng nhập, đăng ký | Tra cứu thông tin chung và đăng nhập hoặc đăng ký tài khoản Đơn vị sử dụng |
| **Bộ phận Mua sắm** | `mua_sam` | M08 — Mua sắm (`/mua-sam/`) | Lập đề nghị mua sắm, quản lý hồ sơ chào hàng; Trưởng BP Mua sắm phê duyệt các gói < 100 triệu |
| **Bộ phận Quản lý tài sản** | `quan_ly_kho` | M09 — Quản lý tài sản (`/tai-san/`) | Tiếp nhận hàng hóa vào kho, cấp mã tài sản, bàn giao cho cán bộ Ban Quản lý Tòa A1/A2/BCD, ghi nhận bảo trì, lập phiếu kiểm kê, xử lý sửa chữa và lập hồ sơ thanh toán |
| **Đơn vị sử dụng** | `don_vi` | M09 — Yêu cầu sửa chữa, tài sản đơn vị; M08 — Đề xuất mua sắm | Gửi yêu cầu sửa chữa, theo dõi tiến độ, phối hợp nghiệm thu, tra cứu tài sản và lập đề xuất mua sắm |
| **Kế toán** | `ke_toan` | M08 — Kế toán (`/ke-toan/`) | Tiếp nhận hồ sơ thanh toán mua sắm và sửa chữa, kiểm tra chứng từ, yêu cầu bổ sung, xác nhận thanh toán |
| **Quản trị viên (Admin)** | `quan_tri` | Giám sát toàn hệ thống & Phê duyệt | Phê duyệt đề nghị mua sắm (bắt buộc duyệt các gói ≥ 100 triệu), quản trị tài khoản và **duyệt riêng phương án sửa chữa M09**; không thực hiện các nghiệp vụ tiếp nhận, khảo sát, thi công hay nghiệm thu |

### Luồng sửa chữa M09

1. Đơn vị gửi yêu cầu; QTTB tiếp nhận hoặc trả lại để bổ sung thông tin.
2. QTTB khảo sát hiện trạng, bảo hành, mức độ hư hỏng, ảnh hưởng an toàn và khối lượng công việc; lưu biên bản BM03 cùng ảnh.
3. QTTB trình phương án và dự toán. Admin chỉ thực hiện bước phê duyệt phương án này.
4. Nếu cần mua vật tư/thuê dịch vụ, QTTB tạo đề nghị M08 liên kết; sau khi M08 được tiếp nhận, QTTB bắt đầu thi công.
5. QTTB cập nhật nhật ký thi công/ảnh và lập biên bản nghiệm thu. Đơn vị sử dụng xác nhận đạt hoặc yêu cầu khắc phục; đạt thì cập nhật lịch sử bảo trì và khôi phục trạng thái tài sản.
6. QTTB lập/sửa hồ sơ đề nghị thanh toán, gửi Kế toán M08. Kế toán tiếp nhận, xử lý hoặc yêu cầu bổ sung; chỉ Kế toán xác nhận đã thanh toán để hoàn tất quy trình sửa chữa.

Trạng thái hiển thị: **Chờ tiếp nhận → Chờ khảo sát → Đang khảo sát (BM03) → Chờ phê duyệt phương án → Chờ thủ tục M08 (nếu cần) → Đang sửa chữa → Chờ nghiệm thu → Chờ lập hồ sơ thanh toán → Chờ thanh toán → Đang xử lý thanh toán → Đã thanh toán**. Kế toán có thể chuyển hồ sơ sang **Yêu cầu bổ sung hồ sơ**; nếu nghiệm thu không đạt, phiếu chuyển **Không đạt yêu cầu** và quay lại thi công khắc phục.

Tài sản chỉ được bàn giao cho cán bộ có tài khoản Đơn vị sử dụng thuộc Ban Quản lý Tòa A1, A2 hoặc BCD. Sau khi bàn giao, tài sản không thể chuyển sang Ban Quản lý khác; chỉ có thể đổi người nhận trong cùng đơn vị tiếp nhận.

### Báo cáo Admin M17

Trang báo cáo Admin xuất hai biểu mẫu PDF mang tên Đại học Kinh tế Quốc dân: báo cáo Mua sắm theo bố cục Thẻ tài sản cố định (S11-DNN) và báo cáo Tài sản theo bố cục Bảng kê mua hàng (Mẫu 06-VT). Tài liệu sử dụng phông Times New Roman nhúng hỗ trợ tiếng Việt, khổ A4 dọc, lề theo thể thức văn bản hành chính và cỡ chữ nội dung 13 pt. Các chức năng tải CSV đã được gỡ bỏ.

---

## 🗂️ 3. Cấu trúc thư mục dự án

```text
Web quản lý cơ sở vật chất/
├── app/
│   ├── __init__.py              # Application Factory (tao_app), bộ lọc Jinja2, đăng ký Blueprints
│   ├── db.py                    # Kết nối SQLite, tự động khởi tạo bảng CSDL
│   ├── clock.py                 # Cung cấp clock.now(), hỗ trợ mock thời gian qua CSV_GIO
│   ├── errors.py                # Xử lý ngoại lệ nghiệp vụ (LoiNghiepVu)
│   ├── schemas.py               # Xác thực dữ liệu đầu vào trước khi vào Service
│   ├── services/                # Tầng chứa 100% logic nghiệp vụ
│   │   ├── auth.py              # Đăng ký, đăng nhập, phân quyền, mã hóa mật khẩu
│   │   ├── mua_sam.py           # Nghiệp vụ M08 (lập đề nghị, duyệt, tạo tài sản tự động)
│   │   ├── ke_toan.py           # Nghiệp vụ thanh toán M08
│   │   ├── tai_san.py           # Nghiệp vụ M09 (bàn giao, bảo trì, kiểm kê)
│   │   ├── bao_cao.py           # Thống kê KPI, biểu đồ M17, xuất báo cáo PDF
│   ├── routes/                  # Tầng định tuyến HTTP (chỉ nhận request, gọi service, trả view)
│   │   ├── __init__.py          # Decorators kiểm tra đăng nhập và phân quyền vai trò
│   │   ├── main.py              # Trang chủ công khai
│   │   ├── auth.py              # Đăng nhập, đăng ký, đăng xuất
│   │   ├── mua_sam.py           # Blueprint M08 Bộ phận Mua sắm
│   │   ├── ke_toan.py           # Blueprint M08 Kế toán
│   │   ├── tai_san.py           # Blueprint M09 Quản lý tài sản
│   │   └── admin.py             # Blueprint Admin Dashboard & Báo cáo M17
│   ├── templates/               # Giao diện HTML Jinja2 (Phong cách NEU)
│   │   ├── base.html            # Layout master (Header, Navbar, Footer NEU)
│   │   ├── main/                # trang_chu.html
│   │   ├── auth/                # dang_nhap.html, dang_ky.html
│   │   ├── mua_sam/             # danh_sach.html, tao_de_nghi.html, chi_tiet.html, tiep_nhan.html, ho_so.html
│   │   ├── ke_toan/             # danh_sach.html, chi_tiet.html, lich_su.html
│   │   ├── tai_san/             # danh_sach.html, chi_tiet.html, chinh_sua.html, bao_tri.html, kiem_ke.html
│   │   ├── admin/               # dashboard.html, mua_sam.html, tai_san.html, bao_cao.html, tai_khoan.html
│   │   └── errors/              # 403.html, 404.html, loi.html
│   └── static/                  # Tệp tĩnh: CSS, hình ảnh, JavaScript
│       ├── css/style.css        # Toàn bộ CSS phong cách NEU
│       └── img/neu_logo.webp    # Logo chính thức của trường NEU
├── scripts/
│   └── du_lieu_mau.py           # Script nạp CSDL mẫu ban đầu
├── tests/                       # Bộ kiểm thử tự động (pytest)
│   ├── conftest.py              # Fixtures app, client, auth
│   ├── test_auth.py             # Test đăng nhập, phân quyền, redirect theo vai trò
│   ├── test_mua_sam.py          # Test M08 mua sắm, phê duyệt, tiếp nhận hàng
│   ├── test_ke_toan.py          # Test thanh toán hóa đơn
│   ├── test_tai_san.py          # Test M09 kho, bàn giao, bảo trì
│   ├── test_bao_cao.py          # Test M17 Dashboard, xuất PDF theo biểu mẫu
├── .env.example                 # Mẫu cấu hình môi trường
├── requirements.txt             # Danh sách thư viện Python
├── run.py                       # File thực thi khởi động server chính
└── README.md                    # Tài liệu hướng dẫn này
```

---

## 🚀 4. Hướng dẫn cài đặt và chạy trên VS Code

### Bước 1: Mở Terminal trong VS Code
* Mở thư mục dự án trong VS Code.
* Nhấn tổ hợp phím **`Ctrl + ~`** (hoặc chọn **Terminal &rarr; New Terminal** trên thanh menu).

### Bước 2: Cài đặt các thư viện cần thiết
```bash
pip install -r requirements.txt
```

### Bước 3: Nạp dữ liệu mẫu ban đầu (Khởi tạo CSDL)
```bash
python scripts/du_lieu_mau.py
```
*Script sẽ tự động tạo cơ sở dữ liệu `csvc.db` kèm tài khoản mẫu, đề xuất mua sắm, tài sản trong kho và yêu cầu sửa chữa mẫu.*

### Bước 4: Khởi động Website
Chạy trực tiếp file `run.py`:
```bash
`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````                                                                                                                                                                                                                                                                  python run.py`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````
```
Website sẽ chạy tại địa chỉ: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 🔑 5. Danh sách tài khoản thử nghiệm

| STT | Vai trò | Tên đăng nhập | Mật khẩu | Đơn vị / chức năng |
|:---:|---|:---:|:---:|---|
| **1** | **Quản trị viên (Admin)** | `admin` | `admin123` | Phê duyệt đề xuất, xem Dashboard M17, quản lý tài khoản |
| **2** | **Trưởng Bộ phận Mua sắm** | `truongmuasam` | `muasam1234` | Duyệt đề nghị dưới 100 triệu |
| **3** | **Cán bộ Mua sắm** | `cb_muasam` | `password123` | Lập đề nghị, khảo sát, quản lý báo giá |
| **4** | **Quản lý tài sản** | `cb_kho` | `password123` | Tiếp nhận tài sản, bàn giao, bảo trì, kiểm kê và xử lý sửa chữa |
| **5** | **Kế toán** | `cb_ketoan` | `password123` | Kiểm tra chứng từ và ghi nhận thanh toán |
| **6** | **Đơn vị sử dụng — Tòa A1** | `bql_a1` | `password123` | Gửi yêu cầu sửa chữa và đề xuất mua sắm |
| **7** | **Đơn vị sử dụng — Tòa A2** | `bql_a2` | `password123` | Tài khoản Đơn vị sử dụng |
| **8** | **Đơn vị sử dụng — Tòa BCD** | `bql_bcd` | `password123` | Tài khoản Đơn vị sử dụng |

---

## 🧪 6. Chạy kiểm thử tự động (Unit Tests)

Dự án đi kèm bộ test suite pytest cho xác thực, phân quyền và các luồng nghiệp vụ:
```bash
# Chạy toàn bộ test suite
pytest

# Chạy với thông tin chi tiết từng test
pytest -v
```
**Kết quả xác minh gần nhất**: `37 passed`.
