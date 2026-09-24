# What the workbook says of itself: land use statistics, England 2022

Written on 2026-09-24. It is a note of what a program read in the file. No person has opened the file.

| | |
|---|---|
| Registry entry | `mhclg-land-use-statistics-2022` |
| Publisher | Department for Levelling Up, Housing and Communities |
| File | `Live_Tables_-_Land_Use_Stock_2022_-_LSOA.ods`, as the release page lists it |
| Fetched | 2026-09-24, from the address the entry names under `file_urls` |
| File id | `f-b8db326abd8b` |
| Size | 38,142,392 bytes |
| SHA-256 | `b8db326abd8b4e1807a54dc600923403ac09246871ec0b9fdfb5e15659754284` |
| Read with | `python -m burro_pipeline describe`, with `--sheet` for each sheet |
| What that reads | Each row of a sheet that holds words alone. A row that holds a number is never given |

## What was looked for

The release page states the Open Government Licence v3.0 "except where otherwise stated". The entry asks that the workbook is read for any statement of Ordnance Survey's rights, or of any term beside the licence.

## What the workbook holds

| Where | What it says |
|---|---|
| Its sheets | Two: `P404a` and `P404b`. No cover, no contents and no sheet of notes |
| `P404a`, row 1, column A | "Table 405a: Land Use: England, Regions and Lower Super Output Areas - proportion of total land area by usage type, 2022" |
| `P404b`, row 1, column A | "Table 405b: Land Use: England, Regions and Lower Super Output Areas - total land area by usage type (hectares), 2022" |
| Row 3, column AW | The unit: "Per cent" in the first sheet, "Hectares" in the second |
| Rows 4 to 6 | The names of the columns: developed and non-developed use, the 13 groups, the categories and a total for each group |
| Under each table, the first note | "1 The land use dataset has been mapped to lower layer super output (LSOA) 2021 boundaries at the mean high tide mark." It then gives an address on the statistics office's portal of boundaries |
| Under each table, the second note | "2 The grand total column is the sum of all the land use categories. The figures within the grand total column should not be used as the definitive source for the size of each local authority." It then gives an address for the Standard Area Measurements |

Every other row of either sheet holds a number, and was not read.

## What it does not hold

- No statement of a licence.
- No statement of copyright, and no mention of Ordnance Survey.
- No attribution of its own.
- No term of use, and no limit on reuse.
- No month or day. The year 2022 in the two titles is all it says of its date.
- No word on what a dash in a cell of figures stands for.

So nothing in the workbook is "otherwise stated". The licence is the one the release page, the statistical release and the technical notes each state.

## What this note cannot say

- What a person would see who opened the workbook in a spreadsheet program. A program read the part of the file that holds its sheets. It did not read how a cell is drawn, a picture, a header or a footer of a printed page, or the properties of the document.
- Whether a row that holds a number also holds words that matter. A row of figures holds the code and the name of its area beside them, and was not read.
- Anything of Ordnance Survey's terms for the products the figures were made from. The entry uses the published table alone.

## What would settle it

A person opens the workbook once, looks at each sheet, and says here that they have.

Credit: Contains public sector information licensed under the Open Government Licence v3.0.
