"""Journey times: from a timetable and the streets to the journeys a release holds.

The step takes a timetable in the open format that transit feeds use, the
streets for the walk at each end, where the homes of each area are, and the
points journeys end at. It gives, for every area and every such point, the
time by public transport at the hours the design names, by bike and on foot,
as `travel.json` holds a journey.

| Module | What it is |
|---|---|
| `feed` | The reader of a timetable, which checks it as it reads |
| `write_feed` | The writer of a timetable, which gives the same bytes on any machine |
| `engine` | What a routing engine is asked and gives back, and the settings of a build |
| `route` | The driver: origins in shards, each routed once, and one shard twice |
| `roll_up` | From home points to areas, and the table a release holds |
| `plain` | For tests only: a plain, slow router for the made-up town |
| `made_up` | The made-up town: a timetable, streets and homes that describe no real place |
| `cli` | The step `travel` of the command line |
| `transxchange` | The reader of a publisher's timetable in TransXChange, for one day |
| `timed` | A journey timed from a timetable: what an estimate is held against |

The engine that will route London needs Java, and runs on a hosted runner
alone. No module here imports it: `docs/design/london-data-travel.md` says
what its first run must settle.

`transxchange` and `timed` build no release. They are what the estimate of a
journey was held against (decision record 0027), and they know no street.
"""
