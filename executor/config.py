from __future__ import annotations

import os

ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID") or os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_PAPER = (os.getenv("ALPACA_PAPER", "1").lower() in ("1", "true", "yes"))

ALLOW_MARKET_BRACKET = (os.getenv("ALLOW_MARKET_BRACKET", "0").lower() in ("1", "true", "yes"))

# Guards
MAX_PENNY_POSITIONS = int(os.getenv("MAX_PENNY_POSITIONS", "1"))
MAX_PENNY_TRADES_PER_DAY = int(os.getenv("MAX_PENNY_TRADES_PER_DAY", "1"))

MAX_STOCKS_POSITIONS = int(os.getenv("MAX_STOCKS_POSITIONS", "5"))
MAX_STOCKS_TRADES_PER_DAY = int(os.getenv("MAX_STOCKS_TRADES_PER_DAY", "10"))

POLL_SEC = int(os.getenv("EXECUTOR_POLL_SEC", "5"))
IDLE_HEARTBEAT_SEC = int(os.getenv("EXECUTOR_IDLE_HEARTBEAT_SEC", "30"))

def require_alpaca():
    if not ALPACA_KEY_ID or not ALPACA_SECRET_KEY:
        raise RuntimeError("Missing Alpaca creds: ALPACA_KEY_ID/ALPACA_SECRET_KEY")
