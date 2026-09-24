"""The questions the desk asks, held to the table of docs/design/desk.md, section 2."""

import json
import re
from pathlib import Path
from typing import Any, cast

import pytest

QUESTIONS = Path(__file__).resolve().parents[2] / "questions.json"

RULE = (
    "Use what you know and what the page shows. Copy no name and no border from a map or a "
    "website. Move a border for the ground, never for who lives there. If you rely on a "
    "document, give its address in the note."
)
# The queue, its question, its answers in key order, its view, what it adds, and whether
# its lines may be published.
DESIGN: tuple[tuple[str, str, tuple[str, ...], str, tuple[str, ...], bool], ...] = (
    (
        "rules",
        "Shall this rule settle what it fits, with no person reading each?",
        ("yes", "no"),
        "text",
        (),
        True,
    ),
    ("know", "How well do you know this borough?", ("well", "a_little", "not"), "map", (), False),
    ("kinds", "Is this a {kind}?", ("yes", "no", "cannot_tell"), "text", (), True),
    (
        "commons",
        "Is this place in the file, with a name and a way in?",
        ("in_file", "no_name_or_way_in", "not_in_file"),
        "text",
        (),
        True,
    ),
    (
        "figures",
        "Does this figure look wrong for this area?",
        ("looks_right", "looks_wrong", "cannot_say"),
        "text",
        (),
        True,
    ),
    (
        "sentences",
        "Is this sentence fit to quote about the place?",
        ("fit", "residents", "safety", "praise", "person", "change_or_price", "not_a_place"),
        "text",
        (),
        False,
    ),
    (
        "names",
        "Is this the name of an area?",
        ("area", "same_ground", "inside", "wide", "drop"),
        "map",
        ("pick",),
        True,
    ),
    ("borders", "Is this boundary right?", ("right", "wrong", "unknown"), "map", ("move",), True),
    (
        "whole",
        "Is anything wrong in this borough?",
        ("right", "wrong", "unknown"),
        "map",
        ("move",),
        True,
    ),
    ("ratings", "{rubric}", ("1", "2", "3", "4", "5", "cannot_say"), "map", (), False),
    (
        "articles",
        "Is this the article about this place?",
        ("its_article", "not_its_article", "cannot_tell"),
        "text",
        (),
        True,
    ),
    (
        "claims",
        "May this be shown as the source's words about this area?",
        ("accept", "not_this_place", "describes_people", "passes_judgement", "not_fair"),
        "text",
        (),
        False,
    ),
)
KEYS = {
    *("id", "version", "title", "text", "rule", "view", "adds"),
    *("after", "open_to", "public", "answers", "flags"),
}
# What each queue waits on, and the queues a reviewer other than the founder is asked to
# work: the second reviewer's half of the borders and sample of the claims, and a rater's
# boroughs and ratings.
AFTER = {
    "names": ["rules"],
    "borders": ["rules", "names"],
    "whole": ["rules", "names"],
    "ratings": ["names"],
    "articles": ["names"],
    "claims": ["articles"],
}
OPEN_TO_ALL = {"know", "borders", "ratings", "claims"}
# The flags the design names, which the areas build and the research run write.
NAMED_FLAGS = {
    "margin_under_10",
    "least_compact",
    "two_boroughs",
    "two_centres",
    "one_publisher",
    "names_another_area",
    "no_reference",
}
# Every flag the areas build raises about a border, and about a name. A flag with no
# words stops the fill, so an area the draft flags would be flagged nowhere at the desk.
OF_A_BORDER = {
    *("margin_under_10", "least_compact", "two_boroughs", "two_centres", "one_publisher"),
    *("seeds_close", "follows_nothing", "size_unlike_neighbours", "two_pieces"),
    *("both_banks", "seed_outside", "no_receipt"),
}
OF_A_NAME = {
    *("one_publisher", "same_name_elsewhere", "describes_residents", "no_receipt"),
    # A name that carries a mark to settle, which the desk shows as a line "Look hard".
    "look_hard",
}


def queues() -> list[dict[str, Any]]:
    held = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    assert held["desk"] == 1
    return cast(list[dict[str, Any]], held["queues"])


def words_of(queue: dict[str, Any]) -> list[str]:
    """Every word of a queue that a person reads."""
    labels = [answer["label"] for answer in queue["answers"]]
    labels += [queue["covers"]["label"]] if "covers" in queue else []
    for held in ("cells", "names"):
        labels += list(queue.get("set_aside", {}).get(held, {}).values())
    moved = queue.get("moved", {"text": queue["text"], "answers": {}})
    after = [moved["text"], *moved["answers"].values()]
    return [queue["title"], queue["text"], queue["rule"], *labels, *queue["flags"].values(), *after]


def test_the_queues_are_those_of_the_design_in_the_order_of_the_work():
    assert [queue["id"] for queue in queues()] == [row[0] for row in DESIGN]
    assert [row[0] for row in DESIGN] == [
        *("rules", "know", "kinds", "commons", "figures", "sentences"),
        *("names", "borders", "whole", "ratings", "articles", "claims"),
    ]


def test_a_name_that_may_say_who_lives_there_has_a_flag_of_its_own():
    # Areas design, section 6: each such name is put to the founder.
    names = next(queue for queue in queues() if queue["id"] == "names")
    assert names["flags"]["describes_residents"] == "the name may say who lives there"


def test_a_queue_says_what_it_waits_on_and_who_works_it():
    for at, queue in enumerate(queues()):
        assert queue["after"] == AFTER.get(queue["id"], []), queue["id"]
        assert queue["open_to"] == ("all" if queue["id"] in OPEN_TO_ALL else "founder")
        before = [each["id"] for each in queues()[:at]]
        assert set(queue["after"]) <= set(before), "a queue comes after what it waits on"


@pytest.mark.parametrize("design", DESIGN, ids=[row[0] for row in DESIGN])
def test_a_queue_asks_the_question_of_the_design_with_its_answers_in_key_order(
    design: tuple[str, str, tuple[str, ...], str, tuple[str, ...], bool],
):
    name, text, codes, view, adds, public = design
    queue = next(queue for queue in queues() if queue["id"] == name)
    more: set[str] = {"moved"} if "move" in adds else {"covers"} if name == "ratings" else set()
    more |= {"set_aside"} if name == "names" else set()
    assert set(queue) == KEYS | more
    assert queue["text"] == text
    assert tuple(answer["code"] for answer in queue["answers"]) == codes
    assert (queue["view"], tuple(queue["adds"]), queue["public"]) == (view, adds, public)
    assert queue["version"] == 1
    assert all(set(answer) == {"code", "label"} for answer in queue["answers"])


def test_the_three_queues_that_draw_a_border_carry_the_reviewers_rule():
    rules = {queue["id"]: queue["rule"] for queue in queues()}
    assert rules["names"] == rules["borders"] == rules["whole"] == RULE


def test_a_queue_that_moves_cells_asks_in_other_words_once_a_cell_is_moved():
    # After a move "Is this boundary right?" reads as "was the draft right?". Both answers
    # apply the move, and only one says the border is now checked.
    for queue in queues():
        if "move" not in queue["adds"]:
            continue
        moved = queue["moved"]
        assert set(moved) == {"text", "answers"}
        assert moved["text"].startswith("With your moves, ")
        assert set(moved["answers"]) == {"right", "wrong"}
        labels = {answer["code"]: answer["label"] for answer in queue["answers"]}
        assert all(moved["answers"][code] != labels[code] for code in ("right", "wrong"))
        assert "now" in moved["answers"]["right"].casefold()
        assert "still" in moved["answers"]["wrong"].casefold()
        assert all(len(label) <= 40 for label in moved["answers"].values())


def test_the_page_is_given_words_for_an_answer_that_a_build_will_set_aside():
    # The desk cannot take the ground from under an area. It saves an answer that turns
    # the name of an area down, and the step that makes a build's files sets it aside.
    # The founder is told at once, and told what to do.
    names = next(queue for queue in queues() if queue["id"] == "names")
    held = names["set_aside"]
    assert set(held) == {"answers", "mark", "cells", "names"}
    assert held["answers"] == ["same_ground", "inside", "wide", "drop"]
    assert set(held["answers"]) == {answer["code"] for answer in names["answers"]} - {"area"}
    for why in ("cells", "names"):
        assert set(held[why]) == {"short", "words", "saved"}
        assert all(words.endswith(".") for words in held[why].values())
        assert len(held[why]["short"]) <= 80
    said = held["cells"]["words"]
    first, again, last = (said.index(each) for each in ("every name", "draft again", "borders"))
    assert first < again < last, "names first, then the draft again, then borders"
    assert [queue["id"] for queue in queues() if "set_aside" in queue] == ["names"]


def test_every_flag_the_design_names_has_its_words():
    held = {code for queue in queues() for code in queue["flags"]}
    assert held >= NAMED_FLAGS


def test_every_flag_the_areas_build_raises_has_its_words():
    flags = {queue["id"]: queue["flags"] for queue in queues()}
    assert set(flags["borders"]) == OF_A_BORDER
    assert set(flags["names"]) == OF_A_NAME
    assert flags["borders"]["seeds_close"] == "its seed is close to the seed of another area"
    assert flags["names"]["no_receipt"] == "it rests on a file that has no receipt"
    assert flags["names"]["look_hard"] == "the draft has a mark on it to settle"


def test_a_whole_borough_has_words_for_every_flag_of_a_border():
    # A borough is flagged with the flags of the areas in it.
    flags = {queue["id"]: queue["flags"] for queue in queues()}
    assert set(flags["whole"]) == set(flags["borders"])
    for code, words in flags["whole"].items():
        assert " here" in words and words != flags["borders"][code], code


def test_a_flag_reads_on_after_the_words_here_because():
    for queue in queues():
        for code, words in queue["flags"].items():
            assert re.fullmatch(r"[a-z][a-z0-9_]*", code), code
            assert words[0].islower() and not words.endswith("."), words


def test_a_flag_is_short_enough_to_read_at_a_glance():
    # The column beside the item is 22rem wide: about forty letters to a line.
    for queue in queues():
        for words in queue["flags"].values():
            assert len(words) <= 70, words


def test_the_words_are_plain():
    for queue in queues():
        for words in words_of(queue):
            assert words.strip() == words and words, queue["id"]
            assert "!" not in words and words.isascii(), words
            assert len(words) <= 220, words
        assert all(len(answer["label"]) <= 40 for answer in queue["answers"]), queue["id"]


def test_a_rating_is_a_number_and_the_rubric_says_what_its_ends_mean():
    # "1 is nearly all houses. 5 is nearly all flats." is no amount: 1 is not "the least".
    ratings = next(queue for queue in queues() if queue["id"] == "ratings")
    labels = [answer["label"] for answer in ratings["answers"]]
    assert labels == ["1", "2", "3", "4", "5", "I cannot say"]
    assert "The rubric says what 1 and 5 mean" in ratings["rule"]


def test_one_answer_says_of_a_whole_area_that_it_is_not_known():
    # A rater knows about 15 areas, and the queue holds every area on eight vibes.
    ratings = next(queue for queue in queues() if queue["id"] == "ratings")
    assert ratings["covers"] == {
        "by": "area_id",
        "code": "cannot_say",
        "label": "I do not know this area",
    }
    assert len(ratings["answers"]) < 9, "the answer for the whole area has a key of its own"


def test_no_question_uses_a_word_that_a_rubric_may_not():
    # docs/design/vibes.md, 6.2: what people call gritty is shaped by who lives there.
    for queue in queues():
        assert "gritty" not in " ".join(words_of(queue)).casefold()
