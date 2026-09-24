"""Data releases on disk: writing one, reading one back, and building the synthetic one.

A release is one folder named for its id. `write_release` is the only way one
is written and `read_release` the only way one is read, and both leave the
checking to `burro_core`, so nothing here can disagree with the API about what
a valid release is.
"""

from burro_pipeline.release.read import UnreadableRelease, read_release
from burro_pipeline.release.synthetic import build_synthetic
from burro_pipeline.release.write import canonical_json, write_release

__all__ = [
    "UnreadableRelease",
    "build_synthetic",
    "canonical_json",
    "read_release",
    "write_release",
]
