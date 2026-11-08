# Examples

`fictional_fauna.csv` is **entirely fictional**. It was invented to exercise the code
(ambiguous `Ovis/Capra`, a class-level `Mammalia`, an unidentified lot, aggregated counts)
and says nothing about any real site. Do not cite it as data.

Hand-checkable values (identified specimens only): *Bos taurus* 1+1+2 = 4,
*Ovis aries* 1+2 = 3, *Ovis/Capra* 3, *Capra hircus* 1, *Sus domesticus* 1, *Mammalia* 6;
18 identified in all; the unidentified lot adds 12 to NR/NSP (total 30).

## Fragment examples (for the planned MNE/MNI, not runnable yet)

`fictional_fragments.csv` and `fictional_zone_scheme.csv` illustrate the data contract in the
main [README](../README.md). The zone scheme is **invented** and marked as such in its
`source` column; it is not a published scheme.

What each row of `fictional_fragments.csv` exercises:

| Rows | Case |
|---|---|
| H001–H005 | The worked example: left *Bos taurus* humerus fragments with overlapping zones |
| H006 | Right side: never the same bone as a left one |
| H007 | `Ovis/Capra`: ambiguous label, kept apart from *Bos taurus* unless the researcher decides otherwise |
| H008, H009 | Same `refit_group` (R1): two pieces of the same bone, both scoring `PS`; they count once |
| H010 | `diagnostic_zones` empty = zones not recorded, so it cannot be used |
| H011 | `Mammalia` long bone shaft, no element/side/zones: left out and reported |

Hand-checked expectation for left *Bos taurus* humerus: `PE` 1, `PS` 3 (H001, H004 and the
refit group R1), `MS` 2, `DS` 1, `DE` 2, so **at least 3**. Without using `refit_group`,
`PS` would be 4: the refit changes the result and the metadata must say which was used.

## NISP example

```python
from zooarchpy import Assemblage

fauna = Assemblage.from_csv("examples/fictional_fauna.csv")
print(fauna.nisp(group_by=["context", "taxon"], percent=["context"]))
fauna.nisp(group_by="taxon").to_csv("nisp.csv")
```
