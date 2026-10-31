from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import tai_san as ts_svc
from app.services import auth as auth_svc
from app.routes import yeu_cau_vai_tro, yeu_cau_dang_nhap
from app import schemas
from app.errors import LoiNghiepVu

tai_san_bp = Blueprint("tai_san", __name__, url_prefix="/tai-san")

@tai_san_bp.route("/")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach():
    """Xem toàn bộ danh sách tài sản cơ sở vật chất (Bộ phận Quản lý kho / Admin)."""
    trang_thai = request.args.get("trang_thai")
    tu_khoa = request.args.get("tu_khoa")
    ds_tai_san = ts_svc.lay_danh_sach_tai_san(trang_thai=trang_thai, tu_khoa=tu_khoa)
    return render_template("tai_san/danh_sach.html", tai_san_list=ds_tai_san, trang_thai_chon=trang_thai, tu_khoa=tu_khoa)

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
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def chinh_sua(id):
    """Chỉnh sửa thông tin tài sản."""
    tai_san = ts_svc.lay_chi_tiet_tai_san(id)
    if request.method == "POST":
        du_lieu_form = {
            "ten_tai_san": request.form.get("ten_tai_san"),
            "loai_tai_san": request.form.get("loai_tai_san"),
            "vi_tri": request.form.get("vi_tri"),
            "phong_ban": request.form.get("phong_ban"),
            "mo_ta": request.form.get("mo_ta"),
            "gia_tri": request.form.get("gia_tri")
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
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def ban_giao(id):
    """Bàn giao tài sản cho cán bộ / phòng ban sử dụng."""
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
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def bao_tri(id):
    """Ghi nhận hoạt động bảo trì, sửa chữa tài sản."""
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

@tai_san_bp.route("/kiem-ke")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def kiem_ke():
    """Danh sách các đợt kiểm kê tài sản định kỳ."""
    ds_kiem_ke = ts_svc.lay_danh_sach_kiem_ke()
    tai_san_list = ts_svc.lay_danh_sach_tai_san()
    return render_template("tai_san/kiem_ke.html", kiem_ke_list=ds_kiem_ke, tai_san_list=tai_san_list)

@tai_san_bp.route("/kiem-ke/tao", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def tao_kiem_ke():
    """Tạo phiếu kiểm kê mới."""
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
