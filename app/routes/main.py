from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services import bao_cao_hu_hai as bc_svc
from app.services import bao_cao as tk_svc
from app import schemas
from app.errors import LoiNghiepVu

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def trang_chu():
    """Trang chủ cổng thông tin Quản lý Cơ sở Vật chất (phong cách NEU)."""
    try:
        thong_ke = tk_svc.thong_ke_tong_quan()
    except Exception:
        thong_ke = None
    return render_template("main/trang_chu.html", thong_ke=thong_ke)

@main_bp.route("/bao-cao-hu-hai", methods=["GET", "POST"])
def bao_cao_hu_hai():
    """Form báo cáo sự cố hư hại cơ sở vật chất (công khai cho tất cả mọi người)."""
    if request.method == "POST":
        du_lieu_form = {
            "ho_ten": request.form.get("ho_ten"),
            "lien_he": request.form.get("lien_he"),
            "ten_vat_chat": request.form.get("ten_vat_chat"),
            "vi_tri": request.form.get("vi_tri"),
            "muc_do": request.form.get("muc_do"),
            "mo_ta_chi_tiet": request.form.get("mo_ta_chi_tiet"),
            "thoi_gian_phat_hien": request.form.get("thoi_gian_phat_hien")
        }
        try:
            cleaned_data = schemas.xac_thuc_bao_cao_hu_hai(du_lieu_form)
            bc_svc.gui_bao_cao(cleaned_data)
            flash("Báo cáo hư hại đã được gửi thành công. Bộ phận quản lý sẽ kiểm tra và xử lý sớm nhất!", "success")
            return redirect(url_for("main.cam_on"))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")
            return render_template("main/bao_cao_hu_hai.html", du_lieu=du_lieu_form)

    return render_template("main/bao_cao_hu_hai.html")

@main_bp.route("/bao-cao-hu-hai/cam-on")
def cam_on():
    """Trang thông báo tiếp nhận báo cáo thành công."""
    return render_template("main/cam_on.html")

