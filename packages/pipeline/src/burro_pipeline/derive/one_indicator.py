"""The period of what one measure reads, in a file that holds more.

A receipt states one period for its file. A measure may read a part of the
file that is of a shorter span: the crime files of the police hold 36 months,
and a measure counts the months of them that are whole. So a measure says here
which part of the span of its receipt is its own.

Two things follow, and each is one function:

- A figure is cited to a receipt only where the receipt states a period that
  takes in every day of what was read. `takes_in` says whether it does.
- The row of evidence behind a figure states the period of what was read, with
  the periods of the other files behind the figure, and not the span of the
  whole file. `behind` gives it.
"""

from collections.abc import Sequence

from burro_pipeline.evidence.receipt import Period, Receipt
from burro_pipeline.evidence.row import EvidenceRow


def takes_in(stated: Period, indicator: Period) -> bool:
    """Whether the period a receipt states takes in every day of an indicator's own."""
    (first, last), (starts, ends) = stated.days(), indicator.days()
    return first <= starts and ends <= last


def behind(indicator: Period, others: Sequence[Receipt]) -> Period:
    """The span of what stands behind a figure: the indicator, and every other file."""
    spans = [indicator.days(), *(receipt.data_period.days() for receipt in others)]
    first, last = min(span[0] for span in spans), max(span[1] for span in spans)
    return Period(as_at=first) if first == last else Period(start=first, end=last)


def cited(
    rows: Sequence[EvidenceRow], workbook: Receipt, files: Sequence[Receipt], indicator: Period
) -> tuple[EvidenceRow, ...]:
    """Rows of evidence that state the period of the one indicator they rest on.

    `files` are the receipts of every file behind the rows, the workbook's
    among them. A row that names no file states no period, and is left as it
    is.
    """
    others = [receipt for receipt in files if receipt.file_id != workbook.file_id]
    period = behind(indicator, others)
    return tuple(
        row if row.data_period is None else row.model_copy(update={"data_period": period})
        for row in rows
    )
