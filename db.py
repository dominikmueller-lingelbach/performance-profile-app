# db.py
# ============================================================
# Datenbank: PostgreSQL via Supabase (persistent)
# Fallback auf SQLite für lokale Entwicklung
# ============================================================

import os
import json
from typing import Dict, Any, Optional

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # ============================================================
    # POSTGRESQL (Produktion auf Render + Supabase)
    # ============================================================
    import psycopg2
    from psycopg2.extras import RealDictCursor

    def _get_conn():
        return psycopg2.connect(DATABASE_URL)

    def init_db():
        with _get_conn() as con:
            with con.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        report_id TEXT PRIMARY KEY,
                        payload_json TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            con.commit()

    def save_report(report_id: str, payload: Dict[str, Any]):
        with _get_conn() as con:
            with con.cursor() as cur:
                cur.execute(
                    """INSERT INTO reports (report_id, payload_json)
                       VALUES (%s, %s)
                       ON CONFLICT (report_id)
                       DO UPDATE SET payload_json = EXCLUDED.payload_json""",
                    (report_id, json.dumps(payload, ensure_ascii=False))
                )
            con.commit()

    def load_report(report_id: str) -> Optional[Dict[str, Any]]:
        with _get_conn() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT payload_json FROM reports WHERE report_id = %s",
                    (report_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                return json.loads(row[0])

else:
    # ============================================================
    # SQLITE (Fallback fuer lokale Entwicklung)
    # ============================================================
    import sqlite3
    from pathlib import Path

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
