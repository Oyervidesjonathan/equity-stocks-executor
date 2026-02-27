from __future__ import annotations

from typing import Dict, Any
import math

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
    pc = source_facts.get("planning_context") or {}

    conviction = source_facts.get("conviction", "unknown")
    run_position_cap = source_facts.get("run_position_cap")

    ok, why = validate_planning_context(pc)
    if not ok:
        return {"ok": False, "reason": why}

    # ------------------------------------------------------
    # DAILY TRADE GUARD
    # ------------------------------------------------------

    if MAX_PENNY_TRADES_PER_DAY > 0:
        buys_today = count_filled_buys_today_utc(client)
        if buys_today >= MAX_PENNY_TRADES_PER_DAY:
            return {
                "ok": False,
                "reason": "max_trades_per_day_reached",
                "buys_today": buys_today,
            }

    # ------------------------------------------------------
    # POSITION CAP (PLANNER-AWARE)
    # ------------------------------------------------------

    open_pos = count_open_positions(client)

    effective_cap = MAX_PENNY_POSITIONS
    if isinstance(run_position_cap, int) and run_position_cap > 0:
        effective_cap = min(effective_cap, run_position_cap)

    if open_pos >= effective_cap:
        return {
            "ok": False,
            "reason": "max_positions_reached",
            "open_positions": open_pos,
            "cap": effective_cap,
        }

    if has_open_position(client, symbol):
        return {"ok": False, "reason": "skip_already_in_position"}

    if has_open_buy_order(client, symbol):
        return {"ok": False, "reason": "skip_open_buy_order"}

    # ------------------------------------------------------
    # POSITION SIZING (CONVICTION-AWARE)
    # ------------------------------------------------------

    qty = pc.get("qty")

    if qty is None:
        # Auto-size using max_notional_usd and entry_price_hint
        max_notional = pc.get("max_notional_usd")
        entry_hint = (pc.get("meta") or {}).get("entry_price_hint")

        if not max_notional or not entry_hint:
            return {"ok": False, "reason": "missing_qty_and_sizing_inputs"}

        try:
            qty = math.floor(float(max_notional) / float(entry_hint))
        except Exception:
            return {"ok": False, "reason": "sizing_error"}

        if qty <= 0:
            return {"ok": False, "reason": "qty_zero_after_sizing"}

    try:
        qty = int(qty)
    except Exception:
        return {"ok": False, "reason": "invalid_qty"}

    # ------------------------------------------------------
    # BUILD ORDER
    # ------------------------------------------------------

    req, status = build_order_from_planning_context(
        symbol=symbol,
        qty=qty,
        planning_context=pc,
    )

    if status != "ok" or req is None:
        return {"ok": False, "reason": status}

    # ------------------------------------------------------
    # SUBMIT ORDER
    # ------------------------------------------------------

    try:
        order = client.submit_order(req)
        alp_id = str(getattr(order, "id", "") or "")

        log_trade_event(
            run_id=run_id,
            symbol=symbol,
            event_type="ENTRY_SUBMITTED",
            source="executor_penny",
            reason="alpaca_submit_order",
            raw={
                "intent_id": intent_id,
                "strategy": strategy,
                "conviction": conviction,
                "alpaca_order_id": alp_id,
                "qty": qty,
                "planning_context": pc,
            },
        )

        return {
            "ok": True,
            "alpaca_order_id": alp_id,
            "status": str(getattr(order, "status", "")),
            "qty": qty,
            "conviction": conviction,
        }

    except Exception as e:
        return {
            "ok": False,
            "reason": "submit_error",
            "error": str(e)[:300],
        }
