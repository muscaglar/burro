"""Run the review desk: `python -m desk serve`. `desk/cli.py` says what each step does."""

import sys

# Said here, before anything newer is read: an older Python stops at the first file it cannot.
if sys.version_info < (3, 13):  # noqa: UP036
    sys.exit("The desk needs Python 3.13 or later. Start it with make desk.")

from desk.cli import main

sys.exit(main())
