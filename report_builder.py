from dataclasses import dataclass
from pathlib import Path
import json

from report_content import FUNCTION_NAMES, TOP_THRESHOLD, TOP_ADDENDUM_HIGH, TOP_ADDENDUM_MID

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Fallback / Kompatibilität (du kannst langfristig nur FUNCTION_NAMES nutzen)
FUNCTIONS = {
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


@dataclass
class RankedItem:
    fid: str
    name: str
    percent: int
    addendum: str = ""


@dataclass
class ReportResult:
    profile_type: str
    ranked: list          # [(function_id, percent), ...]
    percents: dict        # function_id -> percent
    sums: dict            # function_id -> sum
    avgs: dict            # function_id -> avg
    top_categories: list  # Top-3 Klartext-Namen

    # neu: direkt für PDF/Webreport
    top3: list            # [RankedItem, RankedItem, RankedItem]
    bottom2: list         # [RankedItem, RankedItem]


def _load_questions():
    path = DATA_DIR / "questions.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _top_addendum(fid: str, percent: int) -> str:
    """
    Liefert eine individuelle Zusatzzeile für Top-Hebel.
    HIGH (>= TOP_THRESHOLD) klingt wie stabiler Hebel.
    MID (< TOP_THRESHOLD) klingt wie relativer Top-Hebel ohne falsche Überhöhung.
    """
    if percent >= TOP_THRESHOLD:
        return TOP_ADDENDUM_HIGH.get(fid, "")
    return TOP_ADDENDUM_MID.get(fid, "")


def decide_profile_type(p: dict) -> str:
    # Schwellen: High >= 67, Low <= 33
    def high(fid): return p.get(fid, 0) >= 67
    def low(fid):  return p.get(fid, 0) <= 33

    # A Stabilitätsmodus: STR hoch, MOR hoch, DST nicht extrem niedrig
    if high("STR") and high("MOR") and p.get("DST", 0) >= 40:
        return "A"

    # B Druckmodus: DST hoch, AKT hoch, STR niedrig
    if high("DST") and high("AKT") and low("STR"):
        return "B"

    # C Gestaltungsmodus: IND hoch, INF hoch, STR ok
    if high("IND") and high("INF") and p.get("STR", 0) >= 40:
        return "C"

    # D Vergleichsmodus: COM hoch, AUF hoch, STA hoch
    if high("COM") and high("AUF") and high("STA"):
        return "D"

    # E Kontrollmodus: MAC hoch, STR hoch, INF hoch
    if high("MAC") and high("STR") and high("INF"):
        return "E"

    # Fallback: Top-Treiber
    top = max(p.items(), key=lambda x: x[1])[0]
    if top in ["STR", "MOR"]:
        return "A"
    if top in ["DST", "AKT"]:
        return "B"
    if top in ["IND", "INF"]:
        return "C"
    if top in ["COM", "AUF", "STA"]:
        return "D"
    return "E"


def build_report_data(answers: dict) -> ReportResult:
    questions = _load_questions()

    q_to_fid = {}
    for q in questions:
        qid = q["id"]
        fid = q.get("function_id")
        if not fid:
            raise ValueError(f"Frage {qid} hat keine function_id in questions.json.")
        q_to_fid[qid] = fid

    sums = {fid: 0.0 for fid in FUNCTIONS.keys()}
    counts = {fid: 0 for fid in FUNCTIONS.keys()}

    for qid, val in answers.items():
        fid = q_to_fid.get(qid)
        if not fid or fid not in sums:
            continue
        try:
            v = float(val)
        except Exception:
            v = 0.0
        sums[fid] += v
        counts[fid] += 1

    avgs = {}
    percents = {}
    for fid in FUNCTIONS.keys():
        c = counts[fid] if counts[fid] else 1
        avg = sums[fid] / c
        avgs[fid] = round(avg, 2)
        percents[fid] = int(round((avg / 10.0) * 100))

    ranked = sorted(
        [(fid, percents[fid]) for fid in FUNCTIONS.keys()],
        key=lambda x: x[1],
        reverse=True
    )

    # Top 3 / Bottom 2 als strukturierte Items (für PDF + Webreport)
    top3_pairs = ranked[:3]
    bottom2_pairs = sorted(ranked, key=lambda x: x[1])[:2]

    top3_items = [
        RankedItem(
            fid=fid,
            name=FUNCTION_NAMES.get(fid, FUNCTIONS.get(fid, fid)),
            percent=percent,
            addendum=_top_addendum(fid, percent)
        )
        for fid, percent in top3_pairs
    ]

    bottom2_items = [
        RankedItem(
            fid=fid,
            name=FUNCTION_NAMES.get(fid, FUNCTIONS.get(fid, fid)),
            percent=percent,
            addendum=""
        )
        for fid, percent in bottom2_pairs
    ]

    top_categories = [item.name for item in top3_items]
    profile_type = decide_profile_type(percents)

    return ReportResult(
        profile_type=profile_type,
        ranked=ranked,
        percents=percents,
        sums=sums,
        avgs=avgs,
        top_categories=top_categories,
        top3=top3_items,
        bottom2=bottom2_items
    )
