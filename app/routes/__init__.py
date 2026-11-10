from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify, render_template

def yeu_cau_dang_nhap(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "nguoi_dung_id" not in session:
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            if request.is_json or request.path.endswith("/phe-duyet") or request.path.endswith("/tu-choi"):
                return jsonify({"loi": "CHUA_DANG_NHAP", "thong_bao": "Vui lòng đăng nhập để tiếp tục."}), 401
            return redirect(url_for("auth.dang_nhap", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def yeu_cau_vai_tro(*vai_tro_duoc_phep):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "nguoi_dung_id" not in session:
                flash("Vui lòng đăng nhập để tiếp tục.", "warning")
                if request.is_json or request.method == "POST":
                    return jsonify({"loi": "CHUA_DANG_NHAP", "thong_bao": "Vui lòng đăng nhập để tiếp tục."}), 401
                return redirect(url_for("auth.dang_nhap", next=request.url))

            vai_tro_hien_tai = session.get("vai_tro")
            if vai_tro_hien_tai not in vai_tro_duoc_phep:
                if request.is_json or request.method == "POST":
                    return jsonify({"loi": "KHONG_DU_QUYEN", "thong_bao": "Bạn không có quyền thực hiện thao tác này."}), 403
                return render_template("errors/403.html", thong_bao="Bạn không có quyền truy cập trang này."), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
