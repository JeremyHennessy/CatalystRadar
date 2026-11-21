"""Offline NYSE core-equity close selection, not price or execution evidence."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
CORE_CLOSES = (time(13), time(16))


def next_two_core_closes(observed: datetime, reviewed_days: dict[date, time | None]) -> tuple[datetime, datetime]:
    """Select two strictly later scheduled UTC closes, or reject incomplete coverage.

    Supply independently reviewed date rows. A present None marks a known
    non-session; a missing key cannot be assumed closed. No inferred dates,
    exchange-status observations, provider publication times, or prices.
    """
    if not isinstance(observed, datetime) or observed.utcoffset() is None:
        raise ValueError("timezone-aware observation required")
    day = observed.astimezone(NEW_YORK).date()
    found = []
    while day in reviewed_days:
        close = reviewed_days[day]
        if close is not None:
            if type(close) is not time or close.tzinfo is not None or close not in CORE_CLOSES:
                raise ValueError("unsupported NYSE core close")
            scheduled_utc = datetime.combine(day, close, tzinfo=NEW_YORK).astimezone(timezone.utc)
            if scheduled_utc > observed.astimezone(timezone.utc):
                found.append(scheduled_utc)
                if len(found) == 2:
                    return found[0], found[1]
        if day == date.max:
            break
        day += timedelta(days=1)
    raise ValueError("insufficient reviewed calendar coverage")
