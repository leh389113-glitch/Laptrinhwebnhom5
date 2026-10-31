from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import ke_toan as kt_svc
from app.routes import yeu_cau_vai_tro
from app import schemas
from app.errors import LoiNghiepVu

ke_toan_bp = Blueprint("ke_toan", __name__, url_prefix="/ke-toan")

@ke_toan_bp.route("/")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def danh_sach():
    """Danh sách đề nghị mua sắm đã tiếp nhận hàng chờ thanh toán."""
    de_nghi_list = kt_svc.lay_de_nghi_cho_thanh_toan()
    return render_template("ke_toan/danh_sach.html", de_nghi_list=de_nghi_list)

@ke_toan_bp.route("/de-nghi/<int:id>")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def chi_tiet(id):
    """Xem chi tiết hóa đơn/đề nghị để thực hiện thanh toán."""
    try:
        de_nghi = kt_svc.lay_chi_tiet_thanh_toan(id)
        return render_template("ke_toan/chi_tiet.html", de_nghi=de_nghi)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("ke_toan.danh_sach"))

@ke_toan_bp.route("/de-nghi/<int:id>/thanh-toan", methods=["POST"])
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def thanh_toan(id):
    """Ghi nhận thanh toán tiền cho đề nghị mua sắm."""
    du_lieu_form = {
        "so_tien": request.form.get("so_tien"),
        "so_hoa_don": request.form.get("so_hoa_don"),
        "phuong_thuc": request.form.get("phuong_thuc"),
        "ghi_chu": request.form.get("ghi_chu")
    }
    try:
        cleaned = schemas.xac_thuc_thanh_toan(du_lieu_form)
        kt_svc.ghi_nhan_thanh_toan(id, cleaned, session["nguoi_dung_id"])
        flash("Ghi nhận thanh toán thành công! Đề nghị đã chuyển sang trạng thái Hoàn tất.", "success")
        return redirect(url_for("ke_toan.lich_su"))
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("ke_toan.chi_tiet", id=id))

@ke_toan_bp.route("/lich-su")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def lich_su():
    """Lịch sử các khoản đã thanh toán."""
    lich_su_list = kt_svc.lay_lich_su_thanh_toan()
    return render_template("ke_toan/lich_su.html", lich_su_list=lich_su_list)

