from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from app.services import bao_cao as bc_svc
from app.services import mua_sam as ms_svc
from app.services import tai_san as ts_svc
from app.services import auth as auth_svc
from app.routes import yeu_cau_vai_tro
from app.errors import LoiNghiepVu

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@yeu_cau_vai_tro("quan_tri")
def dashboard():
    """Dashboard quản trị tổng hợp M17 với các KPI cards và biểu đồ Chart.js."""
    thong_ke = bc_svc.thong_ke_tong_quan()
    return render_template("admin/dashboard.html", thong_ke=thong_ke)

@admin_bp.route("/mua-sam")
@yeu_cau_vai_tro("quan_tri")
def mua_sam():
    """Admin quản lý mua sắm: xem, phê duyệt/từ chối đề nghị."""
    trang_thai = request.args.get("trang_thai")
    de_nghi_list = ms_svc.lay_danh_sach_de_nghi(trang_thai=trang_thai)
    return render_template("admin/mua_sam.html", de_nghi_list=de_nghi_list, trang_thai_chon=trang_thai)

@admin_bp.route("/tai-san")
@yeu_cau_vai_tro("quan_tri")
def tai_san():
    """Admin quản lý tài sản: xem danh sách, cập nhật, điều chuyển."""
    trang_thai = request.args.get("trang_thai")
    tu_khoa = request.args.get("tu_khoa")
    ds_tai_san = ts_svc.lay_danh_sach_tai_san(trang_thai=trang_thai, tu_khoa=tu_khoa)
    return render_template("admin/tai_san.html", tai_san_list=ds_tai_san, trang_thai_chon=trang_thai, tu_khoa=tu_khoa)

@admin_bp.route("/bao-cao")
@yeu_cau_vai_tro("quan_tri")
def bao_cao():
    """Trang tổng hợp báo cáo M17 và tải biểu mẫu PDF."""
    tu_ngay = request.args.get("tu_ngay")
    den_ngay = request.args.get("den_ngay")
    phong_ban = request.args.get("phong_ban")

    ds_mua_sam = bc_svc.bao_cao_mua_sam(tu_ngay=tu_ngay, den_ngay=den_ngay)
    ds_tai_san = bc_svc.bao_cao_tai_san(phong_ban=phong_ban)

    return render_template(
        "admin/bao_cao.html",
        ds_mua_sam=ds_mua_sam,
        ds_tai_san=ds_tai_san,
        tu_ngay=tu_ngay,
        den_ngay=den_ngay,
        phong_ban=phong_ban
    )

@admin_bp.route("/bao-cao/xuat-pdf-mua-sam")
@yeu_cau_vai_tro("quan_tri")
def xuat_pdf_mua_sam():
    """Xuất hồ sơ mua sắm theo mẫu Thẻ tài sản cố định."""
    pdf_data = bc_svc.xuat_pdf_mua_sam(
        tu_ngay=request.args.get("tu_ngay"),
        den_ngay=request.args.get("den_ngay")
    )
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=bao_cao_mua_sam_the_tai_san.pdf"}
    )

@admin_bp.route("/bao-cao/xuat-pdf-tai-san")
@yeu_cau_vai_tro("quan_tri")
def xuat_pdf_tai_san():
    """Xuất danh mục tài sản theo mẫu Bảng kê mua hàng Mẫu 06-VT."""
    pdf_data = bc_svc.xuat_pdf_tai_san(phong_ban=request.args.get("phong_ban"))
    return Response(
        pdf_data,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=bao_cao_tai_san_mau_06.pdf"}
    )

@admin_bp.route("/tai-khoan")
@yeu_cau_vai_tro("quan_tri")
def tai_khoan():
    """Quản lý danh sách tài khoản và phân quyền người dùng."""
    ds_nguoi_dung = auth_svc.lay_danh_sach_nguoi_dung()
    return render_template("admin/tai_khoan.html", nguoi_dung_list=ds_nguoi_dung)

@admin_bp.route("/tai-khoan/<int:id>/doi-vai-tro", methods=["POST"])
@yeu_cau_vai_tro("quan_tri")
def doi_vai_tro(id):
    """Admin thay đổi vai trò người dùng."""
    vai_tro_moi = request.form.get("vai_tro")
    try:
        auth_svc.doi_vai_tro(id, vai_tro_moi)
        flash("Thay đổi quyền người dùng thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("admin.tai_khoan"))
