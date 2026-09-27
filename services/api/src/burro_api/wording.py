"""How an offer is worded: what it would do, what follows for areas, and the choices.

The words are the API's, served with the offer, so that the website and the
iPhone app show the same. They are made here from the edits an offer holds
and from the catalogue, and from nothing a person typed: the person's own
words are shown by where they stand, and are never retyped.

An offer has four parts, in this order.

1. What it would do, which begins with a verb. Where Burro has no guess and
   the thing runs more than one way, it is a question. So it is where the
   thing runs one way and something beside it puts the wish in doubt.
2. "You wrote": where the words stand. The client cuts them from the text.
3. What follows for areas: which rank higher, which lower, which are left out.
4. The choices. Doing nothing is "Skip".

What nobody said is said: the way of travelling Burro assumed, which of two
numbers, the tenure. A way that leaves areas out says so on its face, and
recorded crime is chosen under its own name, alone or inside a vibe.

A wish against a thing is never said to be "counted less". What is said is
what happens to areas.

Every part is written for a person who has never seen Burro: in whole
sentences that are joined, which say what follows from what.
"""

from collections.abc import Mapping, Sequence
from typing import NamedTuple

from burro_core.catalogue import CRIME_CAVEAT, FEATURES, HOLDS_CRIME, NEAR_A_STATION, TAGS
from burro_core.facts import (
    MODE_LABELS,
    RENT_CAUTION,
    RENT_IS_OF_A_PLACE,
    SEGMENT_LABELS,
    money,
)
from burro_core.ids import (
    AreaAction,
    Dimension,
    DirectionChoice,
    FeatureId,
    Mode,
    ModeChoice,
    Polarity,
    Provenance,
    Segment,
    SegmentChoice,
    Step,
    StrictnessChoice,
    SuggestionDirection,
    TagId,
    TagShape,
    Tenure,
    TenureChoice,
    TowardChoice,
    WeightAction,
)
from burro_core.interpret import TIME_NOT_PLACED, VISITING, Choice
from burro_core.ops import AreaEdit, BudgetEdit, CommuteEdit, TagEdit, WeightEdit
from burro_core.rank import FIRM_BUDGET_MARGIN_PERCENT, held_on_the_median
from burro_core.reducer import minutes_limit
from burro_core.release import CostEstimate, Release
from burro_core.spec import (
    DEFAULT_COMMUTE_MINUTES,
    DEFAULT_COMMUTE_MODE,
    PreferenceSpec,
    default_spec,
)

from burro_api.offers import IGNORE, Offer, Unsaid, UnsaidCode, Way, holds_crime, in_add_all

__all__ = [
    "AN_AREA_AS_A_WHOLE",
    "GUESS",
    "NOTHING_TAKEN",
    "NO_JOURNEY",
    "NO_LEAST",
    "NO_PLACE",
    "SKIP_LABEL",
    "WHEN",
    "Worded",
    "worded",
]

SKIP_LABEL = "Skip"
# What a client says of the way Burro reads the words. It marks a choice, and applies nothing.
GUESS = "Burro's guess"
COUNTING_CRIME = ", counting recorded crime"
NO_PLACE = "Burro does not know this place: choose one."
NO_JOURNEY = "Burro could not make a journey from these words."
# What is said of any other thing that is noticed and has no way to take: the note of the
# offer says why, as of a home by its bedrooms where prices are held by the kind of home.
NOTHING_TAKEN = "Burro could not use these words in your search."
NO_LEAST = (
    "Burro can only treat a number of minutes as the longest a journey may take. "
    "This means it cannot keep your search away from a place."
)
ANOTHER_WAY = (
    "Burro has assumed public transport. If you travel another way, you can change this "
    "once the journey has been added."
)
# What every vibe cannot see, as an offer of one says it after what the vibe counts. It
# is what the first line of what a vibe cannot see says, in a sentence that follows on.
AN_AREA_AS_A_WHOLE = (
    "It describes an area as a whole, so it cannot tell you about one street or one home."
)
# What is left for a person once one press has added what it may: what they alone may
# choose, and what they may make firmer.
CRIME_BY_NAME = "recorded crime, which Burro adds only when you choose it by name"
MAY_BE_FIRM = "the {thing}, which you can make a firm limit"
# What a firm budget leaves out. Where a price is a range, an area is left out where the
# upper end is over the budget. Where it is a median of what sold, an area is left out only
# where the median is over the budget by more than the margin core holds, and the offer
# says why.
DEARER = "Dearer areas are left out."
# Which areas a firm budget leaves out, as a way of an offer says it on its face.
THAT_COST_MORE = "that cost more"
WHERE_FAR_DEARER = f"where the middle price is more than {FIRM_BUDGET_MARGIN_PERCENT}% over it"
WHERE_FAR_DEARER_TO_RENT = (
    f"where the middle rent is more than {FIRM_BUDGET_MARGIN_PERCENT}% over it"
)
FAR_DEARER = f"Areas {WHERE_FAR_DEARER} are left out."
# The two ways of a budget and of a journey. Each says on its face what it does to areas,
# so that a way that leaves areas out is never pressed for one that does not.
SET_FIRM = "Set it as a firm limit, which leaves out areas {left_out}"
SET_AS_A_GUIDE = "Set it as a guide, which ranks areas lower when they cost more"
ADD_FIRM = "Add it as a firm limit, which leaves out areas that are further away"
ADD_AS_A_GUIDE = "Add it as a guide, which ranks areas lower when they are further away"
HALF_SOLD_FOR_LESS = "About half of the homes sold in an area went for under its middle price."
# The same of a budget to rent, where a rent is of a postcode district or a borough: it is
# held against the middle rent of the place, with the same margin.
FAR_DEARER_TO_RENT = f"Areas {WHERE_FAR_DEARER_TO_RENT} are left out."
HALF_LET_FOR_LESS = "About half of the rents recorded in a place were under its middle rent."
# What a person should know before they set a budget to rent, where a rent is of a wider
# place than an area: that it is, and the caution of its publisher, in plain words.
RENTS_NOTE = f"{RENT_IS_OF_A_PLACE} {RENT_CAUTION}"

_Edit = WeightEdit | TagEdit | CommuteEdit | BudgetEdit | AreaEdit


class Worded(NamedTuple):
    """The words of one offer. Every string is Burro's own."""

    label: str
    does: str
    follows: str
    said: tuple[str, ...]
    # The words of each way, in the order of the offer's choices.
    labels: tuple[str, ...]
    # The way "add all" takes, by its id, or nothing where it takes none.
    add_all: str
    # What is left for the person once "add all" has been pressed, or nothing.
    needs: str
    # What a person should know before they choose: the note of the offer, and of a budget
    # to rent what is said of a rent that is of a wider place than an area.
    note: str = ""


class _Part(NamedTuple):
    """One way of an offer, in words: what it would do, what follows, and its button."""

    does: str
    follows: str
    button: str


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _upper_first(text: str) -> str:
    return text[:1].upper() + text[1:]


def _of_a_home(edits: Sequence[BudgetEdit]) -> tuple[BudgetEdit, ...]:
    """What some edits to a budget say together, as one edit.

    A budget for a house holds the kind in an edit of its own, before the
    amount. It is worded as one thing.
    """
    if len(edits) < 2:
        return tuple(edits)
    whole = edits[0]
    for edit in edits[1:]:
        whole = whole.replace(
            tenure=whole.tenure if edit.tenure is TenureChoice.UNCHANGED else edit.tenure,
            amount=edit.amount or whole.amount,
            segment=whole.segment if edit.segment is SegmentChoice.UNCHANGED else edit.segment,
            strictness=(
                whole.strictness
                if edit.strictness is StrictnessChoice.UNCHANGED
                else edit.strictness
            ),
        )
    return (whole,)


def _edit_of(way: Choice) -> _Edit | None:
    edits = way.operations
    found: Sequence[_Edit] = (
        *_of_a_home(edits.budget_ops),
        *edits.commute_ops,
        *edits.weight_ops,
        *edits.tag_ops,
        *edits.area_ops,
    )
    return found[0] if found else None


# --- A feature ---------------------------------------------------------------------------------


def _wish_of(edit: WeightEdit) -> str:
    """What is wished of a feature, in the catalogue's words: "nearer a park", "fewer pubs"."""
    feature = FEATURES[edit.feature_id]
    if feature.polarity is not Polarity.EITHER:
        return _lower_first(feature.short_label)
    word = feature.lower if edit.direction is DirectionChoice.LESS else feature.higher
    # A word of the feature's own, "denser", stands by itself.
    thing = f" {_lower_first(feature.short_label)}" if feature.higher == "more" else ""
    return f"{word}{thing}"


# What a wish is for, of a measure whose two ways each have a word of their own: "dearer",
# "denser". The word says which way and nothing of what, so the offer says both, in a
# clause that stands after "when". Each is of the place: of its homes, or of its shops.
WHEN: Mapping[FeatureId, tuple[str, str]] = {
    FeatureId.HOMES_DENSITY: (
        "its homes stand closer together",
        "its homes stand further apart",
    ),
    FeatureId.PRICE_MEDIAN: ("homes there sell for more", "homes there sell for less"),
    FeatureId.BRAND_MIX: (
        "the chain grocers, gyms and coffee places near it are more premium",
        "the chain grocers, gyms and coffee places near it are less premium",
    ),
    FeatureId.PRICE_RISE_5Y: (
        "what homes there sell for has risen more over five years",
        "what homes there sell for has risen less over five years",
    ),
    FeatureId.PRICE_RISE_10Y: (
        "what homes there sell for has risen more over ten years",
        "what homes there sell for has risen less over ten years",
    ),
}
# A wish that says where an area is, and not what it has: "nearer a park", "away from
# main roads". An area is nearer a park, and has cleaner air.
_IS = ("nearer ", "away ")


def _when(edit: WeightEdit) -> str:
    """What an area is or has where it ranks higher for a wish: "it is nearer a park"."""
    feature = FEATURES[edit.feature_id]
    own = WHEN.get(edit.feature_id)
    if own is not None and feature.polarity is Polarity.EITHER:
        return own[1] if edit.direction is DirectionChoice.LESS else own[0]
    wish = _wish_of(edit)
    return f"it is {wish}" if wish.startswith(_IS) else f"it has {wish}"


def _counts(feature_id: FeatureId) -> str:
    """What a feature counts, as the catalogue names it, and what is to be known of it.

    Of a station it says what near means, which the founder decided on 2026-09-25. The
    figure is still named a straight line, and never a walk.
    """
    feature = FEATURES[feature_id]
    crime = f" {CRIME_CAVEAT}" if feature.dimension is Dimension.CRIME else ""
    near = f" {NEAR_A_STATION}" if feature_id is FeatureId.STATION_WALK else ""
    return f"This is what Burro measures for it: {_lower_first(feature.label)}.{near}{crime}"


def _why_it_counts(spec: PreferenceSpec, feature_id: FeatureId) -> str:
    held = next((w for w in spec.weights if w.feature_id is feature_id and w.weight > 0), None)
    if held is None:
        return ""
    if held.provenance is Provenance.DEFAULT:
        return "It counts a little now, because nobody chose."
    return "It counts now because it was chosen."


def _feature(edit: WeightEdit, spec: PreferenceSpec) -> _Part:
    feature = FEATURES[edit.feature_id]
    if edit.action is WeightAction.REMOVE:
        why = _why_it_counts(spec, edit.feature_id)
        one_way = feature.polarity is not Polarity.EITHER
        cannot = "Burro cannot rank an area for the opposite of it." if one_way else ""
        return _Part(
            f"Stop counting this: {_lower_first(feature.short_label)}.",
            " ".join(part for part in (why, cannot) if part),
            "Stop counting it",
        )
    wish = _wish_of(edit)
    much = ", and count this above all" if edit.action is WeightAction.SET else ""
    little = " a little" if edit.step is Step.UP_SMALL else ""
    # Recorded crime is chosen under its own name, and under no other word.
    named = feature.polarity is Polarity.EITHER or feature.dimension is Dimension.CRIME
    return _Part(
        f"Rank an area{little} higher when {_when(edit)}{much}.",
        _counts(edit.feature_id),
        _upper_first(wish) if named else "Add",
    )


# --- A vibe ------------------------------------------------------------------------------------


def _runs(tag_id: TagId) -> str:
    tag = TAGS[tag_id]
    return f"{tag.label} runs from {tag.low_end} to {tag.high_end}."


def _vibe_counts(tag_id: TagId) -> str:
    """What a vibe counts, as the catalogue says what it means, and what none can see."""
    return f"This vibe counts {_lower_first(TAGS[tag_id].meaning)}. {AN_AREA_AS_A_WHOLE}"


def _tag(edit: TagEdit) -> _Part:
    tag = TAGS[edit.tag_id]
    crime = COUNTING_CRIME if edit.tag_id in HOLDS_CRIME else ""
    if edit.action is WeightAction.REMOVE:
        return _Part(
            f"Stop counting {tag.label}.",
            "It counts now because it was chosen.",
            "Stop counting it",
        )
    much = ", counted above all" if edit.action is WeightAction.SET else ""
    little = ", counted a little" if edit.step is Step.UP_SMALL else ""
    if tag.shape is TagShape.SCALE:
        end = tag.low_end if edit.toward is TowardChoice.LOW else tag.high_end
        return _Part(
            f"Add {tag.label}, towards {end}{crime}{little}{much}.",
            f"{_runs(edit.tag_id)} {_vibe_counts(edit.tag_id)}",
            f"Towards {end}{crime}",
        )
    return _Part(f"Add {tag.label}{crime}{little}{much}.", _vibe_counts(edit.tag_id), f"Add{crime}")


# --- A journey ---------------------------------------------------------------------------------


def _by(mode: ModeChoice) -> str:
    chosen = DEFAULT_COMMUTE_MODE if mode is ModeChoice.UNCHANGED else Mode(mode.value)
    return _lower_first(MODE_LABELS[chosen])


def _journey(edit: CommuteEdit, release: Release, asks_place: bool) -> _Part:
    place = release.place(edit.place_id) if edit.place_id else None
    to = "" if place is None else f" to {place.name}"
    if asks_place:
        of = f" of at most {edit.max_minutes} minutes" if edit.max_minutes else ""
        does = f"Add a journey{of}, {_by(edit.mode)}. {NO_PLACE}"
    elif edit.max_minutes:
        does = f"Add a journey{to}: at most {edit.max_minutes} minutes, {_by(edit.mode)}."
    else:
        does = f"Add a journey{to}, {_by(edit.mode)}."
    if edit.strictness is StrictnessChoice.HARD:
        return _Part(does, "Areas further off are left out.", ADD_FIRM)
    if edit.strictness is StrictnessChoice.SOFT:
        return _Part(does, "Areas further off rank lower. None is left out.", ADD_AS_A_GUIDE)
    return _Part(does, "Areas further off rank lower.", "Add")


# --- A budget ----------------------------------------------------------------------------------


def _tenure_of(edit: BudgetEdit, spec: PreferenceSpec) -> Tenure:
    return spec.tenure if edit.tenure is TenureChoice.UNCHANGED else Tenure(edit.tenure.value)


# What a way that makes a search a visit would do, and what follows from it for areas.
A_VISIT = "Look for somewhere to stay on a visit"
RANKED_BY_THE_REST = (
    "A search for somewhere to stay has no budget and no kind of home, so Burro ranks areas "
    "by everything else you ask for."
)
# What is said where a model read a budget or a home beside a visit, and neither was kept.
LEFT_OUT_OF_A_VISIT = (
    "A search for somewhere to stay has no budget and no kind of home, so Burro has left those out."
)
# What each kind of search is called where a sentence says which one a search was kept on.
_KEPT_ON = {Tenure.RENT: "renting", Tenure.BUY: "buying", Tenure.VISIT: "visiting"}


def _home(edit: BudgetEdit, spec: PreferenceSpec) -> str:
    """What a budget edit would set, in words: each part of it that the edit holds."""
    if _tenure_of(edit, spec) is Tenure.VISIT:
        return A_VISIT
    rent = _tenure_of(edit, spec) is Tenure.RENT
    to = "to rent" if rent else "to buy"
    sized = edit.segment is not SegmentChoice.UNCHANGED
    home = f" a {SEGMENT_LABELS[Segment(edit.segment.value)]}" if sized else ""
    if edit.amount:
        said = f"Set a budget of \N{POUND SIGN}{money(edit.amount)}{' a month' if rent else ''}"
        named = edit.tenure is not TenureChoice.UNCHANGED or sized
        return f"{said} {to}{home}" if named else said
    if edit.tenure is not TenureChoice.UNCHANGED:
        return f"Look for a home {to}" if not sized else f"Look for{home} {to}"
    return f"Look for{home}"


def _costs(edit: BudgetEdit, spec: PreferenceSpec, release: Release) -> list[CostEstimate]:
    """What the release holds of the kind of home a budget would be held against."""
    tenure = _tenure_of(edit, spec)
    if edit.segment is not SegmentChoice.UNCHANGED:
        segment = Segment(edit.segment.value)
    elif tenure is spec.tenure:
        segment = spec.budget.segment
    else:
        segment = default_spec(tenure).budget.segment
    held = (release.cost(area.area_id, tenure, segment) for area in release.neighbourhoods)
    return [cost for cost in held if cost is not None]


def _on_a_median(edit: BudgetEdit, spec: PreferenceSpec, release: Release) -> bool:
    """Whether the budget would be held against a median, and against no upper end."""
    return any(held_on_the_median(cost) for cost in _costs(edit, spec, release))


def _of_a_wider_place(edit: BudgetEdit, spec: PreferenceSpec, release: Release) -> bool:
    """Whether the budget would be held against a rent of a postcode district or a borough."""
    return any(cost.of_a_wider_place for cost in _costs(edit, spec, release))


def _budget(edit: BudgetEdit, spec: PreferenceSpec, release: Release) -> _Part:
    home = _home(edit, spec)
    if _tenure_of(edit, spec) is Tenure.VISIT:
        return _Part(f"{home}.", RANKED_BY_THE_REST, "Set")
    if edit.strictness is StrictnessChoice.HARD:
        if _of_a_wider_place(edit, spec, release):
            return _Part(
                f"{home}, as a firm limit.",
                f"{FAR_DEARER_TO_RENT} {HALF_LET_FOR_LESS}",
                SET_FIRM.format(left_out=WHERE_FAR_DEARER_TO_RENT),
            )
        if _on_a_median(edit, spec, release):
            return _Part(
                f"{home}, as a firm limit.",
                f"{FAR_DEARER} {HALF_SOLD_FOR_LESS}",
                SET_FIRM.format(left_out=WHERE_FAR_DEARER),
            )
        return _Part(f"{home}, as a firm limit.", DEARER, SET_FIRM.format(left_out=THAT_COST_MORE))
    if edit.strictness is StrictnessChoice.SOFT:
        return _Part(
            f"{home}, as a guide.", "Dearer areas rank lower. None is left out.", SET_AS_A_GUIDE
        )
    return _Part(f"{home}.", "", "Set")


# --- An area -----------------------------------------------------------------------------------


def _area(edit: AreaEdit, release: Release) -> _Part:
    area = release.neighbourhood(edit.area_id)
    name = "this area" if area is None else area.name
    if edit.action is AreaAction.ONLY:
        return _Part(
            f"Look only in {name}.", "Every other area is left out.", f"Look only in {name}"
        )
    if edit.action is AreaAction.EXCLUDE:
        return _Part(
            f"Leave {name} out of the results.",
            f"No area of {name} is shown.",
            "Leave it out of the results",
        )
    return _Part(f"Take off the rule for {name}.", "", "Take off the rule")


# --- The whole of an offer ------------------------------------------------------------------------


def _part(way: Choice, spec: PreferenceSpec, release: Release, asks_place: bool) -> _Part:
    edit = _edit_of(way)
    if isinstance(edit, WeightEdit):
        return _feature(edit, spec)
    if isinstance(edit, TagEdit):
        return _tag(edit)
    if isinstance(edit, CommuteEdit):
        return _journey(edit, release, asks_place)
    if isinstance(edit, BudgetEdit):
        return _budget(edit, spec, release)
    if isinstance(edit, AreaEdit):
        return _area(edit, release)
    return _Part("", "", SKIP_LABEL)


def _thing(way: Choice, release: Release) -> str:
    """What a way is a way of, by the name the catalogue or the release gives it."""
    edit = _edit_of(way)
    if isinstance(edit, WeightEdit):
        return FEATURES[edit.feature_id].short_label
    if isinstance(edit, TagEdit):
        return TAGS[edit.tag_id].label
    if isinstance(edit, CommuteEdit):
        place = release.place(edit.place_id) if edit.place_id else None
        return "A journey" if place is None else place.name
    if isinstance(edit, AreaEdit):
        area = release.neighbourhood(edit.area_id)
        return "An area" if area is None else area.name
    if isinstance(edit, BudgetEdit):
        if edit.amount:
            return f"A budget of \N{POUND SIGN}{money(edit.amount)}"
        if edit.segment is not SegmentChoice.UNCHANGED:
            return f"A {SEGMENT_LABELS[Segment(edit.segment.value)]}"
        if edit.tenure is TenureChoice.VISIT:
            return VISITING
        return "Renting" if edit.tenure is TenureChoice.RENT else "Buying"
    return ""


def _is_a_name(way: Choice) -> bool:
    """Whether what a way is of has a name of its own, which keeps its case wherever it stands.

    A place and an area are named by the release, and a vibe by the
    catalogue. What a feature is called is the wish itself: "nearer a park".
    """
    return isinstance(_edit_of(way), CommuteEdit | AreaEdit | TagEdit)


def _named(way: Choice, release: Release) -> str:
    name = _thing(way, release)
    return name if _is_a_name(way) else _lower_first(name)


def _asks(ways: Sequence[Way], parts: Sequence[_Part], release: Release) -> tuple[str, str]:
    """The question an offer asks where none of its ways is the guess, and what follows it."""
    things = list(dict.fromkeys(_thing(way, release) for way in ways))
    edit = _edit_of(ways[0])
    if len(things) > 1:
        rest = [_named(way, release) for way in ways if _thing(way, release) != things[0]]
        named = ", or ".join([things[0], *dict.fromkeys(rest)])
        return f"{named}: which of these?", ""
    one = len(ways) == 1
    if isinstance(edit, TagEdit):
        if TAGS[edit.tag_id].shape is TagShape.SCALE:
            return f"{_runs(edit.tag_id)} Which end do you want?", _vibe_counts(edit.tag_id)
        asks = "add this" if one else "add this, or to stop counting it"
        return f"{things[0]}: do you want Burro to {asks}?", _vibe_counts(edit.tag_id)
    if isinstance(edit, WeightEdit):
        feature = FEATURES[edit.feature_id]
        if feature.polarity is Polarity.EITHER:
            ends = f"{feature.higher}, or {feature.lower}"
            return f"{feature.short_label}: do you want {ends}?", _counts(edit.feature_id)
        asks = "count this" if one else "count this, or to stop counting it"
        return f"{things[0]}: do you want Burro to {asks}?", _counts(edit.feature_id)
    if isinstance(edit, AreaEdit):
        return f"{things[0]}: do you want Burro to look only there, or to leave it out?", ""
    kinds = list(dict.fromkeys(_kind_of_house(way) for way in ways))
    if isinstance(edit, BudgetEdit) and len(kinds) > 1 and all(kinds):
        # A budget for a house, which is held by the kind of house: the person says which.
        which = f"{', '.join(kinds[:-1])} or {kinds[-1]}"
        return f"{things[0]} for a house: do you mean {which}?", parts[0].follows
    # A journey and a budget say the same of themselves whichever way they are taken.
    firmness = (", as a guide.", ", as a firm limit.")
    does = parts[0].does
    for ending in firmness:
        does = does.removesuffix(ending) + "." if does.endswith(ending) else does
    return does, ""


def _kind_of_house(way: Choice) -> str:
    """The kind of house a way of a budget is for, as a list says it. Nothing for any other."""
    edit = _edit_of(way)
    if not isinstance(edit, BudgetEdit) or edit.segment is SegmentChoice.UNCHANGED:
        return ""
    kind = SEGMENT_LABELS[Segment(edit.segment.value)]
    return kind.removesuffix(" house") if kind.endswith(" house") else ""


def _unsaid(unsaid: Unsaid, way: Choice | None, spec: PreferenceSpec, release: Release) -> str:
    edit = None if way is None else _edit_of(way)
    if unsaid.code is UnsaidCode.RANGE:
        return f"You gave {unsaid.low} to {unsaid.high} minutes, so Burro has used {unsaid.took}."
    if unsaid.code is UnsaidCode.MODE:
        by = _by(ModeChoice.UNCHANGED).removeprefix("by ")
        return f"You did not say how you would travel, so Burro has assumed {by}."
    if unsaid.code is UnsaidCode.ANOTHER_WAY:
        return ANOTHER_WAY
    limit = min(DEFAULT_COMMUTE_MINUTES, minutes_limit(DEFAULT_COMMUTE_MODE, release))
    if unsaid.code is UnsaidCode.MINUTES:
        return f"You gave no number of minutes, so Burro has used {limit}."
    if unsaid.code is UnsaidCode.NOT_PLACED:
        return (
            "Burro could not tell whether the minutes you gave are for this journey, so it "
            f"has used {limit}."
        )
    if unsaid.code is UnsaidCode.TENURE:
        return (
            "You did not say whether you are renting or buying, so Burro has kept your "
            f"search on {_KEPT_ON[spec.tenure]}."
        )
    if unsaid.code is UnsaidCode.VISIT:
        return LEFT_OUT_OF_A_VISIT
    if unsaid.code is UnsaidCode.SIZE:
        if isinstance(edit, BudgetEdit) and _tenure_of(edit, spec) is Tenure.BUY:
            return (
                "Burro knows prices by the kind of home, and not by the number of bedrooms, "
                "so it has left the size out."
            )
        return (
            "Burro knows rents by the number of bedrooms, and not by the kind of home, so it "
            "has left the kind out."
        )
    # The journey is added with a number nobody gave, so the offer says which.
    took = (
        "" if not isinstance(edit, CommuteEdit) or edit.max_minutes else f", so it will use {limit}"
    )
    return f"Burro could not use a number of minutes from these words{took}. {NO_LEAST}"


def _assumed(
    way: Choice | None, offer: Offer, spec: PreferenceSpec, names_a_way: bool
) -> list[Unsaid]:
    """What a way leaves to a default, which the offer has not said already."""
    edit = None if way is None else _edit_of(way)
    said = {unsaid.code for unsaid in offer.unsaid}
    found: list[Unsaid] = []
    if isinstance(edit, CommuteEdit):
        of_the_way = {UnsaidCode.MODE, UnsaidCode.ANOTHER_WAY}
        if edit.mode is ModeChoice.UNCHANGED and not said & of_the_way:
            code = UnsaidCode.ANOTHER_WAY if names_a_way else UnsaidCode.MODE
            found.append(Unsaid(code=code))
        if not edit.max_minutes and offer.note == TIME_NOT_PLACED:
            # A time was typed, and the rules could not tell that it is this journey's. It
            # is never said that the person gave none.
            found.append(Unsaid(code=UnsaidCode.NOT_PLACED))
        elif not edit.max_minutes and UnsaidCode.LEAST not in said:
            found.append(Unsaid(code=UnsaidCode.MINUTES))
    nobody_chose = spec.tenure_from is Provenance.DEFAULT
    unchanged = isinstance(edit, BudgetEdit) and edit.tenure is TenureChoice.UNCHANGED
    if isinstance(edit, BudgetEdit) and edit.amount and unchanged and nobody_chose:
        found.append(Unsaid(code=UnsaidCode.TENURE))
    return found


def _needs(offer: Offer, taken: Way | None, ways: Sequence[Way], release: Release) -> str:
    """What is left for the person once "add all" has been pressed. Nothing where nothing is."""
    if not ways:
        return ""
    edit = _edit_of(ways[0])
    if offer.asks_place:
        return "a place for the journey"
    if taken is None:
        if any(holds_crime(way.operations) for way in ways):
            return CRIME_BY_NAME
        if isinstance(edit, CommuteEdit):
            return f"the journey to {_named(ways[0], release)}"
        return _named(ways[0], release)
    # What is taken as a firm limit can be made no firmer: the other ways of a budget for
    # a house are other kinds of house.
    firmer = not _is_firm(taken) and any(other.id != taken.id and _is_firm(other) for other in ways)
    if firmer and isinstance(edit, CommuteEdit):
        return MAY_BE_FIRM.format(thing="journey")
    if firmer and isinstance(edit, BudgetEdit):
        return MAY_BE_FIRM.format(thing="budget")
    return ""


def _stops_counting(way: Choice) -> bool:
    edit = _edit_of(way)
    return isinstance(edit, WeightEdit | TagEdit) and edit.action is WeightAction.REMOVE


def _is_firm(way: Choice) -> bool:
    edit = _edit_of(way)
    return isinstance(edit, CommuteEdit | BudgetEdit) and edit.strictness is StrictnessChoice.HARD


def _labels(ways: Sequence[Way], parts: Sequence[_Part], release: Release) -> list[str]:
    """The words on each button. Each says which thing it is of, where an offer holds several."""
    several = len({_thing(way, release) for way in ways}) > 1
    labels = [
        _of_which(way, part, release) if several else part.button
        for way, part in zip(ways, parts, strict=True)
    ]
    # Two ways that would be called the same are each called by what they would do.
    return [
        part.does.removesuffix(".") if labels.count(label) > 1 else label
        for label, part in zip(labels, parts, strict=True)
    ]


def _of_which(way: Way, part: _Part, release: Release) -> str:
    """The words on a button that stands beside the ways of another thing.

    Nothing above the buttons says what this one holds, so it says all of it.
    """
    name = _thing(way, release)
    if isinstance(_edit_of(way), BudgetEdit | CommuteEdit):
        return part.does.removesuffix(".")
    if name.lower() in part.button.lower():
        return part.button
    if part.button == "Add":
        return f"Add: {_named(way, release)}"
    return f"{name}: {_lower_first(part.button)}"


def _sets_a_rent_of_a_place(ways: Sequence[Way], spec: PreferenceSpec, release: Release) -> bool:
    """Whether some way of an offer sets an amount that would be held against a rent of a
    postcode district or a borough. Such an offer says so, and says the publisher's caution."""
    return any(
        edit.amount > 0 and _of_a_wider_place(edit, spec, release)
        for way in ways
        for edit in way.operations.budget_ops
    )


def worded(
    offer: Offer,
    spec: PreferenceSpec,
    release: Release,
    settled: bool = True,
    names_a_way: bool = False,
) -> Worded:
    """The four parts of an offer, in words of Burro's own.

    `settled` is whether nothing beside the offer puts it in doubt. Where
    something does, "add all" leaves it for the person. `names_a_way` is
    whether the sentence holds a word for walking or cycling that the offer
    did not take.
    """
    ways = [way for way in offer.choices if way.direction is not SuggestionDirection.IGNORE]
    parts = [_part(way, spec, release, offer.asks_place) for way in ways]
    guessed = next((at for at, way in enumerate(ways) if way.guess), None)
    # The one way of a wish that something beside it puts in doubt is asked,
    # and not said: "not leafy" is not answered with "Add Leafy."
    wish = bool(ways) and isinstance(_edit_of(ways[0]), WeightEdit | TagEdit)
    # The one way that is left of a wish the words turn round is to stop counting the
    # thing. It is said, and not asked: nothing of it is a wish for the thing.
    said = len(ways) == 1 and (settled or not wish or _stops_counting(ways[0]))
    led = guessed if guessed is not None else (0 if said else None)
    if not ways:
        journey = offer.target == "commute"
        does, follows = (NO_JOURNEY, NO_LEAST) if journey else (NOTHING_TAKEN, "")
        if journey and offer.note:
            # The note says why in one sentence, and nothing is said twice.
            follows = ""
    elif led is None:
        does, follows = _asks(ways, parts, release)
    else:
        does, follows = parts[led].does, parts[led].follows
    of = ways[led or 0] if ways else None
    unsaid = [*offer.unsaid, *_assumed(of, offer, spec, names_a_way)]
    taken = in_add_all(offer) if settled else None
    noted = [offer.note, *([RENTS_NOTE] if _sets_a_rent_of_a_place(ways, spec, release) else [])]
    return Worded(
        label=offer.label or (_thing(ways[0], release) if ways else "A journey"),
        does=does,
        follows=follows,
        # What a notice with no way to take says is said above, and once.
        said=tuple(_unsaid(one, of, spec, release) for one in unsaid if ways),
        labels=(
            *_labels(ways, parts, release),
            *(SKIP_LABEL for way in offer.choices if way.id == IGNORE),
        ),
        add_all="" if taken is None else taken.id,
        needs=_needs(offer, taken, ways, release),
        note=" ".join(note for note in noted if note),
    )
