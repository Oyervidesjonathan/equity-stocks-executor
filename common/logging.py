from __future__ import annotations

import os
import json
from typing import Optional, Dict, Any

import psycopg
from psycopg.types.json import Jsonb


def _get_conn():
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        return psycopg.connect(dsn, autocommit=True)
    except Exception:
        return None


def _safe_json(x: Any) -> Dict[str, Any]:
    try:
        return json.loads(json.dumps(x or {}, default=str))
    except Exception:
        return {}


def log_trade_event(
    *,
    trade_id: Optional[int] = None,
    run_id: Optional[str] = None,
    symbol: str,
    event_type: str,
    source: str,
    reason: Optional[str] = None,
    raw: Optional[dict] = None,
):
    conn = _get_conn()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO trade_events (
                    trade_id, run_id, symbol, event_type, source, reason, raw
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    trade_id,
                    run_id,
                    symbol.upper(),
                    event_type,
                    source,
                    reason,
                    Jsonb(_safe_json(raw)),
                ),
            )
    except Exception:
        pass
    finally:
        conn.close()
