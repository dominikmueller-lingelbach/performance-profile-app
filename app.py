from typing import List, Dict, Any
from pathlib import Path
import json
from uuid import uuid4
import os
import requests

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from report_builder import build_report_data
from pdf_report import build_pdf_report
from db import init_db, save_report, load_report


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
# PATHS / APP
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()
init_db()

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================
# HELPERS
# ============================================================
def load_questions() -> List[Dict[str, Any]]:
    path = DATA_DIR / "questions.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# ROUTES
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    questions = load_questions()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "questions": questions}
    )


@app.get("/r/{report_id}", response_class=HTMLResponse)
async def show_result(request: Request, report_id: str):
    payload = load_report(report_id)
    if not payload:
        return HTMLResponse("Report nicht gefunden.", status_code=404)

    # ✅ Template bekommt ALLES, egal ob es data.*, result.* oder direkte Keys nutzt
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,

            # Falls dein Template "data.xxx" nutzt:
            "data": payload,

            # Falls dein Template "result.xxx" nutzt:
            "result": payload,

            # Falls dein Template direkte Variablen nutzt:
            "report_id": payload.get("report_id"),
            "result_url": payload.get("result_url"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "profile_type": payload.get("profile_type"),
            "ranked": payload.get("ranked"),
            "percents": payload.get("percents"),
            "sums": payload.get("sums"),
            "avgs": payload.get("avgs"),
        }
    )


@app.post("/submit")
async def submit(request: Request):
    payload = await request.json()

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip()
    answers = payload.get("answers") or {}

    if not isinstance(answers, dict) or not answers:
        return JSONResponse(
            {"ok": False, "error": "Keine Antworten erhalten."},
            status_code=400
        )

    # ================== REPORT BERECHNEN ==================
    result = build_report_data(answers)

    report_id = str(uuid4())
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

    # ================== BREVO KONTAKT ERSTELLEN / UPDATEN ==================
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
            r = requests.post(
                brevo_url,
                json=brevo_payload,
                headers=headers,
                timeout=10
            )
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
