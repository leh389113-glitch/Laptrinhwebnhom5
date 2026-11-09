import re
from typing import Tuple, Dict, Any, Optional, List
from app.errors import LoiNghiepVu

def xac_thuc_dang_ky(data: Dict[str, Any]) -> Dict[str, Any]:
    ho_ten = (data.get("ho_ten") or "").strip()
    email = (data.get("email") or "").strip().lower()
    ten_dang_nhap = (data.get("ten_dang_nhap") or "").strip()
    mat_khau = data.get("mat_khau") or ""
    xac_nhan_mat_khau = data.get("xac_nhan_mat_khau") or ""
    vai_tro = (data.get("vai_tro") or "don_vi").strip()
    don_vi = (data.get("don_vi") or "Đơn vị đào tạo").strip()
    so_dien_thoai = (data.get("so_dien_thoai") or "").strip()

    if not ho_ten or len(ho_ten) < 2:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Họ tên phải từ 2 ký tự trở lên.")
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Địa chỉ email không hợp lệ.")
    if not ten_dang_nhap or len(ten_dang_nhap) < 3:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tên đăng nhập phải có ít nhất 3 ký tự.")
    if not mat_khau or len(mat_khau) < 6:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mật khẩu phải từ 6 ký tự trở lên.")
    if mat_khau != xac_nhan_mat_khau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Mật khẩu xác nhận không khớp.")

    if vai_tro not in ["don_vi", "mua_sam", "quan_ly_kho", "ke_toan", "quan_tri"]:
        vai_tro = "don_vi"

    return {
        "ho_ten": ho_ten,
        "email": email,
        "ten_dang_nhap": ten_dang_nhap,
        "mat_khau": mat_khau,
        "vai_tro": vai_tro,
        "don_vi": don_vi,
        "so_dien_thoai": so_dien_thoai
    }

def xac_thuc_dang_nhap(data: Dict[str, Any]) -> Dict[str, Any]:
    ten_dang_nhap = (data.get("ten_dang_nhap") or "").strip()
    mat_khau = data.get("mat_khau") or ""

    if not ten_dang_nhap or not mat_khau:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")

    return {
        "ten_dang_nhap": ten_dang_nhap,
        "mat_khau": mat_khau
    }

def xac_thuc_bao_cao_hu_hai(data: Dict[str, Any]) -> Dict[str, Any]:
    ho_ten = (data.get("ho_ten") or "").strip()
    lien_he = (data.get("lien_he") or "").strip()
    ten_vat_chat = (data.get("ten_vat_chat") or "").strip()
    vi_tri = (data.get("vi_tri") or "").strip()
    muc_do = (data.get("muc_do") or "trung_binh").strip().lower()
    mo_ta_chi_tiet = (data.get("mo_ta_chi_tiet") or "").strip()
    thoi_gian_phat_hien = (data.get("thoi_gian_phat_hien") or "").strip()

    if not ho_ten:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Họ tên người báo cáo không được để trống.")
    if not lien_he:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số điện thoại hoặc email liên hệ không được để trống.")
    if not ten_vat_chat:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tên / mô tả vật chất bị hư hại không được để trống.")
    if not vi_tri:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vị trí xảy ra hư hại không được để trống.")
    if muc_do not in ["nhe", "trung_binh", "nghiem_trong"]:
        muc_do = "trung_binh"

    return {
        "ho_ten": ho_ten,
        "lien_he": lien_he,
        "ten_vat_chat": ten_vat_chat,
        "vi_tri": vi_tri,
        "muc_do": muc_do,
        "mo_ta_chi_tiet": mo_ta_chi_tiet,
        "thoi_gian_phat_hien": thoi_gian_phat_hien
    }

def xac_thuc_de_nghi_mua_sam(data: Dict[str, Any]) -> Dict[str, Any]:
    tieu_de = (data.get("tieu_de") or "").strip()
    don_vi_de_nghi = (data.get("don_vi_de_nghi") or "").strip()
    mo_ta = (data.get("mo_ta") or "").strip()
    muc_do_uu_tien = (data.get("muc_do_uu_tien") or "binh_thuong").strip()
    nguon_kinh_phi = (data.get("nguon_kinh_phi") or "Nguồn thu hợp pháp của Trường").strip()
    thoi_gian_can_hang = (data.get("thoi_gian_can_hang") or "").strip()
    dia_diem_su_dung = (data.get("dia_diem_su_dung") or "").strip()
    ly_do_su_can_thiet = (data.get("ly_do_su_can_thiet") or "").strip()
    nguon_goc = (data.get("nguon_goc") or "moi").strip()
    bao_cao_hu_hai_id = data.get("bao_cao_hu_hai_id")

    if not tieu_de:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tiêu đề đề nghị mua sắm không được để trống.")
    if not don_vi_de_nghi:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Đơn vị đề nghị không được để trống.")

    items_raw = data.get("items") or []
    if not items_raw:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Đề nghị phải có ít nhất một hạng mục hàng hóa.")

    cleaned_items = []
    tong_du_toan = 0.0
    for idx, item in enumerate(items_raw, 1):
        ten_hang = (item.get("ten_hang_hoa") or "").strip()
        don_vi_tinh = (item.get("don_vi_tinh") or "").strip() or "Cái"
        try:
            so_luong = int(item.get("so_luong", 0))
            don_gia = float(item.get("don_gia_du_kien", 0))
        except (ValueError, TypeError):
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", f"Số lượng hoặc đơn giá hạng mục #{idx} không hợp lệ.")

        if not ten_hang:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", f"Hạng mục #{idx} thiếu tên hàng hóa.")
        if so_luong <= 0:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", f"Số lượng hạng mục #{idx} phải lớn hơn 0.")
        if don_gia < 0:
            raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", f"Đơn giá hạng mục #{idx} không được âm.")

        thanh_tien = so_luong * don_gia
        tong_du_toan += thanh_tien
        cleaned_items.append({
            "ten_hang_hoa": ten_hang,
            "don_vi_tinh": don_vi_tinh,
            "so_luong": so_luong,
            "don_gia_du_kien": don_gia,
            "thanh_tien": thanh_tien,
            "vi_tri_su_dung": (item.get("vi_tri_su_dung") or "").strip(),
            "ly_do_muc_dich": (item.get("ly_do_muc_dich") or "").strip(),
            "ghi_chu": (item.get("ghi_chu") or "").strip()
        })

    return {
        "tieu_de": tieu_de,
        "don_vi_de_nghi": don_vi_de_nghi,
        "mo_ta": mo_ta,
        "tong_du_toan": tong_du_toan,
        "items": cleaned_items,
        "muc_do_uu_tien": muc_do_uu_tien,
        "nguon_kinh_phi": nguon_kinh_phi,
        "thoi_gian_can_hang": thoi_gian_can_hang,
        "dia_diem_su_dung": dia_diem_su_dung,
        "ly_do_su_can_thiet": ly_do_su_can_thiet,
        "nguon_goc": nguon_goc,
        "bao_cao_hu_hai_id": int(bao_cao_hu_hai_id) if bao_cao_hu_hai_id else None
    }

def xac_thuc_khao_sat(data: Dict[str, Any]) -> Dict[str, Any]:
    noi_dung = (data.get("noi_dung") or "").strip()
    dia_diem = (data.get("dia_diem") or "").strip()
    can_bo_khao_sat = (data.get("can_bo_khao_sat") or "").strip()
    dai_dien_don_vi = (data.get("dai_dien_don_vi") or "").strip()
    ket_qua_danh_gia = (data.get("ket_qua_danh_gia") or "").strip()
    kiem_tra_kho = (data.get("kiem_tra_kho") or "Khô không còn vật tư đáp ứng").strip()
    doi_chieu_dinh_muc = (data.get("doi_chieu_dinh_muc") or "Phù hợp định mức").strip()
    muc_do_can_thiet = (data.get("muc_do_can_thiet") or "can_thiet").strip()
    phuong_an_de_xuat = (data.get("phuong_an_de_xuat") or "mua_bo_sung").strip()
    ket_luan = (data.get("ket_luan") or "phu_hop").strip()

    if not noi_dung:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Nội dung khảo sát không được để trống.")
    if ket_luan not in (
        "phu_hop",
        "chua_du",
        "Phù hợp và cần thiết để tổ chức thực hiện",
        "Chưa đủ cơ sở để tổ chức thực hiện"
    ):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kết luận khảo sát chỉ chấp nhận 'phù hợp và cần thiết để tổ chức thực hiện' hoặc 'chưa đủ cơ sở để tổ chức thực hiện'.")

    return {
        "noi_dung": noi_dung,
        "dia_diem": dia_diem,
        "can_bo_khao_sat": can_bo_khao_sat,
        "dai_dien_don_vi": dai_dien_don_vi,
        "ket_qua_danh_gia": ket_qua_danh_gia,
        "kiem_tra_kho": kiem_tra_kho,
        "doi_chieu_dinh_muc": doi_chieu_dinh_muc,
        "muc_do_can_thiet": muc_do_can_thiet,
        "phuong_an_de_xuat": phuong_an_de_xuat,
        "ket_luan": ket_luan
    }

def xac_thuc_bao_gia(data: Dict[str, Any]) -> Dict[str, Any]:
    nha_cung_cap = (data.get("nha_cung_cap") or "").strip()
    if not nha_cung_cap:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tên nhà cung cấp không được để trống.")
    
    try:
        tong_gia = float(data.get("tong_gia", 0))
    except (ValueError, TypeError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tổng giá báo giá không hợp lệ.")

    if tong_gia <= 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tổng giá báo giá phải lớn hơn 0.")

    return {
        "nha_cung_cap": nha_cung_cap,
        "ma_so_thue": (data.get("ma_so_thue") or "").strip(),
        "lien_he": (data.get("lien_he") or "").strip(),
        "tong_gia": tong_gia,
        "hieu_luc": (data.get("hieu_luc") or "30 ngày").strip(),
        "ghi_chu": (data.get("ghi_chu") or "").strip()
    }

def xac_thuc_nghiem_thu(data: Dict[str, Any]) -> Dict[str, Any]:
    dai_dien_ben_mua = (data.get("dai_dien_ben_mua") or "").strip()
    dai_dien_nha_cung_cap = (data.get("dai_dien_nha_cung_cap") or "").strip()
    dai_dien_don_vi_su_dung = (data.get("dai_dien_don_vi_su_dung") or "").strip()
    ket_qua = (data.get("ket_qua") or "dat").strip()
    y_kien_danh_gia = (data.get("y_kien_danh_gia") or "").strip()
    if ket_qua not in ("dat", "khong_dat"):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Kết quả nghiệm thu không hợp lệ.")

    return {
        "dai_dien_ben_mua": dai_dien_ben_mua,
        "dai_dien_nha_cung_cap": dai_dien_nha_cung_cap,
        "dai_dien_don_vi_su_dung": dai_dien_don_vi_su_dung,
        "ket_qua": ket_qua,
        "y_kien_danh_gia": y_kien_danh_gia
    }

def xac_thuc_tiep_nhan(data: Dict[str, Any]) -> Dict[str, Any]:
    nha_cung_cap = (data.get("nha_cung_cap") or "").strip()
    so_hop_dong = (data.get("so_hop_dong") or "").strip()
    ghi_chu = (data.get("ghi_chu") or "").strip()
    items = data.get("items") or []

    return {
        "nha_cung_cap": nha_cung_cap,
        "so_hop_dong": so_hop_dong,
        "ghi_chu": ghi_chu,
        "items": items
    }

def xac_thuc_thanh_toan(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        so_tien = float(data.get("so_tien", 0))
    except (ValueError, TypeError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số tiền thanh toán không hợp lệ.")

    if so_tien <= 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Số tiền thanh toán phải lớn hơn 0.")

    so_hoa_don = (data.get("so_hoa_don") or "").strip()
    phuong_thuc = (data.get("phuong_thuc") or "chuyen_khoan").strip()
    ghi_chu = (data.get("ghi_chu") or "").strip()
    if not so_hoa_don:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Cần nhập số hóa đơn hoặc chứng từ thanh toán.")

    return {
        "so_tien": so_tien,
        "so_hoa_don": so_hoa_don,
        "phuong_thuc": phuong_thuc,
        "ghi_chu": ghi_chu
    }

def xac_thuc_de_nghi_thanh_toan(data: Dict[str, Any]) -> Dict[str, Any]:
    noi_dung = (data.get("noi_dung_thanh_toan") or "").strip()
    if not noi_dung:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Nội dung đề nghị thanh toán không được để trống.")
    try:
        gia_tri = float(data.get("gia_tri_de_nghi", 0)) if data.get("gia_tri_de_nghi") else 0
    except (ValueError, TypeError) as exc:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Giá trị đề nghị thanh toán không hợp lệ.") from exc
    if gia_tri < 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Giá trị đề nghị thanh toán không được âm.")

    return {
        "noi_dung_thanh_toan": noi_dung,
        "gia_tri_de_nghi": gia_tri,
        "ghi_chu": (data.get("ghi_chu") or "").strip()
    }

def xac_thuc_tai_san(data: Dict[str, Any]) -> Dict[str, Any]:
    ten_tai_san = (data.get("ten_tai_san") or "").strip()
    if not ten_tai_san:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tên tài sản không được để trống.")

    loai_tai_san = (data.get("loai_tai_san") or "").strip()
    phan_loai = (data.get("phan_loai") or "tai_san_co_dinh").strip()
    tinh_trang_ky_thuat = (data.get("tinh_trang_ky_thuat") or "binh_thuong").strip()
    vi_tri = (data.get("vi_tri") or "").strip()
    phong_ban = (data.get("phong_ban") or "").strip()
    don_vi_su_dung = (data.get("don_vi_su_dung") or phong_ban).strip()
    mo_ta = (data.get("mo_ta") or "").strip()
    so_serial = (data.get("so_serial") or "").strip()
    model = (data.get("model") or "").strip()
    hang_san_xuat = (data.get("hang_san_xuat") or "").strip()
    thoi_han_bao_hanh = (data.get("thoi_han_bao_hanh") or "").strip()

    try:
        gia_tri = float(data.get("gia_tri", 0))
    except (ValueError, TypeError):
        gia_tri = 0.0

    return {
        "ten_tai_san": ten_tai_san,
        "loai_tai_san": loai_tai_san,
        "phan_loai": phan_loai,
        "tinh_trang_ky_thuat": tinh_trang_ky_thuat,
        "vi_tri": vi_tri,
        "phong_ban": phong_ban,
        "don_vi_su_dung": don_vi_su_dung,
        "mo_ta": mo_ta,
        "so_serial": so_serial,
        "model": model,
        "hang_san_xuat": hang_san_xuat,
        "thoi_han_bao_hanh": thoi_han_bao_hanh,
        "gia_tri": max(0.0, gia_tri)
    }

def xac_thuc_ban_giao(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        nguoi_nhan_id = int(data.get("nguoi_nhan_id", 0))
    except (ValueError, TypeError):
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng chọn người nhận bàn giao hợp lệ.")

    if nguoi_nhan_id <= 0:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Vui lòng chọn người nhận bàn giao.")

    ghi_chu = (data.get("ghi_chu") or "").strip()
    return {
        "nguoi_nhan_id": nguoi_nhan_id,
        "ghi_chu": ghi_chu
    }

def xac_thuc_bao_tri(data: Dict[str, Any]) -> Dict[str, Any]:
    noi_dung = (data.get("noi_dung") or "").strip()
    if not noi_dung:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Nội dung bảo trì/sửa chữa không được để trống.")

    don_vi_thuc_hien = (data.get("don_vi_thuc_hien") or "").strip()
    ghi_chu = (data.get("ghi_chu") or "").strip()
    try:
        chi_phi = float(data.get("chi_phi", 0))
    except (ValueError, TypeError):
        chi_phi = 0.0

    return {
        "noi_dung": noi_dung,
        "chi_phi": max(0.0, chi_phi),
        "don_vi_thuc_hien": don_vi_thuc_hien,
        "ghi_chu": ghi_chu
    }

def xac_thuc_yeu_cau_sua_chua(data: Dict[str, Any]) -> Dict[str, Any]:
    noi_dung = (data.get("noi_dung") or "").strip()
    if not noi_dung:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Nội dung yêu cầu sửa chữa không được để trống.")

    loai_sua_chua = (data.get("loai_sua_chua") or "sua_chua_nho").strip()
    hien_trang = (data.get("hien_trang") or "").strip()
    don_vi_thuc_hien = (data.get("don_vi_thuc_hien") or "").strip()
    ghi_chu = (data.get("ghi_chu") or "").strip()
    
    try:
        chi_phi_du_kien = float(data.get("chi_phi_du_kien", 0))
    except (ValueError, TypeError):
        chi_phi_du_kien = 0.0

    try:
        tai_san_id = int(data.get("tai_san_id", 0)) if data.get("tai_san_id") else None
    except (ValueError, TypeError):
        tai_san_id = None

    try:
        bao_cao_hu_hai_id = int(data.get("bao_cao_hu_hai_id", 0)) if data.get("bao_cao_hu_hai_id") else None
    except (ValueError, TypeError):
        bao_cao_hu_hai_id = None

    return {
        "noi_dung": noi_dung,
        "loai_sua_chua": loai_sua_chua,
        "hien_trang": hien_trang,
        "don_vi_thuc_hien": don_vi_thuc_hien,
        "chi_phi_du_kien": max(0.0, chi_phi_du_kien),
        "tai_san_id": tai_san_id,
        "bao_cao_hu_hai_id": bao_cao_hu_hai_id,
        "ghi_chu": ghi_chu
    }

def xac_thuc_kiem_ke(data: Dict[str, Any]) -> Dict[str, Any]:
    ghi_chu = (data.get("ghi_chu") or "").strip()
    chi_tiet = data.get("chi_tiet") or []

    return {
        "ghi_chu": ghi_chu,
        "chi_tiet": chi_tiet
    }
