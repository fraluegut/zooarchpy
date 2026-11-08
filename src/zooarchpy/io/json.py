"""JSON writing (standard library only)."""

from __future__ import annotations

import json
from pathlib import Path


def write_json(path: str | Path, payload: object) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)
        fh.write("\n")
