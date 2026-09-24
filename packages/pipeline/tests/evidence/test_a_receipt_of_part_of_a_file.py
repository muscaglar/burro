"""A receipt of part of a file says which part: the file, the row groups and the bytes.

Every value here is made up. No file was fetched and none is read.
"""

import hashlib
import json
from typing import Any

import pytest
from burro_pipeline.evidence.receipt import Receipt
from burro_pipeline.evidence.record import file_id_of, in_words
from burro_pipeline.release import canonical_json
from pydantic import ValidationError

from .examples import RECEIPT

SHA = hashlib.sha256(b"a made-up part").hexdigest()
# A part of a made-up file of 10,000 bytes and 8 row groups: the four letters it starts
# with, two columns of row groups 2 and 3, and its footer.
TAKEN: dict[str, Any] = {
    "of_bytes": 10_000,
    "box": [2.3, 53.0, 2.7, 54.0],
    "box_in": "bbox",
    "columns": ["bbox", "geometry"],
    "of_row_groups": 8,
    "row_groups": [2, 3],
    "of_rows": 800,
    "rows": 200,
    "runs": [[0, 4], [2_000, 300], [2_600, 100], [3_000, 400], [9_000, 1_000]],
}


def fetched(**changes: Any) -> dict[str, Any]:
    real = {
        "file_id": file_id_of(SHA),
        "sha256": SHA,
        "source_id": "made-up-places",
        "how": "fetched",
        "url": "https://data.example.org/release/1/places.parquet",
        "publisher_file": "places.parquet",
        "bytes": 1_804,
        "taken": TAKEN,
    }
    return RECEIPT.model_dump(mode="json") | real | changes


def part(**changes: Any) -> dict[str, Any]:
    return fetched(taken=TAKEN | changes)


def refusal(fields: dict[str, Any]) -> str:
    with pytest.raises(ValidationError) as caught:
        Receipt.model_validate(fields)
    return in_words(caught.value)


def test_a_receipt_of_a_part_says_which_file_which_row_groups_and_which_bytes():
    receipt = Receipt.model_validate(fetched())
    assert receipt.taken is not None
    assert receipt.url == "https://data.example.org/release/1/places.parquet"
    assert (receipt.taken.of_bytes, receipt.taken.of_row_groups) == (10_000, 8)
    assert receipt.taken.row_groups == (2, 3)
    assert receipt.taken.runs == ((0, 4), (2_000, 300), (2_600, 100), (3_000, 400), (9_000, 1_000))
    assert receipt.bytes == sum(count for _, count in receipt.taken.runs)


def test_it_is_written_one_way_and_reads_back_the_same():
    receipt = Receipt.model_validate(fetched())
    written = receipt.canonical()
    assert written == canonical_json(json.loads(written))
    assert json.loads(written)["taken"] == TAKEN
    assert Receipt.model_validate_json(written) == receipt


def test_a_receipt_of_a_whole_file_is_written_as_it_was_before_the_field():
    """So every receipt written before reads back as the same record, with the same hash."""
    whole = Receipt.model_validate(fetched(taken=None))
    assert whole.taken is None
    assert "taken" not in json.loads(whole.canonical())
    before = canonical_json({k: v for k, v in fetched().items() if k != "taken"})
    assert Receipt.model_validate_json(before).canonical() == before
    assert "taken" not in RECEIPT.model_dump(mode="json")
    assert Receipt.model_validate(fetched()) != whole


def test_the_bytes_of_the_part_are_the_bytes_of_its_runs():
    assert "as many bytes as its runs" in refusal(fetched(bytes=1_805))
    assert "as many bytes as its runs" in refusal(
        part(of_bytes=10_001, runs=[[0, 4], [9_000, 1_001]])
    )


def test_only_a_file_that_code_fetched_is_taken_in_part():
    said = refusal(fetched(how="by_hand"))
    assert "only a file that was fetched" in said
    made_up = RECEIPT.model_dump(mode="json") | {"taken": TAKEN}
    assert "only a file that was fetched" in refusal(made_up)


@pytest.mark.parametrize(
    ("changed", "said"),
    [
        ({"runs": []}, "at least 1"),
        ({"runs": [[4, 1_796], [9_000, 4]]}, "starts with the start of the file"),
        ({"runs": [[0, 4], [2_000, 800], [8_999, 1_000]]}, "ends with the end of the file"),
        (
            {"runs": [[0, 4], [2_000, 300], [2_300, 500], [9_000, 1_000]]},
            "in the order of the file",
        ),
        (
            {"runs": [[0, 4], [3_000, 400], [2_000, 400], [9_000, 1_000]]},
            "in the order of the file",
        ),
        (
            {"runs": [[0, 4], [2_000, 0], [2_600, 800], [9_000, 1_000]]},
            "greater than or equal to 1",
        ),
        ({"runs": [[0, 4], [-5, 800], [9_000, 1_000]]}, "greater than or equal to 0"),
        ({"row_groups": [3, 2]}, "counted from 0, each once"),
        ({"row_groups": [2, 2]}, "counted from 0, each once"),
        ({"row_groups": [2, 8]}, "counted from 0, each once"),
        ({"row_groups": [-1, 2]}, "counted from 0, each once"),
        ({"rows": 801}, "no more rows than the file"),
        ({"row_groups": [], "rows": 5}, "no more rows than the file"),
        ({"columns": []}, "at least 1"),
        ({"columns": ["geometry", "bbox"]}, "in name order, each once"),
        ({"columns": ["bbox", "bbox"]}, "in name order, each once"),
        ({"columns": ["bbox", "geometry", "taxonomy"], "box_in": "box"}, "one of the columns"),
        ({"box": [2.7, 53.0, 2.3, 54.0]}, "from west to east"),
        ({"box": [2.3, 54.0, 2.7, 53.0]}, "from west to east"),
        ({"box": [2.3, 53.0, 2.7]}, "box"),
        ({"box": [2.3, 53.0, 2.7, 91.0]}, "from west to east"),
        ({"box": [2.3000001, 53.0, 2.7, 54.0]}, "six decimal places"),
        ({"colour": "red"}, "holds a field that a record does not have"),
    ],
)
def test_a_part_that_does_not_hold_together_is_refused(changed: dict[str, Any], said: str):
    assert said in refusal(part(**changed))


def test_a_refusal_repeats_nothing_it_was_given():
    said = refusal(part(box_in="Zzyzx Parva", columns=["Zzyzx Parva"]))
    assert "Zzyzx" not in said
