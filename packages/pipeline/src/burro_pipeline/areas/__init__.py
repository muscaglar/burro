"""Areas: the named neighbourhoods of London, drafted for a person to decide.

An area is a set of census output areas with one name. It is built as
`docs/design/london-data-areas.md` sets out: names and seeds from publishers'
files, each output area given to a seed, and what is in doubt put to a person.

Every module says in its own first lines what it reads and what it gives.
Modules whose names begin `names` or `seeds` draft the names and the seeds.
Modules whose names begin `assign` or `grow` give each output area to an area.
"""
