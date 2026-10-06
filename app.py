from typing import List, Dict, Any
from pathlib import Path
import json
import re
import hmac
from uuid import uuid4, uuid5, NAMESPACE_URL
import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from report_builder import build_report_data
from pdf_report import build_pdf_report
from db import init_db, save_report, load_report
from report_content import FUNCTION_NAMES, TYPE_MAP, MEANING_CARDS

# ============================================================
# ENV
# ============================================================
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_LIST_ID = int(os.getenv("BREVO_LIST_ID", "3"))
PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

# ============================================================
# ZUGANGSSCHUTZ
# ACCESS_GATE=on  -> Test nur nach Kauf (Stripe) oder mit Zugangscode
# ACCESS_GATE=off -> Test frei aufrufbar (Standard, bisheriges Verhalten)
# ============================================================
ACCESS_GATE = os.getenv("ACCESS_GATE", "off").strip().lower() in ("on", "1", "true", "yes")
STRIPE_SECRET_KEY = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
ACCESS_CODES = [
    c.strip().lower()
    for c in (os.getenv("ACCESS_CODES") or "").split(",")
    if c.strip()
]
BUY_URL = (os.getenv("BUY_URL") or "https://performanceprofil.de").strip()
SESSION_RE = re.compile(r"^cs_(live|test)_[A-Za-z0-9]{10,200}$")

# ============================================================
# PATHS / APP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()
init_db()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ============================================================
# Content-Paket für das Frontend (wird als JSON injiziert)
# Single Source of Truth: alles aus report_content.py
# ============================================================
FRONTEND_CONTENT = {
    "function_names": FUNCTION_NAMES,
    "type_map": TYPE_MAP,
    "meaning_cards": MEANING_CARDS,
}

# ============================================================
# HELPERS
# ============================================================
def load_questions() -> List[Dict[str, Any]]:
    path = DATA_DIR / "questions.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def code_is_valid(code: str) -> bool:
    c = (code or "").strip().lower()
    if not c:
        return False
    return any(hmac.compare_digest(c.encode("utf-8"), k.encode("utf-8")) for k in ACCESS_CODES)


def verify_stripe_session(session_id: str):
    """
    Prueft bei Stripe, ob der Kauf abgeschlossen ist.
    Rueckgabe: ("ok", {"email": ..., "name": ...}) | ("invalid", None) | ("error", None)
    """
    sid = (session_id or "").strip()
    if not SESSION_RE.match(sid):
        return "invalid", None
    if not STRIPE_SECRET_KEY:
        print("STRIPE: kein STRIPE_SECRET_KEY gesetzt")
        return "error", None
    try:
        r = requests.get(
            "https://api.stripe.com/v1/checkout/sessions/" + sid,
            headers={"Authorization": "Bearer " + STRIPE_SECRET_KEY},
            timeout=10,
        )
    except Exception as e:
        print("STRIPE exception:", repr(e))
        return "error", None
    if r.status_code == 404:
        return "invalid", None
    if r.status_code != 200:
        # bewusst nur der Statuscode, keine Kundendaten ins Log
        print("STRIPE status:", r.status_code)
        return "error", None
    s = r.json()
    if s.get("status") != "complete":
        return "invalid", None
    if s.get("payment_status") not in ("paid", "no_payment_required"):
        return "invalid", None
    details = s.get("customer_details") or {}
    email = (details.get("email") or s.get("customer_email") or "").strip()
    name = (details.get("name") or "").strip()
    return "ok", {"email": email, "name": name}


def session_report_id(session_id: str) -> str:
    # ein Kauf = genau ein Ergebnis: die Report-ID leitet sich fest aus dem Kauf ab
    return str(uuid5(NAMESPACE_URL, "performance-profil-session:" + session_id.strip()))


def resolve_access(session_id: str, code: str):
    """
    Rueckgabe: (state, access)
    state: "open" (Schutz aus) | "ok" | "invalid" | "error"
    """
    if not ACCESS_GATE:
        return "open", None
    if (session_id or "").strip():
        state, info = verify_stripe_session(session_id)
        if state == "ok":
            return "ok", {
                "kind": "stripe",
                "session_id": session_id.strip(),
                "email": info["email"],
                "name": info["name"],
            }
        if state == "error" and not code_is_valid(code):
            return "error", None
    if code_is_valid(code):
        return "ok", {"kind": "code", "code": code.strip()}
    return "invalid", None


def locked_page(kind: str) -> str:
    if kind == "error":
        title = "Einen Moment bitte"
        text = (
            "Deine Zahlung konnte gerade nicht geprüft werden. "
            "Bitte lade diese Seite in einer Minute neu. Dein Kauf bleibt gültig."
        )
        button = ""
    else:
        title = "Dein Zugang zum Performance Profil"
        text = (
            "Der Test öffnet sich direkt nach dem Kauf. "
            "Du hast bereits gekauft? Dann nutze bitte den Link aus deinem Kauf "
            "oder schreib an info@performanceprofil.de, dann bekommst du deinen Zugang erneut."
        )
        button = '<a class="btn" href="' + BUY_URL + '">Zum Performance Profil</a>'
    return """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Performance Profil</title>
  <style>
    body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial;background:#0b0f14;color:#eaf0f6}
    .wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}
    .card{width:min(620px,100%);background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:18px;padding:30px;box-sizing:border-box}
    .brand{font-weight:700;opacity:.9;margin-bottom:14px}
    h1{font-size:26px;margin:0 0 12px}
    p{opacity:.8;line-height:1.55;margin:0 0 22px}
    .btn{display:inline-block;background:#22c55e;color:#05210f;font-weight:700;text-decoration:none;padding:14px 22px;border-radius:12px}
    .foot{display:flex;gap:18px;flex-wrap:wrap;margin-top:26px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.10);font-size:12.5px;opacity:.75}
    .foot a{color:#eaf0f6;text-decoration:underline}
  </style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="brand">Performance Profil</div>
    <h1>""" + title + """</h1>
    <p>""" + text + """</p>
    """ + button + """
    <div class="foot">
      <a href="https://performanceprofil.de/impressum.html" target="_blank" rel="noopener">Impressum</a>
      <a href="https://performanceprofil.de/datenschutz.html" target="_blank" rel="noopener">Datenschutz</a>
    </div>
  </div>
</div>
</body>
</html>"""

# ============================================================
# ROUTES
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    state, access = resolve_access(
        request.query_params.get("session_id", ""),
        request.query_params.get("code", ""),
    )
    if state == "invalid":
        return HTMLResponse(locked_page("invalid"), status_code=403)
    if state == "error":
        return HTMLResponse(locked_page("error"), status_code=503)

    # Kauf wurde schon fuer einen Test genutzt -> direkt zum vorhandenen Ergebnis
    if access and access["kind"] == "stripe":
        existing_id = session_report_id(access["session_id"])
        if load_report(existing_id):
            return RedirectResponse("/r/" + existing_id, status_code=303)

    questions = load_questions()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "questions": questions, "access": access}
    )

@app.get("/r/{report_id}", response_class=HTMLResponse)
async def show_result(request: Request, report_id: str):
    payload = load_report(report_id)
    if not payload:
        return HTMLResponse("Report nicht gefunden.", status_code=404)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "data": payload,
            "content": FRONTEND_CONTENT,
        }
    )

@app.get("/health")
async def health():
    try:
        load_report("ping")
        return JSONResponse({"ok": True, "db": "connected"})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@app.post("/submit")
async def submit(request: Request):
    payload = await request.json()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    answers = payload.get("answers") or {}

    # ================== ZUGANG PRUEFEN ==================
    state, access = resolve_access(
        str(payload.get("session_id") or ""),
        str(payload.get("code") or ""),
    )
    if state == "invalid":
        return JSONResponse(
            {"ok": False, "error": "Kein gültiger Zugang. Bitte öffne den Test über den Link aus deinem Kauf."},
            status_code=403
        )
    if state == "error":
        return JSONResponse(
            {"ok": False, "error": "Deine Zahlung konnte gerade nicht geprüft werden. Bitte versuche es in einer Minute erneut."},
            status_code=503
        )

    if not isinstance(answers, dict) or not answers:
        return JSONResponse(
            {"ok": False, "error": "Keine Antworten erhalten."},
            status_code=400
        )

    report_id = str(uuid4())
    if access and access["kind"] == "stripe":
        # ein Kauf = ein Ergebnis; die E-Mail kommt fest aus dem Kauf
        report_id = session_report_id(access["session_id"])
        existing = load_report(report_id)
        if existing:
            return JSONResponse({
                "ok": True,
                "report_id": report_id,
                "result_url": existing.get("result_url") or f"{PUBLIC_BASE_URL}/r/{report_id}"
            })
        if access["email"]:
            email = access["email"]

    # ================== REPORT BERECHNEN ==================
    result = build_report_data(answers)
    result_url = f"{PUBLIC_BASE_URL}/r/{report_id}"

    # ================== REPORT SPEICHERN ==================
    save_report(report_id, {
        "report_id": report_id,
        "result_url": result_url,
        "name": name,
        "email": email,
        "profile_type": result.profile_type,
        "ranked": result.ranked,
        "percents": result.percents,
        "sums": result.sums,
        "avgs": result.avgs,
    })

    # ================== BREVO KONTAKT ==================
    if BREVO_API_KEY and email:
        brevo_url = "https://api.brevo.com/v3/contacts"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json",
        }
        brevo_payload = {
            "email": email,
            "attributes": {
                "RESULT_URL": result_url,
                "PROFILE_TYPE": result.profile_type,
                "REPORT_ID": report_id
            },
            "listIds": [BREVO_LIST_ID],
            "updateEnabled": True
        }
        try:
            r = requests.post(brevo_url, json=brevo_payload, headers=headers, timeout=10)
            print("BREVO status:", r.status_code)
            print("BREVO response:", r.text)
        except Exception as e:
            print("BREVO exception:", repr(e))
    else:
        print("BREVO nicht ausgeführt (API-Key oder E-Mail fehlt)")

    # ================== RESPONSE ==================
    return JSONResponse({
        "ok": True,
        "report_id": report_id,
        "result_url": result_url
    })

@app.get("/report/{report_id}.pdf")
async def report_pdf(report_id: str):
    payload = load_report(report_id)
    if not payload:
        return JSONResponse(
            {"ok": False, "error": "Report nicht gefunden"},
            status_code=404
        )
    pdf_bytes = build_pdf_report(payload)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="Performance-Profil-Report.pdf"'
        }
    )
