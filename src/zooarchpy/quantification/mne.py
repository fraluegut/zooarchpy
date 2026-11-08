"""MNE: Minimum Number of Elements, zone-based.

For each taxon, element and side within an aggregation unit, every specimen records the
diagnostic zones it preserves. The MNE is the highest count reached by any single zone:
if zone A is present on 3 specimens and zone B on 5, at least 5 elements are needed.
See docs/mne.md for scope and limitations.

ZooArchPy ships **no** zone tables. Zones are whatever the researcher recorded, following
a published scheme that must be named (``zone_scheme``) so that it is cited in the result.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal

from zooarchpy.quantification.mni import AGGREGATABLE
from zooarchpy.quantification.nisp import (
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
    "MNE is the minimum number of skeletal elements needed to explain the most frequent "
    "diagnostic zone. It is a lower bound that depends on the zone scheme and on the "
    "aggregation unit."
)


def mne(
    assemblage: Assemblage,
    *,
    aggregate_by: str | Sequence[str] | None,
    zone_scheme: str,
    counts_are_elements: bool,
    method: Literal["zones"] = "zones",
    ambiguous: Literal["separate", "exclude"] = "separate",
    taxon_map: Mapping[str, str] | None = None,
    allow_errors: bool = False,
) -> AnalysisResult:
    """Zone-based MNE per taxon, element, side and aggregation unit.

    Required declarations (none has a default because each changes the result):

    * ``aggregate_by``: fields defining the aggregation unit, or ``[]`` to pool everything.
    * ``zone_scheme``: the published scheme the recorded zones follow (e.g. an author and
      year). It is stored in the metadata; it is not validated against any table.
    * ``counts_are_elements``: must be ``True``. A zone found on two specimens is counted
      twice, i.e. specimens are assumed to be different elements. Refit or reduce
      fragments of one bone beforehand.

    Each row must be one specimen (``count`` 1, or ``rows_are_specimens``): a lot with
    ``count > 1`` cannot say which zones belong to which piece, so it is excluded.
    """
    if method != "zones":
        raise ValueError("only method='zones' is implemented")
    if not isinstance(zone_scheme, str) or not zone_scheme.strip():
        raise ValueError(
            "zone_scheme is required: name the published scheme your diagnostic zones follow"
        )
    if not counts_are_elements:
        raise ValueError(
            "zone counts only give a minimum number of elements if different specimens are "
            "different elements (fragments of one bone refitted or reduced beforehand). "
            "Declare it with counts_are_elements=True."
        )
    if aggregate_by is None:
        raise ValueError(
            "aggregate_by is required: MNE depends on the aggregation unit. Pass a field "
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

    # (aggregation..., taxon, element, side) -> zone -> number of specimens showing it
    zones: dict[tuple[Any, ...], Counter[str]] = {}
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
        if n > 1:
            exclude("lot with count > 1: zones cannot be assigned to pieces")
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
        if not sp.diagnostic_zones:
            exclude("no diagnostic zones recorded")
            continue
        side = sp.side.value if sp.side is not None else None
        key = (*(_value(sp, g, label) for g in groups), label, sp.element, side)
        counter = zones.setdefault(key, Counter())
        for z in set(sp.diagnostic_zones):  # a zone repeated on one specimen counts once
            counter[z] += 1
        used_rows += 1

    columns = (*groups, "taxon", "element", "side", "mne", "limiting_zones", "zone_counts")
    rows: list[dict[str, Any]] = []
    for key in sorted(zones, key=_sort_key):
        counter = zones[key]
        best = max(counter.values())
        row: dict[str, Any] = dict(zip((*groups, "taxon", "element", "side"), key, strict=True))
        row["mne"] = best
        row["limiting_zones"] = "; ".join(sorted(z for z, c in counter.items() if c == best))
        row["zone_counts"] = "; ".join(f"{z}={c}" for z, c in sorted(counter.items()))
        rows.append(row)

    seen = sorted({r["taxon"] for r in rows})
    amb = [t for t in seen if assemblage.taxonomy.is_ambiguous(t)]
    if amb:
        warnings.append(f"ambiguous categories kept separate, not merged into other taxa: {amb}")
    if any(r["side"] is None for r in rows):
        warnings.append("rows without a recorded side are reported with side=None, not merged")
    warnings.append(
        "MNE is not additive across aggregation units, sides or taxa, and sides are not "
        "combined or paired"
    )
    if not groups:
        warnings.append("whole assemblage pooled into a single aggregation unit")

    meta = base_metadata(
        "mne",
        {
            "method": method,
            "zone_scheme": zone_scheme,
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
            "unit": "elements (MNE, lower bound)",
            "interpretation": INTERPRETATION,
            "analytic_unit": [*groups, "taxon", "element", "side"],
            "rows_used": used_rows,
            "rows_excluded": sum(ex_rows.values()),
            "exclusions": _reason_table(ex_rows, ex_specs),
            "source": assemblage.source,
        }
    )
    return AnalysisResult(columns, rows, meta, warnings)
