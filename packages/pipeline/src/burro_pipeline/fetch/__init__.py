"""Fetch: the only step of a build that may reach a network.

It asks the licence registry before every file and holds the file to the
registry entry of its source, downloads the file with one request, keeps it in
the store under its hash, and writes its receipt. It also takes a file a person
saved by hand, and describes the shape of a stored file without printing a
value from any row.

The receipt it writes is the one record of a fetched file, defined in
`burro_pipeline.evidence`. Its steps are run as `python -m burro_pipeline STEP`.
A test checks that no module but the downloader and the object store names a
network library.
"""
