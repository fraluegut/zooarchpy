# MNI (conservative sided element)

**MNI** is the minimum number of animals needed to account for the specimens of a taxon.
This implementation is the simplest, most conservative variant: for each taxon within an
aggregation unit, take every element type that has a recorded side, count lefts and
rights, keep the larger of the two, and report the maximum over element types. The
element(s) that set that maximum are reported in `limiting_elements`.

```python
fauna.mni(aggregate_by="phase", counts_are_elements=True)
```

Worked by hand: humerus 3 left / 2 right -> 3; femur 1 left / 4 right -> 4. MNI = 4,
limited by the femur.

## Choices the user must declare

| Decision | Parameter | Why it is not defaulted |
|---|---|---|
| Aggregation unit | `aggregate_by` (required; `[]` pools everything) | MNI changes with the unit and is not additive (Grayson 1984; Lyman 2008). |
| Is each counted specimen a distinct element? | `counts_are_elements` (required, must be `True`) | Counting fragments of one bone as separate elements inflates the MNI. Derive elements (MNE) or refit first. |
| Ambiguous labels | `ambiguous` | Same policy as NISP: kept separate, never merged. |
| Merging labels | `taxon_map` | Explicit only. |

## What is excluded (and reported)

Rows without count, taxon, element or side are excluded, as are elements whose side is
`axial` or `indeterminate`. They are listed by reason in `metadata["exclusions"]`; nothing
is guessed. A taxon with only axial elements therefore gets no MNI row, not an MNI of 0.

## Limitations

- It is a **lower bound** and says nothing about how many animals were actually deposited.
- Not additive: never sum MNI across taxa, aggregation units or taxonomic ranks.
- Ignores age, sex, size and fusion; pairing refinements and other MNI variants are not
  implemented.
- With `counts_are_elements=True` the result is only as good as that declaration.
- Not yet reviewed against the primary sources listed in [references.md](references.md);
  the definition above follows the textbook formulation, and the page numbers and exact
  wording must be checked before citing it in a publication.

References: Lyman 1994; Lyman 2008; Grayson 1984 (see [references.md](references.md)).
