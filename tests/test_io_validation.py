import pytest
from conftest import spec

from zooarchpy import Assemblage, DataFormatError, Observation, Side, Specimen, Vocabulary


def write(tmp_path, text):
    p = tmp_path / "f.csv"
    p.write_text(text, encoding="utf-8")
    return p


def codes(report):
    return {i.code for i in report.issues}


def test_reads_example_and_distinguishes_observation_states(example):
    assert len(example) == 10
    by_id = {s.specimen_id: s for s in example}
    assert by_id["F001"].cut_marks is Observation.PRESENT
    assert by_id["F002"].cut_marks is Observation.ABSENT
    assert by_id["F003"].cut_marks is Observation.UNKNOWN
    assert by_id["F007"].cut_marks is Observation.NOT_APPLICABLE
    assert by_id["F009"].side is None and by_id["F001"].side is Side.LEFT


def test_example_validates_with_only_warnings(example):
    report = example.validate()
    assert report.ok
    assert "ambiguous_taxon" in codes(report)


def test_missing_mandatory_column_is_fatal(tmp_path):
    with pytest.raises(DataFormatError, match="context"):
        Assemblage.from_csv(write(tmp_path, "specimen_id,site,count\n1,S,1\n"))


def test_no_count_column_requires_explicit_declaration(tmp_path):
    p = write(tmp_path, "specimen_id,site,context,taxon\n1,S,C,Bos taurus\n2,S,C,Bos taurus\n")
    with pytest.raises(DataFormatError, match="rows_are_specimens"):
        Assemblage.from_csv(p)
    assert sum(Assemblage.from_csv(p, rows_are_specimens=True).nisp().column("nisp")) == 2


def test_bad_cells_are_reported_not_hidden(tmp_path):
    p = write(
        tmp_path,
        "specimen_id,site,context,count,weight_g,side,extra\n"
        "1,S,C,two,5,left,x\n2,S,C,1,-3,up,x\n,S,C,1,1,left,x\n",
    )
    a = Assemblage.from_csv(p)
    assert len(a) == 2  # row without id dropped, loudly
    report = a.validate()
    assert not report.ok
    assert {"unparseable_value", "negative_weight", "missing_required", "unknown_column"} <= codes(
        report
    )
    assert next(i for i in report.issues if i.code == "missing_required").row == 3


def test_invalid_count_values():
    report = Assemblage([spec("1", count=0), spec("2", count=-2)]).validate()
    assert [i.code for i in report.errors] == ["invalid_count", "invalid_count"]


def test_duplicate_ids_and_completeness():
    report = Assemblage([spec("1", count=1), spec("1", count=1, completeness=1.5)]).validate()
    assert {"duplicate_id", "completeness_out_of_range"} <= codes(report)


def test_missing_count_warning_unless_rows_are_specimens():
    assert "missing_count" in codes(Assemblage([spec("1")]).validate())
    assert "missing_count" not in codes(Assemblage([spec("1")], rows_are_specimens=True).validate())


def test_controlled_vocabulary_warns_without_modifying():
    vocab = {"element": Vocabulary.of("element", ["humerus", "femur"])}
    a = Assemblage([spec("1", element="humerus"), spec("2", element="hummerus")],
                   rows_are_specimens=True, vocabularies=vocab)  # fmt: skip
    report = a.validate()
    assert [i.specimen_id for i in report.warnings if i.code == "unrecognized_term"] == ["2"]
    assert a.specimens[1].element == "hummerus"


def test_specimen_requires_provenance():
    with pytest.raises(ValueError):
        Specimen(specimen_id="1", site="", context="C")


def test_validation_does_not_mutate(example):
    before = example.specimens
    example.validate()
    assert example.specimens == before
