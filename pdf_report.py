from __future__ import annotations
from io import BytesIO
from typing import Dict, Any, List, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable, KeepTogether, HRFlowable
)

from report_content import (
    FUNCTION_NAMES, FUNCTION_ORDER, TYPE_MAP,
    MEANING_CARDS, CATEGORY_TEXT, get_band
)

# ============================================================
# DESIGN CONSTANTS
# ============================================================
GREEN       = colors.HexColor("#22c55e")
DARK_GREEN  = colors.HexColor("#166534")
LIGHT_GREEN = colors.HexColor("#ecfdf5")
ACCENT_BG   = colors.HexColor("#f0fdf4")
DARK        = colors.HexColor("#0f172a")
MEDIUM      = colors.HexColor("#334155")
MUTED_CLR   = colors.HexColor("#64748b")
BORDER      = colors.HexColor("#e2e8f0")
LIGHT_BG    = colors.HexColor("#f8fafc")
CARD_BG     = colors.HexColor("#ffffff")
PAGE_W, PAGE_H = A4
MARGIN_L = 18 * mm
MARGIN_R = 18 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R

# ============================================================
# PUBLIC API
# ============================================================
def build_pdf_report(payload: Dict[str, Any]) -> bytes:
    name = (payload.get("name") or "").strip() or "Kunde"
    email = (payload.get("email") or "").strip()
    ptype = (payload.get("profile_type") or "").strip() or "-"
    ranked_raw = payload.get("ranked") or []
    ranked = _normalize_ranked(ranked_raw)
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    if not ranked:
        ranked = [(fid, 0) for fid in FUNCTION_ORDER]
    top3 = ranked[:3]
    bottom2 = list(reversed(ranked[-2:]))

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title="Performance Profil Report"
    )
    S = _build_styles()
    story: List[Any] = []

    # Seite 1: Einstieg (mit Hinweis auf Kompaktauswertung am Ende)
    story.extend(_page_cover(name, email, S))
    story.append(PageBreak())

    # Seite 2: Bar Chart Gesamtübersicht
    story.extend(_page_bar_overview(ranked, S))
    story.append(PageBreak())

    # Seite 3: Meaning Cards (Top-Hebel + Reibungszonen)
    story.extend(_page_meaning_cards(top3, bottom2, S))
    story.append(PageBreak())

    # Seite 4-24: 11 Kategorien im Detail
    perc_map = {fid: pct for fid, pct in ranked}
    for fid in FUNCTION_ORDER:
        pct = int(round(perc_map.get(fid, 0)))
        story.extend(_page_category(fid, pct, S))

    # Actionplan
    story.append(PageBreak())
    story.extend(_page_actionplan(top3, bottom2, S))

    # LETZTE SEITE: Kompaktauswertung (One-Pager)
    story.append(PageBreak())
    story.extend(_page_compact_overview(name, email, ptype, ranked, top3, bottom2, S))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()

# ============================================================
# STYLES
# ============================================================
def _build_styles():
    base = getSampleStyleSheet()
    return {
        "H0": ParagraphStyle("H0", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=22, leading=26,
            spaceBefore=0, spaceAfter=4, textColor=DARK, keepWithNext=1),
        "H1": ParagraphStyle("H1", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=16, leading=19,
            spaceBefore=0, spaceAfter=2, textColor=DARK, keepWithNext=1),
        "H2": ParagraphStyle("H2", parent=base["Heading3"],
            fontName="Helvetica-Bold", fontSize=13, leading=16,
            spaceBefore=0, spaceAfter=2, textColor=DARK),
        "P": ParagraphStyle("P", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10.5, leading=14,
            spaceBefore=0, spaceAfter=0, textColor=DARK),
        "Ps": ParagraphStyle("Ps", parent=base["BodyText"],
            fontName="Helvetica", fontSize=9.5, leading=12.5,
            spaceBefore=0, spaceAfter=0, textColor=DARK),
        "Muted": ParagraphStyle("Muted", parent=base["BodyText"],
            fontName="Helvetica", fontSize=10, leading=13,
            spaceBefore=0, spaceAfter=0, textColor=MUTED_CLR),
        "MutedS": ParagraphStyle("MutedS", parent=base["BodyText"],
            fontName="Helvetica", fontSize=9, leading=11.5,
            spaceBefore=0, spaceAfter=0, textColor=MUTED_CLR),
        "Label": ParagraphStyle("Label", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=9, leading=11,
            spaceBefore=0, spaceAfter=0, textColor=MUTED_CLR),
        "LabelGreen": ParagraphStyle("LabelGreen", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=9, leading=11,
            spaceBefore=0, spaceAfter=0, textColor=DARK_GREEN),
        "Brand": ParagraphStyle("Brand", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=10, leading=12,
            spaceBefore=0, spaceAfter=0, textColor=DARK),
        "Tag": ParagraphStyle("Tag", parent=base["BodyText"],
            fontName="Helvetica", fontSize=8.5, leading=10,
            spaceBefore=0, spaceAfter=0, textColor=MUTED_CLR),
        "Quote": ParagraphStyle("Quote", parent=base["BodyText"],
            fontName="Helvetica-Oblique", fontSize=11, leading=14,
            spaceBefore=0, spaceAfter=0, textColor=MEDIUM),
        "Big": ParagraphStyle("Big", parent=base["BodyText"],
            fontName="Helvetica-Bold", fontSize=28, leading=32,
            spaceBefore=0, spaceAfter=0, textColor=DARK),
    }

# ============================================================
# HEADER / FOOTER
# ============================================================
def _header_footer(canvas, doc):
    canvas.saveState()
    # Green accent line top
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(2.5)
    canvas.line(MARGIN_L, PAGE_H - 10*mm, PAGE_W - MARGIN_R, PAGE_H - 10*mm)
    # Footer
    canvas.setFillColor(MUTED_CLR)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGIN_L, 10*mm, "Performance Profil  |  Individuelle Auswertung")
    canvas.drawRightString(PAGE_W - MARGIN_R, 10*mm, f"Seite {doc.page}")
    canvas.restoreState()

# ============================================================
# PAGE: COVER (Seite 1)
# ============================================================
def _page_cover(name, email, S):
    story = []
    story.append(Spacer(1, 30))
    story.append(Paragraph("PERFORMANCE PROFIL", S["Label"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Deine individuelle<br/>Leistungsarchitektur", S["H0"]))
    story.append(Spacer(1, 4))
    who = f"{name}  |  {email}" if email else name
    story.append(Paragraph(_esc(who), S["Muted"]))
    story.append(Spacer(1, 20))
    story.append(GreenLine())
    story.append(Spacer(1, 20))

    story.append(_card("Wichtig", [
        Paragraph("Das hier ist kein Persönlichkeitstest.", S["P"]),
        Spacer(1, 3),
        Paragraph("Was du jetzt in den Händen hältst, ist eine <b>Landkarte deiner Leistungsmechanik</b>. Sie zeigt dir nicht, wer du bist - sondern <b>wie du Leistung erzeugst</b>. Und warum sie manchmal kommt - und manchmal nicht.", S["P"]),
    ], S))
    story.append(Spacer(1, 10))

    story.append(_card("So liest du diesen Report", [
        Paragraph("<b>Es geht nicht darum, überall HOCH zu erreichen.</b> Jede Ausprägung hat eine Funktion. Niedrig ist nicht schlecht. Hoch ist nicht automatisch gut.", S["P"]),
        Spacer(1, 3),
        Paragraph("Dein Bereich ist in jeder Kategorie markiert (grüner Rahmen). Die anderen Bereiche dienen als Kontext.", S["P"]),
        Spacer(1, 3),
        Paragraph("Wenn du denkst: <b>Verdammt - das bin genau ich</b> - dann funktioniert dieser Report. Wenn du Widerstand spürst - dann triffst du auf deine Reibung. Beides ist wertvoll. Beides ist steuerbar.", S["P"]),
    ], S))
    story.append(Spacer(1, 10))

    story.append(_green_accent_card([
        Paragraph("<b>Tipp: Auf der letzten Seite findest du deine Kompaktauswertung</b> - dein gesamtes Profil auf einer Seite. Zum Ausdrucken, an den Schreibtisch hängen und täglich nutzen.", S["Ps"]),
    ], S))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Leistung ist kein Zufall. Sie entsteht dort, wo Klarheit, Steuerung und Verantwortung zusammenkommen.", S["Quote"]))
    return story

# ============================================================
# PAGE: COMPACT OVERVIEW (One-Pager, Seite 2)
# ============================================================
def _page_compact_overview(name, email, ptype, ranked, top3, bottom2, S):
    story = []
    story.append(Paragraph("KOMPAKTAUSWERTUNG", S["Label"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Dein Profil auf einen Blick", S["H0"]))
    story.append(Spacer(1, 2))
    who = f"{name}  |  {email}" if email else name
    story.append(Paragraph(_esc(who), S["MutedS"]))
    story.append(Spacer(1, 8))

    # Typ-Box
    t = TYPE_MAP.get(ptype) or {"name": f"Typ {ptype}", "label": "-", "hint": "-"}
    typ_content = Table([
        [Paragraph(f"<b>Dein Arbeitsmodus:</b>", S["Ps"]),
         Paragraph(f"<b>{_esc(t['name'])}</b> ({_esc(t.get('label',''))})", S["Ps"])],
    ], colWidths=[45*mm, None])
    typ_content.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    story.append(_green_accent_card([
        typ_content,
        Spacer(1, 1),
        Paragraph(_esc(t.get('hint','')), S["MutedS"]),
    ], S))
    story.append(Spacer(1, 6))

    # Top 3 + Reibungszonen nebeneinander
    top_rows = []
    for fid, pct in top3:
        top_rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), S["Ps"]),
            Paragraph(f"<b>{int(pct)}%</b>", S["Ps"]),
        ])
    top_tbl = Table(top_rows, colWidths=[None, 14*mm])
    top_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1), 0.4, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))

    bot_rows = []
    for fid, pct in bottom2:
        bot_rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), S["Ps"]),
            Paragraph(f"<b>{int(pct)}%</b>", S["Ps"]),
        ])
    bot_tbl = Table(bot_rows, colWidths=[None, 14*mm])
    bot_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1), 0.4, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))

    left_card = _card("Deine Top-Hebel", [top_tbl], S)
    right_card = _card("Deine Reibungszonen", [bot_tbl], S)

    grid = Table([[left_card, Spacer(4*mm, 1), right_card]], colWidths=[None, 4*mm, None])
    grid.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),0),
    ]))
    story.append(grid)
    story.append(Spacer(1, 6))

    # Mini Bar Chart
    story.append(Paragraph("<b>Alle 11 Funktionen</b>", S["Ps"]))
    story.append(Spacer(1, 3))
    bar_rows = []
    for fid, pct in ranked:
        bar_rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), S["MutedS"]),
            RoundedProgressBar(int(pct), width_mm=75, height_mm=3.5),
            Paragraph(f"{int(pct)}%", S["MutedS"]),
        ])
    bar_tbl = Table(bar_rows, colWidths=[52*mm, None, 12*mm])
    bar_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(2,0),(2,-1),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),2),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
    ]))
    story.append(bar_tbl)
    story.append(Spacer(1, 6))

    # Wichtigste Steuerungshinweise
    story.append(Paragraph("<b>Deine wichtigsten Steuerungsschritte</b>", S["Ps"]))
    story.append(Spacer(1, 3))
    steer_items = []
    for fid, pct in top3[:2]:
        card = MEANING_CARDS.get(fid, {})
        steer = card.get("steer", "")
        if steer:
            fname = FUNCTION_NAMES.get(fid, fid)
            steer_items.append(
                Paragraph(f"<b>{_esc(fname)}:</b> {_esc(steer)}", S["Ps"])
            )
            steer_items.append(Spacer(1, 3))
    for fid, pct in bottom2[:1]:
        card = MEANING_CARDS.get(fid, {})
        steer = card.get("steer", "")
        if steer:
            fname = FUNCTION_NAMES.get(fid, fid)
            steer_items.append(
                Paragraph(f"<b>{_esc(fname)}:</b> {_esc(steer)}", S["Ps"])
            )
    if steer_items:
        story.append(_card("Sofort umsetzbar", steer_items, S))

    return story

# ============================================================
# PAGE: RESULT SNAPSHOT (Seite 3)
# ============================================================
def _page_result_snapshot(name, email, ptype, top3, bottom2, S):
    story = []
    story.append(Paragraph("ERGEBNIS", S["Label"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Dein Ergebnis ist da.", S["H0"]))
    story.append(Paragraph("Du siehst nicht wer du bist, sondern <b>wie du unter Druck funktionierst</b> - und wie du das steuerst.", S["Muted"]))
    story.append(Spacer(1, 12))

    t = TYPE_MAP.get(ptype) or {"name": f"Typ {ptype}", "label": "-", "hint": "-", "explain": "-"}

    # Typ Card
    type_inner = []
    type_inner.append(Paragraph(f"<b>{_esc(t['name'])}</b>", S["H1"]))
    type_inner.append(Spacer(1, 2))
    type_inner.append(Paragraph(_esc(t.get('hint', '')), S["P"]))
    type_inner.append(Spacer(1, 6))
    type_inner.append(GreenLine())
    type_inner.append(Spacer(1, 6))
    type_inner.append(Paragraph(f"<b>{_esc(t.get('label', ''))}</b>", S["LabelGreen"]))
    type_inner.append(Spacer(1, 3))
    explain = t.get('explain', '')
    if "Führung:" in explain:
        parts = explain.split("Führung:", 1)
        type_inner.append(Paragraph(_esc(parts[0].strip()), S["P"]))
        type_inner.append(Spacer(1, 3))
        type_inner.append(Paragraph(f"<b>Führung:</b> {_esc(parts[1].strip())}", S["P"]))
    else:
        type_inner.append(Paragraph(_esc(explain), S["P"]))

    story.append(_card("Dein Performance-Modus", type_inner, S))
    story.append(Spacer(1, 10))

    # Top 3
    story.append(Paragraph("<b>Deine stärksten Hebel (Top 3)</b>", S["Label"]))
    story.append(Spacer(1, 4))
    for fid, pct in top3:
        row = Table([[
            Paragraph(f"<b>{_esc(FUNCTION_NAMES.get(fid, fid))}</b>", S["P"]),
            Paragraph(f"<b>{int(pct)}%</b>", S["P"]),
        ]], colWidths=[None, 16*mm])
        row.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("ALIGN",(1,0),(1,0),"RIGHT"),
            ("BACKGROUND",(0,0),(-1,-1), LIGHT_GREEN),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),8),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("ROUNDEDCORNERS", [4,4,4,4]),
        ]))
        story.append(row)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 6))

    # Bottom 2
    story.append(Paragraph("<b>Deine Reibungszonen (2 niedrigste)</b>", S["Label"]))
    story.append(Spacer(1, 4))
    for fid, pct in bottom2:
        row = Table([[
            Paragraph(f"<b>{_esc(FUNCTION_NAMES.get(fid, fid))}</b>", S["P"]),
            Paragraph(f"<b>{int(pct)}%</b>", S["P"]),
        ]], colWidths=[None, 16*mm])
        row.setStyle(TableStyle([
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("ALIGN",(1,0),(1,0),"RIGHT"),
            ("BACKGROUND",(0,0),(-1,-1), LIGHT_BG),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("RIGHTPADDING",(0,0),(-1,-1),8),
            ("TOPPADDING",(0,0),(-1,-1),6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(row)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Es geht nicht darum, überall HOCH zu sein. Entscheidend ist, dass du weißt, <b>wo du Leistung holst</b> und <b>wo Reibung entsteht</b> - damit du dein Profil gezielt für dich nutzt.", S["MutedS"]))
    return story

# ============================================================
# PAGE: BAR OVERVIEW (Seite 4)
# ============================================================
def _page_bar_overview(ranked, S):
    story = []
    story.append(Paragraph("PROFIL-ÜBERSICHT", S["Label"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Alle 11 Funktionen im Überblick", S["H0"]))
    story.append(Spacer(1, 12))

    rows = []
    for fid, pct in ranked:
        rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), S["Ps"]),
            RoundedProgressBar(int(pct), width_mm=90, height_mm=5),
            Paragraph(f"<b>{int(pct)}%</b>", S["Ps"]),
        ])
    tbl = Table(rows, colWidths=[55*mm, None, 14*mm])
    tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(2,0),(2,-1),"RIGHT"),
        ("LINEBELOW",(0,0),(-1,-1), 0.3, BORDER),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),6),
        ("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 14))

    story.append(_card("Einordnung", [
        Paragraph("<b>0-25 %:</b> Niedrig - bedeutet nicht schlecht. Hier lohnt sich gezielte Steuerung.", S["Ps"]),
        Spacer(1, 2),
        Paragraph("<b>25-75 %:</b> Mittel - flexibel einsetzbar. Bewusste Steuerung macht den Unterschied.", S["Ps"]),
        Spacer(1, 2),
        Paragraph("<b>75-100 %:</b> Hoch - starker Hebel. Aber: Hoch ist kein Ziel an sich. Es geht darum, dein Profil zu kennen und zu nutzen.", S["Ps"]),
    ], S))
    return story

# ============================================================
# PAGE: MEANING CARDS (Seite 5)
# ============================================================
def _page_meaning_cards(top3, bottom2, S):
    story = []
    story.append(Paragraph("AUSWERTUNG", S["Label"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Was das konkret bedeutet", S["H0"]))
    story.append(Paragraph("Dein Profil ist individuell - es gibt kein Richtig oder Falsch.", S["Muted"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Deine stärksten Hebel</b>", S["LabelGreen"]))
    story.append(Spacer(1, 6))
    for fid, pct in top3:
        story.append(_meaning_card(fid, int(pct), "top", S))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Deine Reibungszonen</b>", S["Label"]))
    story.append(Spacer(1, 6))
    for fid, pct in bottom2:
        story.append(_meaning_card(fid, int(pct), "low", S))
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 6))
    story.append(Paragraph("Das Ziel ist nicht, überall hoch zu sein. Das Ziel ist, dein Profil zu kennen und gezielt zu nutzen.", S["MutedS"]))
    return story

# ============================================================
# PAGE: CATEGORY (11x)
# ============================================================
def _page_category(fid, pct, S):
    t = CATEGORY_TEXT.get(fid)
    if not t:
        t = {"title": FUNCTION_NAMES.get(fid, fid), "worum": ["(Text fehlt)"],
             "hoch": ["(Text fehlt)"], "mittel": ["(Text fehlt)"],
             "niedrig": ["(Text fehlt)"], "praxis": ["(Text fehlt)"]*3,
             "merksatz": "(Text fehlt)"}
    band = get_band(pct)
    story = []

    header = KeepTogether([
        Paragraph("KATEGORIE", S["Label"]),
        Spacer(1, 4),
        Paragraph(_esc(t["title"]), S["H0"]),
        Spacer(1, 4),
        Paragraph(f"Dein Wert: <b>{pct} %</b>  |  Bereich: <b>{_esc(band)}</b>", S["Muted"]),
        Spacer(1, 6),
        RoundedProgressBar(pct, width_mm=160, height_mm=6),
        Spacer(1, 10),
        _card("Worum es hier wirklich geht", [_lines_to_para(t["worum"], S)], S),
        Spacer(1, 8),
    ])
    story.append(header)

    titles = {
        "hoch":    "Wenn der Wert hoch ist (75-100 %)",
        "mittel":  "Wenn der Wert im mittleren Bereich liegt (25-75 %)",
        "niedrig": "Wenn der Wert niedrig ist (0-25 %)",
    }
    for b in ["hoch", "mittel", "niedrig"]:
        is_active = (b == band)
        fill = LIGHT_GREEN if is_active else CARD_BG
        stroke_c = GREEN if is_active else BORDER
        sw = 2.0 if is_active else 0.5
        title = titles[b]
        if is_active:
            title = "DEIN BEREICH  |  " + title
        story.append(_card(title,
            [_lines_to_para(t[b], S)], S,
            fillColor=fill, strokeColor=stroke_c, strokeWidth=sw))
        story.append(Spacer(1, 6))

    # Praxisregeln
    pr = t.get("praxis", [])[:3]
    pr_rows = []
    for i, line in enumerate(pr):
        pr_rows.append([
            Paragraph(f"<b>{i+1}.</b>", S["P"]),
            Paragraph(_esc(line), S["P"]),
        ])
    pr_tbl = Table(pr_rows, colWidths=[8*mm, None])
    pr_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
    ]))
    story.append(_card("Praxisregeln - so steuerst du diesen Hebel", [pr_tbl], S))
    story.append(Spacer(1, 6))

    story.append(_green_accent_card([
        Paragraph(f"<b>Merksatz:</b> {_esc(t.get('merksatz', ''))}", S["P"]),
    ], S))
    story.append(Spacer(1, 16))
    return story

# ============================================================
# PAGE: ACTIONPLAN + OUTRO
# ============================================================
def _page_actionplan(top3, bottom2, S):
    story = []
    top_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in top3])
    low_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in bottom2])

    story.append(Paragraph("DEIN NÄCHSTER SCHRITT", S["Label"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Actionplan", S["H0"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph("<b>Leistung ist kein Zufall. Leistung ist steuerbar.</b>", S["P"]))
    story.append(Spacer(1, 10))

    story.append(_green_accent_card([
        Paragraph("<b>Dein Fokus (14 Tage)</b>", S["H2"]),
        Spacer(1, 4),
        Paragraph(f"<b>Top-Hebel nutzen:</b> {_esc(top_names)}", S["P"]),
        Paragraph("Wähle <b>eine</b> Praxisregel aus deinem stärksten Hebel - und setze sie täglich um.", S["P"]),
        Spacer(1, 4),
        Paragraph(f"<b>Reibung reduzieren:</b> {_esc(low_names)}", S["P"]),
        Paragraph("Wähle <b>eine</b> Praxisregel aus deiner Reibungszone - und mache sie zur Pflicht.", S["P"]),
    ], S))
    story.append(Spacer(1, 12))

    story.append(_card("Abschluss", [
        Paragraph("Dieses Profil ist kein Urteil. Und es ist keine Motivation. Es ist eine Landkarte.", S["P"]),
        Spacer(1, 4),
        Paragraph("Sie zeigt dir nicht, wer du bist, sondern wie du Leistung erzeugst - und warum sie unter Druck manchmal abrufbar ist und manchmal nicht.", S["P"]),
        Spacer(1, 4),
        Paragraph("Du hast jetzt gesehen, wo dein Zugriff stabil ist, wo er kippt und welche Muster darüber entscheiden, ob Leistung kommt - oder verloren geht.", S["P"]),
        Spacer(1, 4),
        Paragraph("<b>Doch Klarheit allein ändert gar nichts.</b>", S["P"]),
    ], S))
    story.append(Spacer(1, 10))

    story.append(_card("Was jetzt entscheidet", [
        Paragraph("Der Unterschied entsteht nicht im Verstehen. Er entsteht dort, wo Entscheidungen getroffen werden - auch wenn sie unbequem sind.", S["P"]),
        Spacer(1, 4),
        Paragraph("<b>Ich arbeite nicht an Motivation. Ich baue Systeme, damit Leistung unter Druck abrufbar wird.</b>", S["P"]),
        Spacer(1, 4),
        Paragraph("Nicht theoretisch. Nicht im Idealzustand. Sondern genau dort, wo Führung, Verantwortung und Entscheidung wirklich stattfinden.", S["P"]),
    ], S))
    story.append(Spacer(1, 10))

    story.append(_card("Deine Entscheidung", [
        Paragraph("Die Frage ist nicht, ob du mehr Potenzial hast. Die Frage ist, wie lange du es noch ungenutzt lassen willst.", S["P"]),
        Spacer(1, 4),
        Paragraph("Wenn du beim Lesen gespürt hast, dass hier etwas trifft, das tiefer geht als Motivation, dann ist das kein Zufall.", S["P"]),
        Spacer(1, 4),
        Paragraph("Dann bist du genau an dem Punkt, an dem echte Performance-Arbeit beginnt.", S["P"]),
        Spacer(1, 4),
        Paragraph("<b>Sag mir Bescheid, wenn du bereit bist.</b>", S["P"]),
    ], S))
    return story

# ============================================================
# CARD COMPONENTS
# ============================================================
def _card(title, content_list, S, fillColor=CARD_BG, strokeColor=BORDER, strokeWidth=0.6):
    head = Paragraph(f"<b>{_esc(title)}</b>", S["Label"])
    rows = [[head]]
    for c in content_list:
        rows.append([c])
    t = Table(rows, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), fillColor),
        ("LEFTPADDING",(0,0),(-1,-1), 10),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("TOPPADDING",(0,0),(-1,0), 8),
        ("BOTTOMPADDING",(0,0),(-1,0), 5),
        ("TOPPADDING",(0,1),(-1,-1), 4),
        ("BOTTOMPADDING",(0,-1),(-1,-1), 8),
        ("LINEBELOW",(0,0),(-1,0), 0.4, BORDER),
    ]))
    return RoundedCard(t, radius=5, stroke=strokeWidth,
                       strokeColor=strokeColor, fillColor=fillColor, padding=5)

def _green_accent_card(content_list, S):
    rows = []
    for c in content_list:
        rows.append([c])
    t = Table(rows, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), LIGHT_GREEN),
        ("LEFTPADDING",(0,0),(-1,-1), 12),
        ("RIGHTPADDING",(0,0),(-1,-1), 10),
        ("TOPPADDING",(0,0),(-1,0), 8),
        ("BOTTOMPADDING",(0,-1),(-1,-1), 8),
    ]))
    return RoundedCard(t, radius=5, stroke=1.5,
                       strokeColor=GREEN, fillColor=LIGHT_GREEN, padding=5)

def _meaning_card(fid, pct, mode, S):
    tag = "Top-Hebel" if mode == "top" else "Reibungszone"
    card = MEANING_CARDS.get(fid, {})
    title = FUNCTION_NAMES.get(fid, fid)
    desc = card.get("top", "") if mode == "top" else card.get("low", "")
    steer = card.get("steer", "")

    head = Table([[
        Paragraph(f"<b>{_esc(tag)}</b>", S["LabelGreen"] if mode == "top" else S["Label"]),
        Paragraph(f"<b>{int(pct)}%</b>", S["Label"]),
    ]], colWidths=[None, 18*mm])
    head.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(1,0),"RIGHT"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LINEBELOW",(0,0),(-1,-1),0.4,BORDER),
    ]))

    rows = [
        [head],
        [Paragraph(f"<b>{_esc(title)}</b>", S["H2"])],
        [Paragraph(_esc(desc), S["P"])],
        [Spacer(1, 2)],
        [Paragraph(f"<b>Steuerung:</b> {_esc(steer)}", S["MutedS"])],
    ]
    t = Table(rows, colWidths=[None])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), LIGHT_BG),
        ("LEFTPADDING",(0,0),(-1,-1),10),
        ("RIGHTPADDING",(0,0),(-1,-1),10),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,-1),(-1,-1),6),
    ]))
    return RoundedCard(t, radius=5, stroke=0.5, strokeColor=BORDER, fillColor=LIGHT_BG, padding=5)

# ============================================================
# HELPERS
# ============================================================
def _normalize_ranked(ranked):
    if not ranked:
        return []
    if isinstance(ranked, list):
        out = []
        for item in ranked:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try: out.append((str(item[0]), int(round(float(item[1])))))
                except: out.append((str(item[0]), 0))
        return out
    if isinstance(ranked, dict):
        return [(str(k), int(round(float(v)))) for k, v in ranked.items()]
    return []

def _esc(s):
    s = (s or "")
    s = s.replace("\xad","").replace("\u200b","").replace("\u2060","")
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _lines_to_para(lines, S):
    paras, cur = [], []
    def flush():
        nonlocal cur
        if cur:
            paras.append("<br/>".join(cur))
            cur = []
    for ln in lines:
        s = (ln or "").strip()
        if not s:
            flush()
            continue
        if s.startswith(("*", "-", "--")):
            item = s.lstrip("*--").strip()
            cur.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(item)}")
            continue
        cur.append(_esc(s))
    flush()
    return Paragraph("<br/><br/>".join(paras), S["P"])

# ============================================================
# CUSTOM FLOWABLES
# ============================================================
class GreenLine(Flowable):
    def __init__(self, width_mm=None, thickness=2):
        super().__init__()
        self.fixed_width = (width_mm * mm) if width_mm else None
        self.thickness = thickness
    def wrap(self, aw, ah):
        self.width = self.fixed_width if self.fixed_width else aw
        return self.width, self.thickness
    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(GREEN)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)
        self.canv.restoreState()

class RoundedProgressBar(Flowable):
    def __init__(self, pct, width_mm=160, height_mm=5, radius_mm=None,
                 fillColor=GREEN, backColor=colors.HexColor("#e2e8f0"),
                 strokeColor=colors.HexColor("#cbd5e1"), strokeWidth=0.4):
        super().__init__()
        self.pct = max(0, min(100, int(pct)))
        self.width = width_mm * mm
        self.height = height_mm * mm
        self.radius = (radius_mm * mm) if radius_mm else (self.height / 2)
        self.fillColor = fillColor
        self.backColor = backColor
        self.strokeColor = strokeColor
        self.strokeWidth = strokeWidth
    def wrap(self, aw, ah):
        return self.width, self.height
    def draw(self):
        c = self.canv
        c.saveState()
        r = min(self.radius, self.height / 2)
        c.setLineWidth(self.strokeWidth)
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.backColor)
        c.roundRect(0, 0, self.width, self.height, r, stroke=1, fill=1)
        fw = (self.pct / 100.0) * self.width
        if fw > 0:
            c.setStrokeColor(self.fillColor)
            c.setFillColor(self.fillColor)
            c.roundRect(0, 0, fw, self.height, min(r, fw/2), stroke=0, fill=1)
        c.restoreState()

class Badge(Flowable):
    def __init__(self, text, w=12*mm, h=12*mm, radius=3, stroke=0.9,
                 strokeColor=GREEN, fillColor=colors.HexColor("#e9f7ef")):
        super().__init__()
        self.text = text; self.w = w; self.h = h
        self.radius = radius; self.stroke = stroke
        self.strokeColor = strokeColor; self.fillColor = fillColor
    def wrap(self, aw, ah):
        return self.w, self.h
    def draw(self):
        c = self.canv
        c.saveState()
        c.setLineWidth(self.stroke)
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.fillColor)
        c.roundRect(0, 0, self.w, self.h, self.radius, stroke=1, fill=1)
        c.setFillColor(DARK_GREEN)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.w/2, (self.h/2)-6, self.text)
        c.restoreState()

class RoundedCard(Flowable):
    def __init__(self, inner, radius=5, stroke=0.6, strokeColor=BORDER,
                 fillColor=CARD_BG, padding=6):
        super().__init__()
        self.inner = inner; self.radius = radius; self.stroke = stroke
        self.strokeColor = strokeColor; self.fillColor = fillColor; self.padding = padding
    def wrap(self, aw, ah):
        iw, ih = self.inner.wrap(aw - 2*self.padding, ah)
        self.width = aw
        self.height = ih + 2*self.padding
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
