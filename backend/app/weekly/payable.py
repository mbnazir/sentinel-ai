from decimal import Decimal, InvalidOperation
from typing import Any

from app.weekly.models import ResolutionStatus, SessionPayable


def _number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return number if number.is_finite() and number >= 0 else None


def resolve_session_payable(metadata: dict[str, object] | None) -> SessionPayable:
    data = metadata or {}
    raw_regular, raw_overtime = data.get("regular_hour"), data.get("overtime")
    regular, overtime = _number(raw_regular), _number(raw_overtime)
    if ("regular_hour" not in data or "overtime" not in data
            or regular is None or overtime is None):
        return SessionPayable(status=ResolutionStatus.INSUFFICIENT_DATA,
                              raw_regular_hour=raw_regular, raw_overtime=raw_overtime,
                              provenance=("Quartz payable metadata absent or invalid",))
    # Repository transports these fields without unit or authority documentation.
    return SessionPayable(regular_seconds=regular, overtime_seconds=overtime,
                          total_seconds=(regular or Decimal(0)) + (overtime or Decimal(0)),
                          status=ResolutionStatus.PROVISIONAL, raw_regular_hour=raw_regular,
                          raw_overtime=raw_overtime,
                          provenance=("Assumed metadata unit seconds; Quartz semantics unconfirmed",))
