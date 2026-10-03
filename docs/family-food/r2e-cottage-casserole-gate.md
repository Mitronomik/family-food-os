# R2-E — School2022 54-1т identity + household-applicability Contract Gate

**Status:** docs/data implementation contract gate
**Decision date:** 2026-10-03
**Issue:** #135
**Accepted base:** `99a579e35b0a0fa6d09947b80ffecb222a45bf96` (merged PR #134)
**Runtime publication authorized before this gate merges:** no

## 1. Goal

Freeze the smallest truthful runtime candidate after R2-D:

`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` — School2022 54-1т — Запеканка из творога.

R2-E closes only the remaining exact FoodIngredient/form and bounded
household-applicability review for this card. It does not claim to close the full
seven-BREAKFAST milk-exclusion gap.

## 2. FACT — accepted input from R2-D

R2-D established:

- source output = 150 g;
- exact same-card prepared `ENERGY_KCAL = 301.2`;
- authority = `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- 301.3 kcal retained menu row = non-authoritative QA-only;
- no new migration/Planner/Nutrition authority is needed.

The current active milk-exclusion pool remains only `HARD_BOILED_EGG`, capacity
3/week at unchanged repetition=3.

## 3. DECISION — candidate selection

54-1т is selected because it reuses the accepted School2022 source family,
contains exact required quantities including 36 g process water, is non-clinical,
has exact same-card prepared energy and is executable as ordinary household
baking.

Deferred alternatives:

- 54-4т / 54-6т remain blocked on unquantified required process water;
- 54-7т is explicitly `specialized_medical_scope=true` / “для детей с
  целиакией” and is not admitted into the current MVP wellness Planner;
- a standalone SANDWICH family remains valuable but would open a larger new
  source/bread-form/Nutrition authority surface and is not the shortest next step.

## 4. Source and immutable lineage

Durable archive:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

- archive size: 206692075 bytes;
- archive SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- School2022 PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

54-1т exact records:

- source card: `6103c16a7de140a83257e37908f34142788400d99832f04b2384f5d084d4e562`;
- source variant: `377ba327fa4823a431c648e4d6bfd795bb2944068c1f74ff6f52ebc0c82491d1`;
- process text: `911df98552cbcdf7e195b70dc0e96549f43864dc280f7e5fdc5a3ec54b9f6869`.

All ten ingredient-demand hashes are frozen in
`data/curation/r2e-cottage-casserole/publication-specs.json`.

The absence of a prepared-energy reconciliation row does not weaken the accepted
same-card authority: the exact card publishes 150 g and 301.2 kcal directly.

## 5. DECISION — FoodIngredient mappings

### Reuse exact existing identities

- `SUGAR` ← сахар-песок;
- `BREADCRUMBS` ← сухари панировочные;
- `EGG` ← яйцо куриное; runtime quantity uses exact net 4.0 g while gross 4.4 g
  remains in source text/provenance;
- `BUTTER_PEASANT_72_5_UNSALTED` ← School2022 standard 72.5% butter, matching
  the already accepted binding used by prior School2022 publications;
- `SALT_IODIZED` ← соль поваренная йодированная;
- `WATER` ← exact quantified 36 g.

### Create identity-only

- `TVOROG_5` — Творог 5% — dairy;
- `SEMOLINA_GROATS` — Крупа манная — grains;
- `SOUR_CREAM_15` — Сметана 15% — dairy;
- `VANILLIN` — Ванилин — staples.

No Nutrition or Composition authority is published for these four identities.

Explicit non-equivalences:

- `TVOROG_5 != TVOROG_9 != COTTAGE_CHEESE_FULL_FAT`;
- `SOUR_CREAM_15 != SOUR_CREAM_30` and no generic fat-class substitution;
- `SEMOLINA_GROATS != WHEAT_GROATS != wheat flour`;
- `VANILLIN != VANILLA_EXTRACT`.

## 6. DECISION — household applicability

54-1т is `HOUSEHOLD_APPLICABLE`.

The recipe-defining operations are ordinary household cooking: prepare semolina
in quantified hot water, combine cottage cheese/egg/sugar/salt, grease and
breadcrumb a baking dish, top with sour cream and bake in an oven. Independent
household recipes corroborate this method; they are applicability evidence only,
not Nutrition or quantity authority.

Consumer steps may retain the exact source temperature/time wording. The
institutional “пароконвектомат” alternative and serving-temperature requirement
are source context only and do not become required household execution rules.

No exact scalar `cook_time_minutes` is invented from “не менее 15 минут” plus
the source's staged temperature process; the structured scalar remains unknown.

## 7. BREAKFAST classification

Retained School2022 menus use 54-1т under `Завтрак`, supporting
`meal_type_code = breakfast`.

Menu rows do not own prepared Nutrition. In particular 301.3 kcal cannot replace
the exact same-card 301.2 kcal value.

## 8. Preservation matrix

| Existing truth | Required preservation |
|---|---|
| PR #134 / R2-D decisions | Same-card 301.2 authority and QA-only 301.3 interpretation unchanged. |
| Existing active recipes | No deactivation/relabeling. |
| Planner v0.4 compatibility/scoring/repetition | Unchanged. |
| `PREPARED_OUTPUT_V1` | Reused; no new authority kind. |
| Frozen 54-code nutrient set | ENERGY_KCAL available; all other unreviewed codes UNKNOWN. |
| Existing FoodIngredient identities | No broadening to absorb the four exact new forms. |
| Migration chain through 0042 | No 0043. |
| School2022 rights/source receipt | Reused unchanged. |
| Medical/wellness boundary | 54-7т remains outside ordinary MVP Planner admission. |

## 9. Future runtime fresh/replay/conflict semantics

After this gate merges, a bounded runtime PR may implement exactly this candidate.

### Fresh

1. reconcile four identity-only FoodIngredients;
2. create inactive SOURCE_VERIFIED Recipe/RecipeVersion;
3. publish exact prepared-output authority in the same caller-owned UoW;
4. verify exact positive 301.2 kcal projection before commit;
5. activate only through the existing guarded prepared activation boundary.

### Replay

- exact identity and RecipeVersion replay is zero-write;
- exact prepared authority replay is zero-write;
- deliberate Recipe deactivation remains deactivated;
- no replay may replace 301.2 with menu 301.3.

### Conflict / failure

Fail closed on:

- any changed source/variant/process/ingredient-demand hash;
- conflicting existing identity for any new exact code;
- substitution of `TVOROG_9`, generic/full-fat cottage cheese, `SOUR_CREAM_30`,
  wheat groats/flour or vanilla extract;
- changed source gross/net egg semantics;
- partial Recipe without prepared authority or the inverse;
- any prepared value beyond reviewed ENERGY_KCAL;
- activation before exact prepared authority is readable;
- any schema/migration requirement not authorized here.

Failure injection must prove the one-UoW fresh publication does not leave a
partial Recipe/authority state.

## 10. Projected product effect

Future runtime activation adds a second non-`MILK_2_5` breakfast candidate:

`HARD_BOILED_EGG + SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`.

At repetition=3 this is capacity 6/week.

**DECISION:** R2-E improves exclusion resilience but does not close a seven-day
milk-exclusion week. Runtime acceptance must not claim 7/7 feasibility.

## 11. Required runtime acceptance

A later runtime PR must prove at least:

1. exact four new identity-only foods and six exact reuses;
2. no Nutrition/Composition publication for the four new identities;
3. exact RecipeVersion source/process/ingredient/output binding;
4. prepared ENERGY_KCAL exactly 301.2; other frozen codes UNKNOWN;
5. 301.3 menu value cannot override or exact-replay as authority;
6. fresh Recipe + prepared authority is atomic;
7. exact replay is zero-write;
8. deliberate deactivation remains deactivated;
9. tampered contract/source hashes fail closed;
10. hard `MILK_2_5` exclusion leaves the new casserole eligible;
11. projected unaffected active pool becomes two candidates / capacity six;
12. no false assertion of seven-BREAKFAST feasibility;
13. `AI_ENABLED=false`;
14. migration head remains 0042.

## 12. Verification tier

This gate is docs/data curation only:

- evidence JSON parses;
- source/archive/hash consistency;
- exact identity mapping review;
- household applicability review;
- Docs verification;
- DC1 corpus verification where triggered;
- scope/whitespace checks.

No runtime/backend regression is required for this contract PR.

## 13. Non-goals

No runtime Recipe/FoodIngredient publication, activation, migration, schema,
Planner algorithm/role change, new Nutrition authority, 54-4т/54-6т repair,
54-7т medical admission, SANDWICH source-family publication, DC4, Gate1-CLOSE,
PR9 Shopping, Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## 14. Stop rule

After this Contract Gate is review-ready, stop for independent review.

Runtime implementation starts only after this gate is merged. The runtime PR must
also stop after review; it must not automatically start the next resilience
candidate.
