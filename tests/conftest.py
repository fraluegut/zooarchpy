from pathlib import Path

import pytest

from zooarchpy import Assemblage, Specimen

EXAMPLE = Path(__file__).parent.parent / "examples" / "fictional_fauna.csv"


@pytest.fixture
def example() -> Assemblage:
    return Assemblage.from_csv(EXAMPLE)


def spec(sid: str, taxon: str | None = "Bos taurus", **kw: object) -> Specimen:
    kw.setdefault("site", "S")
    kw.setdefault("context", "C1")
    return Specimen(specimen_id=sid, taxon=taxon, **kw)  # type: ignore[arg-type]
