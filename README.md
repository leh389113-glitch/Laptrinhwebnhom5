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

Hệ thống được thiết kế với **4 nhóm tài khoản phân quyền độc lập** và cổng tiếp nhận công khai:

| Nhóm tài khoản | Mã vai trò | Phân hệ được phép truy cập | Chức năng chính |
|---|---|---|---|
| **Khách / Sinh viên / Giảng viên** | *(Công khai)* | Trang chủ, Báo cáo hư hại | Gửi phản ánh hỏng hóc thiết bị, bàn ghế, quạt, máy chiếu mà **không cần đăng nhập** |
| **Bộ phận Mua sắm** | `mua_sam` | M08 — Mua sắm (`/mua-sam/`) | Lập đề nghị mua sắm động, theo dõi tiến độ phê duyệt, quản lý hồ sơ mua sắm |
| **Bộ phận Quản lý kho** | `quan_ly_kho` | M09 — Kho & Tài sản (`/tai-san/`) | Tiếp nhận hàng hóa vào kho (tự động cấp mã `TS-YYYYMMDD-XXX`), biên bản bàn giao, ghi nhận bảo trì, lập phiếu kiểm kê |
| **Kế toán** | `ke_toan` | M08 — Kế toán (`/ke-toan/`) | Xem các gói mua sắm đã nhận hàng tại kho, thực hiện thanh toán hóa đơn, xem lịch sử giải ngân |
| **Quản trị viên (Admin)** | `quan_tri` | Toàn quyền (Admin, M08, M09, M17) | Phê duyệt/từ chối đề nghị, điều phối xử lý báo cáo hư hại, xem Dashboard KPI và biểu đồ M17, quản lý tài khoản & phân quyền |

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
│   │   ├── bao_cao.py           # Thống kê KPI, biểu đồ M17, xuất tệp CSV
│   │   └── bao_cao_hu_hai.py    # Xử lý phản ánh sự cố hư hại từ người dùng
│   ├── routes/                  # Tầng định tuyến HTTP (chỉ nhận request, gọi service, trả view)
│   │   ├── __init__.py          # Decorators kiểm tra đăng nhập và phân quyền vai trò
│   │   ├── main.py              # Trang chủ và Form báo cáo hư hại (public)
│   │   ├── auth.py              # Đăng nhập, đăng ký, đăng xuất
│   │   ├── mua_sam.py           # Blueprint M08 Bộ phận Mua sắm
│   │   ├── ke_toan.py           # Blueprint M08 Kế toán
│   │   ├── tai_san.py           # Blueprint M09 Quản lý Kho & Tài sản
│   │   └── admin.py             # Blueprint Admin Dashboard & Báo cáo M17
│   ├── templates/               # Giao diện HTML Jinja2 (Phong cách NEU)
│   │   ├── base.html            # Layout master (Header, Navbar, Footer NEU)
│   │   ├── main/                # trang_chu.html, bao_cao_hu_hai.html, cam_on.html
│   │   ├── auth/                # dang_nhap.html, dang_ky.html
│   │   ├── mua_sam/             # danh_sach.html, tao_de_nghi.html, chi_tiet.html, tiep_nhan.html, ho_so.html
│   │   ├── ke_toan/             # danh_sach.html, chi_tiet.html, lich_su.html
│   │   ├── tai_san/             # danh_sach.html, chi_tiet.html, chinh_sua.html, bao_tri.html, kiem_ke.html
│   │   ├── admin/               # dashboard.html, mua_sam.html, tai_san.html, bao_cao.html, bao_cao_hu_hai.html, tai_khoan.html
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
│   ├── test_bao_cao.py          # Test M17 Dashboard, xuất CSV
│   └── test_bao_cao_hu_hai.py   # Test gửi báo cáo hư hại công khai
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
*Script sẽ tự động tạo cơ sở dữ liệu `csvc.db` kèm đầy đủ tài khoản, đề xuất mua sắm, tài sản trong kho và báo cáo hư hại mẫu.*

### Bước 4: Khởi động Website
Chạy trực tiếp file `run.py`:
```bash
python run.py
```
Website sẽ chạy tại địa chỉ: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

---

## 🔑 5. Danh sách tài khoản thử nghiệm

| STT | Vai trò | Tên đăng nhập | Mật khẩu | Chức năng thử nghiệm |
|:---:|---|:---:|:---:|---|
| **1** | **Quản trị viên (Admin)** | `admin` | `admin123` | Phê duyệt/từ chối đề xuất, xem Dashboard KPI M17, xuất báo cáo CSV, điều chuyển phân quyền |
| **2** | **Bộ phận Mua sắm** | `cb_muasam` | `password123` | Lập đề nghị mua sắm M08 (thêm động các dòng vật tư, tự động tính tổng tiền), theo dõi tiến độ |
| **3** | **Bộ phận Quản lý kho** | `cb_kho` | `password123` | Tiếp nhận hàng nhập kho (tự động tạo mã `TS-...`), bàn giao tài sản, ghi nhận bảo trì, tạo phiếu kiểm kê M09 |
| **4** | **Kế toán** | `cb_ketoan` | `password123` | Xem các gói đề xuất đã nhận hàng, ghi nhận thanh toán hóa đơn M08 |
| **5** | **Khách / Sinh viên** | *(Không cần đăng nhập)* | *(Trống)* | Truy cập trang chủ, nhấn nút đỏ **"Báo cáo hư hại"** để gửi sự cố hỏng hóc |

---

## 🧪 6. Chạy kiểm thử tự động (Unit Tests)

Dự án đi kèm bộ test suite toàn diện với **19 kịch bản kiểm thử độc lập**:
```bash
# Chạy toàn bộ test suite
pytest

# Chạy với thông tin chi tiết từng test
pytest -v
```
**Kết quả kiểm tra**: `19 passed in 100%`.

