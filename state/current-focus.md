# Current focus

Updated: 2026-10-02.

## Accepted state

PR #121 / R1-G catalogue-capacity expansion gate is merged into `main` at:

`07af24cf1821bbb1ee9f70bdcc3311361d7b443b`.

The merged gate freezes the next runtime batch to exactly:

- `SCHOOL2022_54_29M_BEEF_MEATBALLS / Фрикадельки из говядины` —
  source output 80 g — exact prepared ENERGY_KCAL 153;
- `SCHOOL2022_54_2M_BEEF_GOULASH / Гуляш из говядины` —
  source output 80 g — exact prepared ENERGY_KCAL 185.6.

It also authorizes exactly four new identity-only FoodIngredients:

- `BEEF_CATEGORY_1_RAW`;
- `WHEAT_BREAD_HIGH_GRADE_STALE`;
- `SALT_IODIZED`;
- `TOMATO_PUREE_PASTE`.

Prepared Nutrition reuses only:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

## Current bounded operation

**R1-H — School2022 MAIN prepared-output runtime batch.**

Issue: `#122`.

PR: `#123`.

Branch: `feat/r1h-school2022-main-runtime`.

Accepted base:

`07af24cf1821bbb1ee9f70bdcc3311361d7b443b`.

Runtime freeze:

`c300118fd554829ddd9d6429c2abccba8dbb250b`.

## Runtime result

R1-H implements only the merged R1-G contract:

- the four identity-only FoodIngredients are idempotently reconciled;
- no FoodNutritionProfile or FoodComposition is created for those four identities;
- both School2022 Recipes publish inactive with the exact frozen Russian
  RecipeVersion truth;
- each RecipeVersion receives immutable sparse PREPARED_OUTPUT_V1 authority;
- ENERGY_KCAL is AVAILABLE and the remaining 53 frozen nutrients are UNKNOWN;
- fresh Recipe + prepared authority publication uses the existing caller-owned
  Recipe Nutrition UoW;
- activation uses the existing guarded `activate_prepared_recipe(...)` boundary;
- exact replay is zero-write and does not reactivate deliberate deactivation;
- historical R1-F egg/chicken truth remains unchanged.

Focused exact-runtime verification at `c300118f...`:

- R1-H affected/focused suite — 135 passed;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- Russian nutrition methodologies — SUCCESS.

Planner proof through the ordinary authoritative boundary shows:

- existing `BOILED_CHICKEN_MAIN_PRODUCT`;
- new beef meatballs;
- new beef goulash;

form three active exact-energy MAIN candidates.

Under unchanged `max_recipe_repetitions=3`, the real authoritative candidate
pool can cover a seven-opportunity DINNER/MAIN week without changing Planner
rules. Hard FoodIngredient exclusions still reject the corresponding real
candidate.

## Scope boundaries

Do not:

- add migration 0043 or any schema change;
- add raw Nutrition/Composition for the four identity-only foods;
- add another Nutrition authority kind/calculation version;
- publish School2022 54-1р;
- publish USSR82 467/492/1081/208/364;
- change Planner algorithm/scoring/roles/repetition;
- start R1-C persisted MealPlan proof;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3.

## Verification state

Runtime behavior is frozen at `c300118fd554829ddd9d6429c2abccba8dbb250b`.

Final exact-head verification was completed on review head
`d1bf279ffe76084d525dd99edbb9ff6346823f2d`:

- R1-H runtime — SUCCESS;
- focused/affected R1-H suite — 135 passed;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- Russian nutrition methodologies — SUCCESS;
- Docs verification — SUCCESS;
- DC1 corpus verification — SUCCESS;
- Nutrient registry V2 — focused + backend shards 0/1/2/3 + launcher SUCCESS;
- Partial nutrition profiles — focused + backend shards 0/1/2/3 + launcher SUCCESS.

After the runtime freeze, only `state/*` and test-only acceptance assertions
changed; production runtime bytes are unchanged. Relative to the verified
`d1bf279...` review head, the subsequent truth correction changes only
`state/*`.

Status:

`READY_FOR_FINAL_REVIEW`.

## Next step

Independent final review of PR #123.

After R1-H is explicitly reviewed and merged, reassess R1-C readiness against the
expanded production catalogue. Do not start R1-C automatically.
