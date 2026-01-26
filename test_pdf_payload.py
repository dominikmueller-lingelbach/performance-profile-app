# test_pdf_payload.py
from pathlib import Path

# ✅ 1) HIER anpassen:
# Wenn deine Funktion in "pdf_report.py" liegt, passt das so:
from pdf_report import build_pdf_report

def make_payload(ranked):
    return {
        "name": "TEST USER",
        "email": "test@performanceprofil.de",
        "profile_type": "A",
        "ranked": ranked,  # <- hier kommen deine Prozentwerte rein
    }

def write_pdf(filename: str, payload: dict):
    pdf_bytes = build_pdf_report(payload)
    Path(filename).write_bytes(pdf_bytes)
    print(f"✅ PDF geschrieben: {filename}")

if __name__ == "__main__":
    # =========================
    # EDGE-CASE TESTS
    # =========================

    tests = [
        ("edge_24.pdf", make_payload([
            ("DST", 24), ("STR", 80), ("MAC", 60), ("KON", 55), ("MOR", 50),
            ("IND", 45), ("AKT", 40), ("INF", 35), ("COM", 30), ("AUF", 25), ("STA", 75)
        ])),
        ("edge_25.pdf", make_payload([
            ("DST", 25), ("STR", 80), ("MAC", 60), ("KON", 55), ("MOR", 50),
            ("IND", 45), ("AKT", 40), ("INF", 35), ("COM", 30), ("AUF", 25), ("STA", 75)
        ])),
        ("edge_74.pdf", make_payload([
            ("DST", 74), ("STR", 80), ("MAC", 60), ("KON", 55), ("MOR", 50),
            ("IND", 45), ("AKT", 40), ("INF", 35), ("COM", 30), ("AUF", 25), ("STA", 75)
        ])),
        ("edge_75.pdf", make_payload([
            ("DST", 75), ("STR", 80), ("MAC", 60), ("KON", 55), ("MOR", 50),
            ("IND", 45), ("AKT", 40), ("INF", 35), ("COM", 30), ("AUF", 25), ("STA", 75)
        ])),
    ]

    for filename, payload in tests:
        write_pdf(filename, payload)