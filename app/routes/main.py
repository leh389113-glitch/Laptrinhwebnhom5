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
    """Form báo cáo sự cố hư hại cơ sở vật chất (yêu cầu đăng nhập tài khoản cán bộ đơn vị)."""
    from flask import session
    if "nguoi_dung_id" not in session:
        flash("Vui lòng đăng nhập bằng tài khoản cán bộ đơn vị để gửi báo cáo hư hại / yêu cầu sửa chữa.", "info")
        return redirect(url_for("auth.dang_nhap", next=url_for("don_vi.tao_sua_chua")))
    
    if session.get("vai_tro") == "don_vi":
        return redirect(url_for("don_vi.tao_sua_chua"))
    elif session.get("vai_tro") == "quan_ly_kho":
        return redirect(url_for("tai_san.danh_sach_hu_hai"))
    elif session.get("vai_tro") == "quan_tri":
        return redirect(url_for("admin.bao_cao_hu_hai"))
    return redirect(url_for("don_vi.tao_sua_chua"))

@main_bp.route("/bao-cao-hu-hai/cam-on")
def cam_on():
    """Trang thông báo tiếp nhận báo cáo thành công."""
    return render_template("main/cam_on.html")

