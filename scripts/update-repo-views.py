#!/usr/bin/env python3
"""Merge GitHub repository traffic into cumulative view stats.

Reads the JSON returned by GET /repos/{owner}/{repo}/traffic/views and keeps a
running per-day tally in stats/repo-views-data.json, then writes a shields.io
endpoint badge payload to stats/repo-views.json.
"""

import datetime
import json
import pathlib
import sys


def load_days(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    days = data.get("days")
    return days if isinstance(days, dict) else {}


def main() -> int:
    traffic_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/views.json")
    stats_dir = pathlib.Path("stats")
    stats_dir.mkdir(exist_ok=True)

    acc_path = stats_dir / "repo-views-data.json"
    days = load_days(acc_path)

    traffic = json.loads(traffic_path.read_text(encoding="utf-8"))
    for item in traffic.get("views", []):
        day = str(item.get("timestamp", ""))[:10]
        if not day:
            continue
        # GitHub only exposes a rolling 14-day window, so each run refreshes
        # the days still inside it and keeps older days from earlier runs.
        days[day] = int(item.get("count", 0) or 0)

    total = sum(int(value) for value in days.values())
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

    acc_path.write_text(
        json.dumps(
            {"days": days, "total": total, "updated": now},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    badge = {
        "schemaVersion": 1,
        "label": "仓库浏览",
        "message": f"{total:,}",
        "color": "b94f6f",
        "labelColor": "1c2826",
    }
    (stats_dir / "repo-views.json").write_text(
        json.dumps(badge, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"total views: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
