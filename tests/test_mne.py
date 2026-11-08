"""MNE tests: tiny assemblages whose answer is checked by hand.

Zone labels (Z1, Z2...) are arbitrary test labels, not a real zone scheme.
"""

import pytest

from conftest import spec
from zooarchpy import Assemblage, DataQualityError, Side

KW = {"aggregate_by": [], "zone_scheme": "test scheme", "counts_are_elements": True}


def piece(sid: str, zones: tuple[str, ...], side: Side | None = Side.LEFT, **kw):
    kw.setdefault("element", "humerus")
    return spec(sid, side=side, diagnostic_zones=zones, count=1, **kw)


def test_mne_is_the_most_frequent_zone():
    # Z1 on 3 specimens, Z2 on 1, Z3 on 2 -> MNE 3 (Z1)
    a = Assemblage([piece("1", ("Z1", "Z3")), piece("2", ("Z1",)), piece("3", ("Z1", "Z2", "Z3"))])
    row = a.mne(**KW).rows[0]
    assert row["mne"] == 3
    assert row["limiting_zones"] == "Z1"
    assert row["zone_counts"] == "Z1=3; Z2=1; Z3=2"


def test_ties_are_all_reported():
    a = Assemblage([piece("1", ("Z1",)), piece("2", ("Z2",))])
    row = a.mne(**KW).rows[0]
    assert (row["mne"], row["limiting_zones"]) == (1, "Z1; Z2")


def test_repeated_zone_on_one_specimen_counts_once():
    a = Assemblage([piece("1", ("Z1", "Z1"))])
    assert a.mne(**KW).rows[0]["mne"] == 1


def test_sides_elements_and_taxa_are_separate_rows():
    a = Assemblage([
        piece("1", ("Z1",), Side.LEFT), piece("2", ("Z1",), Side.RIGHT),
        piece("3", ("Z1",), Side.RIGHT), piece("4", ("Z1",), None),
        piece("5", ("Z1",), element="femur"),
        piece("6", ("Z1",), taxon="Ovis aries"),
    ])  # fmt: skip
    res = a.mne(**KW)
    got = {(r["taxon"], r["element"], r["side"]): r["mne"] for r in res}
    assert got == {
        ("Bos taurus", "humerus", "left"): 1,
        ("Bos taurus", "humerus", "right"): 2,
        ("Bos taurus", "humerus", None): 1,
        ("Bos taurus", "femur", "left"): 1,
        ("Ovis aries", "humerus", "left"): 1,
    }
    assert any("side=None" in w for w in res.warnings)


def test_aggregation_unit_changes_the_result():
    a = Assemblage([piece("1", ("Z1",), context="A"), piece("2", ("Z1",), context="B")])
    assert a.mne(**KW).rows[0]["mne"] == 2
    split = a.mne(**{**KW, "aggregate_by": "context"})
    assert [(r["context"], r["mne"]) for r in split] == [("A", 1), ("B", 1)]


def test_exclusions_are_reported_not_guessed():
    a = Assemblage([
        piece("1", ("Z1",)),
        spec("2", element="humerus", side=Side.LEFT, count=4, diagnostic_zones=("Z1",)),
        spec("3", element="humerus", side=Side.LEFT, count=1),  # no zones
        spec("4", None, element="humerus", diagnostic_zones=("Z1",), count=1),
        spec("5", element=None, diagnostic_zones=("Z1",), count=1),
        spec("6", element="humerus", diagnostic_zones=("Z1",)),  # no count
    ])  # fmt: skip
    res = a.mne(**KW)
    assert [r["mne"] for r in res] == [1]
    ex = res.metadata["exclusions"]
    assert ex["lot with count > 1: zones cannot be assigned to pieces"]["specimens"] == 4
    assert ex["no diagnostic zones recorded"]["rows"] == 1
    assert ex["unidentified"]["rows"] == 1
    assert ex["element not recorded"]["rows"] == 1
    assert ex["count not recorded"]["rows"] == 1


def test_rows_are_specimens_allows_rows_without_count():
    row = spec("1", element="humerus", diagnostic_zones=("Z1",))
    a = Assemblage([row], rows_are_specimens=True)
    assert a.mne(**KW).rows[0]["mne"] == 1


def test_ambiguous_kept_separate_and_taxon_map_explicit():
    a = Assemblage(
        [piece("1", ("Z1",), taxon="Ovis/Capra"), piece("2", ("Z1",), taxon="Ovis aries")]
    )
    res = a.mne(**KW)
    assert {r["taxon"] for r in res} == {"Ovis/Capra", "Ovis aries"}
    assert any("Ovis/Capra" in w for w in res.warnings)
    assert [r["taxon"] for r in a.mne(**KW, ambiguous="exclude")] == ["Ovis aries"]
    merged = a.mne(**KW, taxon_map={"Ovis aries": "Ovis/Capra"})
    assert merged.rows[0]["mne"] == 2


def test_required_declarations():
    a = Assemblage([piece("1", ("Z1",))])
    with pytest.raises(ValueError, match="zone_scheme is required"):
        a.mne(**{**KW, "zone_scheme": "  "})
    with pytest.raises(ValueError, match="different elements"):
        a.mne(**{**KW, "counts_are_elements": False})
    with pytest.raises(ValueError, match="aggregate_by is required"):
        a.mne(**{**KW, "aggregate_by": None})
    with pytest.raises(ValueError, match="only method='zones'"):
        a.mne(**KW, method="other")
    with pytest.raises(ValueError, match="cannot aggregate by"):
        a.mne(**{**KW, "aggregate_by": "side"})
    with pytest.raises(TypeError):
        a.mne(aggregate_by=[], counts_are_elements=True)  # type: ignore[call-arg]


def test_metadata_records_scheme_and_validation_is_enforced():
    a = Assemblage([piece("1", ("Z1",)), piece("1", ("Z1",), Side.RIGHT)])
    with pytest.raises(DataQualityError):
        a.mne(**KW)
    res = a.mne(**KW, allow_errors=True)
    assert res.metadata["parameters"]["zone_scheme"] == "test scheme"
    assert "lower bound" in res.metadata["interpretation"]
