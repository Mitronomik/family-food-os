# R3-D — Final DC3 Batch Contract Gate

**Status:** implementation contract / evidence gate — preflight complete / review-ready
**Issue:** #157
**Accepted base:** `1c82f34b960621aed3e1c43780270f8048edfe0f`
**Scope:** docs + curation evidence only

## 1. Decision

PR #156 is merged. DATA-CORPUS-V1 / DC3 remains active.

This gate implements the later explicit product decision that **R3-D is the last
planned DC3 catalogue-expansion pair before DC4**.

The lower DATA-CORPUS-V1 usable baseline is `50–80+`; the current post-R3-C
exact-energy Planner-supported catalogue is 41. R3-D therefore needs at least 9
additional source-clean usable RecipeVersions.

The gate freezes **10** recipes. The target is not “ten because ten looks nice”:
the selected set crosses 50 with a one-recipe buffer and materially improves
MAIN diversity without weakening source truth.

Runtime publication remains a separate future PR and is not authorized until this
gate is independently reviewed and merged.

## 2. FACT — current post-R3-C truth

The committed validator reconstructs current truth from accepted runtime
publication code/packages and current Planner contracts rather than trusting this
document or `summary.json`.

Expected current result:

- exact-energy active: **41**;
- `breakfast`: 17;
- `main`: 23;
- `sandwich`: 1;
- breakfast-compatible: 18;
- `max_recipe_repetitions=3`;
- hard exact `MILK_2_5`: 15 dependent breakfast recipes, 3 unaffected
  breakfast-compatible recipes, capacity 9;
- MAIN exact `BEEF_CATEGORY_1_RAW`: 12;
- fish-based MAIN: 9;
- chicken-based MAIN: 2;
- meat-free MAIN: 0;
- gap to 50: 9;
- DC4: not yet ready.

## 3. DECISION — exact R3-D batch

All selected records use the already retained normative source
`RU_MR_2_4_0162_19`, Appendix 5, the `12 лет и старше` quantity/output
column.

| # | Canonical code | Russian name | Source card | Type | Output | kcal |
|---|---|---|---|---|---:|---:|
| 1 | `MR2019_1_2A_VEGETARIAN_CABBAGE_SOUP` | Щи из свежей капусты вегетарианские | 1.2а | main | 350 g | 112 |
| 2 | `MR2019_1_3_LENINGRAD_RASSOLNIK_SOUR_CREAM` | Рассольник ленинградский со сметаной | 1.3 | main | 350 g | 119 |
| 3 | `MR2019_1_4_OAT_VEGETABLE_SOUP_SOUR_CREAM` | Суп овсяный с овощами и сметаной | 1.4 | main | 350 g | 112 |
| 4 | `MR2019_1_16_POTATO_SPLIT_PEA_SOUP` | Суп картофельный с горохом | 1.16 | main | 350 g | 219 |
| 5 | `MR2019_6_9_VERMICELLI_HARD_CHEESE` | Вермишель с тёртым сыром | 6.9 | main | 120 g | 193 |
| 6 | `MR2019_6_19_BAKED_MACARONI_HARD_CHEESE` | Макаронник с сыром запечённый | 6.19 | main | 180 g | 313 |
| 7 | `MR2019_2_15_STEAMED_CHICKEN_SOUFFLE` | Суфле из отварной курицы паровое | 2.15 | main | 115 g | 291 |
| 8 | `MR2019_2_14_BOILED_CHICKEN_CATEGORY_1` | Курица 1 категории отварная | 2.14 | main | 110 g | 267 |
| 9 | `MR2019_2_11_BEEF_VEGETABLE_RAGOUT` | Рагу из овощей с отварной говядиной | 2.11 | main | 230 g | 336 |
| 10 | `MR2019_2_9_STEAMED_BEEF_ROLL_OMELET` | Рулет говяжий с омлетом паровой | 2.9 | main | 105 g | 222 |

The exact ingredient rows, source hashes, process decisions and Russian consumer
steps are frozen in:

`data/curation/r3d-final-dc3-batch-gate/frozen-batch.json`.

## 4. Product-value selection

### 4.1 MAIN concentration

Current 23 MAIN candidates are highly concentrated:

- 12 exact category-I beef;
- 9 fish;
- 2 chicken;
- 0 meat-free.

R3-D adds:

- 6 meat-free MAIN;
- 2 chicken MAIN;
- 2 beef MAIN;
- 0 fish.

Projected 33 MAIN:

- beef: 14;
- fish: 9;
- chicken: 4;
- meat-free: 6.

Beef-or-fish share therefore moves:

```text
21/23 -> 23/33
```

The exact-beef hard exclusion path improves from 11 unaffected MAIN today to a
projected 19 unaffected MAIN, capacity 57 under repetition=3.

The two new beef recipes are retained because they add materially different
household patterns — vegetable-heavy ragout and a steamed stuffed roll — rather
than another cutlet/meatball duplicate.

### 4.2 Milk-free breakfast resilience

R3-D does **not** claim to improve the hard exact-`MILK_2_5` breakfast path.

The retained source review found no additional source-clean in-scope candidate:

- School2022 `54-3т`: quantified sugar not placed in technology;
- `54-4т` / `54-6т`: vanillin requires unquantified hot water;
- `54-5т`: source table/process fat conflict;
- `54-7т`: specialized celiac/medical scope;
- MR card 6.5а: ingredient table has no milk but retained technology instructs
  adding milk;
- MR 5.46 cottage-cheese soufflé: technology explicitly adds salt with no
  quantitative source row.

The current unaffected set therefore remains exactly:

- `HARD_BOILED_EGG`;
- `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- `SAD28_SANDWICH_CHEESE_20_10`.

Count 3 × repetition 3 = capacity 9.

This is a real remaining catalogue-quality gap. It is not a reason to weaken
source evidence before DC4.

### 4.3 Household variety

The selected batch adds several ordinary household patterns missing from the
current exact-energy pool:

- vegetarian cabbage soup;
- rassolnik;
- oat/vegetable soup;
- split-pea/potato soup;
- vermicelli with cheese;
- baked macaroni with cheese;
- steamed chicken soufflé;
- whole boiled chicken;
- beef-and-vegetable ragout;
- steamed beef roll with omelet.

No fish recipes are added.

## 5. Meal-type classification and reviewer focus

Current `MealTypeCode` has no dedicated `soup` type. Under the current coarse
catalogue taxonomy, the four hot soups are frozen as `main` and therefore
Planner-supported for LUNCH.

This is a **per-recipe data classification**, not a Planner role/mapping change.

It is intentionally a reviewer focus because three of the soups have relatively
low source energy per 350 g portion. DC4 must test realistic persisted weeks and
Serving feasibility rather than treating the raw recipe count as sufficient
readiness.

If independent review rejects these soups as ordinary `main` candidates under
the current product model, this gate must be reconsidered; they must not be
silently relabelled or counted only to cross 50.

## 6. Source / provenance

Selected R3-D recipes use only the repository-retained MR bundle:

`data/seed/ru_normative_recipe_corpus/mr_2_4_0162_19.bundle.json`

Pinned bundle Git blob:

`9210458b9ad81aa3650eccad7935519f8d375432`

Original retained document receipts:

- raw bytes SHA-256:
  `973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e`;
- raw text SHA-256:
  `b5a05ffb36d34cd7bd82de71b55319d72ac850064302bf228e1e1ad19fd02062`;
- source version: `2019-12-30`;
- publication policy: `NORMATIVE_BASE_RECIPE_APPROVED`.

Every selected card pins its own `raw_card_sha256`. The validator recomputes
that hash from the committed raw-card text and checks the 12+ ingredient/output
and energy row against the frozen package.

The private School2022 corpus archive is used only to reproduce the rejected
milk-free-breakfast candidate audit. No selected R3-D runtime recipe depends on
that private archive.

## 7. Identity-only FoodIngredients

R3-D freezes exactly ten new FoodIngredient identities:

1. `VEGETABLE_OIL_REFINED_UNSPECIFIED`;
2. `CUCUMBER_PICKLED_CANNED`;
3. `SOUR_CREAM_20`;
4. `SPLIT_PEAS_DRY`;
5. `CHEESE_HARD_UNSPECIFIED`;
6. `CHICKEN_CATEGORY_1_WHOLE_RAW`;
7. `MILK_3_2`;
8. `FLOUR_WHEAT_FIRST_GRADE`;
9. `CHEESE_DUTCH_HARD`;
10. `BUTTER_PEASANT_72`.

They are **identity-only**. The gate grants none of them:

- FoodNutritionProfile authority;
- NutrientVector authority;
- Composition authority.

This higher identity count is intentional. The gate does not collapse:

- milk 3.2% into `MILK_2_5`;
- wheat flour first grade into high-grade flour;
- Dutch cheese into generic hard cheese;
- 72% butter into accepted 72.5% butter;
- unspecified refined vegetable oil into sunflower/canola.

Exact form truth is preferred over artificial debt minimization.

## 8. Process and fail-closed review

Notable rejected/deferred cards include:

- MR 1.2: butter in table vs vegetable oil in process;
- MR 1.4а: vegetable oil in table while process calls for butter and sour cream;
- MR 2.2: 12+ table gives 4 g greasing oil while technology fixes 2 g;
- MR 2.17: beef ingredient table vs chicken technology;
- MR 2.24: depends on separate chicken-broth recipe/intermediate N 1.0;
- School2022 54-5м / 54-12м: sunflower-oil table vs butter process;
- 54-22м / 54-27м: unquantified process water and/or unusable bay-leaf mass;
- 54-28м: unquantified process water;
- the School2022 breakfast blockers listed in §4.2.

Clean but low-incremental-value beef cutlet/meatball duplicates were also not
selected.

Unknown remains unknown. Source presence is not publication readiness.

## 9. Future runtime transaction contract

Reuse merged R3-A/R3-B/R3-C Option B.

### Publication

For each frozen recipe:

```text
inactive RecipeVersion
+ exact prepared authority
→ one caller-owned UoW
→ one commit
```

Required semantics:

- fresh publication is atomic per recipe;
- exact replay is zero-write;
- exact inactive subset is resumable;
- failed recipe leaves no partial state;
- conflicting/partial persisted truth fails closed;
- publication never activates.

### Activation

Activation begins only after every frozen recipe exactly reconciles.

- all inactive → one caller-owned batch UoW / one commit;
- all active → zero-write replay;
- mixed active/inactive → fail closed;
- injected failure → rollback all staged activation writes.

No new activation architecture is authorized by this gate.

## 10. Projection

After a successful separately authorized R3-D runtime:

- exact-energy active: **51**;
- breakfast: 17;
- MAIN: **33**;
- sandwich: 1;
- breakfast-compatible: 18;
- hard exact-`MILK_2_5` unaffected set: 3 / capacity 9, unchanged;
- exact category-I beef MAIN: 14;
- fish MAIN: 9;
- chicken MAIN: 4;
- meat-free MAIN: 6;
- exact-beef unaffected MAIN: 19 / capacity 57;
- gap to 50: **0**;
- gap to 80: 29.

Crossing 50 is necessary but not itself DC4 completion.

**DECISION:** after successful R3-D runtime and post-runtime reconciliation, the
next planned operation is **DC4 corpus readiness audit + Gate1 consumption**.

No further discretionary DC3 expansion batch is authorized merely to make the
catalogue larger.

A concrete defect discovered by DC4 may require a separate reviewed correction;
that is not a license for R3-E/R3-F catalogue expansion.

## 11. Durable verification

Committed validator:

`scripts/validate_r3d_final_dc3_gate.py`

Retained receipt:

`data/curation/r3d-final-dc3-batch-gate/verification.json`

Repo-contained verification:

```bash
python scripts/validate_r3d_final_dc3_gate.py --json
```

Optional School2022 gap-audit reproduction:

```bash
python scripts/validate_r3d_final_dc3_gate.py \
  --school-archive "$R3D_SCHOOL_ARCHIVE" \
  --json
```

The validator independently derives post-R3-C repository truth, checks current
Planner compatibility, current FoodIngredient reuse universe, selected mappings,
identity-only boundaries, MR source card hashes/rows, product mix, projections
and the DC4 handoff condition.

It does not accept `summary.json` as the authority for the numbers it verifies.

## 12. Non-goals

This gate does not:

- publish or activate R3-D runtime data;
- add migration 0043 or schema changes;
- change Planner roles/scoring/repetition;
- create a new Nutrition authority;
- introduce recipe-intermediate/sub-recipe architecture;
- start DC4 inside this PR;
- start Gate1-CLOSE;
- start PR9 Shopping;
- start Prep/PDF/PWA/Retail/Auth/PostgreSQL/AI;
- authorize a later discretionary R3-E/R3-F expansion.

## 13. Next allowed action

If this Contract Gate is independently reviewed and merged, the only next
bounded operation is:

**one R3-D runtime PR implementing exactly this frozen ten-recipe batch.**

After that runtime merges:

```text
post-runtime reconciliation
→ DC4 corpus readiness audit + Gate1 consumption
→ Gate1-CLOSE
→ PR9 Shopping Engine
```

Do not start another planned DC3 expansion batch between R3-D runtime and DC4.
