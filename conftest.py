"""What every test shares: how often Python stops to look for what it can throw away.

The tests make millions of small records and let them go. Python stops to look for
records that nothing holds any more each time a few hundred have been made. Here that
frees next to nothing, and costs the tests a second or two of the thirty they may take.
So while the tests run it looks less often. No code under test is changed by this.
"""

import gc

gc.set_threshold(200_000, 20, 20)
