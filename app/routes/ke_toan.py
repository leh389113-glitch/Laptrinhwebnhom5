from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import ke_toan as kt_svc
from app.services import tai_san as ts_svc
from app.routes import yeu_cau_vai_tro
from app import schemas
from app.errors import LoiNghiepVu

ke_toan_bp = Blueprint("ke_toan", __name__, url_prefix="/ke-toan")

@ke_toan_bp.route("/")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def danh_sach():
    """Danh sách đề nghị mua sắm đã tiếp nhận hàng chờ thanh toán."""
    de_nghi_list = kt_svc.lay_de_nghi_cho_thanh_toan()
    ho_so_sua_chua_list = ts_svc.lay_danh_sach_ho_so_thanh_toan_sua_chua()
    return render_template(
        "ke_toan/danh_sach.html",
        de_nghi_list=de_nghi_list,
        ho_so_sua_chua_list=ho_so_sua_chua_list
    )

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
@yeu_cau_vai_tro("ke_toan")
def thanh_toan(id):
    """Ghi nhận thanh toán tiền cho đề nghị mua sắm (chuyên trách do Kế toán thực hiện)."""
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

@ke_toan_bp.route("/sua-chua/<int:id>")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def chi_tiet_thanh_toan_sua_chua(id):
    try:
        ho_so = ts_svc.lay_ho_so_thanh_toan_sua_chua(id)
        if not ho_so or ho_so["trang_thai"] == "nhap":
            raise LoiNghiepVu("KHONG_CO_DE_NGHI_THANH_TOAN", "Hồ sơ sửa chữa chưa được M09 gửi sang Kế toán.")
        yc = ts_svc.lay_chi_tiet_sua_chua(id)
        return render_template(
            "ke_toan/sua_chua_chi_tiet.html",
            yc=yc,
            ho_so=ho_so
        )
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("ke_toan.danh_sach"))

@ke_toan_bp.route("/sua-chua/<int:id>/tiep-nhan", methods=["POST"])
@yeu_cau_vai_tro("ke_toan")
def tiep_nhan_ho_so_sua_chua(id):
    return _cap_nhat_ho_so_sua_chua(id, "tiep_nhan")

@ke_toan_bp.route("/sua-chua/<int:id>/bo-sung", methods=["POST"])
@yeu_cau_vai_tro("ke_toan")
def yeu_cau_bo_sung_ho_so_sua_chua(id):
    return _cap_nhat_ho_so_sua_chua(id, "bo_sung")

@ke_toan_bp.route("/sua-chua/<int:id>/xac-nhan-thanh-toan", methods=["POST"])
@yeu_cau_vai_tro("ke_toan")
def xac_nhan_thanh_toan_sua_chua(id):
    return _cap_nhat_ho_so_sua_chua(id, "da_thanh_toan")

def _cap_nhat_ho_so_sua_chua(id, hanh_dong):
    try:
        ts_svc.cap_nhat_ho_so_thanh_toan_sua_chua(
            id, hanh_dong, session["nguoi_dung_id"],
            request.form.get("ghi_chu", "")
        )
        flash(
            "Đã cập nhật trạng thái hồ sơ thanh toán sửa chữa."
            if hanh_dong != "da_thanh_toan"
            else "Đã xác nhận thanh toán; quy trình sửa chữa hoàn tất.",
            "success"
        )
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("ke_toan.chi_tiet_thanh_toan_sua_chua", id=id))

@ke_toan_bp.route("/lich-su")
@yeu_cau_vai_tro("ke_toan", "quan_tri")
def lich_su():
    """Lịch sử các khoản đã thanh toán."""
    lich_su_list = kt_svc.lay_lich_su_thanh_toan()
    lich_su_sua_chua_list = ts_svc.lay_lich_su_thanh_toan_sua_chua()
    return render_template(
        "ke_toan/lich_su.html",
        lich_su_list=lich_su_list,
        lich_su_sua_chua_list=lich_su_sua_chua_list
    )
