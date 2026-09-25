import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def save_brief(brief: dict) -> Path:
    day = datetime.now(IST).strftime("%Y-%m-%d")

    # Ensure the brief itself also contains the correct date.
    brief["date"] = day

    directory = Path("daily")
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{day}.json"

    path.write_text(
        json.dumps(
            brief,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path