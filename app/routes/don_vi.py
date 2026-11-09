from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import don_vi as dv_svc
from app.services import mua_sam as ms_svc
from app.services import tai_san as ts_svc
from app.routes import yeu_cau_vai_tro
from app import schemas
from app.errors import LoiNghiepVu

don_vi_bp = Blueprint("don_vi", __name__, url_prefix="/don-vi")

def get_current_user_info():
    return {
        "id": session.get("nguoi_dung_id"),
        "ho_ten": session.get("ho_ten", ""),
        "ten_dang_nhap": session.get("ten_dang_nhap", ""),
        "don_vi": session.get("don_vi", "Khoa / Đơn vị"),
        "email": session.get("email", ""),
        "so_dien_thoai": session.get("so_dien_thoai", "")
    }

@don_vi_bp.route("/")
@don_vi_bp.route("/dashboard")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def dashboard():
    """Bảng điều khiển trung tâm dành cho Đơn vị sử dụng."""
    user = get_current_user_info()
    don_vi = user["don_vi"]
    thong_ke = dv_svc.lay_thong_ke_don_vi(don_vi, user["id"])
    
    # Lấy nhanh 5 yêu cầu sửa chữa gần nhất
    ds_sua_chua = dv_svc.lay_danh_sach_sua_chua_don_vi(don_vi, user["id"])[:5]
    # Lấy nhanh 5 đề xuất mua sắm gần nhất
    ds_mua_sam = dv_svc.lay_danh_sach_de_xuat_don_vi(don_vi, user["id"])[:5]
    # Lấy tài sản cần xác nhận bàn giao
    ts_cho_ban_giao = dv_svc.lay_danh_sach_tai_san_don_vi(don_vi, cho_xac_nhan=True)

    return render_template(
        "don_vi/dashboard.html",
        user=user,
        thong_ke=thong_ke,
        sua_chua_list=ds_sua_chua,
        mua_sam_list=ds_mua_sam,
        ts_cho_ban_giao=ts_cho_ban_giao
    )

# =========================================================================
# 1. QUẢN LÝ YÊU CẦU SỬA CHỮA & BÁO CÁO HƯ HẠI (M09)
# =========================================================================

@don_vi_bp.route("/sua-chua")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def danh_sach_sua_chua():
    """Theo dõi danh sách và tiến độ xử lý sửa chữa thiết bị của đơn vị."""
    user = get_current_user_info()
    trang_thai = request.args.get("trang_thai")
    ds = dv_svc.lay_danh_sach_sua_chua_don_vi(user["don_vi"], user["id"], trang_thai=trang_thai)
    return render_template("don_vi/sua_chua_danh_sach.html", sua_chua_list=ds, trang_thai_chon=trang_thai, user=user)

@don_vi_bp.route("/sua-chua/tao", methods=["GET", "POST"])
@yeu_cau_vai_tro("don_vi")
def tao_sua_chua():
    """Lập phiếu báo cáo hư hại / Yêu cầu sửa chữa mới (tự động điền danh tính cán bộ)."""
    user = get_current_user_info()
    
    # Lấy danh sách tài sản của đơn vị để chọn nhanh
    tai_san_list = dv_svc.lay_danh_sach_tai_san_don_vi(user["don_vi"])
    tai_san_id_chon = request.args.get("tai_san_id")

    if request.method == "POST":
        du_lieu_form = {
            "loai_yeu_cau": request.form.get("loai_yeu_cau", "sua_chua_thiet_bi"),
            "tai_san_id": request.form.get("tai_san_id"),
            "ten_vat_chat": request.form.get("ten_vat_chat"),
            "vi_tri": request.form.get("vi_tri"),
            "do_khan_cap": request.form.get("do_khan_cap", "binh_thuong"),
            "muc_do": request.form.get("muc_do", "trung_binh"),
            "thoi_gian_phat_hien": request.form.get("thoi_gian_phat_hien"),
            "mo_ta_chi_tiet": request.form.get("mo_ta_chi_tiet"),
            "hinh_anh": request.form.get("hinh_anh", "")
        }

        try:
            yc = dv_svc.tao_yeu_cau_sua_chua(du_lieu_form, user)
            flash(f"Đã gửi thành công Yêu cầu sửa chữa mã {yc['ma_bao_cao']}! Phòng QTTB sẽ tiến hành khảo sát và xử lý.", "success")
            return redirect(url_for("don_vi.chi_tiet_sua_chua", id=yc["id"]))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template(
        "don_vi/sua_chua_tao.html",
        user=user,
        tai_san_list=tai_san_list,
        tai_san_id_chon=tai_san_id_chon
    )

@don_vi_bp.route("/sua-chua/<int:id>")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def chi_tiet_sua_chua(id):
    """Xem tiến độ xử lý sửa chữa thời gian thực và xác nhận các biên bản."""
    user = get_current_user_info()
    try:
        yc = dv_svc.lay_chi_tiet_sua_chua(id)
        return render_template("don_vi/sua_chua_chi_tiet.html", yc=yc, user=user)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("don_vi.danh_sach_sua_chua"))

@don_vi_bp.route("/sua-chua/<int:id>/xac-nhan-khao-sat", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def xac_nhan_khao_sat(id):
    """Đơn vị ký xác nhận kết quả khảo sát hiện trạng hư hỏng tại chỗ (BM03)."""
    user = get_current_user_info()
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        dv_svc.xac_nhan_khao_sat_sua_chua(id, user["id"], ghi_chu)
        flash("Đã ký xác nhận kết quả khảo sát hiện trạng hư hỏng thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.chi_tiet_sua_chua", id=id))

@don_vi_bp.route("/sua-chua/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def nghiem_thu_sua_chua(id):
    """Đơn vị phối hợp kiểm tra thiết bị sau sửa chữa và ký Biên bản nghiệm thu hoàn thành."""
    user = get_current_user_info()
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        dv_svc.xac_nhan_nghiem_thu_sua_chua(id, user["id"], ghi_chu)
        flash("Đã ký xác nhận nghiệm thu hoàn thành sửa chữa thiết bị! Tài sản đã sẵn sàng sử dụng.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.chi_tiet_sua_chua", id=id))

# =========================================================================
# 2. QUẢN LÝ ĐỀ XUẤT MUA SẮM & DỊCH VỤ MỚI (M08)
# =========================================================================

@don_vi_bp.route("/mua-sam")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def danh_sach_mua_sam():
    """Xem danh sách đề xuất mua sắm của đơn vị và theo dõi trạng thái phê duyệt."""
    user = get_current_user_info()
    trang_thai = request.args.get("trang_thai")
    ds = dv_svc.lay_danh_sach_de_xuat_don_vi(user["don_vi"], user["id"], trang_thai=trang_thai)
    return render_template("don_vi/mua_sam_danh_sach.html", de_nghi_list=ds, trang_thai_chon=trang_thai, user=user)

@don_vi_bp.route("/mua-sam/tao", methods=["GET", "POST"])
@yeu_cau_vai_tro("don_vi")
def tao_de_xuat_mua_sam():
    """Lập phiếu đề xuất mua sắm trang thiết bị, vật tư mới (BM01) từ Đơn vị sử dụng."""
    user = get_current_user_info()

    if request.method == "POST":
        ten_hang_list = request.form.getlist("ten_hang_hoa[]")
        don_vi_list = request.form.getlist("don_vi_tinh[]")
        so_luong_list = request.form.getlist("so_luong[]")
        don_gia_list = request.form.getlist("don_gia_du_kien[]")
        vi_tri_list = request.form.getlist("vi_tri_su_dung[]")
        ly_do_list = request.form.getlist("ly_do_muc_dich[]")
        ghi_chu_list = request.form.getlist("ghi_chu[]")

        items = []
        for i in range(len(ten_hang_list)):
            if ten_hang_list[i].strip():
                items.append({
                    "ten_hang_hoa": ten_hang_list[i],
                    "don_vi_tinh": don_vi_list[i] if i < len(don_vi_list) else "Bộ",
                    "so_luong": so_luong_list[i] if i < len(so_luong_list) else 1,
                    "don_gia_du_kien": don_gia_list[i] if i < len(don_gia_list) else 0,
                    "vi_tri_su_dung": vi_tri_list[i] if i < len(vi_tri_list) else "",
                    "ly_do_muc_dich": ly_do_list[i] if i < len(ly_do_list) else "",
                    "ghi_chu": ghi_chu_list[i] if i < len(ghi_chu_list) else ""
                })

        du_lieu_form = {
            "tieu_de": request.form.get("tieu_de"),
            "don_vi_de_nghi": user["don_vi"],
            "mo_ta": request.form.get("mo_ta"),
            "muc_do_uu_tien": request.form.get("muc_do_uu_tien", "binh_thuong"),
            "nguon_kinh_phi": request.form.get("nguon_kinh_phi", "Nguồn thu hợp pháp của Trường"),
            "thoi_gian_can_hang": request.form.get("thoi_gian_can_hang", ""),
            "dia_diem_su_dung": request.form.get("dia_diem_su_dung", ""),
            "ly_do_su_can_thiet": request.form.get("ly_do_su_can_thiet", ""),
            "items": items
        }

        try:
            cleaned = schemas.xac_thuc_de_nghi_mua_sam(du_lieu_form)
            de_nghi = ms_svc.tao_de_nghi(cleaned, user["id"])
            flash(f"Đã lập thành công đề xuất mua sắm mã {de_nghi['ma_de_nghi']}! Hồ sơ đã được chuyển tiếp đến Bộ phận Mua sắm.", "success")
            return redirect(url_for("don_vi.chi_tiet_mua_sam", id=de_nghi["id"]))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template("don_vi/mua_sam_tao.html", user=user)

@don_vi_bp.route("/mua-sam/<int:id>")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def chi_tiet_mua_sam(id):
    """Xem chi tiết đề xuất mua sắm, trạng thái duyệt và xác nhận phối hợp."""
    user = get_current_user_info()
    try:
        de_nghi = ms_svc.lay_chi_tiet_de_nghi(id)
        return render_template("don_vi/mua_sam_chi_tiet.html", de_nghi=de_nghi, user=user)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("don_vi.danh_sach_mua_sam"))

@don_vi_bp.route("/mua-sam/<int:id>/xac-nhan-khao-sat", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def xac_nhan_khao_sat_mua_sam(id):
    """Đơn vị xác nhận biên bản khảo sát nhu cầu thực tế (BM02) với BP Mua sắm."""
    user = get_current_user_info()
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        dv_svc.xac_nhan_khao_sat_mua_sam(id, user["id"], ghi_chu)
        flash("Đã xác nhận biên bản khảo sát nhu cầu mua sắm thực tế!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.chi_tiet_mua_sam", id=id))

@don_vi_bp.route("/mua-sam/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def nghiem_thu_mua_sam(id):
    """Đơn vị tham gia ký biên bản nghiệm thu hàng hóa mua sắm trước khi đưa vào sử dụng."""
    user = get_current_user_info()
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        dv_svc.xac_nhan_nghiem_thu_mua_sam(id, user["id"], ghi_chu)
        flash("Đã xác nhận tham gia nghiệm thu tiếp nhận hàng hóa mua sắm!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.chi_tiet_mua_sam", id=id))

# =========================================================================
# 3. QUẢN LÝ & TRA CỨU DANH MỤC TÀI SẢN CỦA ĐƠN VỊ (M09)
# =========================================================================

@don_vi_bp.route("/tai-san")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def danh_sach_tai_san():
    """Tra cứu danh mục toàn bộ tài sản đang chịu trách nhiệm quản lý của đơn vị."""
    user = get_current_user_info()
    tu_khoa = request.args.get("tu_khoa")
    vi_tri = request.args.get("vi_tri")
    tinh_trang = request.args.get("tinh_trang")
    cho_xac_nhan = bool(request.args.get("cho_xac_nhan"))

    ds_tai_san = dv_svc.lay_danh_sach_tai_san_don_vi(
        user["don_vi"],
        tu_khoa=tu_khoa,
        vi_tri=vi_tri,
        tinh_trang=tinh_trang,
        cho_xac_nhan=cho_xac_nhan
    )
    return render_template(
        "don_vi/tai_san_danh_sach.html",
        tai_san_list=ds_tai_san,
        user=user,
        tu_khoa=tu_khoa,
        vi_tri=vi_tri,
        tinh_trang_chon=tinh_trang,
        cho_xac_nhan=cho_xac_nhan
    )

@don_vi_bp.route("/tai-san/<int:id>")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def chi_tiet_tai_san(id):
    """Xem chi tiết thông số, lịch sử bàn giao, bảo hành và lịch sử sửa chữa của tài sản."""
    user = get_current_user_info()
    try:
        tai_san = ts_svc.lay_chi_tiet_tai_san(id)
        return render_template("don_vi/tai_san_chi_tiet.html", tai_san=tai_san, user=user)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("don_vi.danh_sach_tai_san"))

@don_vi_bp.route("/tai-san/<int:id>/xac-nhan-ban-giao", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def xac_nhan_ban_giao(id):
    """Xác nhận và ký Biên bản tiếp nhận bàn giao tài sản mới từ Phòng QTTB."""
    user = get_current_user_info()
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        dv_svc.xac_nhan_ban_giao_tai_san(id, user, ghi_chu)
        flash("Đã ký xác nhận tiếp nhận bàn giao tài sản vào sổ quản lý của đơn vị!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.chi_tiet_tai_san", id=id))

# =========================================================================
# 4. PHỐI HỢP KIỂM KÊ & GIẢI TRÌNH CHÊNH LỆCH
# =========================================================================

@don_vi_bp.route("/kiem-ke")
@yeu_cau_vai_tro("don_vi", "quan_tri")
def kiem_ke():
    """Phối hợp kiểm kê định kỳ và giải trình chênh lệch số liệu kiểm kê."""
    user = get_current_user_info()
    ds_kiem_ke = dv_svc.lay_danh_sach_kiem_ke_don_vi(user["don_vi"])
    return render_template("don_vi/kiem_ke.html", kiem_ke_list=ds_kiem_ke, user=user)

@don_vi_bp.route("/kiem-ke/<int:id>/giai-trinh", methods=["POST"])
@yeu_cau_vai_tro("don_vi")
def giai_trinh_kiem_ke(id):
    """Gửi phản hồi / giải trình chênh lệch kiểm kê (thừa, thiếu, hỏng chưa báo, chuyển sai vị trí)."""
    noi_dung = request.form.get("noi_dung_giai_trinh", "")
    try:
        dv_svc.gui_giai_trinh_kiem_ke(id, noi_dung)
        flash("Đã gửi văn bản giải trình chênh lệch kiểm kê đến Phòng QTTB thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("don_vi.kiem_ke"))
