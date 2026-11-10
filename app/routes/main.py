from flask import Blueprint, render_template
from app.services import bao_cao as tk_svc

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def trang_chu():
    """Trang chủ cổng thông tin Quản lý Cơ sở Vật chất (phong cách NEU)."""
    try:
        thong_ke = tk_svc.thong_ke_tong_quan()
    except Exception:
        thong_ke = None
    return render_template("main/trang_chu.html", thong_ke=thong_ke)
