"""Group study content and exams by JLPT level (N5 → N1)."""

from __future__ import annotations

from app.content import LEVEL_ORDER
from app.data_loader import JLPT_LEVELS


def group_items_by_level(items, level_attr: str = "level") -> list[dict]:
    buckets: dict[str, list] = {lv: [] for lv in LEVEL_ORDER}
    for item in items:
        lv = getattr(item, level_attr, None) if not isinstance(item, dict) else item.get(level_attr)
        if lv in buckets:
            buckets[lv].append(item)
    return [{"level": lv, "entries": buckets[lv], "total": len(buckets[lv])} for lv in LEVEL_ORDER]


def resolve_active_level(request, default_level: str) -> str:
    level = (request.args.get("level") or "").strip().upper()
    if level in JLPT_LEVELS:
        return level
    return default_level if default_level in JLPT_LEVELS else "N5"


def group_leaderboard(entries: list[dict]) -> list[dict]:
    buckets: dict[str, list] = {lv: [] for lv in LEVEL_ORDER}
    for entry in entries:
        lv = entry.get("level")
        if lv in buckets:
            buckets[lv].append(entry)
    groups = []
    for lv in LEVEL_ORDER:
        rows = buckets[lv]
        if not rows:
            continue
        for i, row in enumerate(rows):
            row = {**row, "rank": i + 1}
            rows[i] = row
        groups.append({"level": lv, "entries": rows, "total": len(rows)})
    return groups
