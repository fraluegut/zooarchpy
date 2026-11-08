# ZooArchPy

Verifiable quantitative zooarchaeology for Python. The aim is a library whose results can
be cited in a methods section: explicit policies, no silent assumptions, every result
carrying the method and warnings that produced it.

**Status: pre-alpha, Phase 1 (MVP).** Implemented: `Specimen` model, `Assemblage`, CSV
import, structured validation, NR/NSP, NISP (+ percentages, grouping by site / context /
phase / taxon / element...), zone-based MNE, conservative sided-element MNI, CSV and JSON
export. MAU, mortality, taphonomy, biometry and diversity are planned (see [docs/roadmap.md](docs/roadmap.md)).

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
- MNI and MNE refuse to run until you declare the aggregation unit and that each count is
  a distinct element, because they change with both. MNE also requires you to name the
  zone scheme: the library contains no zone tables.

## Documentation

[docs/design.md](docs/design.md) · [docs/nisp.md](docs/nisp.md) · [docs/mne.md](docs/mne.md) · [docs/mni.md](docs/mni.md) ·
[docs/roadmap.md](docs/roadmap.md) · [docs/references.md](docs/references.md) ·
[CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT. See [LICENSE](LICENSE). Cite via [CITATION.cff](CITATION.cff).
