from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import mua_sam as ms_svc
from app.routes import yeu_cau_vai_tro
from app import schemas
from app.errors import LoiNghiepVu

mua_sam_bp = Blueprint("mua_sam", __name__, url_prefix="/mua-sam")

@mua_sam_bp.route("/")
@yeu_cau_vai_tro("mua_sam", "quan_ly_kho", "quan_tri")
def danh_sach():
    """Danh sách các đề nghị mua sắm."""
    trang_thai = request.args.get("trang_thai")
    de_nghi_list = ms_svc.lay_danh_sach_de_nghi(trang_thai=trang_thai)
    return render_template("mua_sam/danh_sach.html", de_nghi_list=de_nghi_list, trang_thai_chon=trang_thai)

@mua_sam_bp.route("/de-nghi/tao", methods=["GET", "POST"])
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def tao_de_nghi():
    """Lập đề nghị mua sắm cơ sở vật chất mới."""
    if request.method == "POST":
        # Thu thập các dòng hàng hóa từ form
        ten_hang_list = request.form.getlist("ten_hang_hoa[]")
        don_vi_list = request.form.getlist("don_vi_tinh[]")
        so_luong_list = request.form.getlist("so_luong[]")
        don_gia_list = request.form.getlist("don_gia_du_kien[]")
        ghi_chu_list = request.form.getlist("ghi_chu[]")

        items = []
        for i in range(len(ten_hang_list)):
            if ten_hang_list[i].strip():
                items.append({
                    "ten_hang_hoa": ten_hang_list[i],
                    "don_vi_tinh": don_vi_list[i] if i < len(don_vi_list) else "Cái",
                    "so_luong": so_luong_list[i] if i < len(so_luong_list) else 1,
                    "don_gia_du_kien": don_gia_list[i] if i < len(don_gia_list) else 0,
                    "ghi_chu": ghi_chu_list[i] if i < len(ghi_chu_list) else ""
                })

        du_lieu_form = {
            "tieu_de": request.form.get("tieu_de"),
            "don_vi_de_nghi": request.form.get("don_vi_de_nghi"),
            "mo_ta": request.form.get("mo_ta"),
            "items": items
        }

        try:
            cleaned = schemas.xac_thuc_de_nghi_mua_sam(du_lieu_form)
            de_nghi = ms_svc.tao_de_nghi(cleaned, session["nguoi_dung_id"])
            flash(f"Đã lập thành công đề nghị mua sắm mã {de_nghi['ma_de_nghi']}!", "success")
            return redirect(url_for("mua_sam.chi_tiet", id=de_nghi["id"]))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")
            return render_template("mua_sam/tao_de_nghi.html", du_lieu=du_lieu_form)

    return render_template("mua_sam/tao_de_nghi.html")

@mua_sam_bp.route("/de-nghi/<int:id>")
@yeu_cau_vai_tro("mua_sam", "quan_ly_kho", "quan_tri")
def chi_tiet(id):
    """Xem chi tiết đề nghị mua sắm."""
    try:
        de_nghi = ms_svc.lay_chi_tiet_de_nghi(id)
        return render_template("mua_sam/chi_tiet.html", de_nghi=de_nghi)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("mua_sam.danh_sach"))

@mua_sam_bp.route("/de-nghi/<int:id>/phe-duyet", methods=["POST"])
@yeu_cau_vai_tro("quan_tri")
def phe_duyet(id):
    """Admin phê duyệt đề nghị mua sắm."""
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        de_nghi = ms_svc.phe_duyet_de_nghi(id, session["nguoi_dung_id"], ghi_chu)
        flash(f"Đã phê duyệt đề nghị {de_nghi['ma_de_nghi']} thành công!", "success")
        if request.is_json:
            return jsonify({"thanh_cong": True, "ma_de_nghi": de_nghi["ma_de_nghi"]})
    except LoiNghiepVu as e:
        if request.is_json:
            return jsonify(e.to_dict()), e.status_code
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/tu-choi", methods=["POST"])
@yeu_cau_vai_tro("quan_tri")
def tu_choi(id):
    """Admin từ chối đề nghị mua sắm."""
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        de_nghi = ms_svc.tu_choi_de_nghi(id, session["nguoi_dung_id"], ghi_chu)
        flash(f"Đã từ chối đề nghị {de_nghi['ma_de_nghi']}.", "warning")
        if request.is_json:
            return jsonify({"thanh_cong": True, "ma_de_nghi": de_nghi["ma_de_nghi"]})
    except LoiNghiepVu as e:
        if request.is_json:
            return jsonify(e.to_dict()), e.status_code
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/tiep-nhan", methods=["GET", "POST"])
@yeu_cau_vai_tro("quan_ly_kho", "mua_sam", "quan_tri")
def tiep_nhan(id):
    """Ghi nhận tiếp nhận hàng hóa nhập kho."""
    de_nghi = ms_svc.lay_chi_tiet_de_nghi(id)
    if request.method == "POST":
        du_lieu = {
            "ghi_chu": request.form.get("ghi_chu", "")
        }
        try:
            ms_svc.tiep_nhan_hang_hoa(id, du_lieu, session["nguoi_dung_id"])
            flash(f"Tiếp nhận hàng hóa thành công! Các tài sản đã được tạo tự động và đưa vào kho (M09).", "success")
            return redirect(url_for("mua_sam.chi_tiet", id=id))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template("mua_sam/tiep_nhan.html", de_nghi=de_nghi)

@mua_sam_bp.route("/ho-so")
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def ho_so():
    """Danh sách hồ sơ mua sắm."""
    danh_sach_hs = ms_svc.lay_danh_sach_ho_so()
    return render_template("mua_sam/ho_so.html", ho_so_list=danh_sach_hs)

