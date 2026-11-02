# AGENTS.md — Hướng dẫn cho AI Agent

> Tài liệu này mô tả toàn bộ quy ước, kiến trúc và hướng dẫn hành vi dành cho AI Agent khi làm việc trong dự án **Website Quản lý Cơ sở Vật chất**.  
> Agent **phải đọc và tuân thủ** toàn bộ nội dung trong file này trước khi thực hiện bất kỳ thay đổi nào.

---

## 1. Tổng quan dự án

| Mục | Nội dung |
|---|---|
| **Tên đề tài** | Xây dựng Website Quản lý Cơ sở Vật chất |
| **Mục tiêu** | Số hóa quy trình mua sắm, tiếp nhận, quản lý tài sản và tổng hợp báo cáo tại trường đại học |
| **Công nghệ** | Python (Flask), HTML, CSS, JavaScript (Bootstrap 5, Chart.js), SQLite (sqlite3), Jinja2, pytest |
| **Giao diện nhận diện** | Thiết kế theo form mẫu & nhận diện thương hiệu của **Trường Đại học Kinh tế Quốc dân (NEU)**: tông màu xanh Navy (`#002D62`), xanh dương (`#0B4F9C`), đỏ điểm nhấn (`#C41230`), vàng kim (`#F5A623`), font Source Sans Pro / Roboto, logo NEU chính thức |
| **Ngôn ngữ giao diện** | Tiếng Việt |
| **Ngôn ngữ code** | Tiếng Việt cho tên biến nghiệp vụ, tên bảng CSDL, thông báo lỗi; tiếng Anh cho tên hàm kỹ thuật và cú pháp |

### Mục tiêu nghiệp vụ

- Nghiên cứu, phân tích quy trình quản lý cơ sở vật chất từ khâu **đề xuất mua sắm → tiếp nhận hàng hóa → nhập kho & quản lý tài sản → tổng hợp báo cáo**.
- Số hóa quy trình mua sắm và quản lý tài sản tập trung, minh bạch, chính xác.
- Giảm thiểu sai sót thủ công, tiết kiệm thời gian xử lý hồ sơ.
- Hỗ trợ lãnh đạo và các phòng ban chuyên trách ra quyết định dựa trên dữ liệu thực tế.

---

## 2. Đối tượng người dùng và phân quyền

Hệ thống được thiết kế chuyên biệt cho 4 nhóm người dùng nội bộ và công chúng (không có tài khoản người dùng nội bộ thông thường):

| Vai trò | Mã vai trò | Quyền hạn và phạm vi truy cập |
|---|---|---|
| **Bộ phận Mua sắm** | `mua_sam` | Quản lý đề nghị mua sắm, lập đề nghị mới, tạo hồ sơ mua sắm (M08 - `/mua-sam/`); Trưởng BP Mua sắm duyệt các đề nghị < 100 triệu. |
| **Bộ phận Quản lý tài sản** | `quan_ly_kho` | Quản lý toàn bộ vòng đời tài sản (M09 - `/tai-san/`); Tiếp nhận hàng hóa vào kho (`/mua-sam/de-nghi/<id>/tiep-nhan`); Tiếp nhận phản ánh hư hại công khai, xác minh hiện trường, lập phương án sửa chữa hoặc đề xuất mua sắm thay thế chuyển M08 (`/tai-san/bao-cao-hu-hai`). |
| **Kế toán** | `ke_toan` | Quản lý hóa đơn và ghi nhận thanh toán các đề nghị mua sắm đã tiếp nhận hàng (M08 - `/ke-toan/`). |
| **Quản trị viên (Admin)** | `quan_tri` | **Admin chỉ có quyền duyệt và giám sát**: Phê duyệt/từ chối các đề nghị mua sắm (bắt buộc duyệt các gói ≥ 100 triệu), quản lý tài khoản người dùng (`/admin/tai-khoan`); **Đối với các phân hệ khác (M08, M09, Kế toán, Báo cáo hư hại), Admin chỉ có quyền xem (giám sát), không thực hiện tác nghiệp thay các bộ phận**. |
| **Công chúng / Bất kỳ ai** | _(không có)_ | Truy cập trang chủ (`/`), gửi báo cáo sự cố hư hại vật chất (`/bao-cao-hu-hai`) mà không cần đăng nhập, đăng nhập (`/dang-nhap`), đăng ký tài khoản (`/dang-ky`). |

> **Quy tắc phân quyền:**
> 1. **Loại bỏ hoàn toàn người dùng nội bộ thông thường (`nguoi_dung`)**: Giảng viên, sinh viên, cán bộ hay khách khi phát hiện hỏng hóc cơ sở vật chất chỉ cần vào trang công khai `/bao-cao-hu-hai` gửi thông tin mà không cần tài khoản.
> 2. **Tách biệt rõ ràng 2 bộ phận**:
>    - `mua_sam`: Chuyên trách lập, theo dõi hồ sơ mua sắm và duyệt đơn < 100 triệu.
>    - `quan_ly_kho`: Chuyên trách kiểm tra hàng, nhập kho, cấp mã tài sản, xử lý phản ánh hư hại hiện trường và lập đề xuất thay thế.
> 3. **Nguyên tắc quyền hạn Admin (Lãnh đạo)**: Admin chỉ có quyền duyệt đề nghị mua sắm (gói ≥ 100 triệu) và quản lý tài khoản người dùng; tất cả các tính năng nghiệp vụ khác (nhập hàng, bàn giao tài sản, thanh toán, sửa chữa) Admin chỉ có quyền xem.
> 4. Mọi route có bảo vệ phải kiểm tra `session["vai_tro"]`. Nếu chưa đăng nhập → redirect về `/dang-nhap`. Nếu không đủ quyền → trả về mã HTTP 403 kèm thông báo tiếng Việt rõ ràng.

---

## 3. Kiến trúc trang (Pages Architecture)

### 3.1 Tổng quan các trang

| # | Tên trang | URL | Quyền truy cập | Blueprint |
|---|---|---|---|---|
| 1 | Trang chủ | `/` | Công khai (Public) | `main` |
| 2 | Báo cáo hư hại | `/bao-cao-hu-hai` | Công khai (Không cần tài khoản) | `main` |
| 3 | Đăng nhập / Đăng ký | `/dang-nhap`, `/dang-ky` | Công khai (Khách) | `auth` |
| 4 | M08 — Mua sắm | `/mua-sam/` | `mua_sam`, `quan_ly_kho` (xem/tiếp nhận), `quan_tri` | `mua_sam` |
| 5 | M08 — Kế toán | `/ke-toan/` | `ke_toan`, `quan_tri` | `ke_toan` |
| 6 | M09 — Quản lý tài sản | `/tai-san/` | `quan_ly_kho`, `quan_tri` | `tai_san` |
| 7 | Admin Dashboard | `/admin/` | `quan_tri` | `admin` |

---

### 3.2 Trang chủ (`/`)

**Mục đích:** Giới thiệu hệ thống quản lý cơ sở vật chất theo nhận diện NEU, điều hướng trực quan đến các nghiệp vụ.

**Hiển thị:**
- Header thương hiệu: Logo NEU, tên trường Đại học Kinh tế Quốc dân, tên hệ thống.
- Banner giới thiệu quy trình cơ sở vật chất số hóa: Mua sắm → Quản lý tài sản → Kế toán thanh toán → Báo cáo quản trị.
- Nút tác vụ nổi bật:
  - **"Báo cáo hư hại vật chất"** (màu đỏ NEU) → `/bao-cao-hu-hai` (Chỉ hiển thị trên Trang chủ khi **chưa đăng nhập**; sau khi người dùng đăng nhập thì ẩn/xóa toàn bộ nút báo cáo hư hại).
  - **"Đăng nhập hệ thống"** (màu xanh Navy) → `/dang-nhap` (Dành cho cán bộ các phòng ban).
  - **"Đăng ký tài khoản"** → `/dang-ky`.

**Template:** `templates/main/trang_chu.html`  
**Route:** `GET /`

---

### 3.3 Trang Đăng nhập / Đăng ký (`/dang-nhap`, `/dang-ky`)

#### Đăng nhập (`/dang-nhap`)
- Form nhập: tên đăng nhập, mật khẩu.
- Sau khi xác thực thành công → lưu `session["vai_tro"]`, `session["nguoi_dung_id"]`, `session["ho_ten"]`.
- **Chuyển hướng tự động theo vai trò (Redirect on Login):**

```
vai_tro == "mua_sam"     → /mua-sam/   (Trang làm việc Mua sắm)
vai_tro == "quan_ly_kho" → /tai-san/   (Trang Quản lý tài sản)
vai_tro == "ke_toan"     → /ke-toan/   (Trang thanh toán Kế toán)
vai_tro == "quan_tri"    → /admin/     (Admin Dashboard tổng hợp)
```

- Nếu sai thông tin → hiển thị thông báo lỗi tiếng Việt tại trang đăng nhập.
- Nếu đã đăng nhập → tự động chuyển tiếp tới trang làm việc tương ứng (không bắt đăng nhập lại).

#### Đăng ký (`/dang-ky`)
- Form nhập: họ tên, email, tên đăng nhập, mật khẩu, xác nhận mật khẩu, và **đơn vị / bộ phận công tác**:
  - `mua_sam`: Bộ phận Mua sắm
  - `quan_ly_kho`: Bộ phận Quản lý tài sản
  - `ke_toan`: Kế toán
- Sau khi đăng ký thành công → chuyển về `/dang-nhap` kèm thông báo thành công.
- Admin có thể thay đổi hoặc phân quyền lại vai trò tại `/admin/tai-khoan`.

---

### 3.4 Trang M08 — Mua sắm (`/mua-sam/`)

**Mục đích:** Quản lý toàn bộ quy trình lập đề nghị mua sắm, hồ sơ đấu thầu/chào hàng và tiếp nhận hàng hóa về kho.

**Phân quyền chi tiết:**
- `mua_sam`: Lập đề nghị mua sắm, quản lý hồ sơ, xem chi tiết; **Trưởng BP Mua sắm có thẩm quyền phê duyệt các đề nghị có kinh phí dưới 100 triệu đồng**.
- `quan_ly_kho`: Được quyền xem danh sách đề nghị đã duyệt và **chuyên trách thực hiện tiếp nhận hàng hóa vào kho M09**.
- `quan_tri`: Có quyền **Phê duyệt** hoặc **Từ chối** đề nghị mua sắm (bắt buộc phê duyệt các đề nghị từ 100 triệu đồng trở lên); các thao tác khác chỉ xem.

**Các endpoint chính:**

| URL | Chức năng | Vai trò được phép |
|---|---|---|
| `GET /mua-sam/` | Danh sách đề nghị mua sắm | `mua_sam`, `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `GET/POST /mua-sam/de-nghi/tao` | Lập phiếu đề nghị mua sắm mới | `mua_sam`, `quan_ly_kho` |
| `GET /mua-sam/de-nghi/<id>` | Xem chi tiết đề nghị & danh mục vật tư | `mua_sam`, `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `POST /mua-sam/de-nghi/<id>/phe-duyet` | Phê duyệt đề nghị (<100tr: BP Mua sắm / Admin; ≥100tr: Lãnh đạo Admin) | `mua_sam`, `quan_tri` |
| `POST /mua-sam/de-nghi/<id>/tu-choi` | Từ chối đề nghị kèm lý do | `mua_sam`, `quan_tri` |
| `GET/POST /mua-sam/de-nghi/<id>/tiep-nhan` | Ghi nhận tiếp nhận hàng hóa (nhập kho M09) | `quan_ly_kho` (Admin không làm thay) |
| `GET /mua-sam/ho-so` | Danh mục hồ sơ mua sắm (hợp đồng, báo giá) | `mua_sam`, `quan_tri` (chỉ xem) |

**Trạng thái đề nghị mua sắm:**
- `cho_phe_duyet` — Chờ phê duyệt (< 100 triệu)
- `cho_lanh_dao_duyet` — Chờ Lãnh đạo phê duyệt (≥ 100 triệu)
- `da_phe_duyet` — Đã phê duyệt (chờ giao hàng/nhập kho)
- `tu_choi` — Từ chối
- `dang_mua` — Đang triển khai mua sắm
- `da_nhan` — Đã tiếp nhận hàng *(hệ thống tự động sinh tài sản vào kho M09)*
- `hoan_tat` — Hoàn tất (đã thanh toán xong)

---

### 3.5 Trang M08 — Kế toán (`/ke-toan/`)

**Mục đích:** Kiểm soát chi phí, hóa đơn chứng từ và ghi nhận thanh toán các đề nghị mua sắm đã được bộ phận quản lý tài sản tiếp nhận đầy đủ.

**Vai trò được phép:** `ke_toan` (tác nghiệp), `quan_tri` (chỉ xem)

**Các endpoint chính:**

| URL | Chức năng | Vai trò được phép |
|---|---|---|
| `GET /ke-toan/` | Danh sách đề nghị đã tiếp nhận, chờ thanh toán | `ke_toan`, `quan_tri` (chỉ xem) |
| `GET /ke-toan/de-nghi/<id>` | Chi tiết thanh toán, vật tư, hóa đơn chứng từ | `ke_toan`, `quan_tri` (chỉ xem) |
| `POST /ke-toan/de-nghi/<id>/thanh-toan` | Xác nhận đã thanh toán giải ngân | `ke_toan` (Admin không thanh toán thay) |
| `GET /ke-toan/lich-su` | Lịch sử giải ngân & thanh toán theo kỳ | `ke_toan`, `quan_tri` (chỉ xem) |

---

### 3.6 Trang M09 — Quản lý tài sản (`/tai-san/`)

**Mục đích:** Quản lý tài sản trường học từ lúc nhập kho, cấp phát mã định danh, bàn giao phòng ban, tiếp nhận xử lý hư hại, theo dõi bảo trì, kiểm kê định kỳ đến thanh lý theo `Yêu cầu 1.docx`.

**Vai trò được phép:** `quan_ly_kho` (chuyên trách tác nghiệp), `quan_tri` (chỉ xem giám sát)

**Các endpoint chính:**

| URL | Chức năng | Vai trò được phép |
|---|---|---|
| `GET /tai-san/` | Danh sách tài sản & trang thiết bị toàn trường | `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `GET /tai-san/<id>` | Chi tiết tài sản, lịch sử bàn giao & bảo trì | `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `GET/POST /tai-san/<id>/chinh-sua` | Cập nhật thông tin tài sản | `quan_ly_kho` |
| `POST /tai-san/<id>/ban-giao` | Bàn giao tài sản cho đơn vị / phòng học / giảng đường | `quan_ly_kho` |
| `GET/POST /tai-san/<id>/bao-tri` | Ghi nhận sự vụ bảo trì, sửa chữa, thay thế | `quan_ly_kho` |
| `GET /tai-san/kiem-ke` | Danh sách các đợt kiểm kê tài sản | `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `POST /tai-san/kiem-ke/tao` | Tạo phiếu kiểm kê định kỳ mới | `quan_ly_kho` |
| `GET /tai-san/bao-cao-hu-hai` | Tiếp nhận và theo dõi phản ánh hư hại từ công chúng | `quan_ly_kho`, `quan_tri` (chỉ xem) |
| `POST /tai-san/bao-cao-hu-hai/<id>/xu-ly` | Xác minh hiện trường, chọn phương án Sửa chữa hoặc Thay thế | `quan_ly_kho` |
| `POST /tai-san/bao-cao-hu-hai/<id>/tao-mua-sam` | Lập yêu cầu mua sắm thay thế chuyển sang M08 | `quan_ly_kho` |

**Trạng thái tài sản:**
- `cho_ban_giao` — Trong kho, chưa bàn giao
- `dang_su_dung` — Đang sử dụng tại phòng học/khoa/viện
- `dang_sua_chua` — Đang bảo dưỡng/sửa chữa
- `cho_thanh_ly` — Chờ thanh lý
- `da_thanh_ly` — Đã thanh lý, loại khỏi sổ tài sản

---

### 3.7 Trang Báo cáo hư hại vật chất (`/bao-cao-hu-hai`)

**Mục đích:** Kênh tiếp nhận phản ánh công khai dành cho tất cả mọi người (sinh viên, giảng viên, nhân viên, khách) khi phát hiện hỏng hóc, sự cố về bàn ghế, máy chiếu, điều hòa, bóng đèn, cửa, thiết bị vệ sinh...

**Quyền truy cập:** **Công khai — Không cần tài khoản**

**Dữ liệu tiếp nhận:**
- Họ và tên người gửi *(bắt buộc)*
- Số điện thoại hoặc email liên lạc *(bắt buộc)*
- Vị trí sự cố (Tòa nhà, số phòng, khu vực giảng đường...) *(bắt buộc)*
- Tên thiết bị / vật tư hư hại *(bắt buộc)*
- Mức độ ảnh hưởng: Nhẹ / Trung bình / Nghiêm trọng *(bắt buộc)*
- Mô tả chi tiết hiện trạng sự cố *(tùy chọn)*

> **Luồng xử lý (theo Yêu cầu 1.docx):**
> 1. Dữ liệu sau khi gửi được lưu trữ tập trung.
> 2. **Bộ phận Quản lý tài sản (M09)** tiếp nhận, trực tiếp kiểm tra xác minh tại hiện trường:
>    - Nếu khắc phục được: Tạo phiếu bảo trì/sửa chữa (`dang_sua_chua`).
>    - Nếu không thể sửa: Lập biên bản đánh giá hư hỏng (`can_thay_the`) & tạo yêu cầu mua sắm thay thế chuyển sang phân hệ M08.
> 3. **Admin**: Giám sát tiến độ xử lý hư hại toàn trường qua `/admin/bao-cao-hu-hai` (chỉ xem, không tác nghiệp thay bộ phận tài sản).

---

### 3.8 Trang Admin Dashboard (`/admin/`)

**Mục đích:** Trung tâm điều hành dành riêng cho Quản trị viên (`quan_tri`), tích hợp giám sát module M08, M09, M17, ra quyết định phê duyệt và quản lý tài khoản. **Nguyên tắc cốt lõi: Admin chỉ có quyền duyệt và giám sát, không làm thay chức năng tác nghiệp của các bộ phận chuyên môn.**

**Các endpoint chính:**

| URL | Chức năng | Vai trò |
|---|---|---|
| `GET /admin/` | Dashboard M17: Thẻ KPI, biểu đồ Chart.js thống kê tài sản, mua sắm | `quan_tri` |
| `GET /admin/mua-sam` | Trung tâm duyệt mua sắm: Xem, phê duyệt, từ chối đề nghị | `quan_tri` |
| `GET /admin/tai-san` | Giám sát toàn bộ tài sản và trạng thái kho M09 (chỉ xem) | `quan_tri` |
| `GET /admin/bao-cao` | Tổng hợp báo cáo, xuất dữ liệu CSV | `quan_tri` |
| `GET /admin/bao-cao-hu-hai` | Giám sát tiến độ xử lý phản ánh hư hại từ người dùng (chỉ xem) | `quan_tri` |
| `GET /admin/tai-khoan` | Quản trị người dùng, thay đổi vai trò phân quyền | `quan_tri` |
| `POST /admin/tai-khoan/<id>/doi-vai-tro` | Cập nhật vai trò cho tài khoản | `quan_tri` |

---

### 3.9 Sơ đồ phân quyền tổng thể

```
Người dùng truy cập URL
        │
        ├─ URL Công khai (/, /bao-cao-hu-hai, /dang-nhap, /dang-ky)
        │       └─ Cho phép truy cập trực tiếp
        │
        └─ URL Bảo vệ
                │
                ├─ Chưa đăng nhập?
                │       └─ Chuyển hướng (302) → /dang-nhap
                │
                └─ Đã đăng nhập → Kiểm tra vai_tro trong Session:
                        │
                        ├─ /mua-sam/*   → Yêu cầu: mua_sam | quan_ly_kho (tiếp nhận) | quan_tri
                        ├─ /ke-toan/*   → Yêu cầu: ke_toan | quan_tri
                        ├─ /tai-san/*   → Yêu cầu: quan_ly_kho | quan_tri
                        └─ /admin/*     → Yêu cầu: quan_tri (Admin)
                                │
                                └─ Sai vai trò: Trả về HTTP 403 Forbidden (thông báo lỗi tiếng Việt)
```

---

## 4. Kiến trúc thư mục dự án

```
Web quản lý cơ sở vật chất/
├── app/
│   ├── __init__.py              # Tạo Flask app, đăng ký blueprint, thiết lập context processor
│   ├── db.py                    # Kết nối SQLite (sqlite3.Row), khởi tạo schema tự động
│   ├── clock.py                 # Cung cấp clock.now() hỗ trợ mock thời gian qua CSV_GIO
│   ├── errors.py                # Xử lý ngoại lệ nghiệp vụ và trả lỗi JSON chuẩn
│   ├── schemas.py               # Xác thực dữ liệu đầu vào (Form & JSON)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py              # Đăng nhập, đăng ký, băm mật khẩu sha256
│   │   ├── mua_sam.py           # Nghiệp vụ M08: lập đề nghị, phê duyệt, tiếp nhận hàng
│   │   ├── ke_toan.py           # Nghiệp vụ kế toán: hóa đơn, thanh toán
│   │   ├── tai_san.py           # Nghiệp vụ M09: tài sản, mã định danh, bàn giao, bảo trì
│   │   ├── bao_cao.py           # Nghiệp vụ M17: thống kê dashboard, xuất file CSV
│   │   └── bao_cao_hu_hai.py    # Xử lý tiếp nhận phản ánh hư hại vật chất
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py              # Blueprint main: Trang chủ, Báo cáo hư hại (Public)
│   │   ├── auth.py              # Blueprint auth: Đăng nhập, Đăng ký, Đăng xuất
│   │   ├── mua_sam.py           # Blueprint mua_sam: M08 Mua sắm
│   │   ├── ke_toan.py           # Blueprint ke_toan: M08 Kế toán thanh toán
│   │   ├── tai_san.py           # Blueprint tai_san: M09 Kho & Quản lý tài sản
│   │   └── admin.py             # Blueprint admin: Admin Dashboard & phân quyền
│   ├── templates/
│   │   ├── base.html            # Layout chính với Header & Navbar nhận diện NEU
│   │   ├── main/
│   │   │   ├── trang_chu.html   # Trang chủ NEU Facility Hub
│   │   │   ├── bao_cao_hu_hai.html # Form báo cáo sự cố hư hại
│   │   │   └── cam_on.html      # Xác nhận gửi báo cáo thành công
│   │   ├── auth/
│   │   │   ├── dang_nhap.html   # Giao diện đăng nhập chuẩn NEU
│   │   │   └── dang_ky.html     # Giao diện đăng ký cán bộ đơn vị
│   │   ├── mua_sam/             # Giao diện M08 Mua sắm
│   │   ├── ke_toan/             # Giao diện M08 Kế toán
│   │   ├── tai_san/             # Giao diện M09 Quản lý tài sản
│   │   └── admin/               # Giao diện M17 Admin Dashboard
│   └── static/
│       ├── css/
│       │   └── neu_style.css    # Màu sắc, font chữ, form theo nhận diện NEU
│       └── img/
│           └── neu_logo.webp    # Logo chính thức của NEU
├── scripts/
│   └── du_lieu_mau.py           # Khởi tạo CSDL và tạo 4 tài khoản mẫu chuẩn
├── tests/
│   ├── conftest.py              # Fixtures pytest (client test, bộ nhớ :memory:)
│   ├── test_auth.py             # Kiểm thử xác thực & phân quyền 4 vai trò
│   ├── test_mua_sam.py          # Kiểm thử vòng đời mua sắm M08
│   ├── test_ke_toan.py          # Kiểm thử thanh toán M08
│   ├── test_tai_san.py          # Kiểm thử quản lý tài sản M09
│   ├── test_bao_cao.py          # Kiểm thử dashboard M17 & xuất CSV
│   └── test_bao_cao_hu_hai.py   # Kiểm thử báo cáo hư hại công khai
├── .env.example                 # Mẫu cấu hình môi trường
├── requirements.txt             # Thư viện phụ thuộc (Flask, pytest)
├── run.py                       # File chạy máy chủ web phát triển
├── README.md                    # Hướng dẫn chi tiết cài đặt và sử dụng
└── AGENTS.md                    # Bản đặc tả quy chuẩn này
```

---

## 5. Quy chuẩn kỹ thuật bắt buộc

### 5.1 Phân tách trách nhiệm (Separation of Concerns)

- **`routes/`**: Chỉ tiếp nhận HTTP request, trích xuất dữ liệu, kiểm tra quyền hạn cơ bản, gọi `services/` tương ứng và trả về `render_template` hoặc `redirect`. **Tuyệt đối không viết câu lệnh SQL trong routes**.
- **`services/`**: Nơi thực thi toàn bộ logic nghiệp vụ, tính toán công nợ, sinh mã tài sản tự động, ghi nhận trạng thái và tương tác CSDL qua `db.py`.
- **`db.py`**: Quản lý kết nối SQLite `g.db`, `row_factory = sqlite3.Row`.
- **`clock.py`**: Cung cấp hàm `clock.now()` lấy thời gian thực hoặc giả lập qua biến môi trường `CSV_GIO`. Tất cả các thao tác ghi nhận thời gian trong `services/` **bắt buộc dùng `clock.now()`**.

### 5.2 Xử lý lỗi chuẩn nghiệp vụ (`errors.py`)

Khi có lỗi logic nghiệp vụ, service hoặc route phải trả về cấu trúc thống nhất:
```json
{
  "loi": "MA_LOI_VIET_HOA_KHONG_DAU",
  "thong_bao": "Nội dung giải thích lỗi bằng tiếng Việt có dấu đầy đủ."
}
```

Các mã lỗi quy chuẩn:
- `KHONG_DU_QUYEN`: Người dùng không có thẩm quyền thực hiện thao tác.
- `CHUA_DANG_NHAP`: Yêu cầu đăng nhập trước khi tiếp tục.
- `DE_NGHI_KHONG_TON_TAI`: Phiếu đề nghị mua sắm không tìm thấy.
- `TAI_SAN_KHONG_TON_TAI`: Bản ghi tài sản không tồn tại.
- `TRANG_THAI_KHONG_HOP_LE`: Thao tác không đúng trình tự trạng thái nghiệp vụ.
- `DU_LIEU_DAU_VAO_KHONG_HOP_LE`: Dữ liệu gửi lên không đúng định dạng qua `schemas.py`.

---

## 6. Danh mục tài khoản mẫu kiểm thử

Hệ thống cung cấp sẵn 4 tài khoản mặc định ứng với từng vai trò phục vụ kiểm thử và nghiệm thu:

| Vai trò | Tên đăng nhập | Mật khẩu | Trang chuyển hướng sau đăng nhập |
|---|---|---|---|
| **Quản trị viên (Admin)** | `admin` | `admin123` | `/admin/` |
| **Bộ phận Mua sắm** | `cb_muasam` | `password123` | `/mua-sam/` |
| **Bộ phận Quản lý tài sản** | `cb_kho` | `password123` | `/tai-san/` |
| **Kế toán** | `cb_ketoan` | `password123` | `/ke-toan/` |

---

## 7. Hướng dẫn lệnh (Commands)

### 7.1 Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 7.2 Khởi tạo cơ sở dữ liệu và nạp dữ liệu mẫu
```bash
python scripts/du_lieu_mau.py
```

### 7.3 Chạy ứng dụng web
```bash
python run.py
```
Ứng dụng sẽ khả dụng tại địa chỉ: **`http://127.0.0.1:5000`**

### 7.4 Chạy bộ kiểm thử tự động
```bash
pytest -v
```

---

## 8. Tích hợp dữ liệu liên module (Data Integrity)

1. **Mua sắm → Kho tài sản (M08 → M09):**
   - Khi đề nghị mua sắm chuyển sang trạng thái `da_nhan` (do `quan_ly_kho` hoặc `quan_tri` xác nhận), hàm `tai_san_service.tao_tai_san_tu_de_nghi()` được gọi tự động để sinh mã tài sản mới (định dạng `TS-YYYY-XXXXX`) với trạng thái ban đầu `cho_ban_giao`.
2. **Kho tài sản → Kế toán (M09 → M08 Thanh toán):**
   - Kế toán chỉ được phép ghi nhận thanh toán (`hoan_tat`) cho các đề nghị mua sắm đã có xác nhận tiếp nhận hàng hóa (`da_nhan`).
3. **M08, M09 → M17 Dashboard Admin:**
   - Các chỉ số KPI (tổng giá trị tài sản, số đề nghị chờ duyệt, số sự cố hỏng hóc chưa khắc phục) được tính toán động từ bảng cơ sở dữ liệu tại thời điểm truy vấn.
4. **Báo cáo hư hại công khai → Admin:**
   - Mọi bản ghi gửi từ form `/bao-cao-hu-hai` được lưu vào bảng `bao_cao_hu_hai` với trạng thái `cho_xu_ly` để Quản trị viên theo dõi và điều phối đơn vị bảo trì xử lý.

---

## 9. Checklist kiểm tra cho AI Agent

Mỗi khi thực hiện thay đổi, AI Agent phải kiểm tra và xác nhận:
- [ ] Không có vai trò `nguoi_dung` trong code và logic kiểm tra quyền.
- [ ] Phân định rõ 2 vai trò `mua_sam` và `quan_ly_kho`.
- [ ] Route `/bao-cao-hu-hai` hoàn toàn công khai, không bắt buộc session hay token.
- [ ] Giao diện nhất quán với tông màu và logo nhận diện NEU.
- [ ] Tất cả các route không chứa mã SQL trực tiếp (chỉ gọi `services/`).
- [ ] Thời gian được xử lý tập trung thông qua `clock.now()`.
- [ ] Nút "Báo cáo hư hại" chỉ xuất hiện tại trang chủ khi chưa đăng nhập; sau khi đăng nhập được xóa/ẩn hoàn toàn.
- [ ] Toàn bộ 20 test cases của hệ thống phải vượt qua thành công: `pytest -v`.
