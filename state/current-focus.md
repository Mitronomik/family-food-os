# Current focus

Updated: 2026-09-26.

## Accepted state

PR96 / Step 10-B is merged into `main` at:

`7443f56b856184db6ddb040b9d68425db9f8d41a`.

Accepted reusable path:

```text
composition-backed V2 Recipe Nutrition
→ neutral consumption projection
→ Planner exact-energy readiness
→ planner-v0.3
→ MealPlan / Serving nutrition consumption
```

DATA-CORPUS-V1 remains the active programme before Gate1-CLOSE.
PR9 Shopping remains blocked until Gate1-CLOSE.

## Current bounded state

**PR97 — USSR82-453 Planner-Eligibility Candidate Preflight Contract is ACTIVE.**

Branch:

`docs/dc3-first-planner-eligible-recipe-contract`

Selected candidate:

`USSR82-453 — Яйца вареные`

Accepted DC1 facts:

- sole `DC3-A_CLEAN_BRANCH_EXISTING_PROFILE_REVIEW` candidate;
- one selected source branch;
- one retained relationship row;
- `ING-0071 → EGG` accepted identity mapping;
- current USDA FDC Foundation 748967 profile exists;
- `production_ready = NO`;
- recipe-form/profile suitability is unresolved.

## Review correction

Detailed PR97 review `#5327395931` found blocking contract/state issues.

PR97 is being corrected to a **preflight/evidence contract**, not a direct
runtime-publication authorization.

The preflight contract now freezes that production publication remains blocked
until evidence closes:

- durable exact source/card/variant provenance;
- exact 40 g quantity/basis semantics;
- EGG form/profile suitability;
- transformation/yield/retention disposition;
- deterministic Recipe Nutrition authority;
- exact `meal_type_code` proposal;
- unchanged `meal-role-recipe-v2` compatibility result;
- rights/provenance disposition;
- final `ACTIVATE_CANDIDATE | PUBLISH_INACTIVE | BLOCKED` decision.

## Source reproducibility blocker

The retained DC1 relationship row derives from:

`russian_normative_recipes_v22_5_row_nutrients_part1.xlsx`

SHA-256:

`72a70f31b6b59454a94d78b73bdf2d43119f04799b266773bb34917e9cb3961e`

DC1 records the source bundle as operator-managed with temporary authenticated CI
delivery, but does not record the durable private storage locator required by the
current DATA-CORPUS-V1 durability contract.

That gap must be closed in the evidence-only preflight before production
publication can be authorized.

## Hard boundaries

PR97 changes docs/state only.

Not authorized:

- production RecipeVersion write;
- Recipe activation;
- FoodIngredient/profile mutation;
- transformation/yield/retention publication;
- migration;
- Planner/MealRole compatibility change;
- Gate1-CLOSE;
- PR9 Shopping;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Stop boundary

Review and merge the corrected PR97 preflight contract first.

After merge, the next separately authorized operation is **USSR82-453
evidence-only preflight**.

Do not begin production publication or activation automatically.
