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
    STRICT ENTRY VALIDATION.
    Executor submits ENTRY ONLY.
    Watcher handles exits.
    """

    if not isinstance(pc, dict):
        return False, "planning_context_not_object"

    # --------------------------------------------------
    # SIDE
    # --------------------------------------------------
    side = _req_str(pc, "side")
    if side not in ("buy", "sell"):
        return False, "missing_or_bad_side"

    # --------------------------------------------------
    # ENTRY TYPE
    # --------------------------------------------------
    entry_type = _req_str(pc, "entry_type")
    if entry_type not in ("market", "limit"):
        return False, "missing_or_bad_entry_type"

    # --------------------------------------------------
    # TIME IN FORCE
    # --------------------------------------------------
    tif = _req_str(pc, "time_in_force")
    if tif not in ("day", "gtc"):
        return False, "missing_or_bad_time_in_force"

    # --------------------------------------------------
    # LIMIT REQUIREMENT
    # --------------------------------------------------
    if entry_type == "limit":
        if pc.get("limit_price") is None:
            return False, "limit_missing_limit_price"

    # --------------------------------------------------
    # EXIT STYLE IS IGNORED HERE
    # Watcher handles SL/TP attachment.
    # --------------------------------------------------

    return True, "ok"
