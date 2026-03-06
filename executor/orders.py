from __future__ import annotations

from typing import Dict, Any, Tuple, Optional

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopLimitOrderRequest,
)


def round_price(px: float) -> float:
    px = float(px)
    return round(px, 2) if px >= 1.0 else round(px, 4)


def build_order_from_planning_context(
    *,
    symbol: str,
    qty: int,
    planning_context: Dict[str, Any],
) -> Tuple[Optional[object], str]:

    pc = planning_context

    side = (pc.get("side") or "").lower()
    entry_type = (pc.get("entry_type") or pc.get("entry") or "").lower()
    tif = (pc.get("time_in_force") or "day").lower()

    if side not in ("buy", "sell"):
        return None, "invalid_side"

    alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
    alpaca_tif = TimeInForce.DAY if tif == "day" else TimeInForce.GTC

    # --------------------------------------------------
    # MARKET ENTRY
    # --------------------------------------------------

    if entry_type == "market":
        return (
            MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=alpaca_side,
                time_in_force=alpaca_tif,
            ),
            "ok",
        )

    # --------------------------------------------------
    # LIMIT ENTRY
    # --------------------------------------------------

    if entry_type == "limit":

        limit_price = pc.get("limit_price")
        if limit_price is None:
            return None, "missing_limit_price"

        lp = round_price(limit_price)

        return (
            LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                limit_price=lp,
            ),
            "ok",
        )

    # --------------------------------------------------
    # STOP-LIMIT BREAKOUT ENTRY
    # --------------------------------------------------

    if entry_type == "stop_limit":

        stop_price = pc.get("stop_price")
        limit_price = pc.get("limit_price")

        if stop_price is None or limit_price is None:
            return None, "missing_stop_limit_price"

        sp = round_price(stop_price)
        lp = round_price(limit_price)

        return (
            StopLimitOrderRequest(
                symbol=symbol,
                qty=qty,
                side=alpaca_side,
                time_in_force=alpaca_tif,
                stop_price=sp,
                limit_price=lp,
            ),
            "ok",
        )

    return None, "invalid_entry_type"
