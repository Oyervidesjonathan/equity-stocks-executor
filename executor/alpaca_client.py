from __future__ import annotations

from typing import Optional
from alpaca.trading.client import TradingClient

from executor.config import (
    ALPACA_KEY_ID,
    ALPACA_SECRET_KEY,
    ALPACA_BASE_URL,
)

_client: Optional[TradingClient] = None


def get_trading_client() -> TradingClient:
    global _client
    if _client:
        return _client

    _client = TradingClient(
        api_key=ALPACA_KEY_ID,
        secret_key=ALPACA_SECRET_KEY,
        paper=False,  # 🔴 ignored, we use url_override
        url_override=ALPACA_BASE_URL,
    )

    print(f"[EXECUTOR] TradingClient connected to {ALPACA_BASE_URL}", flush=True)

    return _client
