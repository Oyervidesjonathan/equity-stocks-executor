from __future__ import annotations

from typing import Dict, Any

from executor.alpaca_client import get_trading_client
from executor.validate import validate_planning_context
from executor.guards import (
    count_open_positions,
    has_open_position,
    has_open_buy_order,
    count_filled_buys_today_utc,
)
from executor.orders import build_order_from_planning_context
from executor.config import MAX_PENNY_POSITIONS, MAX_PENNY_TRADES_PER_DAY
from common.logging import log_trade_event


def execute_penny_intent(*, run_id: str, intent: dict) -> Dict[str, Any]:
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
    if MAX_PENNY_TRADES_PER_DAY > 0:
        buys_today = count_filled_buys_today_utc(client)
        if buys_today >= MAX_PENNY_TRADES_PER_DAY:
            return {"ok": False, "reason": "max_trades_per_day_reached", "buys_today": buys_today}

    open_pos = count_open_positions(client)
    if open_pos >= MAX_PENNY_POSITIONS:
        return {"ok": False, "reason": "max_positions_reached", "open_positions": open_pos}

    if has_open_position(client, symbol):
        return {"ok": False, "reason": "skip_already_in_position"}

    if has_open_buy_order(client, symbol):
        return {"ok": False, "reason": "skip_open_buy_order"}

    qty = pc.get("qty")
    if qty is None:
        return {"ok": False, "reason": "missing_qty_strict"}  # strict: no guessing
    qty = int(qty)

    req, status = build_order_from_planning_context(symbol=symbol, qty=qty, planning_context=pc)
    if status != "ok" or req is None:
        return {"ok": False, "reason": status}

    try:
        order = client.submit_order(req)
        alp_id = str(getattr(order, "id", "") or "")

        log_trade_event(
            run_id=run_id,
            symbol=symbol,
            event_type="ENTRY_SUBMITTED",
            source="executor_penny",
            reason="alpaca_submit_order",
            raw={"intent_id": intent_id, "strategy": strategy, "alpaca_order_id": alp_id, "planning_context": pc},
        )

        return {"ok": True, "alpaca_order_id": alp_id, "status": str(getattr(order, "status", ""))}
    except Exception as e:
        return {"ok": False, "reason": "submit_error", "error": str(e)[:300]}
