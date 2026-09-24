"""Sentences the rule-based reader is held to. Every name in them is made up.

`REVERSED` and `UNASKED` are the sentences an adversary wrote after the second round of
fixes: each made the reader do the opposite of what was asked, or something nobody
asked for. `PLAIN` and `HELD_OUT` are plain wishes as a person might type them, each
with what it asks for. `UNKNOWN_WORDS` are ordinary words that are not in the reader's
vocabulary, and must never be added to it without a rule."""

# A wish is met if any of its ids is raised: a feature or a tag by its id, a journey
# as "journey:<place id>", an area rule as "area:<area id>:<rule>", a budget as
# "budget", and a tenure as "tenure:<tenure>".
Wishes = list[set[str]]

REVERSED: tuple[str, ...] = (
    "I don;t want pubs nearby",
    "I don,t want a station nearby",
    "I do n't want bars",
    "I dinnae want pubs",
    "Pubs, bars, restaurants: none of that for me",
    "A station, a high street, nightlife — I can do without all of them",
    "Nightlife, restaurants and theatres? No thanks.",
    "Pubs, bars, clubs. None of it.",
    "Dealbreakers: pubs, a station, nightlife",
    "Cons: nightlife, busy high street",
    "Turn-offs: bars and a busy high street",
    "Red flags for me are pubs and a station on the doorstep",
    "Schools, playgrounds, family stuff, not relevant",
    "A park or a playground? No thanks",
    "Lively and buzzy? Not really my thing.",
    "Restaurants, cafes, pubs - not interested in any of it",
    "Theatres and cinemas and galleries, I don't need any of those",
    "Station, shops, schools. I need none of them.",
    "A high street on my doorstep is my idea of hell",
    "Living by a station would drive me up the wall",
    "A playground next door would do my head in",
    "Nightlife, I'll pass",
    "Pubs are for other people",
    "Nightlife is for the young and I'm past it",
    "A pub on my doorstep would be hell",
    "A station within earshot would drive me mad",
    "Restaurants in walking distance would be wasted on me",
    "Pubs, yuck",
    "Nightlife, ugh",
    "A university next door sounds exhausting",
    "Who'd want to live near a station?",
    "Why would anyone want a pub next door?",
    "Only a fool would want nightlife on their doorstep",
    "Do I look like I want a pub next door?",
    "Who in their right mind wants a station at the end of the garden?",
    "I struggle to see why anyone would want a park",
    "Pubs 🙄",
    "nightlife 🤮",
    "i do nt want a park",
    "I do't want a park",
    "I font want pubs",
    "Id ont want bars",
    "Parks, I don't need",
    "Pubs are what I want to escape",
    "we want somewhere leafy and quiet but not dead and "
    "definitely not near a university or loads of bars",
    "My ex works at Pellam Infirmary so I'd rather be elsewhere",
    "At least 30 minutes from Wexmoor University",
    "More than 40 minutes from Pellam Cross please",
    "No less than 30 minutes from Foxholt Market",
    "I'm escaping the commute to Cindermoor Works",
    "Further than 20 minutes from Foxholt Market",
    "Minimum 45 minutes from Pellam Infirmary",
    "My stalker works at Foxholt Market",
    "I like noise",
    "I want somewhere noisy and lively",
    "I actually like a bit of noise",
    "I enjoy the noise and bustle of a main road",
    "I'm done renting",
    "Renting is dead money",
    "I've had it up to here with renting",
    "Finally escaping the rental market",
    "Buying is out of the question",
    "My mum wants me near a station. I disagree.",
    "I shun busy high street nightlife",
    "I wanted a park but I've changed my mind",
    "more than 15 minutes walk from a pub",
    "further than 5 minutes from a high street",
    "not near a station or loads of bars",
    "no pubs or loads of restaurants",
    "Most people want a station. I'm the exception.",
    "Negatives: nightlife. Positives: parks.",
    "Downsides: a busy high street and nightlife",
    "Irritants - pubs, bars",
    "To be avoided at all costs: nightlife",
    "Veto: pubs",
    "Ruled out: anything near a university",
    "pubs, eww",
    "pubs, forget it",
    "a station, heaven forbid",
    "pubs, pass",
    "pubs, gross",
    "pubs :(",
    "pubs 😡",
    "pubs 🙅",
    "nightlife 😴",
    "a pub on the corner would ruin it for me",
    "pubs in the area would put me right off",
    "a station at the end of the road is exactly what I'm escaping",
    "a playground by the house would be a disaster",
    "nightlife to the left, nightlife to the right, I've had it",
    "a university in the middle of town ruins a place",
    "restaurants on every corner get old fast",
    "Imagine needing a high street",
    "God knows why people want nightlife",
    "kids love playgrounds but mine have grown up",
    "I dob't want pubs",
    "I dint want pubs",
    "i dun want pubs",
    "I donut want a station",
    "My son studies at Wexmoor University and I'd like to give him space",
)

UNASKED: tuple[str, ...] = (
    "I left my job at Cindermoor Works",
    "Should I avoid Cindermoor?",
    "Would you avoid Cindermoor?",
    "I got sacked from my job at Cindermoor Works",
    "Nightlife in small doses",
    "A small number of bars at most",
    "I study crime at university",
    "I love crime in my books",
    "I once loved pubs",
    "I liked pubs when I was younger",
    "Nightlife was essential to my ex",
    "My landlord thinks everyone wants a high street",
    "Supposedly everyone loves a high street",
    "My ex loved pubs",
    "Could I avoid Cindermoor and still get a park?",
    "Some avoid Tallowgate",
    "They avoid Cindermoor",
    "only Wexmoor?",
    "Is it only Cindermoor that has a park?",
    "My job at Cindermoor Works ends in June",
    "I'm leaving my job at Pellam Infirmary",
    "My old office is at Foxholt Market",
    "I was commuting to Pellam Cross until last year",
    "I work at Cindermoor Works (well, I did)",
)

# The first ninety are the adversary's own, written without sight of the vocabulary.
PLAIN: tuple[tuple[str, Wishes], ...] = (
    ("I want to live near a park", [{"park_proximity"}]),
    (
        "Somewhere leafy and quiet",
        [{"green_cover", "leafy"}, {"noise_exposure", "quiet_residential"}],
    ),
    (
        "Good schools are really important to us",
        [{"school_primary_attainment", "school_primary_nearby", "school_secondary_attainment"}],
    ),
    ("Close to a station please", [{"station_lines", "station_walk"}]),
    ("I work at Cindermoor Works", [{"journey:syn-p0021"}]),
    ("Within 30 minutes of Pellam Cross", [{"journey:syn-p0012"}]),
    ("Lots of restaurants and cafes", [{"foodie", "venue_food_drink", "venue_independent"}]),
    (
        "A lively area with good nightlife",
        [{"buzzy", "evening_venues"}, {"buzzy", "evening_venues", "venue_evening"}],
    ),
    ("I'd love to be by the river", [{"water_access", "waterside"}]),
    ("We need a playground nearby for the kids", [{"family_amenities", "play_space_proximity"}]),
    ("My budget is £1,800 a month", [{"budget"}]),
    ("Looking to rent a 2 bed flat for under £2,000", [{"budget"}]),
    ("I cycle to work at Foxholt Market", [{"journey:syn-p0019"}]),
    ("Somewhere with a village feel", [{"village_feel"}]),
    ("I love period houses", [{"conservation_cover", "historic_character", "homes_pre1919"}]),
    (
        "An area with a bit of character",
        [{"conservation_cover", "historic_character", "homes_pre1919"}],
    ),
    (
        "Independent shops and cafes",
        [{"venue_independent"}, {"foodie", "venue_food_drink", "venue_independent"}],
    ),
    ("Good transport links are a must", [{"station_lines", "station_walk"}]),
    ("Low crime", [{"crime_burglary_theft", "crime_violence_robbery"}]),
    ("Clean air matters to me", [{"air_no2"}]),
    ("A proper high street", [{"highstreet_access", "strong_high_street", "venue_independent"}]),
    ("I study at Wexmoor University", [{"journey:syn-p0026"}]),
    ("Only Cindermoor", [{"area:syn-n0003:only"}]),
    ("Walking distance to a park", [{"park_proximity"}]),
    ("I want lots of green space", [{"green_cover", "leafy"}]),
    ("Near the tube", [{"station_lines", "station_walk"}]),
    (
        "Family friendly with good primary schools",
        [
            {
                "family_amenities",
                "play_space_proximity",
                "school_primary_attainment",
                "school_primary_nearby",
            },
            {"school_primary_attainment", "school_primary_nearby", "school_secondary_attainment"},
        ],
    ),
    ("Plenty of pubs and bars", [{"evening_venues", "venue_evening"}]),
    ("Theatres and galleries nearby", [{"creative", "culture_venues"}]),
    ("Peaceful and residential", [{"noise_exposure", "quiet_residential"}]),
    ("Arty and creative", [{"creative", "culture_venues"}]),
    (
        "I want to buy a house near a good secondary school",
        [
            {"tenure:buy"},
            {"school_primary_attainment", "school_primary_nearby", "school_secondary_attainment"},
        ],
    ),
    (
        "We're a family of four and want parks and playgrounds",
        [{"park_proximity"}, {"family_amenities", "play_space_proximity"}],
    ),
    ("Somewhere buzzy with loads going on", [{"buzzy", "evening_venues"}]),
    ("I need to be within 45 minutes of Pellam Exchange by train", [{"journey:syn-p0017"}]),
    ("My office is at Tallowgate Guild Quarter", [{"journey:syn-p0018"}]),
    (
        "A quiet street not far from a station",
        [{"noise_exposure", "quiet_residential"}, {"station_lines", "station_walk"}],
    ),
    (
        "Historic buildings and a conservation area",
        [{"conservation_cover", "historic_character", "homes_pre1919"}],
    ),
    ("Great food scene", [{"foodie", "venue_food_drink", "venue_independent"}]),
    ("Canal walks on the doorstep", [{"water_access", "waterside"}]),
    (
        "I like being able to walk to the shops",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    ("A park within five minutes' walk", [{"park_proximity"}]),
    ("Somewhere green with trees", [{"green_cover", "leafy"}]),
    ("Cinemas and live music", [{"creative", "culture_venues"}]),
    (
        "I'd like a station close by and a park too",
        [{"station_lines", "station_walk"}, {"park_proximity"}],
    ),
    ("Near a university", [{"near_universities", "university_proximity"}]),
    ("Victorian terraces", [{"conservation_cover", "historic_character", "homes_pre1919"}]),
    (
        "I'm after somewhere with a great high street",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    (
        "Must have: a park. Nice to have: pubs.",
        [{"park_proximity"}, {"evening_venues", "venue_evening"}],
    ),
    ("The most important thing is being near a station", [{"station_lines", "station_walk"}]),
    ("Quieter than where I live now", [{"noise_exposure", "quiet_residential"}]),
    ("More green space than I have at the moment", [{"green_cover", "leafy"}]),
    (
        "I really want to be close to the river and a good pub",
        [{"water_access", "waterside"}, {"evening_venues", "venue_evening"}],
    ),
    ("A short walk to the station is essential", [{"station_lines", "station_walk"}]),
    (
        "We want excellent schools and a big park",
        [
            {"school_primary_attainment", "school_primary_nearby", "school_secondary_attainment"},
            {"park_proximity"},
        ],
    ),
    ("Somewhere safe with low crime rates", [{"crime_burglary_theft", "crime_violence_robbery"}]),
    (
        "I work in Cindermoor and my partner works at Pellam Infirmary",
        [{"journey:syn-p0002", "journey:syn-p0021"}, {"journey:syn-p0028"}],
    ),
    ("20 minutes to Foxholt Market by bike", [{"journey:syn-p0019"}]),
    ("Up to £450,000 for a terraced house", [{"budget"}]),
    (
        "Leafy streets, good coffee shops and a station nearby",
        [
            {"green_cover", "leafy"},
            {"foodie", "venue_food_drink", "venue_independent"},
            {"station_lines", "station_walk"},
        ],
    ),
    ("I want to be near Sable Reach Pier", [{"journey:syn-p0041"}]),
    (
        "Open to anywhere but I need a park and low noise",
        [{"park_proximity"}, {"noise_exposure", "quiet_residential"}],
    ),
    ("Waterside living", [{"water_access", "waterside"}]),
    ("Somewhere I can walk to restaurants", [{"foodie", "venue_food_drink", "venue_independent"}]),
    ("An area known for its pubs", [{"evening_venues", "venue_evening"}]),
    (
        "I want a neighbourhood with a real sense of history",
        [{"conservation_cover", "historic_character", "homes_pre1919"}],
    ),
    ("Parks, parks and more parks", [{"park_proximity"}]),
    ("Being close enough to a station to walk", [{"station_lines", "station_walk"}]),
    (
        "Easy access to a high street and a park",
        [{"highstreet_access", "strong_high_street", "venue_independent"}, {"park_proximity"}],
    ),
    ("I can't live without a park", [{"park_proximity"}]),
    ("A park would be lovely", [{"park_proximity"}]),
    (
        "We would love a playground around the corner",
        [{"family_amenities", "play_space_proximity"}],
    ),
    ("I need good air quality because of my asthma", [{"air_no2"}]),
    ("Less noise than my current flat", [{"noise_exposure", "quiet_residential"}]),
    ("Low pollution", [{"air_no2"}]),
    ("Somewhere with a station that has several lines", [{"station_lines", "station_walk"}]),
    (
        "Looking for a one bedroom flat to rent near a park, budget 1500 pcm",
        [{"budget"}, {"park_proximity"}],
    ),
    (
        "Pubs, restaurants and a bit of life",
        [{"evening_venues", "venue_evening"}, {"foodie", "venue_food_drink", "venue_independent"}],
    ),
    (
        "I want it all: parks, pubs and a station",
        [
            {"park_proximity"},
            {"evening_venues", "venue_evening"},
            {"station_lines", "station_walk"},
        ],
    ),
    ("Happy anywhere as long as there's a park nearby", [{"park_proximity"}]),
    (
        "We're looking for somewhere quiet to raise kids, with a "
        "playground and a decent primary school",
        [
            {"noise_exposure", "quiet_residential"},
            {"family_amenities", "play_space_proximity"},
            {"school_primary_attainment", "school_primary_nearby", "school_secondary_attainment"},
        ],
    ),
    ("A good local pub within stumbling distance", [{"evening_venues", "venue_evening"}]),
    ("Decent restaurants, nothing fancy", [{"foodie", "venue_food_drink", "venue_independent"}]),
    ("Somewhere that's well connected", [{"station_lines", "station_walk"}]),
    ("Give me trees and a river", [{"green_cover", "leafy"}, {"water_access", "waterside"}]),
    ("Must be in Tallowgate", [{"area:syn-n0021:only"}]),
    ("Not far from Pellam Cross", [{"journey:syn-p0012"}]),
    ("I want to be able to walk to a park in under ten minutes", [{"park_proximity"}]),
    (
        "High street shops I can get to on foot",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    ("Could you find me somewhere with good pubs?", [{"evening_venues", "venue_evening"}]),
    ("Near a park", [{"park_proximity"}]),
    ("quiet and leafy", [{"quiet_residential", "noise_exposure"}, {"leafy", "green_cover"}]),
    (
        "I want good schools",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    (
        "somewhere with lots of pubs and restaurants",
        [{"venue_evening", "evening_venues"}, {"venue_food_drink", "foodie", "venue_independent"}],
    ),
    ("close to a tube station", [{"station_walk", "station_lines"}]),
    ("I need a park nearby", [{"park_proximity"}]),
    (
        "We want a quiet area with good primary schools",
        [
            {"quiet_residential", "noise_exposure"},
            {"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"},
        ],
    ),
    ("a village feel", [{"village_feel"}]),
    ("I'd like to be near the river", [{"waterside", "water_access"}]),
    (
        "lively with good nightlife",
        [{"buzzy", "evening_venues"}, {"venue_evening", "evening_venues"}],
    ),
    (
        "Looking for a flat to rent near a station",
        [{"tenure:rent"}, {"station_walk", "station_lines"}],
    ),
    ("2 bed flat, £1,800 a month", [{"budget"}]),
    ("My budget is 1500 pcm", [{"budget"}]),
    ("I want to buy", [{"tenure:buy"}]),
    ("up to £400k", [{"budget"}]),
    ("30 minutes to Pellam Cross", [{"journey:syn-p0012"}]),
    ("I work at Pellam Infirmary", [{"journey:syn-p0028"}]),
    ("within 40 minutes of Cindermoor Works by bike", [{"journey:syn-p0021"}]),
    ("I commute to Foxholt Market", [{"journey:syn-p0019"}]),
    ("near Wexmoor University", [{"journey:syn-p0026"}]),
    ("only in Tallowgate", [{"area:syn-n0021:only"}]),
    ("avoid Cindermoor", [{"area:syn-n0003:exclude"}]),
    ("not Wexmoor please", [{"area:syn-n0023:exclude"}]),
    (
        "independent shops and a good high street",
        [{"venue_independent"}, {"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    ("green space is really important to me", [{"green_cover", "leafy"}]),
    ("low crime is essential", [{"crime_violence_robbery", "crime_burglary_theft"}]),
    ("clean air", [{"air_no2"}]),
    ("less traffic noise", [{"noise_exposure"}]),
    ("I'm looking for somewhere family friendly", [{"family_amenities"}]),
    ("theatres and museums", [{"culture_venues", "creative"}]),
    ("a playground within walking distance", [{"play_space_proximity", "family_amenities"}]),
    ("more parks please", [{"park_proximity"}]),
    ("I would love a good pub nearby", [{"venue_evening", "evening_venues"}]),
    (
        "somewhere historic with character",
        [{"historic_character", "homes_pre1919", "conservation_cover"}],
    ),
    ("well connected", [{"station_walk", "station_lines"}]),
    ("I want to live somewhere leafy", [{"leafy", "green_cover"}]),
    ("good food and coffee shops", [{"venue_food_drink", "foodie", "venue_independent"}]),
    (
        "We're looking for a family home near a good school",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("a short walk to the station", [{"station_walk", "station_lines"}]),
    (
        "quiet streets and lots of trees",
        [{"quiet_residential", "noise_exposure"}, {"leafy", "green_cover"}],
    ),
    (
        "parks and playgrounds for the kids",
        [{"park_proximity"}, {"play_space_proximity", "family_amenities"}],
    ),
    (
        "a nice neighbourhood with cafes and restaurants",
        [{"venue_food_drink", "foodie", "venue_independent"}],
    ),
    (
        "Hi, I'm looking for somewhere quiet with a park",
        [{"quiet_residential", "noise_exposure"}, {"park_proximity"}],
    ),
    ("I'm moving to Quillhaven and want to be near a station", [{"station_walk", "station_lines"}]),
    (
        "we have two kids so schools matter a lot",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("arty area with galleries and live music", [{"culture_venues", "creative"}]),
    ("I love being by the water", [{"waterside", "water_access"}]),
    ("A garden would be nice, and a park nearby", [{"park_proximity"}]),
    (
        "walking distance to shops and a station",
        [
            {"highstreet_access", "strong_high_street", "venue_independent"},
            {"station_walk", "station_lines"},
        ],
    ),
    ("budget of £2,000 per month for a two bed", [{"budget"}]),
    ("studio flat under £1,200", [{"budget"}]),
    ("I cycle to work at Kindlewharf Studios", [{"journey:syn-p0020"}]),
    ("no more than 45 minutes to Tallowgate Guild Quarter", [{"journey:syn-p0018"}]),
    ("my office is in Pellam Exchange", [{"journey:syn-p0017"}]),
    ("I study at Kindlewharf School of Art", [{"journey:syn-p0027"}]),
    ("somewhere with a bit of a buzz", [{"buzzy", "evening_venues"}]),
    ("peace and quiet", [{"quiet_residential", "noise_exposure"}]),
    ("period properties", [{"historic_character", "homes_pre1919", "conservation_cover"}]),
    ("I want a conservation area", [{"historic_character", "homes_pre1919", "conservation_cover"}]),
    ("plenty of green space and fresh air", [{"green_cover", "leafy"}, {"air_no2"}]),
    (
        "a really good high street is a must",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    (
        "schools are the top priority",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("the most important thing for us is a park", [{"park_proximity"}]),
    ("I'd prefer somewhere quiet", [{"quiet_residential", "noise_exposure"}]),
    ("ideally near a park", [{"park_proximity"}]),
    (
        "something with good transport links and a park",
        [{"station_walk", "station_lines"}, {"park_proximity"}],
    ),
    (
        "I want to be able to walk to the shops",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    (
        "restaurants and bars on my doorstep",
        [{"venue_food_drink", "foodie", "venue_independent"}, {"venue_evening", "evening_venues"}],
    ),
    ("We both work in Pellam Cross", [{"journey:syn-p0012"}]),
    ("renting, one bedroom, around £1,400 a month", [{"budget"}]),
    ("a house to buy for about 500k", [{"budget"}, {"tenure:buy"}]),
    (
        "leafy. quiet. near a park.",
        [{"leafy", "green_cover"}, {"quiet_residential", "noise_exposure"}, {"park_proximity"}],
    ),
    (
        "I want a park. I also want a station nearby.",
        [{"park_proximity"}, {"station_walk", "station_lines"}],
    ),
    (
        "Moving next month. Need somewhere quiet near a station.",
        [{"quiet_residential", "noise_exposure"}, {"station_walk", "station_lines"}],
    ),
    ("somewhere nice and quiet", [{"quiet_residential", "noise_exposure"}]),
    (
        "must be near a primary school",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    (
        "cafes, bars and restaurants nearby",
        [{"venue_food_drink", "foodie", "venue_independent"}, {"venue_evening", "evening_venues"}],
    ),
    (
        "a buzzy area with great pubs",
        [{"buzzy", "evening_venues"}, {"venue_evening", "evening_venues"}],
    ),
    ("I like villages", [{"village_feel"}]),
    ("lots of culture", [{"culture_venues", "creative"}]),
)
THEIRS = 90

# Written after the vocabulary was settled, and never used to settle it.
HELD_OUT: tuple[tuple[str, Wishes], ...] = (
    ("My partner and I are after a two bed near a park", [{"park_proximity"}]),
    ("Somewhere I can walk the dog", [{"park_proximity"}]),
    (
        "Great schools nearby",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("I'd love a proper local pub", [{"venue_evening", "evening_venues"}]),
    (
        "A lively high street with plenty going on",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    ("Easy commute to Pellam Cross", [{"journey:syn-p0012"}]),
    ("I need to get to Cindermoor Works in under 40 minutes", [{"journey:syn-p0021"}]),
    (
        "Quiet, green and near a station",
        [
            {"quiet_residential", "noise_exposure"},
            {"green_cover", "leafy"},
            {"station_walk", "station_lines"},
        ],
    ),
    (
        "We're hoping for a village feel with good schools",
        [
            {"village_feel"},
            {"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"},
        ],
    ),
    ("Anywhere near the canal", [{"waterside", "water_access"}]),
    ("Looking to buy a terraced house, budget £600k", [{"tenure:buy"}, {"budget"}]),
    ("Rent up to £1,600 pcm", [{"budget"}]),
    ("A one bed flat close to the tube", [{"station_walk", "station_lines"}]),
    ("Nice cafes and a decent bakery", [{"venue_food_drink", "foodie", "venue_independent"}]),
    ("I want parks and good transport", [{"park_proximity"}, {"station_walk", "station_lines"}]),
    ("Family friendly area with playgrounds", [{"play_space_proximity", "family_amenities"}]),
    ("Close to Wexmoor University please", [{"journey:syn-p0026"}]),
    ("Must be in Foxholt", [{"area:syn-n0007:only"}]),
    ("Leafy streets", [{"leafy", "green_cover"}]),
    ("I like a bit of nightlife", [{"venue_evening", "evening_venues"}]),
    ("Not far from a park", [{"park_proximity"}]),
    ("Somewhere arty", [{"culture_venues", "creative"}]),
    (
        "A strong high street and independent cafes",
        [{"highstreet_access", "strong_high_street", "venue_independent"}, {"venue_independent"}],
    ),
    (
        "I work from home so I want somewhere quiet with good coffee shops",
        [
            {"quiet_residential", "noise_exposure"},
            {"venue_food_drink", "foodie", "venue_independent"},
        ],
    ),
    (
        "Low crime and good schools",
        [
            {"crime_violence_robbery", "crime_burglary_theft"},
            {"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"},
        ],
    ),
    ("Near green space", [{"green_cover", "leafy"}]),
    ("I cycle, so within 25 minutes of Pellam Infirmary by bike", [{"journey:syn-p0028"}]),
    (
        "Historic, with lots of character",
        [{"historic_character", "homes_pre1919", "conservation_cover"}],
    ),
    ("Lots to do in the evenings", [{"venue_evening", "evening_venues"}]),
    ("Good air quality", [{"air_no2"}]),
    ("A park on my doorstep", [{"park_proximity"}]),
    (
        "Restaurants, bars and a cinema",
        [
            {"venue_food_drink", "foodie", "venue_independent"},
            {"venue_evening", "evening_venues"},
            {"culture_venues", "creative"},
        ],
    ),
    ("I want to be by the river", [{"waterside", "water_access"}]),
    (
        "Primary schools with good results",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("Somewhere peaceful", [{"quiet_residential", "noise_exposure"}]),
    ("We need two bedrooms and a park nearby", [{"park_proximity"}]),
    ("Station within a ten minute walk", [{"station_walk", "station_lines"}]),
    ("Vibrant area with live music", [{"buzzy", "evening_venues"}, {"culture_venues", "creative"}]),
    ("I'm a renter looking for a studio under £1,100", [{"budget"}]),
    ("Close to shops", [{"highstreet_access", "strong_high_street", "venue_independent"}]),
    ("Trees and parks", [{"leafy", "green_cover"}, {"park_proximity"}]),
    (
        "Pubs and restaurants within walking distance",
        [{"venue_evening", "evening_venues"}, {"venue_food_drink", "foodie", "venue_independent"}],
    ),
    (
        "I would like somewhere with a good secondary school",
        [{"school_primary_nearby", "school_primary_attainment", "school_secondary_attainment"}],
    ),
    ("Waterside", [{"waterside", "water_access"}]),
    ("A calm, residential street", [{"quiet_residential", "noise_exposure"}]),
    ("I want to live near my work at Foxholt Market", [{"journey:syn-p0019"}]),
    ("35 minutes to Tallowgate Guild Quarter by train", [{"journey:syn-p0018"}]),
    (
        "Somewhere with character and period homes",
        [{"historic_character", "homes_pre1919", "conservation_cover"}],
    ),
    ("Good for kids", [{"play_space_proximity", "family_amenities"}]),
    ("Lots of independent shops", [{"venue_independent"}]),
    ("An area with a village vibe", [{"village_feel"}]),
    (
        "Quiet but well connected",
        [{"quiet_residential", "noise_exposure"}, {"station_walk", "station_lines"}],
    ),
    ("Avoid Pellam Cross", [{"area:syn-n0018:exclude"}]),
    ("Parks are really important to us", [{"park_proximity"}]),
    (
        "A high street I can walk to",
        [{"highstreet_access", "strong_high_street", "venue_independent"}],
    ),
    (
        "Green and leafy with a playground",
        [{"green_cover", "leafy"}, {"play_space_proximity", "family_amenities"}],
    ),
    ("I want to rent a two bedroom flat for £2,000 a month", [{"tenure:rent"}, {"budget"}]),
    ("Museums and galleries", [{"culture_venues", "creative"}]),
    ("A place with a real buzz", [{"buzzy", "evening_venues"}]),
    ("Fresh air and open space", [{"air_no2"}]),
)

# What is done to a thing, or was, or is by someone else.
_VERBS = (
    "hate loathe detest despise dislike resent dread fear shun dodge escape flee leave left quit "
    "stop stopped skip ditch drop scrap ban veto cancel reject refuse decline oppose tolerate "
    "endure suffer survive regret miss missed lack lacks forgot delete exclude except wanted "
    "needed liked loved wants needs likes loves hates works worked studies studied used was did "
    "had been went gone came became seemed thought knew said told asked heard saw wish wished "
    "hope hoped doubt doubted wonder wondered guess guessed suppose supposed reckon imagine "
    "imagined pretend pretended joke joked kidding laughed cried moaned complained argued "
    "disagreed agree agreed swear swore promise promised consider considered reconsider changed "
    "switched swapped moved moving sold bought rented lost found got gets getting keep kept keeps "
    "lets put puts run ran runs drove drives fly flew sleep slept wake woke ate drank smoke "
    "smoked "
)
# What is said of a thing.
_ADJECTIVES = (
    "bad awful terrible horrible dreadful grim dire ghastly vile abysmal lousy naff tacky rubbish "
    "overrated pointless useless boring dull tedious annoying irritating exhausting draining "
    "depressing unbearable insufferable intolerable unimportant unnecessary unwanted irrelevant "
    "optional pricey cheap dear costly distant remote away miles beyond absent missing finished "
    "done wrong mistaken false fake ironic sarcastic former previous ancient dead empty least "
    "little minimal scarce rare few tiny small smaller smallest worse worst dirty grubby scruffy "
    "rough dodgy sketchy shabby ugly bleak soulless sterile bland another alternative opposite "
    "contrary reverse unlikely doubtful unsure uncertain impossible improbable hypothetical "
    "imaginary theoretical alleged "
)
# Who else might wish, and what a thing might be called.
_NOUNS = (
    "mistake dealbreaker nightmare disaster hell misery curse plague blight eyesore nuisance pain "
    "headache hassle bother chore burden drawback downside negative con flaw fault problem issue "
    "complaint objection exception exclusion limit minimum gap absence mum dad mother father "
    "brother sister son daughter wife husband partner girlfriend boyfriend ex friend mate "
    "colleague boss landlord neighbour stalker tenant cousin uncle aunt granny everyone everybody "
    "anyone anybody someone somebody nobody nothing none neither others they them he she him her "
    "your yours their theirs his hers whoever whatever yesterday tomorrow never always sometimes "
    "often once twice formerly previously lately question answer reason excuse story rumour myth "
    "lie irony dream fantasy "
)
# What is said in a word.
_SLANG = (
    "yuck ugh eww meh nah nope naw blah bleh pfft tsk hmm pass gross ick yikes oof boo hiss lol "
    "lmao rofl jk psych sike whatevs nvm idk tbh imo imho smh fml innit bruv pal dude cheers ta "
    "soz bye laters hard nay nowt owt summat "
)
# Ways of typing don't, not, never, without and less that a keyboard makes.
_MISSPELT = (
    "don;t don,t don.t dno't dnt dint dun dinnae donut font dob't do't n't nt dosent dosnt "
    "doesn;t isnt isn;t arent wont wouldnt can;t nto ont nott noot nit nnot noo nop noe knot "
    "naught nought n0t n0 nver neva nvr nevr wihtout wthout w/o withot lss les fewwer fwer avod "
    "aviod avoyd "
)
# Words that join, weigh, ask and compare.
_JOINING = (
    "although though however whereas while unless until if whether because since rather instead "
    "besides despite regardless otherwise else either nor yet still barely hardly scarcely rarely "
    "seldom almost nearly merely just even quite fairly pretty maybe perhaps possibly probably "
    "supposedly apparently allegedly ideally hopefully enough zero nil zilch nada who what why "
    "when where which how whose should could might may shall ought down above behind against "
    "versus minus sans "
)
# Words that have nothing to do with a home.
_ANYTHING = (
    "apple table window mountain ocean carpet engine pencil guitar violin helmet jacket candle "
    "mirror basket blanket bottle button camera castle cheese chicken cotton dragon feather "
    "finger flower forest garden hammer island jungle kitten ladder lemon marble napkin needle "
    "orange paper pepper pillow planet pocket rabbit ribbon rocket saddle salmon sandal shadow "
    "silver spider sponge spring square stable statue summer sunset ticket tiger timber tomato "
    "tunnel turtle valley velvet wallet whisper winter wizard yellow zebra anchor arrow badge "
    "barrel beacon bridge bucket cabin canyon cello cliff cloud comet coral crown dagger desert "
    "diamond dolphin eagle ember falcon fiddle galaxy glacier goblin harbor hazel honey ivory "
    "jasmine kettle lantern lizard magnet meadow nectar nutmeg olive otter paddle parrot pebble "
    "penguin piano pigeon quartz raven saffron "
)
UNKNOWN_WORDS: tuple[str, ...] = tuple(
    dict.fromkeys(
        word
        for words in (_VERBS, _ADJECTIVES, _NOUNS, _SLANG, _MISSPELT, _JOINING, _ANYTHING)
        for word in words.split()
    )
)
