from __future__ import annotations

from typing import List
from datetime import datetime, timezone, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.requests import GetOrdersRequest


def count_open_positions(client: TradingClient) -> int:
    try:
        positions = client.get_all_positions() or []
        return len([p for p in positions if float(getattr(p, "qty", 0) or 0) != 0])
    except Exception:
        return 0


def has_open_position(client: TradingClient, symbol: str) -> bool:
    try:
        pos = client.get_open_position(symbol)
        return float(getattr(pos, "qty", 0) or 0) != 0
    except Exception:
        return False


def has_open_buy_order(client: TradingClient, symbol: str) -> bool:
    try:
        req = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            symbols=[symbol],
            limit=200,
            nested=True,
        )
        for o in client.get_orders(req) or []:
            if str(getattr(o, "side", "")).lower() == "buy":
                return True
        return False
    except Exception:
        return False


def count_filled_buys_today_utc(client: TradingClient) -> int:
    """
    Simple UTC-day cap (good enough for kill-switch).
    If you want ET-day, we can swap to zoneinfo.
    """
    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    try:
        req = GetOrdersRequest(
            status=QueryOrderStatus.CLOSED,
            limit=500,
            nested=True,
            after=start,
            until=end,
        )
        orders = client.get_orders(req) or []
    except Exception:
        return 0

    cnt = 0
    for o in orders:
        try:
            if str(getattr(o, "side", "")).lower() != "buy":
                continue
            if str(getattr(o, "status", "")).lower() != "filled":
                continue
            filled_at = getattr(o, "filled_at", None)
            if not filled_at:
                continue
            fa = filled_at
            if getattr(fa, "tzinfo", None) is None:
                fa = fa.replace(tzinfo=timezone.utc)
            fa_utc = fa.astimezone(timezone.utc)
            if start <= fa_utc < end:
                cnt += 1
        except Exception:
            continue

    return cnt
