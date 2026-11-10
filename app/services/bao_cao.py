import io
import os
from pathlib import Path
from xml.sax.saxutils import escape

from app.db import get_db
from app import clock
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

_PDF_FONT = "NEUTimesNewRoman"
_PDF_FONT_BOLD = "NEUTimesNewRomanBold"


def _register_pdf_fonts() -> None:
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    if _PDF_FONT in registered_fonts and _PDF_FONT_BOLD in registered_fonts:
        return

    windows_fonts = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
    font_candidates = [
        (windows_fonts / "times.ttf", windows_fonts / "timesbd.ttf"),
        (Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"),
         Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
         Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
         Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf")),
        (Path("/usr/share/fonts/truetype/freefont/FreeSerif.ttf"),
         Path("/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf")),
    ]
    font_pair = next(
        ((regular, bold) for regular, bold in font_candidates
         if regular.is_file() and bold.is_file()),
        None
    )
    if font_pair is None:
        raise FileNotFoundError(
            "Không tìm thấy phông TrueType hỗ trợ tiếng Việt để tạo PDF."
        )

    pdfmetrics.registerFont(TTFont(_PDF_FONT, str(font_pair[0])))
    pdfmetrics.registerFont(TTFont(_PDF_FONT_BOLD, str(font_pair[1])))


def _pdf_styles() -> dict:
    _register_pdf_fonts()
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "NEUTitle", parent=styles["Title"], fontName=_PDF_FONT_BOLD,
            fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=8
        ),
        "subtitle": ParagraphStyle(
            "NEUSubtitle", parent=styles["Normal"], fontName=_PDF_FONT,
            fontSize=11, leading=14, alignment=TA_CENTER
        ),
        "body": ParagraphStyle(
            "NEUBody", parent=styles["Normal"], fontName=_PDF_FONT,
            fontSize=13, leading=18
        ),
        "small": ParagraphStyle(
            "NEUSmall", parent=styles["Normal"], fontName=_PDF_FONT,
            fontSize=11, leading=14
        ),
        "cell": ParagraphStyle(
            "NEUCell", parent=styles["Normal"], fontName=_PDF_FONT,
            fontSize=9, leading=11
        ),
        "cell_header": ParagraphStyle(
            "NEUCellHeader", parent=styles["Normal"], fontName=_PDF_FONT_BOLD,
            fontSize=9, leading=11, alignment=TA_CENTER
        ),
        "right": ParagraphStyle(
            "NEURight", parent=styles["Normal"], fontName=_PDF_FONT,
            fontSize=12, leading=16, alignment=TA_CENTER
        ),
    }


def _p(text, style, markup: bool = False) -> Paragraph:
    value = str(text if text not in (None, "") else "—")
    return Paragraph(value if markup else escape(value), style)


def _format_money(value) -> str:
    try:
        return f"{float(value or 0):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _header_table(styles) -> Table:
    data = [[
        _p("<b>ĐẠI HỌC KINH TẾ QUỐC DÂN</b><br/><b>ĐƠN VỊ CHỦ TRÌ: ....................</b>",
           styles["body"], markup=True),
        _p("<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br/>"
           "<b>Độc lập - Tự do - Hạnh phúc</b>",
           styles["right"], markup=True)
    ]]
    table = Table(data, colWidths=[82.5 * mm, 82.5 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _form_footer(styles, form_code: str) -> list:
    ngay_lap = clock.now()
    return [
        _p(f"<b>{escape(form_code)}</b> - (Ban hành theo Thông tư số 133/2016/TT-BTC)",
           styles["small"], markup=True),
        _p(f"Hà Nội, ngày {ngay_lap.strftime('%d')} tháng {ngay_lap.strftime('%m')} năm {ngay_lap.strftime('%Y')}",
           styles["right"]),
    ]


def _table_style() -> TableStyle:
    return TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8EEF5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

def thong_ke_tong_quan() -> dict:
    """
    Tổng hợp các chỉ số KPI và dữ liệu cho Dashboard M17 (Admin).
    Dữ liệu được truy vấn trực tiếp từ bảng M08 và M09, không lưu cache cứng.
    """
    db = get_db()
    hien_tai = clock.now()
    thang_hien_tai_prefix = hien_tai.strftime("%Y-%m")

    # 1. Số đề nghị chờ duyệt (cả đơn < 100tr và đơn >= 100tr chờ lãnh đạo)
    row = db.execute("SELECT COUNT(*) AS cnt FROM de_nghi_mua_sam WHERE trang_thai IN ('cho_phe_duyet', 'cho_lanh_dao_duyet')").fetchone()
    so_de_nghi_cho_duyet = row["cnt"] if row else 0

    # 2. Số tài sản đang sử dụng
    row = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE trang_thai = 'dang_su_dung'").fetchone()
    so_tai_san_dang_su_dung = row["cnt"] if row else 0

    # 3. Phân loại tài sản: TSCĐ vs CCDC
    row_tscd = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE phan_loai = 'tai_san_co_dinh'").fetchone()
    so_tscd = row_tscd["cnt"] if row_tscd else 0
    row_ccdc = db.execute("SELECT COUNT(*) AS cnt FROM tai_san WHERE phan_loai = 'cong_cu_dung_cu'").fetchone()
    so_ccdc = row_ccdc["cnt"] if row_ccdc else 0

    # 4. Chi tiêu tháng này (từ bảng thanh_toan)
    row = db.execute(
        "SELECT SUM(so_tien) AS tong FROM thanh_toan WHERE ngay_thanh_toan LIKE ?",
        (f"{thang_hien_tai_prefix}%",)
    ).fetchone()
    chi_tieu_thang_nay = row["tong"] if (row and row["tong"]) else 0.0

    # 5. Số yêu cầu sửa chữa đang xử lý (M09)
    try:
        row_sc = db.execute("SELECT COUNT(*) AS cnt FROM yeu_cau_sua_chua WHERE trang_thai = 'dang_sua_chua'").fetchone()
        so_sua_chua_dang_xu_ly = row_sc["cnt"] if row_sc else 0
    except Exception:
        so_sua_chua_dang_xu_ly = 0

    # 7. Phân bổ tình trạng tài sản (vẽ biểu đồ tròn)
    rows_trang_thai = db.execute(
        "SELECT trang_thai, COUNT(*) AS so_luong FROM tai_san GROUP BY trang_thai"
    ).fetchall()
    phan_bo_tai_san = {r["trang_thai"]: r["so_luong"] for r in rows_trang_thai}

    # 8. Biểu đồ tình hình mua sắm theo tháng (dựa trên ngân sách đề nghị đã tạo)
    rows_thang = db.execute(
        """
        SELECT substr(ngay_tao, 1, 7) AS thang,
               COUNT(*) AS so_de_nghi,
               SUM(tong_du_toan) AS tong_tien
        FROM de_nghi_mua_sam
        GROUP BY thang
        ORDER BY thang DESC
        LIMIT 6
        """
    ).fetchall()
    bieu_do_mua_sam = [dict(r) for r in reversed(rows_thang)]

    # 9. Đề nghị mua sắm gần đây
    rows_dn_moi = db.execute(
        """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        ORDER BY d.id DESC LIMIT 5
        """
    ).fetchall()
    de_nghi_gan_day = [dict(r) for r in rows_dn_moi]

    # 10. Tài sản mới tiếp nhận
    rows_ts_moi = db.execute(
        "SELECT * FROM tai_san ORDER BY id DESC LIMIT 5"
    ).fetchall()
    tai_san_gan_day = [dict(r) for r in rows_ts_moi]

    return {
        "so_de_nghi_cho_duyet": so_de_nghi_cho_duyet,
        "so_tai_san_dang_su_dung": so_tai_san_dang_su_dung,
        "so_tscd": so_tscd,
        "so_ccdc": so_ccdc,
        "chi_tieu_thang_nay": chi_tieu_thang_nay,
        "so_sua_chua_dang_xu_ly": so_sua_chua_dang_xu_ly,
        "phan_bo_tai_san": phan_bo_tai_san,
        "bieu_do_mua_sam": bieu_do_mua_sam,
        "de_nghi_gan_day": de_nghi_gan_day,
        "tai_san_gan_day": tai_san_gan_day
    }

def bao_cao_mua_sam(tu_ngay: str = None, den_ngay: str = None) -> list:
    """Báo cáo danh sách mua sắm theo khoảng thời gian."""
    db = get_db()
    query = """
        SELECT d.*, u.ho_ten AS nguoi_de_nghi_ten
        FROM de_nghi_mua_sam d
        LEFT JOIN nguoi_dung u ON d.nguoi_de_nghi_id = u.id
        WHERE 1=1
    """
    params = []
    if tu_ngay:
        query += " AND d.ngay_tao >= ?"
        params.append(tu_ngay)
    if den_ngay:
        query += " AND d.ngay_tao <= ?"
        params.append(den_ngay + "T23:59:59")

    query += " ORDER BY d.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def bao_cao_tai_san(trang_thai: str = None, phong_ban: str = None) -> list:
    """Báo cáo danh sách tài sản theo trạng thái và phòng ban."""
    db = get_db()
    query = """
        SELECT t.*, u.ho_ten AS nguoi_su_dung_ten,
               d.nha_cung_cap AS nha_cung_cap
        FROM tai_san t
        LEFT JOIN nguoi_dung u ON t.nguoi_su_dung_id = u.id
        LEFT JOIN de_nghi_mua_sam d ON d.id = t.de_nghi_id
        WHERE 1=1
    """
    params = []
    if trang_thai:
        query += " AND t.trang_thai = ?"
        params.append(trang_thai)
    if phong_ban:
        query += " AND t.phong_ban LIKE ?"
        params.append(f"%{phong_ban}%")

    query += " ORDER BY t.id DESC"
    rows = db.execute(query, params).fetchall()
    return [dict(r) for r in rows]

def _chi_tiet_mua_sam(de_nghi_list: list) -> dict:
    if not de_nghi_list:
        return {}

    db = get_db()
    ket_qua = {}
    ids = [dn["id"] for dn in de_nghi_list]
    for offset in range(0, len(ids), 500):
        nhom_ids = ids[offset:offset + 500]
        placeholders = ",".join("?" for _ in nhom_ids)
        rows = db.execute(
            f"""
            SELECT de_nghi_id, ten_hang_hoa, don_vi_tinh, so_luong,
                   don_gia_du_kien, thanh_tien, vi_tri_su_dung
            FROM chi_tiet_de_nghi
            WHERE de_nghi_id IN ({placeholders})
            ORDER BY de_nghi_id, id
            """,
            nhom_ids
        ).fetchall()
        for row in rows:
            ket_qua.setdefault(row["de_nghi_id"], []).append(dict(row))
    return ket_qua


def _ten_trang_thai_mua_sam(trang_thai: str) -> str:
    return {
        "cho_phe_duyet": "Chờ phê duyệt",
        "cho_lanh_dao_duyet": "Chờ Lãnh đạo phê duyệt",
        "da_phe_duyet": "Đã phê duyệt",
        "tu_choi": "Từ chối",
        "dang_mua": "Đang mua sắm",
        "da_nhan": "Đã tiếp nhận",
        "hoan_tat": "Hoàn tất",
    }.get(trang_thai, trang_thai or "—")


def xuat_pdf_mua_sam(tu_ngay: str = None, den_ngay: str = None) -> bytes:
    """Xuất hồ sơ đề nghị mua sắm theo bố cục Thẻ tài sản cố định S11-DNN."""
    styles = _pdf_styles()
    de_nghi_list = bao_cao_mua_sam(tu_ngay=tu_ngay, den_ngay=den_ngay)
    chi_tiet = _chi_tiet_mua_sam(de_nghi_list)
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, leftMargin=30 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="Báo cáo mua sắm - Đại học Kinh tế Quốc dân"
    )
    story = []
    ngay_lap = clock.now().strftime("%d/%m/%Y")

    if not de_nghi_list:
        story.extend([
            _header_table(styles),
            *_form_footer(styles, "Mẫu số S11-DNN"),
            Spacer(1, 5 * mm),
            _p("THẺ TÀI SẢN CỐ ĐỊNH", styles["title"]),
            _p("Không có đề nghị mua sắm trong khoảng thời gian đã chọn.", styles["body"])
        ])

    for index, dn in enumerate(de_nghi_list):
        if index:
            story.append(PageBreak())
        story.extend([
            _header_table(styles),
            *_form_footer(styles, "Mẫu số S11-DNN"),
            Spacer(1, 4 * mm),
            _p("THẺ TÀI SẢN CỐ ĐỊNH", styles["title"]),
            _p("(Biểu mẫu hồ sơ mua sắm - Đại học Kinh tế Quốc dân)",
               styles["subtitle"]),
            Spacer(1, 5 * mm),
            _p(f"<b>Số:</b> {escape(str(dn.get('ma_de_nghi') or ''))} "
               f"&nbsp;&nbsp;&nbsp; <b>Ngày lập:</b> {ngay_lap}", styles["body"], markup=True),
            _p(f"<b>Đơn vị:</b> {escape(str(dn.get('don_vi_de_nghi') or ''))}",
               styles["body"], markup=True),
            _p(f"<b>Căn cứ giao nhận / hợp đồng:</b> {escape(str(dn.get('so_hop_dong') or 'Chưa có thông tin'))}",
               styles["body"], markup=True),
            _p(f"<b>Tên, quy cách hàng hóa:</b> {escape(str(dn.get('tieu_de') or ''))}",
               styles["body"], markup=True),
            _p(f"<b>Bộ phận quản lý, sử dụng:</b> {escape(str(dn.get('don_vi_de_nghi') or ''))}"
               f"&nbsp;&nbsp;&nbsp; <b>Trạng thái:</b> {escape(_ten_trang_thai_mua_sam(dn.get('trang_thai')))}",
               styles["body"], markup=True),
            _p(f"<b>Người đề nghị:</b> {escape(str(dn.get('nguoi_de_nghi_ten') or '—'))}"
               f"&nbsp;&nbsp;&nbsp; <b>Địa điểm sử dụng:</b> {escape(str(dn.get('dia_diem_su_dung') or '—'))}",
               styles["body"], markup=True),
            Spacer(1, 4 * mm),
        ])

        rows = [[
            _p("Số hiệu<br/>chứng từ", styles["cell_header"]),
            _p("Ngày, tháng,<br/>năm", styles["cell_header"]),
            _p("Diễn giải", styles["cell_header"]),
            _p("Nguyên giá<br/>(VNĐ)", styles["cell_header"]),
            _p("Năm", styles["cell_header"]),
            _p("Giá trị hao mòn", styles["cell_header"]),
            _p("Cộng dồn", styles["cell_header"]),
        ], [
            _p("A", styles["cell_header"]), _p("B", styles["cell_header"]),
            _p("C", styles["cell_header"]), _p("1", styles["cell_header"]),
            _p("2", styles["cell_header"]), _p("3", styles["cell_header"]),
            _p("4", styles["cell_header"]),
        ]]
        for item in chi_tiet.get(dn["id"], []):
            rows.append([
                _p(dn.get("ma_de_nghi"), styles["cell"]),
                _p(dn.get("ngay_tao", "")[:10], styles["cell"]),
                _p(f"{item.get('ten_hang_hoa') or ''} "
                   f"({item.get('so_luong') or 0} {item.get('don_vi_tinh') or ''})", styles["cell"]),
                _p(_format_money(item.get("thanh_tien")), styles["cell"]),
                _p((dn.get("ngay_tao") or "")[:4], styles["cell"]),
                _p("—", styles["cell"]),
                _p("—", styles["cell"]),
            ])
        if len(rows) == 2:
            rows.append([
                _p(dn.get("ma_de_nghi"), styles["cell"]), _p(dn.get("ngay_tao", "")[:10], styles["cell"]),
                _p(dn.get("tieu_de"), styles["cell"]), _p(_format_money(dn.get("tong_du_toan")), styles["cell"]),
                _p((dn.get("ngay_tao") or "")[:4], styles["cell"]), _p("—", styles["cell"]),
                _p("—", styles["cell"])
            ])
        rows.append([
            _p("", styles["cell"]), _p("", styles["cell"]),
            _p("<b>Cộng</b>", styles["cell"], markup=True),
            _p(f"<b>{_format_money(dn.get('tong_du_toan'))}</b>", styles["cell"], markup=True),
            _p("", styles["cell"]), _p("", styles["cell"]),
            _p("", styles["cell"])
        ])
        table = Table(rows, colWidths=[20 * mm, 22 * mm, 53 * mm, 25 * mm, 12 * mm, 16 * mm, 17 * mm],
                      repeatRows=2)
        table.setStyle(_table_style())
        phu_tung_rows = [[
            _p("Số STT", styles["cell_header"]),
            _p("Tên, quy cách dụng cụ, phụ tùng", styles["cell_header"]),
            _p("Đơn vị tính", styles["cell_header"]),
            _p("Số lượng", styles["cell_header"]),
            _p("Giá trị (VNĐ)", styles["cell_header"]),
        ], [
            _p("A", styles["cell_header"]), _p("B", styles["cell_header"]),
            _p("C", styles["cell_header"]), _p("1", styles["cell_header"]),
            _p("2", styles["cell_header"]),
        ]]
        for item_index, item in enumerate(chi_tiet.get(dn["id"], []), 1):
            phu_tung_rows.append([
                _p(item_index, styles["cell"]),
                _p(item.get("ten_hang_hoa"), styles["cell"]),
                _p(item.get("don_vi_tinh"), styles["cell"]),
                _p(item.get("so_luong"), styles["cell"]),
                _p(_format_money(item.get("thanh_tien")), styles["cell"]),
            ])
        phu_tung_table = Table(
            phu_tung_rows, colWidths=[15 * mm, 70 * mm, 25 * mm, 20 * mm, 30 * mm],
            repeatRows=2
        )
        phu_tung_table.setStyle(_table_style())
        story.extend([
            table,
            Spacer(1, 4 * mm),
            _p("<b>Dụng cụ phụ tùng kèm theo</b>", styles["body"], markup=True),
            phu_tung_table,
            Spacer(1, 5 * mm),
            _p("<b>Ghi giảm tài sản / ghi chú:</b> " +
               escape(str(dn.get("ly_do_su_can_thiet") or dn.get("mo_ta") or "—")),
               styles["body"], markup=True),
            Spacer(1, 8 * mm),
            Table([[
                _p("<b>Người lập biểu</b><br/><br/><br/>(Ký, họ tên)", styles["subtitle"], markup=True),
                _p("<b>Kế toán trưởng</b><br/><br/><br/>(Ký, họ tên)", styles["subtitle"], markup=True),
                _p("<b>Người đại diện theo pháp luật</b><br/><br/><br/>(Ký, họ tên, đóng dấu)",
                   styles["subtitle"], markup=True),
            ]], colWidths=[55 * mm, 55 * mm, 55 * mm])
        ])

    document.build(story)
    return output.getvalue()


def xuat_pdf_tai_san(phong_ban: str = None) -> bytes:
    """Xuất danh mục tài sản theo bố cục Bảng kê mua hàng Mẫu 06-VT."""
    from app.services.mua_sam import doc_so_thanh_chu

    styles = _pdf_styles()
    tai_san_list = bao_cao_tai_san(phong_ban=phong_ban)
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output, pagesize=A4, leftMargin=30 * mm, rightMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
        title="Bảng kê tài sản - Đại học Kinh tế Quốc dân"
    )
    story = [
        _header_table(styles),
        *_form_footer(styles, "Mẫu số 06 - VT"),
        Spacer(1, 5 * mm),
        _p("BẢNG KÊ MUA HÀNG", styles["title"]),
        _p("(Danh mục tài sản - Đại học Kinh tế Quốc dân)", styles["subtitle"]),
        _p(f"Ngày {clock.now().strftime('%d/%m/%Y')}", styles["subtitle"]),
        Spacer(1, 5 * mm),
        _p(f"<b>Đơn vị:</b> Đại học Kinh tế Quốc dân"
           f"&nbsp;&nbsp;&nbsp; <b>Bộ phận:</b> {escape(str(phong_ban or 'Toàn trường'))}",
           styles["body"], markup=True),
        _p("<b>Họ và tên người mua:</b> Bộ phận Quản lý tài sản"
           "&nbsp;&nbsp;&nbsp; <b>Bộ phận:</b> Quản lý tài sản", styles["body"], markup=True),
        Spacer(1, 4 * mm)
    ]
    rows = [[
        _p("STT", styles["cell_header"]),
        _p("Tên, quy cách, phẩm chất hàng hóa (tài sản)", styles["cell_header"]),
        _p("Địa chỉ mua hàng / vị trí sử dụng", styles["cell_header"]),
        _p("ĐVT", styles["cell_header"]),
        _p("Số lượng", styles["cell_header"]),
        _p("Đơn giá<br/>(VNĐ)", styles["cell_header"]),
        _p("Thành tiền<br/>(VNĐ)", styles["cell_header"]),
    ]]
    tong_tien = 0
    for index, ts in enumerate(tai_san_list, 1):
        gia_tri = ts.get("gia_tri") or 0
        tong_tien += float(gia_tri)
        rows.append([
            _p(index, styles["cell"]),
            _p(f"{ts.get('ten_tai_san') or ''} ({ts.get('ma_tai_san') or ''})", styles["cell"]),
            _p(ts.get("vi_tri") or ts.get("phong_ban") or ts.get("nha_cung_cap") or "Đại học Kinh tế Quốc dân",
               styles["cell"]),
            _p("cái", styles["cell"]),
            _p("1", styles["cell"]),
            _p(_format_money(gia_tri), styles["cell"]),
            _p(_format_money(gia_tri), styles["cell"]),
        ])
    if not tai_san_list:
        rows.append([_p("—", styles["cell"]) for _ in range(7)])
    rows.append([
        _p("", styles["cell"]), _p("<b>Cộng</b>", styles["cell"], markup=True),
        _p("", styles["cell"]), _p("x", styles["cell"]), _p("x", styles["cell"]),
        _p("x", styles["cell"]), _p(f"<b>{_format_money(tong_tien)}</b>", styles["cell"])
    ])
    table = Table(rows, colWidths=[11 * mm, 41 * mm, 39 * mm, 13 * mm, 17 * mm, 22 * mm, 22 * mm],
                  repeatRows=1)
    table.setStyle(_table_style())
    story.extend([
        table,
        Spacer(1, 5 * mm),
        _p(f"<b>Tổng số tiền (Viết bằng chữ):</b> {escape(doc_so_thanh_chu(tong_tien))}",
           styles["body"], markup=True),
        _p("<b>Ghi chú:</b> Đơn giá và thành tiền căn cứ giá trị ghi nhận của từng tài sản.",
           styles["small"], markup=True),
        Spacer(1, 8 * mm),
        Table([[
            _p("<b>Người mua</b><br/><br/><br/>(Ký, họ tên)", styles["subtitle"], markup=True),
            _p("<b>Kế toán trưởng</b><br/><br/><br/>(Ký, họ tên)", styles["subtitle"], markup=True),
            _p("<b>Người duyệt mua</b><br/><br/><br/>(Ký, họ tên)", styles["subtitle"], markup=True),
        ]], colWidths=[55 * mm, 55 * mm, 55 * mm])
    ])

    document.build(story)
    return output.getvalue()
