"""Small five-field cron scheduler used by the competition deployment."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _matches(part: str, value: int, minimum: int, maximum: int) -> bool:
    if part == "*":
        return True
    allowed: set[int] = set()
    for token in part.split(","):
        token = token.strip()
        if token.startswith("*/"):
            step = int(token[2:])
            if step <= 0:
                raise ValueError("Cron 步长必须大于 0")
            allowed.update(range(minimum, maximum + 1, step))
        elif "-" in token:
            start, end = (int(item) for item in token.split("-", 1))
            allowed.update(range(start, end + 1))
        else:
            allowed.add(int(token))
    if any(item < minimum or item > maximum for item in allowed):
        raise ValueError("Cron 字段超出允许范围")
    return value in allowed


def cron_matches(expression: str, moment: datetime) -> bool:
    parts = expression.split()
    if len(parts) != 5:
        raise ValueError("Cron 表达式必须包含分钟、小时、日期、月份、星期五个字段")
    minute, hour, day, month, weekday = parts
    cron_weekday = (moment.weekday() + 1) % 7
    return (
        _matches(minute, moment.minute, 0, 59)
        and _matches(hour, moment.hour, 0, 23)
        and _matches(day, moment.day, 1, 31)
        and _matches(month, moment.month, 1, 12)
        and _matches(weekday, cron_weekday, 0, 6)
    )


def next_cron_time(expression: str, timezone_name: str, after: datetime | None = None) -> datetime:
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("不支持的时区") from exc
    base = after or datetime.now(timezone.utc)
    base_utc = base.replace(tzinfo=timezone.utc) if base.tzinfo is None else base.astimezone(timezone.utc)
    candidate = base_utc.astimezone(zone).replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(366 * 24 * 60):
        if cron_matches(expression, candidate):
            return candidate.astimezone(timezone.utc).replace(tzinfo=None)
        candidate += timedelta(minutes=1)
    raise ValueError("无法在一年内计算出下一次执行时间")
