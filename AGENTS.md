# AGENTS.md — Hướng dẫn cho AI Agent

> Tài liệu này mô tả toàn bộ quy ước, kiến trúc và hướng dẫn hành vi dành cho AI Agent khi làm việc trong dự án **Website Quản lý Cơ sở Vật chất**.  
> Agent **phải đọc và tuân thủ** toàn bộ nội dung trong file này trước khi thực hiện bất kỳ thay đổi nào.

---

## 1. Tổng quan dự án

| Mục | Nội dung |
|---|---|
| **Tên đề tài** | Xây dựng Website Quản lý Cơ sở Vật chất |
| **Mục tiêu** | Số hóa quy trình mua sắm, tiếp nhận, quản lý tài sản và tổng hợp báo cáo tại trường đại học |
| **Công nghệ** | Python (Flask), HTML, CSS, JavaScript, SQLite (sqlite3), Jinja2, pytest |
| **Ngôn ngữ giao diện** | Tiếng Việt |
| **Ngôn ngữ code** | Tiếng Việt cho tên biến nghiệp vụ, tên bảng CSDL, thông báo lỗi; tiếng Anh cho tên hàm kỹ thuật và cú pháp |

### Mục tiêu nghiệp vụ

- Nghiên cứu, phân tích quy trình quản lý cơ sở vật chất từ khâu **đề xuất mua sắm → tiếp nhận → quản lý tài sản → tổng hợp báo cáo**.
- Số hóa quy trình mua sắm và quản lý tài sản tập trung.
- Giảm thiểu sai sót thủ công, tiết kiệm thời gian xử lý.
- Hỗ trợ lãnh đạo ra quyết định dựa trên dữ liệu thực tế.

---

## 2. Đối tượng người dùng và phân quyền

| Vai trò | Mã vai trò | Trang được phép truy cập |
|---|---|---|
| Bộ phận mua sắm & kho | `mua_sam` | Trang M08-Mua sắm, Trang M09-Kho/Tài sản |
| Kế toán | `ke_toan` | Trang M08-Kế toán |
| Người dùng nội bộ | `nguoi_dung` | Trang M09-Kho/Tài sản (chỉ xem tài sản được bàn giao) |
| Admin | `quan_tri` | Trang Admin (toàn bộ M08, M09, M17 + phê duyệt mua sắm + quản lý tài khoản) |
| Khách / Chưa đăng nhập | _(không có)_ | Trang chủ, Trang báo cáo hư hại, Trang đăng nhập/đăng ký |

> **Quy tắc phân quyền:** Mọi route có bảo vệ phải kiểm tra `session["vai_tro"]`. Nếu không đủ quyền hoặc chưa đăng nhập, redirect về trang đăng nhập (HTTP 302) hoặc trả về HTTP 403 kèm thông báo tiếng Việt.

---

## 3. Kiến trúc trang (Pages Architecture)

Hệ thống gồm **7 trang chính** với chính sách truy cập khác nhau:

### 3.1 Tổng quan các trang

| # | Tên trang | URL | Quyền truy cập | Blueprint |
|---|---|---|---|---|
| 1 | Trang chủ | `/` | Public (ai cũng xem được) | `main` |
| 2 | Đăng nhập / Đăng ký | `/dang-nhap`, `/dang-ky` | Public (chưa đăng nhập) | `auth` |
| 3 | M08 — Mua sắm | `/mua-sam/` | `mua_sam`, `quan_tri` | `mua_sam` |
| 4 | M08 — Kế toán | `/ke-toan/` | `ke_toan`, `quan_tri` | `ke_toan` |
| 5 | M09 — Kho & Tài sản | `/tai-san/` | `mua_sam`, `nguoi_dung`, `quan_tri` | `tai_san` |
| 6 | Báo cáo hư hại | `/bao-cao-hu-hai` | Public (không cần đăng nhập) | `main` |
| 7 | Admin Dashboard | `/admin/` | `quan_tri` | `admin` |

---

### 3.2 Trang chủ (`/`)

**Mục đích:** Giới thiệu hệ thống, điều hướng đến các chức năng chính.

**Hiển thị với mọi người dùng (public):**
- Tên và logo hệ thống
- Mô tả ngắn về chức năng quản lý cơ sở vật chất
- Nút **"Báo cáo hư hại vật chất"** → `/bao-cao-hu-hai`
- Nút **"Đăng nhập"** → `/dang-nhap`
- Nút **"Đăng ký"** → `/dang-ky`

**Template:** `templates/main/trang_chu.html`  
**Route:** `GET /`

---

### 3.3 Trang Đăng nhập / Đăng ký (`/dang-nhap`, `/dang-ky`)

**Mục đích:** Xác thực danh tính và phân quyền người dùng trước khi điều hướng đến trang tương ứng.

#### Đăng nhập (`/dang-nhap`)
- Form nhập: tên đăng nhập, mật khẩu
- Sau khi xác thực thành công → lưu `session["vai_tro"]` và `session["nguoi_dung_id"]`
- **Redirect theo vai trò:**

```
vai_tro == "mua_sam"   → /mua-sam/
vai_tro == "ke_toan"   → /ke-toan/
vai_tro == "nguoi_dung"→ /tai-san/cua-toi
vai_tro == "quan_tri"  → /admin/          (Admin — toàn quyền)
```

- Nếu sai thông tin → hiển thị lỗi ngay trang đăng nhập (không redirect)
- Nếu đã đăng nhập → tự động redirect theo vai trò (không cho vào lại trang đăng nhập)

#### Đăng ký (`/dang-ky`)
- Form nhập: họ tên, email, tên đăng nhập, mật khẩu, xác nhận mật khẩu
- Vai trò mặc định khi đăng ký: `nguoi_dung`
- Sau khi đăng ký thành công → redirect về `/dang-nhap` kèm thông báo thành công
- Admin có thể thay đổi vai trò tại trang `/admin/tai-khoan`

**Templates:**
- `templates/auth/dang_nhap.html`
- `templates/auth/dang_ky.html`

**Routes:**
- `GET/POST /dang-nhap`
- `GET/POST /dang-ky`
- `GET /dang-xuat` → xóa session, redirect về `/`

---

### 3.4 Trang M08 — Mua sắm (`/mua-sam/`)

**Vai trò được phép:** `mua_sam`, `quan_tri`

**Mô tả:** Quản lý toàn bộ vòng đời đề nghị mua sắm, từ lập đề nghị đến tiếp nhận hàng. Chức năng phê duyệt/từ chối do **Admin** thực hiện tại trang Admin hoặc trực tiếp trên trang mua sắm.

**Các trang con và chức năng:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /mua-sam/` | Danh sách đề nghị mua sắm | `mua_sam`, `quan_tri` |
| `GET/POST /mua-sam/de-nghi/tao` | Form lập đề nghị mới | `mua_sam`, `quan_tri` |
| `GET /mua-sam/de-nghi/<id>` | Xem chi tiết đề nghị | `mua_sam`, `quan_tri` |
| `POST /mua-sam/de-nghi/<id>/phe-duyet` | Phê duyệt đề nghị | `quan_tri` |
| `POST /mua-sam/de-nghi/<id>/tu-choi` | Từ chối đề nghị | `quan_tri` |
| `GET/POST /mua-sam/de-nghi/<id>/tiep-nhan` | Ghi nhận tiếp nhận hàng | `mua_sam`, `quan_tri` |
| `GET /mua-sam/ho-so` | Danh sách hồ sơ mua sắm | `mua_sam`, `quan_tri` |

**Luồng nghiệp vụ:**
```
[Lập đề nghị] → [Gửi phê duyệt] → [Admin phê duyệt/từ chối]
    → [Tạo hồ sơ mua sắm] → [Tiếp nhận hàng hóa] → [Chuyển sang M09]
```

**Trạng thái đề nghị:**
- `cho_phe_duyet` — Chờ phê duyệt
- `da_phe_duyet` — Đã phê duyệt
- `tu_choi` — Từ chối
- `dang_mua` — Đang mua sắm
- `da_nhan` — Đã tiếp nhận hàng *(tự động tạo tài sản trong M09)*
- `hoan_tat` — Hoàn tất (đã thanh toán)

**Templates:** `templates/mua_sam/`

---

### 3.5 Trang M08 — Kế toán (`/ke-toan/`)

**Vai trò được phép:** `ke_toan`, `quan_tri`

**Mô tả:** Quản lý thanh toán cho các đề nghị mua sắm đã được tiếp nhận.

**Các trang con và chức năng:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /ke-toan/` | Danh sách đề nghị chờ thanh toán | `ke_toan`, `quan_tri` |
| `GET /ke-toan/de-nghi/<id>` | Xem chi tiết đề nghị và hóa đơn | `ke_toan`, `quan_tri` |
| `POST /ke-toan/de-nghi/<id>/thanh-toan` | Ghi nhận đã thanh toán | `ke_toan`, `quan_tri` |
| `GET /ke-toan/lich-su` | Lịch sử các khoản đã thanh toán | `ke_toan`, `quan_tri` |

**Templates:** `templates/ke_toan/`

---

### 3.6 Trang M09 — Kho & Tài sản (`/tai-san/`)

**Vai trò được phép:** `mua_sam`, `nguoi_dung` (chỉ xem), `quan_tri`

**Mô tả:** Theo dõi vòng đời tài sản từ tiếp nhận đến thanh lý.

**Các trang con và chức năng:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /tai-san/` | Danh sách toàn bộ tài sản | `mua_sam`, `quan_tri` |
| `GET /tai-san/cua-toi` | Tài sản được bàn giao cho tôi | `nguoi_dung`, `mua_sam`, `quan_tri` |
| `GET /tai-san/<id>` | Xem chi tiết tài sản | `mua_sam`, `nguoi_dung`, `quan_tri` |
| `GET/POST /tai-san/<id>/chinh-sua` | Chỉnh sửa thông tin tài sản | `mua_sam`, `quan_tri` |
| `POST /tai-san/<id>/ban-giao` | Bàn giao tài sản cho người dùng | `mua_sam`, `quan_tri` |
| `GET/POST /tai-san/<id>/bao-tri` | Ghi nhận bảo trì/sửa chữa | `mua_sam`, `quan_tri` |
| `GET /tai-san/kiem-ke` | Danh sách phiếu kiểm kê | `mua_sam`, `quan_tri` |
| `POST /tai-san/kiem-ke/tao` | Tạo phiếu kiểm kê mới | `mua_sam`, `quan_tri` |

**Luồng nghiệp vụ:**
```
[Tiếp nhận từ M08] → [Cấp mã tài sản] → [Bàn giao đơn vị]
    → [Theo dõi bảo trì/sửa chữa] → [Kiểm kê định kỳ] → [Thanh lý/Xóa sổ]
```

**Trạng thái tài sản:**
- `cho_ban_giao` — Chưa bàn giao (trong kho)
- `dang_su_dung` — Đang sử dụng
- `dang_sua_chua` — Đang sửa chữa/bảo trì
- `cho_thanh_ly` — Chờ thanh lý
- `da_thanh_ly` — Đã thanh lý

**Templates:** `templates/tai_san/`

---

### 3.7 Trang Báo cáo hư hại vật chất (`/bao-cao-hu-hai`)

**Vai trò được phép:** **Tất cả mọi người — không cần đăng nhập**

**Mô tả:** Form đơn giản để bất kỳ ai (học sinh, giảng viên, nhân viên, khách) có thể báo cáo sự cố hư hại vật chất mà không cần tài khoản.

**Các trang con và chức năng:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /bao-cao-hu-hai` | Hiển thị form báo cáo | Public |
| `POST /bao-cao-hu-hai` | Gửi báo cáo hư hại | Public |
| `GET /bao-cao-hu-hai/cam-on` | Trang xác nhận đã gửi thành công | Public |

**Thông tin trong form báo cáo:**
- Họ tên người báo cáo *(bắt buộc)*
- Số điện thoại hoặc email liên hệ *(bắt buộc)*
- Tên / mô tả vật chất bị hư hại *(bắt buộc)*
- Vị trí xảy ra hư hại (phòng, tòa nhà) *(bắt buộc)*
- Mức độ hư hại: Nhẹ / Trung bình / Nghiêm trọng *(bắt buộc)*
- Mô tả chi tiết *(tùy chọn)*
- Thời gian phát hiện *(tùy chọn, mặc định là hiện tại)*

> **Lưu ý:** Báo cáo này sẽ được bộ phận quản lý tài sản xem xét tại trang M09. Không cần xác thực — chỉ cần validate dữ liệu đầu vào qua `schemas.py`.

**Templates:** `templates/main/bao_cao_hu_hai.html`, `templates/main/cam_on.html`

---

### 3.8 Trang Admin Dashboard (`/admin/`)

**Vai trò được phép:** `quan_tri` (Admin — toàn quyền)

**Mô tả:** Trang quản trị tổng hợp dành riêng cho Admin — truy cập và chỉnh sửa cả 3 module M08, M09, M17; **phê duyệt/từ chối đề nghị mua sắm**; xem dashboard báo cáo; quản lý tài khoản người dùng.

**Các trang con và chức năng:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /admin/` | Dashboard M17: thống kê tổng quan + biểu đồ | `quan_tri` |
| `GET /admin/mua-sam` | Toàn bộ chức năng M08: xem, **phê duyệt/từ chối**, sửa | `quan_tri` |
| `GET /admin/tai-san` | Toàn bộ chức năng M09 (xem, sửa, bàn giao) | `quan_tri` |
| `GET /admin/bao-cao` | Báo cáo M17: mua sắm, tài sản, xuất CSV | `quan_tri` |
| `GET /admin/bao-cao-hu-hai` | Danh sách báo cáo hư hại từ người dùng | `quan_tri` |
| `GET /admin/tai-khoan` | Quản lý tài khoản người dùng và vai trò | `quan_tri` |
| `POST /admin/tai-khoan/<id>/doi-vai-tro` | Thay đổi vai trò người dùng | `quan_tri` |

**Nội dung Dashboard M17 (`/admin/`):**
- **Thống kê nhanh (KPI cards):** Số đề nghị chờ duyệt, số tài sản đang sử dụng, chi tiêu tháng này, số báo cáo hư hại chưa xử lý
- **Biểu đồ cột:** Tình hình mua sắm theo tháng
- **Biểu đồ tròn:** Phân bổ tình trạng tài sản
- **Bảng:** Đề nghị mua sắm gần đây, tài sản mới tiếp nhận
- **Xuất báo cáo:** CSV hoặc in từ trình duyệt

**Templates:** `templates/admin/`

---

### 3.9 Luồng phân quyền tổng thể

```
Người dùng truy cập URL
        │
        ├─ URL public? (/,  /bao-cao-hu-hai, /dang-nhap, /dang-ky)
        │       └─ Cho phép truy cập trực tiếp
        │
        └─ URL bảo vệ?
                │
                ├─ Chưa đăng nhập?
                │       └─ Redirect → /dang-nhap
                │
                └─ Đã đăng nhập → Kiểm tra vai_tro trong session
                        │
                        ├─ /mua-sam/*   → cần: mua_sam | quan_tri
                        ├─ /ke-toan/*   → cần: ke_toan | quan_tri
                        ├─ /tai-san/*   → cần: mua_sam | nguoi_dung | quan_tri
                        └─ /admin/*     → cần: quan_tri (Admin)
                                │
                                └─ Không đủ quyền → HTTP 403 + thông báo tiếng Việt
```

---

## 4. Kiến trúc thư mục dự án

```
project_root/
├── app/
│   ├── __init__.py              # Khởi tạo Flask app, đăng ký blueprint, cấu hình
│   ├── db.py                    # Kết nối SQLite, tự khởi tạo bảng
│   ├── clock.py                 # Cung cấp clock.now() với hỗ trợ mock time
│   ├── errors.py                # Xử lý ngoại lệ nghiệp vụ
│   ├── schemas.py               # Xác thực dữ liệu đầu vào/ra
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py              # Logic đăng nhập, đăng ký, hash mật khẩu
│   │   ├── mua_sam.py           # Logic nghiệp vụ module M08
│   │   ├── ke_toan.py           # Logic thanh toán (thuộc M08)
│   │   ├── tai_san.py           # Logic nghiệp vụ module M09
│   │   ├── bao_cao.py           # Logic tổng hợp báo cáo M17
│   │   └── bao_cao_hu_hai.py    # Logic xử lý báo cáo hư hại
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py              # Blueprint: trang chủ + báo cáo hư hại (public)
│   │   ├── auth.py              # Blueprint: đăng nhập, đăng ký, đăng xuất
│   │   ├── mua_sam.py           # Blueprint: M08 bộ phận mua sắm
│   │   ├── ke_toan.py           # Blueprint: M08 kế toán
│   │   ├── tai_san.py           # Blueprint: M09 kho & tài sản
│   │   └── admin.py             # Blueprint: admin dashboard (M17 + quản lý)
│   ├── templates/
│   │   ├── base.html            # Layout chung với navbar (điều chỉnh theo vai trò)
│   │   ├── main/
│   │   │   ├── trang_chu.html   # Trang chủ public
│   │   │   ├── bao_cao_hu_hai.html  # Form báo cáo hư hại
│   │   │   └── cam_on.html      # Xác nhận gửi báo cáo thành công
│   │   ├── auth/
│   │   │   ├── dang_nhap.html   # Form đăng nhập
│   │   │   └── dang_ky.html     # Form đăng ký
│   │   ├── mua_sam/             # Templates M08 (bộ phận mua sắm)
│   │   ├── ke_toan/             # Templates M08 (kế toán)
│   │   ├── tai_san/             # Templates M09
│   │   └── admin/               # Templates admin + M17 dashboard
│   └── static/
│       ├── css/
│       ├── js/
│       └── img/
├── scripts/
│   └── du_lieu_mau.py           # Nạp dữ liệu mẫu vào CSDL
├── tests/
│   ├── conftest.py              # Fixtures pytest dùng chung
│   ├── test_auth.py             # Kiểm thử đăng nhập, phân quyền
│   ├── test_mua_sam.py          # Kiểm thử M08
│   ├── test_ke_toan.py          # Kiểm thử thanh toán (M08)
│   ├── test_tai_san.py          # Kiểm thử M09
│   ├── test_bao_cao.py          # Kiểm thử M17
│   └── test_bao_cao_hu_hai.py   # Kiểm thử form báo cáo hư hại
├── .env.example                 # Mẫu biến môi trường
├── requirements.txt
├── run.py                       # Entry point khởi động server
└── AGENTS.md                    # File này
```

---

## 5. Các module nghiệp vụ chính

### M08 — Mua sắm và thanh toán

**Mô tả:** Quản lý toàn bộ vòng đời của một đề nghị mua sắm, từ lúc lập đến khi thanh toán hoàn tất.

**Luồng nghiệp vụ:**
```
[Lập đề nghị] → [Gửi phê duyệt] → [Lãnh đạo phê duyệt/từ chối]
    → [Tạo hồ sơ mua sắm] → [Tiếp nhận hàng hóa] → [Theo dõi thanh toán]
```

**Các chức năng cần cài đặt:**

| Chức năng | Mô tả | Vai trò được phép |
|---|---|---|
| Lập đề nghị mua sắm | Tạo mới yêu cầu mua sắm với danh mục hàng hóa, số lượng, đơn vị đề nghị | `mua_sam`, `quan_tri` |
| Theo dõi luồng phê duyệt | Xem trạng thái đề nghị đang ở bước nào | `mua_sam`, `lanh_dao`, `quan_tri` |
| Phê duyệt / Từ chối | Lãnh đạo xem xét và ra quyết định kèm ghi chú | `lanh_dao`, `quan_tri` |
| Quản lý hồ sơ mua sắm | Lưu trữ hợp đồng, báo giá, nhà cung cấp | `mua_sam`, `quan_tri` |
| Ghi nhận tiếp nhận hàng | Xác nhận hàng hóa đã nhập kho, số lượng thực nhận | `mua_sam`, `quan_tri` |
| Theo dõi thanh toán | Ghi nhận trạng thái thanh toán, hóa đơn | `ke_toan`, `quan_tri` |

**Trạng thái đề nghị mua sắm:**
- `cho_phe_duyet` — Chờ phê duyệt
- `da_phe_duyet` — Đã phê duyệt
- `tu_choi` — Từ chối
- `dang_mua` — Đang mua sắm
- `da_nhan` — Đã tiếp nhận hàng
- `hoan_tat` — Hoàn tất (đã thanh toán)

---

### M09 — Quản lý tài sản

**Mô tả:** Theo dõi vòng đời tài sản từ khi tiếp nhận đến khi thanh lý.

**Luồng nghiệp vụ:**
```
[Tiếp nhận từ M08] → [Cấp mã tài sản] → [Bàn giao đơn vị]
    → [Theo dõi bảo trì/sửa chữa] → [Kiểm kê định kỳ] → [Thanh lý/Xóa sổ]
```

**Các chức năng cần cài đặt:**

| Chức năng | Mô tả | Vai trò được phép |
|---|---|---|
| Tiếp nhận & cấp mã tài sản | Tự động sinh mã tài sản theo quy tắc định sẵn | `mua_sam`, `quan_tri` |
| Quản lý thông tin tài sản | CRUD thông tin: tên, mô tả, vị trí, phòng ban, giá trị | `mua_sam`, `quan_tri` |
| Bàn giao tài sản | Ghi nhận việc bàn giao tài sản cho đơn vị/cá nhân sử dụng | `mua_sam`, `quan_tri` |
| Lịch sử bảo trì/sửa chữa | Ghi nhận các lần bảo trì, chi phí, đơn vị thực hiện | `mua_sam`, `quan_tri` |
| Kiểm kê tài sản | Tạo và xác nhận phiếu kiểm kê định kỳ | `mua_sam`, `quan_tri` |
| Xem tài sản được bàn giao | Người dùng nội bộ xem tài sản do họ đang sử dụng | `nguoi_dung`, `mua_sam`, `quan_tri` |

**Trạng thái tài sản:**
- `cho_ban_giao` — Chưa bàn giao (trong kho)
- `dang_su_dung` — Đang sử dụng
- `dang_sua_chua` — Đang sửa chữa/bảo trì
- `cho_thanh_ly` — Chờ thanh lý
- `da_thanh_ly` — Đã thanh lý

---

### M17 — Dashboard, báo cáo và đánh giá

**Mô tả:** Tổng hợp, trực quan hóa số liệu từ M08 và M09 để hỗ trợ ra quyết định.

**Các chức năng cần cài đặt:**

| Chức năng | Mô tả | Vai trò được phép |
|---|---|---|
| Dashboard tổng quan | Thống kê nhanh: số đề nghị chờ duyệt, tài sản đang sử dụng, chi tiêu tháng này | `lanh_dao`, `mua_sam`, `quan_tri` |
| Báo cáo mua sắm | Tổng hợp đề nghị theo kỳ, trạng thái, đơn vị đề nghị | `lanh_dao`, `mua_sam`, `quan_tri` |
| Báo cáo tài sản | Danh sách tài sản theo tình trạng, phòng ban, loại tài sản | `lanh_dao`, `mua_sam`, `quan_tri` |
| Biểu đồ trực quan | Biểu đồ cột/tròn hiển thị tình hình mua sắm, tình trạng tài sản | `lanh_dao`, `mua_sam`, `quan_tri` |
| Xuất báo cáo | Xuất dữ liệu ra file CSV hoặc in trực tiếp từ trình duyệt | `lanh_dao`, `mua_sam`, `quan_tri` |

---

## 6. Quy ước lập trình bắt buộc

### 6.1 Phân tách trách nhiệm (Separation of Concerns)

> ⚠️ **Quy tắc cứng — Agent không được vi phạm:**

- **`routes/`** — Chỉ được: nhận HTTP request, đọc tham số, gọi service, trả về response (HTML hoặc JSON).  
  **Không được:** viết câu lệnh SQL, xử lý logic nghiệp vụ phức tạp.

- **`services/`** — Nơi chứa toàn bộ logic nghiệp vụ: tính toán, kiểm tra điều kiện, gọi `db.py`, gọi `clock.now()`.

- **`db.py`** — Chỉ xử lý kết nối, khởi tạo bảng và cung cấp hàm tiện ích truy vấn cơ sở dữ liệu.

- **`templates/`** — Chỉ xử lý trình bày dữ liệu. Không có logic nghiệp vụ trong template.

### 6.2 Xử lý thời gian — `clock.py`

```python
# app/clock.py
import os
from datetime import datetime, timezone

def now() -> datetime:
    """
    Trả về thời điểm hiện tại.
    Nếu biến môi trường CSV_GIO được đặt (ISO 8601), dùng giá trị đó để hỗ trợ mock time khi test.
    """
    gio_mock = os.environ.get("CSV_GIO")
    if gio_mock:
        return datetime.fromisoformat(gio_mock)
    return datetime.now(timezone.utc)
```

> **Bắt buộc:** Mọi chỗ lấy thời gian hiện tại trong `services/` đều phải dùng `clock.now()`, **không dùng** `datetime.now()` hay `time.time()` trực tiếp.

### 6.3 Kết nối CSDL — `db.py`

```python
# app/db.py
import os, sqlite3
from flask import g

DB_PATH = os.environ.get("CSV_DB", "csvc.db")

def get_db():
    """Lấy kết nối SQLite từ Flask application context."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Khởi tạo toàn bộ bảng nếu chưa tồn tại."""
    db = get_db()
    # Đọc và thực thi schema.sql
    ...
```

> **Bắt buộc:** Đường dẫn CSDL luôn lấy từ biến môi trường `CSV_DB`, mặc định là `csvc.db`.

### 6.4 Xử lý lỗi — `errors.py`

Mọi lỗi nghiệp vụ phải trả về JSON theo cấu trúc sau:

```json
{
  "loi": "MA_LOI_VIET_HOA_KHONG_DAU",
  "thong_bao": "Câu thông báo lỗi bằng tiếng Việt đầy đủ dấu."
}
```

**Ví dụ mã lỗi:**

| Mã lỗi | Thông báo |
|---|---|
| `DE_NGHI_KHONG_TON_TAI` | Đề nghị mua sắm không tồn tại trong hệ thống. |
| `KHONG_DU_QUYEN` | Bạn không có quyền thực hiện thao tác này. |
| `TAI_SAN_KHONG_TON_TAI` | Tài sản không tồn tại trong hệ thống. |
| `TRANG_THAI_KHONG_HOP_LE` | Trạng thái hiện tại không cho phép thực hiện thao tác này. |
| `DU_LIEU_DAU_VAO_KHONG_HOP_LE` | Dữ liệu đầu vào không hợp lệ, vui lòng kiểm tra lại. |
| `CHUA_DANG_NHAP` | Vui lòng đăng nhập để tiếp tục. |
| `TAI_KHOAN_KHONG_TON_TAI` | Tài khoản không tồn tại hoặc mật khẩu sai. |

### 6.5 Xác thực dữ liệu — `schemas.py`

- Mọi dữ liệu nhận từ form hoặc JSON body phải được xác thực trong `schemas.py` trước khi truyền vào service.
- Trả về lỗi `DU_LIEU_DAU_VAO_KHONG_HOP_LE` nếu xác thực thất bại.
- Không để dữ liệu chưa được xác thực đi vào lớp service.
- **Form báo cáo hư hại** phải được xác thực qua schema riêng dù là public route.

### 6.6 Quy tắc chung

- **Không dùng thư viện AI** hay bất kỳ thư viện bên ngoài nào không có trong `requirements.txt`.
- **Ưu tiên tính đúng đắn dữ liệu** — đặc biệt đảm bảo tính toàn vẹn liên module (tài sản phát sinh từ M08 phải khớp với M09; số liệu M17 phải phản ánh đúng M08 và M09).
- **Không hardcode** đường dẫn file, cổng server hay thông tin nhạy cảm vào source code. Dùng biến môi trường hoặc file cấu hình.
- Mọi hàm trong `services/` phải có **docstring tiếng Việt** mô tả chức năng, tham số và giá trị trả về.

---

## 7. Biến môi trường

| Tên biến | Mô tả | Giá trị mặc định |
|---|---|---|
| `CSV_DB` | Đường dẫn tới file CSDL SQLite | `csvc.db` |
| `CSV_GIO` | Thời gian giả lập (ISO 8601) để mock khi test | _(không đặt)_ |
| `FLASK_ENV` | Môi trường chạy Flask (`development` / `production`) | `development` |
| `SECRET_KEY` | Khóa bí mật cho Flask session | _(bắt buộc đặt trong production)_ |

> Tạo file `.env` từ `.env.example` và **không commit** file `.env` vào git.

---

## 8. Hướng dẫn lệnh (Commands)

### 8.1 Cài đặt môi trường

```bash
# Tạo và kích hoạt môi trường ảo
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 8.2 Cấu hình biến môi trường

```bash
# Sao chép file mẫu
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS

# Chỉnh sửa .env theo môi trường của bạn
```

### 8.3 Khởi tạo CSDL và nạp dữ liệu mẫu

```bash
# Khởi tạo bảng và nạp dữ liệu mẫu (bao gồm tài khoản admin mặc định)
python scripts/du_lieu_mau.py
```

> Tài khoản admin mặc định được tạo bởi script: `admin` / `admin123` — **đổi ngay sau khi chạy lần đầu**.

### 8.4 Chạy server phát triển

```bash
# Cách 1: Dùng run.py
python run.py

# Cách 2: Dùng Flask CLI
set FLASK_APP=app          # Windows
export FLASK_APP=app       # Linux/macOS
flask run --debug
```

Server sẽ chạy tại: `http://127.0.0.1:5000`

### 8.5 Chạy kiểm thử tự động

```bash
# Chạy toàn bộ test suite
pytest

# Chạy với output chi tiết
pytest -v

# Chạy test của một module cụ thể
pytest tests/test_auth.py -v
pytest tests/test_mua_sam.py -v
pytest tests/test_tai_san.py -v
pytest tests/test_bao_cao.py -v
pytest tests/test_bao_cao_hu_hai.py -v

# Chạy test với mock thời gian
CSV_GIO="2025-01-15T08:00:00" pytest -v
```

---

## 9. Hướng dẫn viết kiểm thử (pytest)

### Nguyên tắc

- Mỗi module nghiệp vụ có file test riêng trong `tests/`.
- Test phải **độc lập**: mỗi test tạo CSDL riêng trong bộ nhớ (`":memory:"`), không chia sẻ trạng thái giữa các test.
- Dùng `CSV_GIO` để kiểm soát thời gian trong test — **không dùng** `time.sleep()` hay `datetime.now()` trực tiếp trong test.
- Đặt tên hàm test theo mẫu: `test_<ten_chuc_nang>_<kich_ban>`.

### Ví dụ cấu trúc test

```python
# tests/test_auth.py

def test_dang_nhap_thanh_cong_redirect_dung_trang(client):
    """Test đăng nhập thành công redirect đúng theo vai trò."""
    response = client.post("/dang-nhap", data={
        "ten_dang_nhap": "user_mua_sam",
        "mat_khau": "password123"
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith("/mua-sam/")

def test_truy_cap_trang_bao_ve_chua_dang_nhap(client):
    """Test truy cập trang bảo vệ khi chưa đăng nhập → redirect về đăng nhập."""
    response = client.get("/mua-sam/", follow_redirects=False)
    assert response.status_code == 302
    assert "/dang-nhap" in response.location

def test_bao_cao_hu_hai_khong_can_dang_nhap(client):
    """Test form báo cáo hư hại truy cập được mà không cần đăng nhập."""
    response = client.get("/bao-cao-hu-hai")
    assert response.status_code == 200

def test_phe_duyet_de_nghi_khong_du_quyen(client, auth):
    """Test người dùng không phải lãnh đạo không được phê duyệt."""
    auth.login(vai_tro="mua_sam")
    response = client.post("/mua-sam/de-nghi/1/phe-duyet")
    assert response.status_code == 403
    assert response.json["loi"] == "KHONG_DU_QUYEN"
```

---

## 10. Tích hợp dữ liệu liên module

> Agent phải đảm bảo tính toàn vẹn dữ liệu giữa các module theo sơ đồ sau:

```
[Form báo cáo hư hại] (Public)
    │
    │  Gửi thông tin → lưu vào bảng bao_cao_hu_hai
    ▼
M09 (Quản lý tài sản) ← Admin xem xét báo cáo hư hại
    ▲
    │
M08 (Mua sắm)
    │
    │  Khi đề nghị mua sắm chuyển sang trạng thái "da_nhan"
    │  → Tự động tạo bản ghi tài sản trong M09
    ▼
M09 (Quản lý tài sản)
    │
    │  Cung cấp dữ liệu tài sản (số lượng, tình trạng, giá trị)
    ▼
M17 (Dashboard & Báo cáo) — hiển thị tại /admin/
    ▲
    │  Đọc dữ liệu tổng hợp từ cả M08 và M09
    │  để tính toán chỉ số và vẽ biểu đồ
```

**Quy tắc tích hợp bắt buộc:**

1. Khi hàng hóa từ M08 được tiếp nhận (`da_nhan`), service của M09 phải được gọi để tạo tài sản mới với mã tự động.
2. Số liệu trên Dashboard (M17) phải truy vấn trực tiếp từ bảng tài sản và đề nghị — không được lưu cache cứng.
3. Nếu một đề nghị bị từ chối hoặc xóa, không được tạo tài sản liên quan.
4. Báo cáo hư hại từ form public được hiển thị trong trang Admin để bộ phận quản lý xử lý.

---

## 11. Checklist trước khi commit

Agent phải tự kiểm tra danh sách sau trước khi hoàn tất bất kỳ thay đổi nào:

- [ ] Router không chứa câu lệnh SQL hoặc logic nghiệp vụ phức tạp.
- [ ] Mọi hàm lấy thời gian đều dùng `clock.now()`.
- [ ] Đường dẫn CSDL lấy từ biến môi trường `CSV_DB`.
- [ ] Lỗi nghiệp vụ trả về đúng định dạng `{"loi": ..., "thong_bao": ...}`.
- [ ] Dữ liệu đầu vào được xác thực qua `schemas.py` — **kể cả form public báo cáo hư hại**.
- [ ] Các route bảo vệ đã kiểm tra `session["vai_tro"]` và redirect/403 đúng.
- [ ] Route public (`/`, `/bao-cao-hu-hai`, `/dang-nhap`, `/dang-ky`) **không yêu cầu** đăng nhập.
- [ ] Redirect sau đăng nhập đúng theo vai trò (`mua_sam`→`/mua-sam/`, `ke_toan`→`/ke-toan/`, v.v.).
- [ ] Có docstring tiếng Việt cho mọi hàm service mới.
- [ ] Có ít nhất một test case cho chức năng mới.
- [ ] Tất cả các test hiện có vẫn pass: `pytest -v`.
- [ ] Không có thông tin nhạy cảm (mật khẩu, secret key) hardcode trong source code.
- [ ] Dữ liệu liên module (M08 → M09 → M17) nhất quán và đúng đắn.
