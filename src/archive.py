import json
from datetime import date
from pathlib import Path


def save_brief(brief: dict) -> Path:
    day = brief.get("date") or date.today().isoformat()
    directory = Path("daily")
    directory.mkdir(parents=True, exist_ok=True)

    path = directory / f"{day}.json"
    path.write_text(
        json.dumps(brief, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return path

