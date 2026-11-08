# Examples

`fictional_fauna.csv` is **entirely fictional**. It was invented to exercise the code
(ambiguous `Ovis/Capra`, a class-level `Mammalia`, an unidentified lot, aggregated counts)
and says nothing about any real site. Do not cite it as data.

Hand-checkable values (identified specimens only): *Bos taurus* 1+1+2 = 4,
*Ovis aries* 1+2 = 3, *Ovis/Capra* 3, *Capra hircus* 1, *Sus domesticus* 1, *Mammalia* 6;
18 identified in all; the unidentified lot adds 12 to NR/NSP (total 30).

```python
from zooarchpy import Assemblage

fauna = Assemblage.from_csv("examples/fictional_fauna.csv")
print(fauna.nisp(group_by=["context", "taxon"], percent=["context"]))
fauna.nisp(group_by="taxon").to_csv("nisp.csv")
```
