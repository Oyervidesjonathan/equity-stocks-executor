from __future__ import annotations

from typing import Dict, Any, Tuple, Optional


def _req_str(pc: dict, k: str) -> Optional[str]:
    v = pc.get(k)
    if v is None:
        return None
    s = str(v).strip().lower()
    return s or None


def validate_planning_context(pc: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Strict validation. Executor will NOT guess.
    """
    if not isinstance(pc, dict):
        return False, "planning_context_not_object"

    side = _req_str(pc, "side")
    if side not in ("buy", "sell"):
        return False, "missing_or_bad_side"

    entry_type = _req_str(pc, "entry_type")
    if entry_type not in ("market", "limit"):
        return False, "missing_or_bad_entry_type"

    tif = _req_str(pc, "time_in_force")
    if tif not in ("day", "gtc"):
        return False, "missing_or_bad_time_in_force"

    exit_style = _req_str(pc, "exit_style")
    if exit_style not in ("none", "oco", "bracket"):
        return False, "missing_or_bad_exit_style"

    if entry_type == "limit":
        if pc.get("limit_price") is None:
            return False, "limit_missing_limit_price"

    if exit_style == "bracket":
        if pc.get("stop_loss") is None or pc.get("take_profit") is None:
            return False, "bracket_missing_sl_tp"

    return True, "ok"
