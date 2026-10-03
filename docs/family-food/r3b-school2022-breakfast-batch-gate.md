# R3-B — School2022 ten-recipe BREAKFAST batch Contract Gate

**Status:** review gate  
**Issue:** #149  
**Accepted base:** `69c68f4153b25ac4e51cbe9ff54fb080201f08bd`  
**Runtime:** not authorized until this gate is independently reviewed and merged.

## FACT — why DC3 continues

Merged R3-A leaves the deterministic exact-energy catalogue at approximately 23
active usable RecipeVersions: 15 MAIN, 7 BREAKFAST and 1 SANDWICH. The sandwich
is breakfast/lunch/snack compatible, so the breakfast-compatible pool is 8.

DATA-CORPUS-V1 requires a `50–80+` verified usable baseline before DC4. Therefore
DC4 is not the next operation.

## DECISION — R3-B bounded goal

R3-B freezes exactly ten additional School2022 BREAKFAST RecipeVersions:

1. `ru-school2022:recipe:54-2о` — **Омлет с зеленым горошком** — 150 g / 153.5 kcal.
2. `ru-school2022:recipe:54-3о` — **Омлет с морковью** — 150 g / 201 kcal.
3. `ru-school2022:recipe:54-4о` — **Омлет с сыром** — 150 g / 316.0 kcal.
4. `ru-school2022:recipe:54-2т` — **Запеканка из творога с морковью** — 150 g / 249.5 kcal.
5. `ru-school2022:recipe:54-3т` — **Суфле из моркови с творогом** — 150 g / 200.9 kcal.
6. `ru-school2022:recipe:54-1к` — **Каша жидкая молочная кукурузная** — 200 g / 207.9 kcal.
7. `ru-school2022:recipe:54-6к` — **Каша вязкая молочная пшенная** — 200 g / 274.9 kcal.
8. `ru-school2022:recipe:54-16к` — **Каша «Дружба»** — 200 g / 168.9 kcal.
9. `ru-school2022:recipe:54-21к` — **Каша вязкая молочная ячневая** — 200 g / 249.1 kcal.
10. `ru-school2022:recipe:54-23к` — **Каша жидкая молочная пшеничная** — 200 g / 208.3 kcal.

This intentionally corrects the MAIN-heavy post-R3-A catalogue without changing
Planner role compatibility.

## FACT — source authority

The authoritative source remains the retained School2022 PDF inside the durable
Library archive.

- archive: 206,692,075 bytes;
- archive SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- School2022 PDF: 4,102,547 bytes;
- PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- latest independent Library materialize/readback: 2026-10-04 — PASS.

Public web is discovery/corroboration only. Runtime must not fetch source bytes.

## DECISION — FoodIngredient identity

Create identity-only only:

- `CHEESE_SEMI_HARD_UNSPECIFIED` — Сыр полутвердый;
- `CORN_GROATS` — Крупа кукурузная;
- `MILLET_GROATS` — Крупа пшенная;
- `BARLEY_GROATS` — Крупа ячневая;

Reuse accepted exact/broad-enough identities for all other rows. In particular,
generic source `морковь` maps to generic `CARROT`, not a narrower color-specific
identity.

No identity creation grants NutritionProfile or Composition authority.

## DECISION — process binding

1. Exact quantified RecipeIngredient totals are authoritative.
2. Unsupported per-step gram splits stay UNKNOWN.
3. Omelet butter keeps the source half/half process fact; runtime need not persist
   derived grams per step.
4. Cottage-cheese cards retain source butter placement/ratios without inventing
   remaining per-step allocations.
5. `54-16к` keeps exact WATER=70 g at recipe level; its rice/millet split is
   UNKNOWN.
6. `54-23к` keeps WATER=68 g as exact source input. Because excess water is
   explicitly drained, retained-water/yield remains UNKNOWN.
7. Wash/rinse/scald water not quantified in the recipe table is process-resource
   context and is not promoted to RecipeIngredient.
8. `54-22к` is not selected because its table quantifies butter while the
   technology does not place it.

## DECISION — household applicability

All ten selected cards are ordinary, non-clinical breakfast preparations using
household-equivalent stovetop, oven, steaming or basic preparation tools.

Institutional serving temperatures, paraconvection wording and industrial
equipment names are quarantined as source context; they do not alter ingredient
quantities, output or prepared Nutrition authority.

The specialized celiac card `54-7т` remains excluded from ordinary wellness
publication.

## DECISION — Nutrition authority

Use the existing:

`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.

For each selected RecipeVersion:

- exact same-card `ENERGY_KCAL` is AVAILABLE;
- all other 53 frozen nutrient codes are UNKNOWN;
- source macros/micros are QA/reference only;
- no source scaling;
- no raw/cooked retention inference;
- unknown is never zero.

## DECISION — future transaction semantics

Reuse merged R3-A option B; no new activation architecture is authorized.

Publication is per recipe and atomic while inactive. A failure may leave an exact
inactive subset. Exact replay is zero-write and rerun converges missing rows.

Activation begins only after all ten RecipeVersions and prepared authorities
reconcile exactly:

- all inactive → activate all ten in one batch UoW / one commit;
- all active → zero-write replay;
- mixed active/inactive → fail closed;
- failure before commit → rollback whole activation UoW.

The future runtime remains **one PR for all ten recipes**. No separate activation PR.

## Projected effect

If the future runtime is accepted:

- active exact-energy recipes: ~23 → ~33;
- breakfast-compatible candidates: ~8 → ~18;
- active MAIN: 15 unchanged;
- active SANDWICH: 1 unchanged;
- breakfast repetition capacity at max 3: 54 opportunities/week.

This still does not satisfy the `50–80+` baseline; another DC3 batch remains
necessary before DC4.

## Acceptance for the future runtime

The runtime PR must prove:

1. exactly four new identity-only foods and no Nutrition/Composition rows for them;
2. exactly ten new immutable SOURCE_VERIFIED BREAKFAST RecipeVersions;
3. exact source quantities, process, output and ENERGY_KCAL;
4. ENERGY_KCAL + 53 UNKNOWN for each;
5. per-recipe publication atomicity and resumable convergence;
6. all-inactive one-UoW activation;
7. mixed-state fail-closed;
8. all-active zero-write replay;
9. activation rollback on injected failure;
10. R3-A/R2-F activation regressions remain green;
11. Planner role mapping/scoring/repetition unchanged;
12. migration head remains 0042;
13. `AI_ENABLED=false`.

## Non-goals

No runtime in this gate. No migration 0043, schema change, Planner change, new
Nutrition authority, R3-C, DC4, Gate1-CLOSE, PR9, Shopping, Prep, Retail, API,
UI, Auth, PostgreSQL or AI.

## Stop rule

Deliver this docs/data gate and stop for independent review. Runtime begins only
after explicit review/merge of this gate.
