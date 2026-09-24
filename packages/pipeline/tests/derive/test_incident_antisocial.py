"""Recorded anti-social behaviour is counted as recorded criminal damage is, of its own kind.

Nothing here is real. The zip and the town are made up: `incident_support.py`
says how. `test_incident_criminal_damage.py` holds the counting.
"""

from pathlib import Path

from burro_core.catalogue import FEATURES
from burro_pipeline.cells import spine
from burro_pipeline.derive import incident_antisocial, incident_criminal_damage
from burro_pipeline.derive.measures import says_what_core_says
from burro_pipeline.evidence.row import State

from .incident_support import ONE, THREE, TWO, inputs_with


def test_it_counts_its_own_kind_and_no_other(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    made = incident_antisocial.build(inputs, spine.build(inputs))
    assert {area: made.placed.count(area) for area in (ONE, TWO, THREE)} == {
        ONE: 0,
        TWO: 0,
        THREE: 6 * 36,
    }
    # 216 records in three years is 72 a year. Over 820 homes that is 87.8 for each 1,000.
    assert made.worked[THREE].value == 87.8
    assert {one.state for one in made.worked.values()} == {State.PRESENT}


def test_the_name_and_the_unit_are_cores_so_a_build_carries_the_measure(tmp_path: Path):
    inputs = inputs_with(tmp_path)
    made = incident_antisocial.build(inputs, spine.build(inputs))
    core = FEATURES[incident_antisocial.FEATURE]
    assert made.metric.label == core.label == "Recorded anti-social behaviour"
    assert made.metric.unit == core.unit == "per 1,000 homes a year"
    assert says_what_core_says(made.metric)


def test_it_reads_the_zip_the_other_measure_reads():
    assert incident_antisocial.SOURCE == incident_criminal_damage.SOURCE
    assert incident_antisocial.METHODS == incident_criminal_damage.METHODS
    assert incident_antisocial.is_the_zip("a-name-the-form-made.zip")
    assert not incident_antisocial.is_the_zip("File_8_made_up.xlsx")
