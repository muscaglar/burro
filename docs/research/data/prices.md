# What homes sold for, the council tax bands, and household income

Status: written on 2026-09-25, from HM Land Registry's files of prices paid for 2023, 2024 and 2025, the statistics office's workbook of median prices, the Valuation Office Agency's table of homes by band, and the statistics office's estimates of household income, as each stood in the store that day. It is a dated snapshot.

**No person has checked anything on this page.** Every count was made by a program. No figure of any one area is on this page, and none is in a test. A count is of London as a whole, or of a borough. The figures of areas are beside the build, in a folder that git ignores.

## 0. In short

| Question | Answer |
|---|---|
| What is built | A price for each kind of home in each area, counted from sales. A margin on a firm budget. Three measures: the council tax bands, and the rise in prices over five years and over ten. Household income, shown and never ranked on |
| Where a price comes from | The median of what was paid for each kind of home, from every standard sale of three years. Section 1 |
| How few sales give no figure | Fewer than 10. A flat has a figure in 984 of London's 1,002 areas. Section 2 |
| How far it stands from the statistics office's median | For flats, half of the areas are within 5 in 100 of it. Section 3 |
| What a firm budget of £400,000 for a flat leaves out | 231 areas, where it left out 424 with no margin. Section 4 |
| What the bands say | The share of homes in bands E to H. Half of London's areas have more than a quarter of their homes there. Section 5 |
| Where prices have risen | Over five years the middle price fell in a third of London's areas. Section 6 |
| Do these follow household income | The bands do, at 0.71 in rank. What homes sell for does, at 0.58. The rises do not. Section 7 |

## 1. What is read of a sale, and which sales count

The files of prices paid hold one row for a sale, with no row of names above them. Sixteen things stand in a row. Six are read: the price, the day, the postcode, the kind of home, whether it was newly built, and whether the sale is of the kind the publisher calls standard. Ten are never read: the id of the sale, freehold or leasehold, the seven lines of the address, and the mark of a changed record. `derive/price_paid.py` names each by where it stands, and a test plants a word in every place that is never read.

| Of the three years | Count |
|---|---|
| Rows | 2,745,967 |
| Sales that are not standard, and are not counted | 479,554 |
| Standard sales placed in an area of London | 244,811 |
| Of those, flats | 130,843 |
| Terraced houses | 66,009 |
| Semi-detached houses | 36,317 |
| Detached houses | 11,642 |
| Newly built flats among them | 15,456 |
| Standard sales at a postcode that has since ended | 17 |

**Only standard sales are counted**, because that is what the statistics office counts. Its median for a year was held against the median of the standard sales of the same year, area by area and kind by kind. The two were the same to the pound in 2,557 of 2,618 cases for 2023 and in 2,565 of 2,657 for 2024. With every sale counted, about a quarter were the same. For 2025 fewer match, 1,979 of 2,684: the files of that year are of a later edition than the workbook, and hold sales that were lodged since.

A postcode puts a sale in an area, through the postcode directory, and is kept nowhere after that. No row of a release, of its evidence or of what a build prints holds a postcode or a price of one sale. A test holds each.

## 2. How few sales give no figure

Fewer than 10 sales of a kind of home in an area, over the three years, give no figure. It is the least the contract calls an observation. The row of evidence says how many there were, and nothing stands in for the figure.

| Kind of home | Areas with a figure | Areas with too few sales | Areas with none | Figures that rest on 50 sales or more |
|---|---|---|---|---|
| Flat | 984 | 18 | 0 | 700 |
| Terraced house | 940 | 58 | 4 | 559 |
| Semi-detached house | 653 | 268 | 81 | 287 |
| Detached house | 282 | 463 | 257 | 57 |

A figure that rests on 50 sales or more says `high`, and one on 10 to 49 says `medium`. The statistics office gives a figure from 5 sales up, for one year, and says nothing of how many. Its median for flats, for the year to March 2026, exists in 927 of the 1,002 areas.

## 3. The three years against the statistics office's one year

The two are not the same thing: one is of three years to December 2025, and the other of one year to March 2026. Where both exist they were held against each other.

| Kind of home | Areas with both | Half of the areas differ by no more than |
|---|---|---|
| Flat | 925 | 4.8 in 100 |
| Terraced house | 868 | 4.0 |
| Semi-detached house | 545 | 4.2 |
| Detached house | 189 | 6.6 |

For flats, three quarters of the areas differ by no more than 9.0 in 100, and nine in ten by no more than 15.9. 481 of the 925 are within 5 in 100, and 727 within 10.

## 4. The margin on a firm budget

Half of what sold in an area sold for less than its median. So an area whose median is over a budget still has homes within it, and how many falls as the median rises. Of the flats sold in London in the three years, held against £400,000:

| Where the median of an area stands | Share of the flats sold there that went for £400,000 or less, in the middle area |
|---|---|
| At the budget | About half |
| 20 to 25 in 100 over it | 26 in 100 |
| 25 to 30 in 100 over it | 24 in 100 |

| The margin | Areas left out, of 984 with a figure |
|---|---|
| None | 424 |
| 10 in 100 | 340 |
| 25 in 100, which is what core holds | 231 |
| 50 in 100 | 105 |

With a quarter, 753 areas are kept. In 193 of them the median is over the budget, and in those the share of flats that sold within it runs from 18 to 50 in 100. Of the 231 left out, 11 had a quarter or more of their flats sold within it. The card of an area that is kept over the budget says how far over its median is, and that about half of the flats sold there went for less than the median.

The boroughs that lose most to a firm £400,000 for a flat, with the margin:

| Borough | Areas left out | Areas |
|---|---|---|
| Camden | 26 | 27 |
| Westminster | 24 | 24 |
| Wandsworth | 23 | 38 |
| Hackney | 20 | 30 |
| Hammersmith and Fulham | 20 | 25 |
| Kensington and Chelsea | 20 | 21 |
| Islington | 17 | 23 |
| Lambeth | 13 | 35 |
| Haringey | 11 | 36 |

Eleven boroughs lose none. With no margin all of Camden, Westminster and Islington were left out. With it one area of Camden and six of Islington are kept. In Camden 11 in 100 of the flats sold went for £400,000 or less, in Islington 15 and in Westminster 8: a firm budget of that size does leave most of each out, and should.

## 5. The council tax bands

The Valuation Office Agency's table gives, for each area, the homes in each of eight bands, rounded to 10, with a dash for a count of 1 to 4. The measure is the homes in bands E to H over all the homes of the area. A dash adds nothing and marks the figure. Where every one of the four bands is a dash or a nought, and one is a dash, no figure is given.

| Across London | |
|---|---|
| Areas with a figure | 982 |
| Areas with none, because the homes in the higher bands are all behind a dash | 20 |
| Figures marked, because a band of theirs is a dash | 460 |
| The middle area | 25.8 in 100 |
| One area in ten has less than | 3.4 |
| One area in ten has more than | 66.0 |
| Homes in band H, across London | 1.8 in 100 |

**A band is a value of 1991.** It says which homes stand in a place, and nothing of what one sells for today. The registry asks that a band is never used as an estimate of a price, and no word of the measure says one.

## 6. Where prices have risen

The statistics office's workbook holds a median for every year that ends with a quarter, from 1995. The measure is the median for a home of any kind in the year to March 2026, for each £100 of the median in the year to March 2021, and to March 2016.

| Across London's 1,002 areas | Over five years | Over ten years |
|---|---|---|
| The middle area | £106 for each £100 | £127 |
| Areas where the middle price fell | 354 | 113 |
| Areas where it rose by a quarter or more | 58 | 542 |

**A rise is of prices that were paid, and promises nothing.** It moves where other homes came to be sold, as where new flats were built, though no home is worth more. One area in ten stands under £85 for each £100 over five years, and one in ten over £121: a figure far from the middle says that what was sold changed, more than that any home did.

## 7. The row of the proxy audit

[Decision record 0006](../../adr/0006-rank-places-not-residents.md) asks for this row before a measure is served. It covers what homes sell for, the council tax bands, and the rise in prices. It was written on 2026-09-25, before any of the last three was in a release that is served. Nobody has reviewed it.

| | |
|---|---|
| The aim it serves | To let a person who types a word for a smart area, or for a place on the rise, choose a figure of the homes of a place: what they sold for, which bands they are in, and how far what was paid has risen |
| Why it is in proportion | Each counts homes or what was paid for them, from an official file, and holds nothing of who lives anywhere. Each is offered and never applied from a word, with a note that says Burro measures places and not people, or that a rise promises nothing. None stands in a vibe or in likeness, and nothing weighs one by default |
| What it was measured against | The statistics office's estimate of total annual household income for the same areas, which the registry allows a check to read. The table below holds the rank correlations. Nothing a check works out joins a release |
| What could not be measured | Whether any of them follows a count of residents by ethnic group, religion, country of birth or health. No file is registered for that audit, and none was read |
| What triggers a review | A rank correlation of 0.5 or more, either way, between a measure and any figure of who lives in an area, across London's areas. It is the figure the row for recorded incidents set, and is the founder's to set |
| What can then be done | Show the measure on an area's page and rank on it no longer. Take it out of what is offered for a word for a smart area. Or leave it as it is served today: offered, never applied, and said to be of the place |

| Measure | Areas | Rank correlation with household income |
|---|---|---|
| `homes_higher_bands` | 982 | **0.71** |
| `price_median`, a home of any kind | 1,002 | **0.58** |
| The price of a semi-detached house, from the sales | 653 | 0.59 |
| The price of a detached house | 282 | 0.53 |
| The price of a terraced house | 940 | 0.40 |
| The price of a flat | 984 | 0.32 |
| `brand_mix`, as another branch measures it | 990 | 0.45 |
| `price_rise_5y` | 1,002 | 0.04 |
| `price_rise_10y` | 1,002 | -0.13 |

The bands stand at 0.70 with what homes sell for, and at 0.51 with the mix of brands. What homes sell for stands at 0.48 with the mix of brands.

**The review is triggered for two measures**: the council tax bands, and what homes of any kind sell for. Each follows what the households of an area are estimated to have more closely than the line allows. Neither was taken out or capped here: each is what the founder asked for, by name, as a reading of "affluent" that counts homes. What stands is the third of the three things that can be done, and [decision record 0028](../../adr/0028-household-income-is-shown-and-never-ranked-on.md) leaves the choice to the founder.

## 8. What could not be checked

- Nobody has looked at a figure of any area beside the place itself.
- The price of a flat is of flats of every size. No file gives a price by the number of bedrooms, and none is worked out.
- The sales of 2025 are not all lodged. A later edition of the file will hold more, and a median will move.
- The rise is of the statistics office's own medians, of one year each. It was not held against the sales.
- How far a band of 1991 says what a home is today was not measured.
