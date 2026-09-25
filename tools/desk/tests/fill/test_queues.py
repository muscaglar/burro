"""Each queue, filled from the synthetic release: how many items, which come first, and why.

The counts and the first three of each queue are held here. A change to the generator of
the made-up draft, or to the order of a queue, shows in this file and nowhere else.
"""

import json
from collections import Counter
from itertools import pairwise
from typing import Any

import pytest
from desk.fill import draft, synthetic

from .conftest import RELEASE, Filled

QUESTIONS = json.loads(draft.QUESTIONS.read_text(encoding="utf-8"))["queues"]
ANSWERS = {queue["id"]: [answer["code"] for answer in queue["answers"]] for queue in QUESTIONS}

# The queue, how many items it holds, and its first three.
HELD = (
    (
        "rules",
        5,
        [
            "two_made_up_publishers_write_it",
            "a_made_up_smaller_place",
            "named_for_a_made_up_building",
        ],
    ),
    ("claims", 10, ["syn-c18cce26883e3", "syn-ce4ad9316728b", "syn-c9eaed75b43d8"]),
    ("borders", 24, ["syn-n0017", "syn-n0020", "syn-n0003"]),
    ("names", 37, ["n:syn-n0020", "n:syn-n0003", "n:syn-n0006"]),
    ("articles", 30, ["syn-n0003:syn-q0003", "syn-n0006:syn-q0006", "syn-n0017:syn-q0017"]),
    ("whole", 3, ["quillhaven", "east-quillhaven", "south-quillhaven"]),
    ("sentences", 25, ["syn-page-4021:1", "syn-page-4021:2", "syn-page-4021:3"]),
    ("ratings", 192, ["syn-n0003:homes", "syn-n0003:built_age", "syn-n0003:pace"]),
    (
        "figures",
        138,
        ["syn-n0005:green_cover", "syn-n0018:homes_density", "syn-n0002:venue_food_drink"],
    ),
    ("kinds", 118, ["syn-v0012", "syn-v0008", "syn-v0009"]),
    ("know", 3, ["east-quillhaven", "quillhaven", "south-quillhaven"]),
    ("commons", 6, ["c:gorsebeck-forest", "c:alderwick-common", "c:larkspur-heath"]),
)


@pytest.mark.parametrize(("queue", "count", "first"), HELD, ids=[row[0] for row in HELD])
def test_a_queue_holds_as_many_items_as_before_and_begins_with_the_same_three(
    made_up: Filled, queue: str, count: int, first: list[str]
):
    assert made_up.header(queue)["count"] == count == len(made_up.items(queue))
    assert made_up.ids(queue)[:3] == first


# Names


def shown(item: dict[str, Any]) -> dict[str, str]:
    return {line["label"]: line["value"] for line in item["lines"]}


def test_every_name_says_which_answer_the_draft_proposes(made_up: Filled):
    # The page marks it, and one key takes it, whichever of the five it is.
    for item in made_up.items("names"):
        proposed = item["preset"]["proposed"]
        assert proposed in ANSWERS["names"], item["id"]
        assert (proposed == "area") == item["id"].startswith("n:"), item["id"]
        said = shown(item)["Proposed as"]
        assert said.startswith(draft.TIERS[proposed]) if proposed != "area" else said == "An area"
    kinds = Counter(item["preset"]["proposed"] for item in made_up.items("names"))
    assert set(kinds) == {"area", "same_ground", "inside", "wide"}


def in_runs(values: list[str]) -> list[str]:
    """Each value once, in the order its run begins. A value with two runs is there twice."""
    return [value for at, value in enumerate(values) if at == 0 or values[at - 1] != value]


def test_in_a_borough_every_name_proposed_as_an_area_comes_before_any_other_name(
    made_up: Filled,
):
    # Borders are drafted from the names of areas alone. So they are read first in each
    # borough, and a sitting in Names moves the milestone from its first item.
    held = made_up.items("names")
    for group in {item["group"] for item in held}:
        kinds = [item["id"][:2] for item in held if item["group"] == group]
        assert in_runs(kinds) in (["n:", "a:"], ["n:"]), group
    kinds = [item["id"][:2] for item in held]
    assert kinds.count("n:") == 24 and kinds.count("a:") == 13


def test_names_are_read_borough_by_borough_so_that_a_borough_is_finished(made_up: Filled):
    # Every name of a borough is read before the next borough begins, the other names
    # among them. Once all the areas of London came first, and after two hours of names
    # no borough was finished.
    groups = [item["group"] for item in made_up.items("names")]
    assert in_runs(groups) == sorted(set(groups))
    assert len(set(groups)) == 3


def test_within_a_borough_the_flagged_names_come_first(made_up: Filled):
    for kind in ("n:", "a:"):
        held = [item for item in made_up.items("names") if item["id"].startswith(kind)]
        for group in {item["group"] for item in held}:
            flagged = [bool(item["flags"]) for item in held if item["group"] == group]
            assert flagged == sorted(flagged, reverse=True), (kind, group)
    assert sum(bool(item["flags"]) for item in made_up.items("names")) == 6


def test_a_name_that_one_publisher_writes_shows_one_publisher(made_up: Filled):
    flagged = [item for item in made_up.items("names") if "one_publisher" in item["flags"]]
    assert len(flagged) == 4
    for item in flagged:
        publishers = {line["source_id"] for line in item["lines"] if line["source_id"]}
        assert len(publishers) == 1, item["id"]


def test_a_name_put_forward_as_an_area_says_that_the_area_has_ground(made_up: Filled):
    # An answer that turns such a name down is set aside when a build's files are made.
    # The item says so, for the page to say it before the answer is given.
    for item in made_up.items("names"):
        holds = item["preset"].get("holds")
        assert holds == ("cells" if item["id"].startswith("n:") else None), item["id"]


def test_a_record_is_labelled_with_its_publisher_and_not_with_an_id(made_up: Filled):
    # An item flagged for one publisher once showed two ids, both of one publisher.
    shown = [
        line for item in made_up.items("names") for line in item["lines"][1:] if line["source_id"]
    ]
    assert len(shown) > 40
    for line in shown:
        of = line["source_id"].removeprefix("synthetic-")
        assert line["label"] == f"Made-up publisher of {of}", line
    figure = made_up.items("figures")[0]
    assert ("Source", "Made up", "synthetic") in [
        (line["label"], line["value"], line["source_id"]) for line in figure["lines"]
    ]


def test_a_name_offers_each_spelling_a_source_wrote_and_no_other(made_up: Filled):
    item = made_up.item("names", "n:syn-n0004")
    assert item["picks"] == ["Dulcimer Green", "Dulcimer green"]
    assert item["preset"] == {
        "of": [],
        "pick": "Dulcimer Green",
        "proposed": "area",
        "holds": "cells",
    }
    assert made_up.item("names", "n:syn-n0001")["preset"] == {
        "of": [],
        "pick": "Alderwick",
        "proposed": "area",
        "holds": "cells",
        "fits": "two_made_up_publishers_write_it",
    }
    written = {line["value"].split(". It gives")[0] for line in item["lines"][1:]}
    assert written == set(item["picks"])
    for each in made_up.items("names"):
        assert 1 <= len(each["picks"]) <= 5 and each["picks"][0] == each["preset"]["pick"]


def test_every_tier_of_the_areas_design_is_proposed_for_some_name(made_up: Filled):
    tiers = ("An area", *draft.TIERS.values())
    proposed = Counter(
        next(tier for tier in tiers if shown(item)["Proposed as"].startswith(tier))
        for item in made_up.items("names")
    )
    assert proposed == {
        "An area": 24,
        "Another name for": 4,
        "A smaller place inside": 8,
        "A wider name, over": 1,
    }


def test_a_name_over_several_areas_is_one_item_that_names_five_at_most(made_up: Filled):
    item = made_up.item("names", "a:syn-n0009:quillhaven-waterside")
    assert item["preset"]["of"] == ["syn-n0009", "syn-n0010", "syn-n0011", "syn-n0019"]
    assert shown(item)["Proposed as"].startswith("A wider name, over Grapnel Dock, ")
    assert len(item["lines"]) == 2, "a record for each area is said once"
    assert all(len(each["preset"]["of"]) <= 5 for each in made_up.items("names"))


def test_the_same_name_in_two_places_is_two_items_and_each_says_so(made_up: Filled):
    twice = [item for item in made_up.items("names") if item["picks"] == ["Pellam"]]
    assert [item["id"] for item in twice] == ["a:syn-n0003:pellam", "a:syn-n0018:pellam"]
    assert all("same_name_elsewhere" in item["flags"] for item in twice)
    assert {item["group"] for item in twice} == {"east-quillhaven", "quillhaven"}


def test_a_name_is_shown_where_a_record_puts_it(made_up: Filled):
    item = made_up.item("names", "a:syn-n0007:foxholt-market")
    assert item["map"]["focus"]["area"] == "syn-n0007"
    west, south, east, north = item["map"]["bbox"]
    x, y = item["map"]["focus"]["at"]
    assert west < x < east and south < y < north


# Borders, and whole boroughs


def test_every_flag_of_the_areas_design_is_on_some_border(made_up: Filled):
    flags = Counter(flag for item in made_up.items("borders") for flag in item["flags"])
    assert flags == {"margin_under_10": 6, "least_compact": 1, "two_boroughs": 1, "two_centres": 1}


def test_borders_are_read_borough_by_borough_so_that_a_borough_is_finished(made_up: Filled):
    groups = [item["group"] for item in made_up.items("borders")]
    assert in_runs(groups) == sorted(set(groups)) and len(set(groups)) == 3


def test_within_a_borough_the_most_flagged_borders_come_first(made_up: Filled):
    held = made_up.items("borders")
    for group in {item["group"] for item in held}:
        counts = [len(item["flags"]) for item in held if item["group"] == group]
        assert counts == sorted(counts, reverse=True), group
    assert sorted((len(item["flags"]) for item in held), reverse=True)[:9] == [2, *[1] * 7, 0]


def test_a_border_shows_its_border_cells_with_the_least_margin_first(made_up: Filled):
    item = made_up.item("borders", "syn-n0007")
    assert item["lines"][0]["label"] == "Cells"
    margins = [int(line["value"].split("%")[0].split()[-1]) for line in item["lines"][1:]]
    assert margins == sorted(margins) and margins[0] < draft.UNDER and len(margins) == 6
    assert "second choice Lantern Yard" in item["lines"][1]["value"]
    assert all(line["label"].startswith("syn-oa") for line in item["lines"][1:])


def test_an_area_in_two_boroughs_is_in_the_borough_that_holds_most_of_it(made_up: Filled):
    item = made_up.item("borders", "syn-n0017")
    assert item["flags"] == ["two_boroughs"] and item["group"] == "east-quillhaven"
    cells = made_up.layer("east-quillhaven", "cells")["features"]
    held = Counter(
        c["properties"]["borough"] for c in cells if c["properties"]["area"] == item["id"]
    )
    assert held.most_common()[0][0] == "East Quillhaven" and len(held) == 2


def test_a_whole_borough_is_about_every_area_in_it(made_up: Filled):
    item = made_up.item("whole", "quillhaven")
    assert len(item["map"]["focus"]) == 15 and "boroughs" in item["map"]["layers"]
    assert shown(item)["Areas"] == "15 areas, 6 flagged, 661 cells"
    assert shown(item)["Flagged"].startswith("Alderwick, Eskerfold, Foxholt")


def test_a_borough_is_shown_among_the_others(made_up: Filled):
    items = made_up.items("know")
    assert len({json.dumps(item["map"]["bbox"]) for item in items}) == 1
    outlines = {each["id"] for each in made_up.layer("all", "boroughs")["features"]}
    assert {item["map"]["focus"] for item in items} == outlines
    assert all(item["map"]["layers"] == ["boroughs"] and not item["lines"] for item in items)


# Ratings


def test_a_rating_shows_the_rubric_and_no_score_and_no_band(made_up: Filled):
    for item in made_up.items("ratings"):
        assert [line["label"] for line in item["lines"]] == ["Rate"]
        assert set(item["fill"]) == {"rubric"} and item["fill"]["rubric"].endswith(".")
        assert item["preset"] == dict(zip(("area_id", "vibe"), item["id"].split(":"), strict=True))
        assert not any(character.isdigit() for character in item["lines"][0]["value"])


def test_every_vibe_of_an_area_is_rated_before_the_next_area(made_up: Filled):
    areas = [item["preset"]["area_id"] for item in made_up.items("ratings")]
    assert len(set(areas)) == 24 and len(synthetic.RUBRICS) == 8
    assert areas == [area for area in dict.fromkeys(areas) for _ in range(8)]


def test_no_rubric_uses_the_word_that_the_vibes_design_keeps_out():
    for _, asks, least, most in synthetic.RUBRICS:
        assert "gritty" not in f"{asks} {least} {most}".casefold()


# Names that may say who lives there


def test_a_name_that_holds_a_word_about_who_lives_there_is_flagged_for_the_founder(
    made_up: Filled,
):
    (item,) = [each for each in made_up.items("names") if "Pensioners Row" in each["title"]]
    assert item["flags"] == ["describes_residents"]
    assert item["id"].startswith("a:syn-n0013:") and item["id"].endswith("-pensioners-row")
    assert len(item["picks"]) == 1, "as its publisher writes it, and no other way"
    assert shown(item)["Proposed as"].startswith("A smaller place inside ")


# The map of areas to articles


def test_every_area_is_asked_about_its_own_article_before_any_page_is_fetched(made_up: Filled):
    held = made_up.items("articles")
    own = {item["preset"]["area_id"] for item in held if item["preset"]["role"] == "own"}
    assert own == {
        item["id"].removeprefix("n:") for item in made_up.items("names") if item["id"][0] == "n"
    }
    for item in held:
        assert item["text"] is None and item["map"] is None
        assert [line["label"] for line in item["lines"]] == [
            *("Area", "Article", "Proposed as", "Item", "Page"),
        ]
        assert item["preset"]["proposed"] == "its_article"
        assert set(item["preset"]) == {"area_id", "qid", "page_id", "role", "proposed"}
        assert item["id"] == f"{item['preset']['area_id']}:{item['preset']['qid']}"


def test_an_article_is_shown_by_its_title_and_by_no_word_of_it(made_up: Filled):
    sentences = {item["text"]["body"] for item in made_up.items("sentences")}
    for item in made_up.items("articles"):
        said = " ".join(line["value"] for line in item["lines"])
        assert not any(sentence in said for sentence in sentences), item["id"]


def test_articles_are_read_area_by_area_with_the_areas_own_article_first(made_up: Filled):
    held = made_up.items("articles")
    areas = [item["preset"]["area_id"] for item in held]
    assert len(in_runs(areas)) == len(set(areas)) == 24
    for area in set(areas):
        roles = [
            i["preset"]["role"] for i in held if i["preset"]["area_id"] == area and not i["flags"]
        ]
        assert roles == sorted(roles, key=list(draft.ROLES).index), area


def test_an_article_that_two_areas_claim_is_flagged_in_both(made_up: Filled):
    claimed = [item for item in made_up.items("articles") if item["flags"] == ["two_areas"]]
    assert len(claimed) == 2 and len({item["preset"]["qid"] for item in claimed}) == 1
    assert len({item["preset"]["area_id"] for item in claimed}) == 2
    unsure = [item for item in made_up.items("articles") if item["flags"] == ["unsure_match"]]
    assert [item["preset"]["role"] for item in unsure] == ["thing"]


# Claims and sentences


@pytest.mark.parametrize("queue", ["claims", "sentences"])
def test_an_item_is_planted_for_every_answer_of_the_queue(made_up: Filled, queue: str):
    planted = dict(synthetic.planted(queue))
    assert set(planted) == set(made_up.ids(queue))
    assert set(planted.values()) == set(ANSWERS[queue])


def test_a_claim_shows_the_words_and_the_sentence_each_side(made_up: Filled):
    item = made_up.item("claims", "syn-ce4ad9316728b")
    assert item["text"] == {
        "before": "The name comes from an old word for a farm among alder trees.",
        "body": "The market at Foxholt, to the south, is older than the station.",
        "after": "Alderwick is the most sought-after address in Quillhaven.",
    }
    assert item["flags"] == ["names_another_area"] and item["group"] == "alderwick"
    assert shown(item)["Address"] == "None. The page is made up"


def test_a_claim_the_source_gives_no_reference_for_is_flagged(made_up: Filled):
    flagged = {item["id"] for item in made_up.items("claims") if "no_reference" in item["flags"]}
    assert flagged == {"syn-c18cce26883e3", "syn-c728940eca0e4"}


def test_claims_are_read_area_by_area_so_that_an_area_is_finished_and_can_ship(made_up: Filled):
    # An area ships as soon as its own claims are read: researcher, section 8.
    areas = [shown(item)["Area"] for item in made_up.items("claims")]
    assert in_runs(areas) == sorted(set(areas)) and len(set(areas)) == 3


def test_within_an_area_the_flagged_claims_come_first(made_up: Filled):
    held = made_up.items("claims")
    for area in {shown(item)["Area"] for item in held}:
        flagged = [bool(item["flags"]) for item in held if shown(item)["Area"] == area]
        assert flagged == sorted(flagged, reverse=True), area
    assert sum(bool(item["flags"]) for item in held) == 3


def test_a_made_up_claim_is_a_claim_as_the_pipeline_holds_one(made_up: Filled):
    from burro_pipeline.evidence.claim import Claim

    rows = draft.read_lines(made_up.data / "draft", "claims.jsonl")
    assert len(rows) == 10
    for row in rows:
        assert Claim.model_validate(row).claim_id == row["claim_id"]


def test_sentences_are_read_article_by_article_in_the_order_they_stand(made_up: Filled):
    items = made_up.items("sentences")
    assert [item["group"] for item in items] == ["alderwick"] * 8 + ["foxholt"] * 11 + [
        "kindlewharf"
    ] * 6
    for before, item in pairwise(items):
        if before["group"] == item["group"]:
            assert item["text"]["before"] == before["text"]["body"]
            assert before["text"]["after"] == item["text"]["body"]
    assert items[0]["text"]["before"] == "" and items[-1]["text"]["after"] == ""
    assert items[0]["preset"] == {"page_id": 4021, "revision_id": 88213, "sentence": 1}


def test_a_made_up_sentence_names_the_made_up_city_alone(made_up: Filled):
    names = {area.name for area in synthetic.city_of(synthetic.release_in(RELEASE)).areas.values()}
    for item in made_up.items("sentences"):
        capitals = {
            word.strip(".,") for word in item["text"]["body"].split()[1:] if word[0].isupper()
        }
        known = {word for name in (*names, "Quillhaven", "Foxholte") for word in name.split()}
        assert capitals <= known | {"Primary", "School", "Studios", "Market"}, item["id"]


# Figures


def test_a_figure_with_no_evidence_comes_before_any_other(made_up: Filled):
    first = [item["flags"][0] for item in made_up.items("figures")]
    assert first == sorted(first, key=draft.RULES.index)
    assert Counter(first) == {
        "no_evidence": 2,
        "moved_between_releases": 3,
        "far_from_neighbours": 129,
        "zero_thin_cover": 4,
    }


def test_a_figure_is_shown_with_the_same_figure_in_each_neighbour(made_up: Filled):
    item = made_up.item("figures", "syn-n0002:venue_food_drink")
    assert item["title"] == (
        "Places to eat and drink within 800 m of home, in a straight line, Brackenhythe (made up)"
    )
    assert shown(item) == {
        # A count is said by its number: the name of the measure says what is counted.
        "Figure": "24.5",
        "The release before": "14.7",
        "Source": "Made up",
        "Date of the data": "2025",
        "Beside it: Hollinsworth Quay": "84.3",
        "Beside it: Larkspur Hill": "26.4",
    }


def test_the_made_up_draft_says_of_a_figure_what_the_coverage_report_says(made_up: Filled):
    # The draft is made with Python alone, so it works out `partial` from the release.
    # This holds what it works out to the report the pipeline writes.
    from burro_pipeline.evidence.coverage import cover
    from burro_pipeline.evidence.row import FULLY_COVERED, State
    from burro_pipeline.release import read_release

    assert synthetic.FULLY_COVERED == FULLY_COVERED and State.PARTIAL == draft.SAYS_THIN
    report = cover(read_release(synthetic.release_in(RELEASE)))
    planted = set(synthetic.NO_RECORD)
    rows = draft.read_table(made_up.data / "draft", "figures.csv")
    # Every measure the release carries, in every area.
    assert len(rows) == 24 * 108
    for row in rows:
        cell = report.cell(row["area_id"], f"feature/{row['feature_id']}")
        said = set(row["flag"].split())
        assert (draft.SAYS_THIN in said) == (cell.state is State.PARTIAL)
        assert ("no_record" in said) == ((row["area_id"], row["feature_id"]) in planted)
        assert bool(row["value"]) == cell.has_a_value


# Kinds of venue


def test_each_kind_is_sampled_to_the_size_its_records_ask_for(made_up: Filled):
    held = Counter(row["kind"] for row in draft.read_table(made_up.data / "draft", "kinds.csv"))
    drawn = Counter(item["preset"]["kind"] for item in made_up.items("kinds"))
    assert drawn == {kind: draft.sample_size(records) for kind, records in held.items()}
    assert held["cafe"] == 121 and drawn["cafe"] == 54


def test_the_kinds_the_first_look_found_in_doubt_come_first(made_up: Filled):
    kinds = list(dict.fromkeys(item["group"] for item in made_up.items("kinds")))
    assert kinds[:3] == ["theatre", "community-hall", "hospital"]
    assert set(kinds[3:]) == {"pub", "cafe", "gym", "library"}


def test_within_a_kind_the_doubtful_records_come_first(made_up: Filled):
    for kind in ("theatre", "community-hall", "cafe"):
        doubts = [bool(item["flags"]) for item in made_up.items("kinds") if item["group"] == kind]
        assert doubts == sorted(doubts, reverse=True) and True in doubts, kind


def test_a_record_is_doubted_for_what_the_first_look_found(made_up: Filled):
    by_flag: dict[str, set[str]] = {}
    for item in made_up.items("kinds"):
        for flag in item["flags"]:
            by_flag.setdefault(flag, set()).add(item["title"].split(" Made-up ")[1])
    assert by_flag == {
        "name_says_another_kind": {"Stage School (made up)", "Scout Group (made up)"},
        "one_of_many_records": {"Hospital (made up)"},
        "in_two_kinds": {"Tap (made up)"},
    }


def test_a_record_under_two_kinds_is_asked_about_under_each(made_up: Filled):
    twice = [item for item in made_up.items("kinds") if "in_two_kinds" in item["flags"]]
    assert [item["id"] for item in twice] == ["syn-v0050:pub", "syn-v0050:cafe"]
    assert [item["fill"] for item in twice] == [{"kind": "pub"}, {"kind": "cafe"}]


def test_the_name_of_a_made_up_venue_gives_away_that_it_is_made_up(made_up: Filled):
    for row in draft.read_table(made_up.data / "draft", "kinds.csv"):
        assert " Made-up " in row["name"] and row["record_id"].startswith("syn-v")
        assert row["upstream"].startswith("made-up feed ") and row["source_id"] == "synthetic"


# Commons


def test_a_common_that_is_not_in_the_file_comes_first(made_up: Filled):
    flags = [item["flags"] for item in made_up.items("commons")]
    assert flags == [["no_match"], ["no_way_in"], ["no_name"], [], [], []]
    assert made_up.item("commons", "c:thrushcombe-green")["preset"] == {"record_id": "syn-p0043"}
    assert made_up.item("commons", "c:gorsebeck-forest")["preset"] == {}


def test_a_common_shows_each_match_in_the_file(made_up: Filled):
    item = made_up.item("commons", "c:marrowfen-common")
    assert [line["label"] for line in item["lines"]] == [
        "Marrowfen Common",
        "Marrowfen Common Playing Field",
    ]
    assert item["lines"][0]["value"].startswith("Public Park Or Garden. A way in. Record syn-g")
