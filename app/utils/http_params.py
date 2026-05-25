def parse_optional_int(value: str | int | None) -> int | None:
    """Безопасный разбор query-параметра; пустая строка и 'None' → None."""
    if value is None or value == "" or value == "None":
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def schedule_cancel_url(
    base: str,
    group_id: int | None,
    period_id: int | None,
    groups: list,
    periods: list,
    week_start_iso: str | None = None,
) -> str:
    gid = group_id or (groups[0].id if groups else None)
    pid = period_id or (periods[0].id if periods else None)
    if gid and pid:
        url = f"{base}/schedule?group_id={gid}&period_id={pid}"
        if week_start_iso:
            url += f"&week_start={week_start_iso}"
        return url
    if week_start_iso:
        return f"{base}/schedule?week_start={week_start_iso}"
    return f"{base}/schedule"
