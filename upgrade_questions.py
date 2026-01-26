import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SRC = DATA_DIR / "questions.json"
OUT = DATA_DIR / "questions_upgraded.json"

CAT_TO_ID = {
  "Druck und Stress": "DST",
  "Struktur": "STR",
  "Macht": "MAC",
  "Kontakt": "KON",
  "Moral": "MOR",
  "Individualität": "IND",
  "Aktivität": "AKT",
  "Information": "INF",
  "Competition": "COM",
  "Aufmerksamkeit": "AUF",
  "Status": "STA",
}

ID_TO_NAME = {
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

data = json.loads(SRC.read_text(encoding="utf-8"))

upgraded = []
missing = []
for q in data:
  cat = q.get("category", "").strip()
  fid = CAT_TO_ID.get(cat)
  if not fid:
    missing.append({"id": q.get("id"), "category": cat})
    fid = "UNK"
  q2 = dict(q)
  q2["function_id"] = fid
  q2["function_name"] = ID_TO_NAME.get(fid, cat or "Unbekannt")
  upgraded.append(q2)

OUT.write_text(json.dumps(upgraded, ensure_ascii=False, indent=2), encoding="utf-8")

print("✅ Fertig.")
print("Output:", OUT)
if missing:
  print("⚠️ Fehlende Kategorien:", missing)