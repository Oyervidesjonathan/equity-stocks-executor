from __future__ import annotations

import os

# =========================================================
# 🔴 LIVE-ONLY ALPACA CONFIG
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

# 🔴 HARD LOCK TO LIVE
ALPACA_PAPER = False
ALPACA_BASE_URL = "https://api.alpaca.markets"

# ---------------------------------------------------------
# DATA / STREAM (kept for compatibility)
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

MAX_STOCKS_POSITIONS = int(os.getenv("MAX_STOCKS_POSITIONS", "5"))
MAX_STOCKS_TRADES_PER_DAY = int(os.getenv("MAX_STOCKS_TRADES_PER_DAY", "10"))

ALLOW_MARKET_BRACKET = os.getenv("ALLOW_MARKET_BRACKET", "0").strip().lower() in (
    "1", "true", "yes"
)

POLL_SEC = int(os.getenv("EXECUTOR_POLL_SEC", "5"))
IDLE_HEARTBEAT_SEC = int(os.getenv("EXECUTOR_IDLE_HEARTBEAT_SEC", "30"))

print(f"[CONFIG] 🔴 LIVE MODE LOCKED → {ALPACA_BASE_URL}", flush=True)
