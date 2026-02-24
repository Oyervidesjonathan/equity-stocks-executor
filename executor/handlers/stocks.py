from __future__ import annotations

from typing import Dict, Any
from datetime import datetime, timezone

from psycopg.types.json import Jsonb

from executor.alpaca_client import get_trading_client
from executor.validate import validate_planning_context
from executor.guards import (
    count_open_positions,
    has_open_position,
    has_open_buy_order,
    count_filled_buys_today_utc,
)
from executor.orders import build_order_from_planning_context
from executor.config import MAX_STOCKS_POSITIONS, MAX_STOCKS_TRADES_PER_DAY
from common.logging import log_trade_event
from common.db import get_shared_conn


def _to_float(x, default=None):
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _insert_trade_open(
    *,
    run_id: str,
    symbol: str,
    strategy: str,
    qty: float,
    entry_price_hint: float | None,
    opened_by: str,
    intent_id: str,
    alpaca_order_id: str,
    planning_context: dict,
    extra_meta: dict | None = None,
) -> int | None:
    """
    Insert an OPEN trade row so DB stays authoritative.

    Idempotency:
      - If an OPEN trade already exists for this symbol, do nothing.
      - If an OPEN trade already exists for this alpaca_order_id, do nothing.
    """
    try:
        with get_shared_conn() as conn, conn.cursor() as cur:
            # If we already have an OPEN trade for this symbol, don't insert another
            cur.execute(
                """
                SELECT id
                FROM trades
                WHERE LOWER(status)='open'
                  AND symbol=%s
                ORDER BY entry_time DESC NULLS LAST, id DESC
                LIMIT 1
                """,
                (symbol,),
            )
            row = cur.fetchone()
            if row:
                return int(row[0])

            # If we already inserted by alpaca order id, don't insert again
            if alpaca_order_id:
                cur.execute(
                    """
                    SELECT id
                    FROM trades
                    WHERE metadata->>'alpaca_order_id' = %s
                    ORDER BY entry_time DESC NULLS LAST, id DESC
                    LIMIT 1
                    """,
                    (alpaca_order_id,),
                )
                row2 = cur.fetchone()
                if row2:
                    return int(row2[0])

            meta = {
                "intent_id": intent_id,
                "alpaca_order_id": alpaca_order_id,
                "planning_context": planning_context or {},
            }
            if extra_meta:
                meta.update(extra_meta)

            cur.execute(
                """
                INSERT INTO trades (
                    run_id,
                    symbol,
                    strategy,
                    side,
                    qty,
                    entry_price,
                    entry_time,
                    status,
                    opened_by,
                    metadata
                )
                VALUES (
                    %s::uuid,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'OPEN',
                    %s,
                    %s::jsonb
                )
                RETURNING id
                """,
                (
                    run_id,
                    symbol,
                    strategy,
                    "buy",
                    float(qty),
                    _to_float(entry_price_hint, None),
                    datetime.now(timezone.utc),
                    opened_by,
                    Jsonb(meta),
                ),
            )
            new_id = cur.fetchone()
            return int(new_id[0]) if new_id else None
    except Exception:
        # Never fail the executor because DB insert failed; but we WANT to see it in logs.
        return None


def execute_stocks_intent(*, run_id: str, intent: dict) -> Dict[str, Any]:
    client = get_trading_client()

    intent_id = str(intent["intent_id"])
    symbol = str(intent["symbol"]).upper().strip()
    strategy = intent.get("strategy") or "unknown"

    source_facts = intent.get("source_facts") or {}
    pc = source_facts.get("planning_context")

    ok, why = validate_planning_context(pc or {})
    if not ok:
        return {"ok": False, "reason": why}

    # Guards
    if MAX_STOCKS_TRADES_PER_DAY > 0:
        buys_today = count_filled_buys_today_utc(client)
        if buys_today >= MAX_STOCKS_TRADES_PER_DAY:
            return {
                "ok": False,
                "reason": "max_trades_per_day_reached",
                "buys_today": buys_today,
            }

    open_pos = count_open_positions(client)
    if open_pos >= MAX_STOCKS_POSITIONS:
        return {"ok": False, "reason": "max_positions_reached", "open_positions": open_pos}

    if has_open_position(client, symbol):
        return {"ok": False, "reason": "skip_already_in_position"}

    if has_open_buy_order(client, symbol):
        return {"ok": False, "reason": "skip_open_buy_order"}

    qty = pc.get("qty")
    if qty is None:
        return {"ok": False, "reason": "missing_qty_strict"}  # strict
    qty = int(qty)

    req, status = build_order_from_planning_context(symbol=symbol, qty=qty, planning_context=pc)
    if status != "ok" or req is None:
        return {"ok": False, "reason": status}

    try:
        order = client.submit_order(req)
        alp_id = str(getattr(order, "id", "") or "")
        alp_status = str(getattr(order, "status", "") or "")

        # -----------------------------
        # ✅ DB-TRUTH: insert OPEN trade
        # -----------------------------
        entry_price_hint = None
        try:
            meta = (pc or {}).get("meta") or {}
            entry_price_hint = meta.get("entry_price_hint")
        except Exception:
            entry_price_hint = None

        trade_id = _insert_trade_open(
            run_id=str(run_id),
            symbol=symbol,
            strategy=strategy,
            qty=qty,
            entry_price_hint=_to_float(entry_price_hint, None),
            opened_by="executor_stocks",
            intent_id=intent_id,
            alpaca_order_id=alp_id,
            planning_context=pc or {},
            extra_meta={
                "alpaca_status": alp_status,
                "executor": "stocks",
            },
        )

        # Keep your existing event log
        log_trade_event(
            run_id=run_id,
            symbol=symbol,
            event_type="ENTRY_SUBMITTED",
            source="executor_stocks",
            reason="alpaca_submit_order",
            raw={
                "intent_id": intent_id,
                "strategy": strategy,
                "alpaca_order_id": alp_id,
                "alpaca_status": alp_status,
                "trade_id": trade_id,
                "planning_context": pc,
            },
        )

        return {
            "ok": True,
            "alpaca_order_id": alp_id,
            "status": alp_status,
            "trade_id": trade_id,
        }

    except Exception as e:
        return {"ok": False, "reason": "submit_error", "error": str(e)[:300]}
