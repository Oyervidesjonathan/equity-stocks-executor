from __future__ import annotations

from typing import Dict, Any, Tuple, Optional

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
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
    """
    ENTRY-ONLY BUILDER.
    Watcher attaches exits.
    Executor NEVER sends bracket/oco orders.
    """

    pc = planning_context
    side = (pc.get("side") or "").lower()
    entry_type = (pc.get("entry_type") or "").lower()
    tif = (pc.get("time_in_force") or "").lower()

    if side not in ("buy", "sell"):
        return None, "invalid_side"

    alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
    alpaca_tif = TimeInForce.DAY if tif == "day" else TimeInForce.GTC

    # --------------------------------------------------
    # ENTRY: MARKET (NO BRACKET ALLOWED)
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
    # ENTRY: LIMIT (NO BRACKET ALLOWED)
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

    return None, "invalid_entry_type"
