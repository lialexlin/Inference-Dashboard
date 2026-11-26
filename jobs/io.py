"""The one JSON writer every job uses."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: Any) -> None:
    """Write `data` as UTF-8 JSON via a temp file, so a crash mid-write never
    leaves a half-written file for the site to load. UTF-8 is explicit because
    refresh.cmd runs on Windows, whose default code page mangles CJK names."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
