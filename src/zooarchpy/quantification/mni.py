"""MNI: conservative sided-element Minimum Number of Individuals.

For each taxon within each *aggregation unit*, the MNI is the largest number of
elements of a single sided element type, taking the more numerous side: if the most
abundant element is the left femur (4 of them) and there are 2 right femora, at least
4 animals are needed to explain the left femora. This is the classical "most frequent
sided element" estimate (see docs/mni.md for scope and limitations).

Two things are deliberately **not** decided for the user:

* the aggregation unit (``aggregate_by``): MNI is not additive and changes with it;
* whether a recorded count is a count of distinct *elements* (``counts_are_elements``):
  counting fragments of the same bone as separate elements overestimates the MNI.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal

from zooarchpy.models import Side
from zooarchpy.quantification.nisp import (
    GROUPABLE,
    _check_quality,
    _reason_table,
    _sort_key,
    _value,
    as_list,
)
from zooarchpy.reporting import AnalysisResult
from zooarchpy.reporting.reports import base_metadata

if TYPE_CHECKING:
    from zooarchpy.assemblage import Assemblage

INTERPRETATION = (
    "MNI is the minimum number of animals needed to explain the most frequent sided "
    "element. It is a lower bound that depends on the aggregation unit."
)
AGGREGATABLE = tuple(g for g in GROUPABLE if g not in ("taxon", "element", "side"))


def mni(
    assemblage: Assemblage,
    *,
    aggregate_by: str | Sequence[str] | None,
    counts_are_elements: bool,
    ambiguous: Literal["separate", "exclude"] = "separate",
    taxon_map: Mapping[str, str] | None = None,
    allow_errors: bool = False,
) -> AnalysisResult:
    """Conservative sided-element MNI per taxon and aggregation unit.

    ``aggregate_by`` is required: pass the fields that define an aggregation unit (e.g.
    ``"phase"``), or ``[]`` to pool the whole assemblage (a deliberate choice that is
    recorded in the metadata). ``counts_are_elements`` is also required and must be
    ``True``: it states that each counted specimen is a distinct element, so
    fragments of one bone must already have been reduced to a single record.
    """
    if not counts_are_elements:
        raise ValueError(
            "MNI from specimen counts is only valid if each counted specimen is a distinct "
            "element (fragments of one bone refitted or reduced beforehand). Declare it with "
            "counts_are_elements=True, or derive the number of elements (MNE) first."
        )
    if aggregate_by is None:
        raise ValueError(
            "aggregate_by is required: MNI depends on the aggregation unit. Pass a field "
            "such as 'phase', a list of fields, or [] to pool the whole assemblage."
        )
    if ambiguous not in ("separate", "exclude"):
        raise ValueError("ambiguous must be 'separate' or 'exclude'")
    groups = as_list(aggregate_by)
    for g in groups:
        if g not in AGGREGATABLE:
            raise ValueError(f"cannot aggregate by {g!r}; valid fields: {', '.join(AGGREGATABLE)}")
    mapping = dict(taxon_map or {})

    warnings: list[str] = []
    _check_quality(assemblage, allow_errors, warnings)

    # (aggregation key, taxon, element) -> {"left": n, "right": n}
    sided: dict[tuple[Any, ...], Counter[str]] = {}
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
        if sp.taxon is None:
            exclude("unidentified")
            continue
        label = mapping.get(sp.taxon, sp.taxon)
        if ambiguous == "exclude" and assemblage.taxonomy.is_ambiguous(label):
            exclude("ambiguous identification")
            continue
        if sp.element is None:
            exclude("element not recorded")
            continue
        if sp.side is None:
            exclude("side not recorded")
            continue
        if sp.side not in (Side.LEFT, Side.RIGHT):
            exclude(f"side is {sp.side.value}: not a left/right element")
            continue
        key = (*(_value(sp, g, label) for g in groups), label, sp.element)
        sided.setdefault(key, Counter())[sp.side.value] += n
        used_rows += 1

    # Per (aggregation, taxon): the most frequent sided element sets the MNI.
    per_unit: dict[tuple[Any, ...], list[tuple[str, int, int, int]]] = {}
    for key, sides in sided.items():
        left, right = sides["left"], sides["right"]
        per_unit.setdefault(key[:-1], []).append((key[-1], max(left, right), left, right))

    columns = (*groups, "taxon", "mni", "limiting_elements", "left", "right")
    rows: list[dict[str, Any]] = []
    for unit in sorted(per_unit, key=_sort_key):
        elements = per_unit[unit]
        best = max(e[1] for e in elements)
        limiting = sorted(e for e in elements if e[1] == best)
        row: dict[str, Any] = dict(zip((*groups, "taxon"), unit, strict=True))
        row["mni"] = best
        row["limiting_elements"] = "; ".join(e[0] for e in limiting)
        # left/right of the first limiting element; ties are listed in limiting_elements.
        row["left"], row["right"] = limiting[0][2], limiting[0][3]
        rows.append(row)

    seen = sorted({r["taxon"] for r in rows})
    amb = [t for t in seen if assemblage.taxonomy.is_ambiguous(t)]
    if amb:
        warnings.append(f"ambiguous categories kept separate, not merged into other taxa: {amb}")
    warnings.append(
        "MNI is not additive: do not sum it across taxa, units or ranks; "
        "it changes with the aggregation unit"
    )
    if not groups:
        warnings.append("whole assemblage pooled into a single aggregation unit")

    meta = base_metadata(
        "mni",
        {
            "method": "sided element, conservative (max of left/right)",
            "aggregate_by": groups,
            "counts_are_elements": counts_are_elements,
            "ambiguous": ambiguous,
            "taxon_map": mapping,
            "allow_errors": allow_errors,
            "rows_are_specimens": assemblage.rows_are_specimens,
        },
    )
    meta.update(
        {
            "unit": "individuals (MNI, lower bound)",
            "interpretation": INTERPRETATION,
            "analytic_unit": [*groups, "taxon"],
            "rows_used": used_rows,
            "elements_used": sum(sum(c.values()) for c in sided.values()),
            "rows_excluded": sum(ex_rows.values()),
            "exclusions": _reason_table(ex_rows, ex_specs),
            "source": assemblage.source,
        }
    )
    return AnalysisResult(columns, rows, meta, warnings)
