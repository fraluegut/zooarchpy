"""CSV reading and writing (standard library only)."""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from zooarchpy.models import FusionStatus, Observation, Side, Specimen
from zooarchpy.validation import Issue, Severity


class DataFormatError(ValueError):
    """The file cannot be interpreted at all (e.g. a mandatory column is missing)."""


REQUIRED_COLUMNS = ("specimen_id", "site", "context")
TEXT_COLUMNS = (
    "phase", "taxon", "taxon_rank", "element", "portion", "tooth", "tooth_wear_stage",
    "age_class", "burning", "identification_confidence", "refit_group",
)  # fmt: skip
OBSERVATION_COLUMNS = ("cut_marks", "carnivore_marks")
KNOWN_COLUMNS = (
    set(REQUIRED_COLUMNS)
    | set(TEXT_COLUMNS)
    | set(OBSERVATION_COLUMNS)
    | {"side", "diagnostic_zones", "count", "weight_g", "completeness", "fusion_status"}
)
MEASUREMENT_PREFIX = "m_"  # e.g. m_GL -> measurements["GL"]

_PRESENT = {"present", "yes", "true", "1"}
_ABSENT = {"absent", "no", "false", "0"}
_NOT_APPLICABLE = {"not_applicable", "n/a"}


def read_specimens(
    path: str | Path, *, rows_are_specimens: bool = False
) -> tuple[list[Specimen], list[Issue]]:
    """Parse a CSV file into specimens plus the issues found while parsing.

    Empty cells mean "not recorded". Unparseable cells are reported as issues and left
    as "not recorded"; rows without the mandatory provenance are dropped *and* reported.
    """
    issues: list[Issue] = []
    specimens: list[Specimen] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        columns = [c.strip() for c in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            raise DataFormatError(f"{path}: missing mandatory column(s): {', '.join(missing)}")
        if "count" not in columns and not rows_are_specimens:
            raise DataFormatError(
                f"{path}: no 'count' column. Either add one or pass rows_are_specimens=True "
                "to declare that every row is exactly one specimen."
            )
        for c in columns:
            if c not in KNOWN_COLUMNS and not c.startswith(MEASUREMENT_PREFIX):
                issues.append(
                    Issue(Severity.INFO, "unknown_column", f"column {c!r} is ignored", field=c)
                )
        for rownum, raw in enumerate(reader, start=1):
            row = {k.strip(): (v or "").strip() for k, v in raw.items() if k is not None}
            spec = _parse_row(row, rownum, issues)
            if spec is not None:
                specimens.append(spec)
    return specimens, issues


def _parse_row(row: dict[str, str], rownum: int, issues: list[Issue]) -> Specimen | None:
    sid = row.get("specimen_id") or None
    if not all(row.get(c) for c in REQUIRED_COLUMNS):
        issues.append(
            Issue(
                Severity.ERROR,
                "missing_required",
                f"row dropped: {', '.join(REQUIRED_COLUMNS)} must all be filled",
                sid,
                row=rownum,
            )
        )
        return None

    def bad(field: str, value: str, expected: str) -> None:
        issues.append(
            Issue(
                Severity.ERROR,
                "unparseable_value",
                f"{value!r} is not {expected}; treated as not recorded",
                sid,
                field,
                rownum,
            )
        )

    def number(field: str, kind: type[int] | type[float]) -> int | float | None:
        value = row.get(field, "")
        if not value:
            return None
        try:
            return kind(value)
        except ValueError:
            bad(field, value, "an integer" if kind is int else "a number")
            return None

    def enum(field: str, cls: type[Side] | type[FusionStatus]) -> Side | FusionStatus | None:
        value = row.get(field, "")
        if not value:
            return None
        try:
            return cls(value.lower())
        except ValueError:
            bad(field, value, f"one of {[m.value for m in cls]}")
            return None

    def observation(field: str) -> Observation:
        value = row.get(field, "").lower()
        if not value:
            return Observation.UNKNOWN
        if value in _PRESENT:
            return Observation.PRESENT
        if value in _ABSENT:
            return Observation.ABSENT
        if value in _NOT_APPLICABLE:
            return Observation.NOT_APPLICABLE
        bad(field, value, "present/absent/not_applicable")
        return Observation.UNKNOWN

    measurements: dict[str, float] = {}
    for key, value in row.items():
        if key.startswith(MEASUREMENT_PREFIX) and value:
            try:
                measurements[key[len(MEASUREMENT_PREFIX) :]] = float(value)
            except ValueError:
                bad(key, value, "a number")

    zones = tuple(z.strip() for z in row.get("diagnostic_zones", "").split(";") if z.strip())
    side = enum("side", Side)
    fusion = enum("fusion_status", FusionStatus)
    count = number("count", int)
    weight = number("weight_g", float)
    completeness = number("completeness", float)
    return Specimen(
        specimen_id=row["specimen_id"],
        site=row["site"],
        context=row["context"],
        diagnostic_zones=zones,
        side=side if isinstance(side, Side) else None,
        fusion_status=fusion if isinstance(fusion, FusionStatus) else None,
        count=int(count) if count is not None else None,
        weight_g=weight,
        completeness=completeness,
        cut_marks=observation("cut_marks"),
        carnivore_marks=observation("carnivore_marks"),
        measurements=measurements,
        **{c: (row.get(c) or None) for c in TEXT_COLUMNS},
    )


def write_table(
    path: str | Path, columns: Sequence[str], rows: Sequence[dict[str, object]]
) -> None:
    """Write a result table; ``None`` becomes an empty cell."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(["" if row[c] is None else row[c] for c in columns])
