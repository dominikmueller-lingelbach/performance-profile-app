from __future__ import annotations
from io import BytesIO
from typing import Dict, Any, List, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable, KeepTogether
)

# ============================================================
# IMPORT AUS ZENTRALER CONTENT-DATEI
# ============================================================
from report_content import (
    FUNCTION_NAMES, FUNCTION_ORDER, TYPE_MAP,
    MEANING_CARDS, CATEGORY_TEXT, get_band
)

# ============================================================
# PUBLIC API
# ============================================================
def build_pdf_report(payload: Dict[str, Any]) -> bytes:
    name = (payload.get("name") or "").strip() or "Kunde"
    email = (payload.get("email") or "").strip()
    ptype = (payload.get("profile_type") or "").strip() or "–"
    ranked_raw = payload.get("ranked") or []
    ranked = _normalize_ranked(ranked_raw)
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    if not ranked:
        ranked = [(fid, 0) for fid in FUNCTION_ORDER]
    top3 = ranked[:3]
    bottom2 = list(reversed(ranked[-2:]))
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Performance Profil Report"
    )
    styles = _build_styles()
    story: List[Any] = []
    # Seite 1: Sog
    story.extend(_page_1_sog(name, email, styles))
    story.append(PageBreak())
    # Seite 2: Webreport-Logik (Typ + Top/Bottom)
    story.extend(_page_2_web_snapshot(name, email, ptype, top3, bottom2, styles))
    story.append(PageBreak())
    # Seite 3: Bar Chart (einmal)
    story.extend(_page_3_bar_overview(ranked, styles))
    story.append(PageBreak())
    # Seite 4: Meaning Cards (Top3 + Bottom2)
    story.extend(_page_4_meaning_cards(top3, bottom2, styles))
    story.append(PageBreak())
    # 11 Kategorien
    perc_map = {fid: pct for fid, pct in ranked}
    for fid in FUNCTION_ORDER:
        pct = int(round(perc_map.get(fid, 0)))
        story.extend(_page_category(fid, pct, styles))
    # Abschluss / Actionplan / Zusammenarbeit (Sog)
    story.append(PageBreak())
    story.extend(_page_actionplan_and_outro(top3, bottom2, styles))
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()

# ============================================================
# STYLES / LOOK
# ============================================================
GREEN = colors.HexColor("#22c55e")
BORDER = colors.HexColor("#d7dbe0")
SOFT_BG = colors.HexColor("#f6f7f9")

def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "Brand": ParagraphStyle(
            "Brand", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=11, leading=13,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "Tag": ParagraphStyle(
            "Tag", parent=base["BodyText"],
            fontName="Helvetica", fontSize=9.5, leading=11,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#444444")
        ),
        "H0": ParagraphStyle(
            "H0", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=20, leading=22,
            spaceBefore=0, spaceAfter=2,
            textColor=colors.HexColor("#111111"),
            keepWithNext=1,
        ),
        "Muted": ParagraphStyle(
            "Muted", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10.5, leading=12.5,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#444444")
        ),
        "P": ParagraphStyle(
            "P", parent=base["BodyText"],
            fontName="Helvetica", fontSize=11, leading=13.2,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "Small": ParagraphStyle(
            "Small", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10, leading=12,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "Label": ParagraphStyle(
            "Label", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=10, leading=12,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "Quote": ParagraphStyle(
            "Quote", parent=base["BodyText"],
            fontName="Helvetica-Oblique", fontSize=12, leading=14,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "CardTitle": ParagraphStyle(
            "CardTitle", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=13, leading=15,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "CardBody": ParagraphStyle(
            "CardBody", parent=base["BodyText"],
            fontName="Helvetica", fontSize=11, leading=13,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
        "CardSteer": ParagraphStyle(
            "CardSteer", parent=base["BodyText"],
            fontName="Helvetica", fontSize=11, leading=13,
            spaceBefore=0, spaceAfter=0,
            textColor=colors.HexColor("#111111")
        ),
    }
    return styles

def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(16*mm, 9*mm, "Performance Profil · Individuelle Auswertung")
    canvas.drawRightString(A4[0]-16*mm, 9*mm, f"Seite {doc.page}")
    canvas.restoreState()

def _topline_brand(name: str, email: str, styles):
    who = name if not email else f"{name} · {email}"
    top = Table([[Paragraph("Performance Profil", styles["Brand"]), Paragraph(_esc(who), styles["Tag"])]],
                colWidths=[None, 70*mm])
    top.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    return top

def _box(title: str, content: List[Any], styles, pad=10, fillColor=colors.white,
         strokeColor=BORDER, strokeWidth=0.7) -> Table:
    head = Paragraph(f"<b>{_esc(title)}</b>", styles["Label"])
    rows = [[head]]
    for c in content:
        rows.append([c])
    t = Table(rows, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, 1), 7),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor("#e5e7eb")),
    ]))
    return RoundedCard(
        t, radius=6, stroke=strokeWidth,
        strokeColor=strokeColor, fillColor=fillColor, padding=6
    )

def _soft_card(title_left: str, title_right: str, body, styles) -> Table:
    head = Table(
        [[
            Paragraph(f"<b>{_esc(title_left)}</b>", styles["Label"]),
            Paragraph(f"<b>{_esc(title_right)}</b>", styles["Label"]),
        ]],
        colWidths=[None, 24 * mm],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 0.6, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
    ]))
    if isinstance(body, str):
        body_flow = Paragraph(_esc(body or ""), styles["P"])
    else:
        body_flow = body
    t = Table([[head], [body_flow]], colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor("#e5e7eb")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
    ]))
    return RoundedCard(t, radius=6, stroke=0.7, strokeColor=BORDER, fillColor=colors.HexColor("#f8fafc"), padding=6)

def _bar(pct: int, width_mm: int = 160, height_mm: int = 4):
    return RoundedProgressBar(pct, width_mm=width_mm, height_mm=height_mm)

# ============================================================
# PAGES
# ============================================================
def _page_1_sog(name: str, email: str, styles):
    story: List[Any] = []
    story.append(_topline_brand(name, email, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Deine individuelle Leistungsarchitektur", styles["H0"]))
    story.append(Spacer(1, 6))
    story.append(_box("Wichtig", [
        Paragraph("Das hier ist kein Persönlichkeitstest.", styles["P"]),
        Paragraph("Was du jetzt in den Händen hältst, ist eine Landkarte deiner Leistungsmechanik.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Sie zeigt dir nicht, wer du bist – sondern <b>wie du Leistung erzeugst</b>.", styles["P"]),
        Paragraph("Und warum sie manchmal kommt – und manchmal nicht.", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Worum es wirklich geht", [
        Paragraph("Die meisten Menschen arbeiten an Motivation, Zielen und Disziplin.", styles["P"]),
        Paragraph("Top-Performer arbeiten an etwas anderem: <b>Zugriff</b>.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Zugriff auf Klarheit.", styles["P"]),
        Paragraph("Zugriff auf Entscheidungskraft.", styles["P"]),
        Paragraph("Zugriff auf Leistung – genau dann, wenn es zählt.", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Wie du diesen Report liest", [
        Paragraph("Nicht wie einen Text – sondern wie einen Spiegel.", styles["P"]),
        Spacer(1, 4),
        Paragraph("<b>Wichtig: Es geht nicht darum, überall HOCH zu erreichen.</b>", styles["P"]),
        Paragraph("Dieses Profil zeigt deine individuelle Leistungsarchitektur – nicht einen Idealzustand, den du erreichen musst. Jede Ausprägung hat eine Funktion. Niedrig ist nicht schlecht. Hoch ist nicht automatisch gut. Entscheidend ist, dass du erkennst, wie du unter Druck funktionierst – und wie du das gezielt für dich nutzt.", styles["P"]),
        Spacer(1, 4),
        Paragraph("In jeder Kategorie findest du drei Bereiche (hoch/mittel/niedrig).", styles["P"]),
        Paragraph("Dein Bereich ist markiert (grüner Rahmen). Die anderen beiden dienen als Kontext – damit du verstehst, wie Leistung entsteht oder kippt.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Wenn du an mehreren Stellen denkst: <b>Verdammt - das bin genau ich</b> → dann funktioniert dieser Report.", styles["P"]),
        Paragraph("Wenn du Widerstand spürst → dann triffst du gerade auf deine Reibung.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Beides ist wertvoll. Beides ist steuerbar.", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Leistung ist kein Zufall. Sie entsteht dort, wo Klarheit, Steuerung und Verantwortung zusammenkommen.", styles["Quote"]))
    return story

def _page_2_web_snapshot(name: str, email: str, ptype: str, top3, bottom2, styles):
    story: List[Any] = []
    story.append(_topline_brand(name, email, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Dein Ergebnis ist da.", styles["H0"]))
    story.append(Paragraph("Du siehst nicht wer du bist, sondern <b>wie du unter Druck funktionierst</b> – und wie du das steuerst.", styles["Muted"]))
    story.append(Spacer(1, 6))
    t = TYPE_MAP.get(ptype, None) or {"name": f"Typ {ptype}", "label": "—", "hint": "—", "explain": "—"}
    type_head = Table([
        [
            Badge(_esc(ptype)),
            Paragraph(
                f"<font size='15'><b>{_esc(t['name'])}</b></font><br/>"
                f"<font size='10' color='#444444'>{_esc(t['hint'])}</font>",
                styles["P"]
            )
        ]
    ], colWidths=[12*mm, None])
    type_head.setStyle(TableStyle([
        ("ALIGN", (0,0), (0,0), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    left = _box("Dein Performance-Modus (Arbeitsmodus)", [
        type_head,
        Spacer(1, 6),
        _soft_card(t["label"], "", _format_explain(t["explain"], styles), styles)
    ], styles)
    right = _box("Kurz-Auswertung", [
        _list_block("Deine stärksten Hebel (Top 3)", top3, styles),
        Spacer(1, 6),
        _list_block("Deine Reibungszonen (2 niedrigste)", bottom2, styles),
        Spacer(1, 6),
        Paragraph("Hinweis: Es geht nicht darum, überall HOCH zu sein. Entscheidend ist, dass du weißt, <b>wo du Leistung holst</b> und <b>wo Reibung entsteht</b> – damit du gezielt steuerst.", styles["Muted"])
    ], styles)
    grid = Table([[left, "", right]], colWidths=[86*mm, 6*mm, None])
    grid.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(grid)
    return story

def _list_block(title: str, arr, styles):
    rows = []
    for fid, pct in arr:
        rows.append([
            Paragraph(f"<b>{_esc(FUNCTION_NAMES.get(fid, fid))}</b>", styles["P"]),
            "",
            Paragraph(f"<b>{int(pct)}%</b>", styles["P"]),
        ])
    tbl = Table(rows, colWidths=[None, 6*mm, 18*mm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, colors.HexColor("#f7f8fa")]),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ALIGN", (2,0), (2,-1), "RIGHT"),
        ("RIGHTPADDING", (2,0), (2,-1), 2),
    ]))
    return _box(title, [tbl], styles)

def _page_3_bar_overview(ranked, styles):
    story: List[Any] = []
    story.append(Paragraph("Dein Profil (Bar Chart)", styles["H0"]))
    story.append(Paragraph("Alle 11 Funktionen im Überblick – als klare Ausgangslage.", styles["Muted"]))
    story.append(Spacer(1, 6))
    rows = []
    for fid, pct in ranked:
        rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), styles["Small"]),
            _bar(int(pct), width_mm=105, height_mm=4),
            Paragraph(f"<b>{int(pct)}%</b>", styles["Small"]),
        ])
    tbl = Table(rows, colWidths=[58*mm, None, 16*mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 0.3, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(_box("Dein Profil", [tbl], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Einordnung der Prozentwerte", [
        Paragraph("<b>0–25 %:</b> niedrig ausgeprägt – das bedeutet nicht schlecht. Es zeigt, dass dieser Bereich unter Druck weniger Zugriff liefert. Hier lohnt es sich, gezielt zu steuern.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>25–75 %:</b> mittel ausgeprägt – flexibel einsetzbar, kann je nach Situation tragen oder kippen. Bewusste Steuerung macht den Unterschied.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>75–100 %:</b> hoch ausgeprägt – ein starker Hebel, wenn du ihn bewusst einsetzt. Aber: Hoch ist kein Ziel an sich. Es geht darum, dein Profil zu kennen und zu nutzen – nicht darum, überall hoch zu sein.", styles["P"]),
    ], styles))
    return story

def _page_4_meaning_cards(top3, bottom2, styles):
    story: List[Any] = []
    story.append(Paragraph("Was das konkret bedeutet", styles["H0"]))
    story.append(Paragraph("Dein Profil ist individuell – es gibt kein Richtig oder Falsch. Hier siehst du, wo du <b>Leistung gewinnst</b> und wo <b>Reibung entsteht</b>. Beides ist steuerbar.", styles["Muted"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Deine stärksten Hebel</b>", styles["Label"]))
    story.append(Spacer(1, 6))
    for fid, pct in top3:
        story.append(_meaning_web_card(fid, int(pct), mode="top", styles=styles))
        story.append(Spacer(1, 6))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Deine Reibungszonen</b>", styles["Label"]))
    story.append(Spacer(1, 6))
    for fid, pct in bottom2:
        story.append(_meaning_web_card(fid, int(pct), mode="low", styles=styles))
        story.append(Spacer(1, 6))
    story.append(Paragraph("Deine Top-Hebel sind deine stärksten Wirkungen. Deine Reibungszonen zeigen, wo du unter Druck unnötig Leistung verlierst. Beides gehört zu dir – und beides ist steuerbar. Das Ziel ist nicht, überall hoch zu sein. Das Ziel ist, dein Profil zu kennen und gezielt zu nutzen.", styles["Muted"]))
    return story

def _page_category(fid: str, pct: int, styles):
    t = CATEGORY_TEXT.get(fid)
    if not t:
        t = {"title": FUNCTION_NAMES.get(fid, fid), "worum": ["(Text fehlt)"], "hoch": ["(Text fehlt)"], "mittel": ["(Text fehlt)"], "niedrig": ["(Text fehlt)"], "praxis": ["(Text fehlt)"] * 3, "merksatz": "(Text fehlt)"}
    band = get_band(pct)
    story: List[Any] = []
    header_pack = KeepTogether([
        Paragraph(_esc(t["title"]), styles["H0"]),
        Paragraph(f"Aktueller Wert: <b>{pct} %</b> · Einordnung: <b>{_esc(band)}</b>", styles["Muted"]),
        Spacer(1, 6),
        _bar(pct, 160, 4),
        Spacer(1, 6),
        _box("Worum es hier wirklich geht", [_lines_to_paragraph(t["worum"], styles)], styles),
        Spacer(1, 6),
    ])
    story.append(header_pack)
    block_titles = {
        "hoch":    "Wenn der Wert hoch ist (75–100 %)",
        "mittel":  "Wenn der Wert im mittleren Bereich liegt (25–75 %)",
        "niedrig": "Wenn der Wert niedrig ist (0–25 %)",
    }
    def _clean_lines(lines: List[str]) -> List[str]:
        out = []
        for ln in lines:
            s = (ln or "").strip()
            if s.startswith("(") and "Orientierung" in s:
                continue
            out.append(ln)
        return out

    for b in ["hoch", "mittel", "niedrig"]:
        is_active = (b == band)
        fill = colors.HexColor("#ecfdf5") if is_active else colors.white
        stroke = GREEN if is_active else BORDER
        sw = 2.0 if is_active else 0.7
        title = block_titles[b]
        if is_active:
            title = "DEIN BEREICH · " + title
        story.append(
            _box(title, [_lines_to_paragraph(_clean_lines(t[b]), styles)], styles,
                 fillColor=fill, strokeColor=stroke, strokeWidth=sw)
        )
        story.append(Spacer(1, 6))

    pr = t.get("praxis", [])[:3]
    rows = []
    for i, line in enumerate(pr):
        rows.append([
            Paragraph(f"<b>{i+1}.</b>", styles["P"]),
            Paragraph(_esc(line), styles["P"]),
        ])
    praxis_table = Table(rows, colWidths=[8 * mm, None])
    praxis_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(_box("Praxisregeln – so steuerst du diesen Hebel", [praxis_table], styles))
    story.append(Spacer(1, 4))
    story.append(_box("Merksatz", [Paragraph(_esc(t.get("merksatz", "")), styles["P"])], styles))
    story.append(Spacer(1, 14))
    return story

def _page_actionplan_and_outro(top3, bottom2, styles):
    story: List[Any] = []
    top_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in top3])
    low_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in bottom2])
    h = Paragraph("Actionplan & nächste Schritte", styles["H0"])
    h.keepWithNext = 1
    story.append(h)
    story.append(Spacer(1, 6))
    sog = Paragraph("<b>Leistung ist kein Zufall. Leistung ist steuerbar.</b>", styles["P"])
    sog.keepWithNext = 1
    story.append(sog)
    story.append(Spacer(1, 6))
    story.append(_box("Dein Fokus (14 Tage)", [
        Paragraph(f"<b>Top-Hebel nutzen:</b> {_esc(top_names)}", styles["P"]),
        Paragraph("Wähle <b>eine</b> Praxisregel aus deinem stärksten Hebel – und setze sie täglich um.", styles["P"]),
        Spacer(1, 2),
        Paragraph(f"<b>Reibung reduzieren:</b> {_esc(low_names)}", styles["P"]),
        Paragraph("Wähle <b>eine</b> Praxisregel aus deiner Reibungszone – und mache sie zur Pflicht.", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Abschluss", [
        Paragraph("Dieses Profil ist kein Urteil.", styles["P"]),
        Paragraph("Und es ist keine Motivation.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Es ist eine Landkarte.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Sie zeigt dir nicht, wer du bist, sondern wie du Leistung erzeugst – und warum sie unter Druck manchmal abrufbar ist und manchmal nicht.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Du hast jetzt gesehen, wo dein Zugriff stabil ist, wo er kippt und welche Muster darüber entscheiden, ob Leistung kommt – oder verloren geht.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Das allein ist wertvoll.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Doch Klarheit allein ändert gar nichts.</b>", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Was jetzt entscheidet", [
        Paragraph("Der Unterschied entsteht nicht im Verstehen. Er entsteht dort, wo Entscheidungen getroffen werden – auch wenn sie unbequem sind.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Unter Druck. Unter Verantwortung. Unter Erwartung.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Und genau hier scheitern selbst sehr erfolgreiche Menschen. Nicht, weil sie zu wenig wissen. Nicht, weil ihnen Disziplin fehlt. Sondern weil ihrem System unter Druck der Zugriff fehlt.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Ich arbeite nicht an Motivation. Ich baue Systeme, damit Leistung unter Druck abrufbar wird.</b>", styles["P"]),
        Spacer(1, 2),
        Paragraph("Nicht theoretisch. Nicht im Idealzustand. Sondern genau dort, wo Führung, Verantwortung und Entscheidung wirklich stattfinden.", styles["P"]),
    ], styles))
    story.append(Spacer(1, 6))
    story.append(_box("Deine Entscheidung", [
        Paragraph("Denn Leistung ist kein Zufall. Sie ist das Ergebnis von Struktur, Steuerung und der Fähigkeit, sich selbst im entscheidenden Moment zu führen.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Und jetzt kommt der entscheidende Punkt:</b>", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Die Frage ist nicht, ob du mehr Potenzial hast. Die Frage ist, wie lange du es noch ungenutzt lassen willst.</b>", styles["P"]),
        Spacer(1, 2),
        Paragraph("Du kannst dieses Profil schließen und weitermachen wie bisher. Vieles wird weiterhin funktionieren. Doch Frust, Hilflosigkeit und Leistungsverlust werden sich immer wiederholen.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Oder du entscheidest dich, dein Leistungssystem nicht länger dem Zufall zu überlassen.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Für Menschen, die führen. Verantwortung tragen. Und mehr wollen als nur funktionieren.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Für Menschen, die wissen, dass ihr nächster Schritt nicht aus weiterem Input entsteht, sondern aus klarer Spiegelung, konsequenter Steuerung und einem System, das auch dann trägt, wenn der Druck am größten wird.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Wenn du beim Lesen gespürt hast, dass hier etwas trifft, das tiefer geht als Motivation oder Mindset, dann ist das kein Zufall.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Dann bist du genau an dem Punkt, an dem echte Performance-Arbeit beginnt.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Nicht für jeden. Sondern für die, die sich entscheiden, einen Unterschied machen zu wollen.</b>", styles["P"]),
        Spacer(1, 2),
        Paragraph("Wenn du willst, ist das hier nicht das Ende dieses Reports. Sondern der Anfang einer Phase, in der Leistung reproduzierbar, Führung klar und Erfolg steuerbar wird.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Sag mir Bescheid, wenn du bereit bist.</b>", styles["P"]),
    ], styles))
    return story

# ============================================================
# HELPERS
# ============================================================
def _normalize_ranked(ranked) -> List[Tuple[str, int]]:
    if not ranked:
        return []
    if isinstance(ranked, list):
        out = []
        for item in ranked:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    out.append((str(item[0]), int(round(float(item[1])))))
                except Exception:
                    out.append((str(item[0]), 0))
        return out
    if isinstance(ranked, dict):
        out = []
        for k, v in ranked.items():
            try:
                out.append((str(k), int(round(float(v)))))
            except Exception:
                out.append((str(k), 0))
        return out
    return []

def _esc(s: str) -> str:
    s = (s or "")
    s = s.replace("\xad", "").replace("\u200b", "").replace("\u2060", "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _lines_to_paragraph(lines: List[str], styles, bullet_prefix: str = "") -> Paragraph:
    paras: List[str] = []
    cur_lines: List[str] = []
    def flush():
        nonlocal cur_lines
        if cur_lines:
            paras.append("<br/>".join(cur_lines))
            cur_lines = []
    for ln in lines:
        s = (ln or "").strip()
        if not s:
            flush()
            continue
        if s.startswith(("•", "-", "–")):
            item = s.lstrip("•-–").strip()
            pref = (bullet_prefix or "").strip()
            if pref:
                cur_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(pref)}&nbsp;&nbsp;{_esc(item)}")
            else:
                cur_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(item)}")
            continue
        cur_lines.append(_esc(s))
    flush()
    html = "<br/><br/>".join(paras)
    return Paragraph(html, styles["P"])

def _format_explain(text: str, styles):
    text = (text or "").strip()
    if not text:
        return Paragraph("", styles["P"])
    if "Führung:" not in text:
        return Paragraph(_esc(text), styles["P"])
    before, after = text.split("Führung:", 1)
    before = before.strip()
    after = after.strip()
    rows = []
    if before:
        rows.append([Paragraph(_esc(before), styles["P"])])
    rows.append([Spacer(1, 4)])
    rows.append([Paragraph(f"<b>Führung:</b> {_esc(after)}", styles["P"])])
    t = Table(rows, colWidths=[None])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    return t

def _tmp_style(size: int, bold: bool = False, color: str = "#111111") -> ParagraphStyle:
    base = getSampleStyleSheet()["BodyText"]
    return ParagraphStyle(
        f"TMP_{size}_{'B' if bold else 'R'}",
        parent=base,
        fontName="Helvetica-Bold" if bold else "Helvetica",
        fontSize=size,
        leading=size + 2,
        textColor=colors.HexColor(color)
    )

def _meaning_web_card(fid: str, pct: int, mode: str, styles):
    tag_left = "Top-Hebel" if mode == "top" else "Reibungszone"
    card = MEANING_CARDS.get(fid, {})
    title = FUNCTION_NAMES.get(fid, fid)
    desc = card.get("top", "") if mode == "top" else card.get("low", "")
    steer = card.get("steer", "")
    title_style = _tmp_style(13, bold=True, color="#111111")
    head = Table(
        [[
            Paragraph(f"<b>{_esc(tag_left)}</b>", styles["Label"]),
            Paragraph(f"<b>{int(pct)}%</b>", styles["Label"]),
        ]],
        colWidths=[None, 24 * mm],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LINEBELOW", (0,0), (-1,0), 0.6, BORDER),
    ]))
    body_title = Paragraph(_esc(title), title_style)
    body_desc = Paragraph(_esc(desc), styles["P"])
    steer_style = ParagraphStyle(
        "Steer", parent=styles["P"],
        fontSize=10.5, leading=12.5,
        textColor=colors.HexColor("#444444"),
        spaceBefore=0, spaceAfter=0,
    )
    body_steer = Paragraph(f"<b>Steuerung:</b> {_esc(steer)}", steer_style)
    t = Table([[head], [body_title], [body_desc], [body_steer]], colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, 1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 5),
        ("TOPPADDING", (0, 2), (-1, 2), 0),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 5),
        ("LINEABOVE", (0, 3), (-1, 3), 0.4, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 3), (-1, 3), 5),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 0),
    ]))
    return RoundedCard(t, radius=6, stroke=0.7, strokeColor=BORDER, fillColor=colors.HexColor("#f8fafc"), padding=6)

# ============================================================
# CUSTOM FLOWABLES
# ============================================================
class RoundedProgressBar(Flowable):
    def __init__(self, pct, width_mm=160, height_mm=4, radius_mm=None,
                 fillColor=GREEN, backColor=colors.HexColor("#e5e7eb"),
                 strokeColor=colors.HexColor("#d1d5db"), strokeWidth=0.6):
        super().__init__()
        self.pct = max(0, min(100, int(pct)))
        self.width = width_mm * mm
        self.height = height_mm * mm
        self.radius = (radius_mm * mm) if radius_mm is not None else (self.height / 2)
        self.fillColor = fillColor
        self.backColor = backColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        r = min(self.radius, self.height / 2)
        c.setLineWidth(self.strokeWidth)
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.backColor)
        c.roundRect(0, 0, self.width, self.height, r, stroke=1, fill=1)
        fill_w = (self.pct / 100.0) * self.width
        if fill_w > 0:
            c.setStrokeColor(self.fillColor)
            c.setFillColor(self.fillColor)
            r2 = min(r, fill_w / 2)
            c.roundRect(0, 0, fill_w, self.height, r2, stroke=0, fill=1)
        c.restoreState()

class Badge(Flowable):
    def __init__(self, text, w=12*mm, h=12*mm, radius=3, stroke=0.9,
                 strokeColor=GREEN, fillColor=colors.HexColor("#e9f7ef")):
        super().__init__()
        self.text = text
        self.w = w
        self.h = h
        self.radius = radius
        self.stroke = stroke
        self.strokeColor = strokeColor
        self.fillColor = fillColor

    def wrap(self, availWidth, availHeight):
        return self.w, self.h

    def draw(self):
        c = self.canv
        c.saveState()
        c.setLineWidth(self.stroke)
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.fillColor)
        c.roundRect(0, 0, self.w, self.h, self.radius, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#0b5d2a"))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.w / 2, (self.h / 2) - 6, self.text)
        c.restoreState()

class RoundedCard(Flowable):
    def __init__(self, inner, radius=6, stroke=1, strokeColor=BORDER,
                 fillColor=colors.white, padding=8):
        super().__init__()
        self.inner = inner
        self.radius = radius
        self.stroke = stroke
        self.strokeColor = strokeColor
        self.fillColor = fillColor
        self.padding = padding

    def wrap(self, availWidth, availHeight):
        iw, ih = self.inner.wrap(availWidth - 2 * self.padding, availHeight)
        self.width = availWidth
        self.height = ih + 2 * self.padding
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.fillColor)
        c.setLineWidth(self.stroke)
        c.roundRect(0, 0, self.width, self.height, self.radius, stroke=1, fill=1)
        self.inner.drawOn(c, self.padding, self.padding)
        c.restoreState()
