"""MNI tests use tiny assemblages whose answer can be checked by hand."""

import pytest

from conftest import spec
from zooarchpy import Assemblage, DataQualityError, Side

KW = {"aggregate_by": [], "counts_are_elements": True}


def sided(sid: str, element: str, side: Side | None, n: int, taxon: str = "Bos taurus", **kw):
    return spec(sid, taxon, element=element, side=side, count=n, **kw)


def by_taxon(result):
    return {r["taxon"]: r["mni"] for r in result}


def test_mni_is_larger_side_of_most_frequent_element():
    # humerus 3L/2R -> 3 ; femur 1L/4R -> 4 ; MNI = 4 (right femur)
    a = Assemblage([
        sided("1", "humerus", Side.LEFT, 3), sided("2", "humerus", Side.RIGHT, 2),
        sided("3", "femur", Side.LEFT, 1), sided("4", "femur", Side.RIGHT, 4),
    ])  # fmt: skip
    row = a.mni(**KW).rows[0]
    assert row["mni"] == 4
    assert row["limiting_elements"] == "femur"
    assert (row["left"], row["right"]) == (1, 4)


def test_ties_are_all_reported():
    a = Assemblage([sided("1", "humerus", Side.LEFT, 2), sided("2", "femur", Side.RIGHT, 2)])
    row = a.mni(**KW).rows[0]
    assert row["mni"] == 2
    assert row["limiting_elements"] == "femur; humerus"


def test_taxa_are_independent_and_ambiguous_ones_stay_separate():
    a = Assemblage([
        sided("1", "femur", Side.LEFT, 2), sided("2", "femur", Side.LEFT, 3, "Ovis/Capra"),
        sided("3", "femur", Side.RIGHT, 1, "Ovis aries"),
    ])  # fmt: skip
    res = a.mni(**KW)
    assert by_taxon(res) == {"Bos taurus": 2, "Ovis aries": 1, "Ovis/Capra": 3}
    assert any("Ovis/Capra" in w for w in res.warnings)
    assert by_taxon(a.mni(**KW, ambiguous="exclude")) == {"Bos taurus": 2, "Ovis aries": 1}


def test_aggregation_unit_changes_the_result():
    a = Assemblage([
        sided("1", "femur", Side.LEFT, 1, context="A"),
        sided("2", "femur", Side.LEFT, 1, context="B"),
    ])  # fmt: skip
    pooled = a.mni(aggregate_by=[], counts_are_elements=True)
    split = a.mni(aggregate_by="context", counts_are_elements=True)
    assert pooled.rows[0]["mni"] == 2
    assert [(r["context"], r["mni"]) for r in split] == [("A", 1), ("B", 1)]
    assert any("not additive" in w for w in split.warnings)


def test_rows_without_usable_side_are_excluded_and_reported():
    a = Assemblage([
        sided("1", "femur", Side.LEFT, 1),
        sided("2", "femur", None, 5),
        sided("3", "vertebra", Side.AXIAL, 7),
        sided("4", "femur", Side.INDETERMINATE, 2),
        spec("5", None, element="femur", side=Side.LEFT, count=9),
        spec("6", element=None, side=Side.LEFT, count=3),
        spec("7", element="femur", side=Side.LEFT),  # no count, rows_are_specimens off
    ])  # fmt: skip
    res = a.mni(**KW)
    assert by_taxon(res) == {"Bos taurus": 1}
    ex = res.metadata["exclusions"]
    assert ex["side not recorded"]["specimens"] == 5
    assert ex["side is axial: not a left/right element"]["specimens"] == 7
    assert ex["side is indeterminate: not a left/right element"]["specimens"] == 2
    assert ex["unidentified"]["specimens"] == 9
    assert ex["element not recorded"]["specimens"] == 3
    assert ex["count not recorded"]["rows"] == 1


def test_taxon_map_is_explicit_and_recorded():
    a = Assemblage([sided("1", "femur", Side.LEFT, 1, "Ovis aries"),
                    sided("2", "femur", Side.RIGHT, 2, "Capra hircus")])  # fmt: skip
    res = a.mni(**KW, taxon_map={"Ovis aries": "Caprinae", "Capra hircus": "Caprinae"})
    assert by_taxon(res) == {"Caprinae": 2}
    assert res.metadata["parameters"]["taxon_map"]["Ovis aries"] == "Caprinae"


def test_must_declare_counts_are_elements_and_aggregation():
    a = Assemblage([sided("1", "femur", Side.LEFT, 1)])
    with pytest.raises(ValueError, match="distinct"):
        a.mni(aggregate_by=[], counts_are_elements=False)
    with pytest.raises(ValueError, match="aggregate_by is required"):
        a.mni(aggregate_by=None, counts_are_elements=True)
    with pytest.raises(ValueError, match="cannot aggregate by"):
        a.mni(aggregate_by="element", counts_are_elements=True)
    with pytest.raises(TypeError):
        a.mni(counts_are_elements=True)  # type: ignore[call-arg]


def test_metadata_and_validation_errors():
    a = Assemblage([sided("1", "femur", Side.LEFT, 1), sided("1", "femur", Side.RIGHT, 1)])
    with pytest.raises(DataQualityError):
        a.mni(**KW)
    res = a.mni(**KW, allow_errors=True)
    assert res.metadata["method"] == "mni"
    assert res.metadata["parameters"]["counts_are_elements"] is True
    assert "lower bound" in res.metadata["interpretation"]
    assert any("validation error" in w for w in res.warnings)
