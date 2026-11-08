import json

import pytest

from conftest import spec
from zooarchpy import Assemblage, DataQualityError, TaxonomyPolicy


def by_taxon(result):
    return {r["taxon"]: r["nisp"] for r in result}


def test_three_specimens_give_nisp_three():
    a = Assemblage([spec("1"), spec("2"), spec("3")], rows_are_specimens=True)
    assert by_taxon(a.nisp()) == {"Bos taurus": 3}


def test_count_column_is_respected():
    a = Assemblage([spec("1", count=4), spec("2", count=2)])
    assert by_taxon(a.nisp()) == {"Bos taurus": 6}


def test_row_without_count_is_not_assumed_to_be_one_specimen():
    a = Assemblage([spec("1", count=2), spec("2")])
    res = a.nisp()
    assert by_taxon(res) == {"Bos taurus": 2}
    assert res.metadata["exclusions"]["count not recorded"]["rows"] == 1


def test_unidentified_excluded_from_nisp_but_counted_in_nsp():
    a = Assemblage([spec("1", count=3), spec("2", taxon=None, count=5)])
    assert by_taxon(a.nisp()) == {"Bos taurus": 3}
    assert a.nisp().metadata["exclusions"]["unidentified"]["specimens"] == 5
    nsp = a.nsp().rows[0]
    assert (nsp["identified"], nsp["unidentified"], nsp["total"]) == (3, 5, 8)


def test_ambiguous_taxa_are_never_merged():
    a = Assemblage(
        [spec("1", "Ovis/Capra", count=2), spec("2", "Ovis aries", count=1),
         spec("3", "Capra hircus", count=1)]
    )  # fmt: skip
    res = a.nisp()
    assert by_taxon(res) == {"Capra hircus": 1, "Ovis aries": 1, "Ovis/Capra": 2}
    assert any("Ovis/Capra" in w for w in res.warnings)
    assert by_taxon(a.nisp(ambiguous="exclude")) == {"Capra hircus": 1, "Ovis aries": 1}


def test_custom_ambiguous_label_and_explicit_taxon_map():
    pol = TaxonomyPolicy(ambiguous_taxa=frozenset({"Caprinae"}))
    a = Assemblage([spec("1", "Caprinae", count=2), spec("2", "Ovis aries", count=1)], taxonomy=pol)
    assert by_taxon(a.nisp(ambiguous="exclude")) == {"Ovis aries": 1}
    merged = a.nisp(taxon_map={"Ovis aries": "Caprinae"})
    assert by_taxon(merged) == {"Caprinae": 3}
    assert merged.metadata["parameters"]["taxon_map"] == {"Ovis aries": "Caprinae"}


def test_min_rank_requires_recorded_rank():
    a = Assemblage(
        [spec("1", "Ovis aries", taxon_rank="species", count=1),
         spec("2", "Mammalia", taxon_rank="class", count=4),
         spec("3", "Bovidae", count=2)]
    )  # fmt: skip
    res = a.nisp(min_rank="genus")
    assert by_taxon(res) == {"Ovis aries": 1}
    ex = res.metadata["exclusions"]
    assert ex["rank less specific than min_rank"]["specimens"] == 4
    assert ex["rank not recorded or unknown"]["specimens"] == 2
    with pytest.raises(ValueError):
        a.nisp(min_rank="nonsense")


def test_taxon_filter():
    a = Assemblage([spec("1", count=2), spec("2", "Sus domesticus", count=1)])
    assert by_taxon(a.nisp(taxon="Sus domesticus")) == {"Sus domesticus": 1}


def test_grouping_and_percent_within_group(example):
    res = example.nisp(group_by=["context", "taxon"], percent=["context"])
    ctx101 = [r for r in res if r["context"] == "CTX-101"]
    assert sum(r["nisp"] for r in ctx101) == 4 + 3 + 1
    assert sum(r["percent"] for r in ctx101) == pytest.approx(100)
    assert sum(r["percent"] for r in res if r["context"] == "CTX-102") == pytest.approx(100)


def test_group_by_phase_and_site(example):
    assert {r["phase"]: r["nisp"] for r in example.nisp("phase")} == {"Phase 1": 8, "Phase 2": 10}
    assert example.nisp("site").rows == [{"site": "FICTIONAL-SITE", "nisp": 18}]


def test_example_values_match_hand_count(example):
    assert by_taxon(example.nisp()) == {
        "Bos taurus": 4, "Capra hircus": 1, "Mammalia": 6,
        "Ovis aries": 3, "Ovis/Capra": 3, "Sus domesticus": 1,
    }  # fmt: skip
    assert example.nsp().rows[0]["total"] == 18 + 12  # identified + unidentified


def test_invariant_partition_sums_to_total(example):
    total = sum(example.nisp().column("nisp"))
    for field in ("context", "phase", "element", "side"):
        assert sum(example.nisp(field).column("nisp")) == total


def test_percent_sums_to_100(example):
    assert sum(example.nisp(percent=True).column("percent")) == pytest.approx(100)


def test_missing_group_values_stay_missing_and_sort_last(example):
    res = example.nisp("side")
    assert res.column("side")[-1] is None


def test_validation_errors_block_by_default():
    a = Assemblage([spec("1", count=1), spec("1", count=1)])
    with pytest.raises(DataQualityError):
        a.nisp()
    res = a.nisp(allow_errors=True)
    assert by_taxon(res) == {"Bos taurus": 2}
    assert any("validation error" in w for w in res.warnings)


def test_invalid_group_field():
    with pytest.raises(ValueError):
        Assemblage([spec("1")], rows_are_specimens=True).nisp("colour")


def test_reproducible_table(example):
    assert example.nisp(["context", "taxon"]).rows == example.nisp(["context", "taxon"]).rows


def test_metadata_and_exports(example, tmp_path):
    res = example.nisp("taxon", percent=True)
    assert res.metadata["zooarchpy_version"]
    assert "not a number of animals" in res.metadata["interpretation"]
    res.to_csv(tmp_path / "n.csv")
    lines = (tmp_path / "n.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "taxon,nisp,percent"
    res.to_json(tmp_path / "n.json")
    data = json.loads((tmp_path / "n.json").read_text(encoding="utf-8"))
    assert data["metadata"]["method"] == "nisp" and len(data["rows"]) == 6
    assert "Bos taurus" in str(res)
