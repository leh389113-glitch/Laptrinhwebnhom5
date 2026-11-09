from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.services import tai_san as ts_svc
from app.services import auth as auth_svc
from app.services import bao_cao_hu_hai as hh_svc
from app.services import mua_sam as ms_svc
from app.routes import yeu_cau_vai_tro, yeu_cau_dang_nhap
from app import schemas
from app.errors import LoiNghiepVu

tai_san_bp = Blueprint("tai_san", __name__, url_prefix="/tai-san")

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
        danh_sach_nguoi_dung = auth_svc.lay_danh_sach_nguoi_dung()
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

@tai_san_bp.route("/sua-chua/<int:id>/nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def nghiem_thu_sua_chua(id):
    """Nghiệm thu hoàn thành sửa chữa thiết bị, đưa tài sản về trạng thái hoạt động."""
    du_lieu = {
        "chi_phi_thuc_te": request.form.get("chi_phi_thuc_te", 0),
        "ghi_chu": request.form.get("ghi_chu", "")
    }
    try:
        ts_svc.nghiem_thu_sua_chua(id, du_lieu, session["nguoi_dung_id"])
        flash("Nghiệm thu hoàn tất sửa chữa thành công! Tài sản đã hoạt động bình thường.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")

    return redirect(url_for("tai_san.danh_sach_sua_chua"))

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
# LUỒNG XỬ LÝ HƯ HỎNG VÀ MUA SẮM THAY THẾ (YÊU CẦU 1.DOCX - BỘ PHẬN QUẢN LÝ TÀI SẢN)
# =========================================================================

@tai_san_bp.route("/bao-cao-hu-hai")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def danh_sach_hu_hai():
    """
    Bộ phận Quản lý tài sản (Phòng QTTB) tiếp nhận, phân loại và xử lý các sự cố hư hại vật chất
    theo luồng 8 trạng thái chuẩn của M09.
    """
    trang_thai = request.args.get("trang_thai")
    danh_sach = hh_svc.lay_danh_sach_bao_cao(trang_thai=trang_thai)
    return render_template("tai_san/bao_cao_hu_hai.html", bao_cao_list=danh_sach, trang_thai_chon=trang_thai)

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>")
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def chi_tiet_hu_hai(id):
    """
    Xem chi tiết phiếu sự cố hư hại, stepper tiến độ 8 bước và toàn bộ lịch sử:
    Khảo sát BM03, phương án trình duyệt, tiến độ thi công, nghiệm thu.
    """
    bc = hh_svc.lay_chi_tiet_bao_cao(id)
    return render_template("tai_san/bao_cao_hu_hai_chi_tiet.html", bc=bc)

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/tiep-nhan", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tiep_nhan_hu_hai(id):
    """Nút 📥 Tiếp nhận: Phòng QTTB tiếp nhận phiếu, chuyển sang Đang khảo sát."""
    try:
        hh_svc.tiep_nhan_yeu_cau(id, session["nguoi_dung_id"])
        flash("Đã tiếp nhận yêu cầu xử lý sự cố! Bắt đầu chuyển sang bước khảo sát hiện trạng.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.danh_sach_hu_hai"))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/tra-lai", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tra_lai_hu_hai(id):
    """Nút ↩️ Trả lại: Trả lại yêu cầu để đơn vị gửi bổ sung thông tin."""
    ly_do = request.form.get("ly_do_tra_lai", "Thông tin mô tả chưa rõ ràng, đề nghị bổ sung chi tiết.")
    try:
        hh_svc.tra_lai_yeu_cau(id, ly_do, session["nguoi_dung_id"])
        flash(f"Đã trả lại yêu cầu để đơn vị bổ sung thông tin.", "warning")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.danh_sach_hu_hai"))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/khao-sat", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def khao_sat_hu_hai(id):
    """
    Nút 📋 Lập khảo sát (BM03):
    Ghi nhận biên bản khảo sát hiện trạng hư hỏng, nguyên nhân, hình ảnh và phân loại 3 nhóm sửa chữa.
    """
    du_lieu = {
        "thanh_phan_khao_sat": request.form.get("thanh_phan_khao_sat", ""),
        "hien_trang_thuc_te": request.form.get("hien_trang_thuc_te", ""),
        "nguyen_nhan_hu_hong": request.form.get("nguyen_nhan_hu_hong", ""),
        "muc_do_hu_hong": request.form.get("muc_do_hu_hong", "trung_binh"),
        "anh_huong_an_toan": request.form.get("anh_huong_an_toan", ""),
        "khoi_luong_du_kien": request.form.get("khoi_luong_du_kien", ""),
        "nhom_sua_chua": request.form.get("nhom_sua_chua", "sua_chua_thiet_bi"),
        "tinh_trang_bao_hanh": request.form.get("tinh_trang_bao_hanh", "het_bao_hanh"),
        "hinh_anh_khao_sat": request.form.get("hinh_anh_khao_sat", "")
    }
    try:
        hh_svc.lap_khao_sat_bm03(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã lập Biên bản khảo sát hiện trường BM03 thành công! Chuyển sang bước Lập phương án trình duyệt.", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/phuong-an", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def phuong_an_hu_hai(id):
    """Nút 📄 Lập phương án trình duyệt: Nhập phương án xử lý, kinh phí dự kiến và trình lãnh đạo phê duyệt."""
    du_lieu = {
        "phuong_an_chi_tiet": request.form.get("phuong_an_chi_tiet", ""),
        "kinh_phi_du_kien": request.form.get("kinh_phi_du_kien", 0),
        "nguon_kinh_phi_sua_chua": request.form.get("nguon_kinh_phi_sua_chua", "Kinh phí bảo dưỡng thường xuyên"),
        "yeu_cau_m08": request.form.get("yeu_cau_m08", 0)
    }
    try:
        hh_svc.lap_phuong_an_trinh_duyet(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã lập phương án xử lý và dự toán kinh phí trình duyệt!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/phe-duyet-phuong-an", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho", "quan_tri")
def phe_duyet_phuong_an_hu_hai(id):
    """Phê duyệt phương án sửa chữa và kinh phí."""
    du_lieu = {
        "y_kien_lanh_dao": request.form.get("y_kien_lanh_dao", "Đồng ý phê duyệt phương án sửa chữa.")
    }
    try:
        hh_svc.phe_duyet_phuong_an(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã phê duyệt phương án sửa chữa thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/lien-ket-m08", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def lien_ket_m08_hu_hai(id):
    """
    Nút 🔗 Liên kết M08 (Mua sắm):
    Tự động đẩy dữ liệu sang Module M08 để lập hồ sơ mua vật tư / thiết bị thay thế hoặc thuê ngoài.
    """
    try:
        bc = hh_svc.lien_ket_m08_mua_sam(id, session["nguoi_dung_id"])
        flash(f"Đã tự động liên kết và đẩy dữ liệu sang Module M08 mua sắm thành công (Mã gói: {bc.get('ma_de_nghi')})!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/tien-do", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tien_do_hu_hai(id):
    """Nút 📝 Cập nhật tiến độ: Nhập nhật ký thi công và đính kèm hình ảnh trong quá trình đang sửa chữa."""
    du_lieu = {
        "don_vi_thi_cong": request.form.get("don_vi_thi_cong", ""),
        "nhat_ky_thi_cong": request.form.get("nhat_ky_thi_cong", ""),
        "hinh_anh_thi_cong": request.form.get("hinh_anh_thi_cong", "")
    }
    try:
        hh_svc.cap_nhat_tien_do(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã cập nhật nhật ký thi công và tiến độ sửa chữa!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/lap-nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def lap_nghiem_thu_hu_hai(id):
    """Nút 🏁 Lập biên bản nghiệm thu: Khi sửa chữa hoàn thành, tạo phiếu nghiệm thu chuyển sang Chờ nghiệm thu."""
    du_lieu = {
        "ghi_chu": request.form.get("ghi_chu", "")
    }
    try:
        hh_svc.lap_bien_ban_nghiem_thu(id, du_lieu, session["nguoi_dung_id"])
        flash("Đã lập biên bản nghiệm thu kỹ thuật, chuyển sang trạng thái Chờ nghiệm thu kiểm tra thực tế!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/danh-gia-nghiem-thu", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def danh_gia_nghiem_thu_hu_hai(id):
    """Đánh giá nghiệm thu: Đạt yêu cầu (Hoàn tất & Cập nhật tài sản) hoặc Không đạt yêu cầu."""
    ket_qua = request.form.get("ket_qua", "dat")
    y_kien = request.form.get("y_kien_nghiem_thu", "")
    yeu_cau_khac_phuc = request.form.get("yeu_cau_khac_phuc", "")
    try:
        hh_svc.danh_gia_nghiem_thu(id, ket_qua, y_kien, yeu_cau_khac_phuc, session["nguoi_dung_id"])
        if ket_qua == "dat":
            flash("Nghiệm thu ĐẠT! Sự cố đã hoàn tất khắc phục, tài sản đã khôi phục trạng thái hoạt động bình thường.", "success")
        else:
            flash("Kiểm tra nghiệm thu KHÔNG ĐẠT! Đã gửi yêu cầu đơn vị thi công khắc phục lại.", "warning")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/khac-phuc", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def khac_phuc_hu_hai(id):
    """Chuyển phiếu từ Không đạt quay lại Đang sửa chữa để tiếp tục khắc phục."""
    ghi_chu = request.form.get("ghi_chu", "Tiếp tục thi công khắc phục theo yêu cầu nghiệm thu")
    try:
        hh_svc.khac_phuc_lai(id, ghi_chu, session["nguoi_dung_id"])
        flash("Đã chuyển phiếu về trạng thái Đang sửa chữa để khắc phục lại.", "info")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(request.referrer or url_for("tai_san.chi_tiet_hu_hai", id=id))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/xu-ly", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def xu_ly_hu_hai(id):
    """Hàm xử lý tương thích ngược."""
    phuong_an = request.form.get("phuong_an")
    ghi_chu = request.form.get("ghi_chu", "")
    try:
        hh_svc.xac_minh_danh_gia(id, phuong_an, ghi_chu=ghi_chu, nguoi_xu_ly_id=session["nguoi_dung_id"])
        flash("Đã cập nhật kết quả xác minh và phương án xử lý sự cố cơ sở vật chất!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.danh_sach_hu_hai"))

@tai_san_bp.route("/bao-cao-hu-hai/<int:id>/tao-mua-sam", methods=["POST"])
@yeu_cau_vai_tro("quan_ly_kho")
def tao_mua_sam_thay_the(id):
    """Hàm tạo mua sắm thay thế tương thích ngược."""
    try:
        de_nghi = hh_svc.tao_yeu_cau_thay_the_sang_m08(id, session["nguoi_dung_id"])
        flash(f"Đã lập yêu cầu mua sắm thay thế mã {de_nghi['ma_de_nghi']} chuyển sang phân hệ M08 thành công!", "success")
    except LoiNghiepVu as e:
        flash(e.thong_bao, "danger")
    return redirect(url_for("tai_san.danh_sach_hu_hai"))

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
