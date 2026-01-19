import sqlite3
from pathlib import Path
import json
from typing import Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "reports.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL
            )
        """)
        con.commit()

def save_report(report_id: str, payload: Dict[str, Any]):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO reports (report_id, payload_json) VALUES (?, ?)",
            (report_id, json.dumps(payload, ensure_ascii=False))
        )
        con.commit()

def load_report(report_id: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT payload_json FROM reports WHERE report_id = ?",
            (report_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row[0])
