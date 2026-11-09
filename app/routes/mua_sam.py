from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import mua_sam as ms_svc
from app.routes import yeu_cau_vai_tro
from app import schemas
from app.errors import LoiNghiepVu

mua_sam_bp = Blueprint("mua_sam", __name__, url_prefix="/mua-sam")

@mua_sam_bp.route("/")
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def danh_sach():
    """Danh sách các đề nghị mua sắm (Bộ phận Mua sắm tác nghiệp, Admin giám sát)."""
    trang_thai = request.args.get("trang_thai")
    de_nghi_list = ms_svc.lay_danh_sach_de_nghi(trang_thai=trang_thai)
    return render_template("mua_sam/danh_sach.html", de_nghi_list=de_nghi_list, trang_thai_chon=trang_thai)

@mua_sam_bp.route("/de-nghi/tao", methods=["GET", "POST"])
@yeu_cau_vai_tro("mua_sam")
def tao_de_nghi():
    """Lập đề nghị / Yêu cầu mua sắm cơ sở vật chất mới (BM01) - Chỉ bộ phận Mua sắm."""
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
                    "don_vi_tinh": don_vi_list[i] if i < len(don_vi_list) else "Cái",
                    "so_luong": so_luong_list[i] if i < len(so_luong_list) else 1,
                    "don_gia_du_kien": don_gia_list[i] if i < len(don_gia_list) else 0,
                    "vi_tri_su_dung": vi_tri_list[i] if i < len(vi_tri_list) else "",
                    "ly_do_muc_dich": ly_do_list[i] if i < len(ly_do_list) else "",
                    "ghi_chu": ghi_chu_list[i] if i < len(ghi_chu_list) else ""
                })

        du_lieu_form = {
            "tieu_de": request.form.get("tieu_de"),
            "don_vi_de_nghi": request.form.get("don_vi_de_nghi"),
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
            de_nghi = ms_svc.tao_de_nghi(cleaned, session["nguoi_dung_id"])
            flash(f"Đã lập thành công đề nghị mua sắm mã {de_nghi['ma_de_nghi']}!", "success")
            return redirect(url_for("mua_sam.chi_tiet", id=de_nghi["id"]))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")
            return render_template("mua_sam/tao_de_nghi.html", du_lieu=du_lieu_form)

    return render_template("mua_sam/tao_de_nghi.html")

@mua_sam_bp.route("/de-nghi/<int:id>")
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def chi_tiet(id):
    """Xem chi tiết đề nghị mua sắm và tiến trình các bước mua sắm M08."""
    try:
        de_nghi = ms_svc.lay_chi_tiet_de_nghi(id)
        return render_template("mua_sam/chi_tiet.html", de_nghi=de_nghi)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("mua_sam.danh_sach"))

@mua_sam_bp.route("/de-nghi/<int:id>/phe-duyet", methods=["POST"])
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def phe_duyet(id):
    """Phê duyệt đề nghị mua sắm: Trưởng BP Mua sắm duyệt đơn < 100tr, Lãnh đạo/Admin duyệt đơn >= 100tr."""
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        de_nghi = ms_svc.phe_duyet_de_nghi(id, session["nguoi_dung_id"], ghi_chu, vai_tro=session.get("vai_tro"))
        flash(f"Đã phê duyệt đề nghị {de_nghi['ma_de_nghi']} thành công!", "success")
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"thanh_cong": True, "ma_de_nghi": de_nghi["ma_de_nghi"]})
    except LoiNghiepVu as e:
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify(e.to_dict()), e.status_code
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/tu-choi", methods=["POST"])
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def tu_choi(id):
    """Từ chối đề nghị mua sắm."""
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        de_nghi = ms_svc.tu_choi_de_nghi(id, session["nguoi_dung_id"], ghi_chu, vai_tro=session.get("vai_tro"))
        flash(f"Đã từ chối đề nghị {de_nghi['ma_de_nghi']}.", "warning")
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify({"thanh_cong": True, "ma_de_nghi": de_nghi["ma_de_nghi"]})
    except LoiNghiepVu as e:
        if request.is_json or request.headers.get("Accept") == "application/json":
            return jsonify(e.to_dict()), e.status_code
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/khao-sat", methods=["POST"])
@yeu_cau_vai_tro("mua_sam")
def khao_sat(id):
    """Lập biên bản khảo sát nhu cầu mua sắm thực tế BM02."""
    du_lieu_form = {
        "noi_dung": request.form.get("noi_dung"),
        "dia_diem": request.form.get("dia_diem"),
        "can_bo_khao_sat": request.form.get("can_bo_khao_sat"),
        "dai_dien_don_vi": request.form.get("dai_dien_don_vi"),
        "ket_qua_danh_gia": request.form.get("ket_qua_danh_gia"),
        "kiem_tra_kho": request.form.get("kiem_tra_kho"),
        "doi_chieu_dinh_muc": request.form.get("doi_chieu_dinh_muc"),
        "muc_do_can_thiet": request.form.get("muc_do_can_thiet"),
        "phuong_an_de_xuat": request.form.get("phuong_an_de_xuat"),
        "ket_luan": request.form.get("ket_luan")
    }
    try:
        cleaned = schemas.xac_thuc_khao_sat(du_lieu_form)
        ms_svc.tao_khao_sat(id, cleaned)
        flash("Đã lập biên bản khảo sát nhu cầu mua sắm BM02 thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/bao-gia", methods=["POST"])
@yeu_cau_vai_tro("mua_sam")
def them_bao_gia(id):
    """Cập nhật báo giá cạnh tranh từ các nhà cung cấp."""
    du_lieu_form = {
        "nha_cung_cap": request.form.get("nha_cung_cap"),
        "ma_so_thue": request.form.get("ma_so_thue"),
        "lien_he": request.form.get("lien_he"),
        "tong_gia": request.form.get("tong_gia"),
        "hieu_luc": request.form.get("hieu_luc"),
        "ghi_chu": request.form.get("ghi_chu")
    }
    try:
        cleaned = schemas.xac_thuc_bao_gia(du_lieu_form)
        ms_svc.them_bao_gia(id, cleaned)
        flash("Đã thêm báo giá cạnh tranh thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/chon-bao-gia/<int:bao_gia_id>", methods=["POST"])
@yeu_cau_vai_tro("mua_sam")
def chon_bao_gia(id, bao_gia_id):
    """Lựa chọn nhà cung cấp trúng thầu."""
    try:
        ms_svc.chon_bao_gia(id, bao_gia_id)
        flash("Đã xác nhận lựa chọn nhà cung cấp trúng thầu!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("mua_sam")
def lap_nghiem_thu(id):
    """Lập biên bản kiểm tra, nghiệm thu hàng hóa trước khi bàn giao cho M09."""
    du_lieu_form = {
        "dai_dien_ben_mua": request.form.get("dai_dien_ben_mua"),
        "dai_dien_nha_cung_cap": request.form.get("dai_dien_nha_cung_cap"),
        "dai_dien_don_vi_su_dung": request.form.get("dai_dien_don_vi_su_dung"),
        "ket_qua": request.form.get("ket_qua", "dat"),
        "y_kien_danh_gia": request.form.get("y_kien_danh_gia")
    }
    try:
        cleaned = schemas.xac_thuc_nghiem_thu(du_lieu_form)
        ms_svc.lap_bien_ban_nghiem_thu(id, cleaned)
        flash("Đã lập biên bản kiểm tra & nghiệm thu hàng hóa thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/de-nghi/<int:id>/de-nghi-thanh-toan", methods=["POST"])
@yeu_cau_vai_tro("mua_sam")
def de_nghi_thanh_toan(id):
    """Lập giấy đề nghị thanh toán chuyển khoản cho nhà cung cấp chuẩn NEU gửi sang Kế toán."""
    du_lieu_form = {
        "noi_dung_thanh_toan": request.form.get("noi_dung_thanh_toan") or request.form.get("ve_khoan"),
        "ve_khoan": request.form.get("ve_khoan") or request.form.get("noi_dung_thanh_toan"),
        "nguoi_de_nghi_ten": request.form.get("nguoi_de_nghi_ten"),
        "don_vi": request.form.get("don_vi"),
        "hop_dong_so": request.form.get("hop_dong_so"),
        "hop_dong_ngay": request.form.get("hop_dong_ngay"),
        "so_tien_bang_chu": request.form.get("so_tien_bang_chu"),
        "don_vi_thu_huong": request.form.get("don_vi_thu_huong"),
        "so_tai_khoan": request.form.get("so_tai_khoan"),
        "ngan_hang": request.form.get("ngan_hang"),
        "ho_so_kem_theo": request.form.get("ho_so_kem_theo"),
        "ghi_chu": request.form.get("ghi_chu")
    }
    try:
        cleaned = schemas.xac_thuc_de_nghi_thanh_toan(du_lieu_form)
        phieu = ms_svc.tao_de_nghi_thanh_toan(id, cleaned, session["nguoi_dung_id"])
        flash(f"Đã lập Giấy đề nghị thanh toán (gửi phiếu thanh toán {phieu['ma_thanh_toan']}) sang trạng thái Chờ thanh toán để Kế toán kiểm tra.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("mua_sam.chi_tiet", id=id))

@mua_sam_bp.route("/ho-so")
@yeu_cau_vai_tro("mua_sam", "quan_tri")
def ho_so():
    """Danh sách hồ sơ mua sắm & hợp đồng."""
    danh_sach_hs = ms_svc.lay_danh_sach_ho_so()
    return render_template("mua_sam/ho_so.html", ho_so_list=danh_sach_hs)
