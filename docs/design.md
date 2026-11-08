# Design (Phase 1)

## Public interface

```python
Assemblage.from_csv(path, *, rows_are_specimens=False, taxonomy=None, vocabularies=None)
Assemblage(specimens, ...)
Assemblage.validate() -> ValidationReport
Assemblage.nisp(group_by="taxon", *, taxon, min_rank, ambiguous, taxon_map,
                include_unidentified, percent, allow_errors) -> AnalysisResult
Assemblage.nsp(group_by=None) -> AnalysisResult
AnalysisResult: .rows .columns .metadata .warnings .to_csv() .to_json()
```

## Entities

`Specimen` (frozen dataclass; provenance mandatory) → `Assemblage` (specimens + explicit
policies: `rows_are_specimens`, `TaxonomyPolicy`, `Vocabulary` per field) → analyses return
`AnalysisResult` (table + metadata + warnings). `Issue`/`ValidationReport` carry validation.

## Methodological decisions that need configuration

| Decision | Where | Default |
|---|---|---|
| Is a row one specimen? | `rows_are_specimens` | no: needs `count` |
| What is an ambiguous identification? | `TaxonomyPolicy` | `/`, `cf.`, `aff.` + declared labels |
| How to treat ambiguous labels | `nisp(ambiguous=)` | kept as separate categories |
| Merging labels | `nisp(taxon_map=)` | never automatic |
| Rank filter | `nisp(min_rank=)`, `TaxonomyPolicy.ranks` | off |
| Unidentified in NISP | `include_unidentified` | excluded (counted in NSP) |
| Validation errors | `allow_errors` | computation refused |

## Dependencies

None at runtime (stdlib `csv`, `dataclasses`, `json`). Why: the core must stay light and
installable anywhere. `pandas`, `pydantic`, `scipy`, `matplotlib`, `openpyxl` are only
added when a feature truly needs them, as extras (`plots`, `excel` are already declared).
Dev: `pytest`, `ruff`, `mypy`.

## Rigorous now vs. needs literature/data first

- Now: NR/NSP, NISP, percentages, grouping, validation of basic data integrity.
- Phase 2, needs primary sources and reference tables: MNE (zone-based), MNI (sided element),
  MAU (needs per-taxon skeletal frequency tables supplied by the researcher).
- Phase 3+, needs published reference tables: fusion and dental-wear ageing, tafonomic
  scales, LSI references. Nothing will be invented to fill these in.

## Not yet implemented from the brief's tree

`models/anatomy.py`, `mne/mni/mau`, `mortality`, `taphonomy`, `biometry`, `diversity`,
`visualization`, `io/excel.py`. They are added in the phase that implements them rather
than as empty stubs.
