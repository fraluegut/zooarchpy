"""NR/NSP and NISP.

NISP (Number of Identified SPecimens) counts specimens assigned to a taxon. It is a
count of *specimens*, not of animals (Lyman 1994; Grayson 1984). See docs/nisp.md.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal

from zooarchpy.reporting import AnalysisResult
from zooarchpy.reporting.reports import base_metadata

if TYPE_CHECKING:
    from zooarchpy.assemblage import Assemblage

GROUPABLE = (
    "site", "context", "phase", "taxon", "taxon_rank", "element", "side", "portion",
    "fusion_status", "age_class", "burning", "cut_marks", "carnivore_marks",
)  # fmt: skip

INTERPRETATION = "NISP counts identified specimens. It is not a number of animals."


class DataQualityError(ValueError):
    """The assemblage has validation errors and the caller did not accept them."""


def as_list(value: str | Sequence[str] | None) -> list[str]:
    if value is None:
        return []
    return [value] if isinstance(value, str) else list(value)


def _value(spec: Any, field: str, taxon: str | None) -> Any:
    v = taxon if field == "taxon" else getattr(spec, field)
    return getattr(v, "value", v)  # enums -> plain strings


def _sort_key(key: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple((v is None, "" if v is None else str(v)) for v in key)


def _check_quality(assemblage: Assemblage, allow_errors: bool, warnings: list[str]) -> None:
    errors = assemblage.validate().errors
    if not errors:
        return
    if not allow_errors:
        shown = "; ".join(str(e) for e in errors[:3])
        raise DataQualityError(
            f"{len(errors)} validation error(s), e.g. {shown}. Fix them or pass "
            "allow_errors=True to compute anyway (affected rows are reported)."
        )
    warnings.append(
        f"computed despite {len(errors)} validation error(s); see assemblage.validate()"
    )


def _reason_table(rows: Counter[str], specimens: Counter[str]) -> dict[str, dict[str, int]]:
    return {r: {"rows": rows[r], "specimens": specimens[r]} for r in sorted(rows)}


def nisp(
    assemblage: Assemblage,
    group_by: str | Sequence[str] = "taxon",
    *,
    taxon: str | Sequence[str] | None = None,
    min_rank: str | None = None,
    ambiguous: Literal["separate", "exclude"] = "separate",
    taxon_map: Mapping[str, str] | None = None,
    include_unidentified: bool = False,
    percent: bool | Sequence[str] = False,
    allow_errors: bool = False,
) -> AnalysisResult:
    """NISP per group.

    Policies (all recorded in the result metadata):

    * ``ambiguous``: ``"separate"`` keeps e.g. ``Ovis/Capra`` as its own category;
      ``"exclude"`` drops such rows. They are never merged into other taxa.
    * ``taxon_map``: explicit relabelling applied before filtering/grouping.
    * ``min_rank``: keep only identifications at least this specific; rows without a
      recorded rank are excluded (and reported), not guessed.
    * ``percent``: ``True`` = percentage of the grand total; a list of group columns =
      percentage within each combination of those columns.
    """
    groups = as_list(group_by)
    for g in groups:
        if g not in GROUPABLE:
            raise ValueError(f"cannot group by {g!r}; valid fields: {', '.join(GROUPABLE)}")
    within: list[str] = [] if percent is True else as_list(percent) if percent else []
    for w in within:
        if w not in groups:
            raise ValueError(f"percent column {w!r} must be one of group_by {groups}")
    if min_rank is not None and assemblage.taxonomy.rank_index(min_rank) is None:
        raise ValueError(f"unknown rank {min_rank!r}; known: {assemblage.taxonomy.ranks}")
    wanted = set(as_list(taxon)) if taxon is not None else None
    mapping = dict(taxon_map or {})
    if ambiguous not in ("separate", "exclude"):
        raise ValueError("ambiguous must be 'separate' or 'exclude'")

    warnings: list[str] = []
    _check_quality(assemblage, allow_errors, warnings)

    totals: Counter[tuple[Any, ...]] = Counter()
    ex_rows: Counter[str] = Counter()
    ex_specs: Counter[str] = Counter()
    used_rows = 0
    for sp in assemblage.specimens:
        n = assemblage.effective_count(sp)

        def exclude(reason: str, n: int | None = n) -> None:
            ex_rows[reason] += 1
            ex_specs[reason] += n if n and n > 0 else 0

        if n is None:
            exclude("count not recorded")
            continue
        if n <= 0:
            exclude("invalid count (<= 0)")
            continue
        label = mapping.get(sp.taxon, sp.taxon) if sp.taxon is not None else None
        if label is None and not include_unidentified:
            exclude("unidentified")
            continue
        if label is not None:
            if ambiguous == "exclude" and assemblage.taxonomy.is_ambiguous(label):
                exclude("ambiguous identification")
                continue
            if wanted is not None and label not in wanted:
                exclude("taxon filter")
                continue
            if min_rank is not None:
                idx = assemblage.taxonomy.rank_index(sp.taxon_rank) if sp.taxon_rank else None
                if idx is None:
                    exclude("rank not recorded or unknown")
                    continue
                if idx < assemblage.taxonomy.rank_index(min_rank):  # type: ignore[operator]
                    exclude("rank less specific than min_rank")
                    continue
        elif wanted is not None:
            exclude("taxon filter")
            continue
        totals[tuple(_value(sp, g, label) for g in groups)] += n
        used_rows += 1

    keys = sorted(totals, key=_sort_key)
    columns = (*groups, "nisp") + (("percent",) if percent else ())
    rows: list[dict[str, Any]] = []
    denominators: Counter[tuple[Any, ...]] = Counter()
    if percent:
        pidx = [groups.index(w) for w in within]
        for k in keys:
            denominators[tuple(k[i] for i in pidx)] += totals[k]
    for k in keys:
        row: dict[str, Any] = dict(zip(groups, k, strict=True))
        row["nisp"] = totals[k]
        if percent:
            row["percent"] = 100 * totals[k] / denominators[tuple(k[i] for i in pidx)]
        rows.append(row)

    if "taxon" in groups:
        seen = sorted({r["taxon"] for r in rows if r["taxon"] is not None})
        amb = [t for t in seen if assemblage.taxonomy.is_ambiguous(t)]
        if amb:
            warnings.append(
                f"ambiguous categories kept separate, not merged into other taxa: {amb}"
            )
    if percent:
        warnings.append(
            "percentages depend on the denominator; it is the "
            + (f"total within {within}" if within else "grand total")
            + " of included specimens"
        )

    meta = base_metadata(
        "nisp",
        {
            "group_by": groups,
            "taxon": sorted(wanted) if wanted is not None else None,
            "min_rank": min_rank,
            "ambiguous": ambiguous,
            "taxon_map": mapping,
            "include_unidentified": include_unidentified,
            "percent": percent if isinstance(percent, bool) else list(percent),
            "allow_errors": allow_errors,
            "rows_are_specimens": assemblage.rows_are_specimens,
        },
    )
    meta.update(
        {
            "unit": "specimens (NISP)",
            "interpretation": INTERPRETATION,
            "analytic_unit": groups,
            "rows_used": used_rows,
            "specimens_used": sum(totals.values()),
            "rows_excluded": sum(ex_rows.values()),
            "exclusions": _reason_table(ex_rows, ex_specs),
            "source": assemblage.source,
        }
    )
    return AnalysisResult(columns, rows, meta, warnings)


def nsp(
    assemblage: Assemblage,
    group_by: str | Sequence[str] | None = None,
    *,
    allow_errors: bool = False,
) -> AnalysisResult:
    """NR/NSP: all specimens, split into identified and unidentified."""
    groups = as_list(group_by)
    for g in groups:
        if g not in GROUPABLE or g == "taxon":
            raise ValueError(f"cannot group NSP by {g!r}")
    warnings: list[str] = []
    _check_quality(assemblage, allow_errors, warnings)

    table: dict[tuple[Any, ...], list[int]] = {}
    ex_rows: Counter[str] = Counter()
    ex_specs: Counter[str] = Counter()
    for sp in assemblage.specimens:
        n = assemblage.effective_count(sp)
        if n is None or n <= 0:
            reason = "count not recorded" if n is None else "invalid count (<= 0)"
            ex_rows[reason] += 1
            continue
        cell = table.setdefault(tuple(_value(sp, g, sp.taxon) for g in groups), [0, 0])
        cell[0 if sp.is_identified else 1] += n
    columns = (*groups, "identified", "unidentified", "total")
    rows = []
    for k in sorted(table, key=_sort_key):
        ident, unident = table[k]
        row: dict[str, Any] = dict(zip(groups, k, strict=True))
        row.update(identified=ident, unidentified=unident, total=ident + unident)
        rows.append(row)
    meta = base_metadata(
        "nsp",
        {
            "group_by": groups,
            "allow_errors": allow_errors,
            "rows_are_specimens": assemblage.rows_are_specimens,
        },
    )
    meta.update(
        {
            "unit": "specimens (NR/NSP)",
            "rows_excluded": sum(ex_rows.values()),
            "exclusions": _reason_table(ex_rows, ex_specs),
            "source": assemblage.source,
        }
    )
    return AnalysisResult(columns, rows, meta, warnings)
