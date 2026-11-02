from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, abort
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
    tu_khoa = request.args.get("tu_khoa")
    ds_tai_san = ts_svc.lay_danh_sach_tai_san(trang_thai=trang_thai, tu_khoa=tu_khoa)
    return render_template("tai_san/danh_sach.html", tai_san_list=ds_tai_san, trang_thai_chon=trang_thai, tu_khoa=tu_khoa)

@tai_san_bp.route("/cua-toi")
@yeu_cau_dang_nhap
def cua_toi():
    """Hiển thị tài sản được bàn giao và yêu cầu xử lý của người đang đăng nhập."""
    nguoi_dung_id = session["nguoi_dung_id"]
    return render_template(
        "tai_san/cua_toi.html",
        tai_san_list=ts_svc.lay_tai_san_cua_toi(nguoi_dung_id),
        yeu_cau_list=ts_svc.lay_danh_sach_yeu_cau_su_co(nguoi_tao_id=nguoi_dung_id)
    )

@tai_san_bp.route("/<int:id>")
@yeu_cau_dang_nhap
def chi_tiet(id):
    """Xem thông tin chi tiết một tài sản."""
    try:
        tai_san = ts_svc.lay_chi_tiet_tai_san(id)
        vai_tro = session.get("vai_tro")
        co_quyen_quan_ly = vai_tro in ["quan_ly_kho", "quan_tri"]
        if not co_quyen_quan_ly and tai_san["nguoi_su_dung_id"] != session["nguoi_dung_id"]:
            abort(403)
        danh_sach_nguoi_dung = auth_svc.lay_danh_sach_nguoi_dung() if co_quyen_quan_ly else []
        return render_template("tai_san/chi_tiet.html", tai_san=tai_san, nguoi_dung_list=danh_sach_nguoi_dung)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach"))

@tai_san_bp.route("/<int:id>/bao-hong", methods=["POST"])
@yeu_cau_dang_nhap
def tao_yeu_cau_su_co(id):
    """Gửi yêu cầu xử lý hư hại cho tài sản đang được bàn giao."""
    try:
        cleaned = schemas.xac_thuc_yeu_cau_su_co({
            "mo_ta_tinh_trang": request.form.get("mo_ta_tinh_trang"),
            "muc_do": request.form.get("muc_do"),
            "thoi_gian_phat_hien": request.form.get("thoi_gian_phat_hien")
        })
        yeu_cau = ts_svc.tao_yeu_cau_su_co(id, cleaned, session["nguoi_dung_id"])
        flash(f"Đã gửi yêu cầu xử lý {yeu_cau['ma_tai_san']} thành công.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet", id=id))

@tai_san_bp.route("/yeu-cau")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_yeu_cau():
    """Hiển thị hàng đợi yêu cầu xử lý tài sản cho bộ phận phụ trách."""
    trang_thai = request.args.get("trang_thai")
    return render_template(
        "tai_san/yeu_cau.html",
        yeu_cau_list=ts_svc.lay_danh_sach_yeu_cau_su_co(trang_thai=trang_thai),
        trang_thai_chon=trang_thai
    )

@tai_san_bp.route("/yeu-cau/<int:id>")
@yeu_cau_dang_nhap
def chi_tiet_yeu_cau(id):
    """Hiển thị yêu cầu xử lý cùng các thao tác phù hợp với trạng thái."""
    try:
        yeu_cau = ts_svc.lay_chi_tiet_yeu_cau_su_co(id)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach_yeu_cau"))
    if session.get("vai_tro") not in ["quan_ly_kho", "quan_tri"] and session["nguoi_dung_id"] not in [
        yeu_cau["nguoi_tao_id"], yeu_cau["nguoi_duoc_phan_cong_id"]
    ]:
        abort(403)
    return render_template(
        "tai_san/chi_tiet_yeu_cau.html",
        yeu_cau=yeu_cau,
        nguoi_dung_list=auth_svc.lay_danh_sach_nguoi_dung()
    )

@tai_san_bp.route("/yeu-cau/<int:id>/xac-minh", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def xac_minh_yeu_cau(id):
    """Xác minh tình trạng và quyết định sửa chữa hoặc lập đề nghị thay thế."""
    du_lieu_form = {
        "phuong_an": request.form.get("phuong_an"),
        "ket_qua_xac_minh": request.form.get("ket_qua_xac_minh"),
        "ten_hang_thay_the": request.form.get("ten_hang_thay_the"),
        "don_vi_tinh": request.form.get("don_vi_tinh"),
        "don_vi_de_nghi": request.form.get("don_vi_de_nghi"),
        "so_luong": request.form.get("so_luong"),
        "don_gia_du_kien": request.form.get("don_gia_du_kien")
    }
    try:
        cleaned = schemas.xac_thuc_xac_minh_su_co(du_lieu_form)
        ket_qua = ts_svc.xac_minh_yeu_cau_su_co(id, cleaned, session["nguoi_dung_id"])
        if cleaned["phuong_an"] == "thay_the":
            flash(f"Đã lập đề nghị thay thế {ket_qua['ma_de_nghi']} và chuyển sang M08.", "success")
        else:
            flash("Đã xác minh và chuyển yêu cầu sang bước phân công sửa chữa.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_yeu_cau", id=id))

@tai_san_bp.route("/yeu-cau/<int:id>/phan-cong", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def phan_cong_yeu_cau(id):
    """Phân công người thực hiện sửa chữa."""
    try:
        cleaned = schemas.xac_thuc_phan_cong_su_co({
            "nguoi_duoc_phan_cong_id": request.form.get("nguoi_duoc_phan_cong_id")
        })
        ts_svc.phan_cong_yeu_cau_su_co(
            id, cleaned["nguoi_duoc_phan_cong_id"], session["nguoi_dung_id"]
        )
        flash("Đã phân công xử lý yêu cầu sửa chữa.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_yeu_cau", id=id))

@tai_san_bp.route("/yeu-cau/<int:id>/bat-dau", methods=["POST"])
@yeu_cau_dang_nhap
def bat_dau_sua_chua(id):
    """Cho phép người được phân công bắt đầu sửa chữa."""
    try:
        ts_svc.bat_dau_sua_chua(id, session["nguoi_dung_id"])
        flash("Đã chuyển yêu cầu sang trạng thái đang sửa chữa.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_yeu_cau", id=id))

@tai_san_bp.route("/yeu-cau/<int:id>/hoan-thanh", methods=["POST"])
@yeu_cau_dang_nhap
def hoan_thanh_sua_chua(id):
    """Ghi nhận công việc đã thực hiện và chờ bộ phận quản lý kiểm tra."""
    try:
        cleaned = schemas.xac_thuc_ket_qua_sua_chua({
            "noi_dung_thuc_hien": request.form.get("noi_dung_thuc_hien"),
            "don_vi_thuc_hien": request.form.get("don_vi_thuc_hien"),
            "chi_phi": request.form.get("chi_phi"),
            "ghi_chu": request.form.get("ghi_chu")
        })
        ts_svc.hoan_tat_sua_chua(id, cleaned, session["nguoi_dung_id"])
        flash("Đã ghi nhận kết quả và chuyển sang bước kiểm tra.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_yeu_cau", id=id))

@tai_san_bp.route("/yeu-cau/<int:id>/kiem-tra", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def kiem_tra_sua_chua(id):
    """Kiểm tra sửa chữa và cập nhật trạng thái tài sản."""
    try:
        cleaned = schemas.xac_thuc_kiem_tra_su_co({
            "ket_qua_kiem_tra": request.form.get("ket_qua_kiem_tra"),
            "ghi_chu": request.form.get("ghi_chu")
        })
        ts_svc.kiem_tra_sua_chua(id, cleaned, session["nguoi_dung_id"])
        if cleaned["ket_qua_kiem_tra"] == "dat":
            flash("Kiểm tra đạt; tài sản đã được cập nhật và ghi nhận lịch sử sửa chữa.", "success")
        else:
            flash("Kết quả chưa đạt; yêu cầu đã được chuyển lại để tiếp tục sửa chữa.", "warning")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_yeu_cau", id=id))

@tai_san_bp.route("/bao-cao-cong-khai")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def bao_cao_cong_khai():
    """Hiển thị phản ánh công khai để đối chiếu với tài sản trường."""
    return render_template(
        "tai_san/bao_cao_cong_khai.html",
        bao_cao_list=hh_svc.lay_danh_sach_bao_cao(),
        tai_san_list=ts_svc.lay_tai_san_cong_khai()
    )

@tai_san_bp.route("/bao-cao-cong-khai/<int:id>/tao-yeu-cau", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def tao_yeu_cau_tu_bao_cao(id):
    """Đối chiếu phản ánh công khai với tài sản rồi chuyển sang hàng đợi nội bộ."""
    try:
        cleaned = schemas.xac_thuc_doi_chieu_tai_san({
            "tai_san_id": request.form.get("tai_san_id")
        })
        hh_svc.tao_yeu_cau_tu_bao_cao(id, cleaned["tai_san_id"], session["nguoi_dung_id"])
        flash("Đã đối chiếu và chuyển phản ánh thành yêu cầu xử lý nội bộ.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.bao_cao_cong_khai"))

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
