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
         * @description Every area of the release, by id.
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
         * @description The release that is loaded, the vocabulary, the defaults and the limits.
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
        };
        /**
         * AssumptionCode
         * @enum {string}
         */
        readonly AssumptionCode: "tenure" | "segment" | "strictness" | "mode" | "max_minutes" | "direction" | "weight";
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
            readonly upper_quartile: number;
            /** Utility */
            readonly utility: number;
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
            /** Facts */
            readonly facts: readonly components["schemas"]["Fact"][];
            /** Rows */
            readonly rows: readonly components["schemas"]["CompareRow"][];
        };
        /** CompareRow */
        readonly CompareRow: {
            /** Cells */
            readonly cells: readonly components["schemas"]["CompareCell"][];
            /** Component */
            readonly component: string;
            /** Label */
            readonly label: string;
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
        readonly CompareStatus: "ranked" | "excluded" | "not_selected" | "over_budget" | "commute_cap" | "not_rankable" | "insufficient_data";
        /** ComparedArea */
        readonly ComparedArea: {
            /** Area Id */
            readonly area_id: string;
            /** Name */
            readonly name: string;
            readonly status: components["schemas"]["CompareStatus"];
        };
        /**
         * Confidence
         * @enum {string}
         */
        readonly Confidence: "high" | "medium" | "low";
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
        /** CostEstimate */
        readonly CostEstimate: {
            /** Area Id */
            readonly area_id: string;
            /** As Of */
            readonly as_of: string;
            readonly confidence: components["schemas"]["Confidence"];
            /** Lower Quartile */
            readonly lower_quartile: number;
            /** Median */
            readonly median: number;
            readonly segment: components["schemas"]["Segment"];
            /** Source Ids */
            readonly source_ids: readonly string[];
            readonly tenure: components["schemas"]["Tenure"];
            /** Upper Quartile */
            readonly upper_quartile: number;
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
         * Dimension
         * @enum {string}
         */
        readonly Dimension: "crime" | "schools" | "green_water" | "air_noise" | "venues_culture" | "homes" | "station_access";
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
        readonly ErrorCode: "malformed_json" | "body_too_large" | "unsupported_media_type" | "internal_error" | "not_found" | "method_not_allowed" | "invalid_request" | "invalid_text" | "invalid_spec" | "invalid_operations" | "invalid_compare" | "invalid_query" | "unknown_place" | "unknown_area" | "area_not_found" | "share_not_found" | "release_changed";
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
        readonly FactKind: "area" | "feature" | "tag" | "cost" | "budget_fit" | "travel" | "station" | "missing";
        /** FactSource */
        readonly FactSource: {
            /** Name */
            readonly name: string;
            /** Source Id */
            readonly source_id: string;
        };
        /**
         * FeatureId
         * @enum {string}
         */
        readonly FeatureId: "crime_violence_robbery" | "crime_burglary_theft" | "school_primary_nearby" | "school_primary_attainment" | "school_secondary_attainment" | "university_proximity" | "green_cover" | "park_proximity" | "play_space_proximity" | "water_access" | "air_no2" | "noise_exposure" | "venue_food_drink" | "venue_evening" | "venue_independent" | "culture_venues" | "highstreet_access" | "homes_flats" | "homes_pre1919" | "homes_density" | "conservation_cover" | "station_walk" | "station_lines";
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
        /** Health */
        readonly Health: {
            /** Ok */
            readonly ok: boolean;
        };
        /** InterpretBody */
        readonly InterpretBody: {
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
            readonly notice: components["schemas"]["Notice"];
            /** Notice Text */
            readonly notice_text: string;
            readonly operations: components["schemas"]["Operations"];
            /** Rejected */
            readonly rejected: readonly components["schemas"]["Rejected"][];
            /** Rests On */
            readonly rests_on: readonly components["schemas"]["RestsOn"][];
            readonly spec: components["schemas"]["PreferenceSpec"];
            /** Spec Hash */
            readonly spec_hash: string;
            readonly status: components["schemas"]["InterpretStatus"];
            /** Unmet */
            readonly unmet: readonly components["schemas"]["UnmetCategory"][];
        };
        /**
         * InterpretStatus
         * @description In the order that decides the status: the first that applies wins.
         * @enum {string}
         */
        readonly InterpretStatus: "off_topic" | "policy_redirect" | "clarify" | "ok";
        /**
         * InterpreterName
         * @enum {string}
         */
        readonly InterpreterName: "rule" | "claude";
        /** Meta */
        readonly Meta: {
            /** Engine Version */
            readonly engine_version: string;
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
            readonly counts: components["schemas"]["Counts"];
            readonly defaults: components["schemas"]["Defaults"];
            /** Engine Version */
            readonly engine_version: string;
            /** Features */
            readonly features: readonly components["schemas"]["Metric"][];
            readonly limits: components["schemas"]["ServedLimits"];
            /** Release Id */
            readonly release_id: string;
            /** Synthetic */
            readonly synthetic: boolean;
            /** Tags */
            readonly tags: readonly components["schemas"]["Tag"][];
        };
        /**
         * Metric
         * @description A feature this release carries. Core decides what it is; the release says where from.
         */
        readonly Metric: {
            /** Definition */
            readonly definition: string;
            readonly dimension: components["schemas"]["Dimension"];
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Label */
            readonly label: string;
            readonly native_resolution: components["schemas"]["NativeResolution"];
            readonly polarity: components["schemas"]["Polarity"];
            /** Rankable */
            readonly rankable: boolean;
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
         * NativeResolution
         * @enum {string}
         */
        readonly NativeResolution: "oa" | "lsoa" | "grid_1km" | "point" | "polygon" | "network";
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
            /** Empty Spec */
            readonly empty_spec: boolean;
            /** Filtered */
            readonly filtered: readonly components["schemas"]["Filtered"][];
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
            /** Untested Filters */
            readonly untested_filters: readonly components["schemas"]["FilterReason"][];
            /** Weight Coverage */
            readonly weight_coverage: number;
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
            /** @default {
             *       "maximum": 20000,
             *       "minimum": 300,
             *       "unit": 25
             *     } */
            readonly rent: components["schemas"]["MoneyLimits"];
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
            /** Share Id */
            readonly share_id: string;
            readonly spec: components["schemas"]["PreferenceSpec"];
        };
        /**
         * ShareData
         * @description A shared search, ranked now on the release that is loaded.
         */
        readonly ShareData: {
            /** Coarsened */
            readonly coarsened: boolean;
            /** Empty Spec */
            readonly empty_spec: boolean;
            /** Filtered */
            readonly filtered: readonly components["schemas"]["Filtered"][];
            /** Original Release Id */
            readonly original_release_id: string;
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
        /** Tag */
        readonly Tag: {
            /** Label */
            readonly label: string;
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
            /** Value */
            readonly value: number;
        };
        /**
         * TagId
         * @enum {string}
         */
        readonly TagId: "village_feel" | "buzzy" | "leafy" | "creative" | "family_amenities" | "near_universities" | "waterside" | "strong_high_street" | "evening_venues" | "quiet_residential" | "foodie" | "historic_character";
        /** TagTerm */
        readonly TagTerm: {
            readonly feature_id: components["schemas"]["FeatureId"];
            /** Hundredths */
            readonly hundredths: number;
            readonly reading: components["schemas"]["TermReading"];
        };
        /** TagValue */
        readonly TagValue: {
            /** Area Id */
            readonly area_id: string;
            /** Coverage */
            readonly coverage: number;
            /** Raw */
            readonly raw: number | null;
            /** Score */
            readonly score: number | null;
            readonly tag_id: components["schemas"]["TagId"];
        };
        /** TagWeight */
        readonly TagWeight: {
            readonly provenance: components["schemas"]["Provenance"];
            readonly tag_id: components["schemas"]["TagId"];
            /** Weight */
            readonly weight: number;
        };
        /**
         * TemplateId
         * @enum {string}
         */
        readonly TemplateId: "area" | "feature" | "feature_crime" | "tag" | "cost_rent" | "cost_buy" | "budget_under" | "budget_over" | "travel_pt" | "travel_other" | "travel_beyond" | "station" | "station_nearby" | "missing";
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
         * TravelStatus
         * @enum {string}
         */
        readonly TravelStatus: "ok" | "beyond_cutoff" | "missing";
        /**
         * UnmetCategory
         * @enum {string}
         */
        readonly UnmetCategory: "broadband" | "flood_risk" | "health_services" | "driving" | "listings" | "affordability_verdict" | "community_amenities" | "outside_the_city" | "other";
        /** Unranked */
        readonly Unranked: {
            /** Area Id */
            readonly area_id: string;
            readonly reason: components["schemas"]["UnrankedReason"];
        };
        /**
         * UnrankedReason
         * @enum {string}
         */
        readonly UnrankedReason: "not_rankable" | "insufficient_data";
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
export type Budget = components['schemas']['Budget'];
export type BudgetAction = components['schemas']['BudgetAction'];
export type BudgetEdit = components['schemas']['BudgetEdit'];
export type BudgetFit = components['schemas']['BudgetFit'];
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
export type Dimension = components['schemas']['Dimension'];
export type Direction = components['schemas']['Direction'];
export type DirectionChoice = components['schemas']['DirectionChoice'];
export type EditProvenance = components['schemas']['EditProvenance'];
export type EnvelopeAreaData = components['schemas']['Envelope_AreaData_'];
export type EnvelopeAreasData = components['schemas']['Envelope_AreasData_'];
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
export type FeatureId = components['schemas']['FeatureId'];
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
export type Health = components['schemas']['Health'];
export type InterpretBody = components['schemas']['InterpretBody'];
export type InterpretData = components['schemas']['InterpretData'];
export type InterpretStatus = components['schemas']['InterpretStatus'];
export type InterpreterName = components['schemas']['InterpreterName'];
export type Meta = components['schemas']['Meta'];
export type MetaData = components['schemas']['MetaData'];
export type Metric = components['schemas']['Metric'];
export type Mode = components['schemas']['Mode'];
export type ModeChoice = components['schemas']['ModeChoice'];
export type MoneyLimits = components['schemas']['MoneyLimits'];
export type NativeResolution = components['schemas']['NativeResolution'];
export type Neighbourhood = components['schemas']['Neighbourhood'];
export type Notice = components['schemas']['Notice'];
export type Operations = components['schemas']['Operations'];
export type OpsGroup = components['schemas']['OpsGroup'];
export type OptionKind = components['schemas']['OptionKind'];
export type PlaceKind = components['schemas']['PlaceKind'];
export type PlaceSearchBody = components['schemas']['PlaceSearchBody'];
export type PlacesData = components['schemas']['PlacesData'];
export type Polarity = components['schemas']['Polarity'];
export type PreferenceSpec = components['schemas']['PreferenceSpec'];
export type Problem = components['schemas']['Problem'];
export type Provenance = components['schemas']['Provenance'];
export type PtBasis = components['schemas']['PtBasis'];
export type RankBody = components['schemas']['RankBody'];
export type RankData = components['schemas']['RankData'];
export type RankedArea = components['schemas']['RankedArea'];
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
export type Source = components['schemas']['Source'];
export type StationAccess = components['schemas']['StationAccess'];
export type Step = components['schemas']['Step'];
export type Strictness = components['schemas']['Strictness'];
export type StrictnessChoice = components['schemas']['StrictnessChoice'];
export type Tag = components['schemas']['Tag'];
export type TagEdit = components['schemas']['TagEdit'];
export type TagId = components['schemas']['TagId'];
export type TagTerm = components['schemas']['TagTerm'];
export type TagValue = components['schemas']['TagValue'];
export type TagWeight = components['schemas']['TagWeight'];
export type TemplateId = components['schemas']['TemplateId'];
export type Tenure = components['schemas']['Tenure'];
export type TenureChoice = components['schemas']['TenureChoice'];
export type TermReading = components['schemas']['TermReading'];
export type TravelStatus = components['schemas']['TravelStatus'];
export type UnmetCategory = components['schemas']['UnmetCategory'];
export type Unranked = components['schemas']['Unranked'];
export type UnrankedReason = components['schemas']['UnrankedReason'];
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
