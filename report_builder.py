# report_builder.py
# ============================================================
# Auswertungslogik: Berechnet Ergebnis aus Antworten
# Importiert alle Texte/Namen aus report_content.py
# ============================================================

from dataclasses import dataclass
from pathlib import Path
import json

from report_content import FUNCTION_NAMES, FUNCTION_ORDER

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


@dataclass
class ReportResult:
    profile_type: str
    ranked: list          # [(function_id, percent), ...]
    percents: dict        # function_id -> percent
    sums: dict            # function_id -> sum
    avgs: dict            # function_id -> avg
    top_categories: list  # Top-3 Klartext-Namen


def _load_questions():
    path = DATA_DIR / "questions.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def decide_profile_type(p: dict) -> str:
    """
    Gewichtetes Scoring statt harter Schwellen.
    Berechnet für jeden der 5 Typen einen Score.
    Der höchste Score gewinnt.
    """
    scores = {
        # A Stabilitätsmodus: STR + MOR stark, wenig AKT
        "A": 0.40 * p.get("STR", 0) + 0.40 * p.get("MOR", 0) + 0.20 * (100 - p.get("AKT", 0)),

        # B Druckmodus: DST + AKT stark, wenig STR
        "B": 0.40 * p.get("DST", 0) + 0.30 * p.get("AKT", 0) + 0.30 * (100 - p.get("STR", 0)),

        # C Gestaltungsmodus: IND + INF stark, mittlere STR
        "C": 0.40 * p.get("IND", 0) + 0.35 * p.get("INF", 0) + 0.25 * (100 - p.get("STR", 0)),

        # D Vergleichsmodus: COM + AUF + STA stark
        "D": 0.35 * p.get("COM", 0) + 0.35 * p.get("AUF", 0) + 0.30 * p.get("STA", 0),

        # E Kontrollmodus: MAC + STR + INF stark
        "E": 0.40 * p.get("MAC", 0) + 0.30 * p.get("STR", 0) + 0.30 * p.get("INF", 0),
    }

    return max(scores, key=scores.get)


def build_report_data(answers: dict) -> ReportResult:
    questions = _load_questions()

    q_to_fid = {}
    for q in questions:
        qid = q["id"]
        fid = q.get("function_id")
        if not fid:
            raise ValueError(f"Frage {qid} hat keine function_id in questions.json.")
        q_to_fid[qid] = fid

    sums = {fid: 0.0 for fid in FUNCTION_NAMES.keys()}
    counts = {fid: 0 for fid in FUNCTION_NAMES.keys()}

    for qid, val in answers.items():
        fid = q_to_fid.get(qid)
        if not fid or fid not in sums:
            continue
        try:
            v = float(val)
        except:
            v = 0.0
        sums[fid] += v
        counts[fid] += 1

    avgs = {}
    percents = {}
    for fid in FUNCTION_NAMES.keys():
        c = counts[fid] if counts[fid] else 1
        avg = sums[fid] / c
        avgs[fid] = round(avg, 2)
        percents[fid] = int(round((avg / 10.0) * 100))

    ranked = sorted(
        [(fid, percents[fid]) for fid in FUNCTION_NAMES.keys()],
        key=lambda x: x[1],
        reverse=True
    )
    top_categories = [FUNCTION_NAMES[fid] for fid, _ in ranked[:3]]
    profile_type = decide_profile_type(percents)

    return ReportResult(
        profile_type=profile_type,
        ranked=ranked,
        percents=percents,
        sums=sums,
        avgs=avgs,
        top_categories=top_categories
    )
