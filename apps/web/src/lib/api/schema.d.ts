/**
 * Generated from contracts/openapi.json by `npm run gen:api`.
 * Never edited by hand: change the contract and generate again.
 */

export interface paths {
    readonly "/healthz": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Healthz
         * @description Whether the service is up. It says nothing about the release, so it has no `meta`.
         */
        readonly get: operations["healthz"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/areas": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * List Areas
         * @description Every area of the release, by id, and where each sits on every vibe.
         */
        readonly get: operations["list_areas"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/areas/geometry": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Get Geometry
         * @description The boundary of every area, as a GeoJSON feature collection.
         */
        readonly get: operations["get_geometry"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/areas/{id_or_slug}": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Get Area
         * @description One area: what the release holds about it, and the facts a profile page shows.
         */
        readonly get: operations["get_area"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/areas/{id_or_slug}/census": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Get Census
         * @description The census figures of one area, beside the figures of the whole city and nothing else.
         */
        readonly get: operations["get_census"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/compare": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Compare
         * @description Two to four areas side by side, the rows in the order of the person's own weights.
         */
        readonly post: operations["compare"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/explanations": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Explain Top
         * @description A few checked sentences about each of the top areas, and the facts they cite.
         */
        readonly post: operations["explain_top"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/interpret": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Interpret
         * @description Read a request in words into typed edits, and apply them to the spec.
         */
        readonly post: operations["interpret"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/meta": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Get Meta
         * @description The release that is loaded, the vocabulary, the defaults, the limits, and who reads.
         */
        readonly get: operations["get_meta"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/places/search": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Search Places
         * @description The places that match, best first.
         */
        readonly post: operations["search_places"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/rank": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Rank
         * @description Apply any edits to the spec, then rank every area of the release for it.
         */
        readonly post: operations["rank"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/shares": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly get?: never;
        readonly put?: never;
        /**
         * Create Share
         * @description Store a search and give back the id of a link to it.
         */
        readonly post: operations["create_share"];
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
    readonly "/v1/shares/{share_id}": {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        /**
         * Get Share
         * @description A shared search, ranked now on the release that is loaded.
         */
        readonly get: operations["get_share"];
        readonly put?: never;
        readonly post?: never;
        readonly delete?: never;
        readonly options?: never;
        readonly head?: never;
        readonly patch?: never;
        readonly trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** Applied */
        readonly Applied: {
            /** Changed */
            readonly changed: boolean;
            readonly group: components["schemas"]["OpsGroup"];
            /** Index */
            readonly index: number;
        };
        /**
         * AreaAction
         * @enum {string}
         */
        readonly AreaAction: "exclude" | "only" | "clear";
        /** AreaData */
        readonly AreaData: {
            readonly area: components["schemas"]["Neighbourhood"];
            /** Cost */
            readonly cost: readonly components["schemas"]["CostEstimate"][];
            /** Facts */
            readonly facts: readonly components["schemas"]["Fact"][];
            /** Features */
            readonly features: readonly components["schemas"]["FeatureValue"][];
            /** Neighbours */
            readonly neighbours: readonly components["schemas"]["AreaSummary"][];
            readonly portrait: components["schemas"]["Portrait"];
            /** Similar */
            readonly similar: readonly components["schemas"]["Similar"][];
            /** Stations */
            readonly stations: readonly components["schemas"]["StationAccess"][];
            /** Tags */
            readonly tags: readonly components["schemas"]["TagValue"][];
        };
        /** AreaEdit */
        readonly AreaEdit: {
            readonly action: components["schemas"]["AreaAction"];
            /** Area Id */
            readonly area_id: string;
            readonly provenance: components["schemas"]["EditProvenance"];
        };
        /** AreaRule */
        readonly AreaRule: {
            /** Area Id */
            readonly area_id: string;
            readonly provenance: components["schemas"]["Provenance"];
            readonly rule: components["schemas"]["AreaRuleKind"];
        };
        /**
         * AreaRuleKind
         * @enum {string}
         */
        readonly AreaRuleKind: "exclude" | "only";
        /** AreaSummary */
        readonly AreaSummary: {
            /** Area Id */
            readonly area_id: string;
            /** Borough */
            readonly borough: string;
            /** Centroid */
            readonly centroid: readonly [
                number,
                number
            ];
            /** Name */
            readonly name: string;
            /** Rankable */
            readonly rankable: boolean;
            /** Slug */
            readonly slug: string;
        };
        /** AreasData */
        readonly AreasData: {
            /** Areas */
            readonly areas: readonly components["schemas"]["AreaSummary"][];
            /** Bands */
            readonly bands: readonly components["schemas"]["VibeBands"][];
        };
        /**
         * Assumption
         * @description What was chosen for an edit because the text did not say.
         */
        readonly Assumption: {
            readonly code: components["schemas"]["AssumptionCode"];
            readonly group: components["schemas"]["OpsGroup"];
            /** Index */
            readonly index: number;
            /**
             * Word
             * @default
             */
            readonly word: string;
        };
        /**
         * AssumptionCode
         * @enum {string}
         */
        readonly AssumptionCode: "tenure" | "segment" | "strictness" | "mode" | "max_minutes" | "direction" | "weight" | "word";
        /**
         * BandMark
         * @description Where one area sits on one vibe: a band, one of five, and the bands it spans.
         *
         *     All three are `null` for an area that cannot be placed. It is never drawn
         *     in the middle. The score a vibe is ranked on is not here, and is never shown.
         */
        readonly BandMark: {
            /** Area Id */
            readonly area_id: string;
            /** Band */
            readonly band: number | null;
            /** Spread High */
            readonly spread_high: number | null;
            /** Spread Low */
            readonly spread_low: number | null;
        };
        /** Budget */
        readonly Budget: {
            /** Amount */
            readonly amount: number | null;
            readonly provenance: components["schemas"]["Provenance"];
            readonly segment: components["schemas"]["Segment"];
            readonly strictness: components["schemas"]["Strictness"];
            /** Weight */
            readonly weight: number;
        };
        /**
         * BudgetAction
         * @enum {string}
         */
        readonly BudgetAction: "set" | "clear" | "nudge";
        /** BudgetEdit */
        readonly BudgetEdit: {
            readonly action: components["schemas"]["BudgetAction"];
            /** Amount */
            readonly amount: number;
            readonly provenance: components["schemas"]["EditProvenance"];
            readonly segment: components["schemas"]["SegmentChoice"];
            readonly step: components["schemas"]["Step"];
            readonly strictness: components["schemas"]["StrictnessChoice"];
            readonly tenure: components["schemas"]["TenureChoice"];
        };
        /** BudgetFit */
        readonly BudgetFit: {
            /** As Of */
            readonly as_of: string;
            readonly confidence: components["schemas"]["Confidence"];
            /** Margin */
            readonly margin: number;
            /** Upper Quartile */
            readonly upper_quartile: number | null;
            /** Utility */
            readonly utility: number;
        };
        /**
         * CensusColumns
         * @description The heading of each column, in the order they are printed.
         */
        readonly CensusColumns: {
            /** City */
            readonly city: string;
            /** Count */
            readonly count: string;
            /** Label */
            readonly label: string;
            /** Share */
            readonly share: string;
        };
        /**
         * CensusKind
         * @description What a table counts. It is no `FeatureId` and no `TagId`: no spec or edit can name it.
         * @enum {string}
         */
        readonly CensusKind: "age" | "households" | "country_of_birth" | "ethnic_group" | "religion";
        /**
         * CensusLeftOut
         * @description Why an area has no figure for a table. Nothing is filled in for either.
         * @enum {string}
         */
        readonly CensusLeftOut: "too_few" | "not_held";
        /**
         * CensusOffer
         * @description What the closed block of an area's page says. It holds no figure and names no area.
         */
        readonly CensusOffer: {
            /** Available */
            readonly available: boolean;
            /** Heading */
            readonly heading: string;
            /** Intro */
            readonly intro: string;
        };
        /**
         * CensusPanel
         * @description The census of one area, as its page shows it. Every word but a button's is here.
         */
        readonly CensusPanel: {
            /** Area Id */
            readonly area_id: string;
            /** City */
            readonly city: string;
            /** Date Line */
            readonly date_line: string;
            /** Derivation Line */
            readonly derivation_line: string;
            /** Heading */
            readonly heading: string;
            /** Licence Line */
            readonly licence_line: string;
            /** Notes */
            readonly notes: readonly string[];
            /** Output Areas */
            readonly output_areas: number;
            /** Source Line */
            readonly source_line: string;
            /** Tables */
            readonly tables: readonly components["schemas"]["CensusPanelTable"][];
        };
        /**
         * CensusPanelRow
         * @description One row as it is printed: the area's figure, and the whole city's beside it.
         *
         *     `share` and `city_share` are words. `percent` and `city_percent` are the
         *     same shares as whole numbers, for the picture alone, and are `None`
         *     where the share is under 1 in 100. `count` is as it is printed, and is
         *     `None` where the share is under 1 in 100: a small count is never given.
         */
        readonly CensusPanelRow: {
            /** City Percent */
            readonly city_percent: number | null;
            /** City Share */
            readonly city_share: string;
            /** Code */
            readonly code: string;
            /** Count */
            readonly count: string | null;
            /** Depth */
            readonly depth: number;
            /** Heading */
            readonly heading: string;
            /** Label */
            readonly label: string;
            /** Percent */
            readonly percent: number | null;
            /** Share */
            readonly share: string;
        };
        /** CensusPanelTable */
        readonly CensusPanelTable: {
            /** Caption */
            readonly caption: string;
            readonly columns: components["schemas"]["CensusColumns"];
            /** Definition */
            readonly definition: string;
            readonly kind: components["schemas"]["CensusKind"];
            /** Left Out */
            readonly left_out: string | null;
            /** Note */
            readonly note: string | null;
            readonly reason: components["schemas"]["CensusLeftOut"] | null;
            /** Rows */
            readonly rows: readonly components["schemas"]["CensusPanelRow"][];
            /** Shown Only */
            readonly shown_only: string | null;
            /** Source Id */
            readonly source_id: string;
            /** Source Label */
            readonly source_label: string;
            /** Source Url */
            readonly source_url: string;
            /** Table Code */
            readonly table_code: string;
            /** Title */
            readonly title: string;
        };
        /** CharacterMark */
        readonly CharacterMark: {
            /** Area Id */
            readonly area_id: string;
            /** Band */
            readonly band: number | null;
            /** Fact Id */
            readonly fact_id: string;
            /** Spread High */
            readonly spread_high: number | null;
            /** Spread Low */
            readonly spread_low: number | null;
        };
        /** CharacterRow */
        readonly CharacterRow: {
            /** Marks */
            readonly marks: readonly components["schemas"]["CharacterMark"][];
            readonly tag_id: components["schemas"]["TagId"];
        };
        /**
         * Choice
         * @enum {string}
         */
        readonly Choice: "slowest" | "mean" | "typical" | "just_missed" | "none";
        /**
         * Clarify
         * @description An edit whose place or area could not be settled, and what to offer instead.
         */
        readonly Clarify: {
            readonly group: components["schemas"]["OpsGroup"];
            /** Index */
            readonly index: number;
            /** Options */
            readonly options: readonly components["schemas"]["ClarifyOption"][];
        };
        /** ClarifyOption */
        readonly ClarifyOption: {
            /** Id */
            readonly id: string;
            readonly kind: components["schemas"]["OptionKind"];
            /** Name */
            readonly name: string;
        };
        /**
         * Combine
         * @enum {string}
         */
        readonly Combine: "slowest" | "mean";
        /** Commute */
        readonly Commute: {
            /** Max Minutes */
            readonly max_minutes: number;
            readonly mode: components["schemas"]["Mode"];
            /** Place Id */
            readonly place_id: string;
            readonly provenance: components["schemas"]["Provenance"];
            readonly strictness: components["schemas"]["Strictness"];
        };
        /**
         * CommuteAction
         * @enum {string}
         */
        readonly CommuteAction: "add" | "update" | "remove";
        /** CommuteEdit */
        readonly CommuteEdit: {
            readonly action: components["schemas"]["CommuteAction"];
            /** Max Minutes */
            readonly max_minutes: number;
            readonly mode: components["schemas"]["ModeChoice"];
            /** Place Id */
            readonly place_id: string;
            readonly provenance: components["schemas"]["EditProvenance"];
            readonly step: components["schemas"]["Step"];
            readonly strictness: components["schemas"]["StrictnessChoice"];
        };
        /** CommuteLeg */
        readonly CommuteLeg: {
            /** Minutes */
            readonly minutes: number | null;
            /** Minutes Just Missed */
            readonly minutes_just_missed: number | null;
            /** Minutes Typical */
            readonly minutes_typical: number | null;
            readonly mode: components["schemas"]["Mode"];
            /** Place Id */
            readonly place_id: string;
            readonly status: components["schemas"]["TravelStatus"];
            /** Utility */
            readonly utility: number | null;
        };
        /** CompareBody */
        readonly CompareBody: {
            /** Area Ids */
            readonly area_ids: readonly string[];
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /** CompareCell */
        readonly CompareCell: {
            /** Area Id */
            readonly area_id: string;
            /** Contribution */
            readonly contribution: number | null;
            /** Fact Id */
            readonly fact_id: string | null;
            /** Percentile */
            readonly percentile: number | null;
            /** Utility */
            readonly utility: number | null;
            /** Value */
            readonly value: number | null;
        };
        /** CompareData */
        readonly CompareData: {
            /** Areas */
            readonly areas: readonly components["schemas"]["ComparedArea"][];
            /** Character */
            readonly character: readonly components["schemas"]["CharacterRow"][];
            /** Facts */
            readonly facts: readonly components["schemas"]["Fact"][];
            /** Rows */
            readonly rows: readonly components["schemas"]["CompareRow"][];
        };
        /**
         * CompareRow
         * @description One thing that counts, across the areas. The journeys have a row each.
         *
         *     Every cell of a journey's row is to the same place. The row is named as
         *     core keys a journey, `commute.<place_id>.<mode>`, and carries the weight
         *     of the journeys, which count as one thing between them.
         */
        readonly CompareRow: {
            /** Cells */
            readonly cells: readonly components["schemas"]["CompareCell"][];
            /** Component */
            readonly component: string;
            /** Label */
            readonly label: string;
            readonly place: components["schemas"]["NamedPlace"] | null;
            /** Weight */
            readonly weight: number;
        };
        /**
         * CompareStatus
         * @description `ranked`, or the reason the area was filtered or left unranked.
         *
         *     One enum and not a union of three, so that a generated client gets one
         *     type. A test holds it to `FilterReason` and `UnrankedReason`.
         * @enum {string}
         */
        readonly CompareStatus: "ranked" | "excluded" | "not_selected" | "over_budget" | "commute_cap" | "not_rankable" | "insufficient_data" | "character_unknown";
        /** ComparedArea */
        readonly ComparedArea: {
            /** Area Id */
            readonly area_id: string;
            /** Counted */
            readonly counted: number;
            /** Name */
            readonly name: string;
            /** Present */
            readonly present: number;
            readonly status: components["schemas"]["CompareStatus"];
        };
        /**
         * Confidence
         * @description What a cost rests on. The first three are of a range Burro worked out.
         * @enum {string}
         */
        readonly Confidence: "high" | "medium" | "low" | "unstated";
        /** Contribution */
        readonly Contribution: {
            /** Component */
            readonly component: string;
            /** Contribution */
            readonly contribution: number;
            /** Fact Ids */
            readonly fact_ids: readonly string[];
            /** Loss */
            readonly loss: number;
            /** Present */
            readonly present: boolean;
            /** Share */
            readonly share: number;
            /** Utility */
            readonly utility: number | null;
            /** Weight */
            readonly weight: number;
        };
        /**
         * CostEstimate
         * @description What a home of one kind costs in one area: a range, or one number where no range is known.
         *
         *     A row holds both quartiles or neither. A row with neither is a publisher's
         *     own median of what was paid for the homes sold in the twelve months that
         *     end with `as_of`. Nothing stands in for the range, and what the median
         *     rests on is `unstated`: the publisher gives no count of the sales.
         */
        readonly CostEstimate: {
            /** Area Id */
            readonly area_id: string;
            /** As Of */
            readonly as_of: string;
            readonly confidence: components["schemas"]["Confidence"];
            /** Lower Quartile */
            readonly lower_quartile: number | null;
            /** Median */
            readonly median: number;
            readonly segment: components["schemas"]["Segment"];
            /** Source Ids */
            readonly source_ids: readonly string[];
            readonly tenure: components["schemas"]["Tenure"];
            /** Upper Quartile */
            readonly upper_quartile: number | null;
        };
        /** Counts */
        readonly Counts: {
            /** Destinations */
            readonly destinations: number;
            /** Neighbourhoods */
            readonly neighbourhoods: number;
            /** Places */
            readonly places: number;
            /** Rankable */
            readonly rankable: number;
            /** Stations */
            readonly stations: number;
        };
        /**
         * Cutoffs
         * @description The longest journey the release routed, by mode. Anything longer is `beyond_cutoff`.
         */
        readonly Cutoffs: {
            /** Cycle */
            readonly cycle: number;
            /** Pt */
            readonly pt: number;
            /** Walk */
            readonly walk: number;
        };
        /** Defaults */
        readonly Defaults: {
            readonly buy: components["schemas"]["PreferenceSpec"];
            readonly rent: components["schemas"]["PreferenceSpec"];
        };
        /**
         * Describes
         * @description What a feature is a fact about. There is no value for who lives somewhere.
         * @enum {string}
         */
        readonly Describes: "place" | "buildings" | "events";
        /**
         * Dimension
         * @enum {string}
         */
        readonly Dimension: "crime" | "schools" | "green_water" | "air_noise" | "venues_culture" | "homes" | "station_access" | "services";
        /**
         * Direction
         * @enum {string}
         */
        readonly Direction: "more" | "less";
        /**
         * DirectionChoice
         * @enum {string}
         */
        readonly DirectionChoice: "more" | "less" | "default";
        /**
         * EditProvenance
         * @enum {string}
         */
        readonly EditProvenance: "stated" | "inferred" | "ui_edit";
        /** Envelope[AreaData] */
        readonly Envelope_AreaData_: {
            readonly data: components["schemas"]["AreaData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[AreasData] */
        readonly Envelope_AreasData_: {
            readonly data: components["schemas"]["AreasData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[CensusPanel] */
        readonly Envelope_CensusPanel_: {
            readonly data: components["schemas"]["CensusPanel"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[CompareData] */
        readonly Envelope_CompareData_: {
            readonly data: components["schemas"]["CompareData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[ExplanationsData] */
        readonly Envelope_ExplanationsData_: {
            readonly data: components["schemas"]["ExplanationsData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[GeometryData] */
        readonly Envelope_GeometryData_: {
            readonly data: components["schemas"]["GeometryData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[InterpretData] */
        readonly Envelope_InterpretData_: {
            readonly data: components["schemas"]["InterpretData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[MetaData] */
        readonly Envelope_MetaData_: {
            readonly data: components["schemas"]["MetaData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[PlacesData] */
        readonly Envelope_PlacesData_: {
            readonly data: components["schemas"]["PlacesData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[RankData] */
        readonly Envelope_RankData_: {
            readonly data: components["schemas"]["RankData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[ShareCreated] */
        readonly Envelope_ShareCreated_: {
            readonly data: components["schemas"]["ShareCreated"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** Envelope[ShareData] */
        readonly Envelope_ShareData_: {
            readonly data: components["schemas"]["ShareData"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** ErrorBody */
        readonly ErrorBody: {
            readonly code: components["schemas"]["ErrorCode"];
            /** Fields */
            readonly fields: readonly components["schemas"]["FieldProblem"][];
            /** Message */
            readonly message: string;
        };
        /**
         * ErrorCode
         * @enum {string}
         */
        readonly ErrorCode: "malformed_json" | "body_too_large" | "unsupported_media_type" | "internal_error" | "not_found" | "method_not_allowed" | "invalid_request" | "invalid_text" | "invalid_spec" | "invalid_operations" | "invalid_compare" | "invalid_query" | "unknown_place" | "unknown_area" | "area_not_found" | "share_not_found" | "release_changed" | "census_not_available";
        /** ErrorEnvelope */
        readonly ErrorEnvelope: {
            readonly error: components["schemas"]["ErrorBody"];
            readonly meta: components["schemas"]["Meta"];
        };
        /** ExplainedSentence */
        readonly ExplainedSentence: {
            /** Fact Ids */
            readonly fact_ids: readonly string[];
            readonly origin: components["schemas"]["SentenceOrigin"];
            /** Replaced */
            readonly replaced: boolean;
            /** Text */
            readonly text: string;
        };
        /** Explanation */
        readonly Explanation: {
            /** Area Id */
            readonly area_id: string;
            /** Missing */
            readonly missing: readonly components["schemas"]["ExplainedSentence"][];
            readonly orientation: components["schemas"]["ExplainedSentence"];
            /** Reasons */
            readonly reasons: readonly components["schemas"]["ExplainedSentence"][];
            readonly trade_off: components["schemas"]["ExplainedSentence"] | null;
        };
        /** ExplanationsBody */
        readonly ExplanationsBody: {
            /**
             * Limit
             * @default 3
             */
            readonly limit: number;
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /** ExplanationsData */
        readonly ExplanationsData: {
            /** Explanations */
            readonly explanations: readonly components["schemas"]["Explanation"][];
            /** Facts */
            readonly facts: readonly components["schemas"]["Fact"][];
            /** Spec Hash */
            readonly spec_hash: string;
        };
        /** Fact */
        readonly Fact: {
            /** Area Id */
            readonly area_id: string;
            /** As Of */
            readonly as_of: string;
            /** Fact Id */
            readonly fact_id: string;
            /** Key */
            readonly key: string;
            readonly kind: components["schemas"]["FactKind"];
            /** Label */
            readonly label: string;
            /** Names */
            readonly names: readonly string[];
            /** Numbers */
            readonly numbers: readonly string[];
            /** Slots */
            readonly slots: {
                readonly [key: string]: string;
            };
            /** Sources */
            readonly sources: readonly components["schemas"]["FactSource"][];
            /** Synthetic */
            readonly synthetic: boolean;
            readonly template: components["schemas"]["TemplateId"];
        };
        /**
         * FactKind
         * @enum {string}
         */
        readonly FactKind: "area" | "feature" | "tag" | "cost" | "budget_fit" | "travel" | "station" | "missing" | "likeness";
        /** FactSource */
        readonly FactSource: {
            /** Name */
            readonly name: string;
            /** Publisher */
            readonly publisher: string;
            /** Source Id */
            readonly source_id: string;
        };
        /**
         * Family
         * @description The groups of the settings, in the order they are shown.
         * @enum {string}
         */
        readonly Family: "streets_homes" | "pace_food" | "green" | "daily_life";
        /** FamilyLabel */
        readonly FamilyLabel: {
            readonly family: components["schemas"]["Family"];
            /** Label */
            readonly label: string;
        };
        /**
         * FeatureId
         * @enum {string}
         */
        readonly FeatureId: "crime_violence_robbery" | "crime_burglary_theft" | "school_primary_nearby" | "school_primary_attainment" | "school_secondary_attainment" | "university_proximity" | "green_cover" | "park_proximity" | "play_space_proximity" | "water_access" | "air_no2" | "noise_exposure" | "venue_food_drink" | "venue_evening" | "venue_independent" | "culture_venues" | "highstreet_access" | "homes_flats" | "homes_pre1919" | "homes_density" | "conservation_cover" | "station_walk" | "station_lines" | "independents_nearby" | "centre_small" | "centre_compact" | "listed_buildings" | "homes_post2000" | "road_major_exposure" | "evening_cluster_exposure" | "land_industry" | "land_storage" | "land_transport_other" | "land_gardens" | "land_woodland" | "park_large_proximity" | "park_facilities" | "grocery_walk" | "incident_criminal_damage" | "incident_antisocial" | "private_outdoor_space" | "cuisine_variety" | "gp_walk" | "pharmacy_walk" | "venue_food_drink_per_homes" | "price_median" | "culture_venues_per_homes";
        /**
         * FeatureKind
         * @description What a person may want of a feature, which decides where it may stand.
         * @enum {string}
         */
        readonly FeatureKind: "taste" | "amenity" | "nuisance" | "on_request";
        /** FeatureValue */
        readonly FeatureValue: {
            /** Area Id */
            readonly area_id: string;
            /** Coverage */
            readonly coverage: number;
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Percentile */
            readonly percentile: number | null;
            /** Value */
            readonly value: number | null;
        };
        /** FeatureWeight */
        readonly FeatureWeight: {
            readonly direction: components["schemas"]["Direction"];
            readonly feature_id: components["schemas"]["FeatureId"];
            readonly provenance: components["schemas"]["Provenance"];
            /** Weight */
            readonly weight: number;
        };
        /** FieldProblem */
        readonly FieldProblem: {
            /** Path */
            readonly path: string;
            readonly problem: components["schemas"]["Problem"];
        };
        /**
         * FilterReason
         * @description In the order the filters are applied. An area stops at the first that catches it.
         * @enum {string}
         */
        readonly FilterReason: "excluded" | "not_selected" | "over_budget" | "commute_cap";
        /** Filtered */
        readonly Filtered: {
            /** Area Id */
            readonly area_id: string;
            readonly reason: components["schemas"]["FilterReason"];
        };
        /** FoundPlace */
        readonly FoundPlace: {
            /** Coarse Name */
            readonly coarse_name: string;
            readonly kind: components["schemas"]["PlaceKind"];
            /** Name */
            readonly name: string;
            /** Place Id */
            readonly place_id: string;
        };
        /** GeoFeature */
        readonly GeoFeature: {
            readonly geometry: components["schemas"]["Geometry"];
            /** Id */
            readonly id: string;
            readonly properties: components["schemas"]["GeoProperties"];
            /**
             * Type
             * @constant
             */
            readonly type: "Feature";
        };
        /** GeoProperties */
        readonly GeoProperties: {
            /** Area Id */
            readonly area_id: string;
        };
        /**
         * Geometry
         * @description A GeoJSON geometry object: a polygon or a multipolygon, in WGS84.
         */
        readonly Geometry: {
            /** Coordinates */
            readonly coordinates: readonly (readonly (readonly [
                number,
                number
            ])[])[] | readonly (readonly (readonly (readonly [
                number,
                number
            ])[])[])[];
            readonly type: components["schemas"]["GeometryType"];
        };
        /**
         * GeometryData
         * @description A GeoJSON `FeatureCollection`, as `geometry.json` holds it.
         */
        readonly GeometryData: {
            /** Features */
            readonly features: readonly components["schemas"]["GeoFeature"][];
            /**
             * Type
             * @constant
             */
            readonly type: "FeatureCollection";
        };
        /**
         * GeometryType
         * @enum {string}
         */
        readonly GeometryType: "Polygon" | "MultiPolygon";
        /**
         * GrittyVariant
         * @description Whether a release carries Gritty, the one vibe that counts recorded crime.
         * @enum {string}
         */
        readonly GrittyVariant: "a" | "b";
        /** Health */
        readonly Health: {
            /** Ok */
            readonly ok: boolean;
        };
        /**
         * Holds
         * @description What a release holds to answer a search with, apart from its measures and its vibes.
         *
         *     A first build holds neither. A client then says so where a person would
         *     look for it, and offers no control that could only be turned away.
         */
        readonly Holds: {
            /** Costs */
            readonly costs: boolean;
            /** Journeys */
            readonly journeys: boolean;
        };
        /** InterpretBody */
        readonly InterpretBody: {
            /**
             * Ask Model
             * @default true
             */
            readonly ask_model: boolean;
            readonly spec?: components["schemas"]["PreferenceSpec"] | null;
            /** Text */
            readonly text: string;
        };
        /** InterpretData */
        readonly InterpretData: {
            /** Applied */
            readonly applied: readonly components["schemas"]["Applied"][];
            /** Assumptions */
            readonly assumptions: readonly components["schemas"]["Assumption"][];
            /** Clarify */
            readonly clarify: readonly components["schemas"]["Clarify"][];
            /** Degraded */
            readonly degraded: boolean;
            readonly interpreter: components["schemas"]["InterpreterName"];
            /** Model Pending */
            readonly model_pending: boolean;
            /** Model Refused */
            readonly model_refused: boolean;
            /** Not In Release */
            readonly not_in_release: readonly components["schemas"]["NotInRelease"][];
            readonly notice: components["schemas"]["Notice"];
            /** Notice Text */
            readonly notice_text: string;
            readonly operations: components["schemas"]["Operations"];
            /** Places */
            readonly places: readonly components["schemas"]["NamedPlace"][];
            /** Rejected */
            readonly rejected: readonly components["schemas"]["Rejected"][];
            /** Rests On */
            readonly rests_on: readonly components["schemas"]["RestsOn"][];
            readonly spec: components["schemas"]["PreferenceSpec"];
            /** Spec Hash */
            readonly spec_hash: string;
            readonly status: components["schemas"]["InterpretStatus"];
            /** Suggestions */
            readonly suggestions: readonly components["schemas"]["Suggestion"][];
            /** Unmet */
            readonly unmet: readonly components["schemas"]["UnmetCategory"][];
            /** Unmet At */
            readonly unmet_at: readonly components["schemas"]["UnmetAt"][];
            /** Unread */
            readonly unread: readonly components["schemas"]["Span"][];
        };
        /**
         * InterpretStatus
         * @description In the order that decides the status: the first that applies wins.
         * @enum {string}
         */
        readonly InterpretStatus: "off_topic" | "policy_redirect" | "clarify" | "suggest" | "ok";
        /**
         * InterpreterName
         * @enum {string}
         */
        readonly InterpreterName: "rule" | "model";
        /** Meta */
        readonly Meta: {
            /** Engine Version */
            readonly engine_version: string;
            /** Preview */
            readonly preview: boolean;
            /** Release Id */
            readonly release_id: string;
            /** Synthetic */
            readonly synthetic: boolean;
        };
        /** MetaData */
        readonly MetaData: {
            /** Attributions */
            readonly attributions: readonly components["schemas"]["Source"][];
            /** Built At */
            readonly built_at: string;
            /** Catalogue Version */
            readonly catalogue_version: number;
            readonly census: components["schemas"]["CensusOffer"];
            readonly counts: components["schemas"]["Counts"];
            readonly defaults: components["schemas"]["Defaults"];
            /** Engine Version */
            readonly engine_version: string;
            /** Families */
            readonly families: readonly components["schemas"]["FamilyLabel"][];
            /** Features */
            readonly features: readonly components["schemas"]["Metric"][];
            readonly gritty_variant: components["schemas"]["GrittyVariant"];
            readonly holds: components["schemas"]["Holds"];
            readonly limits: components["schemas"]["ServedLimits"];
            /** Preview */
            readonly preview: boolean;
            readonly reader: components["schemas"]["Reader"];
            /** Recipes */
            readonly recipes: readonly components["schemas"]["RecipeHeld"][];
            /** Release Id */
            readonly release_id: string;
            /** Synthetic */
            readonly synthetic: boolean;
            /** Tags */
            readonly tags: readonly components["schemas"]["Tag"][];
        };
        /**
         * Method
         * @enum {string}
         */
        readonly Method: "measured" | "modelled" | "averaged";
        /**
         * Metric
         * @description A feature this release carries. Core decides what it is; the release says where from.
         */
        readonly Metric: {
            /** Definition */
            readonly definition: string;
            readonly describes: components["schemas"]["Describes"];
            readonly dimension: components["schemas"]["Dimension"];
            readonly family: components["schemas"]["Family"] | null;
            readonly feature_id: components["schemas"]["FeatureId"];
            /** In Likeness */
            readonly in_likeness: boolean;
            readonly kind: components["schemas"]["FeatureKind"];
            /** Label */
            readonly label: string;
            readonly method: components["schemas"]["Method"];
            readonly native_resolution: components["schemas"]["NativeResolution"];
            readonly polarity: components["schemas"]["Polarity"];
            /** Rankable */
            readonly rankable: boolean;
            /** Short Label */
            readonly short_label: string;
            /** Source Ids */
            readonly source_ids: readonly string[];
            /** Unit */
            readonly unit: string;
            /** Vintage */
            readonly vintage: string;
        };
        /**
         * Mode
         * @enum {string}
         */
        readonly Mode: "pt" | "cycle" | "walk";
        /**
         * ModeChoice
         * @enum {string}
         */
        readonly ModeChoice: "pt" | "cycle" | "walk" | "unchanged";
        /** MoneyLimits */
        readonly MoneyLimits: {
            /** Maximum */
            readonly maximum: number;
            /** Minimum */
            readonly minimum: number;
            /** Unit */
            readonly unit: number;
        };
        /**
         * NamedPlace
         * @description A place a spec names, by the release's own name for it. Never what was typed.
         *
         *     A spec holds a `place_id` and no name. A name says where someone works as
         *     an id does, so it is handled as one: served in a body, and in no log.
         */
        readonly NamedPlace: {
            readonly kind: components["schemas"]["PlaceKind"];
            /** Name */
            readonly name: string;
            /** Place Id */
            readonly place_id: string;
        };
        /**
         * NativeResolution
         * @enum {string}
         */
        readonly NativeResolution: "oa" | "lsoa" | "msoa" | "grid_1km" | "point" | "polygon" | "network";
        /** Neighbourhood */
        readonly Neighbourhood: {
            /** Aliases */
            readonly aliases: readonly string[];
            /** Area Id */
            readonly area_id: string;
            /** Borough */
            readonly borough: string;
            /** Centroid */
            readonly centroid: readonly [
                number,
                number
            ];
            /** Name */
            readonly name: string;
            /** Neighbours */
            readonly neighbours: readonly string[];
            /** Rankable */
            readonly rankable: boolean;
            /** Slug */
            readonly slug: string;
        };
        /**
         * NotInRelease
         * @description A thing a person asked for that the release holds for no area, so none is ranked on it.
         *
         *     A vibe that no area has a band for, a measure the release does not carry,
         *     a budget where it holds no cost of that kind of home, a journey where it
         *     names no place. It is said, so that a person is told what is not there
         *     yet. It is never offered, and nothing stands in for it.
         */
        readonly NotInRelease: {
            /** Label */
            readonly label: string;
            /** Spans */
            readonly spans: readonly components["schemas"]["Span"][];
            /** Target */
            readonly target: string;
        };
        /**
         * Notice
         * @enum {string}
         */
        readonly Notice: "none" | "neutral_places" | "off_topic";
        /** Operations */
        readonly Operations: {
            /** Area Ops */
            readonly area_ops: readonly components["schemas"]["AreaEdit"][];
            /** Budget Ops */
            readonly budget_ops: readonly components["schemas"]["BudgetEdit"][];
            /** Commute Ops */
            readonly commute_ops: readonly components["schemas"]["CommuteEdit"][];
            /** Setting Ops */
            readonly setting_ops: readonly components["schemas"]["SettingEdit"][];
            /** Tag Ops */
            readonly tag_ops: readonly components["schemas"]["TagEdit"][];
            /** Weight Ops */
            readonly weight_ops: readonly components["schemas"]["WeightEdit"][];
        };
        /**
         * OpsGroup
         * @description The six arrays of `Operations`, in the order the reducer applies them.
         * @enum {string}
         */
        readonly OpsGroup: "budget_ops" | "commute_ops" | "weight_ops" | "tag_ops" | "area_ops" | "setting_ops";
        /**
         * OptionKind
         * @description What a clarification offers: a place of one of the kinds of 2.7, or an area.
         * @enum {string}
         */
        readonly OptionKind: "station" | "district" | "postcode_district" | "university" | "hospital" | "school" | "landmark" | "area";
        /**
         * PlaceKind
         * @description In the order that breaks a tie between two matches of the same score.
         * @enum {string}
         */
        readonly PlaceKind: "station" | "district" | "postcode_district" | "university" | "hospital" | "school" | "landmark";
        /** PlaceSearchBody */
        readonly PlaceSearchBody: {
            /**
             * Limit
             * @default 8
             */
            readonly limit: number;
            /** Q */
            readonly q: string;
        };
        /** PlacesData */
        readonly PlacesData: {
            /** Places */
            readonly places: readonly components["schemas"]["FoundPlace"][];
        };
        /**
         * Polarity
         * @enum {string}
         */
        readonly Polarity: "less" | "more" | "either";
        /** Portrait */
        readonly Portrait: {
            /** Less */
            readonly less: readonly components["schemas"]["PortraitMark"][];
            /** More */
            readonly more: readonly components["schemas"]["PortraitMark"][];
            /** Others */
            readonly others: readonly components["schemas"]["PortraitMark"][];
            /** Scales */
            readonly scales: readonly components["schemas"]["PortraitMark"][];
            /** Unplaced */
            readonly unplaced: readonly components["schemas"]["PortraitMark"][];
        };
        /**
         * PortraitMark
         * @description One vibe on the portrait. The band and the sentence are in the fact it names.
         */
        readonly PortraitMark: {
            /** Fact Id */
            readonly fact_id: string;
            /** Figure Fact Id */
            readonly figure_fact_id: string | null;
            /** Parts */
            readonly parts: readonly components["schemas"]["PortraitPart"][];
            readonly tag_id: components["schemas"]["TagId"];
        };
        /**
         * PortraitPart
         * @description One part of a recipe, and the fact that holds this area's figure for it.
         */
        readonly PortraitPart: {
            /** Fact Id */
            readonly fact_id: string | null;
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Hundredths */
            readonly hundredths: number;
            readonly reading: components["schemas"]["TermReading"];
        };
        /** PreferenceSpec */
        readonly PreferenceSpec: {
            /** Areas */
            readonly areas: readonly components["schemas"]["AreaRule"][];
            readonly budget: components["schemas"]["Budget"];
            readonly commute_combine: components["schemas"]["Combine"];
            readonly commute_combine_from: components["schemas"]["Provenance"];
            /** Commute Weight */
            readonly commute_weight: number;
            readonly commute_weight_from: components["schemas"]["Provenance"];
            /** Commutes */
            readonly commutes: readonly components["schemas"]["Commute"][];
            readonly pt_basis: components["schemas"]["PtBasis"];
            readonly pt_basis_from: components["schemas"]["Provenance"];
            /**
             * Schema Version
             * @constant
             */
            readonly schema_version: 1;
            /** Tags */
            readonly tags: readonly components["schemas"]["TagWeight"][];
            readonly tenure: components["schemas"]["Tenure"];
            readonly tenure_from: components["schemas"]["Provenance"];
            /** Weights */
            readonly weights: readonly components["schemas"]["FeatureWeight"][];
        };
        /**
         * Problem
         * @description What is wrong with one field. A code, never the value that was sent.
         * @enum {string}
         */
        readonly Problem: "missing" | "unknown_field" | "wrong_type" | "not_allowed" | "bad_format" | "out_of_range" | "invalid" | "unknown_place" | "unknown_area" | "segment_not_for_tenure" | "direction_not_allowed" | "not_in_release";
        /**
         * Provenance
         * @enum {string}
         */
        readonly Provenance: "stated" | "inferred" | "default" | "ui_edit";
        /**
         * Provider
         * @enum {string}
         */
        readonly Provider: "gemini" | "openai" | "deepseek" | "anthropic";
        /**
         * PtBasis
         * @enum {string}
         */
        readonly PtBasis: "typical" | "just_missed";
        /** RankBody */
        readonly RankBody: {
            /**
             * Limit
             * @default 20
             */
            readonly limit: number;
            readonly operations?: components["schemas"]["Operations"] | null;
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /** RankData */
        readonly RankData: {
            /** Applied */
            readonly applied: readonly components["schemas"]["Applied"][];
            /** Areas Listed */
            readonly areas_listed: number;
            /** Areas Ranked */
            readonly areas_ranked: number;
            /** Empty Spec */
            readonly empty_spec: boolean;
            /** Filtered */
            readonly filtered: readonly components["schemas"]["Filtered"][];
            /** Places */
            readonly places: readonly components["schemas"]["NamedPlace"][];
            /** Ranked */
            readonly ranked: readonly components["schemas"]["RankedArea"][];
            /** Rejected */
            readonly rejected: readonly components["schemas"]["Rejected"][];
            /** Scores */
            readonly scores: readonly components["schemas"]["Score"][];
            readonly spec: components["schemas"]["PreferenceSpec"];
            /** Spec Hash */
            readonly spec_hash: string;
            /** Unranked */
            readonly unranked: readonly components["schemas"]["Unranked"][];
        };
        /** RankedArea */
        readonly RankedArea: {
            /** Area Id */
            readonly area_id: string;
            readonly budget: components["schemas"]["BudgetFit"] | null;
            /** Contributions */
            readonly contributions: readonly components["schemas"]["Contribution"][];
            /** Legs */
            readonly legs: readonly components["schemas"]["CommuteLeg"][];
            /** Rank */
            readonly rank: number;
            /** Score */
            readonly score: number;
            /** Strip */
            readonly strip: readonly components["schemas"]["StripMark"][];
            /** Untested Filters */
            readonly untested_filters: readonly components["schemas"]["FilterReason"][];
            /** Weight Coverage */
            readonly weight_coverage: number;
        };
        /**
         * Reader
         * @description Who reads what a person types, and what people are told of it.
         *
         *     It is how the service is set, and no part of the release. A client shows
         *     `notice` by the box before anything is typed, as it is served, and writes
         *     no provider's name or terms of its own.
         */
        readonly Reader: {
            /** Company */
            readonly company: string | null;
            /** Model Reads */
            readonly model_reads: boolean;
            /** Notice */
            readonly notice: string;
            readonly provider: components["schemas"]["Provider"] | null;
            /** Settings Sent */
            readonly settings_sent: boolean;
            /** Terms Url */
            readonly terms_url: string | null;
        };
        /**
         * RecipeHeld
         * @description How much of one vibe's recipe a release carries, and what the vibe waits on.
         *
         *     It is of the release and of no area. An area may have a figure for fewer
         *     parts than the release carries, and its own fact says so.
         */
        readonly RecipeHeld: {
            /** Held */
            readonly held: number;
            /** Needed */
            readonly needed: number;
            /** Placed */
            readonly placed: boolean;
            readonly tag_id: components["schemas"]["TagId"];
            /** Waits On */
            readonly waits_on: readonly components["schemas"]["WaitsOn"][];
        };
        /**
         * RejectReason
         * @enum {string}
         */
        readonly RejectReason: "unknown_place" | "unknown_area" | "not_in_release" | "too_many_commutes" | "no_such_commute" | "out_of_range" | "segment_not_for_tenure" | "direction_not_allowed" | "crime_needs_explicit_request" | "mismatched_choice" | "nothing_to_change";
        /** Rejected */
        readonly Rejected: {
            readonly group: components["schemas"]["OpsGroup"];
            /** Index */
            readonly index: number;
            readonly reason: components["schemas"]["RejectReason"];
        };
        /**
         * RestsOn
         * @description Which words of the text an edit rests on: where they start and end, never the words.
         *
         *     `start` and `end` count the characters of the text as it was typed, as
         *     Python counts them, so `text[start:end]` is the words. An edit made of
         *     several parts, as a budget is of "renting", "2 bed" and "£1,500", has one
         *     of these for each part. They are for showing a person which of their
         *     words made each edit. Nothing stores or logs them.
         */
        readonly RestsOn: {
            /** End */
            readonly end: number;
            readonly group: components["schemas"]["OpsGroup"];
            /** Index */
            readonly index: number;
            /** Start */
            readonly start: number;
        };
        /** Score */
        readonly Score: {
            /** Area Id */
            readonly area_id: string;
            /** Counted */
            readonly counted: number;
            /** Present */
            readonly present: number;
            /** Score */
            readonly score: number;
        };
        /**
         * Segment
         * @enum {string}
         */
        readonly Segment: "room" | "studio" | "bed_1" | "bed_2" | "bed_3" | "bed_4plus" | "flat" | "terraced" | "semi_detached" | "detached";
        /**
         * SegmentChoice
         * @enum {string}
         */
        readonly SegmentChoice: "room" | "studio" | "bed_1" | "bed_2" | "bed_3" | "bed_4plus" | "flat" | "terraced" | "semi_detached" | "detached" | "unchanged";
        /**
         * SentenceOrigin
         * @enum {string}
         */
        readonly SentenceOrigin: "template" | "model";
        /**
         * ServedLimits
         * @description The limits of section 5.2, with the cutoffs of the release that is loaded.
         *
         *     A form that keeps to these never offers a value the reducer would refuse.
         */
        readonly ServedLimits: {
            /**
             * Budget Step Large Percent
             * @default 15
             */
            readonly budget_step_large_percent: number;
            /**
             * Budget Step Small Percent
             * @default 5
             */
            readonly budget_step_small_percent: number;
            /** @default {
             *       "maximum": 20000000,
             *       "minimum": 50000,
             *       "unit": 5000
             *     } */
            readonly buy: components["schemas"]["MoneyLimits"];
            readonly cutoff_minutes: components["schemas"]["Cutoffs"];
            /** Max Body Bytes */
            readonly max_body_bytes: number;
            /**
             * Max Commutes
             * @default 3
             */
            readonly max_commutes: number;
            /** Max Text */
            readonly max_text: number;
            /**
             * Minutes Max
             * @default 120
             */
            readonly minutes_max: number;
            /**
             * Minutes Min
             * @default 10
             */
            readonly minutes_min: number;
            /**
             * Minutes Step Large
             * @default 15
             */
            readonly minutes_step_large: number;
            /**
             * Minutes Step Small
             * @default 5
             */
            readonly minutes_step_small: number;
            /** Reason Min Utility */
            readonly reason_min_utility: number;
            /** @default {
             *       "maximum": 20000,
             *       "minimum": 300,
             *       "unit": 25
             *     } */
            readonly rent: components["schemas"]["MoneyLimits"];
            /** Trade Off Max Utility */
            readonly trade_off_max_utility: number;
            /**
             * Weight Step Large
             * @default 0.25
             */
            readonly weight_step_large: number;
            /**
             * Weight Step Small
             * @default 0.1
             */
            readonly weight_step_small: number;
            /**
             * Weight Unit
             * @default 0.05
             */
            readonly weight_unit: number;
        };
        /**
         * Setting
         * @enum {string}
         */
        readonly Setting: "commute_combine" | "pt_basis" | "commute_weight" | "budget_weight";
        /**
         * SettingAction
         * @enum {string}
         */
        readonly SettingAction: "set" | "nudge";
        /** SettingEdit */
        readonly SettingEdit: {
            readonly action: components["schemas"]["SettingAction"];
            readonly choice: components["schemas"]["Choice"];
            readonly provenance: components["schemas"]["EditProvenance"];
            readonly setting: components["schemas"]["Setting"];
            readonly step: components["schemas"]["Step"];
            /** Value */
            readonly value: number;
        };
        /** ShareBody */
        readonly ShareBody: {
            /**
             * Exact Destinations
             * @default false
             */
            readonly exact_destinations: boolean;
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /** ShareCreated */
        readonly ShareCreated: {
            /** Coarsened */
            readonly coarsened: boolean;
            /** Places */
            readonly places: readonly components["schemas"]["NamedPlace"][];
            /** Share Id */
            readonly share_id: string;
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /**
         * ShareData
         * @description A shared search, ranked now on the release that is loaded.
         */
        readonly ShareData: {
            /** Areas Listed */
            readonly areas_listed: number;
            /** Areas Ranked */
            readonly areas_ranked: number;
            /** Coarsened */
            readonly coarsened: boolean;
            /** Empty Spec */
            readonly empty_spec: boolean;
            /** Filtered */
            readonly filtered: readonly components["schemas"]["Filtered"][];
            /** Original Release Id */
            readonly original_release_id: string;
            /** Places */
            readonly places: readonly components["schemas"]["NamedPlace"][];
            /** Ranked */
            readonly ranked: readonly components["schemas"]["RankedArea"][];
            /** Scores */
            readonly scores: readonly components["schemas"]["Score"][];
            readonly spec: components["schemas"]["PreferenceSpec"];
            /** Spec Hash */
            readonly spec_hash: string;
            /** Stale */
            readonly stale: boolean;
            /** Unranked */
            readonly unranked: readonly components["schemas"]["Unranked"][];
        };
        /**
         * Similar
         * @description One of the areas most like this one. The sentence is in the `likeness` fact it names.
         */
        readonly Similar: {
            /** Area Id */
            readonly area_id: string;
            /** Fact Id */
            readonly fact_id: string;
        };
        /** Source */
        readonly Source: {
            /** Attribution */
            readonly attribution: string;
            /** Licence */
            readonly licence: string;
            /** Name */
            readonly name: string;
            /** Publisher */
            readonly publisher: string;
            /** Retrieved On */
            readonly retrieved_on: string;
            /** Source Id */
            readonly source_id: string;
            /** Url */
            readonly url: string;
        };
        /**
         * Span
         * @description A stretch of the text: where it starts and ends, counted as `RestsOn` counts.
         */
        readonly Span: {
            /** End */
            readonly end: number;
            /** Start */
            readonly start: number;
        };
        /** StationAccess */
        readonly StationAccess: {
            /** Area Id */
            readonly area_id: string;
            /** Lines */
            readonly lines: readonly string[];
            /** Name */
            readonly name: string;
            /** Nearest */
            readonly nearest: boolean;
            /** Station Id */
            readonly station_id: string;
            /** Step Free */
            readonly step_free: boolean;
            /** Walk Minutes */
            readonly walk_minutes: number;
        };
        /**
         * Step
         * @enum {string}
         */
        readonly Step: "none" | "up_small" | "up_large" | "down_small" | "down_large";
        /**
         * Strictness
         * @enum {string}
         */
        readonly Strictness: "soft" | "hard";
        /**
         * StrictnessChoice
         * @enum {string}
         */
        readonly StrictnessChoice: "soft" | "hard" | "unchanged";
        /**
         * StripMark
         * @description Where an area sits on one vibe, for the strip under its name. Shown, never scored.
         */
        readonly StripMark: {
            /** Asked */
            readonly asked: boolean;
            /** Band */
            readonly band: number;
            /** Fact Id */
            readonly fact_id: string;
            /** Spread High */
            readonly spread_high: number;
            /** Spread Low */
            readonly spread_low: number;
            readonly tag_id: components["schemas"]["TagId"];
            readonly toward: components["schemas"]["Toward"] | null;
        };
        /**
         * Suggestion
         * @description An offer: a thing that was noticed, in four parts. The person chooses.
         *
         *     What it would do (`does`), the person's own words (`spans`, shown within
         *     `shown`), what follows for areas (`follows`), and the choices. Every word
         *     is Burro's own. The person's words are never here: a client cuts them
         *     from the text it holds, by where they stand.
         */
        readonly Suggestion: {
            /** Add All */
            readonly add_all: string;
            /** Asks Place */
            readonly asks_place: boolean;
            /** Choices */
            readonly choices: readonly components["schemas"]["SuggestionChoice"][];
            /** Does */
            readonly does: string;
            /** Follows */
            readonly follows: string;
            /** Label */
            readonly label: string;
            readonly named_at: components["schemas"]["Span"] | null;
            /** Needs */
            readonly needs: string;
            /** Note */
            readonly note: string;
            /** Options */
            readonly options: readonly components["schemas"]["ClarifyOption"][];
            readonly read_by: components["schemas"]["InterpreterName"];
            /** Said */
            readonly said: readonly string[];
            readonly shown: components["schemas"]["Span"];
            /** Spans */
            readonly spans: readonly components["schemas"]["Span"][];
            /** Target */
            readonly target: string;
        };
        /**
         * SuggestionChoice
         * @description One way a person may take an offer, and the edits it would make.
         *
         *     It has a name of its own here because core has another `Choice`, what a
         *     setting is set to, and one document cannot hold two records of one name.
         */
        readonly SuggestionChoice: {
            readonly direction: components["schemas"]["SuggestionDirection"];
            /** Guess */
            readonly guess: boolean;
            /** Id */
            readonly id: string;
            /** Label */
            readonly label: string;
            readonly operations: components["schemas"]["Operations"];
        };
        /**
         * SuggestionDirection
         * @description What a person may choose of a thing the reader noticed. It never guesses one.
         * @enum {string}
         */
        readonly SuggestionDirection: "more" | "less" | "ignore";
        /** Tag */
        readonly Tag: {
            /** Cannot See */
            readonly cannot_see: readonly string[];
            readonly family: components["schemas"]["Family"];
            /** High End */
            readonly high_end: string | null;
            /** Label */
            readonly label: string;
            /** Lens */
            readonly lens: boolean;
            /** Low End */
            readonly low_end: string | null;
            /** Meaning */
            readonly meaning: string;
            readonly shape: components["schemas"]["TagShape"];
            /** Shelf Order */
            readonly shelf_order: number | null;
            readonly shelf_toward: components["schemas"]["Toward"] | null;
            /** Shelf Word */
            readonly shelf_word: string | null;
            /** Short Label */
            readonly short_label: string;
            /** Strip */
            readonly strip: boolean;
            /** Table */
            readonly table: boolean;
            readonly tag_id: components["schemas"]["TagId"];
            /** Terms */
            readonly terms: readonly components["schemas"]["TagTerm"][];
        };
        /** TagEdit */
        readonly TagEdit: {
            readonly action: components["schemas"]["WeightAction"];
            readonly provenance: components["schemas"]["EditProvenance"];
            readonly step: components["schemas"]["Step"];
            readonly tag_id: components["schemas"]["TagId"];
            readonly toward: components["schemas"]["TowardChoice"];
            /** Value */
            readonly value: number;
        };
        /**
         * TagId
         * @description On screen a tag is a vibe. Seven ids of catalogue version 1 are retired and never reused:
         *     buzzy, evening_venues, historic_character, creative, strong_high_street,
         *     near_universities and waterside.
         * @enum {string}
         */
        readonly TagId: "leafy" | "village_feel" | "pace" | "quiet_residential" | "built_age" | "everyday_on_foot" | "parks_close_by" | "homes" | "foodie" | "family_amenities" | "works_warehouses" | "street_character";
        /**
         * TagShape
         * @enum {string}
         */
        readonly TagShape: "scale" | "one_way";
        /** TagTerm */
        readonly TagTerm: {
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Hundredths */
            readonly hundredths: number;
            readonly reading: components["schemas"]["TermReading"];
        };
        /**
         * TagValue
         * @description Where one area sits on one vibe. `score` is for ranking and is never printed.
         *
         *     `band` is what is shown: one of five, counted from the low end. The
         *     spread is the bands the middle half of the area's homes span, so a mixed
         *     area is drawn as a range and never as a point in the middle.
         */
        readonly TagValue: {
            /** Area Id */
            readonly area_id: string;
            /** Band */
            readonly band: number | null;
            /** Coverage */
            readonly coverage: number;
            /** Raw */
            readonly raw: number | null;
            /** Score */
            readonly score: number | null;
            /** Spread High */
            readonly spread_high: number | null;
            /** Spread Low */
            readonly spread_low: number | null;
            readonly tag_id: components["schemas"]["TagId"];
        };
        /** TagWeight */
        readonly TagWeight: {
            readonly provenance: components["schemas"]["Provenance"];
            readonly tag_id: components["schemas"]["TagId"];
            /** @default high */
            readonly toward: components["schemas"]["Toward"];
            /** Weight */
            readonly weight: number;
        };
        /**
         * TemplateId
         * @enum {string}
         */
        readonly TemplateId: "area" | "feature" | "feature_crime" | "vibe" | "vibe_range" | "vibe_unknown" | "cost_rent" | "cost_buy" | "cost_buy_median" | "budget_under" | "budget_over" | "budget_under_median" | "budget_over_median" | "travel_pt" | "travel_pt_over" | "travel_other" | "travel_other_over" | "travel_beyond" | "station" | "station_nearby" | "missing" | "missing_journey" | "likeness" | "likeness_same";
        /**
         * Tenure
         * @enum {string}
         */
        readonly Tenure: "rent" | "buy";
        /**
         * TenureChoice
         * @enum {string}
         */
        readonly TenureChoice: "rent" | "buy" | "unchanged";
        /**
         * TermReading
         * @enum {string}
         */
        readonly TermReading: "high" | "low";
        /**
         * Toward
         * @description Which end of a vibe is asked for. A one-way vibe has the high end alone.
         * @enum {string}
         */
        readonly Toward: "high" | "low";
        /**
         * TowardChoice
         * @enum {string}
         */
        readonly TowardChoice: "high" | "low" | "default";
        /**
         * TravelStatus
         * @enum {string}
         */
        readonly TravelStatus: "ok" | "beyond_cutoff" | "missing";
        /**
         * UnmetAt
         * @description Something that was asked for which nothing measures, and where it was said.
         */
        readonly UnmetAt: {
            readonly category: components["schemas"]["UnmetCategory"];
            readonly span: components["schemas"]["Span"];
        };
        /**
         * UnmetCategory
         * @enum {string}
         */
        readonly UnmetCategory: "broadband" | "flood_risk" | "health_services" | "driving" | "listings" | "affordability_verdict" | "community_amenities" | "outside_the_city" | "street_cleanliness" | "upkeep" | "ratings" | "prices_and_hours" | "mobile_coverage" | "change_over_time" | "other";
        /** Unranked */
        readonly Unranked: {
            /** Area Id */
            readonly area_id: string;
            /** Missing */
            readonly missing: readonly string[];
            readonly reason: components["schemas"]["UnrankedReason"];
        };
        /**
         * UnrankedReason
         * @enum {string}
         */
        readonly UnrankedReason: "not_rankable" | "insufficient_data" | "character_unknown";
        /** VibeBands */
        readonly VibeBands: {
            /** Marks */
            readonly marks: readonly components["schemas"]["BandMark"][];
            readonly tag_id: components["schemas"]["TagId"];
        };
        /**
         * WaitsOn
         * @description A part of a recipe that a release carries no measure for. It is named, never filled in.
         */
        readonly WaitsOn: {
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Hundredths */
            readonly hundredths: number;
            /** Label */
            readonly label: string;
        };
        /**
         * WeightAction
         * @enum {string}
         */
        readonly WeightAction: "set" | "nudge" | "remove";
        /** WeightEdit */
        readonly WeightEdit: {
            readonly action: components["schemas"]["WeightAction"];
            readonly direction: components["schemas"]["DirectionChoice"];
            readonly feature_id: components["schemas"]["FeatureId"];
            readonly provenance: components["schemas"]["EditProvenance"];
            readonly step: components["schemas"]["Step"];
            /** Value */
            readonly value: number;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type Applied = components['schemas']['Applied'];
export type AreaAction = components['schemas']['AreaAction'];
export type AreaData = components['schemas']['AreaData'];
export type AreaEdit = components['schemas']['AreaEdit'];
export type AreaRule = components['schemas']['AreaRule'];
export type AreaRuleKind = components['schemas']['AreaRuleKind'];
export type AreaSummary = components['schemas']['AreaSummary'];
export type AreasData = components['schemas']['AreasData'];
export type Assumption = components['schemas']['Assumption'];
export type AssumptionCode = components['schemas']['AssumptionCode'];
export type BandMark = components['schemas']['BandMark'];
export type Budget = components['schemas']['Budget'];
export type BudgetAction = components['schemas']['BudgetAction'];
export type BudgetEdit = components['schemas']['BudgetEdit'];
export type BudgetFit = components['schemas']['BudgetFit'];
export type CensusColumns = components['schemas']['CensusColumns'];
export type CensusKind = components['schemas']['CensusKind'];
export type CensusLeftOut = components['schemas']['CensusLeftOut'];
export type CensusOffer = components['schemas']['CensusOffer'];
export type CensusPanel = components['schemas']['CensusPanel'];
export type CensusPanelRow = components['schemas']['CensusPanelRow'];
export type CensusPanelTable = components['schemas']['CensusPanelTable'];
export type CharacterMark = components['schemas']['CharacterMark'];
export type CharacterRow = components['schemas']['CharacterRow'];
export type Choice = components['schemas']['Choice'];
export type Clarify = components['schemas']['Clarify'];
export type ClarifyOption = components['schemas']['ClarifyOption'];
export type Combine = components['schemas']['Combine'];
export type Commute = components['schemas']['Commute'];
export type CommuteAction = components['schemas']['CommuteAction'];
export type CommuteEdit = components['schemas']['CommuteEdit'];
export type CommuteLeg = components['schemas']['CommuteLeg'];
export type CompareBody = components['schemas']['CompareBody'];
export type CompareCell = components['schemas']['CompareCell'];
export type CompareData = components['schemas']['CompareData'];
export type CompareRow = components['schemas']['CompareRow'];
export type CompareStatus = components['schemas']['CompareStatus'];
export type ComparedArea = components['schemas']['ComparedArea'];
export type Confidence = components['schemas']['Confidence'];
export type Contribution = components['schemas']['Contribution'];
export type CostEstimate = components['schemas']['CostEstimate'];
export type Counts = components['schemas']['Counts'];
export type Cutoffs = components['schemas']['Cutoffs'];
export type Defaults = components['schemas']['Defaults'];
export type Describes = components['schemas']['Describes'];
export type Dimension = components['schemas']['Dimension'];
export type Direction = components['schemas']['Direction'];
export type DirectionChoice = components['schemas']['DirectionChoice'];
export type EditProvenance = components['schemas']['EditProvenance'];
export type EnvelopeAreaData = components['schemas']['Envelope_AreaData_'];
export type EnvelopeAreasData = components['schemas']['Envelope_AreasData_'];
export type EnvelopeCensusPanel = components['schemas']['Envelope_CensusPanel_'];
export type EnvelopeCompareData = components['schemas']['Envelope_CompareData_'];
export type EnvelopeExplanationsData = components['schemas']['Envelope_ExplanationsData_'];
export type EnvelopeGeometryData = components['schemas']['Envelope_GeometryData_'];
export type EnvelopeInterpretData = components['schemas']['Envelope_InterpretData_'];
export type EnvelopeMetaData = components['schemas']['Envelope_MetaData_'];
export type EnvelopePlacesData = components['schemas']['Envelope_PlacesData_'];
export type EnvelopeRankData = components['schemas']['Envelope_RankData_'];
export type EnvelopeShareCreated = components['schemas']['Envelope_ShareCreated_'];
export type EnvelopeShareData = components['schemas']['Envelope_ShareData_'];
export type ErrorBody = components['schemas']['ErrorBody'];
export type ErrorCode = components['schemas']['ErrorCode'];
export type ErrorEnvelope = components['schemas']['ErrorEnvelope'];
export type ExplainedSentence = components['schemas']['ExplainedSentence'];
export type Explanation = components['schemas']['Explanation'];
export type ExplanationsBody = components['schemas']['ExplanationsBody'];
export type ExplanationsData = components['schemas']['ExplanationsData'];
export type Fact = components['schemas']['Fact'];
export type FactKind = components['schemas']['FactKind'];
export type FactSource = components['schemas']['FactSource'];
export type Family = components['schemas']['Family'];
export type FamilyLabel = components['schemas']['FamilyLabel'];
export type FeatureId = components['schemas']['FeatureId'];
export type FeatureKind = components['schemas']['FeatureKind'];
export type FeatureValue = components['schemas']['FeatureValue'];
export type FeatureWeight = components['schemas']['FeatureWeight'];
export type FieldProblem = components['schemas']['FieldProblem'];
export type FilterReason = components['schemas']['FilterReason'];
export type Filtered = components['schemas']['Filtered'];
export type FoundPlace = components['schemas']['FoundPlace'];
export type GeoFeature = components['schemas']['GeoFeature'];
export type GeoProperties = components['schemas']['GeoProperties'];
export type Geometry = components['schemas']['Geometry'];
export type GeometryData = components['schemas']['GeometryData'];
export type GeometryType = components['schemas']['GeometryType'];
export type GrittyVariant = components['schemas']['GrittyVariant'];
export type Health = components['schemas']['Health'];
export type Holds = components['schemas']['Holds'];
export type InterpretBody = components['schemas']['InterpretBody'];
export type InterpretData = components['schemas']['InterpretData'];
export type InterpretStatus = components['schemas']['InterpretStatus'];
export type InterpreterName = components['schemas']['InterpreterName'];
export type Meta = components['schemas']['Meta'];
export type MetaData = components['schemas']['MetaData'];
export type Method = components['schemas']['Method'];
export type Metric = components['schemas']['Metric'];
export type Mode = components['schemas']['Mode'];
export type ModeChoice = components['schemas']['ModeChoice'];
export type MoneyLimits = components['schemas']['MoneyLimits'];
export type NamedPlace = components['schemas']['NamedPlace'];
export type NativeResolution = components['schemas']['NativeResolution'];
export type Neighbourhood = components['schemas']['Neighbourhood'];
export type NotInRelease = components['schemas']['NotInRelease'];
export type Notice = components['schemas']['Notice'];
export type Operations = components['schemas']['Operations'];
export type OpsGroup = components['schemas']['OpsGroup'];
export type OptionKind = components['schemas']['OptionKind'];
export type PlaceKind = components['schemas']['PlaceKind'];
export type PlaceSearchBody = components['schemas']['PlaceSearchBody'];
export type PlacesData = components['schemas']['PlacesData'];
export type Polarity = components['schemas']['Polarity'];
export type Portrait = components['schemas']['Portrait'];
export type PortraitMark = components['schemas']['PortraitMark'];
export type PortraitPart = components['schemas']['PortraitPart'];
export type PreferenceSpec = components['schemas']['PreferenceSpec'];
export type Problem = components['schemas']['Problem'];
export type Provenance = components['schemas']['Provenance'];
export type Provider = components['schemas']['Provider'];
export type PtBasis = components['schemas']['PtBasis'];
export type RankBody = components['schemas']['RankBody'];
export type RankData = components['schemas']['RankData'];
export type RankedArea = components['schemas']['RankedArea'];
export type Reader = components['schemas']['Reader'];
export type RecipeHeld = components['schemas']['RecipeHeld'];
export type RejectReason = components['schemas']['RejectReason'];
export type Rejected = components['schemas']['Rejected'];
export type RestsOn = components['schemas']['RestsOn'];
export type Score = components['schemas']['Score'];
export type Segment = components['schemas']['Segment'];
export type SegmentChoice = components['schemas']['SegmentChoice'];
export type SentenceOrigin = components['schemas']['SentenceOrigin'];
export type ServedLimits = components['schemas']['ServedLimits'];
export type Setting = components['schemas']['Setting'];
export type SettingAction = components['schemas']['SettingAction'];
export type SettingEdit = components['schemas']['SettingEdit'];
export type ShareBody = components['schemas']['ShareBody'];
export type ShareCreated = components['schemas']['ShareCreated'];
export type ShareData = components['schemas']['ShareData'];
export type Similar = components['schemas']['Similar'];
export type Source = components['schemas']['Source'];
export type Span = components['schemas']['Span'];
export type StationAccess = components['schemas']['StationAccess'];
export type Step = components['schemas']['Step'];
export type Strictness = components['schemas']['Strictness'];
export type StrictnessChoice = components['schemas']['StrictnessChoice'];
export type StripMark = components['schemas']['StripMark'];
export type Suggestion = components['schemas']['Suggestion'];
export type SuggestionChoice = components['schemas']['SuggestionChoice'];
export type SuggestionDirection = components['schemas']['SuggestionDirection'];
export type Tag = components['schemas']['Tag'];
export type TagEdit = components['schemas']['TagEdit'];
export type TagId = components['schemas']['TagId'];
export type TagShape = components['schemas']['TagShape'];
export type TagTerm = components['schemas']['TagTerm'];
export type TagValue = components['schemas']['TagValue'];
export type TagWeight = components['schemas']['TagWeight'];
export type TemplateId = components['schemas']['TemplateId'];
export type Tenure = components['schemas']['Tenure'];
export type TenureChoice = components['schemas']['TenureChoice'];
export type TermReading = components['schemas']['TermReading'];
export type Toward = components['schemas']['Toward'];
export type TowardChoice = components['schemas']['TowardChoice'];
export type TravelStatus = components['schemas']['TravelStatus'];
export type UnmetAt = components['schemas']['UnmetAt'];
export type UnmetCategory = components['schemas']['UnmetCategory'];
export type Unranked = components['schemas']['Unranked'];
export type UnrankedReason = components['schemas']['UnrankedReason'];
export type VibeBands = components['schemas']['VibeBands'];
export type WaitsOn = components['schemas']['WaitsOn'];
export type WeightAction = components['schemas']['WeightAction'];
export type WeightEdit = components['schemas']['WeightEdit'];
export type $defs = Record<string, never>;
export interface operations {
    readonly healthz: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Health"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly list_areas: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_AreasData_"];
                };
            };
            /** @description The release the caller holds is still loaded */
            readonly 304: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly get_geometry: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_GeometryData_"];
                };
            };
            /** @description The release the caller holds is still loaded */
            readonly 304: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly get_area: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path: {
                readonly id_or_slug: string;
            };
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_AreaData_"];
                };
            };
            /** @description The release the caller holds is still loaded */
            readonly 304: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Not Found */
            readonly 404: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly get_census: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path: {
                readonly id_or_slug: string;
            };
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_CensusPanel_"];
                };
            };
            /** @description Not Found */
            readonly 404: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly compare: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["CompareBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_CompareData_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Not Found */
            readonly 404: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly explain_top: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["ExplanationsBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_ExplanationsData_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly interpret: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["InterpretBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_InterpretData_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly get_meta: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_MetaData_"];
                };
            };
            /** @description The release the caller holds is still loaded */
            readonly 304: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly search_places: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["PlaceSearchBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_PlacesData_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly rank: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["RankBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_RankData_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly create_share: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path?: never;
            readonly cookie?: never;
        };
        readonly requestBody: {
            readonly content: {
                readonly "application/json": components["schemas"]["ShareBody"];
            };
        };
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_ShareCreated_"];
                };
            };
            /** @description Bad Request */
            readonly 400: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Content Too Large */
            readonly 413: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unsupported Media Type */
            readonly 415: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
    readonly get_share: {
        readonly parameters: {
            readonly query?: never;
            readonly header?: never;
            readonly path: {
                readonly share_id: string;
            };
            readonly cookie?: never;
        };
        readonly requestBody?: never;
        readonly responses: {
            /** @description Successful Response */
            readonly 200: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["Envelope_ShareData_"];
                };
            };
            /** @description Not Found */
            readonly 404: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Gone */
            readonly 410: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Unprocessable Content */
            readonly 422: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
            /** @description Internal Server Error */
            readonly 500: {
                headers: {
                    readonly [name: string]: unknown;
                };
                content: {
                    readonly "application/json": components["schemas"]["ErrorEnvelope"];
                };
            };
        };
    };
}
