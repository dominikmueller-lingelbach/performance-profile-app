from __future__ import annotations
from io import BytesIO
from typing import Dict, Any, List, Tuple, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# ============================================================
# IMPORT AUS ZENTRALER CONTENT-DATEI
# ============================================================
from report_content import (
    FUNCTION_NAMES, FUNCTION_ORDER, TYPE_MAP,
    MEANING_CARDS, CATEGORY_TEXT, get_band
)

# ============================================================
# DESIGN SYSTEMS - BEIDE VARIANTEN
# ============================================================

class DarkTheme:
    """Premium Dark Theme - Digital/Screen Optimized"""
    BG_DARKEST = HexColor("#0a0a0a")
    BG_DARK = HexColor("#141414")
    BG_ELEVATED = HexColor("#1a1a1a")
    BORDER = HexColor("#2a2a2a")
    BORDER_ACTIVE = HexColor("#22c55e")
    
    TEXT_PRIMARY = HexColor("#fafafa")
    TEXT_SECONDARY = HexColor("#a1a1aa")
    TEXT_MUTED = HexColor("#71717a")
    
    ACCENT = HexColor("#22c55e")
    ACCENT_SOFT = HexColor("#14532d")
    ACCENT_GLOW = HexColor("#4ade80")
    
    SUCCESS = HexColor("#22c55e")
    WARNING = HexColor("#eab308")
    
    FONT_HEADING = "Helvetica-Bold"
    FONT_BODY = "Helvetica"

class LightTheme:
    """Clean Light Theme - Print Optimized"""
    BG_WHITE = HexColor("#ffffff")
    BG_OFFWHITE = HexColor("#fafafa")
    BG_LIGHT = HexColor("#f5f5f5")
    
    BORDER_LIGHT = HexColor("#e5e5e5")
    BORDER = HexColor("#d4d4d4")
    BORDER_DARK = HexColor("#a3a3a3")
    
    TEXT_PRIMARY = HexColor("#171717")
    TEXT_SECONDARY = HexColor("#525252")
    TEXT_MUTED = HexColor("#737373")
    
    ACCENT = HexColor("#16a34a")
    ACCENT_LIGHT = HexColor("#dcfce7")
    ACCENT_DARK = HexColor("#14532d")
    
    SUCCESS = HexColor("#15803d")
    WARNING = HexColor("#a16207")
    
    FONT_HEADING = "Helvetica-Bold"
    FONT_BODY = "Helvetica"

# ============================================================
# PUBLIC API
# ============================================================

def build_pdf_report(payload: Dict[str, Any], theme: str = "dark") -> bytes:
    """
    Erstellt das PDF Report
    
    Args:
        payload: Die Report-Daten
        theme: "dark" (Premium/Screen) oder "light" (Print)
    """
    # Theme wählen
    if theme.lower() == "light":
        colors = LightTheme
        canvas_class = LightCanvas
    else:
        colors = DarkTheme
        canvas_class = DarkCanvas
    
    # Daten extrahieren
    name = (payload.get("name") or "").strip() or "Athlet"
    email = (payload.get("email") or "").strip()
    ptype = (payload.get("profile_type") or "").strip() or "–"
    ranked_raw = payload.get("ranked") or []
    
    # Daten normalisieren
    ranked = _normalize_ranked(ranked_raw)
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    
    if not ranked:
        ranked = [(fid, 0) for fid in FUNCTION_ORDER]
    
    top3 = ranked[:3]
    bottom2 = list(reversed(ranked[-2:]))
    
    # PDF Setup
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Performance Profil – {name}",
        author="Dominik Müller-Lingelbach",
    )
    
    styles = _build_styles(colors)
    story: List[Any] = []
    
    # === SEITE 1: COVER ===
    story.extend(_page_cover(name, email, styles, colors))
    story.append(PageBreak())
    
    # === SEITE 2: PHILOSOPHIE ===
    story.extend(_page_philosophy(name, styles, colors))
    story.append(PageBreak())
    
    # === SEITE 3: ÜBERSICHT ===
    story.extend(_page_overview(name, email, ptype, top3, bottom2, styles, colors))
    story.append(PageBreak())
    
    # === SEITE 4: VISUALISIERUNG ===
    story.extend(_page_visualization(ranked, styles, colors))
    story.append(PageBreak())
    
    # === SEITE 5: BEDEUTUNG ===
    story.extend(_page_meaning(top3, bottom2, styles, colors))
    story.append(PageBreak())
    
    # === SEITEN 6-16: DETAILANALYSE ===
    perc_map = {fid: pct for fid, pct in ranked}
    for fid in FUNCTION_ORDER:
        pct = int(round(perc_map.get(fid, 0)))
        story.extend(_page_category_detail(fid, pct, styles, colors))
        story.append(PageBreak())
    
    # === SEITE 17-18: ACTION PLAN ===
    story.extend(_page_actionplan(top3, bottom2, styles, colors))
    story.append(PageBreak())
    
    # === SEITE 19-24: OUTRO ===
    story.extend(_page_outro(styles, colors))
    
    # Build
    doc.build(story, canvasmaker=canvas_class)
    return buf.getvalue()

# ============================================================
# STYLES BUILDER
# ============================================================

def _build_styles(theme) -> Dict[str, ParagraphStyle]:
    """Baut Styles basierend auf Theme"""
    base = getSampleStyleSheet()
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    
    return {
        "Brand": ParagraphStyle(
            "Brand", parent=base["BodyText"],
            fontName=theme.FONT_HEADING, fontSize=9, leading=11,
            textColor=theme.TEXT_PRIMARY,
        ),
        "HeroTitle": ParagraphStyle(
            "HeroTitle", parent=base["Heading1"],
            fontName=theme.FONT_HEADING, fontSize=32, leading=36,
            textColor=theme.TEXT_PRIMARY, alignment=1, spaceAfter=8,
        ),
        "HeroSubtitle": ParagraphStyle(
            "HeroSubtitle", parent=base["BodyText"],
            fontName=theme.FONT_BODY, fontSize=14, leading=18,
            textColor=theme.TEXT_SECONDARY, alignment=1, spaceAfter=20,
        ),
        "H1": ParagraphStyle(
            "H1", parent=base["Heading1"],
            fontName=theme.FONT_HEADING, fontSize=22, leading=26,
            textColor=theme.TEXT_PRIMARY, spaceAfter=8, keepWithNext=1,
        ),
        "H2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            fontName=theme.FONT_HEADING, fontSize=16, leading=20,
            textColor=theme.TEXT_PRIMARY, spaceAfter=6, keepWithNext=1,
        ),
        "H3": ParagraphStyle(
            "H3", parent=base["Heading3"],
            fontName=theme.FONT_HEADING, fontSize=12, leading=15,
            textColor=theme.TEXT_PRIMARY, spaceAfter=4, keepWithNext=1,
        ),
        "Body": ParagraphStyle(
            "Body", parent=base["BodyText"],
            fontName=theme.FONT_BODY, fontSize=10.5, leading=14,
            textColor=theme.TEXT_PRIMARY, spaceAfter=6,
        ),
        "BodyLarge": ParagraphStyle(
            "BodyLarge", parent=base["BodyText"],
            fontName=theme.FONT_BODY, fontSize=12, leading=16,
            textColor=theme.TEXT_PRIMARY, spaceAfter=8,
        ),
        "Muted": ParagraphStyle(
            "Muted", parent=base["BodyText"],
            fontName=theme.FONT_BODY, fontSize=10, leading=13,
            textColor=theme.TEXT_SECONDARY, spaceAfter=6,
        ),
        "Caption": ParagraphStyle(
            "Caption", parent=base["BodyText"],
            fontName=theme.FONT_BODY, fontSize=8, leading=10,
            textColor=theme.TEXT_MUTED,
        ),
        "Quote": ParagraphStyle(
            "Quote", parent=base["BodyText"],
            fontName="Helvetica-Oblique", fontSize=13, leading=17,
            textColor=theme.TEXT_SECONDARY, leftIndent=20, rightIndent=20,
            spaceBefore=12, spaceAfter=12,
        ),
        "Label": ParagraphStyle(
            "Label", parent=base["BodyText"],
            fontName=theme.FONT_HEADING, fontSize=9, leading=11,
            textColor=theme.TEXT_SECONDARY, spaceAfter=2,
        ),
        "StatNumber": ParagraphStyle(
            "StatNumber", parent=base["BodyText"],
            fontName=theme.FONT_HEADING, fontSize=28, leading=32,
            textColor=theme.ACCENT if is_dark else theme.ACCENT_DARK,
            spaceAfter=2,
        ),
    }

# ============================================================
# SEITEN-BUILDER
# ============================================================

def _page_cover(name: str, email: str, styles: Dict, theme) -> List[Any]:
    """Cover Seite"""
    story = []
    story.append(Spacer(1, 50 * mm))
    story.append(Paragraph("PERFORMANCE PROFIL", styles["Label"]))
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph("Deine individuelle", styles["HeroSubtitle"]))
    story.append(Paragraph("Leistungsarchitektur", styles["HeroTitle"]))
    story.append(Spacer(1, 20 * mm))
    story.append(HRFlowable(width="40%", thickness=1.5, color=theme.ACCENT, spaceBefore=0, spaceAfter=20))
    story.append(Paragraph(f"<b>{_esc(name)}</b>", styles["HeroSubtitle"]))
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("11 Faktoren · 77 Fragen · 1 System", styles["Caption"]))
    return story

def _page_philosophy(name: str, styles: Dict, theme) -> List[Any]:
    """Philosophie Seite"""
    story = []
    story.append(_section_header("Das Fundament", styles))
    story.append(Spacer(1, 12 * mm))
    
    story.append(_card(
        "Das ist kein Persönlichkeitstest.",
        ["Was du jetzt in den Händen hältst, ist eine <b>Landkarte deiner Leistungsmechanik</b>.",
         "Sie zeigt dir nicht, wer du bist – sondern <b>wie du Leistung erzeugst</b>."],
        styles, theme, accent=True
    ))
    
    story.append(Spacer(1, 8 * mm))
    
    story.append(_card(
        "Die meisten arbeiten an Motivation.",
        ["Top-Performer arbeiten an etwas anderem: <b>Zugriff</b>.",
         "",
         "• Zugriff auf Klarheit",
         "• Zugriff auf Entscheidungskraft",
         "• Zugriff auf Leistung – genau dann, wenn es zählt"],
        styles, theme
    ))
    
    story.append(Spacer(1, 8 * mm))
    story.append(_quote_box(
        '"Druck zerstört keine Leistung. Druck entlarvt schlechte Systeme."',
        "— Dominik Müller-Lingelbach",
        styles, theme
    ))
    
    return story

def _page_overview(name: str, email: str, ptype: str, top3, bottom2, styles: Dict, theme) -> List[Any]:
    """Ergebnis Übersicht"""
    story = []
    story.append(_section_header("Dein Ergebnis", styles))
    story.append(Paragraph(
        "Du siehst nicht wer du bist, sondern <b>wie du unter Druck funktionierst</b> – und wie du das steuerst.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 12 * mm))
    
    # Performance Modus
    t = TYPE_MAP.get(ptype, {}) or {"name": f"Typ {ptype}", "label": "—", "hint": "—", "explain": "—"}
    story.append(_mode_card(ptype, t, styles, theme))
    story.append(Spacer(1, 12 * mm))
    
    # Zwei Spalten
    left = _metric_card("Deine stärksten Hebel", top3, styles, theme, "top")
    right = _metric_card("Deine Reibungszonen", bottom2, styles, theme, "bottom")
    
    grid = Table([[left, Spacer(1, 1), right]], colWidths=[84*mm, 6*mm, 84*mm])
    grid.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(grid)
    
    return story

def _page_visualization(ranked, styles: Dict, theme) -> List[Any]:
    """Bar Chart Seite"""
    story = []
    story.append(_section_header("Dein Profil", styles))
    story.append(Paragraph("Alle 11 Funktionen im Überblick – als klare Ausgangslage.", styles["Muted"]))
    story.append(Spacer(1, 12 * mm))
    
    # Chart
    rows = []
    for fid, pct in ranked:
        rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), styles["Body"]),
            _progress_bar(int(pct), 90*mm, theme),
            Paragraph(f"<b>{int(pct)}%</b>", styles["Body"]),
        ])
    
    chart = Table(rows, colWidths=[55*mm, None, 15*mm])
    chart.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    
    story.append(_container([chart], styles, theme))
    story.append(Spacer(1, 8 * mm))
    
    # Legende
    legend = [
        ["0–25%", "Niedrig ausgeprägt – unter Druck weniger Zugriff. Hier lohnt gezielte Steuerung."],
        ["25–75%", "Mittel – flexibel einsetzbar, kann tragen oder kippen."],
        ["75–100%", "Hoch – starker Hebel bei bewusstem Einsatz. Hoch ist kein Ziel an sich."]
    ]
    
    legend_rows = []
    for r, d in legend:
        legend_rows.append([
            Paragraph(f"<b>{r}</b>", styles["Body"]),
            Paragraph(d, styles["Muted"])
        ])
    
    legend_table = Table(legend_rows, colWidths=[20*mm, None])
    legend_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 6)]))
    story.append(_container([legend_table], styles, theme, "Einordnung der Werte"))
    
    return story

def _page_meaning(top3, bottom2, styles: Dict, theme) -> List[Any]:
    """Meaning Cards Seite"""
    story = []
    story.append(_section_header("Was das konkret bedeutet", styles))
    story.append(Paragraph(
        "Dein Profil ist individuell – es gibt kein Richtig oder Falsch. Hier siehst du, wo du <b>Leistung gewinnst</b> und wo <b>Reibung entsteht</b>.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 12 * mm))
    
    story.append(Paragraph("Deine stärksten Hebel", styles["H2"]))
    story.append(Spacer(1, 4 * mm))
    
    for fid, pct in top3:
        story.append(_meaning_card(fid, int(pct), "top", styles, theme))
        story.append(Spacer(1, 4 * mm))
    
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Deine Reibungszonen", styles["H2"]))
    story.append(Spacer(1, 4 * mm))
    
    for fid, pct in bottom2:
        story.append(_meaning_card(fid, int(pct), "bottom", styles, theme))
        story.append(Spacer(1, 4 * mm))
    
    return story

def _page_category_detail(fid: str, pct: int, styles: Dict, theme) -> List[Any]:
    """Detailseite pro Kategorie"""
    t = CATEGORY_TEXT.get(fid, {})
    if not t:
        t = {
            "title": FUNCTION_NAMES.get(fid, fid),
            "worum": ["(Beschreibung folgt)"],
            "hoch": ["(Text fehlt)"], "mittel": ["(Text fehlt)"], "niedrig": ["(Text fehlt)"],
            "praxis": ["(Praxisregel 1)", "(Praxisregel 2)", "(Praxisregel 3)"],
            "merksatz": "(Merksatz fehlt)"
        }
    
    band = get_band(pct)
    story = []
    
    # Header
    header_data = [[Paragraph(_esc(t["title"]), styles["H1"]), Paragraph(f"<b>{pct}%</b>", styles["StatNumber"])]]
    header = Table(header_data, colWidths=[None, 30*mm])
    header.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "BOTTOM"), ("ALIGN", (1,0), (1,0), "RIGHT")]))
    story.append(header)
    
    story.append(Paragraph(f"Einordnung: <b>{_esc(band)}</b>", styles["Muted"]))
    story.append(Spacer(1, 4 * mm))
    story.append(_progress_bar(pct, 170*mm, theme))
    story.append(Spacer(1, 12 * mm))
    
    # Worum es geht
    story.append(_card("Worum es hier wirklich geht", t["worum"], styles, theme))
    story.append(Spacer(1, 8 * mm))
    
    # Bänder
    bands = [("hoch", "75–100%", "Hoch ausgeprägt"), ("mittel", "25–75%", "Mittlerer Bereich"), ("niedrig", "0–25%", "Niedrig ausgeprägt")]
    for b_key, b_range, b_label in bands:
        is_active = (b_key == band)
        content = t.get(b_key, ["(Keine Beschreibung)"])
        story.append(_band_card(b_label, b_range, content, is_active, styles, theme))
        story.append(Spacer(1, 4 * mm))
    
    story.append(Spacer(1, 8 * mm))
    
    # Praxisregeln
    praxis = [f"{i+1}. {p}" for i, p in enumerate(t.get("praxis", [])[:3])]
    story.append(_card("Praxisregeln – so steuerst du diesen Hebel", praxis, styles, theme, accent=True))
    story.append(Spacer(1, 4 * mm))
    story.append(_quote_card(t.get("merksatz", ""), styles, theme))
    
    return story

def _page_actionplan(top3, bottom2, styles: Dict, theme) -> List[Any]:
    """Action Plan"""
    story = []
    story.append(_section_header("Action Plan", styles))
    story.append(Paragraph("Leistung ist kein Zufall. Leistung ist steuerbar.", styles["H2"]))
    story.append(Spacer(1, 12 * mm))
    
    top_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in top3])
    low_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in bottom2])
    
    focus = [
        f"<b>Top-Hebel nutzen:</b> {top_names}",
        "Wähle <b>eine</b> Praxisregel aus deinem stärksten Hebel – und setze sie täglich um.",
        "",
        f"<b>Reibung reduzieren:</b> {low_names}",
        "Wähle <b>eine</b> Praxisregel aus deiner Reibungszone – und mache sie zur Pflicht."
    ]
    
    story.append(_card("Dein Fokus (14 Tage)", focus, styles, theme, accent=True))
    return story

def _page_outro(styles: Dict, theme) -> List[Any]:
    """Outro Seiten"""
    story = []
    story.append(_section_header("Das ist erst der Anfang", styles))
    story.append(Spacer(1, 12 * mm))
    
    sections = [
        ("Dieses Profil ist kein Urteil.", [
            "Und es ist keine Motivation.",
            "Es ist eine Landkarte.",
            "Sie zeigt dir nicht, wer du bist, sondern wie du Leistung erzeugst."
        ]),
        ("Was jetzt entscheidet", [
            "Der Unterschied entsteht nicht im Verstehen.",
            "Er entsteht dort, wo Entscheidungen getroffen werden – auch wenn sie unbequem sind."
        ]),
        ("Die Entscheidung", [
            "Die Frage ist nicht, ob du mehr Potenzial hast.",
            "Die Frage ist, wie lange du es noch ungenutzt lassen willst.",
            "",
            "<b>Sag mir Bescheid, wenn du bereit bist.</b>"
        ])
    ]
    
    for title, content in sections:
        story.append(_card(title, content, styles, theme))
        story.append(Spacer(1, 8 * mm))
    
    # CTA
    cta = [
        "Dominik Müller-Lingelbach",
        "Performance Leader & Landestrainer BWGV",
        "",
        "Kostenloses Erstgespräch buchen:",
        "performanceprofil.de/termin"
    ]
    story.append(_card("Nächster Schritt", cta, styles, theme, accent=True))
    
    return story

# ============================================================
# UI KOMPONENTEN
# ============================================================

def _section_header(title: str, styles: Dict) -> Paragraph:
    return Paragraph(title, styles["H1"])

def _card(title: str, content: List[str], styles: Dict, theme, accent: bool = False) -> Table:
    """Universal Card Komponente"""
    title_p = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    content_html = "<br/>".join([_esc(c) for c in content])
    content_p = Paragraph(content_html, styles["Body"])
    
    data = [[title_p], [content_p]]
    table = Table(data, colWidths=[170*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    
    if accent:
        if is_dark:
            bg = theme.ACCENT_SOFT
            border = theme.ACCENT
        else:
            bg = theme.ACCENT_LIGHT
            border = theme.ACCENT
        border_width = 1.5
    else:
        if is_dark:
            bg = theme.BG_ELEVATED
            border = theme.BORDER
        else:
            bg = theme.BG_WHITE
            border = theme.BORDER
        border_width = 0.5
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), border_width, border),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,0), 12),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("TOPPADDING", (0,1), (-1,1), 8),
        ("BOTTOMPADDING", (0,1), (-1,1), 12),
    ]))
    
    return table

def _container(content: List[Any], styles: Dict, theme, title: Optional[str] = None) -> Table:
    """Container Box"""
    rows = []
    if title:
        rows.append([Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])])
    for c in content:
        rows.append([c])
    
    table = Table(rows, colWidths=[170*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    bg = theme.BG_DARK if is_dark else theme.BG_OFFWHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    
    return table

def _mode_card(ptype: str, type_data: Dict, styles: Dict, theme) -> Table:
    """Performance Modus Card"""
    is_dark = hasattr(theme, 'BG_DARKEST')
    
    badge = _badge(ptype, theme)
    header_data = [[
        badge,
        Paragraph(f"<b>{_esc(type_data.get('name', ptype))}</b><br/><font color='{theme.TEXT_SECONDARY.hexval()}'>{_esc(type_data.get('hint', ''))}</font>", styles["BodyLarge"])
    ]]
    header = Table(header_data, colWidths=[20*mm, None])
    header.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    
    content = Paragraph(_esc(type_data.get('explain', '')), styles["Body"])
    
    data = [[header], [content]]
    table = Table(data, colWidths=[170*mm])
    
    bg = theme.BG_ELEVATED if is_dark else theme.BG_OFFWHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,0), 12),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("TOPPADDING", (0,1), (-1,1), 8),
        ("BOTTOMPADDING", (0,1), (-1,1), 12),
        ("LINEBELOW", (0,0), (-1,0), 0.5, theme.BORDER),
    ]))
    
    return table

def _metric_card(title: str, items: List[Tuple], styles: Dict, theme, mode: str) -> Table:
    """Metric List Card"""
    header = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    
    rows = []
    for fid, pct in items:
        name = FUNCTION_NAMES.get(fid, fid)
        pct_str = f"{int(pct)}%"
        color = theme.SUCCESS if mode == "top" else theme.WARNING
        
        row = Table([[
            Paragraph(_esc(name), styles["Body"]),
            Paragraph(f"<font color='{color.hexval()}'><b>{pct_str}</b></font>", styles["Body"])
        ]], colWidths=[60*mm, None])
        row.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LINEBELOW", (0,0), (-1,-1), 0.5, theme.BORDER),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        rows.append([row])
    
    all_rows = [[header]] + rows
    table = Table(all_rows, colWidths=[84*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    bg = theme.BG_ELEVATED if is_dark else theme.BG_WHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("LINEBELOW", (0,0), (-1,0), 1, theme.BORDER),
    ]))
    
    return table

def _meaning_card(fid: str, pct: int, mode: str, styles: Dict, theme) -> Table:
    """Meaning Card"""
    card_data = MEANING_CARDS.get(fid, {})
    title = FUNCTION_NAMES.get(fid, fid)
    desc = card_data.get("top" if mode == "top" else "low", "")
    steer = card_data.get("steer", "")
    
    tag = "Top-Hebel" if mode == "top" else "Reibungszone"
    color = theme.SUCCESS if mode == "top" else theme.WARNING
    
    header_data = [[
        Paragraph(f"<font color='{color.hexval()}'><b>{tag}</b></font>", styles["Label"]),
        Paragraph(f"<b>{pct}%</b>", styles["Body"])
    ]]
    header = Table(header_data, colWidths=[None, 20*mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    title_p = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    desc_p = Paragraph(_esc(desc), styles["Body"])
    steer_p = Paragraph(f"<font color='{theme.TEXT_MUTED.hexval()}'><b>Steuerung:</b> {_esc(steer)}</font>", styles["Muted"])
    
    data = [[header], [title_p], [desc_p], [steer_p]]
    table = Table(data, colWidths=[170*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    bg = theme.BG_ELEVATED if is_dark else theme.BG_OFFWHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LINEABOVE", (0,3), (-1,3), 0.5, theme.BORDER),
        ("TOPPADDING", (0,3), (-1,3), 8),
    ]))
    
    return table

def _band_card(label: str, range_val: str, content: List[str], is_active: bool, styles: Dict, theme) -> Table:
    """Band Card (hoch/mittel/niedrig)"""
    status = "DEIN BEREICH · " if is_active else ""
    header = Paragraph(f"<b>{_esc(status + label)} ({range_val})</b>", styles["Label"])
    
    content_html = "<br/>".join([_esc(c) for c in content])
    content_p = Paragraph(content_html, styles["Body"])
    
    data = [[header], [content_p]]
    table = Table(data, colWidths=[170*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    
    if is_active:
        if is_dark:
            bg = theme.ACCENT_SOFT
            border = theme.ACCENT
        else:
            bg = theme.ACCENT_LIGHT
            border = theme.ACCENT
        border_width = 1.5
    else:
        if is_dark:
            bg = theme.BG_DARK
            border = theme.BORDER
        else:
            bg = theme.BG_WHITE
            border = theme.BORDER_LIGHT
        border_width = 0.5
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), border_width, border),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("TOPPADDING", (0,1), (-1,1), 6),
        ("BOTTOMPADDING", (0,1), (-1,1), 10),
    ]))
    
    return table

def _quote_box(quote: str, author: str, styles: Dict, theme) -> Table:
    """Quote Box mit Author"""
    is_dark = hasattr(theme, 'BG_DARKEST')
    
    quote_p = Paragraph(quote, styles["Quote"])
    author_p = Paragraph(author, styles["Caption"])
    
    data = [[quote_p], [author_p]]
    table = Table(data, colWidths=[170*mm])
    
    if is_dark:
        bg = theme.BG_ELEVATED
        border = theme.BORDER
    else:
        bg = theme.BG_OFFWHITE
        border = theme.BORDER_LIGHT
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, border),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LINEBEFORE", (0,0), (0,-1), 3, theme.ACCENT),
        ("ALIGN", (0,1), (-1,1), "RIGHT"),
    ]))
    
    return table

def _quote_card(text: str, styles: Dict, theme) -> Table:
    """Simple Quote Card"""
    escaped_text = _esc(text)
    quote = Paragraph(f'<i>„{escaped_text}"</i>', styles["Quote"])
    
    data = [[quote]]
    table = Table(data, colWidths=[170*mm])
    
    is_dark = hasattr(theme, 'BG_DARKEST')
    bg = theme.BG_DARK if is_dark else theme.BG_OFFWHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LINEBEFORE", (0,0), (0,-1), 3, theme.ACCENT),
    ]))
    
    return table

# ============================================================
# CUSTOM FLOWABLES
# ============================================================

def _progress_bar(pct: int, width: float, theme) -> Flowable:
    """Progress Bar Factory"""
    is_dark = hasattr(theme, 'BG_DARKEST')
    return ProgressBar(pct, width, theme, is_dark)

class ProgressBar(Flowable):
    def __init__(self, pct: int, width: float, theme, is_dark: bool):
        super().__init__()
        self.pct = max(0, min(100, int(pct)))
        self.width = width
        self.height = 5 * mm if is_dark else 4 * mm
        self.radius = self.height / 2
        self.theme = theme
        self.is_dark = is_dark
    
    def wrap(self, availWidth, availHeight):
        return self.width, self.height
    
    def draw(self):
        c = self.canv
        c.saveState()
        
        # Track
        if self.is_dark:
            c.setFillColor(self.theme.BG_DARKEST)
            c.setStrokeColor(self.theme.BORDER)
        else:
            c.setFillColor(self.theme.BORDER_LIGHT)
            c.setStrokeColor(self.theme.BORDER)
        
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=1)
        
        # Fill
        if self.pct > 0:
            fill_width = (self.pct / 100.0) * self.width
            c.setFillColor(self.theme.ACCENT)
            c.roundRect(0, 0, fill_width, self.height, self.radius, fill=1, stroke=0)
        
        c.restoreState()

def _badge(text: str, theme) -> Flowable:
    """Badge Factory"""
    is_dark = hasattr(theme, 'BG_DARKEST')
    return Badge(text, theme, is_dark)

class Badge(Flowable):
    def __init__(self, text: str, theme, is_dark: bool):
        super().__init__()
        self.text = text[:2].upper()
        self.size = 16 * mm
        self.theme = theme
        self.is_dark = is_dark
    
    def wrap(self, availWidth, availHeight):
        return self.size, self.size
    
    def draw(self):
        c = self.canv
        c.saveState()
        
        if self.is_dark:
            c.setFillColor(self.theme.BG_ELEVATED)
            c.setStrokeColor(self.theme.ACCENT)
            text_color = self.theme.ACCENT
        else:
            c.setFillColor(self.theme.BG_WHITE)
            c.setStrokeColor(self.theme.ACCENT)
            text_color = self.theme.ACCENT_DARK if hasattr(self.theme, 'ACCENT_DARK') else self.theme.ACCENT
        
        c.setLineWidth(1.5)
        c.roundRect(0, 0, self.size, self.size, 4, fill=1, stroke=1)
        
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.size/2, self.size/2 - 5, self.text)
        
        c.restoreState()

# ============================================================
# CUSTOM CANVAS
# ============================================================

class DarkCanvas(canvas.Canvas):
    """Dark Mode Canvas"""
    def showPage(self):
        self.saveState()
        self.setFillColor(DarkTheme.BG_DARKEST)
        self.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        self._draw_header_footer(DarkTheme)
        self.restoreState()
        super().showPage()
    
    def _draw_header_footer(self, theme):
        self.saveState()
        self.setStrokeColor(theme.BORDER)
        self.setLineWidth(0.5)
        self.line(20*mm, A4[1] - 15*mm, A4[0] - 20*mm, A4[1] - 15*mm)
        
        self.setFillColor(theme.TEXT_MUTED)
        self.setFont("Helvetica", 8)
        self.drawString(20*mm, A4[1] - 12*mm, "PERFORMANCE PROFIL")
        
        page_num = self.getPageNumber()
        self.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, f"Seite {page_num}")
        
        self.line(20*mm, 15*mm, A4[0] - 20*mm, 15*mm)
        self.drawCentredString(A4[0]/2, 10*mm, "performanceprofil.de · Dominik Müller-Lingelbach")
        self.restoreState()

class LightCanvas(canvas.Canvas):
    """Light Mode Canvas"""
    def showPage(self):
        self._draw_header_footer(LightTheme)
        super().showPage()
    
    def _draw_header_footer(self, theme):
        self.saveState()
        self.setStrokeColor(theme.BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(20*mm, A4[1] - 15*mm, A4[0] - 20*mm, A4[1] - 15*mm)
        
        self.setFillColor(theme.TEXT_MUTED)
        self.setFont("Helvetica", 8)
        self.drawString(20*mm, A4[1] - 12*mm, "PERFORMANCE PROFIL")
        
        page_num = self.getPageNumber()
        self.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, f"Seite {page_num}")
        
        self.line(20*mm, 15*mm, A4[0] - 20*mm, 15*mm)
        self.drawCentredString(A4[0]/2, 10*mm, "performanceprofil.de · Dominik Müller-Lingelbach")
        self.restoreState()

# ============================================================
# UTILITIES
# ============================================================

def _normalize_ranked(ranked) -> List[Tuple[str, int]]:
    """Normalisiert Ranked-Daten"""
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
    """XML Escaping"""
    if not s:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
