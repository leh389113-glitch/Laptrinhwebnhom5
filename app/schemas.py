import re
from typing import Tuple, Dict, Any, Optional, List
from app.errors import LoiNghiepVu

def xac_thuc_dang_ky(data: Dict[str, Any]) -> Dict[str, Any]:
    ho_ten = (data.get("ho_ten") or "").strip()
    email = (data.get("email") or "").strip().lower()
    ten_dang_nhap = (data.get("ten_dang_nhap") or "").strip()
    mat_khau = data.get("mat_khau") or ""
    xac_nhan_mat_khau = data.get("xac_nhan_mat_khau") or ""
    vai_tro = (data.get("vai_tro") or "mua_sam").strip()

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

    if vai_tro not in ["mua_sam", "quan_ly_kho", "ke_toan", "quan_tri"]:
        vai_tro = "mua_sam"

    return {
        "ho_ten": ho_ten,
        "email": email,
        "ten_dang_nhap": ten_dang_nhap,
        "mat_khau": mat_khau,
        "vai_tro": vai_tro
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
            "ghi_chu": (item.get("ghi_chu") or "").strip()
        })

    return {
        "tieu_de": tieu_de,
        "don_vi_de_nghi": don_vi_de_nghi,
        "mo_ta": mo_ta,
        "tong_du_toan": tong_du_toan,
        "items": cleaned_items
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

    return {
        "so_tien": so_tien,
        "so_hoa_don": so_hoa_don,
        "phuong_thuc": phuong_thuc,
        "ghi_chu": ghi_chu
    }

def xac_thuc_tai_san(data: Dict[str, Any]) -> Dict[str, Any]:
    ten_tai_san = (data.get("ten_tai_san") or "").strip()
    if not ten_tai_san:
        raise LoiNghiepVu("DU_LIEU_DAU_VAO_KHONG_HOP_LE", "Tên tài sản không được để trống.")

    loai_tai_san = (data.get("loai_tai_san") or "").strip()
    vi_tri = (data.get("vi_tri") or "").strip()
    phong_ban = (data.get("phong_ban") or "").strip()
    mo_ta = (data.get("mo_ta") or "").strip()
    try:
        gia_tri = float(data.get("gia_tri", 0))
    except (ValueError, TypeError):
        gia_tri = 0.0

    return {
        "ten_tai_san": ten_tai_san,
        "loai_tai_san": loai_tai_san,
        "vi_tri": vi_tri,
        "phong_ban": phong_ban,
        "mo_ta": mo_ta,
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

def xac_thuc_kiem_ke(data: Dict[str, Any]) -> Dict[str, Any]:
    ghi_chu = (data.get("ghi_chu") or "").strip()
    chi_tiet = data.get("chi_tiet") or []

    return {
        "ghi_chu": ghi_chu,
        "chi_tiet": chi_tiet
    }
