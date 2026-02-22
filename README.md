# equity-executor

Execution workers that:
- Claim jobs from `job_dispatch`
- Drain `strategy_intents` for a run_id
- Validate strict `planning_context` contract
- Submit orders to Alpaca
- Record dispatch results back to DB

## Required env vars
DATABASE_URL
ALPACA_KEY_ID
ALPACA_SECRET_KEY
ALPACA_PAPER=1|0

## Optional risk/guards
MAX_PENNY_POSITIONS=1
MAX_PENNY_TRADES_PER_DAY=1
MAX_STOCKS_POSITIONS=5
MAX_STOCKS_TRADES_PER_DAY=10

ALLOW_MARKET_BRACKET=0  (default 0: reject market+bracket)
