from __future__ import annotations

import time
import traceback

from common.job_claim import claim_job, mark_done, mark_error
from executor.intents import claim_next_intent, set_intent_result
from executor.handlers.stocks import execute_stocks_intent
from executor.config import POLL_SEC, IDLE_HEARTBEAT_SEC
from executor.alpaca_client import get_trading_client


WORKER = "executor-stocks"
JOB_TYPES = ["stocks"]


def main():
    print("🚀 equity-executor (stocks) started", flush=True)

    # ---------------------------------------------------------
    # LIVE ACCOUNT CHECK (CRITICAL)
    # ---------------------------------------------------------
    try:
        client = get_trading_client()
        acct = client.get_account()

        print(
            f"[EXECUTOR] CONNECTED | STATUS={acct.status} "
            f"buying_power={acct.buying_power}",
            flush=True,
        )
    except Exception as e:
        print(f"[EXECUTOR] ❌ Failed to connect to Alpaca: {e}", flush=True)
        raise

    last_idle = 0.0

    while True:
        job = claim_job(job_types=JOB_TYPES, claimed_by=WORKER)

        # ---------------------------------------------------------
        # IDLE LOOP
        # ---------------------------------------------------------
        if not job:
            if time.time() - last_idle > IDLE_HEARTBEAT_SEC:
                print("[EXECUTOR-STOCKS][IDLE] polling…", flush=True)
                last_idle = time.time()

            time.sleep(POLL_SEC)
            continue

        dispatch_id = job["dispatch_id"]
        payload = job.get("payload") or {}
        run_id = job.get("run_id") or payload.get("run_id")

        if not run_id:
            mark_done(dispatch_id, extra={"skipped": "missing_run_id"})
            continue

        executed = 0
        failed = 0

        print(
            f"[EXECUTOR-STOCKS] START dispatch_id={dispatch_id} run_id={run_id}",
            flush=True,
        )

        try:
            # ---------------------------------------------------------
            # DRAIN INTENTS FOR THIS RUN
            # ---------------------------------------------------------
            while True:
                intent = claim_next_intent(
                    run_id=str(run_id),
                    executor="stocks",
                )

                if not intent:
                    break

                intent_id = str(intent["intent_id"])
                symbol = intent.get("symbol")

                print(
                    f"[EXECUTOR-STOCKS] intent_claimed "
                    f"intent_id={intent_id} symbol={symbol}",
                    flush=True,
                )

                try:
                    res = execute_stocks_intent(
                        run_id=str(run_id),
                        intent=intent,
                    )

                    set_intent_result(
                        intent_id=intent_id,
                        ok=bool(res.get("ok")),
                        detail=res,
                    )

                    if res.get("ok"):
                        executed += 1
                        print(
                            f"[EXECUTOR-STOCKS] SUCCESS "
                            f"symbol={symbol} detail={res}",
                            flush=True,
                        )
                    else:
                        failed += 1
                        print(
                            f"[EXECUTOR-STOCKS] FAIL "
                            f"symbol={symbol} reason={res.get('reason')}",
                            flush=True,
                        )

                except Exception as e:
                    failed += 1
                    traceback.print_exc()

                    set_intent_result(
                        intent_id=intent_id,
                        ok=False,
                        detail={
                            "ok": False,
                            "reason": "handler_crash",
                            "error": str(e)[:300],
                        },
                    )

            # ---------------------------------------------------------
            # JOB COMPLETE
            # ---------------------------------------------------------
            mark_done(
                dispatch_id,
                extra={
                    "run_id": str(run_id),
                    "executed": executed,
                    "failed": failed,
                },
            )

            print(
                f"[EXECUTOR-STOCKS] DONE dispatch_id={dispatch_id} "
                f"executed={executed} failed={failed}",
                flush=True,
            )

        except Exception as e:
            traceback.print_exc()
            mark_error(
                dispatch_id,
                str(e),
                extra={"run_id": str(run_id)},
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
