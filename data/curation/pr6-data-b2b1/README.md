# PR6-DATA-B2-B1 semantic/profile resolution audit

This changeset establishes research and curation only, based exactly on accepted
main `7f17b1372bbd2e9f97fc025ac26b3f04a15cf837`. It recommends a representation;
it does not approve or implement it. PR6 remains **NOT COMPLETE**.
B2-B2 production corrections, estimate-policy implementation and PR7+ are
**NOT AUTHORIZED**. No separate B2-B1-CLOSE operation is needed.

## Authority, scope and reproducibility

The authority order is the exact accepted recipe artifact → current B2-A
RecipeVersion → FoodIngredient and **all** its current uses → current profile
and exact source description → primary official candidate sources. The row
universe is computed from audit v3, never copied from historical DATA-A row IDs.
Stable identities are `recipe:v<current version>:<position>`, not database UUIDs.

The 17 FOOD_FORM_MISMATCH, 1 IDENTITY_MISMATCH and 19
PROFILE_REPRESENTATIVENESS_REVIEW occurrences identify **37 distinct rows**,
**23 current recipes** and **19 FoodIngredients**. These three target issue sets
happen to be disjoint in v3; other issues overlap them. Full impact analysis
covers **46 current uses in 25 recipes**, including nine non-target uses.
Twenty-five recipe source records refer to **21 distinct accepted artifact
hashes**. Each artifact was reopened and hash-verified against PR4 and DATA-A;
relevant ingredients, directions, alternatives and notes were inspected. These
reopened readings are separate from the historical findings.

[semantic-profile-audit.json](semantic-profile-audit.json) is the row authority;
[source-manifest.json](source-manifest.json) retains source facts and
[summary.json](summary.json) is deterministically derived. Original recipe
PDF/HTML bytes are not republished: accepted hashes, source URLs, precise
locations and bounded ingredient/form readings preserve their rights posture.
Official nutrition extracts retain food identities, exact nutrient records,
release/archive and table hashes, survey input foods, retrieval metadata and
source limitations. These are **research candidates**, never production seeds.

Run from the repository root:

```sh
python3 scripts/validate_pr6_data_b2b1.py
AI_ENABLED=false python3 -m pytest -q backend/app/tests/test_pr6_data_b2b1_research.py
python3 scripts/promote_pr6_data_b2a.py
AI_ENABLED=false python3 scripts/audit_pr6_data_b2a.py
```

Regenerate only the derived summary with
`python3 scripts/validate_pr6_data_b2b1.py --write-summary`. Row judgments and
source extracts are reviewed curation, not generated semantic classifications.
Validation and summary regeneration are offline and deterministic after commit;
they require the accepted Git base object and normal backend dependencies for
the separate B2-A replay. Neither ordinary tests nor the validator fetch URLs.
Repeating external research requires the hash-matching originals/official
archives; a changed live webpage is not the accepted recipe artifact.

The validator checks coverage, all current source quantities/versions/profile
facts, original provenance hashes, controlled enums, reverse source references,
Decimal nutrient facts against retained official extracts, complete all-use
proofs for global replacements, architecture completeness, derived summary,
43 non-executable estimates, Git-baseline file hashes and migration head.

## Protected production boundary

All **683 pre-existing tracked files** under `backend/`, `frontend/`, `launcher/`,
`data/seed/`, `data/curation/` and `scripts/` (excluding `.DS_Store`) are pinned
against their Git blobs at the exact starting main. This includes PR4/DATA-A/B1/
B2-A data, nutrition seeds/runtime and schema. Only the new research validator,
focused test and four curation artifacts are added in those directories.
Documentation/state updates are separately allowlisted. Untracked/staged files
outside the research allowance fail the scope audit; unrelated `.DS_Store` is
excluded from delivery. No protected bytes changed. Migration remains
`0027_recipe_same_source_revisions`; no 0028, RecipeVersion v3, new assessment,
MeasureMassEvidence or production profile/ingredient is created.

## Resolution summary

| Primary resolution | Rows |
| --- | --- |
| ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT | 11 |
| ARCHITECTURE_DECISION_REQUIRED | 7 |
| CURRENT_PROFILE_CONFIRMED_COMPATIBLE | 0 |
| EDIBLE_BASIS_OR_YIELD_REQUIRED | 3 |
| NO_ACCEPTABLE_PROFILE_SOURCE | 4 |
| REMAP_TO_EXISTING_FOOD_INGREDIENT | 0 |
| REPLACE_CURRENT_PROFILE_SAFE | 8 |
| SOURCE_FORM_AMBIGUOUS | 4 |

There are **12 selected research profile candidates** and **7 proposed new
FoodIngredient concepts**. Eleven target rows would require recipe revisions
for those additions. Eight target rows have a globally compatible replacement
recommendation across four existing foods; they affect ten current uses when
the two non-target oat uses are counted. Seven APPLE rows have an identified
candidate but remain architecture/order dependent. Eighteen rows remain
unresolved by a standalone profile operation (7 architecture, 4 ambiguous,
4 acceptable-source gaps, 3 edible-yield). Null future-change flags mean the
required change is not yet determined, not that implementation needs no change.
No existing-catalogue remap is recommended.

## Complete row decision matrix

Abbreviations: ADD = ADD_NUTRITION_RELEVANT_FOOD_INGREDIENT; SAFE =
REPLACE_CURRENT_PROFILE_SAFE; ARCH = ARCHITECTURE_DECISION_REQUIRED;
AMBIG = SOURCE_FORM_AMBIGUOUS; NO SOURCE = NO_ACCEPTABLE_PROFILE_SOURCE;
YIELD = EDIBLE_BASIS_OR_YIELD_REQUIRED. Full rationale, current profile values,
source readings and limitations for every row are in the row audit.

| Current row | FoodIngredient | Quantity/unit | Resolution | Proposed concept / candidate FDC | Conversion afterward |
| --- | --- | --- | --- | --- | --- |
| CACFP6_CORN_EDAMAME_BLEND:v1:4 | CORN_SWEET | 141.747616 g | NO SOURCE | — | g input |
| CACFP6_CREAMY_COLESLAW:v1:2 | MAYONNAISE_LOW_FAT | 56.699046 g | SAFE | MAYONNAISE_LOW_FAT / FDC-173594 | g input |
| CACFP6_CREAMY_COLESLAW:v1:11 | CRANBERRIES_DRIED | 63.786427 g | AMBIG | — | g input |
| CACFP6_TABBOULEH:v1:5 | TOMATO | 264.595549 g | SAFE | TOMATO / FDC-170457 | g input |
| CACFP6_TABBOULEH:v1:6 | CUCUMBER | 134.660235 g | NO SOURCE | — | g input |
| CACFP6_TABBOULEH:v1:12 | LEMON | 56.699046 g | ADD | LEMON_JUICE / FDC-2709180 | g input |
| FNS2_ORANGE_PORK_CHOPS:v1:4 | ORANGE | 0.500000 pcs | AMBIG | — | measure/size ambiguous |
| HARV6_FRESH_TOMATO_SALSA:v2:1 | TOMATO | 240.000000 ml | SAFE | TOMATO / FDC-170457 | measure/size ambiguous |
| HARV6_FRESH_TOMATO_SALSA:v2:2 | APPLE | 120.000000 ml | ADD | APPLE_PEELED / FDC-171689 | exact evidence needed |
| HARV6_GARDEN_PASTA_SALAD:v1:1 | PASTA_DRY | 120.000000 ml | ADD | PASTA_COOKED / FDC-168928 | exact evidence needed |
| SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:5 | APPLE | 1.000000 pcs | ARCH | APPLE / FDC-171688 | estimate only |
| SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:6 | STRAWBERRY | 240.000000 ml | ADD | STRAWBERRY_FROZEN_UNSWEETENED / FDC-168173 | exact evidence needed |
| SNAP3_GRILLED_FRUIT:v1:2 | PEACH | 1.000000 pcs | SAFE | PEACH / FDC-2709249 | measure/size ambiguous |
| SNAP4_BRAISED_CHICKEN_SPINACH:v1:1 | CHICKEN_THIGH | 4.000000 pcs | YIELD | — | edible yield required |
| SNAP4_DILLED_FISH_FILLETS:v1:2 | LEMON | 15.000000 ml | ADD | LEMON_JUICE / FDC-2709180 | exact evidence needed |
| SNAP4_PEAR_ORANGE_SAUCE:v1:1 | PEAR | 4.000000 pcs | NO SOURCE | — | estimate only |
| SNAP4_PEAR_ORANGE_SAUCE:v1:2 | ORANGE | 180.000000 ml | ADD | ORANGE_JUICE / FDC-2709186 | exact evidence needed |
| SNAP4_SPANISH_FRITTATA:v1:1 | POTATO | 680.388555 g | YIELD | — | edible yield required |
| SNAP4_SPRING_VEGETABLE_SAUTE:v1:4 | POTATO | 3.000000 pcs | NO SOURCE | — | exact evidence needed |
| SNAP6_HEAVENLY_DEVILED_EGGS:v1:2 | MAYONNAISE_LOW_FAT | 30.000000 ml | SAFE | MAYONNAISE_LOW_FAT / FDC-173594 | estimate only |
| SNAP6_PEACH_CRISP:v1:1 | PEACH | 960.000000 ml | SAFE | PEACH / FDC-2709249 | estimate only |
| SNAP6_PEACH_CRISP:v1:2 | MARGARINE | 30.000000 ml | AMBIG | — | estimate only |
| SNAP6_PEACH_CRISP:v1:3 | OATS_ROLLED | 180.000000 ml | SAFE | OATS_ROLLED / FDC-173904 | exact evidence needed |
| SNAP6_PEACH_CRISP:v1:7 | LEMON | 5.000000 ml | ADD | LEMON_JUICE / FDC-2709180 | exact evidence needed |
| SNAP6_SPINACH_APPLE_SALAD:v2:1 | SPINACH | 188.996821 g | ADD | SPINACH_BABY / FDC-1999632 | g input |
| SNAP6_SPINACH_APPLE_SALAD:v2:2 | APPLE | 1.500000 pcs | ARCH | APPLE / FDC-171688 | measure/size ambiguous |
| SNAP6_WALDORF_SALAD:v1:2 | APPLE | 2.000000 pcs | ARCH | APPLE / FDC-171688 | measure/size ambiguous |
| SNAP6_WALDORF_SALAD:v1:7 | LEMON | 5.000000 ml | ADD | LEMON_JUICE / FDC-2709180 | exact evidence needed |
| SNAP8_APPLE_CARROT_SOUP:v1:2 | APPLE | 4.000000 pcs | ARCH | APPLE / FDC-171688 | measure/size ambiguous |
| SNAP8_SOMALI_SUMMER_SALAD:v1:2 | LEMON | 15.000000 ml | ADD | LEMON_JUICE / FDC-2709180 | exact evidence needed |
| SNAP8_SOMALI_SUMMER_SALAD:v1:3 | APPLE | 3.000000 pcs | ARCH | APPLE / FDC-171688 | measure/size ambiguous |
| SNAP8_SOMALI_SUMMER_SALAD:v1:5 | TOMATO | 3.000000 pcs | SAFE | TOMATO / FDC-170457 | measure/size ambiguous |
| TNC6_APPLESAUCE:v1:1 | APPLE | 6.000000 pcs | AMBIG | — | measure/size ambiguous |
| WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2:5 | APPLE | 0.500000 pcs | ARCH | APPLE / FDC-171688 | measure/size ambiguous |
| WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:5 | APPLE | 240.000000 ml | ARCH | APPLE / FDC-171688 | estimate only |
| WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:6 | CAULIFLOWER | 120.000000 ml | ADD | CAULIFLOWER_FROZEN / FDC-170398 | exact evidence needed |
| WIC4_BUTTERNUT_SOUP:v1:1 | BUTTERNUT_SQUASH | 1360.777110 g | YIELD | — | edible yield required |

## Complete affected-FoodIngredient usage matrix

Every current use is listed, including non-target rows. Preparation refers to the
measured recipe input; later cooking does not itself authorize a cooked-profile
swap or nutrient-retention/yield model.

| FoodIngredient | Current recipe:version:position | Source form / global replacement constraint |
| --- | --- | --- |
| APPLE | HARV6_FRESH_TOMATO_SALSA:v2:2 | Raw apple explicitly peeled and finely chopped; half-cup measures prepared flesh. |
| APPLE | SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:5 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| APPLE | SNAP6_SPINACH_APPLE_SALAD:v2:2 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| APPLE | SNAP6_WALDORF_SALAD:v1:2 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| APPLE | SNAP8_APPLE_CARROT_SOUP:v1:2 | Raw apples explicitly with skin, cored and quartered before simmering. |
| APPLE | SNAP8_SOMALI_SUMMER_SALAD:v1:3 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| APPLE | TNC6_APPLESAUCE:v1:1 | Original explicitly makes peeling optional. Accepted production steps omit that option; PR4 ingredient review does not explicitly bind a peel choice. Keep this source alternative open for review. |
| APPLE | WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2:5 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| APPLE | WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:5 | Raw apple input; core removal/chopping does not imply peeled flesh. No cultivar is fixed. |
| BUTTERNUT_SQUASH | WIC4_BUTTERNUT_SOUP:v1:1 | About three pounds is whole squash. Ends/seeds removed, roasted, flesh scooped away from skin. |
| CAULIFLOWER | WIC1_BEYOND_BASIC_GRILLED_CHEESE:v1:3 | Accepted fresh cauliflower alternative; no roasted mixture is inferred from an unselected source branch. |
| CAULIFLOWER | WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:6 | Frozen cauliflower blended without further cooking. Fresh steamed and frozen riced variants in notes are alternatives, not source changes. |
| CHICKEN_THIGH | SNAP4_BRAISED_CHICKEN_SPINACH:v1:1 | Four 6-ounce bone-in skinless thighs. Bones remain during cooking; serving yield is not an edible-mass factor. |
| CORN_SWEET | CACFP6_CORN_EDAMAME_BLEND:v1:4 | Frozen corn, thawed and drained, weighed before sauteing. Drainage is explicit. |
| CRANBERRIES_DRIED | CACFP6_CREAMY_COLESLAW:v1:11 | Dried cranberries; sweetening is not specified in ingredients, directions or notes. |
| CUCUMBER | CACFP6_TABBOULEH:v1:6 | Fresh cucumber explicitly peeled, seeded and diced; 134.660235 g already describes prepared edible flesh. |
| CUCUMBER | HARV6_GARDEN_PASTA_SALAD:v1:3 | Raw cucumber cut as directed; peel/seed state not explicitly removed in this use. |
| CUCUMBER | SNAP8_SOMALI_SUMMER_SALAD:v1:6 | Raw cucumber cut as directed; peel/seed state not explicitly removed in this use. |
| LEMON | CACFP6_TABBOULEH:v1:12 | Lemon juice ingredient, not fruit flesh or purchase mass. Fresh versus bottled is not specified. |
| LEMON | SNAP4_DILLED_FISH_FILLETS:v1:2 | Lemon juice ingredient, not fruit flesh or purchase mass. Fresh versus bottled is not specified. |
| LEMON | SNAP6_PEACH_CRISP:v1:7 | Lemon juice ingredient, not fruit flesh or purchase mass. Fresh versus bottled is not specified. |
| LEMON | SNAP6_WALDORF_SALAD:v1:7 | Lemon juice ingredient, not fruit flesh or purchase mass. Fresh versus bottled is not specified. |
| LEMON | SNAP8_SOMALI_SUMMER_SALAD:v1:2 | Lemon juice ingredient, not fruit flesh or purchase mass. Fresh versus bottled is not specified. |
| MARGARINE | SNAP6_PEACH_CRISP:v1:2 | Margarine, then melted. Fat grade and stick/tub form unspecified. |
| MAYONNAISE_LOW_FAT | CACFP6_CREAMY_COLESLAW:v1:2 | Low-fat/light mayonnaise category; no olive-oil formulation specified. |
| MAYONNAISE_LOW_FAT | SNAP6_HEAVENLY_DEVILED_EGGS:v1:2 | Low-fat/light mayonnaise category; no olive-oil formulation specified. |
| OATS_ROLLED | SNAP6_PEACH_CRISP:v1:3 | Dry rolled-oat family input; prepared only after measuring. No flavored instant oatmeal selected. |
| OATS_ROLLED | WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2:2 | Source permits rolled or quick oats; notes prefer old-fashioned and distinguish instant. Accepted rolled option retained. |
| OATS_ROLLED | WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:7 | Dry rolled-oat family input; prepared only after measuring. No flavored instant oatmeal selected. |
| ORANGE | FNS2_ORANGE_PORK_CHOPS:v1:4 | Orange slices; source does not specify peeling or whether garnish peel is consumed. |
| ORANGE | SNAP4_PEAR_ORANGE_SAUCE:v1:2 | Three-quarter cup of ready-to-use 100% orange juice, heated with sugar. Neither whole orange nor undiluted concentrate. |
| PASTA_DRY | HARV6_GARDEN_PASTA_SALAD:v1:1 | Half cup of already cooked macaroni; chilled salad assembly performs no pasta cooking. |
| PEACH | SNAP3_GRILLED_FRUIT:v1:2 | Generic raw peach, pit excluded when cut. Recipe measures before heating; no cultivar specified. |
| PEACH | SNAP6_PEACH_CRISP:v1:1 | Generic raw peach, pit excluded when cut. Recipe measures before heating; no cultivar specified. |
| PEAR | SNAP4_PEAR_ORANGE_SAUCE:v1:1 | Pears are explicitly peeled before steaming. A generic with-skin pear profile does not resolve this. |
| POTATO | SNAP4_SPANISH_FRITTATA:v1:1 | Russets weighed scrubbed with skin, boiled, drained, then peeled. The input 680.388555 g includes discarded skin. |
| POTATO | SNAP4_SPRING_VEGETABLE_SAUTE:v1:4 | Three tiny new potatoes, quartered before cooking. No peeling step; new maturity is explicit, not a red cultivar. |
| SPINACH | SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:1 | Fresh spinach input in the accepted branch; no baby-leaf replacement is inferred for other rows. |
| SPINACH | SNAP4_BRAISED_CHICKEN_SPINACH:v1:10 | Accepted fresh bunch alternative, cooked for two minutes; frozen ten-ounce package is unselected and supplies no mass for this row. |
| SPINACH | SNAP6_SPINACH_APPLE_SALAD:v2:1 | Baby spinach, washed; current v2 applies 2/3 of the 10-ounce package, 188.996821 g. Kale alternative is not selected. |
| SPINACH | TNC6_EGGS_SPINACH:v1:3 | Fresh spinach input in the accepted branch; no baby-leaf replacement is inferred for other rows. |
| SPINACH | WIC2_SPINACH_CAULIFLOWER_SMOOTHIE:v1:4 | Fresh spinach input in the accepted branch; no baby-leaf replacement is inferred for other rows. |
| STRAWBERRY | SNAP2_SIMPLE_GREEN_SMOOTHIE:v1:6 | Accepted PR4 all-one-fruit plain frozen strawberry choice, not a mixed or sweetened fruit product. |
| TOMATO | CACFP6_TABBOULEH:v1:5 | Fresh generic tomato input, chopped/diced; no named cultivar. Canned alternatives are not selected. |
| TOMATO | HARV6_FRESH_TOMATO_SALSA:v2:1 | Fresh generic tomato input, chopped/diced; no named cultivar. Canned alternatives are not selected. |
| TOMATO | SNAP8_SOMALI_SUMMER_SALAD:v1:5 | Fresh generic tomato input, chopped/diced; no named cultivar. Canned alternatives are not selected. |

## Proposed new catalogue concepts and safe replacements

These are platform food identities, not RetailSKU, FoodProductType, household
stock or automatic purchase units. Candidate default unit is g; density and
edible fraction remain unknown. No value is invented.

| Proposed code / name | Related existing code | Profile | Rows |
| --- | --- | --- | --- |
| APPLE_PEELED / Яблоко сырое очищенное | APPLE | FDC-171689 | 1 |
| CAULIFLOWER_FROZEN / Капуста цветная замороженная | CAULIFLOWER | FDC-170398 | 1 |
| LEMON_JUICE / Сок лимонный 100% | LEMON | FDC-2709180 | 5 |
| ORANGE_JUICE / Сок апельсиновый 100% готовый к употреблению | ORANGE | FDC-2709186 | 1 |
| PASTA_COOKED / Макаронные изделия варёные без добавленной соли | PASTA_DRY | FDC-168928 | 1 |
| SPINACH_BABY / Шпинат молодой (baby), сырой | SPINACH | FDC-1999632 | 1 |
| STRAWBERRY_FROZEN_UNSWEETENED / Клубника замороженная без сахара | STRAWBERRY | FDC-168173 | 1 |

Globally compatible replacement recommendations on the **current** catalogue:

| Existing food | Candidate | Target/all current uses | All-use compatibility rationale |
| --- | --- | --- | --- |
| MAYONNAISE_LOW_FAT | FDC-173594 | 2/2 | Both uses are generic light/low-fat mayonnaise. USDA FNDDS 2710220 explicitly lists low-fat and reduced-fat among additional descriptions and uses SR 4641 (FDC 173594), the generic light mayonnaise profile. This replaces the unsupported olive-oil formulation without inventing nutrient tolerances. |
| OATS_ROLLED | FDC-173904 | 1/3 | USDA explicitly combines regular and quick, not fortified, dry oats; its food_attribute includes old-fashioned and rolled oats. This covers quick oats in crisp, accepted rolled oats overnight and generic dry oats in smoothie without a processing-equivalence threshold. |
| PEACH | FDC-2709249 | 2/2 | Both recipes specify generic raw peaches before heating, with no cultivar. Select the explicitly generic USDA FNDDS Peach, raw profile rather than present a yellow-only Foundation profile as cultivar-independent truth. |
| TOMATO | FDC-170457 | 3/3 | All three current uses select fresh generic tomatoes, not canned or a specified Roma cultivar. SR year-round average red ripe raw tomatoes is an authoritative generic profile; source bounds cover all three uses. |

“Safe” describes semantic compatibility for all current uses under the stated
source interpretation; it is not implementation approval. The specific FNDDS
peach recommendation needs explicit review of its population-default provenance.
Its generic label is not evidence that yellow and white peaches are equivalent.

APPLE is **not** globally safe now: salsa is explicitly peeled, applesauce makes
peeling optional, and other current uses retain skin. Move the peeled salsa only
after authorization, bind the applesauce choice, then recheck the residual APPLE
uses before replacing the Gala profile with generic raw-with-skin FDC 171688.
Do not create a duplicate APPLE_WITH_SKIN simply to evade that ordering.
All LEMON uses require juice, but LEMON still names a fruit concept; replacing its
profile would redefine that concept. Existing ORANGE_JUICE_CONCENTRATE is not
ready-to-use juice; POTATO_RED does not mean an unspecified tiny new potato.

## Exact selected candidate profile sources

Values below are per **100 g edible material**, in order kcal and g of protein,
fat, carbohydrate (USDA 1005, includes fiber), fiber. Decimal text is retained;
no nutrient tolerance or value-closeness equivalence is applied. Source
`estimated` remains unknown; published official values do not authorize setting
any application estimation flag. Foundation baby-spinach energy uses 2048;
all other selected candidates use 1008. Release provenance and raw records are
in the manifest, including alternatives that were not selected.

| FDC source / official description | Data type / release | kcal | Protein | Fat | Carbohydrate | Fiber |
| --- | --- | --- | --- | --- | --- | --- |
| [168173](https://fdc.nal.usda.gov/food-details/168173/nutrients) — Strawberries, frozen, unsweetened (Includes foods for USDA's Food Distribution Program) | SR Legacy / 2018-04 | 35 | 0.43 | 0.11 | 9.13 | 2.1 |
| [168928](https://fdc.nal.usda.gov/food-details/168928/nutrients) — Pasta, cooked, unenriched, without added salt | SR Legacy / 2018-04 | 158 | 5.8 | 0.93 | 30.86 | 1.8 |
| [170398](https://fdc.nal.usda.gov/food-details/170398/nutrients) — Cauliflower, frozen, unprepared | SR Legacy / 2018-04 | 24 | 2.01 | 0.27 | 4.68 | 2.3 |
| [170457](https://fdc.nal.usda.gov/food-details/170457/nutrients) — Tomatoes, red, ripe, raw, year round average | SR Legacy / 2018-04 | 18 | 0.88 | 0.2 | 3.89 | 1.2 |
| [171688](https://fdc.nal.usda.gov/food-details/171688/nutrients) — Apples, raw, with skin (Includes foods for USDA's Food Distribution Program) | SR Legacy / 2018-04 | 52 | 0.26 | 0.17 | 13.81 | 2.4 |
| [171689](https://fdc.nal.usda.gov/food-details/171689/nutrients) — Apples, raw, without skin | SR Legacy / 2018-04 | 48 | 0.27 | 0.13 | 12.76 | 1.3 |
| [173594](https://fdc.nal.usda.gov/food-details/173594/nutrients) — Salad dressing, mayonnaise, light | SR Legacy / 2018-04 | 238 | 0.37 | 22.22 | 9.23 | 0 |
| [173904](https://fdc.nal.usda.gov/food-details/173904/nutrients) — Cereals, oats, regular and quick, not fortified, dry | SR Legacy / 2018-04 | 379 | 13.15 | 6.52 | 67.7 | 10.1 |
| [1999632](https://fdc.nal.usda.gov/food-details/1999632/nutrients) — Spinach, baby | Foundation / 2026-04-30 | 20.72851125 | 2.851875 | 0.6188 | 2.406325 | 1.558 |
| [2709180](https://fdc.nal.usda.gov/food-details/2709180/nutrients) — Lemon juice, 100%, NS as to form | Survey (FNDDS) / 2024-10-31 / FNDDS 2021-2023 | 22.0 | 0.350 | 0.240 | 6.90 | 0.300 |
| [2709186](https://fdc.nal.usda.gov/food-details/2709186/nutrients) — Orange juice, 100%, NFS | Survey (FNDDS) / 2024-10-31 / FNDDS 2021-2023 | 47.0 | 0.770 | 0.340 | 10.2 | 0.300 |
| [2709249](https://fdc.nal.usda.gov/food-details/2709249/nutrients) — Peach, raw | Survey (FNDDS) / 2024-10-31 / FNDDS 2021-2023 | 46.0 | 0.910 | 0.270 | 10.1 | 1.50 |

Foundation April 2026 and SR Legacy April 2018 were searched first. FNDDS
2021–2023 (October 2024 release) supplies explicitly generic survey candidates
where fresh/cultivar/formulation labels otherwise over-specify the recipe.
Its [official documentation](https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_FNDDS_Doc.pdf)
explains NFS/NS population defaults and distinguishes estimated portion weights.
No portion weight is imported as authority. Lemon NFS derives from raw lemon
juice; orange NFS is a 65% ordinary / 35% calcium-added packaged juice reference;
generic peach derives from yellow raw peach. These inputs are retained in full.
Review must accept or reject each named representative reference; rejection
keeps the corresponding row blocked. This is not a general NFS fallback policy.

Generic light mayonnaise is supported by FNDDS additional descriptions
(low-fat/reduced-fat) and its direct SR light-mayonnaise input. Generic dried
cranberry derives from sweetened fruit and does **not** establish the recipe's
sweetening state. Margarine NFS blends tub/stick forms and does **not** establish
the recipe's fat grade or physical form. Those two rows remain ambiguous.
Generic tomato uses a year-round ripe-red reference with that culinary
interpretation explicit. Generic peeled pear remains unresolved despite locating
generic with-skin pear; the original directions require peeling.

## Edible basis and unresolved decisions

| Current row | Reason / required follow-up |
| --- | --- |
| CACFP6_CORN_EDAMAME_BLEND:v1:4 | Clear frozen/thawed/drained corn source. SR frozen unprepared kernels does not document thaw/drain state; boiled/drained kernel profile adds an uncalled prior cooking step. Fresh Foundation is false. No acceptable complete match established in the searched sources. Obtain an official thawed-drained unprepared kernel profile or explicit primary preparation metadata establishing compatibility. Then a frozen-corn concept would be appropriate; existing 141.747616 g already describes the source drained quantity. |
| CACFP6_CREAMY_COLESLAW:v1:11 | Recipe does not specify sweetened or unsweetened. Foundation, SR and generic FNDDS candidates describe or derive from sweetened cranberries. A generic label cannot prove added-sugar state. Resolve the source sweetening specification; retain current profile without approving its compatibility meanwhile. |
| CACFP6_TABBOULEH:v1:6 | Clear peeled AND seeded form. USDA peeled raw and CNF peeled raw remove peel/ends but do not establish seed-cavity removal. Current source grams already describe prepared flesh; a peel-only profile swap is insufficient. Obtain authoritative composition for peeled seeded cucumber or primary sampling/preparation metadata establishing that same edible part. No mass-yield factor alone fixes a composition mismatch. |
| FNS2_ORANGE_PORK_CHOPS:v1:4 | Original says sliced orange placed on pork but gives no peeling/removal instruction. Neither navel edible-flesh nor an all-varieties flesh profile establishes whether peel is consumed. Clarify the accepted peel/edible branch; 169097 all-commercial-varieties is retained as unselected flesh candidate. Do not remap to orange concentrate. |
| SNAP4_BRAISED_CHICKEN_SPINACH:v1:1 | Four 6-ounce bone-in skinless thighs. Bones remain during cooking; serving yield is not an edible-mass factor. Selecting another edible profile cannot convert gross input into edible mass. Need source-compatible bone refuse/edible meat evidence, quantity binding and reviewed yield handling. Do not infer 4/6 yield from serving text or divide generic boneless thigh portions. |
| SNAP4_PEAR_ORANGE_SAUCE:v1:1 | Directions explicitly peel pears. Generic SR raw pear and FNDDS blend remove the cultivar-only problem but do not establish peeled flesh. No acceptable peeled generic profile located in the accessible official material. Obtain complete official peeled-pear composition and its edible basis. Medium-piece mass evidence must be separately reviewed; the old with-skin estimate cannot be executed. |
| SNAP4_SPANISH_FRITTATA:v1:1 | Russets weighed scrubbed with skin, boiled, drained, then peeled. The input 680.388555 g includes discarded skin. Selecting another edible profile cannot convert gross input into edible mass. Need russet-specific input identity plus evidence for pre-boil gross mass to post-peel edible mass and cooking state. Profiles 170027, 2346401 and 170438 are retained as alternatives, none authorizes a yield. |
| SNAP4_SPRING_VEGETABLE_SAUTE:v1:4 | Tiny new potatoes specify immature harvest, with skin retained by the written preparation. USDA russet/red/gold and generic mature potatoes do not explicitly cover that form. POTATO_RED would silently choose a cultivar. Obtain an authoritative new-potato skin-on profile or exact source harvest metadata. Tiny still needs a reviewed piece mass; no standard size is inferred. |
| SNAP6_PEACH_CRISP:v1:2 | Source specifies margarine but neither fat grade nor stick/tub form. FNDDS Margarine NFS is 75% tub and 25% stick, which invents a physical mixture for this recipe. The current 80% stick profile is not confirmed by melting instructions. Resolve source formulation/grade or approve a separately bounded profile-source policy. No default mixture is selected here. |
| TNC6_APPLESAUCE:v1:1 | Original makes peeling optional; accepted steps omit the option but neither ingredient provenance nor PR4 review explicitly chooses a nutrition form. Do not choose peel state for Nutrition. Project review must bind the retained source option. Candidate profiles 171688 and 171689 are both retained, neither selected. |
| WIC4_BUTTERNUT_SOUP:v1:1 | About three pounds is whole squash. Ends/seeds removed, roasted, flesh scooped away from skin. Selecting another edible profile cannot convert gross input into edible mass. Need whole-to-edible flesh evidence separating seeds, ends, skin and roast moisture loss, with mass state and source provenance. No universal edible_fraction or cooked/raw swap. |

The four NO_ACCEPTABLE_PROFILE_SOURCE outcomes mean **no acceptable match
established within the documented search**, not worldwide nonexistence.
USDA frozen unprepared / boiled drained corn and peeled cucumber are retained
as rejected near matches. CNF peeled cucumber does not establish seed-cavity
removal. CoFID 2021 release/guide were inspected, but its workbook could not be
retrieved through available readers/TLS routes; AFCD pages exposed loading shells.
No values were taken from snippets. DTU's analysed generic peach detail was
inspected; its available-carbohydrate definition and rounded UI values were not
silently substituted for USDA 1005. These access/definition limitations remain
explicit source gaps for future research.

## Architecture analysis

### FACT

- 0023_food_ingredient_catalogue enforces uq_food_nutrition_profiles_one_current WHERE is_current=1.
- RecipeIngredient references FoodIngredient; its food identity selects current profile.
- Assessment stores exact nutrition_profile_id; seed descriptors pin source name/id/version and values. Stale profile bindings fail closed.
- FoodProductType is deliberately not a canonical source-of-truth aggregate (architecture section 6.2).

The unique current-profile index is in
[0023](../../../backend/app/migrations/versions/0023_food_ingredient_catalogue.py).
The [Nutrition domain](../../../backend/app/domain/nutrition.py) checks exact
profile identity and fails stale assessment bindings. The canonical
[architecture](../../../docs/family-food/architecture.md#62-canonical-food-catalogue)
keeps FoodProductType outside source-of-truth aggregates.

### ASSUMPTION

- Generic raw tomato means ripe red culinary tomato; no specialty cultivar is silently included.
- Specified chop/core preparation retains skin unless the source instructs removal; the explicit applesauce peeling alternative remains open.
- The named FNDDS peach and juice candidates are proposed representative references for unspecified same-identity foods; approval is a bounded source-selection judgment, not cultivar/form equivalence or a universal NFS fallback.
- Published food profiles are reference compositions, not measured composition of every purchased item. No nutrient-closeness threshold is used.

| Dimension | A — FoodIngredient form split | B — simultaneous profile variants | C — row-specific nutrition reference |
| --- | --- | --- | --- |
| catalogue complexity | Bounded additional platform concepts, stable names/codes; generic APPLE can be retained after usage repair. | Fewer food codes, more variant/selector lifecycle rules. | Fewer visible food codes but greater hidden row-level curation complexity. |
| implementation migration impact | No new schema layer needed for the recommended form splits; use existing catalogue and same-source revision mechanisms after authorization. | Migrate one-current unique index, selector/backfill, repositories, seed loaders, engine lookups, stale-profile and replay behavior. Rejected as disproportionate to this catalogue. | New row/profile reference schema and deterministic precedence plus stale/replay rules; assessments presently validate against the matching current profile, not an override. Rejected for this bounded operation. |
| nutrition correctness | Form-specific FoodIngredients keep one deterministic profile. Generic references retain source assumptions; yield cases remain blocked. | Requires a mandatory deterministic profile/form selector; multiple is_current rows alone are ambiguous. | Explicit row binding can select correct form but creates a second profile authority path. |
| pantry | Existing household stock retains its food identity; raw and cooked/frozen inventory cannot silently substitute. | Stock form still needs representation; profile variants alone do not establish fungibility. | Stock deductions can target a concept inconsistent with edible nutrition form unless reconciled. |
| recipe truth | Revise only form-remapped recipes, preserving accepted quantities/provenance and immutable history. | RecipeIngredient would need a reviewed selector and immutable provenance for every row. | Needs immutable row-specific reference, review status and revalidation upon recipe/source change. |
| shopping | Potential related purchase concepts; future explicit mapping/yields, no automatic aggregation across forms. | Canonical purchase grouping remains simple but conceals food-form requirements unless propagated. | FoodIngredient can remain a purchase concept; Nutrition form may diverge invisibly. |
| source provenance | Existing versioned profiles and assessment pins remain usable. | Variant identity plus version and assessment pins required; uniqueness must be scoped to variant. | Define precedence, ownership, history, replay and whether updating FoodIngredient default stales an independently bound row. |

### RECOMMENDATION

**RECOMMENDED OPTION: A — nutrition-relevant FoodIngredient split.** It uses
existing food identity, one current profile and immutable recipe history.
It requires no new architecture layer for the seven proposed forms. Global
replacements remain possible only where the complete current use set matches.

**ALTERNATIVES REJECTED: B and C for this bounded operation.** B requires a
mandatory deterministic selector, variant lifecycle, uniqueness migration and
backfill. C creates independent row/default authority with new precedence,
replay and staleness rules. Neither option solves edible-yield or source ambiguity;
flexibility alone does not justify either schema/runtime expansion.

**CONSEQUENCES / future B2-B2 production work, only after authorization:**

- New culinary-form concepts and immutable same-source recipe revisions require separate B2-B2 authorization.
- Generic-profile replacements invalidate pinned assessments and must trigger explicit re-review of every current usage, including non-target rows.
- No global APPLE replacement until peeled use and optional peel branch are resolved; no duplicate APPLE_WITH_SKIN concept proposed.
- Shopping/Pantry relationships must not imply equivalent units, automatic grouping, edible fraction or preparation yields.
- No runtime/migration implementation is authorized by this recommendation.
- Add only approved concepts/profiles, retaining exact source/version and prior
  profile history; apply existing numeric normalization explicitly, never fabricate
  fiber, estimation flags or density.
- Revise the 11 remapped rows in their affected recipes through the existing
  same-source mechanism. Current v2 recipes would need v3 in that later operation;
  none is created here. Preserve quantities, optional flags and source provenance.
- Re-review and publish explicit assessments for every new row and every affected
  profile binding, including non-target oats. No old approval automatically carries.
- Leave unresolved forms/yields blocked. Keep Shopping/Pantry follow-ups separate;
  do not group dry/cooked, whole/juice or gross/edible masses as interchangeable.

### OPEN QUESTION

- Approve Option A before any production semantic/profile correction.
- Approve or reject the exact FNDDS generic peach/lemon/orange profile recommendations, with their retained input-food/default limitations. Rejection leaves the affected rows blocked.
- Bind applesauce peel choice and approve the ordered APPLE repair before its conditional profile replacement.
- Resolve orange peel, cranberry sweetening and margarine formulation from source evidence or explicit project choice.
- Obtain acceptable thawed/drained corn, peeled/seeded cucumber, peeled pear and new skin-on potato profile evidence; inaccessible national sources remain documented limitations.
- Separately authorize any edible-yield or estimate-policy work; no numerical yields or estimates are accepted here.

## Independent conversion boundary

| Conversion after semantic resolution | Rows |
| --- | --- |
| ALREADY_EXACT | 0 |
| DIRECT_G_MASS | 7 |
| NOT_ASSESSED_IN_B2_B1 | 0 |
| STILL_EDIBLE_YIELD_REQUIRED | 3 |
| STILL_ESTIMATE_ONLY | 6 |
| STILL_EXACT_EVIDENCE_NEEDED | 11 |
| STILL_MEASURE_OR_SIZE_AMBIGUOUS | 10 |

DIRECT_G_MASS records an already explicit source input mass; it does not mean
its semantic profile is accepted or its current assessment becomes executable.
The 11 exact-evidence-needed rows still need independently reviewed conversion
facts; ten rows retain measure/size ambiguity; six target rows retain estimate
only; three retain edible-yield requirements. Other non-target conversion
blockers also remain. All **43** current estimate-candidate descendants have
`mass_g = null` in reproduced B2-A v3; 37 are estimate-review assessments and
six have additional blocking issues. **Zero** estimates are accepted. No status,
uncertainty propagation, conversion tolerance or runtime policy changes.

The full baseline remains 30 current RecipeVersions / 189 RecipeIngredient rows,
30 INCOMPLETE, with COMPLETE / COMPLETE_WITH_WARNINGS / CONDITIONAL all zero.
This research does not authorize any production correction, PR6-CLOSE or PR7+.
