"""Write a timetable in the open format that transit feeds use, as the zip a reader takes.

Whatever makes a feed writes it here: the made-up town today, and the
converters of a publisher's timetable when they are built. The same tables
give the same bytes on any machine, so that a build that is run twice can be
compared byte for byte. Nothing is compressed, and no file in the zip carries
the time it was written or the machine it was written on.

Standard library only.
"""

import csv
import io
import zipfile
from collections.abc import Mapping, Sequence

# A table: its column names, and then its rows.
Table = Sequence[Sequence[str]]


def zipped(tables: Mapping[str, Table]) -> bytes:
    """Tables as the zip of a feed. The same tables give the same bytes on any machine."""
    held = io.BytesIO()
    with zipfile.ZipFile(held, "w", zipfile.ZIP_STORED) as archive:
        for name in sorted(tables):
            text = io.StringIO(newline="")
            csv.writer(text, lineterminator="\n").writerows(tables[name])
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, text.getvalue().encode("utf-8"))
    return held.getvalue()
