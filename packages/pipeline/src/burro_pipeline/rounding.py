"""How a figure is rounded: a half is taken upward, as a person does who rounds by hand.

It stands below the geography and the methods, so that both round the same way:
the land of an area, the share of its homes that stood behind a figure, and
the figure itself.
"""

from decimal import ROUND_HALF_UP, Decimal


def to_places(value: float, places: int) -> float:
    """A figure as it is given: to so many decimal places, with a half taken upward.

    The language's own `round` takes a half to the even digit, so 56.25 would
    be given as 56.2 where a person who rounds by hand writes 56.3. The figure
    is read as the shortest decimal that is the same number, so a half that no
    float holds exactly, as 56.35, is still seen to be a half.
    """
    step = Decimal(1).scaleb(-places)
    return float(Decimal(repr(value)).quantize(step, rounding=ROUND_HALF_UP))
