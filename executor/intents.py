from __future__ import annotations

import json
from typing import Optional, Dict, Any, Tuple
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from common.db import DATABASE_URL
import psycopg


def _conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)


def claim_next_intent(*, run_id: str, executor: str) -> Optional[dict]:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            WITH picked AS (
                SELECT intent_id
                FROM strategy_intents
                WHERE run_id = %s::uuid
                  AND executor = %s
                  AND dispatched_ts IS NULL
                ORDER BY priority DESC, ts ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            UPDATE strategy_intents si
            SET dispatched_ts = now()
            FROM picked
            WHERE si.intent_id = picked.intent_id
            RETURNING
                si.intent_id,
                si.symbol,
                si.strategy,
                si.priority,
                si.source_facts;
            """,
            (run_id, executor),
        )
        return cur.fetchone()


def set_intent_result(*, intent_id: str, ok: bool, detail: Dict[str, Any]):
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE strategy_intents
            SET
                dispatched_ok = %s::boolean,
                dispatched_detail = %s::text
            WHERE intent_id = %s::uuid;
            """,
            (ok, json.dumps(detail, default=str)[:500], intent_id),
        )
