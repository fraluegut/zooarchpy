# NR/NSP and NISP

**NR/NSP**: all specimens (sum of `count`), split into identified and unidentified.
**NISP**: sum of `count` over specimens with a recorded taxon, per group.

Each result records its parameters, number of rows/specimens used, and exclusions by
reason (`count not recorded`, `unidentified`, `taxon filter`, ...).

## Counting policy

A row contributes its `count`. Without a count, a row contributes 1 only if the caller
declared `rows_are_specimens=True`; otherwise it is excluded and reported.

## Limitations

- NISP is not a number of animals and is not comparable across taxa without considering
  differential fragmentation, skeletal composition and recovery.
- Counts depend on identification precision: ambiguous or high-rank labels are kept apart,
  so NISP per taxon is not additive across ranks.
- Percentages depend on the chosen denominator; the metadata state it.
- Aggregated lots are trusted as entered; check them against your recording protocol.

References: Lyman 1994; Grayson 1984; Reitz & Wing 2008 (see [references.md](references.md)).
