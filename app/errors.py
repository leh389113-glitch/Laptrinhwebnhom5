class LoiNghiepVu(Exception):
    """Ngoại lệ xử lý các lỗi nghiệp vụ trong hệ thống."""
    def __init__(self, ma_loi: str, thong_bao: str = None, status_code: int = 400):
        self.ma_loi = ma_loi
        self.thong_bao = thong_bao or BANG_MA_LOI.get(ma_loi, "Đã xảy ra lỗi nghiệp vụ.")
        self.status_code = status_code
        super().__init__(self.thong_bao)

    def to_dict(self):
        return {
            "loi": self.ma_loi,
            "thong_bao": self.thong_bao
        }

BANG_MA_LOI = {
    "DE_NGHI_KHONG_TON_TAI": "Đề nghị mua sắm không tồn tại trong hệ thống.",
    "KHONG_DU_QUYEN": "Bạn không có quyền thực hiện thao tác này.",
    "TAI_SAN_KHONG_TON_TAI": "Tài sản không tồn tại trong hệ thống.",
    "TRANG_THAI_KHONG_HOP_LE": "Trạng thái hiện tại không cho phép thực hiện thao tác này.",
    "DU_LIEU_DAU_VAO_KHONG_HOP_LE": "Dữ liệu đầu vào không hợp lệ, vui lòng kiểm tra lại.",
    "CHUA_DANG_NHAP": "Vui lòng đăng nhập để tiếp tục.",
    "TAI_KHOAN_KHONG_TON_TAI": "Tài khoản không tồn tại hoặc mật khẩu sai.",
    "TAI_KHOAN_DA_TON_TAI": "Tên đăng nhập đã được sử dụng.",
    "EMAIL_DA_TON_TAI": "Email đã được đăng ký trong hệ thống."
}
