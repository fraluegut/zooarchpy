"""Checks on the packaged skeleton SVG template.

An SVG is plain XML, so a malformed file (for example ``--`` inside a comment) breaks every
consumer. Parsing it in a test catches that before release. The tests also enforce the
contract documented in the file: one ``<g class="bone">`` per element, with a matching id.
"""

import csv
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = Path(__file__).parents[1] / "src/zooarchpy/data/skeletons/generic_ungulate_lateral.svg"


def _bones() -> list[ET.Element]:
    root = ET.parse(SVG).getroot()
    return [g for g in root.iter("{http://www.w3.org/2000/svg}g") if g.get("class") == "bone"]


def test_svg_is_well_formed_and_has_bones() -> None:
    assert len(_bones()) >= 20


def test_ids_are_unique_and_match_data_element() -> None:
    ids = [g.get("id") for g in _bones()]
    assert len(ids) == len(set(ids))
    for g in _bones():
        element = g.get("data-element")
        assert element, f"{g.get('id')} has no data-element"
        # Paired fore/hind duplicates (e.g. phalanx) may add a suffix after the element label.
        assert (g.get("id") or "").startswith(f"el-{element}")


def test_no_hard_coded_colours_on_shapes() -> None:
    for g in _bones():
        for shape in g:
            assert shape.get("fill") is None and shape.get("stroke") is None


def test_covers_elements_used_in_example_data() -> None:
    examples = Path(__file__).parents[1] / "examples/fictional_fauna.csv"
    with examples.open(newline="", encoding="utf-8") as fh:
        used = {row["element"] for row in csv.DictReader(fh) if row["element"]}
    # Indeterminate categories are not anatomical elements and must not be drawn on a bone.
    indeterminate = {"long bone shaft"}
    available = {g.get("data-element") for g in _bones()}
    missing = used - indeterminate - available
    assert not missing, f"missing in template: {sorted(missing)}"
