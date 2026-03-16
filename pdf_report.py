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
from reportlab.lib.colors import HexColor, white, black

# ============================================================
# IMPORT AUS ZENTRALER CONTENT-DATEI
# ============================================================
from report_content import (
    FUNCTION_NAMES, FUNCTION_ORDER, TYPE_MAP,
    MEANING_CARDS, CATEGORY_TEXT, get_band
)

# ============================================================
# DESIGN SYSTEM - LIGHT MODE (PRINT OPTIMIZED)
# ============================================================

class LightDesignSystem:
    """Light Theme für Performance Profil - Druck-optimiert"""
    
    # Farbpalette - High Contrast für Druck
    BG_WHITE = HexColor("#ffffff")        # Rein Weiß
    BG_OFFWHITE = HexColor("#fafafa")     # Subtiler Hintergrund
    BG_LIGHT = HexColor("#f5f5f5")        # Card Background
    
    BORDER_LIGHT = HexColor("#e5e5e5")    # Sehr helle Borders
    BORDER = HexColor("#d4d4d4")          # Standard Border
    BORDER_DARK = HexColor("#a3a3a3")     # Betonte Borders
    
    TEXT_PRIMARY = HexColor("#171717")    # Fast Schwarz
    TEXT_SECONDARY = HexColor("#525252")  # Dunkelgrau
    TEXT_MUTED = HexColor("#737373")      # Mittelgrau
    
    ACCENT = HexColor("#16a34a")          # Grün (etwas gedämpfter für Druck)
    ACCENT_LIGHT = HexColor("#dcfce7")    # Sehr helles Grün
    ACCENT_DARK = HexColor("#14532d")     # Dunkelgrün für Text
    
    # Status-Farben (Druck-freundlich)
    SUCCESS = HexColor("#15803d")
    WARNING = HexColor("#a16207")
    DANGER = HexColor("#b91c1c")
    
    # Grayscale für Druck-Kompatibilität
    GRAY_100 = HexColor("#f5f5f5")
    GRAY_200 = HexColor("#e5e5e5")
    GRAY_300 = HexColor("#d4d4d4")
    GRAY_400 = HexColor("#a3a3a3")
    GRAY_500 = HexColor("#737373")
    GRAY_600 = HexColor("#525252")
    GRAY_900 = HexColor("#171717")
    
    # Typografie
    FONT_HEADING = "Helvetica-Bold"
    FONT_BODY = "Helvetica"
    
    # Spacing Scale (in mm)
    SPACE_XS = 2 * mm
    SPACE_S = 4 * mm
    SPACE_M = 8 * mm
    SPACE_L = 12 * mm
    SPACE_XL = 20 * mm
    
    @classmethod
    def get_styles(cls) -> Dict[str, ParagraphStyle]:
        """Generiert alle Styles für das Dokument"""
        base = getSampleStyleSheet()
        
        styles = {
            # Branding
            "Brand": ParagraphStyle(
                "Brand",
                parent=base["BodyText"],
                fontName=cls.FONT_HEADING,
                fontSize=9,
                leading=11,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=0,
            ),
            
            # Hero / Cover
            "HeroTitle": ParagraphStyle(
                "HeroTitle",
                parent=base["Heading1"],
                fontName=cls.FONT_HEADING,
                fontSize=32,
                leading=36,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=8,
                alignment=1,
            ),
            
            "HeroSubtitle": ParagraphStyle(
                "HeroSubtitle",
                parent=base["BodyText"],
                fontName=cls.FONT_BODY,
                fontSize=14,
                leading=18,
                textColor=cls.TEXT_SECONDARY,
                spaceAfter=20,
                alignment=1,
            ),
            
            # Headings
            "H1": ParagraphStyle(
                "H1",
                parent=base["Heading1"],
                fontName=cls.FONT_HEADING,
                fontSize=22,
                leading=26,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=8,
                keepWithNext=1,
            ),
            
            "H2": ParagraphStyle(
                "H2",
                parent=base["Heading2"],
                fontName=cls.FONT_HEADING,
                fontSize=16,
                leading=20,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=6,
                keepWithNext=1,
            ),
            
            "H3": ParagraphStyle(
                "H3",
                parent=base["Heading3"],
                fontName=cls.FONT_HEADING,
                fontSize=12,
                leading=15,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=4,
                keepWithNext=1,
            ),
            
            # Body Text
            "Body": ParagraphStyle(
                "Body",
                parent=base["BodyText"],
                fontName=cls.FONT_BODY,
                fontSize=10.5,
                leading=14,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=6,
            ),
            
            "BodyLarge": ParagraphStyle(
                "BodyLarge",
                parent=base["BodyText"],
                fontName=cls.FONT_BODY,
                fontSize=12,
                leading=16,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=8,
            ),
            
            "Muted": ParagraphStyle(
                "Muted",
                parent=base["BodyText"],
                fontName=cls.FONT_BODY,
                fontSize=10,
                leading=13,
                textColor=cls.TEXT_SECONDARY,
                spaceAfter=6,
            ),
            
            "Caption": ParagraphStyle(
                "Caption",
                parent=base["BodyText"],
                fontName=cls.FONT_BODY,
                fontSize=8,
                leading=10,
                textColor=cls.TEXT_MUTED,
            ),
            
            # Special
            "Quote": ParagraphStyle(
                "Quote",
                parent=base["BodyText"],
                fontName="Helvetica-Oblique",
                fontSize=13,
                leading=17,
                textColor=cls.TEXT_SECONDARY,
                leftIndent=20,
                rightIndent=20,
                spaceBefore=12,
                spaceAfter=12,
            ),
            
            "Label": ParagraphStyle(
                "Label",
                parent=base["BodyText"],
                fontName=cls.FONT_HEADING,
                fontSize=9,
                leading=11,
                textColor=cls.TEXT_SECONDARY,
                spaceAfter=2,
            ),
            
            "StatNumber": ParagraphStyle(
                "StatNumber",
                parent=base["BodyText"],
                fontName=cls.FONT_HEADING,
                fontSize=28,
                leading=32,
                textColor=cls.ACCENT_DARK,
                spaceAfter=2,
            ),
            
            "CardTitle": ParagraphStyle(
                "CardTitle",
                parent=base["BodyText"],
                fontName=cls.FONT_HEADING,
                fontSize=13,
                leading=16,
                textColor=cls.TEXT_PRIMARY,
                spaceAfter=4,
            ),
        }
        
        return styles

# ============================================================
# PUBLIC API
# ============================================================

def build_pdf_report(payload: Dict[str, Any]) -> bytes:
    """Hauptfunktion zum Erstellen des Light Mode PDF Reports"""
    
    # Daten extrahieren
    name = (payload.get("name") or "").strip() or "Athlet"
    email = (payload.get("email") or "").strip()
    ptype = (payload.get("profile_type") or "").strip() or "–"
    ranked_raw = payload.get("ranked") or []
    
    # Daten normalisieren und sortieren
    ranked = _normalize_ranked(ranked_raw)
    ranked = sorted(ranked, key=lambda x: x[1], reverse=True)
    
    if not ranked:
        ranked = [(fid, 0) for fid in FUNCTION_ORDER]
    
    top3 = ranked[:3]
    bottom2 = list(reversed(ranked[-2:]))
    
    # PDF Setup - Optimized for Print
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
        subject="Individuelle Leistungsarchitektur",
    )
    
    styles = LightDesignSystem.get_styles()
    story: List[Any] = []
    
    # === SEITE 1: COVER ===
    story.extend(_page_cover(name, email, styles))
    story.append(PageBreak())
    
    # === SEITE 2: WILLKOMMEN / PHILOSOPHIE ===
    story.extend(_page_philosophy(name, styles))
    story.append(PageBreak())
    
    # === SEITE 3: DEIN ERGEBNIS ÜBERSICHT ===
    story.extend(_page_overview(name, email, ptype, top3, bottom2, styles))
    story.append(PageBreak())
    
    # === SEITE 4: VISUALISIERUNG (BAR CHART) ===
    story.extend(_page_visualization(ranked, styles))
    story.append(PageBreak())
    
    # === SEITE 5: BEDEUTUNG (TOP 3 + BOTTOM 2) ===
    story.extend(_page_meaning(top3, bottom2, styles))
    story.append(PageBreak())
    
    # === SEITEN 6-16: DETAILANALYSE (11 Kategorien) ===
    perc_map = {fid: pct for fid, pct in ranked}
    for fid in FUNCTION_ORDER:
        pct = int(round(perc_map.get(fid, 0)))
        story.extend(_page_category_detail(fid, pct, styles))
        story.append(PageBreak())
    
    # === SEITE 17-18: ACTION PLAN ===
    story.extend(_page_actionplan(top3, bottom2, styles))
    story.append(PageBreak())
    
    # === SEITE 19-24: OUTRO / NÄCHSTE SCHRITTE ===
    story.extend(_page_outro(styles))
    
    # Build mit Light Canvas
    doc.build(story, canvasmaker=LightCanvas)
    return buf.getvalue()

# ============================================================
# SEITEN-AUFBAU (Light Mode)
# ============================================================

def _page_cover(name: str, email: str, styles: Dict) -> List[Any]:
    """Clean Cover-Seite - Print Optimized"""
    story = []
    
    story.append(Spacer(1, 50 * mm))
    
    # Logo-Bereich
    story.append(Paragraph("PERFORMANCE PROFIL", styles["Label"]))
    story.append(Spacer(1, 40 * mm))
    
    # Haupttitel
    story.append(Paragraph("Deine individuelle", styles["HeroSubtitle"]))
    story.append(Paragraph("Leistungsarchitektur", styles["HeroTitle"]))
    
    story.append(Spacer(1, 20 * mm))
    
    # Linie
    story.append(HRFlowable(
        width="40%", 
        thickness=1.5, 
        color=LightDesignSystem.ACCENT,
        spaceBefore=0, 
        spaceAfter=20
    ))
    
    # Name
    story.append(Paragraph(f"<b>{_esc(name)}</b>", styles["HeroSubtitle"]))
    
    story.append(Spacer(1, 60 * mm))
    
    # Footer-Info
    footer_text = "11 Faktoren · 77 Fragen · 1 System"
    story.append(Paragraph(footer_text, styles["Caption"]))
    
    return story

def _page_philosophy(name: str, styles: Dict) -> List[Any]:
    """Einleitung und Philosophie"""
    story = []
    
    story.append(_section_header("Das Fundament", styles))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Wichtig-Box mit Border statt Füllung
    story.append(_light_card(
        "Das ist kein Persönlichkeitstest.",
        [
            "Was du jetzt in den Händen hältst, ist eine <b>Landkarte deiner Leistungsmechanik</b>.",
            "Sie zeigt dir nicht, wer du bist – sondern <b>wie du Leistung erzeugst</b>.",
            "Und warum sie manchmal kommt – und manchmal nicht."
        ],
        styles,
        accent=True
    ))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Kern-These
    story.append(_light_card(
        "Die meisten arbeiten an Motivation.",
        [
            "Top-Performer arbeiten an etwas anderem: <b>Zugriff</b>.",
            "",
            "• Zugriff auf Klarheit",
            "• Zugriff auf Entscheidungskraft", 
            "• Zugriff auf Leistung – genau dann, wenn es zählt"
        ],
        styles
    ))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Quote mit Border
    story.append(_light_quote_box(
        '"Druck zerstört keine Leistung. Druck entlarvt schlechte Systeme."',
        "— Dominik Müller-Lingelbach",
        styles
    ))
    
    return story

def _page_overview(name: str, email: str, ptype: str, top3, bottom2, styles: Dict) -> List[Any]:
    """Webreport-Logik mit modernem Grid"""
    story = []
    
    story.append(_section_header("Dein Ergebnis", styles))
    story.append(Paragraph(
        "Du siehst nicht wer du bist, sondern <b>wie du unter Druck funktionierst</b> – und wie du das steuerst.",
        styles["Muted"]
    ))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Performance-Modus Card
    t = TYPE_MAP.get(ptype, {}) or {"name": f"Typ {ptype}", "label": "—", "hint": "—", "explain": "—"}
    
    mode_card = _light_mode_card(ptype, t, styles)
    story.append(mode_card)
    
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Zwei-Spalten-Layout für Top/Bottom
    left_col = _light_metric_list_card("Deine stärksten Hebel", top3, styles, "top")
    right_col = _light_metric_list_card("Deine Reibungszonen", bottom2, styles, "bottom")
    
    grid = Table([[left_col, Spacer(1, 1), right_col]], 
                 colWidths=[84*mm, 6*mm, 84*mm])
    grid.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    
    story.append(grid)
    
    return story

def _page_visualization(ranked, styles: Dict) -> List[Any]:
    """Bar Chart Overview - Print Optimized"""
    story = []
    
    story.append(_section_header("Dein Profil", styles))
    story.append(Paragraph("Alle 11 Funktionen im Überblick – als klare Ausgangslage.", styles["Muted"]))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Chart Container mit subtilem Hintergrund
    rows = []
    for fid, pct in ranked:
        rows.append([
            Paragraph(_esc(FUNCTION_NAMES.get(fid, fid)), styles["Body"]),
            LightProgressBar(int(pct), width=90*mm, height=5),
            Paragraph(f"<b>{int(pct)}%</b>", styles["Body"]),
        ])
    
    chart_table = Table(rows, colWidths=[55*mm, None, 15*mm])
    chart_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER_LIGHT),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    
    story.append(_light_container([chart_table], styles))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Legende
    legend_data = [
        ["0–25%", "Niedrig ausgeprägt – unter Druck weniger Zugriff. Hier lohnt gezielte Steuerung."],
        ["25–75%", "Mittel – flexibel einsetzbar, kann tragen oder kippen."],
        ["75–100%", "Hoch – starker Hebel bei bewusstem Einsatz. Hoch ist kein Ziel an sich."]
    ]
    
    legend_rows = []
    for range_val, desc in legend_data:
        legend_rows.append([
            Paragraph(f"<b>{range_val}</b>", styles["Body"]),
            Paragraph(desc, styles["Muted"])
        ])
    
    legend_table = Table(legend_rows, colWidths=[20*mm, None])
    legend_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    story.append(_light_container([legend_table], styles, title="Einordnung der Werte"))
    
    return story

def _page_meaning(top3, bottom2, styles: Dict) -> List[Any]:
    """Meaning Cards für Top 3 und Bottom 2"""
    story = []
    
    story.append(_section_header("Was das konkret bedeutet", styles))
    story.append(Paragraph(
        "Dein Profil ist individuell – es gibt kein Richtig oder Falsch. Hier siehst du, wo du <b>Leistung gewinnst</b> und wo <b>Reibung entsteht</b>.",
        styles["Muted"]
    ))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Top 3
    story.append(Paragraph("Deine stärksten Hebel", styles["H2"]))
    story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    for fid, pct in top3:
        story.append(_light_meaning_card(fid, int(pct), "top", styles))
        story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Bottom 2
    story.append(Paragraph("Deine Reibungszonen", styles["H2"]))
    story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    for fid, pct in bottom2:
        story.append(_light_meaning_card(fid, int(pct), "bottom", styles))
        story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    return story

def _page_category_detail(fid: str, pct: int, styles: Dict) -> List[Any]:
    """Detailseite für einzelne Kategorie"""
    t = CATEGORY_TEXT.get(fid, {})
    if not t:
        t = {
            "title": FUNCTION_NAMES.get(fid, fid),
            "worum": ["(Beschreibung folgt)"],
            "hoch": ["(Text fehlt)"],
            "mittel": ["(Text fehlt)"],
            "niedrig": ["(Text fehlt)"],
            "praxis": ["(Praxisregel 1)", "(Praxisregel 2)", "(Praxisregel 3)"],
            "merksatz": "(Merksatz fehlt)"
        }
    
    band = get_band(pct)
    story = []
    
    # Header mit großem Titel und Stat
    header_data = [
        [
            Paragraph(_esc(t["title"]), styles["H1"]),
            Paragraph(f"<b>{pct}%</b>", styles["StatNumber"])
        ]
    ]
    header = Table(header_data, colWidths=[None, 30*mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "BOTTOM"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
    ]))
    story.append(header)
    
    story.append(Paragraph(f"Einordnung: <b>{_esc(band)}</b>", styles["Muted"]))
    story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    # Progress Bar
    story.append(LightProgressBar(pct, width=170*mm, height=6))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    # Worum es geht
    story.append(_light_card(
        "Worum es hier wirklich geht",
        t["worum"],
        styles
    ))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Die drei Bereiche (hoch/mittel/niedrig)
    bands = [
        ("hoch", "75–100%", "Hoch ausgeprägt"),
        ("mittel", "25–75%", "Mittlerer Bereich"),
        ("niedrig", "0–25%", "Niedrig ausgeprägt")
    ]
    
    for band_key, range_val, label in bands:
        is_active = (band_key == band)
        content = t.get(band_key, ["(Keine Beschreibung)"])
        
        card = _light_band_card(label, range_val, content, is_active, styles)
        story.append(card)
        story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Praxisregeln
    praxis_items = t.get("praxis", [])[:3]
    praxis_content = [f"{i+1}. {item}" for i, item in enumerate(praxis_items)]
    
    story.append(_light_card(
        "Praxisregeln – so steuerst du diesen Hebel",
        praxis_content,
        styles,
        accent=True
    ))
    
    story.append(Spacer(1, LightDesignSystem.SPACE_S))
    
    # Merksatz
    story.append(_light_quote_card(t.get("merksatz", ""), styles))
    
    return story

def _page_actionplan(top3, bottom2, styles: Dict) -> List[Any]:
    """Action Plan Seite"""
    story = []
    
    story.append(_section_header("Action Plan", styles))
    story.append(Paragraph("Leistung ist kein Zufall. Leistung ist steuerbar.", styles["H2"]))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    top_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in top3])
    low_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in bottom2])
    
    # 14 Tage Fokus
    focus_items = [
        f"<b>Top-Hebel nutzen:</b> {top_names}",
        "Wähle <b>eine</b> Praxisregel aus deinem stärksten Hebel – und setze sie täglich um.",
        "",
        f"<b>Reibung reduzieren:</b> {low_names}",
        "Wähle <b>eine</b> Praxisregel aus deiner Reibungszone – und mache sie zur Pflicht."
    ]
    
    story.append(_light_card("Dein Fokus (14 Tage)", focus_items, styles, accent=True))
    
    return story

def _page_outro(styles: Dict) -> List[Any]:
    """Abschlussseiten mit Call-to-Action"""
    story = []
    
    story.append(_section_header("Das ist erst der Anfang", styles))
    story.append(Spacer(1, LightDesignSystem.SPACE_L))
    
    sections = [
        (
            "Dieses Profil ist kein Urteil.",
            [
                "Und es ist keine Motivation.",
                "Es ist eine Landkarte.",
                "Sie zeigt dir nicht, wer du bist, sondern wie du Leistung erzeugst – und warum sie unter Druck manchmal abrufbar ist und manchmal nicht."
            ]
        ),
        (
            "Was jetzt entscheidet",
            [
                "Der Unterschied entsteht nicht im Verstehen. Er entsteht dort, wo Entscheidungen getroffen werden – auch wenn sie unbequem sind.",
                "Unter Druck. Unter Verantwortung. Unter Erwartung."
            ]
        ),
        (
            "Die Entscheidung",
            [
                "Die Frage ist nicht, ob du mehr Potenzial hast.",
                "Die Frage ist, wie lange du es noch ungenutzt lassen willst.",
                "",
                "<b>Sag mir Bescheid, wenn du bereit bist.</b>"
            ]
        )
    ]
    
    for title, content in sections:
        story.append(_light_card(title, content, styles))
        story.append(Spacer(1, LightDesignSystem.SPACE_M))
    
    # Kontakt/CTA Box
    cta_content = [
        "Dominik Müller-Lingelbach",
        "Performance Leader & Landestrainer BWGV",
        "",
        "Kostenloses Erstgespräch buchen:",
        "performanceprofil.de/termin"
    ]
    story.append(_light_card("Nächster Schritt", cta_content, styles, accent=True))
    
    return story

# ============================================================
# LIGHT MODE KOMPONENTEN
# ============================================================

def _section_header(title: str, styles: Dict) -> Paragraph:
    """Konsistente Section Headers"""
    return Paragraph(title, styles["H1"])

def _light_card(title: str, content_lines: List[str], styles: Dict, accent: bool = False) -> Table:
    """Light Mode Card mit Border statt Füllung"""
    title_para = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    
    content_html = "<br/>".join([_esc(line) for line in content_lines])
    content_para = Paragraph(content_html, styles["Body"])
    
    data = [[title_para], [content_para]]
    table = Table(data, colWidths=[170*mm])
    
    # Light Mode: Border statt Background
    if accent:
        border_color = LightDesignSystem.ACCENT
        border_width = 1.5
        bg_color = LightDesignSystem.ACCENT_LIGHT
    else:
        border_color = LightDesignSystem.BORDER
        border_width = 0.5
        bg_color = LightDesignSystem.BG_WHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg_color),
        ("BOX", (0,0), (-1,-1), border_width, border_color),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,0), 12),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("TOPPADDING", (0,1), (-1,1), 8),
        ("BOTTOMPADDING", (0,1), (-1,1), 12),
    ]))
    
    return table

def _light_container(content: List[Any], styles: Dict, title: Optional[str] = None) -> Table:
    """Light Container mit subtilem Hintergrund"""
    rows = []
    if title:
        rows.append([Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])])
    
    for item in content:
        rows.append([item])
    
    table = Table(rows, colWidths=[170*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LightDesignSystem.BG_OFFWHITE),
        ("BOX", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER_LIGHT),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    
    return table

def _light_mode_card(ptype: str, type_data: Dict, styles: Dict) -> Table:
    """Performance Modus Card - Light"""
    badge = LightBadge(ptype)
    
    header_data = [[
        badge,
        Paragraph(
            f"<b>{_esc(type_data.get('name', ptype))}</b><br/>"
            f"<font color='#525252'>{_esc(type_data.get('hint', ''))}</font>",
            styles["BodyLarge"]
        )
    ]]
    
    header = Table(header_data, colWidths=[20*mm, None])
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    
    content = Paragraph(_esc(type_data.get('explain', '')), styles["Body"])
    
    full_data = [[header], [content]]
    table = Table(full_data, colWidths=[170*mm])
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LightDesignSystem.BG_OFFWHITE),
        ("BOX", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,0), 12),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("TOPPADDING", (0,1), (-1,1), 8),
        ("BOTTOMPADDING", (0,1), (-1,1), 12),
        ("LINEBELOW", (0,0), (-1,0), 0.5, LightDesignSystem.BORDER_LIGHT),
    ]))
    
    return table

def _light_metric_list_card(title: str, items: List[Tuple], styles: Dict, mode: str) -> Table:
    """Top/Bottom Listen Card - Light"""
    header = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    
    rows = []
    for fid, pct in items:
        name = FUNCTION_NAMES.get(fid, fid)
        pct_str = f"{int(pct)}%"
        
        color = LightDesignSystem.SUCCESS if mode == "top" else LightDesignSystem.WARNING
        
        row = Table([[
            Paragraph(_esc(name), styles["Body"]),
            Paragraph(f"<font color='{color.hexval()}'><b>{pct_str}</b></font>", styles["Body"])
        ]], colWidths=[60*mm, None])
        
        row.setStyle(TableStyle([
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LINEBELOW", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER_LIGHT),
            ("TOPPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        
        rows.append([row])
    
    all_rows = [[header]] + rows
    table = Table(all_rows, colWidths=[84*mm])
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LightDesignSystem.BG_WHITE),
        ("BOX", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,0), 10),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
        ("LINEBELOW", (0,0), (-1,0), 1, LightDesignSystem.BORDER),
    ]))
    
    return table

def _light_meaning_card(fid: str, pct: int, mode: str, styles: Dict) -> Table:
    """Meaning Card für Top/Bottom - Light"""
    card_data = MEANING_CARDS.get(fid, {})
    title = FUNCTION_NAMES.get(fid, fid)
    desc = card_data.get("top" if mode == "top" else "low", "")
    steer = card_data.get("steer", "")
    
    tag = "Top-Hebel" if mode == "top" else "Reibungszone"
    tag_color = LightDesignSystem.SUCCESS if mode == "top" else LightDesignSystem.WARNING
    
    # Header mit Tag und Prozent
    header_data = [[
        Paragraph(f"<font color='{tag_color.hexval()}'><b>{tag}</b></font>", styles["Label"]),
        Paragraph(f"<b>{pct}%</b>", styles["Body"])
    ]]
    header = Table(header_data, colWidths=[None, 20*mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("LINEBELOW", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER_LIGHT),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    
    # Content
    title_para = Paragraph(f"<b>{_esc(title)}</b>", styles["H3"])
    desc_para = Paragraph(_esc(desc), styles["Body"])
    steer_para = Paragraph(f"<font color='{LightDesignSystem.TEXT_MUTED.hexval()}'><b>Steuerung:</b> {_esc(steer)}</font>", styles["Muted"])
    
    data = [[header], [title_para], [desc_para], [steer_para]]
    table = Table(data, colWidths=[170*mm])
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LightDesignSystem.BG_OFFWHITE),
        ("BOX", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LINEABOVE", (0,3), (-1,3), 0.5, LightDesignSystem.BORDER_LIGHT),
        ("TOPPADDING", (0,3), (-1,3), 8),
    ]))
    
    return table

def _light_band_card(label: str, range_val: str, content: List[str], is_active: bool, styles: Dict) -> Table:
    """Band Card (hoch/mittel/niedrig) - Light"""
    status = "DEIN BEREICH · " if is_active else ""
    header_text = f"{status}{label} ({range_val})"
    
    header = Paragraph(f"<b>{_esc(header_text)}</b>", styles["Label"])
    
    content_html = "<br/>".join([_esc(line) for line in content])
    content_para = Paragraph(content_html, styles["Body"])
    
    data = [[header], [content_para]]
    table = Table(data, colWidths=[170*mm])
    
    # Light Mode Styling
    if is_active:
        bg = LightDesignSystem.ACCENT_LIGHT
        border = LightDesignSystem.ACCENT
        border_width = 1.5
    else:
        bg = LightDesignSystem.BG_WHITE
        border = LightDesignSystem.BORDER_LIGHT
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

def _quote_card(text: str, styles: Dict, theme, is_dark: bool) -> Table:
    """Simple Quote Card"""
    escaped_text = _esc(text)
    # KORRIGIERT: Einfache Quotes außen, normale Anführungszeichen innen
    quote = Paragraph(f'<i>"{escaped_text}"</i>', styles["Quote"])
    
    data = [[quote]]
    table = Table(data, colWidths=[170*mm])
    
    bg = theme.BG_DARK if is_dark else theme.BG_OFFWHITE
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, theme.BORDER if is_dark else theme.BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LINEBEFORE", (0,0), (0,-1), 3, theme.ACCENT),
    ]))
    
    return table

def _light_quote_box(quote: str, author: str, styles: Dict) -> Table:
    """Zitat Box mit Author"""
    quote_para = Paragraph(quote, styles["Quote"])
    author_para = Paragraph(author, styles["Caption"])
    
    data = [[quote_para], [author_para]]
    table = Table(data, colWidths=[170*mm])
    
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LightDesignSystem.BG_OFFWHITE),
        ("BOX", (0,0), (-1,-1), 0.5, LightDesignSystem.BORDER_LIGHT),
        ("LEFTPADDING", (0,0), (-1,-1), 16),
        ("RIGHTPADDING", (0,0), (-1,-1), 16),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LINEBEFORE", (0,0), (0,-1), 3, LightDesignSystem.ACCENT),
        ("ALIGN", (0,1), (-1,1), "RIGHT"),
    ]))
    
    return table

# ============================================================
# LIGHT MODE FLOWABLES
# ============================================================

class LightProgressBar(Flowable):
    """Clean Progress Bar für Light Mode"""
    
    def __init__(self, pct: int, width: float, height: float = 5):
        super().__init__()
        self.pct = max(0, min(100, int(pct)))
        self.width = width
        self.height = height * mm
        self.radius = self.height / 2
        
    def wrap(self, availWidth, availHeight):
        return self.width, self.height
    
    def draw(self):
        c = self.canv
        c.saveState()
        
        # Hintergrund (Track) - Hellgrau
        c.setFillColor(LightDesignSystem.GRAY_200)
        c.setStrokeColor(LightDesignSystem.GRAY_300)
        c.setLineWidth(0.5)
        c.roundRect(0, 0, self.width, self.height, self.radius, fill=1, stroke=1)
        
        # Fill - Solides Grün
        if self.pct > 0:
            fill_width = (self.pct / 100.0) * self.width
            c.setFillColor(LightDesignSystem.ACCENT)
            c.roundRect(0, 0, fill_width, self.height, self.radius, fill=1, stroke=0)
        
        c.restoreState()

class LightBadge(Flowable):
    """Clean Badge für Light Mode"""
    
    def __init__(self, text: str, size: float = 16 * mm):
        super().__init__()
        self.text = text[:2].upper()
        self.size = size
        
    def wrap(self, availWidth, availHeight):
        return self.size, self.size
    
    def draw(self):
        c = self.canv
        c.saveState()
        
        # Weißer Hintergrund mit Border
        c.setFillColor(LightDesignSystem.BG_WHITE)
        c.setStrokeColor(LightDesignSystem.ACCENT)
        c.setLineWidth(1.5)
        
        c.roundRect(0, 0, self.size, self.size, 4, fill=1, stroke=1)
        
        # Text in Dunkelgrün
        c.setFillColor(LightDesignSystem.ACCENT_DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.size/2, self.size/2 - 5, self.text)
        
        c.restoreState()

class LightCanvas(canvas.Canvas):
    """Light Mode Canvas - Clean für Druck"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        
    def showPage(self):
        # KEIN Hintergrund zeichnen (Weiß ist Standard)
        
        # Header/Footer
        self._draw_header_footer()
        
        super().showPage()
    
    def _draw_header_footer(self):
        self.saveState()
        
        # Header Linie - Subtil
        self.setStrokeColor(LightDesignSystem.BORDER_LIGHT)
        self.setLineWidth(0.5)
        self.line(20*mm, A4[1] - 15*mm, A4[0] - 20*mm, A4[1] - 15*mm)
        
        # Brand
        self.setFillColor(LightDesignSystem.TEXT_MUTED)
        self.setFont("Helvetica", 8)
        self.drawString(20*mm, A4[1] - 12*mm, "PERFORMANCE PROFIL")
        
        # Seitenzahl
        page_num = self.getPageNumber()
        self.drawRightString(A4[0] - 20*mm, A4[1] - 12*mm, f"Seite {page_num}")
        
        # Footer Linie
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
