# R2-F — Cheese-sandwich resilience-closure Contract Gate

**Status:** docs/data/source-authority implementation contract gate
**Decision date:** 2026-10-03
**Issue:** #139
**Accepted base:** `561c13aad6ce978de399dfd807071232af06b71c` (merged PR #138)
**Runtime publication authorized before this gate merges:** no

## 1. Goal

Close the remaining exact-`MILK_2_5` seven-BREAKFAST resilience gap without
weakening source or provenance contracts.

The future runtime batch contains exactly one `sandwich` RecipeVersion:

- `SAD28_SANDWICH_CHEESE_20_10` — Бутерброд с сыром — 30 g / 83 kcal.

No Planner algorithm, compatibility mapping, repetition limit, schema or Nutrition
authority changes here.

## 2. FACT — accepted production state

After merged PR #138:

- active `breakfast` classification: 7 RecipeVersions;
- active MAIN classification: 5 RecipeVersions;
- `max_recipe_repetitions=3`;
- hard exact `MILK_2_5` leaves `HARD_BOILED_EGG` and
  `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- unaffected BREAKFAST-compatible capacity = 6/week;
- seven BREAKFAST opportunities are bounded-infeasible.

## 3. FACT — butter card fails component-consistency review

The reviewed SAD28 butter card declares:

- wheat bread 25 g;
- cream butter 5 g;
- total sandwich fat 0.98 g;
- energy 66.3 kcal.

The declared macros reproduce 66.3 kcal arithmetically, but that is not sufficient
source validation.

TR TS 033/2013 defines `сливочное масло` as butter with fat mass fraction at
least 50%:

https://eec.eaeunion.org/upload/medialibrary/789/TR-TS-033_2013.pdf

Therefore 5 g of the listed butter contributes at least 2.5 g fat before any bread
fat is counted. That contradicts 0.98 g declared fat for the whole sandwich.

**DECISION:** `SAD28_SANDWICH_BUTTER_25_5` is
`REJECT_PREPARED_OUTPUT_AUTHORITY_COMPONENT_INCONSISTENCY`.

No `BUTTER_CREAM_UNSPECIFIED` identity is created by R2-F.

## 4. DECISION — selected source authority

The bounded policy remains:

`BOUNDED_INSTITUTION_PUBLISHED_TECH_CARD_REVIEW_V1`.

Publication scope is exactly one card:

`sad28-hosted:techcard:3:cheese-sandwich:20-10`.

The older discovery identifier
`sad28-luppolovo:techcard:cheese-sandwich:20-10`
is retained only as discovery lineage.

### Durable raw-card source

The future SOURCE_VERIFIED RecipeVersion does **not** use the live PDF or a
normalized derivative as `source_document`. It uses the complete retained
selected-card text snapshot:

- repository path: `data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`;
- SHA-256: `77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`;
- byte size: 1783;
- immutable Git locator: `https://raw.githubusercontent.com/Mitronomik/family-food-os/97ed76c7009229b5c947c63f1ace09b63a32147b/data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`;
- durable Library locator: `library:/FamilyFoodOS/source-artifacts/sad28-cheese-card-raw-text-2026-10-03.txt`;
- Library file id: `libfile_baff1ee2870081918170b98d1cec3c5d`.

The Library copy was materialized and independently re-hashed on 2026-10-03:
1783 bytes and the same SHA-256 — PASS.

The future RecipeVersion tuple is therefore coherent:

`source_url` → exact retained raw-card snapshot
`source_document_sha256` → SHA-256 of that same snapshot.

### Provenance roles

Do not collapse hosting, issuer and recipe provenance into one publisher field.

- **Official host:** МАДОУ «ДСКВ №28» д. Лупполово. Its official nutrition page
  links the technological-card file.
- **Document/card issuer:** `NOT_ESTABLISHED_FROM_RETAINED_CARD`. No issuer is
  inferred from the hosting institution.
- **Upstream recipe collection:** `Сборник методических рекомендаций по организации питания детей и подростков в учреждениях образования Санкт-Петербурга. СПб.: Речь, 2008, Куткина М.Н.`

The public SAD28 PDF remains upstream discovery/corroboration only:

`https://sad28.vsevobr.ru/images/22-23/%D0%BF%D0%B8%D1%82%D0%B0%D0%BD%D0%B8%D0%B5/%D0%A2%D0%B5%D1%85%D0%BD%D0%BE%D0%BB%D0%BE%D0%B3%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5-%D0%BA%D0%B0%D1%80%D1%82%D1%8B-22-23%20%281%29.pdf`

Exact upstream PDF bytes could not be retrieved through the available execution
environment. No PDF SHA is invented. The PDF is not required to reproduce the
accepted one-card publication because the complete selected card text used by
publication is durably retained and independently verified. Any future source
family expansion or reinterpretation requires upstream reacquisition and a new
review.

## 5. Selected cheese card

Publication source record:
`sad28-hosted:techcard:3:cheese-sandwich:20-10`.

Discovery lineage:
`sad28-luppolovo:techcard:cheese-sandwich:20-10`.

Reviewed discovery-card SHA-256:
`2eb846cdb80737c0b4f65202beda1e352f3610c6bb6634b832901615ca3a8f97`.

Exact facts:

- `Хлеб пшеничный` — 20 g net;
- `Сыр` — 11 g gross / 10 g net;
- source output `20/10`;
- total serving mass = 30 g;
- source-published `ENERGY_KCAL = 83`;
- source-declared P/F/C = 3.9 / 3.15 / 9.7 g.

The 4/9/4 QA cross-check is 82.75 kcal. The 0.25 kcal difference is treated as
rounding-level corroboration only; same-card 83 kcal remains the accepted
prepared-output candidate authority.

## 6. FoodIngredient identities

Create exactly two identity-only FoodIngredients:

- `WHEAT_BREAD_PLAIN` — Хлеб пшеничный;
- `CHEESE_UNSPECIFIED` — Сыр.

No NutritionProfile or Composition authority is published for either identity.

Explicit non-equivalences remain:

- `WHEAT_BREAD_PLAIN != BREAD_WHOLE_WHEAT`;
- `WHEAT_BREAD_PLAIN != WHEAT_BREAD_HIGH_GRADE_STALE`;
- `CHEESE_UNSPECIFIED != CHEESE_CHEDDAR` and no automatic substitution to a
  specific cheese identity.

## 7. Household applicability

The selected cheese sandwich is `HOUSEHOLD_APPLICABLE`.

The defining operation is ordinary household sandwich assembly. Institutional
serving-temperature and realization/shelf-life instructions stay provenance-only
and do not become consumer runtime rules.

## 8. Planner compatibility

Future RecipeVersion:

`meal_type_code = sandwich`.

Existing Planner v0 mapping already permits:

- BREAKFAST → `breakfast`, `sandwich`;
- LUNCH → `main`, `sandwich`;
- SNACK → `sandwich`.

No mapping change is authorized.

## 9. Nutrition authority

Reuse `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

For the selected RecipeVersion:

- `ENERGY_KCAL` is the only AVAILABLE frozen nutrient;
- all other 53 frozen nutrient codes remain UNKNOWN;
- no ingredient-composition calculation is required;
- no source scaling is authorized;
- source macros are QA/reference evidence only.

## 10. Preservation matrix

| Existing truth | Required preservation |
|---|---|
| PR #138 R2-E runtime | Byte/semantic behavior unchanged. |
| Existing active exact-energy corpus | No deactivation/relabeling. |
| Planner v0.4 mapping | Unchanged. |
| `max_recipe_repetitions=3` | Unchanged. |
| `PREPARED_OUTPUT_V1` | Reused; no new authority kind. |
| Frozen 54-code nutrient set | ENERGY_KCAL only; other 53 UNKNOWN. |
| Existing FoodIngredient identities | No narrowing/broadening to absorb the two new identities. |
| Migration chain through 0042 | No 0043. |
| Medical/wellness boundary | Unchanged. |
| Runtime web independence | Retained derivative is authoritative; no live-web dependency. |

## 11. Future runtime semantics

### Fresh

1. reconcile the two identity-only FoodIngredients;
2. create the cheese Recipe inactive;
3. create immutable SOURCE_VERIFIED RecipeVersion from the retained source artifact;
4. publish prepared-output authority in the caller-owned UoW;
5. verify exact positive ENERGY_KCAL=83 projection before commit;
6. activate only through the existing guarded prepared activation boundary.

### Replay

- exact identity replay is zero-write;
- exact RecipeVersion + prepared authority replay is zero-write;
- deliberate deactivation remains deactivated;
- replay cannot replace retained bytes with live-web data.

### Conflict / failure

Fail closed on:

- retained-source SHA/size mismatch;
- reviewed card hash mismatch;
- source output/component quantity mismatch;
- narrower FoodIngredient substitution;
- same-code FoodIngredient identity conflict;
- Recipe without matching prepared authority or inverse;
- prepared value other than exact reviewed 83 kcal;
- any non-reviewed nutrient publication;
- activation before exact authority is readable;
- unapproved schema/migration need.

## 12. Projected product effect

Before R2-F runtime:

- exact-`MILK_2_5` unaffected BREAKFAST-compatible pool = 2;
- capacity = 6/week.

After the selected cheese sandwich:

- unaffected pool = 3;
- capacity = 9/week;
- required opportunities = 7.

The future runtime PR must prove a persisted seven-BREAKFAST week under hard exact
`MILK_2_5` exclusion with no RecipeVersion exceeding repetition=3.

Classification counts stay truthful:

- active `breakfast` classification remains 7;
- one active `sandwich` classification is added;
- BREAKFAST-compatible candidate pool becomes 8;
- LUNCH gains 1 compatible sandwich candidate;
- SNACK gains 1 compatible sandwich candidate.

This is **not a dairy-allergy claim**. Cheese is dairy; closure concerns exact
canonical `MILK_2_5` only.

## 13. Required runtime acceptance

A later R2-F runtime PR must prove at least:

1. exactly two new identity-only foods and no Nutrition/Composition;
2. exactly one immutable SOURCE_VERIFIED `sandwich` RecipeVersion;
3. exact 20 g bread + 11/10 g gross/net cheese + 30 g output;
4. prepared ENERGY_KCAL exactly 83;
5. all other 53 frozen nutrient codes UNKNOWN;
6. retained-source/hash tampering fails closed;
7. fresh RecipeVersion + prepared authority publication is atomic;
8. exact replay is zero-write;
9. deliberate deactivation remains deactivated;
10. guarded activation yields an exact-energy eligible candidate;
11. hard `MILK_2_5` rejects affected milk recipes but not egg, casserole or cheese sandwich;
12. persisted seven-BREAKFAST week succeeds;
13. no selected recipe exceeds repetition=3;
14. compatibility with BREAKFAST, LUNCH and SNACK uses the existing mapping;
15. no dairy-allergy/medical claim;
16. migration head remains 0042;
17. `AI_ENABLED=false`.

## 14. Verification tier

This PR is docs/data/source-evidence only.

Required:

- all committed JSON parses;
- retained raw-card SHA-256 and byte-size verification;
- durable Library materialize/readback verification;
- source_url / source_document_sha256 same-artifact verification;
- provenance roles separated: host / issuer / upstream collection;
- discovery derivative/card hash verification;
- butter contradiction calculation;
- source-policy scope exactly one card;
- identity review consistency;
- capacity arithmetic;
- Docs verification;
- DC1 corpus verification where triggered;
- scope/whitespace audit.

No runtime/backend regression is required for this gate.

## 15. Non-goals

No butter runtime publication, migration 0043, schema change, Planner
algorithm/mapping/repetition change, new Nutrition authority, ingredient
Nutrition/Composition, povidlo card, bulk web/PDF ingestion, DC4, Gate1-CLOSE,
PR9 Shopping, Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## 16. Stop rule

After this corrected Contract Gate is review-ready, stop for independent review.

Runtime implementation starts only after this gate is reviewed and merged.
