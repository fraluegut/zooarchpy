"""Result objects: tabular data plus the metadata needed to document the method."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from zooarchpy._version import __version__
from zooarchpy.io import write_json, write_table


def base_metadata(method: str, parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        "zooarchpy_version": __version__,
        "executed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "method": method,
        "parameters": parameters,
    }


@dataclass
class AnalysisResult:
    """Every analysis returns this: a table, the method used and its warnings."""

    columns: tuple[str, ...]
    rows: list[dict[str, Any]]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self.rows)

    def column(self, name: str) -> list[Any]:
        return [r[name] for r in self.rows]

    def to_dicts(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.rows]

    def to_csv(self, path: str | Path) -> None:
        """Write the table only. Use :meth:`to_json` to keep the method metadata."""
        write_table(path, self.columns, self.rows)

    def to_json(self, path: str | Path) -> None:
        write_json(
            path,
            {
                "metadata": self.metadata,
                "warnings": self.warnings,
                "columns": list(self.columns),
                "rows": self.rows,
            },
        )

    def __str__(self) -> str:
        return _render(self.columns, self.rows, self.warnings)


def _fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _render(columns: Sequence[str], rows: Sequence[dict[str, Any]], warnings: list[str]) -> str:
    cells = [[_fmt(r[c]) for c in columns] for r in rows]
    widths = [max([len(c), *(len(r[i]) for r in cells)]) for i, c in enumerate(columns)]
    lines = ["  ".join(c.ljust(w) for c, w in zip(columns, widths, strict=True)).rstrip()]
    lines += ["  ".join(v.ljust(w) for v, w in zip(r, widths, strict=True)).rstrip() for r in cells]
    lines += [f"warning: {w}" for w in warnings]
    return "\n".join(lines)
