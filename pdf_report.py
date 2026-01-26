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
# DATA / TEXTS
# ============================================================

FUNCTION_ORDER = ["DST", "STR", "MAC", "KON", "MOR", "IND", "AKT", "INF", "COM", "AUF", "STA"]

FUNCTION_NAMES = {
    "DST": "Leistungsmodus unter Belastung",
    "STR": "Entscheidungsstabilität & Ordnung",
    "MAC": "Verantwortungs- & Einflussorientierung",
    "KON": "Soziale Steuerung & Anschlussfähigkeit",
    "MOR": "Werte-Stabilität & innere Entscheidungsgrenzen",
    "IND": "Autonomie- & Gestaltungsmodus",
    "AKT": "Energie- & Handlungsdynamik",
    "INF": "Verarbeitungs- & Entscheidungsmodus",
    "COM": "Vergleichs- & Leistungsreferenz",
    "AUF": "Sichtbarkeits- & Feedbackabhängigkeit",
    "STA": "Positions- & Anerkennungsorientierung",
}

TYPE_MAP = {
    "A": {"title": "Stabilitätsmodus", "label": "Fundament-Performer",
          "hint": "Du lieferst, wenn Rahmen & Standards klar sind.",
          "explain": "Ruhig, zuverlässig, präzise. Führung: klare Rahmen, keine künstliche Hektik."},
    "B": {"title": "Druckmodus", "label": "Peak-Performer",
          "hint": "Je höher der Druck, desto besser – wenn du ihn steuerst.",
          "explain": "Hochfokussiert in kritischen Momenten. Führung: Druck dosieren + klare Regeln + Regeneration."},
    "C": {"title": "Gestaltungsmodus", "label": "Lösungs- & Konzeptmodus",
          "hint": "Freiheit erzeugt Leistung. Ziele ja – Detailsteuerung nein.",
          "explain": "Kreativ, konzeptionell, lösungsorientiert. Führung: Ziel klar, Weg offen. Ergebnis zählt, nicht die Methode."},
    "D": {"title": "Vergleichsmodus", "label": "Ambitions-Performer",
          "hint": "Leistung entsteht im Wettbewerb, Standards und Feedback.",
          "explain": "Leistungsgetrieben, benchmark-orientiert, ambitioniert. Führung: Maßstäbe sauber setzen, Feedback sachlich, Vergleich kontrollieren."},
    "E": {"title": "Kontrollmodus", "label": "Steuerungs-Performer",
          "hint": "Du performst maximal, wenn Verantwortung klar bei dir liegt.",
          "explain": "Übernimmt Verantwortung, denkt steuernd, behält Überblick. Führung: Verantwortung abgrenzen, Delegation trainieren."},
}

def _band(pct: int) -> str:
    if pct < 25:
        return "niedrig"
    if pct < 75:
        return "mittel"
    return "hoch"

def _low_variant(pct: int) -> str:
    """
    LOW_A = wirklich niedrig (0–25 %)
    LOW_B = mittel (25–75 %), aber niedrigste Zone
    """
    return "A" if pct <= 25 else "B"

def _band_label(pct: int) -> str:
    b = _band(pct)
    if b == "hoch":
        return "hoch (75–100 %)"
    if b == "mittel":
        return "mittel (25–75 %)"
    return "niedrig (0–25 %)"


# ============================================================
# CATEGORY TEXTS
# DST ist exakt dein MASTER. Alle anderen im gleichen Stil.
# ============================================================

CATEGORY_TEXT: Dict[str, Dict[str, Any]] = {
    "DST": {
        "title": "LEISTUNGSMODUS UNTER BELASTUNG",
        "worum": [
            "Diese Funktion entscheidet nicht, wie leistungsfähig du sein könntest –",
            "sondern ob du Leistung abrufst, wenn es wirklich zählt.",
            "",
            "Zeitdruck.",
            "Erwartung.",
            "Bewertung.",
            "Risiko.",
            "",
            "Genau dort trennt sich Vorbereitung von Performance.",
            "",
            "Der Leistungsmodus unter Belastung beschreibt, wie dein System reagiert,",
            "wenn die äußeren Bedingungen enger werden –",
            "und ob du dann klarer wirst oder enger.",
            "",
            "Nicht im Training.",
            "Nicht im Kopf.",
            "Sondern im Moment der Entscheidung.",
        ],
        "hoch": [
            "Druck aktiviert dich.",
            "Er macht dich klarer, nicht hektischer.",
            "Du bleibst handlungsfähig, während andere anfangen zu zweifeln.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du priorisierst schneller",
            "• Du triffst Entscheidungen auch ohne vollständige Sicherheit",
            "• Du hältst Fokus, während andere Tempo verlieren",
            "• Du kannst Leistung nicht nur vorbereiten, sondern abrufen",
            "",
            "Das ist ein echter Peak-Hebel.",
            "Denn genau hier entstehen Führung, Dominanz und Verlässlichkeit.",
            "",
            "Wichtig:",
            "Diese Stärke wirkt nicht automatisch –",
            "sie wirkt dann maximal, wenn du Druck bewusst dosierst",
            "und nicht permanent im Hochlastmodus bleibst.",
        ],
        "mittel": [
            "Leistung ist unter Druck möglich, aber nicht stabil.",
            "Manche Situationen pushen – andere überfahren.",
            "",
            "Typisch:",
            "• Zu viel gleichzeitig",
            "• Tempoverlust bei Unklarheit",
            "• Wechsel zwischen Aktionismus und Blockade",
            "",
            "Der Schlüssel hier ist nicht mehr Disziplin,",
            "sondern bessere Drucksteuerung.",
        ],
        "niedrig": [
            "Steigender Druck senkt den Zugriff.",
            "Entscheidungen werden schwerer, nicht klarer.",
            "Leistung wird inkonsistent – genau dann, wenn sie gebraucht wird.",
            "",
            "Nicht, weil Kompetenz fehlt.",
            "Sondern weil das System Schutz sucht, statt Output zu liefern.",
        ],
        "praxis": [
            "Vor Belastung: Maximal 1–3 klare Prioritäten festlegen – nie mehr. Druck braucht Richtung, keine To-do-Wolke.",
            "Nach Belastung: Kurzer Reset als Standard (Bewegung, Atmung, Wasser – kein Scrollen, kein Grübeln).",
            "Im Druck: Fokus auf die nächste saubere Aktion, nicht auf das „große Ganze“."
        ],
        "merksatz": "Leistung unter Druck ist kein Talent. Sie ist das Ergebnis von klarer Priorisierung, bewusster Steuerung und der Fähigkeit, im Moment zu entscheiden.",
    },

    "STR": {
        "title": "ENTSCHEIDUNGSSTABILITÄT & ORDNUNG",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du intelligent bist –",
            "sondern ob du in Unruhe sauber entscheiden kannst.",
            "",
            "Unklarheit.",
            "zu viele Baustellen.",
            "wechselnde Prioritäten.",
            "",
            "Hier verlieren viele nicht wegen fehlender Kompetenz –",
            "sondern weil ihnen ein System fehlt.",
            "",
            "Entscheidungsstabilität & Ordnung beschreibt,",
            "ob Struktur dich stabilisiert –",
            "oder ob Chaos dir unbemerkt Leistung abzieht.",
        ],
        "hoch": [
            "Struktur beruhigt dich nicht nur – sie macht dich gefährlich effizient.",
            "Du bleibst klar, weil du Ordnung in Entscheidungen bringst.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du priorisierst sauber statt hektisch",
            "• Du triffst Entscheidungen nach Standards – nicht nach Stimmung",
            "• Du arbeitest stabil, auch wenn außen Lärm ist",
            "• Du verlierst wenig Energie an Chaos",
            "",
            "Das ist ein Elite-Hebel.",
            "Denn Struktur ist nicht „Organisation“ –",
            "Struktur ist Zugriff.",
        ],
        "mittel": [
            "Du kannst strukturiert sein – aber nicht konstant.",
            "Manchmal läuft es über Standards.",
            "Manchmal frisst dich Unordnung.",
            "",
            "Typisch:",
            "• Du startest stark – verlierst aber Richtung",
            "• Du wechselst zu oft die Priorität",
            "• Du bist im Kopf organisiert – aber nicht im System",
            "",
            "Der Schlüssel ist nicht mehr Druck,",
            "sondern ein klarer Standard, der täglich greift.",
        ],
        "niedrig": [
            "Chaos kostet dich unnötig Leistung.",
            "Nicht dramatisch – aber konstant.",
            "",
            "Typisch:",
            "• Entscheidungen dauern zu lange",
            "• Umsetzung beginnt zu spät",
            "• Energie geht in Sortieren statt in Liefern",
            "",
            "Nicht, weil du schwach bist.",
            "Sondern weil du ohne Ordnung zu viel im Kopf tragen musst.",
        ],
        "praxis": [
            "Täglich: 3 Prioritäten. Nicht mehr. Wenn alles wichtig ist, ist nichts klar.",
            "Standards schriftlich: Wer entscheidet was – bis wann? Unklarheit ist Leistungsverlust.",
            "Start- und Abschlussritual: Beginnen mit Fokus, beenden mit Review. Ordnung entsteht nicht zufällig."
        ],
        "merksatz": "Struktur ist kein Selbstzweck. Sie ist das, was Leistung unter Unruhe stabil macht.",
    },

    "MAC": {
        "title": "VERANTWORTUNGS- & EINFLUSSORIENTIERUNG",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du motiviert bist –",
            "sondern ob du Verantwortung nimmst, wenn Richtung fehlt.",
            "",
            "Verantwortung heißt:",
            "nicht warten, bis jemand entscheidet.",
            "sondern die Entscheidung führen.",
            "",
            "Diese Kategorie zeigt,",
            "ob Einfluss dich aktiviert –",
            "oder ob du lieber im Ausführen bleibst.",
        ],
        "hoch": [
            "Verantwortung setzt Energie frei.",
            "Du willst steuern, gestalten, entscheiden.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du übernimmst Verantwortung statt Ausreden",
            "• Du triffst Entscheidungen, wenn andere noch diskutieren",
            "• Du willst Wirkung – nicht nur Arbeit",
            "• Du hältst Systeme stabil, weil du Verantwortung trägst",
            "",
            "Das ist Leadership in Reinform.",
            "Nicht Position – sondern Verhalten.",
        ],
        "mittel": [
            "Du kannst Verantwortung übernehmen – aber nicht immer automatisch.",
            "Manchmal gehst du voran.",
            "Manchmal wartest du auf Autorität.",
            "",
            "Typisch:",
            "• Du übernimmst, wenn du dich sicher fühlst",
            "• Du zögerst, wenn der Verantwortungsrahmen unklar ist",
            "• Du lässt Entscheidungen liegen, wenn niemand sie dir gibt",
            "",
            "Der Schlüssel ist klare Verantwortungsdefinition –",
            "damit du nicht in Unklarheit hängen bleibst.",
        ],
        "niedrig": [
            "Verantwortung ist nicht dein Trigger.",
            "Du wartest eher auf Vorgaben oder klare Führung.",
            "",
            "Typisch:",
            "• Du lieferst gut – aber du steuerst wenig",
            "• Entscheidungen bleiben in der Luft",
            "• Einfluss wird verschenkt",
            "",
            "Nicht, weil dir Stärke fehlt.",
            "Sondern weil Verantwortung nicht sauber bei dir landet.",
        ],
        "praxis": [
            "Verantwortungsrahmen definieren: Was ist mein Bereich – und was nicht? Ohne konkreten Rahmen keine klare Verantwortung.",
            "Entscheidungsspielraum festlegen: „Ich entscheide bis X / bis Datum Y“ – sonst wird’s schwammig.",
            "Verantwortung täglich: Eine Sache aktiv abschließen, statt sie „zu parken“."
        ],
        "merksatz": "Einfluss ist kein Status. Einfluss ist die Fähigkeit, Verantwortung zu führen, bevor es jemand verlangt.",
    },

    "KON": {
        "title": "SOZIALE STEUERUNG & ANSCHLUSSFÄHIGKEIT",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du „menschenfreundlich“ bist –",
            "sondern ob Kontakt deine Leistung verstärkt oder verwässert.",
            "",
            "Feedback.",
            "Sparring.",
            "Teamdynamik.",
            "",
            "Hier entsteht entweder Klarheit –",
            "oder Ablenkung.",
            "",
            "Diese Kategorie zeigt,",
            "ob du über Austausch stabiler wirst –",
            "oder ob du in Autonomie am stärksten bist.",
        ],
        "hoch": [
            "Kontakt ist bei dir kein Smalltalk.",
            "Kontakt ist Performance.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Gespräche machen dich klarer",
            "• Feedback stabilisiert deinen Fokus",
            "• Du wirst besser durch Sparring",
            "• Du ziehst Energie aus einem leistungsstarken Umfeld",
            "",
            "Das ist ein starker Hebel –",
            "wenn du ihn bewusst nutzt und nicht jedem Input die Führung gibst.",
        ],
        "mittel": [
            "Du kannst über Austausch wachsen – aber nicht immer.",
            "Manchmal macht Kontakt dich stärker.",
            "Manchmal kostet er dich Fokus.",
            "",
            "Typisch:",
            "• Du holst Feedback, aber zu unstrukturiert",
            "• Du bist offen, aber manchmal zu beeinflusst",
            "• Du wechselst zwischen Rückzug und Over-Contact",
            "",
            "Der Schlüssel ist Kommunikationsdichte bewusst zu steuern –",
            "nicht nach Gefühl.",
        ],
        "niedrig": [
            "Du bist sehr autonom.",
            "Du brauchst wenig Kontakt, um zu liefern.",
            "",
            "Das kann Stärke sein –",
            "Risiko ist Isolation.",
            "",
            "Typisch:",
            "• Du holst zu wenig Korrektur",
            "• Du bleibst unsichtbar, obwohl du Leistung bringst",
            "• Du trägst zu viel allein im Kopf",
        ],
        "praxis": [
            "Sparring fix: 1 Termin pro Woche, klarer Zweck, klare Fragen – Feedback wird geführt, nicht gesucht.",
            "Input filtern: Nicht jeder Rat ist relevant. Nur Feedback von Menschen mit Standard.",
            "Kontakt dosieren: Austausch als Hebel – nicht als Flucht vor Entscheidung."
        ],
        "merksatz": "Kontakt ist dann ein Hebel, wenn er Klarheit erzeugt – nicht wenn er deine Entscheidung ersetzt.",
    },

    "MOR": {
        "title": "WERTE-STABILITÄT & INNERE ENTSCHEIDUNGSGRENZEN",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du „moralisch“ bist –",
            "sondern ob du unter Druck eine klare innere Linie hast.",
            "",
            "Werte sind keine Worte.",
            "Werte sind Grenzen.",
            "",
            "Diese Kategorie zeigt,",
            "ob du mit Integrität ruhiger wirst –",
            "oder ob innere Konflikte dir Leistung ziehen.",
        ],
        "hoch": [
            "Du entscheidest klarer, wenn Dinge zu deinen Prinzipien passen.",
            "Du verlierst weniger Energie an innere Diskussion.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du hast eine klare Linie",
            "• Du kannst „Nein“ sagen ohne Drama",
            "• Du bleibst stabil, weil du weißt wofür du stehst",
            "• Integrität macht dich leistungsfähig",
            "",
            "Das ist ein Elite-Vorteil –",
            "weil du unter Druck weniger inneren Lärm hast.",
        ],
        "mittel": [
            "Du hast Werte – aber sie sind nicht immer scharf geführt.",
            "Manchmal bist du klar.",
            "Manchmal bist du zu flexibel.",
            "",
            "Typisch:",
            "• Du passt dich an, auch wenn es dich innerlich kostet",
            "• Du rechtfertigst Entscheidungen zu lange",
            "• Du spürst Unruhe, aber benennst sie nicht",
            "",
            "Der Schlüssel ist Klarheit: Was ist No-Go – und warum?",
        ],
        "niedrig": [
            "Flexibilität ist hoch – aber Grenzen sind weich.",
            "Das kann Anpassungsfähigkeit sein –",
            "Risiko ist Beliebigkeit.",
            "",
            "Typisch:",
            "• Innere Unruhe bei Entscheidungen",
            "• Du verlierst Energie an Grübeln",
            "• Du driftest, wenn Druck kommt",
        ],
        "praxis": [
            "3 Kernwerte + 3 No-Gos schriftlich. Kurz. Hart. Ohne Poesie.",
            "Konflikte früh benennen: Was passt nicht? Was kostet Leistung?",
            "Entscheidungen sauber machen: weniger Rechtfertigung, mehr Linie."
        ],
        "merksatz": "Werte sind nicht Deko. Werte sind das, was dich unter Druck stabil hält, wenn alles wackelt.",
    },

    "IND": {
        "title": "AUTONOMIE- & GESTALTUNGSMODUS",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du „freiheitsliebend“ bist –",
            "sondern ob Freiheit bei dir Leistung freisetzt oder Fokus frisst.",
            "",
            "Manche liefern mit Struktur.",
            "Andere liefern mit Spielraum.",
            "",
            "Diese Kategorie zeigt,",
            "ob du über Gestaltungsfreiheit besser wirst –",
            "oder ob du über klare Führung stabiler bist.",
        ],
        "hoch": [
            "Freiheit macht dich nicht chaotisch –",
            "Freiheit macht dich produktiv.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du entwickelst Lösungen statt nur Schritte abzuarbeiten",
            "• Du lieferst besser ohne Micromanagement",
            "• Du denkst in Möglichkeiten und Output",
            "• Du bringst eigene Wege, ohne den Zielrahmen zu verlieren",
            "",
            "Das ist ein starker Hebel –",
            "wenn Ziel und Ergebnis glasklar sind.",
        ],
        "mittel": [
            "Du kannst mit Freiheit umgehen – aber nicht unbegrenzt.",
            "Zu wenig Spielraum bremst dich.",
            "Zu viel Spielraum zerstreut dich.",
            "",
            "Typisch:",
            "• Du brauchst Leitplanken, aber keine Detailsteuerung",
            "• Du performst, wenn Ziele klar sind",
            "• Du verlierst Fokus, wenn niemand ein Ergebnis definiert",
        ],
        "niedrig": [
            "Du bist systemtreuer.",
            "Du wirst besser, wenn Vorgaben klar sind.",
            "",
            "Risiko:",
            "Wenn niemand führt, wirst du passiver.",
            "Nicht aus Faulheit –",
            "sondern weil dir der Rahmen fehlt, der Zugriff gibt.",
        ],
        "praxis": [
            "Freiheitsgrad definieren: Ziel fix, Weg offen – oder Weg fix, Ziel messbar. Nicht beides offen.",
            "Ergebnis-Kriterien schriftlich: Was ist „fertig“? Was ist „gut“?",
            "Timeboxing: Freiheit braucht Zeitfenster, sonst frisst sie Fokus."
        ],
        "merksatz": "Autonomie ist dann ein Hebel, wenn sie geführt ist: Ziel klar, Spielraum bewusst.",
    },

    "AKT": {
        "title": "ENERGIE- & HANDLUNGSDYNAMIK",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du „fleißig“ bist –",
            "sondern ob du Zugriff über Handlung bekommst.",
            "",
            "Manche gewinnen Klarheit durch Denken.",
            "Andere gewinnen Klarheit durch Bewegung.",
            "",
            "Diese Kategorie zeigt,",
            "ob Tempo bei dir Momentum erzeugt –",
            "oder ob du eher über Ruhe stabil bleibst.",
        ],
        "hoch": [
            "Tempo ist bei dir kein Stress –",
            "Tempo ist dein Zündschlüssel.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du kommst schnell ins Tun",
            "• Du baust Momentum auf",
            "• Du entscheidest oft besser in Bewegung",
            "• Du ziehst Dinge durch, statt sie zu zerdenken",
            "",
            "Das ist ein Performance-Vorteil –",
            "wenn du Push und Brake bewusst steuerst.",
        ],
        "mittel": [
            "Du kannst Tempo machen – aber nicht immer stabil.",
            "Manchmal bist du schnell.",
            "Manchmal bleibst du hängen.",
            "",
            "Typisch:",
            "• Start fällt schwer, wenn die Aufgabe groß wirkt",
            "• Du bist gut im Sprint, aber inkonsistent im Rhythmus",
            "• Du wechselst zwischen Aktionismus und Warten",
        ],
        "niedrig": [
            "Du bist reflektierter – und oft langsamer im Start.",
            "Das kann Qualität bringen.",
            "",
            "Risiko:",
            "Du kommst zu spät in Umsetzung.",
            "Nicht, weil du nicht kannst –",
            "sondern weil du zu lange im Kopf bleibst.",
        ],
        "praxis": [
            "5-Minuten-Kickstart: kleinster Schritt, sofort. Nicht diskutieren.",
            "Version 1 liefern: Momentum vor Perfektion. Danach schärfen.",
            "Push/Brake setzen: bewusst beschleunigen – bewusst stoppen, bevor es kippt."
        ],
        "merksatz": "Tempo ist ein Hebel – aber nur, wenn du es führst. Sonst führt es dich.",
    },

    "INF": {
        "title": "VERARBEITUNGS- & ENTSCHEIDUNGSMODUS",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du rational bist –",
            "sondern wie du Sicherheit für Entscheidungen erzeugst.",
            "",
            "Information kann Klarheit sein.",
            "Oder ein Versteck.",
            "",
            "Diese Kategorie zeigt,",
            "ob du über Verständnis stabil wirst –",
            "oder ob du schneller über Intuition performst.",
        ],
        "hoch": [
            "Du wirst stabil, wenn du Zusammenhänge siehst.",
            "Du triffst bessere Entscheidungen, wenn die Lage klar ist.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du denkst strukturiert",
            "• Du erkennst Muster",
            "• Du triffst Entscheidungen fundiert",
            "• Du bleibst ruhiger, weil Fakten dir Zugriff geben",
            "",
            "Wichtig:",
            "Der Hebel kippt, wenn Analyse zur Verzögerung wird.",
        ],
        "mittel": [
            "Du brauchst etwas Klarheit – aber nicht alles.",
            "Manchmal analysierst du gut.",
            "Manchmal entscheidest du zu schnell oder zu spät.",
            "",
            "Typisch:",
            "• Du willst Sicherheit, aber verlierst dich gelegentlich",
            "• Du sammelst zu viel, wenn Druck steigt",
            "• Du gehst in Bauchgefühl, wenn Infos fehlen",
        ],
        "niedrig": [
            "Du bist intuitiver.",
            "Du entscheidest schneller ohne viel Datenlage.",
            "",
            "Das kann mutig und schnell sein –",
            "Risiko sind Fehlgriffe oder blinde Flecken,",
            "wenn Mindest-Klarheit fehlt.",
        ],
        "praxis": [
            "2–3 Pflichtinfos definieren. Nicht 20. Dann entscheiden.",
            "Analyse-Timer: Entscheidung bekommt ein Zeitfenster – sonst wirst du geführt.",
            "Pre-Mortem: „Was wäre der größte Fehler – und wie verhindern wir ihn?“"
        ],
        "merksatz": "Information ist dann Stärke, wenn sie zu Entscheidung führt – nicht wenn sie Entscheidung ersetzt.",
    },

    "COM": {
        "title": "VERGLEICHS- & LEISTUNGSREFERENZ",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du ehrgeizig bist –",
            "sondern ob Vergleich dich schärft oder dich steuert.",
            "",
            "Benchmarks können Standards erhöhen.",
            "Oder Fokus zerstören.",
            "",
            "Diese Kategorie zeigt,",
            "wie stark Wettbewerb, Messbarkeit und Referenzen",
            "deinen Leistungsmodus aktivieren.",
        ],
        "hoch": [
            "Vergleich schärft dich.",
            "Wenn es messbar wird, wirst du wach.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Standards steigen, Intensität steigt",
            "• Du gehst in den Leistungsmodus, wenn es zählt",
            "• Du willst messen statt hoffen",
            "• Du lieferst stärker, wenn Rahmen klar ist",
            "",
            "Wichtig:",
            "Vergleich ist ein Werkzeug – kein Boss.",
        ],
        "mittel": [
            "Wettbewerb kann dich pushen – aber nicht konstant.",
            "Manchmal aktiviert er dich.",
            "Manchmal lenkt er dich ab.",
            "",
            "Typisch:",
            "• Du nutzt Benchmarks, aber nicht sauber",
            "• Du wirst phasenweise getrieben",
            "• Du verlierst Fokus, wenn der Vergleich toxisch wird",
        ],
        "niedrig": [
            "Du bist weniger wettbewerbsgetrieben.",
            "Das kann Stabilität geben.",
            "",
            "Risiko:",
            "Zu wenig externe Reibung.",
            "Standards bleiben weich.",
            "Potenzial wird nicht maximal herausgefordert.",
        ],
        "praxis": [
            "1 Benchmark wählen. Nicht zehn. Klarer Maßstab, klare Richtung.",
            "Vergleich dosieren: Phasenweise – nicht permanent.",
            "Scoreboard für Entwicklung: Fortschritt sichtbar machen, nicht Ego füttern."
        ],
        "merksatz": "Vergleich ist dann Elite, wenn er Standards erhöht – ohne dich emotional zu steuern.",
    },

    "AUF": {
        "title": "SICHTBARKEITS- & FEEDBACKABHÄNGIGKEIT",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du Aufmerksamkeit magst –",
            "sondern ob Feedback bei dir Zugriff erzeugt oder Druck erzeugt.",
            "",
            "Resonanz kann Leistung stabilisieren.",
            "Oder dich abhängig machen.",
            "",
            "Diese Kategorie zeigt,",
            "wie stark Rückmeldung, Sichtbarkeit und Bewertung",
            "deine Leistung beeinflussen.",
        ],
        "hoch": [
            "Feedback ist bei dir Treibstoff.",
            "Resonanz aktiviert Einsatzbereitschaft.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du lieferst stärker, wenn Rückmeldung klar ist",
            "• Du ziehst Energie aus Sichtbarkeit",
            "• Du wirst konsequenter, wenn du „gesehen“ wirst",
            "• Du reagierst sensibel auf Bewertung",
            "",
            "Wichtig:",
            "Du musst Feedback führen – sonst führt Feedback dich.",
        ],
        "mittel": [
            "Feedback kann dich pushen – aber du brauchst es nicht immer.",
            "Manchmal ist es nützlich.",
            "Manchmal lenkt es ab.",
            "",
            "Typisch:",
            "• Du holst dir Rückmeldung, aber nicht systematisch",
            "• Du bist robust, aber manchmal getriggert",
            "• Du wirst inkonsistent, wenn Resonanz fehlt",
        ],
        "niedrig": [
            "Du bist unabhängiger.",
            "Du brauchst wenig Rückmeldung, um zu liefern.",
            "",
            "Das kann Stärke sein –",
            "Risiko ist Unsichtbarkeit.",
            "Du bringst Leistung – aber sie wird nicht abgerufen, weil sie keiner sieht.",
        ],
        "praxis": [
            "Feedbackfrequenz definieren: 1 Review/Woche – aktiv einfordern, nicht hoffen.",
            "Wirkung sichtbar machen: Ergebnisse kurz dokumentieren (sachlich, nicht ego).",
            "Trennen: Feedback ist Information – kein Urteil über deinen Wert."
        ],
        "merksatz": "Feedback ist dann ein Hebel, wenn es Klarheit erzeugt – nicht wenn es deine Stabilität ersetzt.",
    },

    "STA": {
        "title": "POSITIONS- & ANERKENNUNGSORIENTIERUNG",
        "worum": [
            "Diese Funktion entscheidet nicht, ob du Status willst –",
            "sondern ob Rolle und Position dir Zugriff geben.",
            "",
            "Rolle kann Sicherheit sein.",
            "Oder Druck.",
            "",
            "Diese Kategorie zeigt,",
            "wie stark Anerkennung, Stellung und Rollen-Klarheit",
            "deine Leistung freisetzen oder begrenzen.",
        ],
        "hoch": [
            "Rolle aktiviert Leistung.",
            "Wenn deine Position klar ist, steigt Anspruch und Präsenz.",
            "",
            "Typische Wirkung bei hoher Ausprägung:",
            "• Du spielst stärker „auf Niveau“, wenn Rahmen klar ist",
            "• Du übernimmst Raum, wenn du legitimiert bist",
            "• Du lieferst präsenter und konsequenter",
            "• Du reagierst sensibel auf Status-Dynamiken",
            "",
            "Wichtig:",
            "Status muss funktional bleiben – nicht emotional.",
        ],
        "mittel": [
            "Rolle hilft – aber sie ist nicht alles.",
            "Manchmal brauchst du Klarheit im System.",
            "Manchmal bleibst du intrinsisch stabil.",
            "",
            "Typisch:",
            "• Du willst Anerkennung, aber nicht um jeden Preis",
            "• Du nimmst Raum, aber manchmal zu wenig",
            "• Du schwankst zwischen Sichtbarkeit und Rückzug",
        ],
        "niedrig": [
            "Du bist stärker intrinsisch.",
            "Status ist kein großer Trigger.",
            "",
            "Risiko:",
            "Du bleibst zu unsichtbar.",
            "Nicht weil du klein bist –",
            "sondern weil du dir nicht genug Raum gibst, obwohl du Wirkung hättest.",
        ],
        "praxis": [
            "Rolle in 1 Satz definieren: „Ich bin verantwortlich für …“ – Klarheit erzeugt Zugriff.",
            "Wirkung sichtbar machen: Beitrag, Ergebnis, Verantwortung – kurz und sachlich.",
            "Status funktional nutzen: Orientierung und Erwartung, nicht Ego."
        ],
        "merksatz": "Position ist dann ein Hebel, wenn sie Wirkung erhöht – nicht wenn sie dich steuert.",
    },
}

MEANING_CARDS = {
    "DST": {
        "top": "Unter Druck kannst du Leistung abrufen: Fokus, Prioritäten, Handlung. Das ist ein echter Peak-Hebel, wenn es zählt.",
        "lowA": "Bei Druck sinkt dein Zugriff spürbar: Fokus bricht, Entscheidungen werden zäher, du verlierst Tempo oder gehst in Schutzmodus. Das kostet Leistung – nicht wegen Kompetenz, sondern wegen Belastungsmechanik.",
        "lowB": "In vielen Situationen funktioniert es – aber unter bestimmten Triggern (Zeitdruck, Bewertung, Erwartung) kippt der Zugriff. Reibung entsteht nicht, weil du ‘besser werden musst’, sondern weil du Druck anders dosieren musst als dein Umfeld.",
        "steer_high": "Druck dosieren: klare ‘High-Pressure’-Fenster + bewusste Regeneration. Nicht dauerhaft auf Anschlag.",
        "steer_mid": "Trigger kennen: Welche Druckart kippt dich? Dann Vorab-Standard setzen (1–3 Prioritäten, klare nächste Aktion).",
        "steer_low": "Druck entkoppeln: kurze Handlungsschritte, feste Routinen, klare Grenzen. Leistung über Struktur statt Stress erzeugen.",
        "short_top": "Unter Druck bleibt dein Zugriff da: Fokus, Entscheidung, Handlung. Das ist ein echter Leistungsvorteil, wenn es zählt.",
        "short_lowA": "Unter Druck kippt der Zugriff schnell: Fokus bricht, Entscheidungen werden zäh, Tempo geht verloren. Genau hier entsteht Reibung.",
        "short_lowB": "Meist funktioniert es – aber bestimmte Trigger (Zeitdruck, Bewertung, Erwartung) ziehen dir den Zugriff. Reibung entsteht situativ, nicht grundsätzlich." 
    },
    "STR": {
        "top": "Ordnung gibt dir Zugriff: klare Abläufe, Prioritäten, Zuständigkeiten. Du bleibst sauber und zuverlässig, wenn andere chaotisch werden.",
        "lowA": "Unordnung kostet dich konstant Energie: wechselnde Prioritäten, Unklarheit, Chaos. Du verlierst nicht wegen Fähigkeit – sondern weil du zu viel im Kopf tragen musst.",
        "lowB": "Du kannst Struktur – aber sie ist nicht dein Standard. Reibung entsteht, wenn Umfeld ‘System’ erwartet und du es situativ erst bauen musst. Dann geht Energie in Sortieren statt in Liefern.",
        "steer_high": "Nicht übersteuern: Struktur als Rahmen nutzen, nicht als Käfig. Fokus auf wenige Standards, die wirklich Output sichern.",
        "steer_mid": "Minimal-Standards setzen: 3 Prioritäten, 1 Entscheidungsregel, 1 Abschluss-Review. Stabilität ohne Overhead.",
        "steer_low": "Kompensieren statt verbiegen: externe Struktur nutzen (Templates, Checklisten, klare Zuständigkeiten). System entlastet Kopf.",
        "short_top":  "Struktur gibt dir Zugriff: du priorisierst sauber und bleibst stabil, wenn andere in Chaos kippen.",
        "short_lowA": "Unordnung kostet dich Leistung: zu viel im Kopf, zähe Entscheidungen, unnötiger Energieverlust. Hier entsteht klare Reibung.",
        "short_lowB": "Du kannst Struktur, aber sie greift nicht automatisch. Unter Druck verlierst du Zeit durch Sortieren statt durch Liefern."
    },
    "MAC": {
        "top": "Du nimmst Verantwortung aktiv: du steuerst, entscheidest, gehst voran. Das ist Leadership-Power in Leistungssystemen.",
        "lowA": "Verantwortung bleibt zu oft ‘draußen’: du wartest eher auf Vorgaben, Einfluss wird verschenkt. Reibung entsteht, wenn Entscheidungen bei dir erwartet werden – du aber keinen klaren Verantwortungsrahmen hast.",
        "lowB": "Du übernimmst Verantwortung, wenn Rahmen klar ist – aber nicht automatisch. Reibung entsteht, wenn Leadership ‘implizit’ erwartet wird, ohne dass du Mandat oder Grenze hast.",
        "steer_high": "Delegation aktiv trainieren: Verantwortung ja – aber nicht alles selbst. Ergebnisverantwortung statt Detailkontrolle.",
        "steer_mid": "Mandat klären: Was ist dein Verantwortungsrahmen? Welche Entscheidungen gehören dir? Dann handeln, bevor es ‘dringend’ wird.",
        "steer_low": "Verantwortung strukturiert holen: klare Aufgabenpakete, klare Entscheidungspunkte. Ohne Mandat keine saubere Verantwortung.",
        "short_top":  "Du übernimmst Verantwortung aktiv: du steuerst, entscheidest und gehst voran. Das erzeugt Wirkung und Verlässlichkeit.",
        "short_lowA": "Verantwortung landet zu oft nicht klar bei dir: Entscheidungen bleiben hängen, Einfluss wird verschenkt. Das erzeugt Reibung im System.",
        "short_lowB": "Du übernimmst Verantwortung, wenn der Rahmen klar ist. Wird Führung stillschweigend erwartet, entsteht Reibung durch Unklarheit."
    },
    "KON": {
        "top": "Soziale Rückkopplung stärkt dich: Austausch macht dich klarer, stabiler, abrufbarer. Du performst besser über Sparring.",
        "lowA": "Du bist sehr autonom: du brauchst wenig Anschluss, um zu liefern. Reibung entsteht, wenn du dadurch zu wenig Korrektur bekommst oder unsichtbar bleibst.",
        "lowB": "Kontakt funktioniert – aber nicht immer. Reibung entsteht, wenn zu viel Austausch deinen Fokus zerfranst oder wenn du zu spät kommunizierst und dann ‘Reparaturmodus’ brauchst.",
        "steer_high": "Input führen: Sparring gezielt nutzen, nicht jedem Feedback die Führung geben. Standard: feste Slots, klare Fragen.",
        "steer_mid": "Kontakt dosieren: in kritischen Phasen Sparring aktivieren, sonst Fokus schützen. Rhythmus statt Bauchgefühl.",
        "steer_low": "Kompensieren: 1 fester Feedback-Kanal + kurze Status-Updates. Du bleibst autonom – aber nicht blind.",
        "short_top":  "Austausch macht dich klarer: du nutzt Rückkopplung als Hebel und wirst darüber stabiler und abrufbarer.",
        "short_lowA": "Du bist sehr autonom. Reibung entsteht, wenn dadurch Korrektur fehlt oder du zu unsichtbar bleibst, obwohl du Leistung bringst.",
        "short_lowB": "Kontakt hilft, aber nicht immer. Zu viel Austausch zerfasert Fokus – zu wenig Kommunikation führt später zu unnötigem Reparieren."
    },
    "MOR": {
        "top": "Werte geben dir Stabilität: du entscheidest klarer, wenn es zu deinen Prinzipien passt. Integrität wird zu Leistungskraft.",
        "lowA": "Weiche Grenzen kosten Energie: du grübelst länger, bist inkonsistenter, weil innere Linie nicht klar genug geführt wird. Reibung entsteht durch inneren Lärm, nicht durch fehlendes Können.",
        "lowB": "Du hast Werte – aber sie sind situativ. Reibung entsteht, wenn Umfeld klare Kante erwartet und du innerlich noch abwägst. Dann verlierst du Zeit, Fokus und Ruhe.",
        "steer_high": "Nicht dogmatisch werden: Werte als Leitplanke nutzen, nicht als Starrheit. Klar + flexibel in Umsetzung bleiben.",
        "steer_mid": "No-Go-Liste schärfen: 3 Werte + 3 Grenzen. Entscheidungen werden schneller, weil Diskussion wegfällt.",
        "steer_low": "Kompensieren: externe Kriterien nutzen (Regeln, Prinzipien, Entscheidungsfragen). Linie bauen, ohne dich zu ‘verändern’.",
        "short_top":  "Deine Werte stabilisieren Entscheidungen: du hast eine klare innere Linie, die unter Druck trägt.",
        "short_lowA": "Weiche Grenzen erzeugen inneren Lärm: Grübeln, Unruhe, inkonsistente Entscheidungen. Genau das kostet Leistung.",
        "short_lowB": "Du hast Werte, aber sie greifen nicht immer automatisch. Wenn klare Kante erwartet wird, entsteht Reibung durch Abwägen."
    },
    "IND": {
        "top": "Autonomie setzt Leistung frei: wenn du gestalten darfst, lieferst du kreativen Output, Eigenständigkeit und Lösungen.",
        "lowA": "Zu wenig Autonomie zieht Energie: du wirst passiver oder lieferst ‘Dienst nach Vorschrift’. Reibung entsteht, wenn du in starre Vorgaben gezwungen wirst, die nicht dein Modus sind.",
        "lowB": "Du kannst Freiheit nutzen – aber sie muss geführt sein. Reibung entsteht, wenn entweder zu eng kontrolliert wird oder Ziele zu diffus sind und du dann keinen klaren Zugriff hast.",
        "steer_high": "Ergebnis klar halten: Ziel messbar, Weg frei. Nicht in Chaos kippen – Autonomie braucht Richtung.",
        "steer_mid": "Leitplanken definieren: 2–3 Regeln, dann gestalten. Freiheit in Zeitfenster einteilen, nicht grenzenlos.",
        "steer_low": "Kompensieren: klare Vorgaben + kleine Freiheitsfenster. Du performst über Rahmen – nutze ihn bewusst.",
        "short_top":  "Autonomie setzt Leistung frei: Gestaltungsspielraum macht dich produktiv, lösungsorientiert und wirksam.",
        "short_lowA": "Zu wenig Autonomie zieht Energie: du wirst passiver oder lieferst unter Wert. Reibung entsteht durch zu starre Vorgaben.",
        "short_lowB": "Freiheit funktioniert, wenn sie geführt ist. Ohne klare Ziele oder bei zu enger Kontrolle entsteht Reibung durch fehlenden Zugriff."
    },
    "AKT": {
        "top": "Tempo ist dein Motor: du kommst ins Tun, erzeugst Momentum, ziehst Umsetzung durch. Entscheidung folgt oft aus Handlung.",
        "lowA": "Dynamik startet schwer: du bleibst zu lange im Kopf, kommst zu spät in Umsetzung. Reibung entsteht, wenn Umfeld Tempo erwartet und dein System erst Sicherheit aufbauen muss.",
        "lowB": "Du kannst schnell sein – aber nicht konstant. Reibung entsteht, wenn du zwischen Sprint und Stillstand wechselst und dadurch Rhythmus verlierst.",
        "steer_high": "Push & Brake steuern: Tempo bewusst setzen – und bewusst stoppen, bevor es hektisch wird.",
        "steer_mid": "Rhythmus bauen: Start-Ritual + Timeboxing. Stabilität schlägt ‘Motivation’.",
        "steer_low": "Kompensieren: kleinster Schritt sofort (5-Minuten-Start). Output über Mini-Aktionen statt ‘große Energie’.",
        "short_top":  "Tempo ist dein Motor: du kommst ins Tun, baust Momentum auf und ziehst Umsetzung durch.",
        "short_lowA": "Der Start ist zäh: du bleibst zu lange im Kopf und kommst zu spät in Handlung. Reibung entsteht, wenn Tempo gefordert ist.",
        "short_lowB": "Du kannst Tempo, aber nicht konstant. Reibung entsteht durch Wechsel zwischen Sprint und Stillstand – Rhythmus geht verloren."
    },
    "INF": {
        "top": "Verstehen stabilisiert dich: du siehst Zusammenhänge, triffst bessere Entscheidungen, bleibst ruhiger – auch unter Druck.",
        "lowA": "Zu wenig Klarheit macht dich wacklig: du zögerst oder entscheidest zu intuitiv. Reibung entsteht, wenn Komplexität hoch ist und du keine Minimum-Infos hast.",
        "lowB": "Du kannst analysieren – aber situativ. Reibung entsteht, wenn du entweder zu viel Info sammelst oder zu schnell entscheidest, je nach Druck.",
        "steer_high": "Analyse begrenzen: ‘genug Klarheit’ definieren, dann entscheiden. Sonst wird Verständnis zur Bremse.",
        "steer_mid": "2–3 Pflichtinfos pro Entscheidung. Wenn sie da sind: Go. Wenn nicht: bewusst Risiko markieren.",
        "steer_low": "Kompensieren: Entscheidung über klare Heuristiken (Checkfragen). Minimum-Info sichern, dann handeln.",
        "short_top":  "Verstehen gibt dir Zugriff: du erkennst Muster, triffst bessere Entscheidungen und bleibst auch unter Druck stabil.",
        "short_lowA": "Zu wenig Klarheit macht Entscheidungen wacklig: Zögern oder zu schnelle Intuition. Reibung entsteht bei hoher Komplexität.",
        "short_lowB": "Du kannst analysieren, aber situativ. Unter Druck kippst du entweder in Überanalyse oder in zu schnelle Entscheidungen."
    },
    "COM": {
        "top": "Vergleich schärft dich: Benchmarks pushen Standards, Intensität steigt, du gehst in Leistungsmodus, wenn es messbar wird.",
        "lowA": "Ohne Vergleich fehlt dir oft externe Reibung: Standards bleiben weicher, Intensität steigt weniger. Reibung entsteht, wenn Umfeld Wettbewerb nutzt und du dadurch ‘unterfordert’ wirkst.",
        "lowB": "Vergleich kann pushen – aber nicht immer. Reibung entsteht, wenn Benchmarks mal antreiben, mal ablenken, weil der Maßstab nicht sauber geführt ist.",
        "steer_high": "Vergleich kontrollieren: Benchmarks als Tool nutzen, nicht als emotionale Steuerung. Fokus bleibt bei Output.",
        "steer_mid": "Phasenweise messen: Sprint-Phasen mit Benchmarks, dazwischen Stabilitätsmodus ohne Dauervergleich.",
        "steer_low": "Kompensieren: eigene Standards setzen (KPI / Zielkriterien). Externe Reibung bewusst hinzufügen – dosiert.",
        "short_top":  "Vergleich schärft dich: messbare Standards pushen Leistung, Fokus und Intensität steigen.",
        "short_lowA": "Ohne Vergleich fehlt oft Reibung von außen: Standards bleiben weicher, Intensität steigt weniger. Das kann Leistung kosten.",
        "short_lowB": "Vergleich kann pushen oder ablenken. Wenn Maßstäbe nicht sauber geführt sind, entsteht Reibung durch inkonsistente Orientierung."
    },
    "AUF": {
        "top": "Sichtbarkeit & Feedback können dich stabilisieren: Resonanz gibt Richtung und verstärkt Abrufbarkeit – wenn du sie führst.",
        "lowA": "Du bist unabhängig: du brauchst wenig Feedback. Reibung entsteht eher andersrum: du wirst unsichtbar oder unterkommunizierst, obwohl du Leistung bringst – Wirkung wird nicht abgerufen.",
        "lowB": "Du kannst Feedback nutzen, willst aber nicht abhängig sein. Reibung entsteht, wenn Umfeld dauernd Rückmeldung will oder Sichtbarkeit erwartet – und du das als Energieverlust erlebst.",
        "steer_high": "Feedback führen: klare Kanäle, klare Kriterien. Resonanz nutzen, ohne von Bewertung abhängig zu werden.",
        "steer_mid": "Feedback zuschalten: nur in kritischen Phasen aktiv einholen, sonst intern steuern und Fokus schützen.",
        "steer_low": "Kompensieren: Sichtbarkeit funktional machen (kurzes Ergebnis-Log). Kein ‘Feedback suchen’, sondern Wirkung dokumentieren.",
        "short_top":  "Feedback kann dich stabilisieren: Resonanz gibt Richtung und erhöht Abrufbarkeit – wenn du sie bewusst führst.",
        "short_lowA": "Du brauchst wenig Feedback. Reibung entsteht, wenn du dadurch zu unsichtbar wirst oder Wirkung nicht abgerufen wird.",
        "short_lowB": "Du nutzt Feedback, willst aber nicht abhängig sein. Reibung entsteht, wenn Umfeld Dauer-Resonanz fordert oder Sichtbarkeit erwartet."
    },
    "STA": {
        "top": "Rolle/Position geben dir Zugriff: klare Stellung erhöht Präsenz, Anspruch und sichtbare Leistung – wenn du es funktional nutzt.",
        "lowA": "Status ist kein Trigger: du lieferst auch ohne Bühne. Reibung entsteht, wenn du dadurch zu wenig Raum nimmst und deine Wirkung unter Wert bleibt.",
        "lowB": "Rolle hilft, aber ist nicht dein Motor. Reibung entsteht, wenn Umfeld Statusspiele spielt oder klare Positionierung verlangt und du dich dadurch eingeengt fühlst.",
        "steer_high": "Status funktional halten: Rolle = Verantwortung, nicht Ego. Präsenz ja – aber ohne Dominanz-Spielchen.",
        "steer_mid": "Rolle bewusst klären: ‘Wofür stehe ich hier?’ Dann gezielt Raum nehmen, ohne dich zu verbiegen.",
        "steer_low": "Kompensieren: Wirkung sichtbar machen (Beitrag/Ergebnis). Raum nehmen als Pflicht zur Verantwortung, nicht als Selbstdarstellung.",
        "short_top":  "Rolle und Position geben dir Zugriff: klare Stellung erhöht Präsenz, Anspruch und sichtbare Leistung.",
        "short_lowA": "Status triggert dich wenig. Reibung entsteht, wenn du dadurch zu wenig Raum nimmst und Wirkung unter Wert bleibt.",
        "short_lowB": "Rolle hilft, aber ist nicht dein Motor. Reibung entsteht bei Statusspielen oder wenn klare Positionierung dich einengt."
    },
}

# ============================================================
# STYLES / LOOK (weiß, print-friendly, Webreport-ähnlich)
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
            keepWithNext=1,   # ✅ hier rein, sauber
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
        t,
        radius=6,
        stroke=strokeWidth,        # <-- neu (statt fix 0.7)
        strokeColor=strokeColor,
        fillColor=fillColor,
        padding=6
    )

def _soft_card(title_left: str, title_right: str, body: str, styles) -> Table:
    # Kopfzeile: links Label, rechts Wert (z.B. 82%)
    head = Table(
        [[
            Paragraph(f"<b>{_esc(title_left)}</b>", styles["Label"]),
            Paragraph(f"<b>{_esc(title_right)}</b>", styles["Label"]),
        ]],
        colWidths=[None, 24 * mm],
    )
    head.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        # leichte “Header-Zeile” innerhalb der Card
        ("LINEBELOW", (0,0), (-1,-1), 0.6, BORDER),

        # kleine Abstände, damit es wie eine klare Kopfzeile wirkt
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),

        # rechter Titel (z.B. Prozent) sauber rechts
        ("ALIGN", (1,0), (1,0), "RIGHT"),
    ]))

    # Body (String ODER Flowable)
    if isinstance(body, str):
        body_flow = Paragraph(_esc(body or ""), styles["P"])
    else:
        body_flow = body

    t = Table([[head], [body_flow]], colWidths=[None])

    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),  # minimal heller als vorher

        # mehr “Card-Luft”
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),

        # dezente Trennlinie unter dem Head (wie Web-Card Header)
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor("#e5e7eb")),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
    ]))
    return RoundedCard(t, radius=6, stroke=0.7, strokeColor=BORDER, fillColor=colors.HexColor("#f8fafc"), padding=6)

def _bar(pct: int, width_mm: int = 160, height_mm: int = 4):
    return RoundedProgressBar(
        pct,
        width_mm=width_mm,
        height_mm=height_mm
    )

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
        Paragraph("In jeder Kategorie findest du drei Ausprägungen (hoch/mittel/niedrig).", styles["P"]),
        Paragraph("Der Bereich, der auf dich zutrifft, ist im Report markiert (grüner Rahmen).", styles["P"]),
        Paragraph("Die anderen beiden Bereiche dienen nur als Kontext – damit du verstehst, wie Leistung entsteht oder kippt.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Wenn du an mehreren Stellen denkst: <b>„Verdammt – das bin genau ich“</b> → dann funktioniert er.", styles["P"]),
        Paragraph("Wenn du Widerstand spürst → dann triffst du gerade auf deine Reibung.", styles["P"]),
        Spacer(1, 4),
        Paragraph("Beides ist wertvoll. Beides ist steuerbar.", styles["P"]),
    ], styles))

    story.append(Spacer(1, 6))
    story.append(Paragraph("„Leistung ist kein Zufall. Sie entsteht dort, wo Klarheit, Steuerung und Verantwortung zusammenkommen.“", styles["Quote"]))
    return story

def _page_2_web_snapshot(name: str, email: str, ptype: str, top3, bottom2, styles):
    story: List[Any] = []
    story.append(_topline_brand(name, email, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Dein Ergebnis ist da.", styles["H0"]))
    story.append(Paragraph("Du siehst nicht „wer du bist“, sondern <b>wie du unter Druck funktionierst</b> – und wie du das steuerst.", styles["Muted"]))
    story.append(Spacer(1, 6))

    t = TYPE_MAP.get(ptype, None) or {"title": f"Typ {ptype}", "label":"—", "hint":"—", "explain":"—"}

    type_head = Table([
    [
        Badge(_esc(ptype)),  # <- rund
        Paragraph(
            f"<font size='15'><b>{_esc(t['title'])}</b></font><br/>"
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
        Paragraph("Hinweis: Es geht nicht darum, überall „hoch“ zu sein. Entscheidend ist, dass du weißt, <b>wo du Leistung holst</b> und <b>wo Reibung entsteht</b> – damit du gezielt steuerst.", styles["Muted"])
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
            Paragraph(
                f"<b>{_esc(FUNCTION_NAMES.get(fid, fid))}</b>",
                styles["P"]
            ),
            "",  # Spacer-Spalte
            Paragraph(
                f"<b>{int(pct)}%</b>",
                styles["P"]
            ),
        ])

    tbl = Table(rows, colWidths=[None, 6*mm, 18*mm])

    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1),
         [colors.white, colors.HexColor("#f7f8fa")]),
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
        Paragraph("<b>0–25 %:</b> niedrig ausgeprägt (hier entsteht typischerweise Reibung – je nach Kontext)", styles["P"]),
        Paragraph("<b>25–75 %:</b> mittel ausgeprägt (flexibel – kann tragen oder kippen, abhängig von Rahmen & Druck)", styles["P"]),
        Paragraph("<b>75–100 %:</b> hoch ausgeprägt (starker Hebel – wenn du ihn bewusst steuerst)", styles["P"]),
    ], styles))

    return story

from reportlab.platypus import KeepTogether

def _page_4_meaning_cards(top3, bottom2, styles):
    story: List[Any] = []

    h = Paragraph("Was das konkret bedeutet", styles["H0"])
    h.keepWithNext = 1

    sub = Paragraph(
        "Hier siehst du glasklar, wie du unter Druck performst – "
        "wo du <b>Leistung gewinnst</b> und wo du sie unnötig verlierst.",
        styles["Muted"]
    )
    sub.keepWithNext = 1

    # ✅ Header-BLOCK darf NICHT allein stehen (Orphan-Heading Fix)
    story.append(KeepTogether([
        h,
        sub,
        Spacer(1, 4),
        Paragraph("<b>Deine stärksten Hebel</b>", styles["Label"]),
    ]))

    story.append(Spacer(1, 4))

    # ✅ Cards kompakter rendern (Spacing reduziert)
    for i, (fid, pct) in enumerate(top3):
        story.append(_meaning_web_card(fid, int(pct), mode="top", styles=styles))
        if i < len(top3) - 1:
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Deine Reibungszonen</b>", styles["Label"]))
    story.append(Spacer(1, 4))

    for i, (fid, pct) in enumerate(bottom2):
        pct_i = int(pct)
        story.append(_meaning_web_card(fid, pct_i, mode="low", styles=styles))
        if i < len(bottom2) - 1:
            story.append(Spacer(1, 4))

    # ✅ Merksatz soll NICHT auf eine neue Seite rutschen
    merksatz = Paragraph(
        "Merksatz: Top-Hebel sind deine stärksten Wirkungen. Reibungszonen sind die Stellen, "
        "wo du unnötig Leistung verlierst – beides ist steuerbar.",
        styles["Muted"]
    )

    story.append(Spacer(1, 6))
    story.append(KeepTogether([merksatz]))

    return story
    
def _page_category(fid: str, pct: int, styles):
    t = CATEGORY_TEXT.get(fid)
    if not t:
        t = {"title": FUNCTION_NAMES.get(fid, fid), "worum":["(Text fehlt)"], "hoch":["(Text fehlt)"], "mittel":["(Text fehlt)"], "niedrig":["(Text fehlt)"], "praxis":["(Text fehlt)"]*3, "merksatz":"(Text fehlt)"}

    band = _band(pct)
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

     # Alle 3 Bereiche zeigen, aber den zutreffenden grau highlighten
    band = _band(pct)

    block_titles = {
        "hoch":   "Wenn der Wert hoch ist (75–100 %)",
        "mittel": "Wenn der Wert im mittleren Bereich liegt (25–75 %)",
        "niedrig":"Wenn der Wert niedrig ist (0–25 %)",
    }

    # optional: wenn in deinen Texten noch "(Orientierung ...)" steht -> rausfiltern
    def _clean_lines(lines: List[str]) -> List[str]:
        out = []
        for ln in lines:
            s = (ln or "").strip()
            if s.startswith("(") and "Orientierung" in s:
                continue
            out.append(ln)
        return out

    prefix_map = {
        "hoch": "+",
        "mittel": "·",
        "niedrig": "-",
    }

    for b in ["hoch", "mittel", "niedrig"]:
        is_active = (b == band)

        fill = colors.HexColor("#ecfdf5") if is_active else colors.white  # sehr helles Grün (SW = hellgrau)
        stroke = GREEN if is_active else BORDER
        sw = 2.0 if is_active else 0.7  # deutlich dicker für SW-Druck

        title = block_titles[b]
        if is_active:
            title = "DEIN BEREICH · " + title  # optional, aber sehr hilfreich in SW

        story.append(
            _box(
                title,
                [_lines_to_paragraph(_clean_lines(t[b]), styles)],
                styles,
                fillColor=fill,
                strokeColor=stroke,
                strokeWidth=sw
            )
        )
        story.append(Spacer(1, 6))

    pr = t.get("praxis", [])[:3]
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

    story.append(_box("Merksatz", [Paragraph(_esc(t.get("merksatz","")), styles["P"])], styles))
    story.append(Spacer(1, 14))
    return story

def _page_actionplan_and_outro(top3, bottom2, styles):
    story: List[Any] = []

    # Erst berechnen
    top_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in top3])
    low_names = ", ".join([FUNCTION_NAMES.get(fid, fid) for fid, _ in bottom2])

    # Actionplan Überschrift soll an der Fokus-Box "dran bleiben"
    h = Paragraph("Actionplan & nächste Schritte", styles["H0"])
    h.keepWithNext = 1
    story.append(h)

    story.append(Spacer(1, 6))

    sog = Paragraph("<b>Leistung ist kein Zufall. Leistung ist steuerbar.</b>", styles["P"])
    sog.keepWithNext = 1
    story.append(sog)

    story.append(Spacer(1, 6))

    # Fokus-Box (kein KeepTogether -> kein Layout-Crash)
    story.append(_box("Dein Fokus (14 Tage)", [
        Paragraph(f"<b>Top-Hebel nutzen:</b> {_esc(top_names)}", styles["P"]),
        Paragraph(
            "Wähle <b>eine</b> Praxisregel aus deinem stärksten Hebel – "
            "und setze sie täglich um.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(f"<b>Reibung reduzieren:</b> {_esc(low_names)}", styles["P"]),
        Paragraph(
            "Wähle <b>eine</b> Praxisregel aus deiner Reibungszone – "
            "und mache sie zur Pflicht.",
            styles["P"]
        ),
    ], styles))

    story.append(Spacer(1, 6))

    # =========================
    # Abschluss in 3 Boxen (kein Split nötig)
    # =========================

    story.append(_box("Abschluss", [
        Paragraph("Dieses Profil ist kein Urteil.", styles["P"]),
        Paragraph("Und es ist keine Motivation.", styles["P"]),
        Spacer(1, 2),
        Paragraph("Es ist eine Landkarte.", styles["P"]),
        Spacer(1, 2),
        Paragraph(
            "Sie zeigt dir nicht, wer du bist, sondern wie du Leistung erzeugst – "
            "und warum sie unter Druck manchmal abrufbar ist und manchmal nicht.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Du hast jetzt gesehen, wo dein Zugriff stabil ist, wo er kippt "
            "und welche Muster darüber entscheiden, ob Leistung kommt – oder verloren geht.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph("Das allein ist wertvoll.", styles["P"]),
        Spacer(1, 2),
        Paragraph("<b>Doch Klarheit allein ändert gar nichts.</b>", styles["P"]),
    ], styles))

    story.append(Spacer(1, 6))

    story.append(_box("Was jetzt entscheidet", [
        Paragraph(
            "Der Unterschied entsteht nicht im Verstehen. "
            "Er entsteht dort, wo Entscheidungen getroffen werden – auch wenn sie unbequem sind.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph("Unter Druck. Unter Verantwortung. Unter Erwartung.", styles["P"]),
        Spacer(1, 2),
        Paragraph(
            "Und genau hier scheitern selbst sehr erfolgreiche Menschen. "
            "Nicht, weil sie zu wenig wissen. "
            "Nicht, weil ihnen Disziplin fehlt. "
            "Sondern weil ihrem System unter Druck der Zugriff fehlt.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "<b>Ich arbeite nicht an Motivation. "
            "Ich baue Systeme, damit Leistung unter Druck abrufbar wird.</b>",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Nicht theoretisch. Nicht im Idealzustand. "
            "Sondern genau dort, wo Führung, Verantwortung "
            "und Entscheidung wirklich stattfinden.",
            styles["P"]
        ),
    ], styles))

    story.append(Spacer(1, 6))

    story.append(_box("Deine Entscheidung", [
        Paragraph(
            "Denn Leistung ist kein Zufall. "
            "Sie ist das Ergebnis von Struktur, Steuerung "
            "und der Fähigkeit, sich selbst im entscheidenden Moment zu führen.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph("<b>Und jetzt kommt der entscheidende Punkt:</b>", styles["P"]),
        Spacer(1, 2),
        Paragraph(
            "<b>Die Frage ist nicht, ob du mehr Potenzial hast. "
            "Die Frage ist, wie lange du es noch ungenutzt lassen willst.</b>",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Du kannst dieses Profil schließen und weitermachen wie bisher. "
            "Vieles wird weiterhin funktionieren. "
            "Doch Frust, Hilflosigkeit und Leistungsverlust "
            "werden sich immer wiederholen.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Oder du entscheidest dich, dein Leistungssystem "
            "nicht länger dem Zufall zu überlassen.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Für Menschen, die führen. Verantwortung tragen. "
            "Und mehr wollen als nur funktionieren.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Für Menschen, die wissen, dass ihr nächster Schritt "
            "nicht aus weiterem Input entsteht, "
            "sondern aus klarer Spiegelung, konsequenter Steuerung "
            "und einem System, das auch dann trägt, "
            "wenn der Druck am größten wird.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Wenn du beim Lesen gespürt hast, dass hier etwas trifft, "
            "das tiefer geht als Motivation oder Mindset, "
            "dann ist das kein Zufall.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Dann bist du genau an dem Punkt, "
            "an dem echte Performance-Arbeit beginnt.",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "<b>Nicht für jeden. "
            "Sondern für die, die sich entscheiden, "
            "einen Unterschied machen zu wollen.</b>",
            styles["P"]
        ),
        Spacer(1, 2),
        Paragraph(
            "Wenn du willst, ist das hier nicht das Ende dieses Reports. "
            "Sondern der Anfang einer Phase, "
            "in der Leistung reproduzierbar, "
            "Führung klar "
            "und Erfolg steuerbar wird.",
            styles["P"]
        ),
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
    # unsichtbare Trennzeichen entfernen
    s = s.replace("\xad", "").replace("\u200b", "").replace("\u2060", "")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _lines_to_paragraph(lines: List[str], styles, bullet_prefix: str = "") -> Paragraph:
    """
    Render-Regeln:
    - Leerzeile => Absatzwechsel
    - Zeilen, die mit "•" / "-" / "–" beginnen => als Listenzeile mit prefix (+ / · / -)
    - Alles wird zeilenweise gerendert (über <br/>), damit Listen immer sauber untereinander stehen
    """
    paras: List[str] = []
    cur_lines: List[str] = []

    def flush():
        nonlocal cur_lines
        if cur_lines:
            paras.append("<br/>".join(cur_lines))
            cur_lines = []

    for ln in lines:
        s = (ln or "").strip()

        # Absatzwechsel
        if not s:
            flush()
            continue

        # Listen-Zeile erkennen (deine Texte nutzen "•", manchmal auch "-" oder "–")
        if s.startswith(("•", "-", "–")):
            item = s.lstrip("•-–").strip()

            # Prefix setzen (hoch:+ / mittel:· / niedrig:-)
            pref = (bullet_prefix or "").strip()
            if pref:
                # einheitlicher Einzug + Prefix + Abstand
                cur_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(pref)}&nbsp;&nbsp;{_esc(item)}")
            else:
                # falls du mal ohne Prefix rendern willst
                cur_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{_esc(item)}")
            continue

        # normale Zeile
        cur_lines.append(_esc(s))

    flush()
    html = "<br/><br/>".join(paras)
    return Paragraph(html, styles["P"])

def _format_explain(text: str, styles):
    """
    Macht aus:
    '... Momenten. Führung: Druck dosieren ...'
    => Absatz + Leerzeile + 'Führung:' fett am Zeilenanfang
    """
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

def _meaning_web_card(fid: str, pct: int, mode: str, styles, low_variant: str | None = None):
    """
    Web-Report Card Layout:
    - Tag links ("Top-Hebel"/"Reibungszone"), Prozent rechts
    - großer Funktionsname
    - Beschreibung
    - neue Zeile: Steuerung fett + Text
    """

    # ------------------------------------------------
    # 1) Grunddaten
    # ------------------------------------------------
    tag_left = "Top-Hebel" if mode == "top" else "Reibungszone"
    card = MEANING_CARDS.get(fid, {})
    title = FUNCTION_NAMES.get(fid, fid)

    # ------------------------------------------------
    # 2) Band-Logik (0–25 / 25–75 / 75–100)
    # ------------------------------------------------
    def _band(pct: int) -> str:
        if pct < 25:
            return "low"
        if pct < 75:
            return "mid"
        return "high"

    # ------------------------------------------------
    # 3) Text-Auswahl
    # ------------------------------------------------
    def _pick_low(card: dict, pct: int) -> str:
        # Reibungszone:
        # 0–25 %  -> lowA
        # 25–75 % -> lowB
        return card.get("lowA", "") if pct < 25 else card.get("lowB", "")

    def _pick_steer(card: dict, pct: int) -> str:
        b = _band(pct)
        if b == "high":
            return card.get("steer_high", "")
        if b == "mid":
            return card.get("steer_mid", "")
        return card.get("steer_low", "")

    if mode == "top":
        desc = card.get("top", "")
    else:
        desc = _pick_low(card, pct)

    steer = _pick_steer(card, pct)

    # ------------------------------------------------
    # 4) Styles
    # ------------------------------------------------
    title_style = _tmp_style(13, bold=True, color="#111111")

    # ------------------------------------------------
    # 5) Card-Header
    # ------------------------------------------------
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

    # ------------------------------------------------
    # 6) Card-Body
    # ------------------------------------------------
    body_title = Paragraph(_esc(title), title_style)
    body_desc = Paragraph(_esc(desc), styles["P"])

    steer_style = ParagraphStyle(
        "Steer",
        parent=styles["P"],
        fontSize=10.5,
        leading=12.5,
        textColor=colors.HexColor("#444444"),
        spaceBefore=0,
        spaceAfter=0,
    )
    body_steer = Paragraph(
        f"<b>Steuerung:</b> {_esc(steer)}",
        steer_style
    )

    # ------------------------------------------------
    # 7) Card-Wrapper
    # ------------------------------------------------
    t = Table(
        [[head], [body_title], [body_desc], [body_steer]],
        colWidths=[None]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),

        # horizontal deutlich schlanker
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),

        # vertikal stark komprimiert
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),

        # Titel-Zeile (Funktionsname)
        ("TOPPADDING", (0, 1), (-1, 1), 3),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 3),

        # Beschreibung
        ("TOPPADDING", (0, 2), (-1, 2), 1),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 3),

        # Steuerung-Zeile
        ("LINEABOVE", (0, 3), (-1, 3), 0.4, colors.HexColor("#e5e7eb")),
        ("TOPPADDING", (0, 3), (-1, 3), 3),
        ("BOTTOMPADDING", (0, 3), (-1, 3), 1),
    ]))

    return RoundedCard(
        t,
        radius=6,
        stroke=0.7,
        strokeColor=BORDER,
        fillColor=colors.HexColor("#f8fafc"),
        padding=6
    )
    
class RoundedProgressBar(Flowable):
    def __init__(
        self,
        pct: int,
        width_mm: float = 160,
        height_mm: float = 4,
        radius_mm: float | None = None,
        fillColor=GREEN,
        backColor=colors.HexColor("#e5e7eb"),
        strokeColor=colors.HexColor("#d1d5db"),
        strokeWidth: float = 0.6,
    ):
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
        # Background (grau) + Border
        c.setLineWidth(self.strokeWidth)
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.backColor)
        c.roundRect(0, 0, self.width, self.height, r, stroke=1, fill=1)

        # Fill (grün) – ohne Stroke, damit es sauber bleibt
        fill_w = (self.pct / 100.0) * self.width
        if fill_w > 0:
            c.setStrokeColor(self.fillColor)
            c.setFillColor(self.fillColor)
            # bei sehr kleinen Werten Radius begrenzen, sonst sieht's komisch aus
            r2 = min(r, fill_w / 2)
            c.roundRect(0, 0, fill_w, self.height, r2, stroke=0, fill=1)

        c.restoreState()
  
class Badge(Flowable):
    def __init__(self, text: str, w=12*mm, h=12*mm,
                 radius=3, stroke=0.9, strokeColor=GREEN, fillColor=colors.HexColor("#e9f7ef")):
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
        c.drawCentredString(self.w/2, (self.h/2) - 6, self.text)

        c.restoreState()
    
class RoundedCard(Flowable):
    def __init__(self, inner, radius=6, stroke=1,
                 strokeColor=BORDER, fillColor=colors.white, padding=8):
        super().__init__()
        self.inner = inner
        self.radius = radius
        self.stroke = stroke
        self.strokeColor = strokeColor
        self.fillColor = fillColor
        self.padding = padding

    def wrap(self, availWidth, availHeight):
        iw, ih = self.inner.wrap(
            availWidth - 2 * self.padding,
            availHeight
        )
        self.width = availWidth
        self.height = ih + 2 * self.padding
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(self.strokeColor)
        c.setFillColor(self.fillColor)
        c.setLineWidth(self.stroke)
        c.roundRect(
            0, 0,
            self.width,
            self.height,
            self.radius,
            stroke=1,
            fill=1
        )
        self.inner.drawOn(c, self.padding, self.padding)
        c.restoreState()