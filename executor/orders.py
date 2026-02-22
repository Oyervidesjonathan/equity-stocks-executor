from __future__ import annotations

from typing import Dict, Any, Tuple, Optional

from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
)

from executor.config import ALLOW_MARKET_BRACKET


def round_price(px: float) -> float:
    px = float(px)
    return round(px, 2) if px >= 1.0 else round(px, 4)


def _nudge_stop_below(entry_px: float, stop_px: float) -> float:
    if stop_px >= entry_px:
        stop_px = entry_px - (0.01 if entry_px >= 1.0 else 0.0001)
    return round_price(stop_px)


def _nudge_tp_above(entry_px: float, tp_px: float) -> float:
    if tp_px <= entry_px:
        tp_px = entry_px + (0.01 if entry_px >= 1.0 else 0.0001)
    return round_price(tp_px)


def build_order_from_planning_context(
    *,
    symbol: str,
    qty: int,
    planning_context: Dict[str, Any],
) -> Tuple[Optional[object], str]:
    """
    Returns: (alpaca_request_object, status)
    status:
      - ok
      - unsupported_market_bracket
      - invalid
    """
    pc = planning_context
    side = (pc["side"] or "").lower()
    entry_type = (pc["entry_type"] or "").lower()
    exit_style = (pc["exit_style"] or "").lower()
    tif = (pc["time_in_force"] or "").lower()

    alpaca_side = OrderSide.BUY if side == "buy" else OrderSide.SELL
    alpaca_tif = TimeInForce.DAY if tif == "day" else TimeInForce.GTC

    # exits
    sl = pc.get("stop_loss")
    tp = pc.get("take_profit")

    # -------------------------
    # Entry: MARKET
    # -------------------------
    if entry_type == "market":
        if exit_style == "none":
            return (
                MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                ),
                "ok",
            )

        if exit_style == "bracket":
            if not ALLOW_MARKET_BRACKET:
                return None, "unsupported_market_bracket"

            # Attempt (only if your Alpaca allows it)
            # Some accounts reject market+bracket; executor will record failure cleanly.
            return (
                MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    order_class=OrderClass.BRACKET,
                    take_profit=TakeProfitRequest(limit_price=round_price(tp)),
                    stop_loss=StopLossRequest(stop_price=round_price(sl)),
                ),
                "ok",
            )

        return None, "invalid"

    # -------------------------
    # Entry: LIMIT
    # -------------------------
    if entry_type == "limit":
        limit_price = pc.get("limit_price")
        if limit_price is None:
            return None, "invalid"

        lp = round_price(limit_price)

        if exit_style == "none":
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

        if exit_style == "bracket":
            entry_px = lp
            sl_px = _nudge_stop_below(entry_px, round_price(sl))
            tp_px = _nudge_tp_above(entry_px, round_price(tp))
            if sl_px >= tp_px:
                tp_px = _nudge_tp_above(sl_px, tp_px)

            return (
                LimitOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=alpaca_side,
                    time_in_force=alpaca_tif,
                    limit_price=entry_px,
                    order_class=OrderClass.BRACKET,
                    take_profit=TakeProfitRequest(limit_price=tp_px),
                    stop_loss=StopLossRequest(stop_price=sl_px),
                ),
                "ok",
            )

        return None, "invalid"

    return None, "invalid"
