import os
from flask import Flask, render_template, jsonify, request
from app.db import close_db, init_db
from app.errors import LoiNghiepVu

def tao_app(cau_hinh=None):
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'khoa_bi_mat_neu_csvc_2026'),
        TEMPLATES_AUTO_RELOAD=True,
    )

    if cau_hinh:
        app.config.update(cau_hinh)

    app.teardown_appcontext(close_db)

    @app.template_filter('tien_vnd')
    def dinh_dang_tien(so_tien):
        if so_tien is None:
            return '0 đ'
        try:
            val = float(so_tien)
            return f'{val:,.0f} đ'.replace(',', '.')
        except (ValueError, TypeError):
            return str(so_tien)

    @app.template_filter('doc_so_thanh_chu')
    def doc_so_thanh_chu(so_tien):
        if so_tien is None:
            return ''
        try:
            n = int(round(float(so_tien)))
        except (ValueError, TypeError):
            return str(so_tien)
        if n == 0:
            return "Không đồng chẵn"

        chu_so = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
        tien = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ"]

        def doc_ba_so(baso, day_du=False):
            tram = baso // 100
            chuc = (baso % 100) // 10
            donvi = baso % 10
            kq = []
            if tram > 0 or day_du:
                kq.append(chu_so[tram] + " trăm")
            if chuc > 1:
                kq.append(chu_so[chuc] + " mươi")
                if donvi == 1:
                    kq.append("mốt")
                elif donvi == 5:
                    kq.append("lăm")
                elif donvi > 0:
                    kq.append(chu_so[donvi])
            elif chuc == 1:
                kq.append("mười")
                if donvi == 1:
                    kq.append("một")
                elif donvi == 5:
                    kq.append("lăm")
                elif donvi > 0:
                    kq.append(chu_so[donvi])
            elif chuc == 0:
                if (tram > 0 or day_du) and donvi > 0:
                    kq.append("lẻ")
                if donvi > 0:
                    kq.append(chu_so[donvi])
            return " ".join(kq)

        chuoi_so = str(n)
        doan = []
        while len(chuoi_so) > 0:
            doan.append(int(chuoi_so[-3:]))
            chuoi_so = chuoi_so[:-3]

        ket_qua = []
        for i in range(len(doan) - 1, -1, -1):
            if doan[i] > 0:
                doc = doc_ba_so(doan[i], day_du=(i < len(doan) - 1))
                if doc:
                    ket_qua.append(doc)
                    if i > 0:
                        ket_qua.append(tien[i])

        res = " ".join(ket_qua).strip()
        if res:
            res = res[0].upper() + res[1:] + " đồng chẵn"
        return res

    @app.template_filter('dinh_dang_ngay')
    def dinh_dang_ngay(iso_str):
        if not iso_str:
            return '-'
        try:
            phan = iso_str.replace('T', ' ').split('.')[0]
            if len(phan) >= 16:
                ngay_gio = phan[:16]
                ngay, gio = ngay_gio.split(' ')
                y, m, d = ngay.split('-')
                return f'{d}/{m}/{y} {gio}'
            return phan
        except Exception:
            return str(iso_str)

    @app.template_filter('ten_trang_thai')
    def ten_trang_thai(ma):
        tu_dien = {
            'cho_phe_duyet': 'Chờ Trưởng BP duyệt',
            'cho_lanh_dao_duyet': 'Chờ Lãnh đạo duyệt (≥ 100tr)',
            'da_phe_duyet': 'Đã phê duyệt',
            'tu_choi': 'Từ chối',
            'dang_mua': 'Đang mua sắm',
            'da_nhan': 'Đang nghiệm thu',
            'dang_nghiem_thu': 'Đang nghiệm thu',
            'cho_thanh_toan': 'Chờ thanh toán',
            'hoan_tat': 'Hoàn tất',
            'cho_ban_giao': 'Trong kho (Chờ bàn giao)',
            'dang_su_dung': 'Đang sử dụng',
            'dang_sua_chua': 'Đang sửa chữa',
            'cho_thanh_ly': 'Chờ thanh lý',
            'da_thanh_ly': 'Đã thanh lý',
            'chua_xu_ly': 'Chờ tiếp nhận',
            'cho_tiep_nhan': 'Chờ tiếp nhận',
            'dang_khao_sat': 'Đang khảo sát (BM03)',
            'cho_duyet_phuong_an': 'Chờ phê duyệt phương án',
            'cho_thu_tuc_m08': 'Chờ thủ tục tại M08',
            'dang_sua_chua': 'Đang sửa chữa',
            'cho_nghiem_thu': 'Chờ nghiệm thu',
            'da_nghiem_thu': 'Đã nghiệm thu (Hoàn thành)',
            'khong_dat': 'Không đạt yêu cầu (Khắc phục lại)',
            'tra_lai': 'Yêu cầu bổ sung',
            'dang_xu_ly': 'Đang xử lý',
            'can_thay_the': 'Cần thay thế (Chuyển M08)',
            'da_xu_ly': 'Đã nghiệm thu (Hoàn thành)',
            'nhe': 'Nhẹ',
            'trung_binh': 'Trung bình',
            'nghiem_trong': 'Nghiêm trọng',
            'mua_sam': 'Bộ phận Mua sắm',
            'quan_ly_kho': 'Bộ phận Quản lý tài sản',
            'ke_toan': 'Kế toán',
            'quan_tri': 'Quản trị viên (Admin)',
            'don_vi': 'Đơn vị sử dụng'
        }
        return tu_dien.get(ma, ma)

    @app.template_filter('badge_trang_thai')
    def badge_trang_thai(ma):
        tu_dien = {
            'cho_phe_duyet': 'badge-warning',
            'cho_lanh_dao_duyet': 'badge-danger',
            'da_phe_duyet': 'badge-info',
            'tu_choi': 'badge-danger',
            'dang_mua': 'badge-primary',
            'da_nhan': 'badge-info',
            'dang_nghiem_thu': 'badge-info',
            'cho_thanh_toan': 'badge-warning',
            'hoan_tat': 'badge-success',
            'cho_ban_giao': 'badge-warning',
            'dang_su_dung': 'badge-success',
            'dang_sua_chua': 'badge-danger',
            'cho_thanh_ly': 'badge-secondary',
            'da_thanh_ly': 'badge-dark',
            'chua_xu_ly': 'badge-warning',
            'cho_tiep_nhan': 'badge-warning',
            'dang_khao_sat': 'badge-info',
            'cho_duyet_phuong_an': 'badge-warning',
            'cho_thu_tuc_m08': 'badge-secondary',
            'dang_sua_chua': 'badge-primary',
            'cho_nghiem_thu': 'badge-info',
            'da_nghiem_thu': 'badge-success',
            'khong_dat': 'badge-danger',
            'tra_lai': 'badge-danger',
            'dang_xu_ly': 'badge-info',
            'can_thay_the': 'badge-danger',
            'da_xu_ly': 'badge-success',
            'nhe': 'badge-info',
            'trung_binh': 'badge-warning',
            'nghiem_trong': 'badge-danger',
            'mua_sam': 'badge-primary',
            'quan_ly_kho': 'badge-info',
            'ke_toan': 'badge-warning',
            'quan_tri': 'badge-danger',
            'don_vi': 'badge-info'
        }
        return tu_dien.get(ma, 'badge-secondary')

    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.mua_sam import mua_sam_bp
    from app.routes.ke_toan import ke_toan_bp
    from app.routes.tai_san import tai_san_bp
    from app.routes.admin import admin_bp
    from app.routes.don_vi import don_vi_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(mua_sam_bp)
    app.register_blueprint(ke_toan_bp)
    app.register_blueprint(tai_san_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(don_vi_bp)

    @app.errorhandler(LoiNghiepVu)
    def handle_loi_nghiep_vu(e):
        if request.is_json:
            return jsonify(e.to_dict()), e.status_code
        return render_template('errors/loi.html', loi=e), e.status_code

    @app.errorhandler(403)
    def forbidden(e):
        if request.is_json:
            return jsonify({'loi': 'KHONG_DU_QUYEN', 'thong_bao': 'Bạn không có quyền thực hiện thao tác này.'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.is_json:
            return jsonify({'loi': 'KHONG_TIM_THAY', 'thong_bao': 'Tài nguyên yêu cầu không tồn tại.'}), 404
        return render_template('errors/404.html'), 404

    with app.app_context():
        try:
            init_db()
        except Exception:
            pass

    return app
