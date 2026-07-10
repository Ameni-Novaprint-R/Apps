#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génération PDF — Performance Report style KBA (template Projet 11).
Palette : logic.kba_report_theme (référence screenshot KBA).
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, String, Circle, Line, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie

from logic.kba_report_theme import KBA_COLORS, PIE_DISPO, PIE_TEMPS, PIE_VITESSE, BAR_NET, BAR_BRUT, BAR_PERF_MOY, BAR_PERF_MAX, BAR_TIRAGE


def _c(name):
    return colors.HexColor(KBA_COLORS[name])


C = {k: _c(k) for k in KBA_COLORS}
C["white"] = colors.white

PIE_DISPO_C = [_c(x) for x in PIE_DISPO]
PIE_TEMPS_C = [_c(x) for x in PIE_TEMPS]
PIE_VITESSE_C = [_c(x) for x in PIE_VITESSE]


def _fmt_num(value, decimals=0):
    if value is None:
        return "—"
    try:
        n = float(value)
    except (TypeError, ValueError):
        return "—"
    if decimals == 0:
        return f"{int(round(n)):,}".replace(",", ".")
    return f"{n:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_h(value):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _p(text, style):
    return Paragraph(text, style)


def _make_styles():
    return {
        "header_label": ParagraphStyle(
            "kba_hl", fontName="Helvetica", fontSize=7,
            textColor=C["text_muted"], alignment=TA_CENTER, leading=9,
        ),
        "header_value": ParagraphStyle(
            "kba_hv", fontName="Helvetica-Bold", fontSize=12,
            textColor=C["navy"], alignment=TA_CENTER, leading=14,
        ),
        "title": ParagraphStyle(
            "kba_title", fontName="Helvetica-Bold", fontSize=14,
            textColor=C["navy"], alignment=TA_CENTER, leading=17,
        ),
        "subtitle": ParagraphStyle(
            "kba_sub", fontName="Helvetica", fontSize=9,
            textColor=C["text_muted"], alignment=TA_CENTER, leading=11,
        ),
        "section": ParagraphStyle(
            "kba_sec", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=C["navy"], alignment=TA_CENTER, leading=9,
        ),
        "section_left": ParagraphStyle(
            "kba_sec_l", fontName="Helvetica-Bold", fontSize=7.5,
            textColor=C["navy"], alignment=0, leading=9,
        ),
        "detail": ParagraphStyle(
            "kba_det", fontName="Helvetica", fontSize=6,
            textColor=C["text"], alignment=0, leading=5,
        ),
        "kpi_big": ParagraphStyle(
            "kba_kpi", fontName="Helvetica-Bold", fontSize=20,
            textColor=C["navy"], alignment=TA_CENTER, leading=22,
        ),
        "kpi_label": ParagraphStyle(
            "kba_kl", fontName="Helvetica", fontSize=7.5,
            textColor=C["text_muted"], alignment=TA_CENTER, leading=9,
        ),
        "footer": ParagraphStyle(
            "kba_foot", fontName="Helvetica", fontSize=6.5,
            textColor=C["text_muted"], leading=8,
        ),
    }


def _red_line(width, y=0):
    d = Drawing(width, 4)
    d.add(Line(0, y + 2, width, y + 2, strokeColor=C["line_red"], strokeWidth=1.2))
    return d


def _make_pie(vals, pie_colors, width=100, height=82, center_text=None, empty_label="—"):
    d = Drawing(width, height)
    cx, cy, r = width / 2, height / 2 - 2, 30
    total = sum(v for v in vals if v is not None and v > 0)

    if total <= 0:
        d.add(Circle(cx, cy, r, fillColor=C["grey_light"], strokeColor=C["blue_steel"], strokeWidth=1))
        d.add(String(cx, cy - 3, empty_label, fontName="Helvetica-Bold", fontSize=9,
                     fillColor=C["grey_standby"], textAnchor="middle"))
        return d

    pc = Pie()
    pc.x = cx - 32
    pc.y = cy - 32
    pc.width = 64
    pc.height = 64
    pc.data = vals
    pc.slices.strokeWidth = 0.8
    pc.slices.strokeColor = C["white"]
    for i, col in enumerate(pie_colors):
        pc.slices[i].fillColor = col
    pc.slices.fontSize = 0
    pc.labels = None
    d.add(pc)

    if center_text:
        d.add(String(cx, cy + 2, center_text, fontName="Helvetica-Bold", fontSize=10,
                     fillColor=C["navy"], textAnchor="middle"))
    return d


def _numbered_circle_badge(num, color, size=12):
    """Pastille circulaire numérotée (style KBA)."""
    d = Drawing(size, size)
    cx, cy = size / 2, size / 2
    r = size / 2 - 1
    d.add(Circle(cx, cy, r, fillColor=color, strokeColor=C["white"], strokeWidth=0.6))
    d.add(String(
        cx, cy - 2.5, str(num),
        fontName="Helvetica-Bold", fontSize=6.5,
        fillColor=C["white"], textAnchor="middle",
    ))
    return d


def _detail_row(num, text, color, styles, text_width=None):
    """Ligne de légende avec pastille circulaire numérotée (style KBA)."""
    badge = _numbered_circle_badge(num, color)
    tw = text_width if text_width else 120
    row = Table([[badge, _p(text, styles["detail"])]], colWidths=[14, tw])
    row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return row


def _circle_section(title, drawing, detail_rows, col_w, styles):
    rows = [[_p(f"<b>{title}</b>", styles["section"])], [drawing]]
    if detail_rows:
        legend_t = Table([[dr] for dr in detail_rows], colWidths=[col_w])
        legend_t.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]))
        rows.append([legend_t])
    t = Table(rows, colWidths=[col_w])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (0, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("TOPPADDING", (1, 0), (1, 0), 1),
        ("BOTTOMPADDING", (1, 0), (1, 0), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _section_title(text, styles, left=False):
    key = "section_left" if left else "section"
    return _p(f"<b>{text}</b>", styles[key])


def _bar_chart_kba(labels, series_list, series_colors, width=520, height=62, value_axis_max=None):
    d = Drawing(width, height)
    bc = VerticalBarChart()
    bc.x = 34
    bc.y = 14
    bc.height = height - 28
    bc.width = width - 48
    bc.data = series_list
    bc.categoryAxis.categoryNames = labels
    bc.categoryAxis.labels.fontSize = 6
    bc.categoryAxis.labels.fillColor = C["text_muted"]
    bc.valueAxis.labels.fontSize = 5
    bc.valueAxis.labels.fillColor = C["text_muted"]
    bc.valueAxis.valueMin = 0
    if value_axis_max:
        bc.valueAxis.valueMax = value_axis_max
    bc.barWidth = 6
    bc.groupSpacing = 6
    bc.barSpacing = 1
    n_series = len(series_list)
    n_cats = len(labels)
    for si in range(n_series):
        col = series_colors[si % len(series_colors)]
        for bi in range(n_cats):
            bc.bars[(si, bi)].fillColor = col
            bc.bars[(si, bi)].strokeColor = C["navy"]
            bc.bars[(si, bi)].strokeWidth = 0.4
    d.add(bc)
    return d


def _legend(items, styles):
    row = []
    for label, color in items:
        swatch = Table([[""]], colWidths=[10], rowHeights=[10])
        swatch.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("BOX", (0, 0), (-1, -1), 0.4, C["navy"]),
        ]))
        row.append(Table([[swatch, _p(label, styles["footer"])]], colWidths=[12, 58]))
    t = Table([row], colWidths=[72] * len(row))
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


def _legend_vertical(items, styles, text_w=34):
    rows = []
    for label, color in items:
        swatch = Table([[""]], colWidths=[10], rowHeights=[10])
        swatch.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("BOX", (0, 0), (-1, -1), 0.4, C["navy"]),
        ]))
        rows.append([swatch, _p(label, styles["footer"])])
    t = Table(rows, colWidths=[12, text_w])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return t


def _line_chart_vitesse(moy, mx, width=92, height=74):
    """Courbe KBA : perf. moyenne (bleu) + perf. maximale (gris), avec repères mensuels."""
    d = Drawing(width, height)
    mx = [float(v or 0) for v in mx]
    moy = [float(v or 0) for v in moy]
    lc = HorizontalLineChart()
    lc.x = 6
    lc.y = 7
    lc.width = width - 12
    lc.height = height - 13
    lc.data = [mx, moy]
    lc.categoryAxis.visible = 0
    lc.categoryAxis.visibleTicks = 0
    lc.categoryAxis.visibleGrid = 0
    lc.valueAxis.visible = 0
    lc.valueAxis.visibleGrid = 0
    lc.valueAxis.valueMin = 0
    all_vals = [v for v in (moy + mx) if v is not None]
    lc.valueAxis.valueMax = (max(all_vals) * 1.15) if all_vals and max(all_vals) > 0 else 1
    lc.lines[0].strokeColor = C[BAR_PERF_MAX]
    lc.lines[0].strokeWidth = 1.4
    lc.lines[1].strokeColor = C[BAR_PERF_MOY]
    lc.lines[1].strokeWidth = 1.8
    # Ligne de base discrète
    d.add(Line(6, 7, width - 6, 7, strokeColor=C["grey_light"], strokeWidth=0.4))
    d.add(lc)
    return d


def _line_chart_simple(values, color, width=92, height=74):
    """Courbe KBA mono-série (ex. tirage moyen)."""
    d = Drawing(width, height)
    values = [float(v or 0) for v in values]
    lc = HorizontalLineChart()
    lc.x = 6
    lc.y = 7
    lc.width = width - 12
    lc.height = height - 13
    lc.data = [values]
    lc.categoryAxis.visible = 0
    lc.categoryAxis.visibleTicks = 0
    lc.categoryAxis.visibleGrid = 0
    lc.valueAxis.visible = 0
    lc.valueAxis.visibleGrid = 0
    lc.valueAxis.valueMin = 0
    lc.valueAxis.valueMax = (max(values) * 1.15) if values and max(values) > 0 else 1
    lc.lines[0].strokeColor = color
    lc.lines[0].strokeWidth = 1.8
    d.add(Line(6, 7, width - 6, 7, strokeColor=C["grey_light"], strokeWidth=0.4))
    d.add(lc)
    return d


def _tirage_section(hist, width, styles, kpi_value, kpi_label):
    """Bloc Tirage moyen style KBA : une seule section (titre + courbe + détails + KPI)."""
    hist_chrono = sorted(hist, key=lambda h: (h.get("annee", 0), h.get("mois", 0)))
    labels = [(h.get("mois_label") or "").lower() for h in hist_chrono]
    tirages = [h.get("tirage_moyen", 0) for h in hist_chrono]
    n = max(len(labels), 1)
    kpi_w = 88
    legend_w = 74
    chart_w = 110
    col_w = max((width - chart_w - legend_w - kpi_w - 8) / n, 34)

    chart = _line_chart_simple(tirages, C[BAR_TIRAGE], width=chart_w)
    month_row = Table(
        [[_p(lbl, styles["footer"]) for lbl in labels]],
        colWidths=[col_w] * n,
    )
    val_row = Table(
        [[_p(
            f'<b><font color="{KBA_COLORS["navy"]}">{_fmt_num(v)}</font></b>',
            styles["footer"],
        ) for v in tirages]],
        colWidths=[col_w] * n,
    )
    for tbl in (month_row, val_row):
        tbl.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))

    data_table = Table(
        [[month_row], [val_row]],
        colWidths=[col_w * n],
    )
    data_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    legend = _legend_vertical(
        [("Tirage moyen", C[BAR_TIRAGE])],
        styles, text_w=legend_w - 14,
    )
    kpi_col = Table([
        [_p(f'<font size="15"><b>{kpi_value}</b></font>', styles["kpi_big"])],
        [_p(kpi_label or "", styles["kpi_label"])],
    ], colWidths=[kpi_w])
    kpi_col.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    title_row = Table(
        [[_section_title("Tirage moyen", styles, left=True)]],
        colWidths=[width],
    )
    title_row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    body = Table(
        [[chart, data_table, legend, kpi_col]],
        colWidths=[chart_w, col_w * n, legend_w, kpi_w],
    )
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "LEFT"),
        ("ALIGN", (3, 0), (3, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (3, 0), (3, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    block = Table([[title_row], [body]], colWidths=[width])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, C["line_red"]),
    ]))
    return block


def _rating_bar(score, max_score=20, width=150, height=16):
    """Barre de notation KBA : petits rectangles pleins (score) + vides (reste)."""
    d = Drawing(width, height)
    gap = 1.5
    cell_w = (width - (max_score - 1) * gap) / max_score
    cell_h = height - 2
    try:
        filled = int(round(float(score))) if score is not None else 0
    except (TypeError, ValueError):
        filled = 0
    filled = max(0, min(max_score, filled))
    for i in range(max_score):
        x = i * (cell_w + gap)
        col = C["navy"] if i < filled else C["white"]
        d.add(Rect(x, 1, cell_w, cell_h,
                   fillColor=col, strokeColor=C["navy"], strokeWidth=0.5))
    return d


def _score_changement_section(data, mc, width, styles):
    """Section KBA : Performance Score (gauche) + Changement de travail (droite)."""
    score = (data.get("sections_telemetry") or {}).get("performance_score")
    score_txt = _fmt_num(score, 1) if score is not None else "—"
    chg_jour = mc.get("changements_moyen_jour", mc.get("changements_par_jour", 0))
    chg_total = mc.get("changements_total", 0)
    mois_label = (data.get("mois_label") or "").lower()

    # --- Bloc gauche : Performance Score ---
    score_num_bar = Table(
        [[
            _p(f'<font size="17"><b>{score_txt}</b></font>', styles["kpi_big"]),
            _rating_bar(score),
        ]],
        colWidths=[48, 152],
    )
    score_num_bar.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "RIGHT"),
        ("ALIGN", (1, 0), (1, 0), "LEFT"),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
    ]))
    left_block = Table(
        [
            [_section_title("Performance Score", styles, left=True)],
            [score_num_bar],
        ],
        colWidths=[width * 0.58],
    )
    left_block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    # --- Bloc droite : Changement de travail ---
    def _kpi(value, label):
        t = Table([
            [_p(f'<font size="17"><b>{value}</b></font>', styles["kpi_big"])],
            [_p(label, styles["kpi_label"])],
        ], colWidths=[80])
        t.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        return t

    right_block = Table(
        [
            [_section_title("Changement de travail", styles, left=False), ""],
            [_kpi(_fmt_num(chg_jour, 1), "en moyenne/jour"),
             _kpi(_fmt_num(chg_total), f"en {mois_label}")],
        ],
        colWidths=[width * 0.21, width * 0.21],
    )
    right_block.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    block = Table([[left_block, right_block]], colWidths=[width * 0.58, width * 0.42])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, C["line_red"]),
    ]))
    return block


def _vitesse_section(hist, width, styles, kpi_value, kpi_label):
    """Bloc Vitesse d'impression style KBA : une seule section (titre + courbe + détails + KPI)."""
    hist_chrono = sorted(hist, key=lambda h: (h.get("annee", 0), h.get("mois", 0)))
    labels = [(h.get("mois_label") or "").lower() for h in hist_chrono]
    moy = [h.get("cadence_moyenne", 0) for h in hist_chrono]
    mx = [h.get("cadence_max", 0) for h in hist_chrono]
    n = max(len(labels), 1)
    kpi_w = 88
    legend_w = 118
    col_w = max((width - 92 - legend_w - kpi_w - 8) / n, 34)

    chart = _line_chart_vitesse(moy, mx)
    month_row = Table(
        [[_p(lbl, styles["footer"]) for lbl in labels]],
        colWidths=[col_w] * n,
    )
    max_row = Table(
        [[_p(f"<b>{_fmt_num(v)}</b>", styles["footer"]) for v in mx]],
        colWidths=[col_w] * n,
    )
    moy_row = Table(
        [[_p(
            f'<b><font color="{KBA_COLORS["navy"]}">{_fmt_num(v)}</font></b>',
            styles["footer"],
        ) for v in moy]],
        colWidths=[col_w] * n,
    )
    for tbl in (month_row, max_row, moy_row):
        tbl.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))

    data_table = Table(
        [[month_row], [max_row], [moy_row]],
        colWidths=[col_w * n],
    )
    data_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    legend = _legend_vertical(
        [("Performance maximale (F/h)", C[BAR_PERF_MAX]),
         ("Performance moyenne (f/h)", C[BAR_PERF_MOY])],
        styles, text_w=legend_w - 14,
    )
    kpi_col = Table([
        [_p(f'<font size="15"><b>{kpi_value}</b></font>', styles["kpi_big"])],
        [_p(kpi_label or "", styles["kpi_label"])],
    ], colWidths=[kpi_w])
    kpi_col.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    title_row = Table(
        [[_section_title("Vitesse d'impression moyenne et maximale", styles, left=True)]],
        colWidths=[width],
    )
    title_row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    body = Table(
        [[chart, data_table, legend, kpi_col]],
        colWidths=[92, col_w * n, legend_w, kpi_w],
    )
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "LEFT"),
        ("ALIGN", (3, 0), (3, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (3, 0), (3, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    block = Table([[title_row], [body]], colWidths=[width])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, C["line_red"]),
    ]))
    return block


def _stacked_bar_productivite(nets, bruts, width=110, height=80):
    """Barres empilées KBA (dessin manuel) : net (bleu) + surplus brut (gris) au-dessus."""
    d = Drawing(width, height)
    n = len(bruts)
    if n == 0:
        return d

    pad_left, pad_right, pad_top, pad_bottom = 4, 2, 6, 7
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    bruts_f = [float(b or 0) for b in bruts]
    nets_f = [min(float(nt or 0), bf) for nt, bf in zip(nets, bruts_f)]
    max_v = max(bruts_f + [1.0])
    slot = plot_w / n
    bar_w = min(13, slot * 0.68)

    d.add(Line(pad_left, pad_bottom, width - pad_right, pad_bottom,
               strokeColor=C["grey_light"], strokeWidth=0.5))

    # Partie bleue = Net (fidèle). Partie grise = écart (Brut - Net) avec une
    # AMPLIFICATION VISUELLE (x GREY_AMP) pour rester lisible sur les faibles écarts.
    # Les données ne changent pas ; seul l'affichage de la coiffe est agrandi.
    GREY_AMP = 20.0
    for i in range(n):
        brut = bruts_f[i]
        net = nets_f[i]
        cx = pad_left + slot * i + slot / 2
        x = cx - bar_w / 2
        h_net = (net / max_v) * plot_h
        gap_real_h = ((brut - net) / max_v) * plot_h
        grey_h = gap_real_h * GREY_AMP
        # Garde-fou : la coiffe amplifiée ne dépasse jamais la hauteur du bleu
        if h_net > 0:
            grey_h = min(grey_h, h_net)

        if h_net > 0:
            d.add(Rect(x, pad_bottom, bar_w, h_net,
                       fillColor=C[BAR_NET], strokeColor=None))
        if grey_h > 0:
            d.add(Rect(x, pad_bottom + h_net, bar_w, grey_h,
                       fillColor=C[BAR_BRUT], strokeColor=None))
    return d


def _productivite_section(hist, width, styles, kpi_value, kpi_label):
    """Bloc Productivité style KBA : une seule section (titre + graphique + détails + KPI)."""
    hist_chrono = sorted(hist, key=lambda h: (h.get("annee", 0), h.get("mois", 0)))
    labels = [(h.get("mois_label") or "").lower() for h in hist_chrono]
    bruts = [h.get("feuilles_brut", h.get("total_operations", 0)) for h in hist_chrono]
    nets = [h.get("feuilles_net", h.get("total_operations", 0)) for h in hist_chrono]
    n = max(len(labels), 1)
    kpi_w = 88
    chart_w = 110
    col_w = max((width - chart_w - 50 - kpi_w - 8) / n, 38)

    chart = _stacked_bar_productivite(nets, bruts, width=chart_w)
    month_row = Table(
        [[_p(lbl, styles["footer"]) for lbl in labels]],
        colWidths=[col_w] * n,
    )
    brut_row = Table(
        [[_p(f"<b>{_fmt_num(v)}</b>", styles["footer"]) for v in bruts]],
        colWidths=[col_w] * n,
    )
    net_row = Table(
        [[_p(
            f'<b><font color="{KBA_COLORS["navy"]}">{_fmt_num(v)}</font></b>',
            styles["footer"],
        ) for v in nets]],
        colWidths=[col_w] * n,
    )
    for tbl in (month_row, brut_row, net_row):
        tbl.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))

    data_table = Table(
        [[month_row], [brut_row], [net_row]],
        colWidths=[col_w * n],
    )
    data_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    legend = _legend_vertical(
        [("brut", C[BAR_BRUT]), ("net", C[BAR_NET])],
        styles,
    )
    kpi_col = Table([
        [_p(f'<font size="15"><b>{kpi_value}</b></font>', styles["kpi_big"])],
        [_p(kpi_label or "", styles["kpi_label"])],
    ], colWidths=[kpi_w])
    kpi_col.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    title_row = Table(
        [[_section_title("Productivité (feuilles imprimées)", styles, left=True)]],
        colWidths=[width],
    )
    title_row.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (0, 0), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    body = Table(
        [[chart, data_table, legend, kpi_col]],
        colWidths=[chart_w, col_w * n, 50, kpi_w],
    )
    body.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ("ALIGN", (3, 0), (3, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (0, 0), 2),
        ("RIGHTPADDING", (3, 0), (3, 0), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    block = Table([[title_row], [body]], colWidths=[width])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, C["line_red"]),
    ]))
    return block


def _chart_section(
    title, legend_items, labels, series_list, series_colors, width,
    value_axis_max=None, values_row=None, chart_height=34,
    kpi_value=None, kpi_label=None, kpi_extra=None,
):
    """Bloc métrique pleine largeur : titre + KPI à droite, graphique, valeurs."""
    styles = _make_styles()
    chart_w = width - 8

    if kpi_value is not None:
        header = Table(
            [[
                _section_title(title, styles, left=True),
                Table([
                    [_p(f'<font size="15"><b>{kpi_value}</b></font>', styles["kpi_big"])],
                    [_p(kpi_label or "", styles["kpi_label"])],
                ], colWidths=[width * 0.28]),
            ]],
            colWidths=[width * 0.68, width * 0.32],
        )
        header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (0, 0), 4),
            ("RIGHTPADDING", (1, 0), (1, 0), 4),
        ]))
    else:
        header = _section_title(title, styles)

    rows = [
        [header],
        [_legend(legend_items, styles)],
        [_bar_chart_kba(
            labels, series_list, series_colors,
            width=int(chart_w), height=chart_height, value_axis_max=value_axis_max,
        )],
    ]
    col_w = chart_w / max(len(labels), 1)
    if values_row:
        rows.append([Table(
            [[_p(
                f'<b><font color="{KBA_COLORS["navy"]}">{_fmt_num(v)}</font></b>',
                styles["footer"],
            ) for v in values_row]],
            colWidths=[col_w] * len(labels),
        )])
    rows.append([Table(
        [[_p(l, styles["footer"]) for l in labels]],
        colWidths=[col_w] * len(labels),
    )])
    if kpi_extra:
        rows.append([_p(kpi_extra, styles["detail"])])

    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, C["line_red"]),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, C["line_red"]),
    ]))
    return t


def build_rapport_kba_pdf(data):
    """Génère le PDF Performance Report portrait (bytes)."""
    buffer = BytesIO()
    page_w, _ = A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=7 * mm,
        bottomMargin=7 * mm,
    )
    styles = _make_styles()
    story = []
    usable_w = page_w - 20 * mm

    mc = data.get("mois_courant") or {}
    hist = data.get("historique_graph") or []
    tel = data.get("sections_telemetry") or {}
    compteur = data.get("compteur") or {}

    labels_short = [(h.get("mois_label") or "")[:3] for h in hist]

    brut_c = data.get("compteur_brut") or compteur.get("max_cumul")
    net_c = data.get("compteur_net") or compteur.get("max_cumul")
    compteur_txt = f"{_fmt_num(brut_c)} / {_fmt_num(net_c)}" if brut_c or net_c else "— / —"

    # --- En-tête : Machine | Compteur — pleine largeur, gap central (réf. screenshot) ---
    header_gap = usable_w * 0.07
    field_w = (usable_w - header_gap) / 2

    def _header_field(label, value, width):
        t = Table([
            [_p(label, styles["header_label"])],
            [_p(f"<b>{value}</b>", styles["header_value"])],
        ], colWidths=[width], rowHeights=[14, 22])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.2, C["border_red"]),
            ("BACKGROUND", (0, 0), (-1, -1), C["white"]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (0, 0), 5),
            ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("TOPPADDING", (1, 0), (1, 0), 2),
            ("BOTTOMPADDING", (1, 0), (1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return t

    col_machine = _header_field("Machine", data.get("machine", ""), field_w)
    col_compteur = _header_field("Compteur feuilles brut / net", compteur_txt, field_w)
    info_box = Table(
        [[col_machine, "", col_compteur]],
        colWidths=[field_w, header_gap, field_w],
    )
    info_box.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (1, 0), (1, 0), C["white"]),
    ]))

    header_block = Table([
        [_p(f'Performance Report {data.get("titre_periode", "")}', styles["title"])],
        [info_box],
    ], colWidths=[usable_w])
    header_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C["white"]),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (1, 0), (1, 0), 8),
    ]))

    page_content = [header_block, Spacer(1, 4), _red_line(usable_w), Spacer(1, 14)]

    # --- 3 camemberts ---
    col_gap = 10
    col3_w = (usable_w - 2 * col_gap) / 3
    tw = int(col3_w - 18)
    tps_marche = tel.get("temps_impression_h") or mc.get("total_heures")
    tps_veille = tel.get("temps_veille_h")
    tps_arret = tel.get("temps_arret_h")
    tps_plaques = tel.get("temps_plaques_h")
    tps_lavage = tel.get("temps_lavage_h")

    t_prod = float(tps_marche or 0)
    t_arr = float(tps_arret or 0) if tps_arret is not None else 0
    t_vei = float(tps_veille or 0) if tps_veille is not None else 0
    dispo_vals = [t_prod, t_arr, t_vei]
    if sum(dispo_vals) > 0:
        dispo_pie = _make_pie(dispo_vals, PIE_DISPO_C, center_text=f"{_fmt_h(t_prod)} h")
    else:
        dispo_pie = _make_pie([], [], empty_label="—")

    dispo_details = [
        _detail_row(1, f"Temps de production &nbsp; <b>{_fmt_h(t_prod)}</b> h", C["navy"], styles, tw),
        _detail_row(2, f"Arrêt &nbsp; <b>{_fmt_h(tps_arret)}</b> h", C["red"], styles, tw),
        _detail_row(3, f"En mode veille &nbsp; <b>{_fmt_h(tps_veille)}</b> h", C["grey_standby"], styles, tw),
    ]

    t_imp = float(tps_marche or 0)
    t_plq = float(tps_plaques or 0) if tps_plaques is not None else 0
    t_lav = float(tps_lavage or 0) if tps_lavage is not None else 0
    temps_vals = [t_imp, t_lav, t_plq]
    temps_pie = _make_pie(
        temps_vals, PIE_TEMPS_C,
        center_text=f"{_fmt_h(t_imp)} h" if t_imp > 0 else None,
    )
    temps_details = [
        _detail_row(1, f"Temps d'impression &nbsp; <b>{_fmt_h(tps_marche)}</b> h", C["navy"], styles, tw),
        _detail_row(2, f"Temps de lavage &nbsp; <b>{_fmt_h(tps_lavage)}</b> h", C["blue_steel"], styles, tw),
        _detail_row(3, f"Temps chgmt plaques &nbsp; <b>{_fmt_h(tps_plaques)}</b> h", C["blue_mid"], styles, tw),
    ]

    vitesses = tel.get("vitesses") or [
        {"label": "< 8.000 f/h", "pct": None},
        {"label": "8.000 - 12.000 f/h", "pct": None},
        {"label": "12.000 - 16.000 f/h", "pct": None},
        {"label": "> 16.000 f/h", "pct": None},
    ]
    v_pcts, v_details, has_v = [], [], any(v.get("pct") is not None for v in vitesses)
    for i, v in enumerate(vitesses):
        pct = v.get("pct")
        if pct is not None:
            v_pcts.append(float(pct))
        elif has_v:
            v_pcts.append(0)
        pct_txt = f"{_fmt_num(pct, 1)} %" if pct is not None else "— %"
        v_details.append(_detail_row(
            i + 1, f'{v.get("label", "")} &nbsp; <b>{pct_txt}</b>',
            PIE_VITESSE_C[i % len(PIE_VITESSE_C)], styles, tw,
        ))

    vitesse_pie = (
        _make_pie(v_pcts, PIE_VITESSE_C)
        if has_v and sum(v_pcts) > 0
        else _make_pie([1, 1, 1, 1], PIE_VITESSE_C, empty_label="—")
    )

    row_circles = Table(
        [[
            _circle_section("Disponibilité", dispo_pie, dispo_details, col3_w, styles),
            "",
            _circle_section("Temps de production", temps_pie, temps_details, col3_w, styles),
            "",
            _circle_section("Vitesse de production", vitesse_pie, v_details, col3_w, styles),
        ]],
        colWidths=[col3_w, col_gap, col3_w, col_gap, col3_w],
    )
    row_circles.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C["white"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    page_content.append(row_circles)
    page_content.append(_red_line(usable_w))

    if hist:
        cad_moy = [h.get("cadence_moyenne", 0) for h in hist]
        chart_w = int(usable_w)
        tirages = [h.get("tirage_moyen", 0) for h in hist]

        page_content.append(_productivite_section(
            hist,
            width=chart_w,
            styles=styles,
            kpi_value=_fmt_num(mc.get("feuilles_net", mc.get("total_operations", 0))),
            kpi_label="Feuilles / mois (net)",
        ))

        page_content.append(_vitesse_section(
            hist,
            width=chart_w,
            styles=styles,
            kpi_value=_fmt_num(mc.get("cadence_moyenne", cad_moy[-1] if cad_moy else 0)),
            kpi_label="Performance moyenne (f/h)",
        ))

        page_content.append(_tirage_section(
            hist,
            width=chart_w,
            styles=styles,
            kpi_value=_fmt_num(mc.get("tirage_moyen", tirages[-1] if tirages else 0)),
            kpi_label="Feuilles",
        ))

        page_content.append(_score_changement_section(data, mc, chart_w, styles))

    footer_text = (
        f'<font color="{KBA_COLORS["red"]}"><b>A</b></font> Maint. retard · '
        f'<font color="{KBA_COLORS["navy"]}"><b>B</b></font> Maint. planifier · '
        f'<i>{data.get("source", "Projet 11")}</i>'
    )
    page_content.append(_red_line(usable_w))
    page_content.append(Table([[_p(footer_text, styles["footer"])]], colWidths=[usable_w]))

    story.append(KeepTogether(page_content))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
