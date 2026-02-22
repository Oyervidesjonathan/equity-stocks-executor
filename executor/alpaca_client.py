from __future__ import annotations

from typing import Optional
from alpaca.trading.client import TradingClient

from executor.config import ALPACA_KEY_ID, ALPACA_SECRET_KEY, ALPACA_PAPER, require_alpaca

_client: Optional[TradingClient] = None

def get_trading_client() -> TradingClient:
    global _client
    if _client:
        return _client

    require_alpaca()

    _client = TradingClient(
        api_key=ALPACA_KEY_ID,
        secret_key=ALPACA_SECRET_KEY,
        paper=ALPACA_PAPER,
    )
    return _client
