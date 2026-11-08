# ZooArchPy

Verifiable quantitative zooarchaeology for Python. The aim is a library whose results can
be cited in a methods section: explicit policies, no silent assumptions, every result
carrying the method and warnings that produced it.

> **Status: pre-alpha.** Only NR/NSP and NISP are implemented. The API will change.
> Not yet published on PyPI.

## What works today and what is planned

| Area | Status |
|---|---|
| `Specimen` / `Assemblage`, CSV import, structured validation | implemented |
| NR/NSP and NISP (grouping, percentages, ambiguity policies, CSV/JSON export) | implemented |
| MNE and MNI from **fragments** (zone-based, conservative) | planned, Phase 2 |
| MAU / %MAU with researcher-supplied reference tables | planned, Phase 2 |
| Mortality, taphonomy, biometry, diversity | planned, Phase 3 |
| Plots (skeleton diagrams painted by zone or by element) | planned, Phase 4 |

Details in [docs/roadmap.md](docs/roadmap.md) and [docs/design.md](docs/design.md).

### Why another tool

Zooarchaeological quantification is usually done in spreadsheets, closed databases or GIS
add-ons, and the choices that change a result (what counts as one specimen, how ambiguous
identifications are treated, how fragments are matched) are rarely written down. ZooArchPy
makes those choices explicit parameters and records them in every result. It does not invent
methodology: each method cites its primary source, and anything not yet read from the source
is not implemented (see [docs/references.md](docs/references.md)).

## Install (from a clone)

```bash
git clone <repository-url> && cd zooarchpy
uv venv --python 3.11 && uv pip install -e ".[dev]"    # or: python -m venv .venv && pip install -e ".[dev]"
pytest && ruff check . && mypy
```

Requires Python ≥ 3.11. The core has **no runtime dependencies**.

## Example

Using the fictional file [examples/fictional_fauna.csv](examples/fictional_fauna.csv):

```python
from zooarchpy import Assemblage

fauna = Assemblage.from_csv("examples/fictional_fauna.csv")   # fictional data
print(fauna.validate())                                       # errors and warnings
print(fauna.nisp(group_by="taxon"))
```

```text
WARNING ambiguous_taxon: 'Ovis/Capra' is an ambiguous identification (1 rows); it is kept as its own category and never merged automatically
taxon           nisp
Bos taurus      4
Capra hircus    1
Mammalia        6
Ovis aries      3
Ovis/Capra      3
Sus domesticus  1
warning: ambiguous categories kept separate, not merged into other taxa: ['Ovis/Capra']
```

Other calls:

```python
print(fauna.nsp())                                            # identified 18, unidentified 12, total 30
result = fauna.nisp(group_by=["context", "taxon"], percent=["context"])
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
