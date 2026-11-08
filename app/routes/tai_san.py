from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import tai_san as ts_svc
from app.services import auth as auth_svc
from app.services import bao_cao_hu_hai as hh_svc
from app.routes import yeu_cau_vai_tro, yeu_cau_dang_nhap
from app import schemas
from app.errors import LoiNghiepVu

tai_san_bp = Blueprint("tai_san", __name__, url_prefix="/tai-san")

@tai_san_bp.route("/")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach():
    """Xem toàn bộ danh sách tài sản cơ sở vật chất (Bộ phận Quản lý tài sản / Admin)."""
    trang_thai = request.args.get("trang_thai")
    phan_loai = request.args.get("phan_loai")
    tinh_trang_ky_thuat = request.args.get("tinh_trang_ky_thuat")
    tu_khoa = request.args.get("tu_khoa")

    ds_tai_san = ts_svc.lay_danh_sach_tai_san(
        trang_thai=trang_thai,
        tu_khoa=tu_khoa,
        phan_loai=phan_loai,
        tinh_trang_ky_thuat=tinh_trang_ky_thuat
    )
    return render_template(
        "tai_san/danh_sach.html",
        tai_san_list=ds_tai_san,
        trang_thai_chon=trang_thai,
        phan_loai_chon=phan_loai,
        tinh_trang_chon=tinh_trang_ky_thuat,
        tu_khoa=tu_khoa
    )

@tai_san_bp.route("/cua-toi")
@yeu_cau_dang_nhap
def cua_toi():
    """Chuyển hướng về danh sách tài sản kho."""
    return redirect(url_for("tai_san.danh_sach"))

@tai_san_bp.route("/<int:id>")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def chi_tiet(id):
    """Xem thông tin chi tiết một tài sản."""
    try:
        tai_san = ts_svc.lay_chi_tiet_tai_san(id)
        danh_sach_nguoi_dung = auth_svc.lay_danh_sach_nguoi_dung()
        return render_template("tai_san/chi_tiet.html", tai_san=tai_san, nguoi_dung_list=danh_sach_nguoi_dung)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach"))

@tai_san_bp.route("/<int:id>/chinh-sua", methods=["GET", "POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def chinh_sua(id):
    """Chỉnh sửa thông tin tài sản (chuyên trách do Bộ phận Quản lý tài sản thực hiện)."""
    tai_san = ts_svc.lay_chi_tiet_tai_san(id)
    if request.method == "POST":
        du_lieu_form = {
            "ten_tai_san": request.form.get("ten_tai_san"),
            "loai_tai_san": request.form.get("loai_tai_san"),
            "phan_loai": request.form.get("phan_loai"),
            "tinh_trang_ky_thuat": request.form.get("tinh_trang_ky_thuat"),
            "vi_tri": request.form.get("vi_tri"),
            "phong_ban": request.form.get("phong_ban"),
            "don_vi_su_dung": request.form.get("don_vi_su_dung"),
            "mo_ta": request.form.get("mo_ta"),
            "gia_tri": request.form.get("gia_tri"),
            "so_serial": request.form.get("so_serial"),
            "model": request.form.get("model"),
            "hang_san_xuat": request.form.get("hang_san_xuat"),
            "thoi_han_bao_hanh": request.form.get("thoi_han_bao_hanh")
        }
        try:
            cleaned = schemas.xac_thuc_tai_san(du_lieu_form)
            ts_svc.cap_nhat_tai_san(id, cleaned)
            flash("Cập nhật thông tin tài sản thành công!", "success")
            return redirect(url_for("tai_san.chi_tiet", id=id))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template("tai_san/chinh_sua.html", tai_san=tai_san)

@tai_san_bp.route("/<int:id>/ban-giao", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def ban_giao(id):
    """Bàn giao tài sản cho cán bộ / phòng ban sử dụng (chuyên trách do Bộ phận Quản lý tài sản thực hiện)."""
    du_lieu_form = {
        "nguoi_nhan_id": request.form.get("nguoi_nhan_id"),
        "ghi_chu": request.form.get("ghi_chu")
    }
    try:
        cleaned = schemas.xac_thuc_ban_giao(du_lieu_form)
        ts_svc.ban_giao_tai_san(id, cleaned["nguoi_nhan_id"], session["nguoi_dung_id"], cleaned["ghi_chu"])
        flash("Bàn giao tài sản thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.chi_tiet", id=id))

@tai_san_bp.route("/<int:id>/bao-tri", methods=["GET", "POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def bao_tri(id):
    """Ghi nhận hoạt động bảo trì, sửa chữa tài sản (Bộ phận Quản lý tài sản thực hiện)."""
    tai_san = ts_svc.lay_chi_tiet_tai_san(id)
    if request.method == "POST":
        du_lieu_form = {
            "noi_dung": request.form.get("noi_dung"),
            "chi_phi": request.form.get("chi_phi"),
            "don_vi_thuc_hien": request.form.get("don_vi_thuc_hien"),
            "ghi_chu": request.form.get("ghi_chu"),
            "trang_thai_moi": request.form.get("trang_thai_moi")
        }
        try:
            cleaned = schemas.xac_thuc_bao_tri(du_lieu_form)
            cleaned["trang_thai_moi"] = du_lieu_form["trang_thai_moi"]
            ts_svc.ghi_nhan_bao_tri(id, cleaned, session["nguoi_dung_id"])
            flash("Ghi nhận bảo trì/sửa chữa tài sản thành công!", "success")
            return redirect(url_for("tai_san.chi_tiet", id=id))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template("tai_san/bao_tri.html", tai_san=tai_san)

# =========================================================================
# QUY TRÌNH SỬA CHỮA M09 (PHẦN III CỦA QUY TRÌNH & YÊU CẦU 1)
# =========================================================================

@tai_san_bp.route("/sua-chua")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_sua_chua():
    """Xem danh sách các yêu cầu sửa chữa cơ sở vật chất tại M09."""
    trang_thai = request.args.get("trang_thai")
    ds = ts_svc.lay_danh_sach_sua_chua(trang_thai=trang_thai)
    return render_template("tai_san/sua_chua.html", sua_chua_list=ds, trang_thai_chon=trang_thai)

@tai_san_bp.route("/sua-chua/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def nghiem_thu_sua_chua(id):
    """Nghiệm thu hoàn thành sửa chữa thiết bị, đưa tài sản về trạng thái hoạt động."""
    du_lieu = {
        "chi_phi_thuc_te": request.form.get("chi_phi_thuc_te", 0),
        "ghi_chu": request.form.get("ghi_chu", "")
    }
    try:
        ts_svc.nghiem_thu_sua_chua(id, du_lieu, session["nguoi_dung_id"])
        flash("Nghiệm thu hoàn tất sửa chữa thành công! Tài sản đã hoạt động bình thường.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.danh_sach_sua_chua"))

# =========================================================================
# KIỂM KÊ TÀI SẢN
# =========================================================================

@tai_san_bp.route("/kiem-ke")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def kiem_ke():
    """Danh sách các đợt kiểm kê tài sản định kỳ."""
    ds_kiem_ke = ts_svc.lay_danh_sach_kiem_ke()
    tai_san_list = ts_svc.lay_danh_sach_tai_san()
    return render_template("tai_san/kiem_ke.html", kiem_ke_list=ds_kiem_ke, tai_san_list=tai_san_list)

@tai_san_bp.route("/kiem-ke/tao", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tao_kiem_ke():
    """Tạo phiếu kiểm kê mới (Bộ phận Quản lý tài sản)."""
    tai_san_ids = request.form.getlist("tai_san_id[]")
    tinh_trangs = request.form.getlist("tinh_trang[]")
    ghi_chus = request.form.getlist("ghi_chu_kiem_ke[]")

    chi_tiet = []
    for i in range(len(tai_san_ids)):
        if tai_san_ids[i]:
            chi_tiet.append({
                "tai_san_id": int(tai_san_ids[i]),
                "tinh_trang": tinh_trangs[i] if i < len(tinh_trangs) else "tot",
                "ghi_chu": ghi_chus[i] if i < len(ghi_chus) else ""
            })

    du_lieu = {
        "ghi_chu": request.form.get("ghi_chu", ""),
        "chi_tiet": chi_tiet
    }
    try:
        phieu = ts_svc.tao_phieu_kiem_ke(du_lieu, session["nguoi_dung_id"])
        flash(f"Đã lập phiếu kiểm kê {phieu['ma_phieu']} thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.kiem_ke"))

# =========================================================================
# LUỒNG XỬ LÝ HƯ HỎNG VÀ MUA SẮM THAY THẾ (YÊU CẦU 1.DOCX - BỘ PHẬN QUẢN LÝ TÀI SẢN)
# =========================================================================

@tai_san_bp.route("/bao-cao-hu-hai")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_hu_hai():
    """
    Bộ phận Quản lý tài sản tiếp nhận, kiểm tra và xử lý các sự cố hư hại vật chất.
    Admin có thể xem giám sát.
    """
    trang_thai = request.args.get("trang_thai")
    danh_sach = hh_svc.lay_danh_sach_bao_cao(trang_thai=trang_thai)
    return render_template("tai_san/bao_cao_hu_hai.html", bao_cao_list=danh_sach, trang_thai_chon=trang_thai)

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/xu-ly", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def xu_ly_hu_hai(id):
    """
    Bộ phận Quản lý tài sản xác minh thực tế và đánh giá tình trạng hư hại theo Yêu cầu 1.docx:
    - Sửa chữa được -> chuyển sang trạng thái 'dang_sua_chua' và tạo yêu cầu sửa chữa M09
    - Cần thay thế -> lập biên bản đánh giá 'can_thay_the'
    - Hoàn tất xử lý -> 'da_xu_ly'
    """
    phuong_an = request.form.get("phuong_an")
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        hh_svc.xac_minh_danh_gia(id, phuong_an, ghi_chu=ghi_chu, nguoi_xu_ly_id=session["nguoi_dung_id"])
        flash("Đã cập nhật kết quả xác minh và phương án xử lý sự cố cơ sở vật chất!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.danh_sach_hu_hai"))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/tao-mua-sam", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tao_mua_sam_thay_the(id):
    """
    Trường hợp cần thay thế:
    Lập biên bản đánh giá -> Tạo yêu cầu mua sắm thay thế chuyển M08 (theo Yêu cầu 1.docx).
    """
    try:
        de_nghi = hh_svc.tao_yeu_cau_thay_the_sang_m08(id, session["nguoi_dung_id"])
        flash(f"Đã lập yêu cầu mua sắm thay thế mã {de_nghi['ma_de_nghi']} chuyển sang phân hệ M08 thành công!", "success")
        return redirect(url_for("mua_sam.chi_tiet", id=de_nghi["id"]))
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach_hu_hai"))
