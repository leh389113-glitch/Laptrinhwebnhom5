from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from app.services import tai_san as ts_svc
from app.services import mua_sam as ms_svc
from app.routes import yeu_cau_vai_tro, yeu_cau_dang_nhap
from app import schemas, clock
from app.errors import LoiNghiepVu

tai_san_bp = Blueprint("tai_san", __name__, url_prefix="/tai-san")

def _anh_dinh_kem():
    """Đọc tối đa 5 ảnh PNG/JPEG/WebP, giới hạn 5 MB mỗi ảnh."""
    anh_list = []
    for tep in request.files.getlist("hinh_anh"):
        if not tep or not tep.filename:
            continue
        if len(anh_list) >= 5:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mỗi thao tác chỉ được đính kèm tối đa 5 ảnh.")
        ten_tep = secure_filename(tep.filename)
        noi_dung = tep.read(5 * 1024 * 1024 + 1)
        if len(noi_dung) > 5 * 1024 * 1024:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mỗi ảnh không được vượt quá 5 MB.")
        if ten_tep.lower().endswith(".png") and noi_dung.startswith(b"\x89PNG\r\n\x1a\n"):
            mime_type = "image/png"
        elif ten_tep.lower().endswith((".jpg", ".jpeg")) and noi_dung.startswith(b"\xff\xd8\xff"):
            mime_type = "image/jpeg"
        elif (ten_tep.lower().endswith(".webp") and len(noi_dung) >= 12
              and noi_dung[:4] == b"RIFF" and noi_dung[8:12] == b"WEBP"):
            mime_type = "image/webp"
        else:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Chỉ chấp nhận ảnh PNG, JPEG hoặc WebP hợp lệ.")
        anh_list.append({"ten_tep": ten_tep, "mime_type": mime_type, "noi_dung": noi_dung})
    return anh_list

def _tai_lieu_thanh_toan_dinh_kem():
    """Đọc tối đa 5 tệp PDF hoặc ảnh, giới hạn 10 MB mỗi tệp."""
    tep_list = []
    for tep in request.files.getlist("tai_lieu"):
        if not tep or not tep.filename:
            continue
        if len(tep_list) >= 5:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mỗi lần chỉ được đính kèm tối đa 5 tài liệu.")
        ten_tep = secure_filename(tep.filename)
        noi_dung = tep.read(10 * 1024 * 1024 + 1)
        if len(noi_dung) > 10 * 1024 * 1024:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mỗi tài liệu không được vượt quá 10 MB.")
        duoi_tep = ten_tep.lower()
        if duoi_tep.endswith(".pdf") and noi_dung.startswith(b"%PDF-"):
            mime_type = "application/pdf"
        elif duoi_tep.endswith(".png") and noi_dung.startswith(b"\x89PNG\r\n\x1a\n"):
            mime_type = "image/png"
        elif duoi_tep.endswith((".jpg", ".jpeg")) and noi_dung.startswith(b"\xff\xd8\xff"):
            mime_type = "image/jpeg"
        elif (duoi_tep.endswith(".webp") and len(noi_dung) >= 12
              and noi_dung[:4] == b"RIFF" and noi_dung[8:12] == b"WEBP"):
            mime_type = "image/webp"
        else:
            raise LoiNghiepVu(
                "DU_LIEU_DAU_VAO_KHONG_HOP_LE",
                "Tài liệu phải là PDF hoặc ảnh PNG, JPEG, WebP hợp lệ."
            )
        tep_list.append({"ten_tep": ten_tep, "mime_type": mime_type, "noi_dung": noi_dung})
    return tep_list

@tai_san_bp.route("/")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach():
    """Xem toàn bộ danh sách tài sản cơ sở vật chất (Bộ phận Quản lý tài sản / Admin)."""
    trang_thai = request.args.get("trang_thai")
    phan_loai = request.args.get("phan_loai")
    tinh_trang_ky_thuat = request.args.get("tinh_trang_ky_thuat")
    tu_khoa = request.args.get("tu_khoa")

    ds_tai_san = ts_svc.lay_danh_sach_tai_san(
        trang_thai=trang_thai,
        tu_khoa=tu_khoa,
        phan_loai=phan_loai,
        tinh_trang_ky_thuat=tinh_trang_ky_thuat
    )
    return render_template(
        "tai_san/danh_sach.html",
        tai_san_list=ds_tai_san,
        trang_thai_chon=trang_thai,
        phan_loai_chon=phan_loai,
        tinh_trang_chon=tinh_trang_ky_thuat,
        tu_khoa=tu_khoa
    )

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
        danh_sach_nguoi_dung = ts_svc.lay_danh_sach_nguoi_nhan_ban_giao(id)
        return render_template("tai_san/chi_tiet.html", tai_san=tai_san, nguoi_dung_list=danh_sach_nguoi_dung)
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach"))

@tai_san_bp.route("/<int:id>/chinh-sua", methods=["GET", "POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def chinh_sua(id):
    """Chỉnh sửa thông tin tài sản (chuyên trách do Bộ phận Quản lý tài sản thực hiện)."""
    tai_san = ts_svc.lay_chi_tiet_tai_san(id)
    if request.method == "POST":
        du_lieu_form = {
            "ten_tai_san": request.form.get("ten_tai_san"),
            "loai_tai_san": request.form.get("loai_tai_san"),
            "phan_loai": request.form.get("phan_loai"),
            "tinh_trang_ky_thuat": request.form.get("tinh_trang_ky_thuat"),
            "vi_tri": request.form.get("vi_tri"),
            "phong_ban": request.form.get("phong_ban"),
            "don_vi_su_dung": request.form.get("don_vi_su_dung"),
            "mo_ta": request.form.get("mo_ta"),
            "gia_tri": request.form.get("gia_tri"),
            "so_serial": request.form.get("so_serial"),
            "model": request.form.get("model"),
            "hang_san_xuat": request.form.get("hang_san_xuat"),
            "thoi_han_bao_hanh": request.form.get("thoi_han_bao_hanh")
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
@yeu_cau_vai_tro("quan_ly_kho")
def ban_giao(id):
    """Bàn giao tài sản cho cán bộ / phòng ban sử dụng (chuyên trách do Bộ phận Quản lý tài sản thực hiện)."""
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
@yeu_cau_vai_tro("quan_ly_kho")
def bao_tri(id):
    """Ghi nhận hoạt động bảo trì, sửa chữa tài sản (Bộ phận Quản lý tài sản thực hiện)."""
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

# =========================================================================
# QUY TRÌNH SỬA CHỮA M09 (PHẦN III CỦA QUY TRÌNH & YÊU CẦU 1)
# =========================================================================

@tai_san_bp.route("/sua-chua")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_sua_chua():
    """Xem danh sách các yêu cầu sửa chữa cơ sở vật chất tại M09."""
    trang_thai = request.args.get("trang_thai")
    ds = ts_svc.lay_danh_sach_sua_chua(trang_thai=trang_thai)
    return render_template("tai_san/sua_chua.html", sua_chua_list=ds, trang_thai_chon=trang_thai)

@tai_san_bp.route("/sua-chua/<int:id>")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def chi_tiet_sua_chua(id):
    try:
        yc = ts_svc.lay_chi_tiet_sua_chua(id)
        ho_so_thanh_toan = ts_svc.lay_ho_so_thanh_toan_sua_chua(id)
        return render_template(
            "tai_san/sua_chua_chi_tiet.html",
            yc=yc,
            ho_so_thanh_toan=ho_so_thanh_toan
        )
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.danh_sach_sua_chua"))

@tai_san_bp.route("/sua-chua/<int:id>/tiep-nhan", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tiep_nhan_sua_chua(id):
    chap_nhan = request.form.get("hanh_dong") == "tiep_nhan"
    noi_dung = request.form.get("noi_dung", "").strip()
    try:
        ts_svc.tiep_nhan_yeu_cau_sua_chua(id, session["nguoi_dung_id"], chap_nhan, noi_dung)
        flash("Đã tiếp nhận yêu cầu." if chap_nhan else "Đã trả yêu cầu về đơn vị để bổ sung thông tin.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/khao-sat", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def khao_sat_sua_chua(id):
    du_lieu = {
        "thanh_phan_khao_sat": request.form.get("thanh_phan_khao_sat", "").strip(),
        "phan_loai_yeu_cau": request.form.get("phan_loai_yeu_cau", "").strip(),
        "hien_trang": request.form.get("hien_trang", "").strip(),
        "nguyen_nhan_du_kien": request.form.get("nguyen_nhan_du_kien", "").strip(),
        "muc_do_hu_hong": request.form.get("muc_do_hu_hong", "").strip(),
        "anh_huong_an_toan": request.form.get("anh_huong_an_toan", "").strip(),
        "khoi_luong_cong_viec": request.form.get("khoi_luong_cong_viec", "").strip(),
        "tinh_trang_bao_hanh": request.form.get("tinh_trang_bao_hanh", "").strip(),
    }
    try:
        ts_svc.cap_nhat_khao_sat_sua_chua(id, du_lieu, session["nguoi_dung_id"], _anh_dinh_kem())
        flash("Đã lưu biên bản khảo sát BM03.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/khao-sat/bat-dau", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def bat_dau_khao_sat_sua_chua(id):
    try:
        ts_svc.bat_dau_khao_sat_sua_chua(id, session["nguoi_dung_id"])
        flash("Đã chuyển yêu cầu sang trạng thái đang khảo sát.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/phuong-an", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def trinh_phuong_an_sua_chua(id):
    du_lieu = {
        "phuong_an": request.form.get("phuong_an", "").strip(),
        "phuong_an_chi_tiet": request.form.get("phuong_an_chi_tiet", "").strip(),
        "chi_phi_du_kien": request.form.get("chi_phi_du_kien", "0"),
        "can_mua_sam": request.form.get("can_mua_sam") == "1",
    }
    try:
        ts_svc.trinh_phuong_an_sua_chua(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã trình phương án sửa chữa để Lãnh đạo phê duyệt.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/phe-duyet-phuong-an", methods=["POST"])
@yeu_cau_vai_tro("quan_tri")
def phe_duyet_phuong_an_sua_chua(id):
    try:
        ts_svc.phe_duyet_phuong_an_sua_chua(
            id, session["nguoi_dung_id"], session.get("vai_tro"),
            request.form.get("ghi_chu", "").strip()
        )
        flash("Đã phê duyệt phương án sửa chữa.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/lien-ket-m08", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def lien_ket_m08_sua_chua(id):
    try:
        de_nghi = ts_svc.tao_de_nghi_mua_sam_tu_sua_chua(id, session["nguoi_dung_id"])
        flash(f"Đã chuyển nhu cầu sang M08 với mã {de_nghi['ma_de_nghi']}.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/bat-dau", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def bat_dau_sua_chua(id):
    try:
        ts_svc.bat_dau_sua_chua(id, session["nguoi_dung_id"])
        flash("Đã cập nhật trạng thái đang sửa chữa.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/tien-do", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def cap_nhat_tien_do_sua_chua(id):
    try:
        ts_svc.ghi_nhat_ky_sua_chua(
            id, request.form.get("noi_dung", ""), session["nguoi_dung_id"], _anh_dinh_kem()
        )
        flash("Đã lưu nhật ký thi công.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def nghiem_thu_sua_chua(id):
    """QTTB lập biên bản, chuyển phiếu sang chờ đơn vị nghiệm thu."""
    du_lieu = {
        "chi_phi_thuc_te": request.form.get("chi_phi_thuc_te", 0),
        "ghi_chu": request.form.get("ghi_chu", "")
    }
    try:
        ts_svc.nghiem_thu_sua_chua(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã lập biên bản nghiệm thu; phiếu đang chờ đơn vị xác nhận.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/<int:id>/ho-so-thanh-toan", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def luu_ho_so_thanh_toan_sua_chua(id):
    du_lieu = {
        "nguoi_de_nghi_ten": request.form.get("nguoi_de_nghi_ten", ""),
        "don_vi": request.form.get("don_vi", ""),
        "ve_khoan": request.form.get("ve_khoan", ""),
        "hop_dong_so": request.form.get("hop_dong_so", ""),
        "hop_dong_ngay": request.form.get("hop_dong_ngay", ""),
        "so_tien": request.form.get("so_tien", ""),
        "so_tien_bang_chu": request.form.get("so_tien_bang_chu", ""),
        "don_vi_thu_huong": request.form.get("don_vi_thu_huong", ""),
        "so_tai_khoan": request.form.get("so_tai_khoan", ""),
        "ngan_hang": request.form.get("ngan_hang", ""),
        "ho_so_kem_theo": request.form.getlist("ho_so_kem_theo"),
        "ho_so_khac": request.form.get("ho_so_khac", "")
    }
    gui = request.form.get("hanh_dong") == "gui"
    try:
        ts_svc.luu_ho_so_thanh_toan_sua_chua(
            id, du_lieu, session["nguoi_dung_id"], gui=gui,
            tep_dinh_kem=_tai_lieu_thanh_toan_dinh_kem()
        )
        flash(
            "Đã gửi hồ sơ thanh toán sang Kế toán."
            if gui else "Đã lưu hồ sơ thanh toán nháp.",
            "success"
        )
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/ho-so-thanh-toan/tep/<int:id>")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri", "ke_toan")
def xem_tep_ho_so_thanh_toan_sua_chua(id):
    try:
        tep = ts_svc.lay_tep_ho_so_thanh_toan_sua_chua(id)
        response = send_file(
            BytesIO(tep["noi_dung"]), mimetype=tep["mime_type"],
            download_name=tep["ten_tep"], as_attachment=False
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    except LoiNghiepVu as e:
        return jsonify({"loi": e.ma_loi, "thong_bao": e.thong_bao}), 404

@tai_san_bp.route("/sua-chua/<int:id>/ho-so-thanh-toan/in")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri", "ke_toan")
def in_ho_so_thanh_toan_sua_chua(id):
    try:
        yc = ts_svc.lay_chi_tiet_sua_chua(id)
        ho_so = ts_svc.lay_ho_so_thanh_toan_sua_chua(id)
        if not ho_so:
            raise LoiNghiepVu("KHONG_CO_DE_NGHI_THANH_TOAN", "Yêu cầu chưa có hồ sơ thanh toán.")
        return render_template(
            "tai_san/giay_de_nghi_thanh_toan_sua_chua.html",
            yc=yc,
            ho_so=ho_so,
            ngay_in=clock.now()
        )
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
        return redirect(url_for("tai_san.chi_tiet_sua_chua", id=id))

@tai_san_bp.route("/sua-chua/tep/<int:id>")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri", "don_vi", "ke_toan")
def xem_tep_sua_chua(id):
    try:
        tep = ts_svc.lay_tep_sua_chua(id)
        if session.get("vai_tro") == "don_vi":
            if tep["nguoi_tao_id"] != session["nguoi_dung_id"] and tep["don_vi"] != session.get("don_vi"):
                return render_template("errors/403.html", thong_bao="Bạn không có quyền xem ảnh này."), 403
        response = send_file(
            BytesIO(tep["noi_dung"]), mimetype=tep["mime_type"],
            download_name=tep["ten_tep"], as_attachment=False
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response
    except LoiNghiepVu as e:
        return jsonify({"loi": e.ma_loi, "thong_bao": e.thong_bao}), 404

# =========================================================================
# KIỂM KÊ TÀI SẢN
# =========================================================================

@tai_san_bp.route("/kiem-ke")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def kiem_ke():
    """Danh sách các đợt kiểm kê tài sản định kỳ."""
    ds_kiem_ke = ts_svc.lay_danh_sach_kiem_ke()
    tai_san_list = ts_svc.lay_danh_sach_tai_san()
    return render_template("tai_san/kiem_ke.html", kiem_ke_list=ds_kiem_ke, tai_san_list=tai_san_list)

@tai_san_bp.route("/kiem-ke/tao", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tao_kiem_ke():
    """Tạo phiếu kiểm kê mới (Bộ phận Quản lý tài sản)."""
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

# =========================================================================
# TIẾP NHẬN TÀI SẢN MỚI TỪ MUA SẮM (QUY TRÌNH M08 -> M09)
# =========================================================================

@tai_san_bp.route("/tiep-nhan")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_tiep_nhan():
    """
    Chức năng 'Tiếp nhận tài sản mới từ Mua sắm' trong Phân hệ M09.
    ** Chỉ hiển thị đề nghị đã nghiệm thu đạt, đủ điều kiện tiếp nhận vào kho M09.
    """
    trang_thai = request.args.get("trang_thai")
    ds_tiep_nhan = ts_svc.lay_danh_sach_de_nghi_cho_tiep_nhan(trang_thai=trang_thai)
    return render_template("tai_san/tiep_nhan_danh_sach.html", de_nghi_list=ds_tiep_nhan, trang_thai_chon=trang_thai)

@tai_san_bp.route("/tiep-nhan/<int:id>", methods=["GET", "POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tiep_nhan_don_hang(id):
    """
    Bộ phận Quản lý tài sản kiểm tra nghiệm thu kỹ thuật và tiếp nhận nhập kho M09.
    Tự động sinh mã tài sản TSCĐ hoặc CCDC và cập nhật trạng thái gói mua sắm thành 'da_nhan'.
    Chỉ cho phép tiếp nhận đề nghị đã nghiệm thu đạt.
    """
    de_nghi = ms_svc.lay_chi_tiet_de_nghi(id)
    if not de_nghi.get("da_nghiem_thu") or not de_nghi.get("nghiem_thu") or de_nghi["nghiem_thu"].get("ket_qua") != "dat":
        flash("Gói mua sắm chưa có Biên bản nghiệm thu kỹ thuật (BM04) đạt yêu cầu. Chưa đủ điều kiện tiếp nhận vào kho M09.", "danger")
        return redirect(url_for("tai_san.danh_sach_tiep_nhan"))

    if request.method == "POST":
        du_lieu = {
            "ghi_chu": request.form.get("ghi_chu", "")
        }
        try:
            ms_svc.tiep_nhan_hang_hoa(id, du_lieu, session["nguoi_dung_id"])
            flash(f"Tiếp nhận hàng hóa thành công! Các tài sản đã được cấp mã và lưu vào sổ tài sản M09.", "success")
            return redirect(url_for("tai_san.danh_sach"))
        except LoiNghiepVu as e:
            flash(e.thong_bao, "danger")

    return render_template("tai_san/tiep_nhan.html", de_nghi=de_nghi)
