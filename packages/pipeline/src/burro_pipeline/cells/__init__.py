"""Cells: the geography every figure is worked out on.

It reads the statistics office's lookup, its boundaries and the census table of
homes, and gives the spine of London, the areas of the build, each area's
outline and the land each LSOA covers. It reads nothing about who lives
anywhere. Every file is read through `burro_pipeline.inputs`.

| Module | Gives |
|---|---|
| `spine.py` | London's output areas, what each is part of, its homes, and the areas |
| `shapes.py` | Outlines read from a GeoPackage, joined, measured and put on the globe |
| `outline.py` | Each area's outline, its neighbours and a point inside it |
| `land.py` | The land of each LSOA and of each area, in hectares |
| `centres.py` | The point where the homes of each output area are taken to stand |
"""
