"""The synthetic release: a made-up city that stands in for real data until there is some.

It is unmistakably synthetic. The manifest says so, every id begins `syn-`,
every name is invented, and the map lies in open sea.
"""

from burro_pipeline.release.synthetic.build import BUILT_AT, RELEASE_ID, SEED, build_synthetic

__all__ = ["BUILT_AT", "RELEASE_ID", "SEED", "build_synthetic"]
