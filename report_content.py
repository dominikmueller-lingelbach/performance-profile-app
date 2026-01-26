# report_content.py
from typing import Dict

# 11 FUNKTIONEN: Klartext-Namen (IDs -> Anzeige)
FUNCTION_NAMES: Dict[str, str] = {
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

# 5 TYPEN / ARBEITSMODI: Kurz + Erklärung (Report-tauglich)
TYPE_MAP: Dict[str, Dict[str, str]] = {
    "A": {
        "name": "Stabilitätsmodus",
        "headline": "Ich bleibe klar, wenn andere wackeln.",
        "explain": (
            "Du lieferst konstant, wenn Rahmen, Standards und Prioritäten klar sind. "
            "Du gibst Stabilität, triffst saubere Entscheidungen und hältst Qualität – auch wenn es unruhig wird."
        ),
        "lead": "Führung/Steuerung: klare Rahmen, saubere Abläufe, keine künstliche Hektik."
    },
    "B": {
        "name": "Druckmodus",
        "headline": "Je höher der Druck, desto besser werde ich – wenn ich ihn steuere.",
        "explain": (
            "Du kannst in kritischen Momenten extrem fokussiert performen. "
            "Du brauchst Aktivierung – aber nicht als Dauerzustand. Ohne klare Regeln drohen Übersteuerung und Erschöpfung."
        ),
        "lead": "Führung/Steuerung: Druck dosieren, klare Entscheidungsregeln, Regeneration aktiv planen."
    },
    "C": {
        "name": "Gestaltungsmodus",
        "headline": "Ich brauche Freiheit, um Leistung zu bringen.",
        "explain": (
            "Du performst über Autonomie, Eigenständigkeit und konzeptionelles Denken. "
            "Ziele müssen klar sein – der Weg darf offen bleiben. Zu enge Vorgaben drücken deine Leistung."
        ),
        "lead": "Führung/Steuerung: Ziel klar, Weg offen. Ergebnisse messen statt Prozesse kontrollieren."
    },
    "D": {
        "name": "Vergleichsmodus",
        "headline": "Leistung entsteht für mich im Wettbewerb.",
        "explain": (
            "Du gehst an, wenn Standards hoch sind, Vergleich möglich ist und Feedback kommt. "
            "Richtig geführt ist das ein starker Performance-Motor – falsch geführt entsteht Fremdsteuerung."
        ),
        "lead": "Führung/Steuerung: klare Maßstäbe, sachliches Feedback, Vergleich kontrolliert einsetzen."
    },
    "E": {
        "name": "Kontrollmodus",
        "headline": "Ich übernehme Verantwortung – und behalte den Überblick.",
        "explain": (
            "Du willst Verantwortung, Einfluss und klare Steuerung. "
            "Du kannst Führung stabil machen – Risiko ist Mikromanagement oder zu viel allein tragen."
        ),
        "lead": "Führung/Steuerung: Verantwortung abgrenzen, Delegation trainieren, Ergebnis statt Detail kontrollieren."
    },
}

# FUNKTIONSTEXTE fürs PDF: Top / Low / Steuerung (Report-Qualität)
# Wichtig: Das sind die Bausteine, die pro Kategorie individuell gezogen werden.
FUNCTION_TEXT: Dict[str, Dict[str, str]] = {
    "DST": {
        "what": "Wie du unter Belastung funktionierst: Druck aktiviert dich – oder frisst Zugriff.",
        "top": "Unter Druck bleibst du handlungsfähig, priorisierst klar und kannst Leistung abrufen, wenn es zählt.",
        "low": "Wenn Druck steigt, sinkt Zugriff/Fokus schneller. Risiko: Blockade, Vermeidung, inkonsistente Leistung in Peak-Momenten.",
        "steer": "Steuerung: Druck dosieren, klare Peak-Fenster definieren, Erholung als festen Bestandteil planen."
    },
    "STR": {
        "what": "Wie sehr Struktur deine Performance stabilisiert.",
        "top": "Klare Abläufe, Standards und Prioritäten geben dir Ruhe und Konstanz – du bleibst sauber, zuverlässig und stabil.",
        "low": "Unklare Zuständigkeiten/chaotische Abläufe kosten Energie, erhöhen Fehlerquote und machen Entscheidungen schwerer.",
        "steer": "Steuerung: Standards + Routinen + klare Zuständigkeiten schriftlich definieren."
    },
    "MAC": {
        "what": "Wie stark du Verantwortung/Einfluss suchst – und darüber Leistung abrufst.",
        "top": "Du übernimmst Ownership, entscheidest und steuerst. Das ist ein Leadership-Hebel in Leistungssystemen.",
        "low": "Du wartest eher auf Vorgaben: Verantwortung bleibt diffus, Entscheidungen verzögern sich, Ownership sinkt.",
        "steer": "Steuerung: Entscheidungsspielräume definieren, Verantwortung eindeutig zuordnen, Ownership trainieren."
    },
    "KON": {
        "what": "Wie sehr Leistung durch soziale Rückkopplung beeinflusst wird.",
        "top": "Austausch/Sparring erhöht deine Klarheit, Leistungsstabilität und Entscheidungsqualität.",
        "low": "Ohne Anschluss/Feedback kippt Stabilität schneller: Isolation, weniger Korrektur, weniger Energie/Drive.",
        "steer": "Steuerung: Kommunikationsdichte festlegen (z.B. 1–2 feste Sparring-Slots pro Woche)."
    },
    "MOR": {
        "what": "Wie stark Werte/Prinzipien deine Entscheidungskraft stabilisieren.",
        "top": "Wenn Entscheidungen zu deinen Werten passen, wirst du ruhiger, klarer und leistungsstärker.",
        "low": "Wertekonflikte kosten Leistung: innere Unruhe, Grübeln, inkonsistente Entscheidungen.",
        "steer": "Steuerung: 3 Kernwerte + No-Go-Liste definieren, Konflikte früh benennen."
    },
    "IND": {
        "what": "Wie viel Freiheit du brauchst, um maximal zu liefern.",
        "top": "Autonomie erzeugt Performance: du lieferst kreative Lösungen, Eigenständigkeit und hohen Output.",
        "low": "Zu enge Vorgaben drücken Leistung: Passivität, Abwarten oder Dienst-nach-Vorschrift statt Impact.",
        "steer": "Steuerung: Ziel klar, Weg offen – aber Outcomes messbar machen."
    },
    "AKT": {
        "what": "Wie stark Tempo/Umsetzung deine Leistungsfähigkeit treibt.",
        "top": "Du erzeugst Momentum: du kommst ins Tun, triffst Entscheidungen über Handlung und ziehst durch.",
        "low": "Wenn Dynamik fehlt, startest du zu spät: du bleibst zu lange im Kopf und kommst schwer in Umsetzung.",
        "steer": "Steuerung: Timeboxing, Start-Ritual (5 Minuten), kleine erste Schritte statt Perfektion."
    },
    "INF": {
        "what": "Analyse vs. Intuition: wie du über Verständnis Leistung stabilisierst.",
        "top": "Du triffst bessere Entscheidungen, wenn du Zusammenhänge siehst – Stabilität über Klarheit.",
        "low": "Zu wenig Klarheit führt zu Zögern/Fehlgriffen. Risiko: Bauchgefühl ohne Basis oder Overthinking ohne Abschluss.",
        "steer": "Steuerung: 2–3 Pflichtinfos pro Entscheidung, Info-Dosis bewusst begrenzen."
    },
    "COM": {
        "what": "Wie sehr Vergleich/Wettbewerb dich aktiviert.",
        "top": "Benchmarks pushen dich: Standards steigen, Intensität steigt, du gehst in den Leistungsmodus.",
        "low": "Ohne Vergleich fehlt oft Schärfe: Standards werden weicher, weniger Leistungs-Push von außen.",
        "steer": "Steuerung: Referenzsystem (KPIs/Benchmarks) definieren – Vergleich kontrolliert & konstruktiv."
    },
    "AUF": {
        "what": "Wie stark Feedback/Sichtbarkeit deine Leistung stabilisiert.",
        "top": "Rückmeldung stabilisiert dich: du bleibst konsequent, abrufbar, präzise.",
        "low": "Ohne Feedback wirst du unsichtbarer/unklarer. Risiko: Unterkommunikation, weniger Korrektur, weniger Präzision.",
        "steer": "Steuerung: Feedback-Frequenz festlegen (z.B. 1 Review/Woche) und aktiv einfordern."
    },
    "STA": {
        "what": "Wie sehr Rolle/Position Anerkennung Leistung freisetzt.",
        "top": "Klare Rolle/Position erhöht Anspruch, Sicherheit und sichtbaren Abruf von Leistung.",
        "low": "Unklare Rolle erzeugt Reibung: zu wenig Raum, Unsichtbarkeit oder geringerer Abruf von Leistung.",
        "steer": "Steuerung: Rolle definieren, Sichtbarkeit gezielt gestalten (Wirkung, nicht Ego)."
    },
}

TOP_THRESHOLD = 75

TOP_ADDENDUM_HIGH = {
    "STR": "Du hältst Qualität hoch, weil du Entscheidungen über Struktur führst – nicht über Stimmung.",
    "DST": "Wenn es zählt, schaltet dein System auf Klarheit und Handlung – statt auf Zweifel.",
    "STA": "Wenn die Rolle klar ist, nutzt du Präsenz als Leistungstreiber – nicht als Ego-Spiel.",
    "MAC": "Du bringst Dinge ins Ziel, weil du Verantwortung führst, statt auf Richtung zu warten.",
    "KON": "Du wirst stärker durch gezieltes Sparring – Kontakt dient bei dir der Klarheit.",
    "MOR": "Deine innere Linie spart Energie – du wirst klarer, weil du Grenzen kennst.",
    "IND": "Du lieferst am besten, wenn du Spielraum hast, Outcome aber glasklar bleibt.",
    "AKT": "Du erzeugst Output über Momentum – Umsetzung bringt dir Zugriff.",
    "INF": "Du triffst bessere Entscheidungen, weil du Muster erkennst und Zusammenhänge sauber führst.",
    "COM": "Messbarkeit macht dich scharf – solange du Vergleich als Werkzeug steuerst.",
    "AUF": "Feedback wirkt als Verstärker, wenn du Frequenz und Zweck selbst definierst.",
}

TOP_ADDENDUM_MID = {
    "STR": "Dieser Hebel gibt dir Orientierung – er wird stabiler, je klarer du Standards wirklich lebst.",
    "DST": "Leistung unter Druck ist möglich – sie wird verlässlicher, wenn Prioritäten und Reset klar sind.",
    "STA": "Du profitierst von Rollen-Klarheit – die Wirkung hängt spürbar von Kontext und Rahmen ab.",
    "MAC": "Ownership ist da – sie wird stärker, wenn Scope und Entscheidungsspielraum sauber gesetzt sind.",
    "KON": "Austausch hilft – am besten, wenn du ihn dosierst und mit klaren Fragen führst.",
    "MOR": "Werte stabilisieren dich – je klarer deine No-Gos, desto weniger innerer Lärm.",
    "IND": "Freiheit wirkt – sie trägt am meisten, wenn Ziel und Definition von „fertig“ klar sind.",
    "AKT": "Momentum entsteht – es wird konstanter, wenn du Start und Rhythmus bewusst setzt.",
    "INF": "Klarheit kommt über Verständnis – sie bleibt stabil, wenn Analyse in Entscheidung mündet.",
    "COM": "Benchmarks können pushen – sauber wird es, wenn du Vergleich phasenweise steuerst.",
    "AUF": "Feedback kann stärken – wenn du Frequenz, Zweck und Grenzen klar definierst.",
}
