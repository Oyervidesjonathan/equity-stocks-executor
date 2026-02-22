from __future__ import annotations

import os

# =========================================================
# ALPACA CREDENTIALS (YOUR STYLE)
# =========================================================

ALPACA_KEY_ID = (
    os.getenv("APCA_API_KEY_ID")
    or os.getenv("ALPACA_API_KEY")
)

ALPACA_SECRET_KEY = (
    os.getenv("APCA_API_SECRET_KEY")
    or os.getenv("ALPACA_SECRET_KEY")
)

if not ALPACA_KEY_ID or not ALPACA_SECRET_KEY:
    raise RuntimeError("❌ Alpaca credentials missing")

# ---------------------------------------------------------
# PAPER / LIVE MODE (LIVE DEFAULT)
# ---------------------------------------------------------

ALPACA_PAPER = os.getenv("ALPACA_PAPER", "false").strip().lower() in (
    "1", "true", "yes", "y"
)

# 🔴 Explicit base URL (live default)
ALPACA_BASE_URL = os.getenv(
    "ALPACA_BASE_URL",
    "https://paper-api.alpaca.markets" if ALPACA_PAPER else "https://api.alpaca.markets",
).rstrip("/")

# ---------------------------------------------------------
# DATA / STREAM
# ---------------------------------------------------------

ALPACA_DATA_URL = os.getenv(
    "ALPACA_DATA_URL",
    "https://data.alpaca.markets",
).rstrip("/")

ALPACA_FEED = (
    os.getenv("APCA_DATA_FEED")
    or os.getenv("ALPACA_FEED")
    or "iex"
)

ALPACA_STREAM_URL = os.getenv(
    "APCA_STREAM_URL",
    "wss://stream.data.alpaca.markets/v2/sip",
)

# ---------------------------------------------------------
# BACKWARD COMPATIBILITY (DO NOT REMOVE)
# ---------------------------------------------------------

ALPACA_API_KEY = ALPACA_KEY_ID
ALPACA_API_SECRET = ALPACA_SECRET_KEY


# =========================================================
# EXECUTOR GUARDS
# =========================================================

MAX_PENNY_POSITIONS = int(os.getenv("MAX_PENNY_POSITIONS", "1"))
MAX_PENNY_TRADES_PER_DAY = int(os.getenv("MAX_PENNY_TRADES_PER_DAY", "1"))

MAX_STOCKS_POSITIONS = int(os.getenv("MAX_STOCKS_POSITIONS", "5"))
MAX_STOCKS_TRADES_PER_DAY = int(os.getenv("MAX_STOCKS_TRADES_PER_DAY", "10"))

ALLOW_MARKET_BRACKET = os.getenv("ALLOW_MARKET_BRACKET", "0").strip().lower() in (
    "1", "true", "yes"
)

POLL_SEC = int(os.getenv("EXECUTOR_POLL_SEC", "5"))
IDLE_HEARTBEAT_SEC = int(os.getenv("EXECUTOR_IDLE_HEARTBEAT_SEC", "30"))
