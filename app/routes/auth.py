from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.services import auth as auth_svc
from app import schemas
from app.errors import LoiNghiepVu

auth_bp = Blueprint("auth", __name__)

def dieu_huong_theo_vai_tro(vai_tro: str):
    """Xác định URL chuyển hướng dựa trên vai trò của người dùng."""
    if vai_tro == "mua_sam":
        return redirect(url_for("mua_sam.danh_sach"))
    elif vai_tro == "quan_ly_kho":
        return redirect(url_for("tai_san.danh_sach"))
    elif vai_tro == "ke_toan":
        return redirect(url_for("ke_toan.danh_sach"))
    elif vai_tro == "quan_tri":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("main.trang_chu"))

@auth_bp.route("/dang-nhap", methods=["GET", "POST"])
def dang_nhap():
    """Trang đăng nhập hệ thống."""
    if "nguoi_dung_id" in session and "vai_tro" in session:
        return dieu_huong_theo_vai_tro(session["vai_tro"])

    if request.method == "POST":
        du_lieu_form = {
            "ten_dang_nhap": request.form.get("ten_dang_nhap"),
            "mat_khau": request.form.get("mat_khau")
        }
        try:
            cleaned = schemas.xac_thuc_dang_nhap(du_lieu_form)
            user = auth_svc.dang_nhap(cleaned["ten_dang_nhap"], cleaned["mat_khau"])

            # Lưu vào session
            session["nguoi_dung_id"] = user["id"]
            session["vai_tro"] = user["vai_tro"]
            session["ho_ten"] = user["ho_ten"]
            session["ten_dang_nhap"] = user["ten_dang_nhap"]

            flash(f"Xin chào {user['ho_ten']}, bạn đã đăng nhập thành công!", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            return dieu_huong_theo_vai_tro(user["vai_tro"])
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")
            return render_template("auth/dang_nhap.html", ten_dang_nhap=du_lieu_form.get("ten_dang_nhap"))

    return render_template("auth/dang_nhap.html")

@auth_bp.route("/dang-ky", methods=["GET", "POST"])
def dang_ky():
    """Trang đăng ký tài khoản cho cán bộ các phòng ban."""
    if "nguoi_dung_id" in session and "vai_tro" in session:
        return dieu_huong_theo_vai_tro(session["vai_tro"])

    if request.method == "POST":
        du_lieu_form = {
            "ho_ten": request.form.get("ho_ten"),
            "email": request.form.get("email"),
            "ten_dang_nhap": request.form.get("ten_dang_nhap"),
            "mat_khau": request.form.get("mat_khau"),
            "xac_nhan_mat_khau": request.form.get("xac_nhan_mat_khau"),
            "vai_tro": request.form.get("vai_tro")
        }
        try:
            cleaned = schemas.xac_thuc_dang_ky(du_lieu_form)
            auth_svc.dang_ky(cleaned)
            flash("Đăng ký tài khoản thành công! Bạn có thể đăng nhập ngay bây giờ.", "success")
            return redirect(url_for("auth.dang_nhap"))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")
            return render_template("auth/dang_ky.html", du_lieu=du_lieu_form)

    return render_template("auth/dang_ky.html")

@auth_bp.route("/dang-xuat")
def dang_xuat():
    """Đăng xuất và xóa session."""
    session.clear()
    flash("Bạn đã đăng xuất khỏi hệ thống thành công.", "info")
    return redirect(url_for("main.trang_chu"))
