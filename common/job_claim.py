from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from common.db import get_conn


def _row_get(row: Any, key: str, idx: int):
    # psycopg dict_row returns a dict-like; normal cursor returns tuple
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    try:
        return row[idx]
    except Exception:
        return None


def claim_job(*, job_types: List[str], claimed_by: str) -> Optional[Dict[str, Any]]:
    if not job_types:
        return None

    now = datetime.now(timezone.utc).isoformat()

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                WITH candidate AS (
                    SELECT dispatch_id
                    FROM job_dispatch
                    WHERE status = 'queued'
                      AND allowed = true
                      AND job_type = ANY(%s::text[])
                    ORDER BY ts ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE job_dispatch
                SET
                    status = 'running',
                    payload = COALESCE(payload,'{}'::jsonb)
                              || %s::jsonb
                WHERE dispatch_id IN (SELECT dispatch_id FROM candidate)
                RETURNING
                    dispatch_id,
                    job_type,
                    run_id,
                    payload
                """,
                (
                    job_types,
                    Jsonb({"claimed_at": now, "claimed_by": claimed_by}),
                ),
            )
            row = cur.fetchone()
            if not row:
                return None

            dispatch_id = _row_get(row, "dispatch_id", 0)
            job_type = _row_get(row, "job_type", 1)
            run_id = _row_get(row, "run_id", 2)
            payload = _row_get(row, "payload", 3)

            return {
                "dispatch_id": str(dispatch_id) if dispatch_id else None,
                "job_type": str(job_type) if job_type else None,
                "run_id": str(run_id) if run_id else None,
                "payload": payload or {},
            }

    except Exception as e:
        print(f"[JOB_CLAIM] claim failed err={e}", flush=True)
        return None


def mark_done(dispatch_id: str, *, extra: Optional[dict] = None) -> None:
    if not dispatch_id or dispatch_id in ("dispatch_id",):
        print(f"[JOB_CLAIM] mark_done invalid dispatch_id={dispatch_id}", flush=True)
        return

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_dispatch
                SET
                    status = 'done',
                    payload = COALESCE(payload,'{}'::jsonb)
                              || %s::jsonb
                WHERE dispatch_id = %s::uuid
                """,
                (
                    Jsonb(
                        {
                            "done_at": datetime.now(timezone.utc).isoformat(),
                            **(extra or {}),
                        }
                    ),
                    dispatch_id,
                ),
            )
    except Exception as e:
        print(f"[JOB_CLAIM] mark_done failed dispatch_id={dispatch_id} err={e}", flush=True)


def mark_error(dispatch_id: str, error: str, *, extra: Optional[dict] = None) -> None:
    if not dispatch_id or dispatch_id in ("dispatch_id",):
        print(f"[JOB_CLAIM] mark_error invalid dispatch_id={dispatch_id}", flush=True)
        return

    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE job_dispatch
                SET
                    status = 'error',
                    payload = COALESCE(payload,'{}'::jsonb)
                              || %s::jsonb
                WHERE dispatch_id = %s::uuid
                """,
                (
                    Jsonb(
                        {
                            "error_at": datetime.now(timezone.utc).isoformat(),
                            "error": str(error)[:500],
                            **(extra or {}),
                        }
                    ),
                    dispatch_id,
                ),
            )
    except Exception as e:
        print(f"[JOB_CLAIM] mark_error failed dispatch_id={dispatch_id} err={e}", flush=True)
