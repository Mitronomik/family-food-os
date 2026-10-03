# R2-D — Milk-exclusion breakfast resilience Contract Gate

**Status:** docs/data implementation contract gate — runtime publication blocked pending identity/applicability and quantity evidence
**Decision date:** 2026-10-03
**Issue:** #133
**Accepted base:** `463fe46f7c40156c1b8ebab5402ca45698d8c2bc` (merged PR #132)
**Runtime/data publication authorized by this document before merge:** no

## 1. Goal

Freeze the shortest truthful continuation after R2-C for the remaining BREAKFAST
exclusion-resilience gap.

R2-C proves six active exact-energy BREAKFAST RecipeVersions and capacity
18 opportunities/week at unchanged `max_recipe_repetitions=3`. Five of those
six require canonical `MILK_2_5`. A hard exclusion of that FoodIngredient
therefore leaves only `HARD_BOILED_EGG`, so a seven-BREAKFAST week remains
bounded-infeasible.

This gate asks whether the closest retained recipe evidence can close that gap
without changing Planner rules, schema, Nutrition authority or source truth.

## 2. FACT — accepted post-R2-C production state

Merged PR #132 establishes:

- active exact-energy BREAKFAST: 6 RecipeVersions;
- active exact-energy MAIN: 5 RecipeVersions;
- BREAKFAST capacity: 18/week before exclusions;
- current hard repetition limit: 3 uses per RecipeVersion;
- persisted seven-BREAKFAST path succeeds without the milk exclusion;
- `AI_ENABLED=false`;
- migration head remains `0042_recipe_prepared_output_nutrition`.

Milk-dependent active BREAKFAST recipes:

- `SCHOOL2022_54_1O_NATURAL_OMELET`;
- `SCHOOL2022_54_9K_MILK_OAT_PORRIDGE`;
- `SCHOOL2022_54_13K_WHEAT_MILK_PORRIDGE`;
- `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE`;
- `SCHOOL2022_54_25_1K_RICE_MILK_PORRIDGE`.

Unaffected active BREAKFAST recipe:

- `HARD_BOILED_EGG`.

Therefore:

`MILK_2_5 excluded → 1 candidate × repetition 3 = capacity 3/week < 7`.

This is a data/corpus hole, not a Planner-capacity algorithm defect.

## 3. FACT — durable source receipt

The retained project source archive remains:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Pinned receipt:

- size: 206692075 bytes;
- SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

Retained School2022 PDF:

- path inside archive:
  `corpus-work/packages/school2022/raw/source.pdf`;
- size: 4102547 bytes;
- SHA-256:
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- public locator:
  `https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf`.

Rights handling remains the accepted bounded factual normative-recipe policy in
`docs/family-food/ru-normative-recipe-corpus.md`.

## 4. Candidate review

### 4.1 School2022 54-1т — Запеканка из творога

Useful facts:

- source-card canonical SHA-256:
  `6103c16a7de140a83257e37908f34142788400d99832f04b2384f5d084d4e562`;
- process-text SHA-256:
  `911df98552cbcdf7e195b70dc0e96549f43864dc280f7e5fdc5a3ec54b9f6869`;
- exact source output: 150 g;
- source-card prepared energy: 301.2 kcal;
- the source ingredient table includes the water used to prepare the semolina;
- retained menu records repeatedly classify the dish under `Завтрак`.

Under the accepted R1-F/R1-G `PREPARED_OUTPUT_V1` rule, the same exact source
card that owns the RecipeVersion may also own its prepared-output Nutrition.
Therefore the 54-1т source-card value **301.2 kcal / 150 g** is prepared-energy
authority-ready for this exact card.

Retained 150 g breakfast-menu rows publish 301.3 kcal. That value is preserved as
a **cross-record QA signal only**. It does not compete with or override the exact
same-card 301.2 kcal authority. The normalized package's missing
prepared-energy-reconciliation record is a parser/evidence-packaging gap, not a
Nutrition-authority blocker.

**DECISION:** `REVIEW_REQUIRED_FOOD_IDENTITY_AND_HOUSEHOLD_APPLICABILITY`.

Prepared energy is ready at 301.2 kcal. Runtime publication is still not
authorized because exact FoodIngredient/form decisions and bounded household
applicability for this card have not yet been reviewed/frozen.

### 4.2 School2022 54-4т — Пудинг из творога с яблоками

Useful facts:

- source-card canonical SHA-256:
  `87f9795c847bfb42fafe548c15c94fea3c1961cbde4ed83d8ba0e63c7aa14a55`;
- process-text SHA-256:
  `84e93034211260267bb0301ab6a0dfef6388d46c15914f89449c1d10d49d5f5e`;
- exact source output: 150 g;
- prepared energy: 250.3 kcal;
- exact energy-reconciliation SHA-256:
  `b9b3868c7f1b7b1d0307448d94816aad01b9c5c239e65a37fc6e1c223ef7794f`.

The process explicitly says that vanillin is dissolved in hot water. The source
ingredient table does not quantify that water.

**DECISION:** `BLOCKED_REQUIRED_PROCESS_QUANTITY_UNRESOLVED`.

No default water quantity, zero quantity, invented amount or silent omission is
authorized.

### 4.3 School2022 54-6т — Сырники

Useful facts:

- source-card canonical SHA-256:
  `30b8c2ec933c055c40abf69692fd6a650487c19b54d919378dcd08df6c3d0306`;
- process-text SHA-256:
  `cb847403e9c074b78199e80992b33c14f64247719f7df7600742b9b843b606d0`;
- exact source output: 150 g;
- prepared energy: 319.1 kcal;
- exact energy-reconciliation SHA-256:
  `f2940dc90894cea2304af78f788c88e8b41f04e26b9405e8538a84634d6d28d2`;
- retained menu rows explicitly classify the dish under `Завтрак`.

The process explicitly says that vanillin is dissolved in hot water. The source
ingredient table does not quantify that water.

**DECISION:** `BLOCKED_REQUIRED_PROCESS_QUANTITY_UNRESOLVED`.

The process quantity cannot be invented merely because its energy contribution
would be negligible.

## 5. FACT — USSR82 egg fallback is not a prepared-output shortcut

The retained source inventory classifies USSR82-459/460/461/463/464 as:

- `PRODUCTION_RECONCILIATION_REQUIRED`;
- `reconciliation_publication_ready=false`;
- `dc1_production_ready=false`.

For USSR82-459 the retained coverage row is only legacy extraction evidence:

- recipe coverage record SHA-256:
  `dbef8e5c51bc39cf680fb4556215b80266f9eaa6526134bf9c83a9c4912164cc`;
- status `READY_RAW`;
- outer status `UNVERIFIED_LEGACY_EXTRACTION`;
- `ready_for_integration=false`.

The retained prepared-nutrient record for the same numbered dish is secondary
Ekodiet evidence, not accepted primary authority:

- record SHA-256:
  `30cd01c518067ffc41d9d4812936bcb990996c8ca03ab5a6f679506bb0e428a9`;
- output 79 g;
- published secondary energy 192 kcal;
- expected energy 228.1 kcal;
- `EnergyQA=CHECK`;
- `ready_for_integration=false`.

**DECISION:** no USSR82 egg-family RecipeVersion is authorized by this gate.

## 6. Food identity impact

Because no runtime candidate is authorized, this gate creates no new
FoodIngredient identity.

The review nevertheless records why a later cottage-cheese runtime batch would
need exact identity review rather than convenient reuse:

- School2022 standard cottage cheese basis is 5% fat; existing `TVOROG_9`
  is not equivalent;
- School2022 standard sour cream basis is 15% fat; existing
  `SOUR_CREAM_30` is not equivalent;
- generic/full-fat cottage-cheese identities are not automatic substitutes;
- semolina, vanillin and peeled-apple form must be resolved exactly where used.

No identity is created merely because a future candidate might need it.

## 7. Preservation matrix

| Existing truth | Required preservation |
|---|---|
| PR #132 / R2-C recipes and authorities | Byte/semantic behavior unchanged. |
| Existing active exact-energy BREAKFAST pool | No deactivation or relabeling. |
| `ROLE_COMPATIBILITY_V1` | Unchanged. |
| Planner v0.4 scoring/repetition | Unchanged; no algorithm workaround for missing data. |
| `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` | Reused only by a future exact reviewed batch; not changed here. |
| Frozen 54-code nutrient registry | No reinterpretation. |
| FoodIngredient identities | No new identity or equivalence in this gate. |
| Migration chain through 0042 | Immutable; no 0043. |
| School2022 source archive/PDF | Existing pinned bytes and hashes remain authoritative evidence. |
| Deliberate recipe deactivation semantics | Future replay must not reactivate it. |

## 8. Future runtime semantics if evidence is closed

A later runtime PR is permitted only after a separately reviewed decision freezes
an exact non-empty candidate set.

For every authorized future candidate:

### Fresh

- required FoodIngredient identities reconcile exactly;
- Recipe is created inactive;
- immutable SOURCE_VERIFIED RecipeVersion is created;
- exact prepared-output authority is published in the same caller-owned UoW;
- exact positive energy projection is verified before commit;
- activation remains a separate guarded command.

### Replay

- exact RecipeVersion + authority replay is zero-write;
- a deliberately deactivated Recipe remains deactivated;
- no newer/conflicting authority is overwritten.

### Conflict / partial state

Fail closed on:

- changed source-card/process/energy receipt;
- missing or unquantified required process ingredient;
- conflicting FoodIngredient identity;
- Recipe without its required prepared authority;
- prepared authority without matching immutable RecipeVersion;
- attempt to substitute a menu/reference energy row for exact same-card prepared-output authority;
- any attempt to turn UNKNOWN into zero or an estimate into exact truth.

## 9. Required adversarial acceptance for the future runtime PR

The runtime PR that eventually closes this gate must prove at least:

1. a hard `MILK_2_5` exclusion still allows a persisted seven-BREAKFAST week;
2. at least three unaffected active exact-energy BREAKFAST RecipeVersions exist
   under unchanged repetition=3;
3. no RecipeVersion exceeds repetition=3;
4. `MILK_2_5` candidates are rejected by the hard exclusion;
5. unaffected candidates do not inherit that rejection;
6. every selected recipe has exact source-backed required quantities;
7. unquantified process water cannot be synthesized/defaulted/ignored silently;
8. 54-1т exact same-card prepared energy remains 301.2 kcal and the 301.3 menu row remains non-authoritative QA evidence;
9. unsupported nutrients remain UNKNOWN;
10. fresh publication is atomic;
11. exact replay is zero-write;
12. deliberate deactivation remains deactivated;
13. tampered evidence fails closed;
14. migration head stays 0042 unless a separately approved contract reopens it;
15. `AI_ENABLED=false`.

## 10. Verification tier

This gate is docs/data evidence only.

Required evidence:

- durable archive locator, size and SHA-256;
- School2022 PDF SHA-256;
- exact selected record/process/reconciliation hashes;
- explicit cross-record discrepancy capture as non-blocking QA evidence;
- explicit process-quantity blocker capture;
- retained USSR82 fallback status/QA capture;
- documentation/state consistency;
- diff/whitespace checks;
- repository Docs/DC1 verification where triggered.

No backend full regression is required because this gate changes no runtime,
schema, persistence or authoritative production data.

## 11. Non-goals

This gate does not authorize:

- Recipe/RecipeVersion publication;
- activation;
- new FoodIngredient identities;
- migration 0043 or schema changes;
- Planner scoring, role compatibility or repetition changes;
- Nutrition authority changes;
- allergen automation;
- DC4 / Gate1-CLOSE;
- PR9 Shopping;
- Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI.

## 12. DECISION — gate outcome

**R2-D runtime publication remains BLOCKED, but 54-1т prepared energy is not the
blocker.**

54-1т is prepared-energy-ready from its exact source card at 301.2 kcal / 150 g
and remains review-required only for exact FoodIngredient/form decisions and
bounded household applicability. 54-4т and 54-6т remain genuinely blocked by
unquantified required process water. USSR82-459 remains blocked on prepared-output
authority.

This is a successful fail-closed contract result: the project does not trade
source truth for catalogue count and does not invent a stricter cross-record
Nutrition rule than the accepted `PREPARED_OUTPUT_V1` contract.

After independent review and merge, one separate bounded decision may choose
between:

1. completing exact FoodIngredient + household-applicability review for 54-1т
   (and separately deciding whether to close the 54-4т / 54-6т process-water
   evidence gaps); or
2. opening a role-expansion/source-authority gate for a clean alternative
   BREAKFAST/SANDWICH family.

Neither follow-up starts automatically.

## 13. OPEN QUESTION

Which path gives the highest product value per new authority surface after this
gate merges:

- complete 54-1т FoodIngredient/applicability review and only then assess the remaining cottage-family quantity gaps; or
- prioritize a new SANDWICH-capable source family that expands
  BREAKFAST/LUNCH/SNACK simultaneously?

The next operation should answer that question from evidence, not by weakening
this gate.
