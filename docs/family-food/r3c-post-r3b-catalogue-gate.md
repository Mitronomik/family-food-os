# R3-C — Post-R3B DC3 Catalogue Contract Gate

**Status:** implementation contract / evidence gate
**Issue:** #153
**Accepted base:** `90c4f0ebab693b01ec5b4cf7b93b67feeaf0ddb4`
**Scope:** docs + curation evidence only

## 1. Decision

PR #152 is merged. DATA-CORPUS-V1 / DC3 remains active. R3-B proved technical BREAKFAST capacity, but it did not close catalogue readiness.

The next authoritative publication unit is frozen as **eight** School2022 MAIN RecipeVersions. The target was approximately 10–12, but the gate deliberately does not pad the batch: the nearest additional cards contain unresolved required-ingredient placement, unquantified process inputs, or contradictory fat semantics.

Runtime publication is a separate future PR and requires this gate to be independently reviewed and merged first.

## 2. Post-R3B catalogue snapshot

Repository truth separates *verified rows* from *usable Planner truth*.

- ordinary PR4 seed: 30 `SOURCE_VERIFIED` recipes, default-active under the seed contract;
- accepted DC3 exact-energy runtime catalogue after R3-B: 33 active recipes;
- the two code sets are disjoint, so the repository-defined verified union is 63;
- only the **33 exact-energy Planner-supported** recipes count toward the current DATA-CORPUS-V1 usable baseline.

Exact-energy meal types:

| Type | Count | repetition=3 capacity |
|---|---:|---:|
| `breakfast` | 17 | 51 |
| `main` | 15 | 45 |
| `sandwich` | 1 | 3 |
| breakfast-compatible | 18 | 54 |

The lower DATA-CORPUS-V1 target is `50–80+` usable verified recipes. Current gap to 50 is **17**. **DC4 is not ready.**

## 3. Exclusion resilience

### `MILK_2_5`

Fifteen of the 17 exact-energy `breakfast` recipes depend on `MILK_2_5`. The unaffected breakfast-compatible set remains exactly:

- `HARD_BOILED_EGG`;
- `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`;
- `SAD28_SANDWICH_CHEESE_20_10`.

Count 3 × max repetition 3 = capacity 9, therefore the accepted seven-breakfast hard-exclusion proof must remain green. R3-C does not weaken this invariant.

No new milk-free BREAKFAST candidate is frozen here: retained nearby candidates have unresolved process/quantity evidence or insufficient incremental Planner value. That remains a real resilience/variety gap; it is not permission to infer source truth.

### MAIN concentration

Current MAIN is concentrated as a curation signal: seven exact recipes use `BEEF_CATEGORY_1_RAW`, seven are fish-based across several exact fish identities, and one is chicken-based.

Current Planner hard exclusions are exact `FoodIngredient` exclusions, not a synthetic “all meat/all fish” category rule. Excluding `BEEF_CATEGORY_1_RAW` leaves 8 current MAIN candidates, capacity 24; a seven-MAIN week therefore does not structurally depend on this one identity. No invented category-wide hard-exclusion test is added.

## 4. Frozen R3-C batch

1. `SCHOOL2022_54_21M_BOILED_CHICKEN` — Курица отварная — 80 g / 123.8 kcal.
2. `SCHOOL2022_54_3M_LAZY_CABBAGE_ROLLS` — Голубцы ленивые — 100 g / 128.4 kcal.
3. `SCHOOL2022_54_26M_POTATO_BEEF_CASSEROLE` — Запеканка картофельная с говядиной — 200 g / 408.7 kcal.
4. `SCHOOL2022_54_1M_BOILED_BEEF_STROGANOFF` — Бефстроганов из отварной говядины — 80 g / 167.5 kcal.
5. `SCHOOL2022_54_30M_BEEF_RICE_QUENELLES` — Кнели из говядины с рисом — 80 g / 184.6 kcal.
6. `SCHOOL2022_54_20M_BOILED_BEEF` — Говядина отварная — 80 g / 257.1 kcal.
7. `SCHOOL2022_54_15R_SALMON_IN_MILK` — Сёмга, запечённая в молоке — 80 g / 151.7 kcal.
8. `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES` — Сёмга в томате с овощами — 70 g / 140.3 kcal.

All eight are `main` under the current Planner contract. Full ingredient rows, source record/process/output hashes, Russian steps and process-binding decisions are frozen in `data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json`.

One new FoodIngredient identity is allowed, **identity-only**:

- `ATLANTIC_SALMON_FILLET_RAW`.

They receive no NutritionProfile, NutrientVector or Composition authority.

## 5. Why not 10–12

The gate rejects numerical padding. Nearby cards remain out for concrete evidence defects: `54-19м` consumes 5 g butter for onion, then “remaining” butter in the mass, then additionally greases the form with butter without a quantified remaining share; `54-31м` and `54-12р` have unplaced quantified salt; `54-17м` has unplaced parsley; `54-15м` uses unquantified water/bay leaf; `54-23м/54-24м` conflict on sunflower oil vs butter; `54-25м` has unresolved two-fat placement; `54-4т/54-6т` need unquantified water; `54-3т/54-21к/54-22к` retain already-known placement gaps; `54-7т` is medical/celiac scope.

Unknown stays unknown. A recipe is not admitted just to hit a batch-size target.

## 6. Source and provenance

Durable archive: `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

- bytes: `206692075`;
- SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- independently retrieved and re-hashed: 2026-10-04.

School2022 PDF inside that archive:

- path: `corpus-work/packages/school2022/raw/source.pdf`;
- bytes: `4102547`;
- SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Every selected card pins canonical source-record, process-text, output-row and energy-reconciliation hashes. Runtime must consume only the frozen repository package; live web/Library access is not a runtime dependency.

## 7. Process and household rules

Selected technologies use ordinary household cooking operations. Institutional thawing, holding, paraconvection and serving-temperature text is provenance-only where separable.

R3-A/R3-B rules remain: exact ingredient total is authoritative; internal per-step split may remain UNKNOWN; a single same-card fat may bind to an otherwise unqualified sauté/oiling operation without inventing a gram split; an unmentioned required ingredient is not placed by culinary assumption; an alternate branch that requires an unquantified ingredient is not selected.

For `54-30м`, only the steam branch 15–20 minutes is frozen. The water-poaching alternative stays provenance-only because added water is not quantified.

Consumer Recipe Steps are Russian only.

## 8. Future runtime transaction contract

Reuse merged R3-A/R3-B Option B.

Publication: per-recipe atomic inactive RecipeVersion + prepared authority; exact replay zero-write; exact inactive subset resumable; partial/conflicting truth fails closed; publication never activates.

Activation: starts only after all eight exact publications reconcile; all-inactive uses one caller-owned UoW / one commit; all-active replay is zero-write; mixed state fails closed; injected activation failure rolls back all staged writes.

No new activation architecture is authorized.

## 9. Future runtime acceptance

The later runtime PR must prove exact eight-recipe publication/activation, package tamper rejection, identity conflict rejection, wrong prepared ENERGY_KCAL rejection, exact replay, deliberate-deactivation preservation, mixed-state fail closed, rollback, Russian-only persisted steps, unchanged hard `MILK_2_5` breakfast proof, migration head `0042` / no `0043`, and `AI_ENABLED=false`.

## 10. Projection

After future R3-C runtime:

- exact-energy active: **41**;
- `breakfast`: 17;
- `main`: **23**;
- `sandwich`: 1;
- breakfast-compatible: 18;
- gap to 50 usable: **9**;
- gap to 80: 39;
- DC4: **still blocked**.

The broader repository-defined active verified union would become 71, but that number does not substitute for Planner/exact-energy usability. R3-C improves process/dish variety and adds chicken/salmon options, but it does not close protein-family concentration; that remains a later catalogue-quality concern.

## 11. Non-goals

This gate does not authorize runtime publication, activation, migration `0043`, schema changes, Planner changes, new Nutrition authority, DC4, Gate1-CLOSE, PR9, Shopping, Prep, PDF, PWA, Retail, Auth, PostgreSQL, AI or generalized ingestion.

## 12. Next allowed action

After independent review and explicit user-authorized merge of this Contract Gate, the next bounded operation may be **one R3-C runtime PR implementing exactly the frozen eight-recipe batch**.

Do not start DC4 or PR9 automatically.


## Durable verification procedure

This Contract Gate keeps its verification procedure in repository truth rather
than only in an agent session.

Committed validator:

```text
scripts/validate_r3c_post_r3b_gate.py
```

Retained receipt:

```text
data/curation/r3c-post-r3b-catalogue-gate/verification.json
```

The validator is read-only. With `--repo-only` it validates the frozen package,
selected set, mappings, meal types, authority boundaries, Russian consumer text,
exclusion analysis and current/projected arithmetic. With
`--source-archive <path>` it additionally recomputes the durable corpus ZIP and
School2022 PDF hashes and all four frozen source hashes for each of the eight
selected cards.

Canonical full command:

```bash
python scripts/validate_r3c_post_r3b_gate.py \
  --source-archive "$R3C_SOURCE_ARCHIVE" \
  --json
```

The archive path is supplied by the operator after materializing the durable
Library artifact; no private path, temporary URL or network dependency is baked
into the validator.


### Repository-derived current truth

The validator must not accept frozen arithmetic merely because `summary.json`
contains expected constants. Repo-only verification reconstructs the accepted
post-R3B exact-energy catalogue from merged runtime publication code and accepted
publication specs, then compares that derived result to the frozen summary.

It also derives the accepted FoodIngredient reuse universe from repository truth.
Every selected `food_code` must exist in that current universe except the one
explicit new identity `ATLANTIC_SALMON_FILLET_RAW`.

Current meal-type support is parsed from the repository's
`ROLE_COMPATIBILITY_V1`; `main` is not assumed by the gate. Current repetition
capacity is parsed from `PlannerConfig.max_recipe_repetitions`.

The durable receipt records both newly executed repo-derived checks and any
explicitly reused source-archive evidence under the proportional-verification
policy; reused evidence must name its tested revision and reason.
