# MNE (zone-based)

**MNE** is the minimum number of skeletal elements needed to account for the specimens
recorded. This version is zone-based: each specimen lists the diagnostic zones it
preserves, and for every taxon / element / side within an aggregation unit the MNE is the
highest count reached by any single zone.

```python
fauna.mne(
    aggregate_by="phase",
    zone_scheme="<author year of the scheme you recorded with>",
    counts_are_elements=True,
)
```

In the CSV, zones go in `diagnostic_zones` separated by `;` (e.g. `Z1;Z3`).
Worked by hand: zone Z1 on 3 specimens, Z2 on 1, Z3 on 2 -> MNE 3, limited by Z1. The
result also lists every zone count (`zone_counts`) so it can be checked.

## ZooArchPy ships no zone tables

Which zones exist for each element, and when a zone counts as present, depends on a
published scheme. The library does not contain or invent any: you record the zones, and you
must name the scheme in `zone_scheme`, which is stored in the result metadata. The label is
not validated against anything.

## Choices the user must declare

| Decision | Parameter | Why it is not defaulted |
|---|---|---|
| Aggregation unit | `aggregate_by` (required; `[]` pools everything) | MNE changes with the unit (Grayson 1984; Lyman 2008). |
| Zone scheme | `zone_scheme` (required) | Results are only comparable within one scheme. |
| Are different specimens different elements? | `counts_are_elements` (required, `True`) | A zone seen on two fragments is counted twice. Refit or reduce first. |
| Ambiguous labels / merging | `ambiguous`, `taxon_map` | Same policy as NISP and MNI. |

## What is excluded (and reported)

Rows without count, taxon, element or zones are excluded, and so are lots with
`count > 1` (the zones cannot be assigned to individual pieces). A missing side is kept
as `side=None`, never merged with left or right, and sides are never paired. All
exclusions are listed by reason in `metadata["exclusions"]`.

## Limitations

- A lower bound: it says nothing about how many elements were deposited.
- Not additive across aggregation units, sides, taxa or ranks.
- Presence of a zone is taken as recorded; no minimum-completeness rule is applied.
- Refits (`refit_group`), portion overlap and paired left/right elements are not used.
- Not yet reviewed against the primary sources in [references.md](references.md); the
  definition follows the textbook formulation and must be checked before being cited.
- The MNE is not yet fed into MNI: `mni` still needs `counts_are_elements=True`.

References: Lyman 1994; Lyman 2008; Grayson 1984 (see [references.md](references.md)).
