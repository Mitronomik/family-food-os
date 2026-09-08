# PR6 nutrition data readiness

Status: **PR6 engine implementation ACCEPTED / MERGED; PR6 milestone NOT COMPLETE**.
PR6-DATA-A is ACCEPTED / MERGED in PR #19 at
`60908eb8270ef356eff8552855b4cc5d2aa9ee44`. The DATA-A findings below retain
their historical meaning. **B1** establishes the exact evidence/binding
foundation; **B2-A** establishes the bounded same-source quantity corrections
and audit v3 described below. B2-B is NOT AUTHORIZED; PR7+ remain UNAUTHORIZED.

## FACT

### Accepted baseline and reproducibility

[PR #18](https://github.com/Mitronomik/family-food-os/pull/18) merged at
`7c449672c039c66b8d475064462eba2a9f6d38e6`, the exact DATA-A starting main.
Accepted implementation: `0d08839216ddd40a3ef2f5fd84edb8f69b2447f6`;
merged delivery head: `9dffb5fcbc8ec0b3d4a1f36f5349d68c944f2bbe`.
The engine is accepted; data readiness and milestone closure are outstanding.

The [row audit](../../data/curation/pr6-data-a/conversion-gap-audit.json) contains
all **30 current RecipeVersions / 189 RecipeIngredient rows** exactly once.
It joins accepted recipe code, source ID/hash version, one-based production
ingredient position, food code and source amount text. The PR4 source position
is retained separately because omitted source alternatives make it differ from
production position. No generated database UUID is an audit identity.

| Production measure | Rows | Required | Optional | Distinct FoodIngredients |
| --- | ---: | ---: | ---: | ---: |
| g | 31 | 31 | 0 | N/A |
| ml | 123 | 120 | 3 | 55 |
| pcs | 35 | 34 | 1 | 19 |

The ml/pcs union is **65 FoodIngredients** (9 shared between those sets).
Required ml rows affect 30 recipes; optional ml rows affect 2. Required pcs rows
affect 20 recipes; optional pcs affects 1; all pcs rows affect 21 recipes.

The unchanged production Nutrition audit reports:

| Status | Recipes |
| --- | ---: |
| COMPLETE | 0 |
| COMPLETE_WITH_WARNINGS | 0 |
| CONDITIONAL | 0 |
| INCOMPLETE | 30 |

| Runtime reason | Row occurrences | Affected recipes |
| --- | ---: | ---: |
| MISSING_DENSITY | 123 | 30 |
| UNSUPPORTED_PIECE_MASS | 35 | 21 |
| UNKNOWN_FIBER | 30 | 21 |
| ESTIMATION_STATUS_UNKNOWN | 189 | 30 |
| OPTIONAL_INGREDIENT | 4 | 2 |

Missing ingredient/profile and ESTIMATED_SOURCE counts are zero. These are
runtime diagnostics, not evidence that a current profile or g input is
semantically correct. Reasons overlap. No total is made green by this audit.

Offline reproduction:

```sh
python3 scripts/validate_pr6_data_a.py
AI_ENABLED=false python3 -m pytest -q backend/app/tests/test_pr6_data_a_research.py
AI_ENABLED=false python3 -m pytest -q -s backend/app/tests/test_nutrition_catalogue.py
```

The [summary](../../data/curation/pr6-data-a/summary.json) is generated from the
curated rows (`--write-summary`); numeric candidates are checked with Decimal
against retained source portions. Research itself is a reviewed curation step,
not an automatic semantic classifier. Ordinary regression uses no network.
450 protected seed, accepted PR4 evidence, runtime/schema/frontend and baseline
audit files have SHA-256 checks; Git scope validation catches added changes.
The research validator is never imported by production.

### Sources actually consulted, in order

The [source manifest](../../data/curation/pr6-data-a/source-manifest.json)
contains **290 bounded records**, including identity-only and rejected evidence.
A manifest reference is not approval to apply that source: only the row's
`conversion_method.source_manifest_id` identifies its chosen numeric evidence.

1. **Original sources first:** all 30 recipes were reopened from 25 distinct
   accepted primary artifacts and their hashes recomputed against PR4. All
   matched. Live retrieval of the 25 exact URLs was attempted: four distinct
   documents (three CACFP cards and Harvest) matched; other responses were 403
   or non-document bodies. Accepted local artifacts supplied the remaining
   sources. This is a fresh inspection of accepted artifacts, not a claim that
   every website currently serves identical bytes. Saved/printed artifacts
   retain their original PR4 provenance and rights posture. No new raw source
   document, logo or photograph is committed. Ingredient lists, relevant notes,
   alternatives and directions were checked; key Harvest, Tabbouleh and chicken
   pages were also rendered and visually inspected. Original weights take
   precedence when they apply to the selected edible form.
2. **Official FDC CSV releases:**
   [Foundation April 2026 and SR Legacy April 2018](https://fdc.nal.usda.gov/download-datasets/)
   were downloaded on 2026-09-06. Archive hashes, food descriptions, publication
   dates, portion IDs, amount, measure, modifier, grams, data points and footnote
   are retained. Every current same-ID `food_portion` inventory was inspected
   before considering another food ID. Different-ID SR portions are explicitly
   estimates. The current nutrition seed descriptions match official food.csv.
   FDC weights represent edible food, exclude refuse, and are specific to the
   dataset type: [FDC weights documentation](https://fdc.nal.usda.gov/Foundation_Foods_Documentation/).
3. **[FAO/INFOODS Density Database v2 (2012)](https://www.fao.org/4/ap815e/ap815e.pdf):**
   relevant form descriptions and bibliography were inspected. BiblioID RC
   identifies Ruth Charrondiere's measurements at 21 °C / 393 m; KEN identifies
   the 2004 Kenya project, room temperature / 1,350 m. Raw-leaf spinach provides
   two estimate candidates. Cooked spinach, boiled cauliflower, other cuts,
   industrial bulk entries and specific gravity do not become exact household
   densities. No FNDDS group value is adopted.
4. **Other primary references:** USDA SR28 spice report, Health Canada CNF and
   FSANZ AUSNUT methodology were consulted for remaining gaps. CNF supplies
   compatible volume-weight evidence for
   [toasted whole sesame seeds](https://food-nutrition.canada.ca/cnf-fce/serving-portion?id=2521)
   and [plain fat-free Greek yogurt](https://food-nutrition.canada.ca/cnf-fce/serving-portion?id=6979).
   The [CNF guide](https://food-nutrition.canada.ca/cnf-fce/help-aide) identifies
   these pages as the 2015 publication, not a 2019 dataset release. Their
   unexposed derivation/sample count makes both estimate candidates. FSANZ's
   [food measures methodology](https://www.foodstandards.gov.au/science-data/food-nutrient-databases/ausnut/food-measures)
   describes mixed derivations; its workbook was unavailable through the web
   reader and no FSANZ number is adopted. Search scope/limitations are recorded
   in `TIER4-SEARCH`. No community, retailer or LLM conversion is used.

All source weights retain their published precision. Candidate displays use
six-place Decimal HALF_UP, with the original numerator/denominator retained so
implementations need not multiply by a pre-rounded ratio. Existing PR4
cup=240 ml, tablespoon=15 ml and teaspoon=5 ml are source-normalization
conventions, not claims that an arbitrary measured SI volume has the same
physical weight. A cup portion and a spoon portion may have separately rounded
weights; the source measure is preserved where available. Water's FDC liter
portion is used only for WATER; there is no universal 1 ml = 1 g fallback.

### Conversion decisions (158 ml/pcs rows)

| Primary decision | Rows | Affected recipes |
| --- | ---: | ---: |
| DIRECT_RECIPE_MASS | 0 | 0 |
| FDC_EXACT_PORTION | 66 | 28 |
| FDC_COMPATIBLE_ESTIMATE | 39 | 20 |
| INFOODS_EXACT_OR_STRONG_MATCH | 0 | 0 |
| INFOODS_COMPATIBLE_ESTIMATE | 2 | 2 |
| OTHER_SOURCE_EXACT | 0 | 0 |
| OTHER_SOURCE_ESTIMATE | 2 | 2 |
| FOOD_FORM_MISMATCH | 12 | 11 |
| CANONICAL_IDENTITY_MISMATCH | 0 | 0 |
| MEASURE_OR_SIZE_AMBIGUOUS | 36 | 19 |
| NO_ACCEPTABLE_SOURCE | 1 | 1 |

There are **66 exact / 43 estimated / 49 without numeric candidates**.
Implementation-ready: **66 exact, 0 estimated**. **92** conversion rows across
**28** recipes are not implementation-ready. All 43 estimates require a design
that represents conversion uncertainty, independently of nutrient-profile
uncertainty. The 31 g rows have no conversion decision/candidate: their semantic
and source-quantity findings remain visible and can block later data readiness.
No same-source edible direct mass was found for the currently blocked ml/pcs
rows: existing usable source masses are already g rows; chicken mass includes
bone and the spinach package is an unselected alternative.

### Semantic compatibility (all 189 rows)

| Semantic classification | Rows | Affected recipes |
| --- | ---: | ---: |
| MATCH | 63 | 24 |
| MATCH_WITH_FORM_QUALIFIER | 42 | 18 |
| ACCEPTED_SUBSTITUTION | 47 | 24 |
| FORM_MISMATCH | 17 | 15 |
| IDENTITY_MISMATCH | 1 | 1 |
| AMBIGUOUS | 19 | 16 |

These are row comparisons, not authorization to replace the accepted corpus.
The following are the complete form/identity mismatch findings; long recipe
codes plus positions address the corresponding row and its manifest evidence.

| Recipe / position | Food | Finding |
| --- | --- | --- |
| `CACFP6_CORN_EDAMAME_BLEND:4` | `CORN_SWEET` | Source frozen corn is thawed and drained; current profile is fresh raw kernels. Freezing/blanching/draining compatibility is not established by PR4 purchase coverage. |
| `CACFP6_TABBOULEH:6` | `CUCUMBER` | Peeled and seeded cucumber is weighed as used; current profile includes peel. Mass alone does not resolve edible-form composition. |
| `CACFP6_TABBOULEH:12` | `LEMON` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |
| `SNAP4_SPANISH_FRITTATA:1` | `POTATO` | Source specifies russet potatoes weighed scrubbed before boiling and peeling; current profile is gold potatoes without skin. Both cultivar and edible-weight basis differ. |
| `HARV6_FRESH_TOMATO_SALSA:2` | `APPLE` | Source peeled apple; profile Gala with skin. A with-skin chopped-apple portion is incompatible. |
| `HARV6_GARDEN_PASTA_SALAD:1` | `PASTA_DRY` | PR4 explicitly retained cooked macaroni under a dry-pasta purchase concept; current nutrition is dry pasta. Cooked mass must not be multiplied by dry nutrients. |
| `SNAP6_SPINACH_APPLE_SALAD:1` | `SPINACH` | Baby spinach source versus mature spinach profile; also ambiguous 2/3 of a 10-ounce package has been stored as the full 10-ounce mass. |
| `SNAP6_PEACH_CRISP:3` | `OATS_ROLLED` | PR4 kept quick-cooking oats in rolled-oat purchase family; current profile is specifically old fashioned. Processing/form equivalence requires review, not a shared bulk density. |
| `SNAP6_PEACH_CRISP:7` | `LEMON` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |
| `SNAP8_SOMALI_SUMMER_SALAD:2` | `LEMON` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |
| `WIC4_BUTTERNUT_SOUP:1` | `BUTTERNUT_SQUASH` | About 3 pounds describes whole squash before seeds/ends/skin are discarded and flesh is scooped after roasting. Runtime currently treats all of it as edible raw flesh. |
| `SNAP2_SIMPLE_GREEN_SMOOTHIE:6` | `STRAWBERRY` | PR4 selected all-one-fruit plain frozen strawberries. This is not an unsupported mixed-fruit choice, but the profile is raw strawberries and freezing/form/packing are not resolved. |
| `WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:6` | `CAULIFLOWER` | PR4 selected frozen cauliflower, not the steamed-fresh alternative. Current profile is raw; frozen florets versus riced form also requires an explicit choice. |
| `SNAP4_PEAR_ORANGE_SAUCE:2` | `ORANGE` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |
| `SNAP4_SPRING_VEGETABLE_SAUTE:4` | `POTATO` | Source tiny new potatoes are quartered with no peeling instruction; profile is gold without skin. New-potato form and size cannot be replaced by a mature size-specific portion. |
| `SNAP6_WALDORF_SALAD:7` | `LEMON` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |
| `SNAP4_BRAISED_CHICKEN_SPINACH:1` | `CHICKEN_THIGH` | Source 4 bone-in skinless thighs at 6 ounces each are gross purchase mass; current profile is boneless raw thigh. Bone refuse must be excluded by evidence, not a guessed yield. |
| `SNAP4_DILLED_FISH_FILLETS:2` | `LEMON` | Source juice uses whole-fruit purchase concept; current profile describes edible whole fruit, not juice. PR4 deliberately did not claim juice/fruit nutrition equivalence. |

The other **19 AMBIGUOUS** rows cover unspecified cultivar/type versus Gala,
Roma, yellow peach, Bartlett or navel profiles, plus generic mayonnaise,
margarine and dried-cranberry formulation/sweetening. Exact row reasons are in
the audit. These are unresolved representativeness questions, not a claim that
all such foods must become separate canonical ingredients.

Accepted substitutions are not falsely reported as identity errors. PR4
explicitly selected cheddar and fresh cauliflower for grilled cheese,
strawberries under the smoothie all-one-fruit option, Greek nonfat yogurt in
Waldorf salad, sweet red Yalta onion, sunflower oil and golden raisins. Each row
links the exact PR4 source position, quantity and normalization rationale under
[the localization policy](recipe-localization-and-substitution.md). A purchase
choice does not prove profile compatibility: frozen strawberries and juice
still need form-compatible nutrition evidence.

### Source-quantity and edible-weight findings

| Recipe / position | Finding requiring later review |
| --- | --- |
| `HARV6_FRESH_TOMATO_SALSA:1` | Accepted fresh 1-cup tomato branch has no gram weight. Stored 226.796185 g comes from 8 ounces in the unselected canned alternative; it is not a direct fresh-tomato mass. |
| `SNAP6_SPINACH_APPLE_SALAD:1` | PR4 explicitly retained ambiguous 2/3 package (10 ounces); production stores 283.495231 g without the package fraction. Resolve source quantity before accepting mass. |
| `SNAP6_SPINACH_APPLE_SALAD:2` | Source 1 1/2 apples (range 1-2); stored 1 pcs. No accepted policy selects 1 as the deterministic amount. |
| `SNAP6_SEARED_GREENS:1` | Source 1 1/2 pounds equals 680.388555 g; stored 226.796185 g. Review mixed-fraction normalization. |
| `WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:5` | Source 1/2 apple; stored 1 pcs. Review source normalization before any size-specific mass. |
| `SNAP4_BROWN_RICE_PILAF:1` | Source 1 1/2 cups means 360 ml under the accepted 240-ml cup convention; stored 120 ml. |

These six rows affect five recipes. A weight in an unselected alternative must
not become a direct mass for the selected food. Squash's approximate whole-food
weight and the frittata's potato purchase weight additionally need an edible
basis review. The chicken source supplies `4 × 6 oz = 680.388555 g` gross;
DATA-A deliberately leaves its edible-mass candidate null. A fresh spinach
bunch cannot acquire the frozen alternative's 10-ounce package weight.

### Is a single global density safe?

**No, not for this corpus as a general solution.** Concrete evidence:

- The same accepted CARROT code appears shredded, sliced and in medium/large
  pieces. The original corn card gives 1½ cups shredded = 6 oz; coleslaw gives
  ¾ cup shredded = 2 oz. Even their source-specific shredded ratios disagree.
  Preserve each recipe's explicit mass; do not average them into one density.
- SR raw carrots have different cup weights for chopped, grated and slices.
  The current Foundation carrot ID has no portions. Whole-piece mass is a
  separate measure from any of those volumes.
- Same-ID golden raisins have packed/unpacked cups of 165/145 g, and recipes
  omit packing. Neither number is silently selected.
- Same-ID thyme has 1 g per teaspoon leaves and 1.4 g ground; grinding is
  unspecified. Ground cumin cannot use whole-seed portions.
- Same-ID cheddar has a shredded cup; grated cheese without specified fineness
  is an estimate. Walnuts' chopped form is different from halves or ground.
- INFOODS raw sweet pepper cubes and half-rings differ, as do boiled and raw
  short macaroni. These corroborate the form dependency; they do not establish
  exact conversion for another shape or override nutrition identity.

Piece review is explicit on every one of the 35 pcs rows. Only the three
recipes that specify **large eggs** qualify for the same-ID 50.3-g edible egg
portion; six unspecified in-shell eggs do not. Medium/large produce candidates
retain source size labels and published size qualifiers; different-ID values
remain estimates. Unspecified apples, bananas, peaches, peppers, tomatoes,
cucumbers, ginger slices and fresh spinach bunch receive no numeric candidate.
Bread slices and garlic cloves have explicitly labelled population-average
estimate candidates; neither is an exact universal piece. No row authorizes a
global grams-per-piece field.

## ASSUMPTION

An exact class means exact **identity/measure evidence matching**, not a claim
that every real specimen weighs the reference mean. Generic SR alternatives,
cut-size approximations, cultivar/formulation representativeness, average
bread/clove portions, raw-leaf packing and CNF derivations carry the explicit
estimate or unresolved status. No hypothesis is silently added to production.

`estimated` is false only for exact-class numeric candidates, true for estimate
candidates, and **null when no candidate exists or conversion is inapplicable**.
This follows the task's null-for-inapplicable rule: null does not mean exact and
is not counted as an estimate. `implementation_ready` is always boolean and
means provenance-ready for a separately authorized implementation; it does not
mean runtime support exists. It is false for all estimates until the project
can represent and propagate conversion-specific estimation.

Recipe source quantities refer to the selected input/preparation stage, not the
final cooked dish mass. Cooking losses, absorption, discarded coating, bones,
peels and drained liquids must not be invented by a volume conversion.

## DECISION

Authorized for DATA-A only: retain all 189 accepted rows and PR4 provenance;
inspect original sources before external references; use the declared source
hierarchy; keep a controlled primary decision per ml/pcs row; distinguish
exact evidence, estimates and unresolved gaps; retain absent values as null;
make no runtime, schema, migration, recipe, ingredient or nutrition-seed edits.

The decision precedence is source/canonical food-form incompatibility first,
then source quantity/size ambiguity, then applicable evidence. A numeric estimate
may be retained for review alongside unresolved profile representativeness, but
can never be exact or ready. g rows are semantically audited with null primary
conversion decisions. `NO_ACCEPTABLE_SOURCE` means no applicable evidence was
established in the consulted sources; it is not a proof of universal absence.
Semantic classes are distinct from conversion classes and both are required.

The presence of this audit does not accept its implementation recommendations,
complete PR6, authorize DATA-B, or authorize PR7+.

## Historical DATA-A open question — smallest correct DATA-B

### Architecture comparison (recommendation, not implementation)

| Option | Fit to actual evidence | Provenance, duplication and immutability |
| --- | --- | --- |
| A: global FoodIngredient density + piece mass | Small schema surface, but fails raw/cooked, juice/fruit, packing, chopping, size and refuse cases. Potentially usable for a narrowly reviewed homogeneous liquid; unsafe as the general corpus fix. | A mutable scalar loses portion/form and source history. Current field existence is not permission to populate it. |
| B: reusable form-aware measure profiles | Matches repeated salt/oil/spice portions and supports chopped/sliced/shredded profiles. Requires exact measure identity, edible basis and an explicit choice for each consuming row. | Versioned provenance can be reused; automatic code-only selection would recreate the bug. Building a general resolver now would exceed the minimum need. |
| C: RecipeIngredient-specific reviewed conversion | Correctly binds a particular immutable source row to its exact original mass or accepted portion. Can also record blocked semantic/profile assessments on g rows. | A separate versioned assessment references immutable RecipeVersion + position and exact nutrition-profile identity/version; it does not mutate recipe rows. Source evidence references avoid copying the same portion repeatedly. |
| D: publish normalized RecipeVersions | Necessary when source quantity, selected form or recipe truth is corrected. Converting every household amount to g is unnecessary and would discard useful cooking/purchasing measures. | Publish v2 only after explicit correction review; preserve v1. Retain original source measure text and useful pcs/ml quantity alongside reviewed edible mass where authorized. DATA-A publishes none. |

**Recommend a bounded C+B hybrid:** versioned row assessments/bindings (C),
referencing a small immutable table of reviewed source portions (B). Start with
explicit bindings from this finite audit, not an automatic form/AI resolver.
C alone would duplicate 66 matched source facts; general B alone cannot safely
choose among row forms or handle original recipe gross masses. The hybrid
stores source evidence once while making every application explicit. D is
reserved for separately approved corrections to recipe truth.

Minimum proposed responsibilities:

1. Source evidence retains source/release/hash, food description, portion
   amount/unit/form, exact gram numerator, source denominator, edible basis,
   uncertainty class and review/version history. No global bulk density is
   inferred from it. Source facts remain backend/repository-owned.
2. A versioned row assessment binds immutable RecipeVersion + ingredient
   position to selected evidence, food/profile source identity/version,
   source measure, compatibility decision, estimate flag and review reason.
   Unresolved semantic/quantity rows remain blocked, including existing g rows.
   **Converting the 66 exact matches alone must not let a recipe with a flagged
   g/profile mismatch acquire a misleading complete total.**
3. The on-demand Nutrition read scope reads those facts coherently and retains
   the assessment/evidence version in its result. A conversion-specific
   estimated warning must propagate per row and to required aggregate status,
   independently of `FoodNutritionProfile.estimated`; do not change a nutrient
   profile flag to encode a household-measure estimate. Required unresolved
   assessments keep required totals unavailable. Optional contributions stay
   separate under the accepted Nutrition policy.
4. Preserve immutable v1 contents. Source quantity mistakes and intended-food
   corrections need explicitly reviewed v2 publication, not an assessment that
   silently rewrites the recipe's quantity or chosen food. A changed current
   profile invalidates a former compatibility binding until reviewed. Historical
   replay must retain the exact evidence/profile/config references used.
5. Future ingestion follows the same source/resolve/measure-review/validate/
   publish path and writes explicit versioned bindings. Source household pcs/ml
   remain recipe truth where correct; reviewed edible grams are calculation
   evidence. Future Shopping can use the original purchase count/volume and
   separately approved purchase/refuse/package rules, without reverse-inferring
   grocery quantity from edible mass.

**Migration 0026 is likely required and recommended for this hybrid**, to add
versioned evidence/row-assessment storage through the existing custom SQLite
migration runner, synchronous Core repositories and UoW. The precise schema,
backfill, uniqueness, invalidation, backup/export and rollback strategy require
project approval. A static research JSON loader could avoid a migration but
would need an equally explicit versioned data-authority and persistence policy;
it is not automatically a smaller correct production model. DATA-A adds no
migration and chooses no implementation option.

Review must decide the first bounded implementation slice, whether and how to
accept the 43 estimates, which source-quantity/form corrections may publish new
versions, and the closure criteria for fiber/profile estimation and all required
recipe totals. PR7 MealPlan/Serving and every later milestone remain unauthorized.

### Verification record

Focused checks and delivery scope results are recorded in
[state/progress.md](../../state/progress.md#pr6-data-a-evidence). DATA-A uses the
curation tier of [proportional verification](verification-policy.md). Full
backend/launcher regression is not required because runtime remains byte-identical.


## DECISION — PR6-DATA-B1 exact evidence and row binding

Explicit B1 authorization selects the **C+B hybrid** and additive migration
`0026_nutrition_measure_evidence`. This is a supporting operation, not a new
numbered milestone. The implementation establishes immutable reusable
`MeasureMassEvidence` plus versioned `RecipeIngredientNutritionAssessment`.
No automatic form resolver, global density fill, piece-weight property, API,
frontend or AI is introduced. PR6 remains NOT COMPLETE.

Both relations are platform catalogue/review truth, with no Household owner.
Evidence preserves its own food identity, source/release/form and edible basis;
it does not belong to or prove a target FoodIngredient. Source quantity and gram
numerator are Decimal text, with no pre-rounded density replacing the fraction.
Changed evidence requires a new stable curated key and new immutable row.
Evidence update/delete is rejected; ordered assessment issues also retain history.
The repository inserts issues before their assessment under a deferred foreign
key, then inserts the assessment to seal the issue set. A SQLite trigger rejects
all later issue INSERTs for that assessment, whether current or historical;
UPDATE/DELETE remain forbidden. A dangling issue cannot survive transaction commit.
This correction is incorporated into migration 0026, without a new migration.
Disposable databases from earlier B1 builds use a fresh schema or the tested
accepted 0025→0026 path.

An assessment binds one immutable RecipeIngredient and the exact local
FoodNutritionProfile ID resolved from reviewed source name/id/version. The
repository appends consecutive positive review versions and atomically retires
the old current marker. A partial unique index prevents two current reviews.
Only the marker can be retired; assessment facts cannot be overwritten or
reactivated. The append transaction preserves the previous review on failure.
An unassessed row has no mass authority, including a g row.

Runtime compares the pinned profile ID to the current profile. Replacement
invalidates the old assessment (`NUTRITION_ASSESSMENT_PROFILE_STALE`) until an
explicit new review version is supplied. Old profile/review/evidence history
remains available. One NutritionReadScope sees recipe, ingredient, current and
pinned profiles, assessment, evidence and ordered issues in a coherent snapshot.
Results expose all these immutable calculation inputs; no totals are persisted.
The row policy has identifier `ROW_ASSESSMENT_EXACT_ONLY_B1_V1`.

### Promotion authority and deterministic mapping

Production artifacts live in
[`data/seed/nutrition_measure_evidence`](../../data/seed/nutrition_measure_evidence/manifest.json).
The manifest pins the exact DATA-A merged main above, SHA-256 for its row audit,
source manifest and summary, production recipe/profile input hashes, and both
promotion payload hashes. The offline promotion script translates existing
controlled decisions without researching or reclassifying a row. Calculation
never reads research JSON. The loader checks research bytes only for hashes.

Stable descriptors identify recipe code, source name/id/hash version, position,
food code, exact row fields and profile provenance/values. The loader resolves
local UUIDs; no database UUID is committed in production artifacts. It fails on
missing, stale or changed recipe/profile inputs, conflicting existing evidence
or assessments, schema/hash errors, or an unresolved reference. All evidence,
assessments and issues import in one UoW; no partial import survives.

Only the 56 source records selected by numeric DATA-A candidates are promoted,
as **57 immutable evidence records**. `FDC-PORTION-119620` supplies the same source
portion for exact shredded cheddar and estimated grated cheddar; separate
`:exact` / `:estimate` keys preserve both reviewed uncertainty classes. Other
sources are reused within their class. Date-only retrieval records have null
retrieval instants rather than fabricated times; the hashed DATA-A source keeps
the original date. The INFOODS density is stored as its published gram numerator
per 1 ml and remains estimated.

Status derivation first preserves all additional blockers, then adds semantic
and primary-decision issues. DATA-A's
`CONVERSION_ESTIMATION_PROPAGATION_NOT_IMPLEMENTED` is explicitly mapped to
`CONVERSION_ESTIMATE_NOT_ACCEPTED`; B1 represents the estimate but does not accept
it. Semantic AMBIGUOUS adds `PROFILE_REPRESENTATIVENESS_REVIEW`, including four g
rows where DATA-A had no additional-blocker entry. Form/identity and quantity
issues remain distinct. Issues are unique and lexically ordered.

| Current assessment status | Rows |
| --- | ---: |
| APPROVED_NO_CONVERSION | 20 |
| APPROVED_EXACT | 66 |
| REVIEW_REQUIRED_ESTIMATE | 37 |
| BLOCKED | 66 |
| Total | 189 |

The 31 g rows comprise 20 approved and **11 blocked** rows. All 43 estimated
candidates retain candidate evidence but no authoritative mass/nutrients:
37 are review-required and six also have profile representativeness blockers.
The remaining 49 conversion rows have no approved numeric source. Presence of
candidate evidence grants no calculation permission, and no estimate tolerance
or enabling flag exists in B1.

### Production audit v2

The [full deterministic report](../../data/seed/nutrition_measure_evidence/production-audit-v2.json)
contains all 30 recipes and 189 rows. Actual recipe status counts remain:
**0 COMPLETE, 0 COMPLETE_WITH_WARNINGS, 0 CONDITIONAL, 30 INCOMPLETE**.
66 exact conversions execute; unresolved required contributions still prevent
complete totals. The source quantities and RecipeVersion contents are unchanged.

| Runtime warning | Row occurrences |
| --- | ---: |
| MISSING_NUTRITION_ASSESSMENT | 0 |
| NUTRITION_ASSESSMENT_BLOCKED | 66 |
| CONVERSION_ESTIMATE_NOT_ACCEPTED | 43 |
| NUTRITION_ASSESSMENT_PROFILE_STALE | 0 |
| MISSING_MEASURE_EVIDENCE | 0 |
| UNKNOWN_FIBER | 30 |
| ESTIMATION_STATUS_UNKNOWN | 189 |
| ESTIMATED_SOURCE | 0 |
| OPTIONAL_INGREDIENT | 4 |
| MISSING_DENSITY / UNSUPPORTED_PIECE_MASS | 0 / 0 |
| MISSING_FOOD_INGREDIENT / MISSING_NUTRITION_PROFILE | 0 / 0 |

The **123 structured issue rows** contain: estimate non-acceptance 43, food form
mismatch 17, identity mismatch 1, measure/size ambiguity 36, no acceptable source
1, profile representativeness review 19, alternative weight misapplied 1, source
quantity ambiguity 1 and source quantity mismatch 4. Counts overlap by row.

Reproduce in an environment with the backend dependencies:

```sh
python3 scripts/promote_pr6_data_b1.py
AI_ENABLED=false python3 scripts/audit_pr6_data_b1.py
python3 scripts/validate_pr6_data_a.py --protected-revision 60908eb8270ef356eff8552855b4cc5d2aa9ee44
```

Import order is migrations → existing FoodIngredient seed → existing Recipe
seed → `python3 -m app.seed.nutrition_measure_evidence` (from `backend/`). The B1
loader does not duplicate or silently rerun prerequisite seed logic. First run
inserts 57 evidence and 189 assessments with 123 issues; identical second run
inserts zero and preserves the database dump. Fresh and populated 0025 upgrade
paths preserve all earlier schema/data; migration registration includes required
tables for backup/restore lineage validation. Rollback/recovery uses the existing
pre-upgrade backup, never destructive down-migration of review history.

### Remaining B2 decision boundary

B1 does not correct source quantities, forms, food mappings or profile values,
fill fiber, set profile estimation flags, or accept any estimated conversion.
Those data defects remain enforced. Source quantity/food changes require a
separately reviewed RecipeVersion v2; new rows do not inherit old assessments.
This was B1's remaining boundary. The separately authorized B2-A quantity-only
slice is established below. B2-B, estimate acceptance and PR6 closure remain
outside that authorization; PR7+ remain UNAUTHORIZED.


## DECISION — PR6-DATA-B2-A same-source quantity corrections

B2-A starts from accepted main `74bc80eb3ef0e34e17751856638ac58bbccb840e`
(PR #21 / PR6-INFRA). This changeset establishes same-source immutable revision
support, six reviewed source-quantity corrections, explicit assessments for the
new rows, and production audit v3. External provenance is distinct from internal
RecipeVersion identity; [architecture §13.2](architecture.md#132-same-source-recipeversion-revisions-pr6-data-b2-a)
owns the migration and deterministic repository contract.

### Source re-review and publication gate

All five accepted original artifacts were reopened on 2026-09-08 and their full
SHA-256 values matched PR4/DATA-A. The salsa ingredient page (PDF p55 / printed
p53) was also rendered and inspected. The accepted SNAP/WIC saved primary HTML
ingredient lists and directions were reopened, not replaced with live or secondary
recipes. Exact evidence references, old quantities, source text, reviewed results,
normalization notes and changed-row Nutrition decisions are in the
[six-row curation record](../../data/curation/pr6-data-b2a/source-quantity-corrections.json).
DATA-A's original findings remain historically intact.

| Recipe / position | Reviewed original source | v1 → v2 quantity | Outcome |
| --- | --- | --- | --- |
| HARV6_FRESH_TOMATO_SALSA:1 | Fresh branch is 1 cup; 8 oz belongs to the canned alternative | 226.796185 g → 240.000000 ml | CORRECTED / RESOLVED |
| SNAP6_SPINACH_APPLE_SALAD:1 | 2/3 package, with the package specified as 10 oz | 283.495231 g → 188.996821 g | CORRECTED / RESOLVED |
| SNAP6_SPINACH_APPLE_SALAD:2 | Primary amount 1 1/2 apples; parenthetical permits a 1–2 variation | 1.000000 pcs → 1.500000 pcs | CORRECTED / RESOLVED |
| SNAP6_SEARED_GREENS:1 | 1 1/2 lb for the retained kale alternative | 226.796185 g → 680.388555 g | CORRECTED / RESOLVED |
| WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:5 | 1/2 apple, added in the instructions | 1.000000 pcs → 0.500000 pcs | CORRECTED / RESOLVED |
| SNAP4_BROWN_RICE_PILAF:1 | 1 1/2 cups brown rice, before cooking | 120.000000 ml → 360.000000 ml | CORRECTED / RESOLVED |

The salad apple value is the source's explicit primary amount. It is not a
computed midpoint or an acceptance of range-selection policy. The spinach fraction
modifies the package; the parenthetical specifies its 10-oz size. Retain exact
avoirdupois constants (1 oz = 28.349523125 g, 1 lb = 453.59237 g) and round once
HALF_UP to six places. Recipe volume retains the accepted 240-ml cup convention.
No fresh tomato, apple or rice grams are inferred.

All six findings are deterministically resolved, so all five affected recipes
receive v2 with `created_from_version_id = v1.id`; 25 recipes remain on v1.
No source-ambiguous finding remains in this bounded review. The loader nevertheless
enforces the per-recipe gate: any `UNRESOLVED_SOURCE_AMBIGUITY` finding prevents
that recipe's entire v2 and all its assessment promotion, even if another row is
resolved. `CONFIRMED_CURRENT` does not itself request a correction.

The only changed ingredient facts are the six reviewed quantities, the salsa
unit g→ml, and normalization notes explaining those corrections. Source amount
text, FoodIngredient, prep note, optional flags, steps and equipment are retained.
Recipe metadata and external provenance are identical; v2 has new internal row
identities, parent/change note and publication timestamps. v1 remains immutable.

### Separate production promotion and historical replay

[Correction manifest](../../data/seed/recipe_corrections/pr6-data-b2a/manifest.json)
pins the starting main, DATA-A audit/source hashes, B1 manifest/evidence/assessment
hashes, PR4 recipe seed, profile input and B2-A curation hash. `corrections.json`
contains complete stable parent/revision descriptors; `assessments.json` contains
new-row descriptors and explicit comparison proofs. No database UUIDs are committed.

The original PR4 recipes.json and B1 evidence.json / assessments.json / manifest.json
are byte-identical to accepted main. PR4 still creates 30 v1 versions / 189 rows;
B1 still creates its historical 57 evidence / 189 assessments / 123 issues. Both
can be rerun after v2 publication and resolve their historical v1 rows.

B2-A adds **5 versions, 32 ingredient rows and 32 new assessments with 17 issue
rows**. All 26 unchanged rows have explicit carry-forward assessments only after
an offline deterministic comparison of FoodIngredient, quantity, unit, source
amount text, normalization/prep notes, optional and pinned profile provenance and
values. All six changed rows have separate new review decisions; their old B1
status is not blindly copied. Every new assessment uses
`source_audit_operation = PR6-DATA-B2-A` and a new local UUID.

| New v2 assessment status | Rows |
| --- | ---: |
| APPROVED_NO_CONVERSION | 1 |
| APPROVED_EXACT | 17 |
| REVIEW_REQUIRED_ESTIMATE | 4 |
| BLOCKED | 10 |

Only the corrected kale g row now permits direct mass (680.388555 g), because its
accepted kale choice has no independent B1 semantic/profile blocker. Corrected
spinach stays blocked by baby/mature form mismatch. Both apple rows retain
size/mass and cultivar/profile uncertainty. Fresh tomato gains an explicit
measure ambiguity issue after its wrong grams become honest ml; cultivar/profile
uncertainty remains. Rice volume remains blocked without exact mass evidence.
No FoodIngredient/profile correction or new conversion evidence is introduced.

The required PR4→B1→B2-A corrections→B2-A assessments chain, repeated in that
order, yields zero second-pass inserts and an identical final database dump:
35 total versions, 221 historical/current ingredient rows, 57 evidence,
221 assessments and 140 issues. No v3 is created. Historical v1 Nutrition results
are identical before and after publication; new v2 rows have no mass authority
until their explicit assessments are imported. Assessment import also verifies
the complete v2 contents and parent/provenance chain in its transaction.

### Production audit v3

[Audit v3](../../data/seed/recipe_corrections/pr6-data-b2a/production-audit-v3.json)
is deterministic and covers **30 current RecipeVersions / 189 current rows**.
Each recipe records current version number and historical version count. The
six-finding matrix records RESOLVED/UNRESOLVED against its actual current owner.
All six current outcomes are RESOLVED on v2.

Actual Nutrition statuses: **0 COMPLETE, 0 COMPLETE_WITH_WARNINGS, 0 CONDITIONAL,
30 INCOMPLETE**. Current assessment counts: **21 APPROVED_NO_CONVERSION,
66 APPROVED_EXACT, 37 REVIEW_REQUIRED_ESTIMATE, 65 BLOCKED**. These are measured
outcomes, not target completeness counts.

Runtime warning occurrences: blocked 65, estimate not accepted 43, unknown fiber
30, unknown profile estimation 189, optional ingredient 4; missing assessment,
stale profile, missing evidence, estimated source, missing ingredient/profile,
missing density and unsupported piece mass are all zero.

There are **118 current structured issues**: estimate non-acceptance 43, form
mismatch 17, identity mismatch 1, measure/size ambiguity 37, no acceptable source
1, profile representativeness 19. Source alternative weight, source quantity
ambiguity and source quantity mismatch are zero in current rows. Historical B1
retains all 123 original issues, including those six source-quantity findings.

Reproduce with backend dependencies (all databases used by the audit are isolated):

```sh
python3 scripts/promote_pr6_data_b2a.py
AI_ENABLED=false python3 scripts/audit_pr6_data_b2a.py
```

Production import order after migrations and FoodIngredient/PR4/B1 seeds:

```sh
# From backend/, using the configured database
AI_ENABLED=false python3 -m app.seed.recipe_corrections corrections
AI_ENABLED=false python3 -m app.seed.recipe_corrections assessments
```

This slice accepts **0 estimated conversions** and starts **0 form/profile
corrections**. All 43 DATA-A estimates remain non-executable. B1 and PR6-INFRA
are established. **PR6 remains NOT COMPLETE; B2-B is NOT AUTHORIZED; PR7+ remain
UNAUTHORIZED.** There is no separate B2-A-CLOSE operation.
