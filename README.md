# ZooArchPy

Verifiable quantitative zooarchaeology for Python. The aim is a library whose results can
be cited in a methods section: explicit policies, no silent assumptions, every result
carrying the method and warnings that produced it.

**Status: pre-alpha, Phase 1 (MVP).** Implemented: `Specimen` model, `Assemblage`, CSV
import, structured validation, NR/NSP, NISP (+ percentages, grouping by site / context /
phase / taxon / element...), CSV and JSON export. MNE, MNI, MAU, mortality, taphonomy,
biometry and diversity are planned (see [docs/roadmap.md](docs/roadmap.md)).

## Install (from a clone)

```bash
pip install -e ".[dev]"
pytest
```

Requires Python ≥ 3.11. The core has **no runtime dependencies**.

## Example

```python
from zooarchpy import Assemblage

fauna = Assemblage.from_csv("examples/fictional_fauna.csv")   # fictional data
print(fauna.validate())                                       # errors and warnings
result = fauna.nisp(group_by=["context", "taxon"], percent=["context"])
print(result)
result.to_csv("nisp.csv")      # table only
result.to_json("nisp.json")    # table + method, parameters, exclusions, warnings
```

Principles visible in the API:

- A row is **not** assumed to be one specimen. Use a `count` column, or declare
  `rows_are_specimens=True`.
- Missing ≠ observed absence ≠ not applicable (`Observation`).
- `Ovis/Capra`, `Capra hircus` and `Mammalia` stay separate categories; merging requires
  an explicit `taxon_map`.
- Data with validation errors are rejected unless you pass `allow_errors=True`.
- NISP is reported as a count of specimens, never as a number of animals.

## Data format (the contract)

Input is a CSV, one row per specimen **or** per aggregated lot. Every analysis declares the
columns it needs; the same file can be used by several analyses. Rules for all columns:

- An **empty cell means "not recorded"**. It is never read as zero, as "absent" or as
  "not applicable".
- Unknown columns are ignored with an informational message (nothing is lost silently).
- Unparseable cells are reported as errors and treated as "not recorded".
- Column names are lower case. Measurements use the prefix `m_` (e.g. `m_GL` = greatest length).
- Encoding: UTF-8. Several values in one cell are separated by `;`.

### Specimen table

| Column | Type | Accepted values | Needed by |
|---|---|---|---|
| `specimen_id` | text | any, non-empty | all (mandatory) |
| `site` | text | any, non-empty | all (mandatory) |
| `context` | text | any, non-empty | all (mandatory) |
| `count` | integer | ≥ 1 | NISP/NSP. If absent, pass `rows_are_specimens=True` |
| `taxon` | text | your labels, exact match (`Ovis/Capra` ≠ `Ovis aries`) | NISP, MNE*, MNI* |
| `taxon_rank` | text | one of the ranks in `TaxonomyPolicy` (`species`, `genus`...) | NISP with `min_rank` |
| `element` | text | your labels (`humerus`, `tibia`...) | MNE*, MNI* (must exist in the zone scheme) |
| `side` | text | `left`, `right`, `axial`, `indeterminate` | MNE*, MNI* |
| `portion` | text | free (`proximal`, `shaft`...) | grouping only |
| `diagnostic_zones` | text list | zone codes of the scheme, separated by `;` | MNE*, MNI* |
| `refit_group` | text | free label; rows sharing it are one physical bone | MNE*, MNI* (optional) |
| `fusion_status` | text | `fused`, `unfused`, `indeterminate` | MNI* (optional) |
| `age_class` | text | free | optional |
| `completeness` | number | 0–1 | optional |
| `weight_g` | number | ≥ 0 | optional |
| `cut_marks`, `carnivore_marks` | text | `present`, `absent`, `not_applicable` (empty = unknown) | optional |
| `burning`, `tooth`, `tooth_wear_stage`, `identification_confidence` | text | free | optional |
| `m_<name>` | number | any | optional |

\* **Planned, not implemented yet** (Phase 2). Today only NR/NSP and NISP exist; they need
the three mandatory columns, `count` (or `rows_are_specimens=True`) and, for NISP, `taxon`.

### Zone scheme table (planned, Phase 2)

For MNE and MNI the library must know how each element is divided into zones. It does **not**
ship invented schemes: you supply a table, or use one that cites its published source.

| Column | Type | Meaning |
|---|---|---|
| `group` | text | taxonomic group the scheme applies to (`Ungulata`, ...) |
| `element` | text | same labels as in the specimen table |
| `zone` | text | short code, unique within group + element |
| `criterion` | text | when the zone counts as present, quoted from the source |
| `source` | text | mandatory citation; a scheme without one is refused |

### Deciding whether two fragments can be the same bone (planned)

Two fragments of the same element and side that **both score the same zone** cannot be the
same bone. Fragments that share no zone **may** be the same bone, which is not proven. The
number of bones required is therefore a **minimum**, not an estimate.

With the fictional scheme `PE, PS, MS, DS, DE` (proximal epiphysis ... distal epiphysis):

```
fragment  side   zones       fragment  side   zones
A         left   PE;PS       D         left   PS;MS
B         left   DS;DE       E         left   DE
C         left   MS          F         right  DE

A and D share PS  -> two different bones      B and E share DE -> two different bones
A + B + C share nothing -> may be one bone    F is right-sided -> never the left bone
Left zone counts: PE 1, PS 2, MS 2, DS 1, DE 2   -> at least 2 left humeri, 1 right
```

Fragments with no usable taxon, element or zones are **not guessed at**: they are left out
and listed with the reason. A blank `diagnostic_zones` cell (not recorded) will be kept
distinct from an explicit `none` (recorded, no diagnostic zone preserved).

Working example files (all fictional): [examples/](examples/).

## Documentation

[docs/design.md](docs/design.md) · [docs/nisp.md](docs/nisp.md) ·
[docs/roadmap.md](docs/roadmap.md) · [docs/references.md](docs/references.md) ·
[CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT. See [LICENSE](LICENSE). Cite via [CITATION.cff](CITATION.cff).
