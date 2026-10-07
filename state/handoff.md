# Handoff

## Post-DC4 correction reconciliation — 2026-10-07

Accepted main:

`d3e73072e4e24dde25a1251e19327731455e306f`.

Merged evidence/research:

- PR #165 — DC4 evidence, product gate BLOCKED;
- PR #168 / Issue #166 — seven genuine Russian RecipeStep language violations;
- PR #169 / Issue #167 — Planner Fixture 3 role/order root cause isolated.

Current reconciliation: Issue #170 / branch `docs/post-dc4-correction-reconciliation`.

Read before continuing:

- `AGENTS.md`;
- `state/current-focus.md`;
- `docs/family-food/dc4-corpus-readiness-contract.md`;
- `docs/family-food/dc4-corpus-readiness-report.md`;
- `docs/family-food/dc4-russian-steps-investigation.md`;
- `docs/family-food/dc4-planner-mealplan-order-investigation.md`.

After this reconciliation is merged, two bounded tracks may run independently:

### A — immutable Russian RecipeStep correction

Exact sequence:

```text
A1 evidence                         MERGED #168
→ A2 docs-only immutable correction Contract Gate
→ A3 separately reviewed RecipeVersion runtime/data correction
→ A accepted
```

A2 must define a version-aware publication route preserving immutable RecipeVersion history, exact retained source/provenance, process bindings, rights, ingredient quantities and Nutrition authority. Do not edit prior versions in place.

**A2 merge alone does not complete Track A and does not authorize DC4 rerun.** A3 must be independently reviewed, merged and verified first.

### B — Planner ordering runtime correction

The accepted investigation classifies the current defect as a local Planner ordering bug. Implement a focused correction preserving per-member precedence and MealPlan completeness.

Critical review rule: deterministic output semantics are versioned. The known Fixture 3 fix changes event ordering for the same accepted inputs, so B2 is expected to introduce a new Planner algorithm/config version. Do not silently alter `planner-v0.4`. Preserving the old version identity requires explicit independently reviewed evidence that semantics are unchanged.

If B implementation reveals a necessary cross-context contract change, stop and create/merge a docs-only Contract Gate before further runtime work.

Required downstream order:

```text
Track B
B1 investigation                    MERGED #169
→ B2 versioned Planner ordering runtime correction
→ B accepted

A3 accepted + B2 accepted
→ separate DC4 rerun
→ separate Gate1-CLOSE
→ PR9 only if Gate1-CLOSE passes
```

Do not interpret A2 Contract Gate acceptance as Track A completion.

No DC4 rerun, Gate1-CLOSE or Shopping implementation belongs to this reconciliation PR.

---

## DC4 execution/evidence — 2026-10-06

Accepted main:

`0ce316009eb6223d05756f175f388869ae8debd8` (merged PR #163).

Current operation: Issue #164, branch `feat/dc4-corpus-readiness`.

Read first:

- `AGENTS.md`;
- `state/current-focus.md`;
- `docs/family-food/dc4-corpus-readiness-contract.md`;
- `scripts/audit_dc4_corpus_readiness.py`.

The first execution slice adds a reproducible audit harness, tests and dedicated
CI. It must discover the full active catalogue dynamically and keep it separate
from the accepted 51-row Planner-eligible exact-energy baseline.

Durable evidence is now available:

- `data/curation/dc4-corpus-readiness/summary.json`;
- `docs/family-food/dc4-corpus-readiness-report.md`.

Observed DC4 = BLOCKED:

- active catalogue 51, 7 Russian-step readiness violations;
- Planner eligible exact-energy 51 / 17+33+1, PASS;
- fixtures 1 and 2 SUCCESS;
- fixture 3 produces complete pure Planner week but fails persisted
  MealPlan member-role/order validation;
- hard exclusions respected in selected pure Planner events;
- bounded MILK_2_5 + EGG failure has no partial plan.

Audit receipt: GitHub Actions #37569620771, exact audited head
`bc6c91b779fdd4c5d5c01b97e947a37ef049ca90`; focused 2 passed and
audit step SUCCESS, Ruff style corrected in later branch commits.

Do not repair these blockers inside DC4. They require independently scoped
corrections, re-audit and separate Gate1-CLOSE. PR9 remains NOT STARTED.

---

## DC4 Contract Gate — 2026-10-06

Accepted main:

`d3fc30d7eb677d3dc7aec8f6cb219fffa22762e4`
(merged PR #161).

Current operation: Issue #162, DC4 corpus readiness audit + Gate1 consumption
contract.

Read first:

- `AGENTS.md`;
- `state/current-focus.md`;
- `docs/family-food/master-roadmap.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- `docs/family-food/data-corpus-v1.md`;
- `docs/family-food/dc4-corpus-readiness-contract.md`.

Current branch:

`docs/dc4-gate1-consumption-contract`.

This PR is docs/state plus one verification-only R3-D runtime workflow
compatibility correction. The workflow still executes its focused runtime and
invariant checks; only the historical changed-path restriction is skipped for
downstream PR bases, matching the already accepted R3-D gate pattern.

It must be independently reviewed and merged before DC4 execution begins.

After merge, the next bounded operation is a separate DC4 execution/evidence PR.
That execution must dynamically enumerate every active current production
RecipeVersion for corpus-wide audit, and separately reconcile the
Planner-eligible exact-energy subset to 51 (17 breakfast / 33 MAIN / 1 sandwich).
It may audit/test Gate1 fixtures but may not
silently publish new FoodIngredient/RecipeVersion/Nutrition authority, change
Planner rules, consume migration 0043 or start PR9.

Required sequence:

`DC4 execution → Gate1-CLOSE → PR9 Shopping Engine`.

---

## Post-R3-D reconciliation — 2026-10-05

Accepted main:

`bbab6a0899c74f995c988455fe57d8d1f63d79af`
(merged PR #160 — R3-D final DC3 runtime).

DATA-CORPUS-V1 / DC3 is COMPLETE.

Current repository truth:

- 51 active exact-energy RecipeVersions;
- 17 breakfast / 33 MAIN / 1 sandwich;
- MAIN: beef 14 / fish 9 / chicken 4 / meat-free 6;
- exact-beef unaffected MAIN 19 / capacity 57;
- hard exact `MILK_2_5` breakfast unaffected set 3 / capacity 9;
- migration head 0042 / no 0043;
- AI disabled;
- R3-D changed catalogue truth, not Planner algorithm or runtime architecture.

Read before continuation:

- `AGENTS.md`;
- `state/current-focus.md`;
- `docs/family-food/master-roadmap.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-19-data-corpus.md`;
- `docs/family-food/data-corpus-v1.md`;
- relevant Gate1/Planner contracts.

Next bounded product operation after this reconciliation is reviewed/merged:

**DC4 — corpus readiness audit + Gate1 consumption.**

DC4 must consume ordinary accepted production catalogue truth. It must not
silently become R3-E/R3-F or introduce gate-only authoritative data.

After successful DC4 evidence:

`Gate1-CLOSE → PR9 Shopping Engine`.

Do not start PR9, Prep/PDF/PWA, Retail, AI or shared-deployment work early.

---

## R3-D final DC3 runtime — corrected review-ready — 2026-10-05

Accepted main:
`a6c1a0bd203e0ec21fd73eb4107282c2b144ff9a` (merged PR #158).

Issue #159 / PR #160 / branch `feat/r3d-final-dc3-batch-runtime`.

Corrected runtime/test freeze + broad verification:
`50934bca489e4c87204b56032dde6a4d0d3d1862`.

Read first:

- `docs/family-food/r3d-final-dc3-batch-gate.md`;
- `data/curation/r3d-final-dc3-batch-gate/frozen-batch.json`;
- `backend/app/seed/r3d_final_dc3_batch.py`;
- `backend/app/tests/test_r3d_final_dc3_batch.py`.

Independent-review correction:

- immutable RecipeVersion `change_note` now stores
  `review_contract_sha256=<hash>`;
- the hash covers exact frozen ingredients + `process_binding` + intermediates
  + alternatives + branch selection + household/medical context + prepared authority;
- changing only process-binding `status` or `rule` changes the hash (adversarial proof);
- prior misleading `source_partition_sha256` marker is no longer used.

All previous runtime semantics and catalogue result remain unchanged:

- 10 identity-only foods / no Nutrition-Vector-Composition authority;
- 10 MAIN RecipeVersions;
- 51 exact-energy / 33 MAIN;
- beef 14 / fish 9 / chicken 4 / meat-free 6;
- exact-beef unaffected 19 / capacity 57;
- hard MILK breakfast closure 3 / capacity 9;
- per-recipe atomic/resumable publication;
- batch one-UoW activation / replay / mixed-state / rollback.

Exact corrected freeze verification is fully green:

- R3-D #37281889334 — SUCCESS, **25 passed**;
- Gate #37281889429 / Docs #37281889396 / DC1 #37281889497 — SUCCESS;
- affected R1/R2/R3 workflows — SUCCESS;
- Nutrient registry #37281889714 — SUCCESS including backend/launcher;
- Partial nutrition #37281889327 — SUCCESS including backend/launcher.

Status: `READY_FOR_FINAL_REVIEW`.

After merge:
`post-runtime reconciliation → DC4`.

Do not merge autonomously. Do not create R3-E/R3-F.

---



## R3-D final DC3 Contract Gate — review-ready — 2026-10-04

Accepted main:
`1c82f34b960621aed3e1c43780270f8048edfe0f` (merged PR #156).

Issue #157 / PR #158 / branch `docs/r3d-final-dc3-batch-gate`.
Preflight is complete; PR #158 is open for independent review.

Read first:

- `docs/family-food/r3d-final-dc3-batch-gate.md`;
- `data/curation/r3d-final-dc3-batch-gate/frozen-batch.json`;
- `data/curation/r3d-final-dc3-batch-gate/candidate-audit.json`;
- `data/curation/r3d-final-dc3-batch-gate/source-verification.json`;
- `scripts/validate_r3d_final_dc3_gate.py`.

Preflight-frozen batch = 10 MAIN from retained MR 2.4.0162-19:

- 6 meat-free;
- 2 chicken;
- 2 beef;
- 0 fish.

Projected post-runtime = 51 usable exact-energy recipes / 33 MAIN.

Milk-free breakfast remains a known limitation (3 unaffected / capacity 9)
because no new candidate survives current source/process review.

Ten new FoodIngredient identities are identity-only; do not grant
NutritionProfile/NutrientVector/Composition authority.

Reviewer focus:

- whether four hot soups are truthful `main` candidates under current coarse
  MealType taxonomy and realistic Serving behavior;
- exact source mapping for MR 12+ rows;
- identity exactness (3.2% milk, first-grade flour, Dutch cheese, 72% butter);
- no hidden sub-recipe/intermediate truth;
- projected 51 means “eligible for DC4 audit”, not “DC4 passed”.

Pre-PR verification:
- exact review-ready branch run #37213223139 on `3a66e892a340274fc1bf86b601f98364f8e090b9` — SUCCESS;
- 10/10 committed MR source cards / output / energy rows — PASS;
- repo-derived 41 current / 51 projected — PASS;
- Ruff/format/scope/Markdown — PASS;
- independently materialized School2022 ZIP/PDF hashes and breakfast blocker
  replay — PASS.

After successful R3-D runtime + post-runtime reconciliation, next planned
operation is DC4. Do not create R3-E/R3-F for catalogue aesthetics.

Independent-review corrections now frozen:

- every selected recipe has REVIEWED_PASS household applicability,
  specialized_medical_scope=false, rationale and quarantined source context;
- soups remain current-coarse-taxonomy MAIN, with Serving feasibility deferred
  explicitly to DC4;
- MR 2.15 / 2.9 dietetic collection provenance does not become a therapeutic claim;
- every selected recipe freezes PREPARED_OUTPUT_V1 /
  RECIPE_PREPARED_OUTPUT_NUTRITION_V1 with exact ENERGY_KCAL only;
- all other frozen nutrient codes remain UNKNOWN; publication requires inactive Recipe;
- tested correction revision: `ae8418bac52a9d4459a26f16b6ada607f654241a`;
- R3-D #37224055581 / Docs #37224055575 / DC1 #37224055565 — SUCCESS.

Source completeness correction:

- every selected MR 12+ source row must be covered exactly once by
  RecipeIngredient / source_intermediate / explicit not-selected alternative;
- exact card-specific source URLs are pinned and validated 10/10;
- source intermediate labels are literal retained-source text; semantics are
  stored separately;
- MR 2.11 uses exact `варка крупным куском — 50`,
  semantic_role=`COOKED_MEAT_INTERMEDIATE`;
- branch selections bind to exact source row labels/quantities;
- tested completeness revision:
  `48fdfb3743e4a9c23ec022c7073dc8eeb489ced7`;
- R3-D #37229372543 / Docs #37229372530 / DC1 #37229372415 — SUCCESS.

Status: `READY_FOR_INDEPENDENT_REVIEW`.

---


## R3-C runtime — review-ready — 2026-10-04

Accepted main:
`3c5740b319e453715c5a58f5b65e6d216b7c4fdb` (merged PR #154).

Issue #155 / PR #156 / branch `feat/r3c-school2022-main-batch-runtime`.

Runtime freeze:
`c9e985eaad876fbc66519488d995d6e65975308a`.

Read first:

- `docs/family-food/r3c-post-r3b-catalogue-gate.md`;
- `data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json`;
- `backend/app/seed/r3c_school2022_main_batch.py`;
- `backend/app/tests/test_r3c_school2022_main_batch.py`.

Delivered exactly eight frozen MAIN RecipeVersions and exactly one identity-only
`ATLANTIC_SALMON_FILLET_RAW`. Reused R3-A/R3-B option B without shared-service,
schema, migration, Planner or Nutrition-authority changes.

Post-runtime projected truth verified in tests:

- 41 exact-energy recipes;
- 23 MAIN;
- 17 breakfast;
- 1 sandwich;
- hard MILK_2_5 breakfast proof unchanged at capacity 9;
- exact beef: 12/23 MAIN dependent, 11 unaffected / capacity 33;
- gap-to-50 = 9;
- DC4 remains blocked.

Exact runtime-freeze verification is all green, including dedicated R3-C
#37202224299 (22/22), R3-A/R3-B/R2-F regressions, and full backend/launcher
regression in Nutrient registry #37202224305 and Partial nutrition #37202224282.

Status: `READY_FOR_FINAL_REVIEW`.

Only state/PR metadata may change after the runtime freeze unless independent
review explicitly reopens runtime behavior. Do not merge autonomously. After
merge, reassess DC3 catalogue coverage before another batch or DC4.

---


## R3-C Contract Gate — merged historical — 2026-10-04

Merged as PR #154 at:
`3c5740b319e453715c5a58f5b65e6d216b7c4fdb`.

Issue #153 / PR #154 / branch `docs/r3c-post-r3b-catalogue-gate`.

Read first:

- `docs/family-food/r3c-post-r3b-catalogue-gate.md`;
- `data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json`;
- `data/curation/r3c-post-r3b-catalogue-gate/summary.json`.

Exact future batch: eight MAIN RecipeVersions. The only new identity is
`ATLANTIC_SALMON_FILLET_RAW`, identity-only.

Preserve R3-A/R3-B Option B and hard MILK_2_5 breakfast proof. No 0043,
schema, Planner or new Nutrition authority.

Projected exact-energy count after future runtime: 41; DC4 remains blocked.

Verification reproduction:

- `python scripts/validate_r3c_post_r3b_gate.py --repo-only --json`;
- full retained-source validation uses `--source-archive "$R3C_SOURCE_ARCHIVE"`;
- retained receipt: `data/curation/r3c-post-r3b-catalogue-gate/verification.json`.

Repo-derived validator facts:

- accepted current reuse food-code universe = 210;
- current exact-energy set derived from merged runtime seeds/specs = 33;
- derived meal split = 17 breakfast / 15 main / 1 sandwich;
- current Planner BREAKFAST compatibility yields 18 candidates;
- MILK_2_5 = 15 dependent, 3 unaffected, capacity 9;
- BEEF_CATEGORY_1_RAW = 7/15 MAIN, 8 unaffected, capacity 24.

Final status: `MERGED`; both independent-review verification blockers were
corrected before merge. Frozen eight-recipe content remained unchanged.

Runtime continuation is PR #156 / Issue #155 above. DC4/Gate1-CLOSE/PR9 remain
blocked until post-runtime DC3 reassessment.

---

## R3-B runtime — review-ready — 2026-10-04

Accepted main:
`dcc5f37f57a83283e4dee0d3c2957ed0704e9a46` (merged PR #150).

Issue #151 / branch `feat/r3b-school2022-breakfast-batch-runtime` / PR #152.

Runtime freeze:
`bf4580684140b00404bc91d16b8c7fcda016acb4`.

Delivered one runtime PR for exactly ten BREAKFAST RecipeVersions and exactly
three identity-only FoodIngredients.

Reused option B:

- per-recipe atomic inactive publication;
- partial exact inactive subset allowed after failure;
- rerun converges missing rows with exact rows zero-write;
- activation waits for all ten exact publications;
- all-inactive activation uses one batch UoW / one commit;
- all-active replay is zero-write;
- mixed active/inactive fails closed;
- activation failure rolls back all staged writes.

Source/product invariants preserved:

- Russian-only consumer Recipe Steps;
- omelet oven branch selected; steam branch provenance-only;
- hard `MILK_2_5` rejects all ten R3-B recipes;
- unaffected breakfast set remains exactly egg + cottage casserole + cheese
  sandwich, capacity 9, seven-breakfast authoritative generation succeeds;
- deliberate deactivation in the prior R3-A batch is preserved.

Verification on runtime freeze:

- R3-B #8 SUCCESS — 114 passed, Ruff/format/scope PASS;
- Docs #892 / DC1 #749 SUCCESS;
- R1-C #149 / R2 #133 / R2-B #123 / R2-C #111 / R2-E #94 /
  R2-F #66 / R3-A #32 SUCCESS;
- Russian methodologies #482 SUCCESS;
- Nutrient registry #949 SUCCESS including full backend/launcher regression;
- Partial nutrition #704 SUCCESS including full backend/launcher regression;
- migration remains 0042; AI disabled.

Status: `READY_FOR_FINAL_REVIEW`.

Only state/PR metadata may change after this freeze unless runtime verification is
explicitly reopened. Do not merge autonomously or start R3-C/DC4.

## R3-B breakfast Contract Gate — active — 2026-10-04

Accepted main:
`69c68f4153b25ac4e51cbe9ff54fb080201f08bd` (merged PR #148).

Issue #149 / branch `docs/r3b-school2022-breakfast-batch-gate`.

Read first:
`docs/family-food/r3b-school2022-breakfast-batch-gate.md`.

Exact batch: ten School2022 BREAKFAST cards
`54-2о/3о/4о/2т/1к/2к/6к/16к/23к/24к`.

New identity-only foods:
`CHEESE_SEMI_HARD_UNSPECIFIED`, `CORN_GROATS`, `MILLET_GROATS`.

Adversarial process audit removed `54-3т` / `54-21к` for unplaced quantified sugar and keeps `54-22к` deferred for unplaced quantified butter. Replacements are `54-2к` / `54-24к`.

Source archive/PDF independently re-hashed 2026-10-04 and match the accepted
School2022 receipt.

Future runtime must reuse merged R3-A option B in one PR. No migration/schema/
Planner/new-authority change.

Content freeze: `f72c7c51d6758dcb11573ab88e49d51272d80e73`.

Verification: cross-file/source/process audit PASS; Docs #876 SUCCESS; DC1 #733 SUCCESS.

Status: `READY_FOR_FINAL_REVIEW`.

Review corrections applied: Russian-only consumer steps for `54-23к/54-24к`; explicit oven-vs-steam branch selection for `54-2о/3о/4о`; mandatory hard `MILK_2_5` exclusion proof for all ten future runtime candidates.

Corrected content freeze: `6d043ba23e73a3373de95a22dd6fa226db35e8a3`.

Correction audit PASS. Docs #883 SUCCESS. DC1 #740 SUCCESS.

Do not start runtime before independent review and merge of PR #150.

## R3-A runtime — review-ready — 2026-10-04

Accepted main:
`e152b357528bb000cf5cf16e792a0d31b983f117` (merged PR #146).

Issue #147 / branch `feat/r3a-school2022-main-batch-runtime` / PR #148.

Runtime freeze:
`6887b58e2331c1324a8269c4f8778a4ef3a0b143`.

Delivered one runtime PR for exactly ten MAIN RecipeVersions and exactly three
identity-only FoodIngredients.

Option B is implemented:

- per-recipe atomic inactive publication;
- partial exact inactive subset allowed after failure;
- rerun converges missing rows with exact rows zero-write;
- activation waits for all ten exact publications;
- all-inactive activation uses one batch UoW / one commit;
- all-active replay is zero-write;
- mixed active/inactive fails closed;
- activation failure rolls back all staged writes;
- existing single-recipe activation remains regression-safe.

Source corrections preserved: 54-8м pre-soak liquid UNKNOWN; 54-11м exact
5–10 minute weak boil + 160 °C / 30–40 minute covered oven finish.

Verification on runtime freeze:

- R3-A #13 SUCCESS — 95 passed, Ruff/format/scope PASS;
- Docs #873 / DC1 #730 SUCCESS;
- R1-D #90 / R1-F #85 / R1-H #30 / R1-C #130 SUCCESS;
- R2 #114 / R2-B #104 / R2-C #92 / R2-E #75 / R2-F #47 SUCCESS;
- Russian methodologies #473 SUCCESS;
- Nutrient registry #929 SUCCESS including full backend/launcher regression;
- Partial nutrition #685 SUCCESS including full backend/launcher regression;
- migration remains 0042; AI disabled.

Status: `READY_FOR_FINAL_REVIEW`.

Only state/PR metadata may change after this freeze unless runtime verification is
explicitly reopened. Do not merge autonomously or start the next batch/DC4.

## R2-F cheese-sandwich runtime — active — 2026-10-03

Accepted base:
`2e4278cb06c2f683d1113434d04396c723409003`.

Issue #141 / branch `feat/r2f-cheese-sandwich-runtime`.

Read first:

`docs/family-food/r2f-sandwich-resilience-gate.md`.

Implement exactly:

`SAD28_SANDWICH_CHEESE_20_10`.

Retained source:
`data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`,
1783 bytes,
SHA-256
`77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`.

Create only:
`WHEAT_BREAD_PLAIN`, `CHEESE_UNSPECIFIED`,
identity-only with no Nutrition/Composition.

Prepared authority:
`ENERGY_KCAL=83`; other 53 frozen nutrient codes UNKNOWN.

Required Planner proof:
hard exact `MILK_2_5` leaves egg + cottage casserole + cheese sandwich and a
persisted seven-BREAKFAST week succeeds under repetition=3.

No migration 0043, schema change, Planner mapping/scoring/repetition change,
butter publication or new Nutrition authority.

After this PR is reviewed/merged, reassess corpus readiness and switch future DC3
work to larger R3 batches (~10–12 recipes initially). Do not start that batch
while #141 is still under review.

Runtime freeze:
`a84395cfff2923881f78048b976f358333726419`.

Exact runtime verification: R2-F #4 SUCCESS, 169 focused/affected tests passed,
Ruff check/format and scope/whitespace SUCCESS. Docs #830, DC1 #687, R1-C #87,
R2 #71, R2-B #61, R2-C #49 and R2-E #32 are SUCCESS on the same head.

Status:
`READY_FOR_FINAL_REVIEW`.

## R2-F cheese-sandwich Contract Gate — provenance correction — 2026-10-03

Accepted main:
`561c13aad6ce978de399dfd807071232af06b71c`.

Issue #139 / branch `docs/r2f-sandwich-resilience-gate`.

Read first:
`docs/family-food/r2f-sandwich-resilience-gate.md`.

Selected runtime candidate:
`SAD28_SANDWICH_CHEESE_20_10`.

Do not publish the rejected butter candidate.

Future RecipeVersion source document:

`data/curation/r2f-sandwich-resilience/raw-cheese-card.txt`

SHA-256 `77bc74917305adb0d4fee7a54910c9675068b1ec093a051f7c58bd34cc7dd27c`, 1783 bytes.

Durable Library:
`library:/FamilyFoodOS/source-artifacts/sad28-cheese-card-raw-text-2026-10-03.txt`
Library file id: `libfile_baff1ee2870081918170b98d1cec3c5d`.

Library materialize/readback verification is PASS.

Provenance roles:

- SAD28 = official host only;
- card issuer = `NOT_ESTABLISHED_FROM_RETAINED_CARD`;
- upstream collection = Kutkina 2008.

Do not replace the raw-card source with live web/PDF data. The upstream PDF is
corroboration/discovery only. Future source-family expansion requires reacquisition
and a new review.

Projected hard exact-`MILK_2_5` capacity remains 9/week.

Verified content freeze:
`2f2deaff731a07c1937e44059106f8bfcc2f4778`.

Docs #824 / DC1 #681 are SUCCESS. Raw-card Git/Library hashes, provenance role
separation, source tuple coherence, derivative/card hashes, butter rejection and
capacity 9 all pass.

Status:
`READY_FOR_FINAL_REVIEW`.

## R2-E cottage casserole runtime review-ready — 2026-10-03

Accepted main:
`ea30ae82a253ee712d211b3b19caf53e9d2ccc45` (merged PR #136).

Issue #137 / branch `feat/r2e-cottage-casserole-runtime`.

Read first:
`docs/family-food/r2e-cottage-casserole-gate.md`.

Implement exactly one runtime candidate:
`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE`.

Four identity-only FoodIngredients are allowed and must remain without
Nutrition/Composition:
`TVOROG_5`, `SEMOLINA_GROATS`, `SOUR_CREAM_15`, `VANILLIN`.

Prepared Nutrition is ENERGY_KCAL-only at exact 301.2; all other frozen nutrient
codes remain UNKNOWN. Menu 301.3 is not authority.

Fresh publication must be atomic at RecipeVersion + prepared authority; activation
uses the existing guarded boundary. Replay is zero-write and deliberate
deactivation must remain deactivated.

The hard `MILK_2_5` proof must demonstrate two unaffected candidates and
capacity 6/week, therefore bounded seven-breakfast failure with no partial plan.
Do not claim 7/7 closure.

Delivered runtime:

- `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` active at 150 g / 301.2 kcal;
- four identity-only foods remain without Nutrition/Composition;
- exact prepared replay is zero-write; deliberate deactivation stays deactivated;
- failure/tamper/conflict/partial-state paths fail closed;
- ordinary BREAKFAST pool becomes 7/capacity 21;
- hard `MILK_2_5` unaffected pool becomes exactly two/capacity 6, and the
  seven-BREAKFAST proof fails with no partial persisted plan.

Runtime freeze:
`fc75f5dcbc4e5e640b64cb37028f3f599b0df8f6`.

R2-E workflow #4 SUCCESS: 152 focused/affected tests, Ruff check/format,
scope/whitespace. Docs #802, DC1 #659, R1-C #59, R2 #43, R2-B #33, R2-C #21 and
Russian methodologies #452 are SUCCESS. Migration remains 0042; AI disabled.

PR #138 is READY FOR FINAL REVIEW.

Do not merge autonomously. Do not start the next resilience candidate before
review and merge.

## R2-E 54-1т Contract Gate review-ready — 2026-10-03

Accepted main:
`99a579e35b0a0fa6d09947b80ffecb222a45bf96` (merged PR #134).

Issue #135 / branch `docs/r2e-cottage-casserole-gate`.

Frozen future runtime candidate:
`SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` — School2022 54-1т — Запеканка из творога —
150 g / exact same-card 301.2 kcal.

Four new identity-only foods are required:
`TVOROG_5`, `SEMOLINA_GROATS`, `SOUR_CREAM_15`, `VANILLIN`.
Six existing exact identities are reused. No Nutrition/Composition is published
for the new identities.

Household applicability is reviewed PASS; source quantities/Nutrition remain
School2022 authority, while independent household recipes only corroborate that
the core oven-baking method is ordinary domestic cooking.

Do not use 54-7т as an ordinary shortcut: its source explicitly marks it for
children with celiac disease and current MVP wellness scope excludes therapeutic
diet admission.

This is docs/data only.

Evidence head:
`444651459e64b9699a034fb4c67d95a45b98b464`.

Pinned source/variant/process/10 ingredient-demand hashes PASS; medical-scope
54-7т hash PASS; evidence JSON PASS; Docs #795 SUCCESS; DC1 #652 SUCCESS.

PR #136 is READY FOR FINAL REVIEW. Runtime implementation requires independent
review and merge of this gate.


## R2-D milk-exclusion breakfast resilience Contract Gate — 2026-10-03

Accepted main:
`463fe46f7c40156c1b8ebab5402ca45698d8c2bc` (merged PR #132).

Issue #133 / branch `docs/r2d-milk-exclusion-breakfast-gate`.

The current product hole is not generic BREAKFAST capacity. It is hard-exclusion
resilience: five of six active exact-energy BREAKFAST recipes require
`MILK_2_5`; excluding it leaves one candidate and capacity 3/week.

The nearest retained candidates were audited before runtime:

- 54-1т exact same-card prepared energy is ready at 301.2 kcal / 150 g;
  the 301.3 kcal menu row is QA-only. Runtime publication still requires exact
  FoodIngredient/form and household-applicability review;
- 54-4т and 54-6т are blocked because required process water for vanillin is not
  quantified;
- USSR82-459 remains production-reconciliation-required and its secondary
  prepared nutrient row fails energy QA.

Durable source archive:
`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`
SHA-256
`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

R2-D is a docs/data Contract Gate only. No runtime/data publication is authorized.

Independent final review found one contract blocker in the 54-1т authority
interpretation. It has been corrected to the accepted same-card
`PREPARED_OUTPUT_V1` rule.

Correction evidence head:
`21d768b243de4064292065ba10f36b9b5c900e54`.

Docs #793 SUCCESS; DC1 #650 SUCCESS; corrected evidence JSON parses; no
runtime/schema/migration diff.

PR #134 is READY FOR FINAL REVIEW.

After independent review/merge, separately decide whether to close the School2022
evidence gaps or investigate a clean BREAKFAST/SANDWICH source family. Do not
start either automatically.

## R2-C breakfast grain diversity final handoff — 2026-10-03

Accepted base:
`13a81d2497737f3b275b10055cd084548be02bf3`.

Issue #131 / PR #132 / branch `feat/r2c-breakfast-grain-diversity`.

Proof/runtime freeze:
`5dc3bda151d412662f75e7cd64ae7f1811bb25c7`.

Published and activated:

- `SCHOOL2022_54_13K_WHEAT_MILK_PORRIDGE` — 200 g / 270.3 kcal;
- `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE` — 200 g / 187.3 kcal;
- `SCHOOL2022_54_25_1K_RICE_MILK_PORRIDGE` — 200 g / 184.5 kcal.

New identity-only food:
`WHEAT_GROATS`.

Existing exact identities cover buckwheat groats, reviewed rice groats, milk 2.5%,
butter, sugar, iodized salt and water. No Nutrition/Composition is published for
the new wheat-groats identity.

The recipes reuse PREPARED_OUTPUT_V1. ENERGY_KCAL is the sole AVAILABLE nutrient;
all other frozen codes stay UNKNOWN.

Ordinary active exact-energy BREAKFAST count is now 6 and capacity is 18/week
under unchanged repetition=3. A persisted seven-BREAKFAST week selects all three
new preferred recipes. Excluding `WHEAT_GROATS` removes only wheat porridge and
the week still succeeds.

Replay/failure semantics:
exact replay is zero-write; deliberate deactivation stays deactivated; frozen
contract tamper, partial Recipe/prepared state and conflicting wheat identity all
fail closed.

Source/consumer boundary:
institutional serving-temperature rules remain provenance-only. Source process
ranges remain explicit RecipeStep text and do not become invented scalar
cook-time values. Exact rice source amount text keeps the comma form `30,8`.

Exact proof/runtime-freeze verification:
136 passed; Ruff check/format SUCCESS; scope/whitespace SUCCESS; AI disabled;
migration head remains 0042.

PR #132 is READY FOR FINAL REVIEW.

Do not merge autonomously. After merge, reassess the next R2/R3 batch. Do not
start DC4/Gate1-CLOSE or PR9 automatically.

## R2-C breakfast grain diversity active — 2026-10-03

Accepted main:
`13a81d2497737f3b275b10055cd084548be02bf3`.

Issue #131 / branch `feat/r2c-breakfast-grain-diversity`.

Current batch:
- School2022 54-13к / wheat milk porridge / 200 g / 270.3 kcal;
- School2022 54-20к / buckwheat milk porridge / 200 g / 187.3 kcal;
- School2022 54-25.1к / rice milk porridge / 200 g / 184.5 kcal.

Only one new identity-only food is introduced:
`WHEAT_GROATS`.

Existing exact identities cover buckwheat groats, reviewed rice groats, milk 2.5%,
butter, sugar, iodized salt and water.

Prepared Nutrition remains ENERGY_KCAL-only PREPARED_OUTPUT_V1.

Institutional serving-temperature context is quarantined. No scalar cook-time is
invented from source ranges.

Next:
run focused R2-C CI, correct only task-local failures, freeze exact
runtime/evidence head and update state with the verification receipt.

Do not start another corpus batch, DC4/Gate1-CLOSE or PR9 before review/merge.

## R2-B fish MAIN diversity final handoff — 2026-10-02

Accepted base:
`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Issue #129 / PR #130 / branch `feat/r2b-fish-main-diversity`.

Proof/runtime freeze:
`4fd0c946b43785c0eb242d26184c7a20441a6012`.

Published and activated:

- `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK` — 80 g / 144.8 kcal;
- `SCHOOL2022_54_7R_POLLOCK_IN_MILK` — 80 g / 105.3 kcal.

New identity-only fish foods:
`PINK_SALMON_FILLET_RAW`, `POLLOCK_FILLET_RAW`.

No Nutrition/Composition is published for those identities.

The recipes reuse PREPARED_OUTPUT_V1. ENERGY_KCAL is the sole AVAILABLE nutrient;
all other frozen codes stay UNKNOWN.

Ordinary active exact-energy MAIN count is now 5 and capacity is 15/week under
unchanged repetition=3. A persisted seven-DINNER week selects both preferred fish
recipes. Excluding pink-salmon fillet removes only that candidate and the week
still succeeds through the remaining MAIN pool.

Replay/failure semantics:
exact replay is zero-write; deliberate deactivation stays deactivated; source
tamper, partial Recipe/prepared state and conflicting fish identity all fail
closed.

Source/consumer boundary:
the exact route hash is retained, but thawing logistics, paraconvection and
institutional serving-temperature rules are provenance-only. Consumer steps start
with already-thawed fillet.

Cod cutlet 54-1р remains deferred because its exact source does not establish the
narrower high-grade/stale wheat-bread form proposed in older R1-G evidence.

Independent audit correction:
- source range 20–25 min is no longer collapsed into `cook_time_minutes=25`;
  the scalar field stays null and the Russian step preserves the range;
- consumer Russian text now uses the grammatical `филе горбуши / филе минтая`;
- regression assertions lock both facts.

Exact corrected proof/runtime-freeze verification:
128 passed; Ruff check/format SUCCESS; scope/whitespace SUCCESS; AI disabled;
migration head remains 0042.

PR #130 is READY FOR FINAL REVIEW.

Do not merge autonomously. After merge, reassess the next R2/R3 batch. Do not
start DC4/Gate1-CLOSE or PR9 automatically.

## R2-B fish MAIN diversity active — 2026-10-02

Accepted main:
`1e4a0e137dee87f2aaef7d885481fef17f6e324c`.

Issue #129 / branch `feat/r2b-fish-main-diversity`.

Current batch:
- School2022 54-6р / pink salmon in milk / 80 g / 144.8 kcal;
- School2022 54-7р / pollock in milk / 80 g / 105.3 kcal.

Only two new identity-only FoodIngredients are introduced:
`PINK_SALMON_FILLET_RAW` and `POLLOCK_FILLET_RAW`.

Existing exact identities cover milk 2.5%, onion, sunflower oil and iodized salt.
Prepared Nutrition remains ENERGY_KCAL-only PREPARED_OUTPUT_V1.

Consumer RecipeSteps intentionally omit source thawing logistics, paraconvection
and institutional serving-temperature requirements. The selected source route is
retained only for deterministic provenance.

Cod cutlet 54-1р is deferred because its exact retained bread form does not support
the narrower high-grade/stale identity proposed in older R1-G evidence.

Next:
run focused R2-B CI, fix only task-local failures, freeze exact runtime/evidence
head and update state with the verification receipt.

Do not start another corpus batch, DC4/Gate1-CLOSE or PR9 before review/merge.

## R2 breakfast capacity final handoff — 2026-10-02

Accepted base:
`8995e85e4cda2ae30fc62fdc63daaf441f4226bd`.

Issue #127 / PR #128 / branch `feat/r2-breakfast-capacity`.

Proof/runtime freeze:
`1d93631b07a25a260b7d45cc0b91f3437865fd8a`.

R2 selection follows Issue #99's maximum-marginal-capacity rule. BREAKFAST was
the bottleneck at one active exact-energy RecipeVersion; MAIN already had three.

Published and activated:

- School2022 54-1о / natural omelet / 150 g / 225.5 kcal;
- School2022 54-9к / viscous milk oat porridge / 200 g / 272.9 kcal.

New identity-only foods:

- `MILK_2_5` — exact 2.5% fat identity without invented heat-treatment subtype;
- `OAT_GROATS` — exact oat-groats identity, not `OATS_ROLLED`.

No Nutrition/Composition is published for those identities.

The new RecipeVersions reuse the R1-F/R1-H
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` seam. ENERGY_KCAL is
the sole AVAILABLE nutrient; the remaining frozen codes stay UNKNOWN.

The ordinary production Planner now has three active exact-energy BREAKFAST
candidates and proves a persisted seven-BREAKFAST week at repetition=3.

Failure semantics verified:
exact replay is zero-write, deliberate deactivation remains deactivated, frozen
artifact tamper fails, partial Recipe/prepared authority state fails, conflicting
FoodIngredient identity fails, and milk exclusion leaves no partial MealPlan.

Exact proof/runtime-freeze verification:
120 passed; Ruff check/format SUCCESS; scope/whitespace SUCCESS; AI disabled;
migration head remains 0042.

PR #128 is READY FOR FINAL REVIEW.

After merge, reassess the next R2/R3 batch. Do not start DC4/Gate1-CLOSE or PR9
automatically.

## R1-C final proof receipt — 2026-10-02

Accepted implementation base:

`5bf5127a238b8bb139903f008ad7c14b9b1309c7` (merged PR #125).

PR:

`#126 — R1-C: production persisted Planner proof`.

Proof freeze:

`2f643303308f3bb6b95d7161435474109ad91a34`.

R1-C uses the ordinary persisted application boundary end to end:

- persisted Household / HouseholdMember;
- persisted accepted CUSTOM MealPattern selection with exact v0.4 shares;
- active production RecipeVersions from R1-F/R1-H;
- current neutral Recipe Nutrition;
- `PlannerService.generate_authoritative(...)`;
- existing MealPlan / Serving persistence and revision history.

Proof result:

- complete seven-DINNER week persists successfully;
- all 3 MAIN candidates are used under repetition=3;
- Serving portions are positive and allocation-backed;
- replay has the same semantic week and trace fingerprint;
- BREAKFAST+DINNER is an explicit bounded infeasible pattern with no partial plan;
- hard FoodIngredient exclusion rejects the affected candidate and leaves
  unaffected candidates free of that exclusion code;
- persisted two-member exclusion/sharedness proof keeps six compatible dinner
  events shared, keeps meatballs available to the unaffected member, and never
  assigns meatballs to the excluded member;
- active exact-energy pool remains 1 BREAKFAST + 3 MAIN;
- migration head remains 0042;
- no Planner/runtime/schema/new-authority change;
- `AI_ENABLED=false`.

Verification at the proof freeze:

- R1-C focused/affected — 102 passed;
- Ruff check / format — SUCCESS;
- scope/whitespace — SUCCESS.

Independent review blocker closure:
the earlier one-member exclusion proof could not demonstrate preservation of
other members/sharedness. The corrected two-member persisted scenario proves
member-local exclusion plus preserved shared execution. No runtime/schema/Planner
or authority change was needed.

Earlier red attempts were task-local proof-fixture/hygiene issues only:
the unsupported `moderate` activity correctly failed closed at
`MISSING_REFERENCE_ENERGY`; the fixture now uses supported `active`, and
trace assertions use stable `applied_exclusions`/event participation semantics.

PR #126 is READY FOR FINAL REVIEW.

Do not merge autonomously. After explicit review and merge, do not start R2/R3
automatically; first reassess and authorize the next corpus-expansion operation.
DC4 / Gate1-CLOSE and PR9 remain later.

## R1-C authorized after merged R1-H — 2026-10-02

Accepted main:

`e50da0d21a6c740e5d60c257ac64de12e0c5d2b3` (merged PR #123).

R1-H production truth now provides:

- one active exact-energy breakfast RecipeVersion;
- three active exact-energy MAIN RecipeVersions;
- real seven-DINNER capacity under unchanged repetition=3;
- ordinary authoritative Planner loading;
- hard FoodIngredient exclusion behavior;
- no Planner algorithm/schema expansion.

This closes the minimum prerequisite in
`docs/family-food/r1c-production-planner-proof-prerequisite.md`.

Issue #124 is the next bounded operation:

`R1-C: production persisted Planner proof`.

R1-C must use materially different repository-backed accepted
Household/MealPattern scenarios and real RecipeVersion/Nutrition state, generate
and persist at least one complete seven-day week, persist individualized
Servings, prove deterministic replay, prove one atomic bounded infeasible case,
and prove hard FoodIngredient exclusion through the ordinary authoritative
Planner boundary.

Do not add migration 0043, publish additional food/recipe/nutrition authority,
change Planner scoring/repetition, weaken exclusions, or start DC4/Gate1-CLOSE,
PR9 Shopping, Prep/PDF/Retail/API/UI/Auth/PostgreSQL/AI or R2/R3.

If implementation discovers a new persisted contract or authority need, stop and
reopen the applicable Implementation Contract Gate.

Status:

`R1_C_AUTHORIZED_NOT_STARTED`.

After successful independent review and merge of R1-C, preserve the accepted
sequence: explicitly authorize the next R2/R3 corpus-expansion operation toward
the DATA-CORPUS-V1 baseline before DC4 / Gate1-CLOSE. Do not start R2/R3, DC4,
Gate1-CLOSE or PR9 automatically.

## R1-H final verification receipt — 2026-10-02

Accepted base:
`07af24cf1821bbb1ee9f70bdcc3311361d7b443b`.

Runtime freeze:
`c300118fd554829ddd9d6429c2abccba8dbb250b`.

Current PR #123 head after state/test-only finalization remains byte-identical for
all production runtime files.

Final verification is complete:

- R1-H runtime focused/affected: 135 passed;
- Ruff check / format: SUCCESS;
- Russian nutrition methodologies: SUCCESS;
- Docs verification: SUCCESS;
- DC1 corpus verification: SUCCESS;
- Nutrient registry V2: focused + backend shards 0/1/2/3 + launcher SUCCESS;
- Partial nutrition profiles: focused + backend shards 0/1/2/3 + launcher SUCCESS.

Delivered runtime truth:

- four identity-only FoodIngredients, without Nutrition/Composition authority;
- two exact School2022 MAIN RecipeVersions;
- 80 g / 153 kcal meatballs and 80 g / 185.6 kcal goulash;
- sparse prepared Nutrition with 1 AVAILABLE energy + 53 UNKNOWN codes;
- guarded activation;
- exact replay / conflict / partial / failure-injection coverage;
- real authoritative Planner loading and FoodIngredient exclusions;
- real seven-DINNER capacity under unchanged max repetition 3.

No migration/schema/Planner algorithm change exists.

PR #123 is READY FOR FINAL REVIEW.
Do not merge autonomously and do not start R1-C automatically.

## R1-H runtime freeze — 2026-10-02

Accepted base:
`07af24cf1821bbb1ee9f70bdcc3311361d7b443b` (merged PR #121).

Issue #122 / PR #123 / branch `feat/r1h-school2022-main-runtime`.

Runtime freeze:
`c300118fd554829ddd9d6429c2abccba8dbb250b`.

Delivered exactly the R1-G frozen batch:

- four identity-only FoodIngredients:
  `BEEF_CATEGORY_1_RAW`, `WHEAT_BREAD_HIGH_GRADE_STALE`,
  `SALT_IODIZED`, `TOMATO_PUREE_PASTE`;
- `SCHOOL2022_54_29M_BEEF_MEATBALLS` — 80 g / 153 kcal;
- `SCHOOL2022_54_2M_BEEF_GOULASH` — 80 g / 185.6 kcal.

No raw Nutrition/Composition was invented for the new identities.
Recipe + prepared authority fresh publication reuses the R1-F caller-owned UoW.
Activation reuses the R1-F guarded boundary. Replay is zero-write and deliberate
deactivation is preserved.

Focused receipt on the runtime freeze:
- 135 tests passed;
- Ruff check SUCCESS;
- Ruff format SUCCESS;
- Russian nutrition methodologies SUCCESS.

Ordinary authoritative Planner loading/exclusion is proven, and the existing
chicken + two new mains cover seven DINNER opportunities under max repetition 3.

This state commit is documentation-only. Runtime bytes after `c300118f...` must
remain unchanged while broad backend + launcher verification completes.

Do not merge autonomously. Do not start R1-C automatically.

## R1-G gate review-ready — 2026-10-01

Issue #120 / PR #121 now freeze the next runtime batch after merged PR #119.

Selected runtime Recipes:

- `SCHOOL2022_54_29M_BEEF_MEATBALLS` — School2022 54-29м — 80 g — exact 153 kcal;
- `SCHOOL2022_54_2M_BEEF_GOULASH` — School2022 54-2м — 80 g — exact 185.6 kcal.

Both passed the user-approved bounded per-recipe household-applicability review.
Institutional thaw/holding/serving rules remain source context and are not promoted
to consumer RecipeSteps.

Exact runtime provenance + Russian RecipeVersion seeds are frozen in
`data/curation/r1g-catalogue-capacity-expansion/prepared-publication-specs.json`.
Runtime must not choose alternative source/version/rights/step strings.

Prepared Nutrition reuses the proven R1-F seam:
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`.
Only ENERGY_KCAL is promoted; all other unreviewed codes remain UNKNOWN.

Future runtime identity-only publications:
- BEEF_CATEGORY_1_RAW;
- WHEAT_BREAD_HIGH_GRADE_STALE;
- SALT_IODIZED;
- TOMATO_PUREE_PASTE.

Existing identities reused:
- BUTTER_PEASANT_72_5_UNSALTED;
- WATER;
- ONION_BULB_FRESH;
- FLOUR_WHEAT_HIGH_GRADE.

Projected MAIN capacity becomes 3 active exact-energy RecipeVersions, supporting
up to 9 MAIN opportunities/week under the unchanged max repetition 3. This is
enough for a seven-opportunity MAIN-only R1-C success fixture in principle.

467/492/1081/208 remain blocked exactly as recorded; 364 remains promising but is
not in the first runtime batch. 54-1р is the immediate School2022 follow-up.

No runtime/schema/Planner change is in PR #121. Do not start the runtime PR until
#121 is reviewed and merged.

## R1-G research checkpoint — 2026-10-01

Issue #120 / draft PR #121 are active on
`docs/r1g-catalogue-capacity-expansion-gate`.

Important correction to the post-R1-F expectation: no candidate is yet fully
runtime-ready.

Verified durable private corpus archive:
- size 206692075 bytes;
- SHA-256 `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

Current dispositions:
- USSR82-467 — blocked: unquantified required salt;
- USSR82-492 — blocked: unquantified required salt;
- USSR82-1081 — blocked: discovered 150/10 / 370 kcal row is not exact-linked to
  the selected III branch;
- USSR82-208 — not R1-F V1 ready because 250 g prepared nutrition vs 1000 g source
  Recipe basis would require forbidden scaling;
- USSR82-364 — strongest retained USSR82 MAIN candidate, but needs exact
  III+margarine receipt and `Жир кулинарный` identity/form closure.

School2022:
- exact source PDF in the pinned archive independently verifies at
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- exact same-card output/kcal exists for many material-ready mains;
- leading shortlist is 54-29м / 54-2м / 54-1р;
- accepted R1-E truth still applies `HOUSEHOLD_APPLICABILITY` to 264 unpublished
  School2022 cards, and retained process evidence says
  domestic_applicability=unestablished for institutional rules.

Do not silently treat exact kcal as household publication readiness. A reviewed
per-recipe applicability decision/evidence path is required.

No runtime, migration, activation or Planner change has started.

## R1-G catalogue-capacity expansion gate started — 2026-10-01

PR #119 is merged into main at
`879d68087845dea09454089e822f5d8d8238d12d`.

Issue #120 now owns the next bounded operation:
`R1-G: catalogue-capacity expansion evidence and contract gate`.

Branch:
`docs/r1g-catalogue-capacity-expansion-gate`.

Initial evidence state:

- USSR82-1081: exact variant/output/ingredient quantities retained, but exact
  cooked prepared-output ENERGY_KCAL receipt is not yet proven; READY_RAW is not
  authority;
- USSR82-467: blocked on exact salt quantity;
- USSR82-492: blocked on exact salt quantity;
- current explicit historical MAIN alternatives 364/208 retain source/form
  blockers; broader cross-corpus MAIN ranking is required;
- no fixed number of additional Recipes is assumed for R1-C; capacity must be
  calculated from concrete repository-backed scenarios under the unchanged
  repetition limit.

R1-G is docs/data evidence only. No runtime, migration, publication, activation,
Planner change or R1-C execution is authorized.

## R1-F authoritative Planner acceptance closure — 2026-10-01

Runtime freeze remains:
`ac647a9fd0546876db743faf545d64ef2622c595`.

A final independent review found one acceptance-evidence gap: the R1-F ingredient
exclusion test manually constructed a PlannerCandidate instead of proving the
ordinary authoritative application boundary required by #118.

Closed on test-only head:
`2c35a0df7a6acafec09cbc107e12ac5e3e5a19a6`.

The R1-F test now:

- seeds the real pilot Recipes and prepared Nutrition authority;
- calls `PlannerService.compose_authoritative_request(...)`;
- lets the application service load active RecipeVersions, neutral Nutrition and
  RecipeIngredient identities itself;
- proves HARD_BOILED_EGG is loaded at exact 63 kcal and role-compatible;
- proves BOILED_CHICKEN_MAIN_PRODUCT is loaded at exact 167.7 kcal and role-compatible;
- applies EGG / CHICKEN_CATEGORY_2_RAW exclusions through
  `GenerationMemberConstraints`;
- proves the corresponding real candidate receives
  `MEMBER_EXCLUDED_INGREDIENT`;
- contains no manual PlannerCandidate construction.

Verification on that test-only head:

- R1-F focused/affected suite — 122 passed;
- Ruff check — SUCCESS;
- Ruff format --check — SUCCESS;
- Docs / DC1 / R1-D / Russian methodologies — SUCCESS.

No production/runtime bytes changed after the accepted runtime freeze, so the
already-green broad runtime receipt remains valid under verification-policy.md.
PR119 is READY FOR FINAL REVIEW. Do not merge autonomously.

## R1-F blocker closure final receipt — 2026-10-01

Runtime freeze:
`ac647a9fd0546876db743faf545d64ef2622c595`.

The final two review blockers are closed:

- `ReviewedPreparedRecipeNutritionSpec` now carries explicit
  `expected_unknown_codes`; validation requires AVAILABLE and UNKNOWN to be
  disjoint and together cover the frozen 54-code nutrient set;
- the pilot specs keep only ENERGY_KCAL AVAILABLE and explicitly keep the other
  53 codes UNKNOWN;
- an adversarial test proves an unreviewed PROTEIN value cannot be added while
  still declared UNKNOWN;
- `FoodRecipeCatalogueService` no longer exposes public unchecked
  `activate()`; the raw reversible mutation is internal and the public R1-F path
  remains `activate_prepared_recipe(...)`.

Exact runtime-head verification:

- R1-F runtime — SUCCESS; 122 tests passed;
- Ruff check / format — SUCCESS;
- Docs / DC1 / R1-D / Russian methodologies — SUCCESS;
- Partial nutrition profiles — focused + 4 backend shards + launcher SUCCESS;
- Nutrient registry V2 — focused + 4 backend shards + launcher SUCCESS.

No migration, Planner algorithm/scoring/role/repetition, historical Recipe truth,
Shopping/UI/Retail/Auth/PostgreSQL/AI scope, or 54/54 completeness requirement
was added.

PR119 is READY FOR FINAL REVIEW. Do not merge autonomously and do not start the
catalogue-expansion follow-up automatically.

## R1-F final-review corrections — 2026-10-01

User-authorized corrections to PR119 are implemented on runtime head
`6f7ea30c23cb8a16fd9863425026399439c371e8`.

Closed review blockers:

- canonical prepared Nutrition now materializes all 54 frozen nutrient codes;
- absent values remain explicit UNKNOWN; numeric zero remains AVAILABLE(0);
- PARTIAL nutrition is not an admission blocker when exact positive energy exists;
- R1-F activation uses a guarded application boundary that verifies exact prepared
  authority and Planner admission before flipping the reversible active flag;
- targeted adversarial coverage now proves rejection of wrong output/source/hash/
  rights, soft/medium egg, category-I chicken, 697/824 + 144 kcal, and
  missing/zero/negative ENERGY_KCAL.

Runtime verification at `6f7ea30...` proves R1-F runtime (120 focused tests +
Ruff check/format), Docs, DC1, R1-D admission, Russian methodologies, Partial
nutrition profiles with all backend shards + full launcher, and Nutrient registry
V2 focused + all backend shards. The Nutrient registry duplicate launcher was
cancelled only by a later state-only synchronize; its command is identical to the
full launcher regression that already passed on the same runtime bytes, so it is
not reported as a PASS and is not a separate runtime gate.

PR119 is READY FOR FINAL REVIEW. Do not merge autonomously and do not start
catalogue expansion automatically.

## R1-F runtime final handoff — 2026-10-01

PR119 runtime is frozen at:
`a20d13aacbd5222c696658fdde2cc4a0efbba075`.

All exact runtime-freeze CI is green:
R1-F runtime, Docs, DC1, R1-D admission, Russian methodologies,
Nutrient registry V2 and Partial nutrition profiles.

Production pilot truth on the branch:

- `HARD_BOILED_EGG` — breakfast — 40 g source output — exact 63 kcal —
  active — Planner eligible;
- `BOILED_CHICKEN_MAIN_PRODUCT` — main — 107 g category-II chicken input /
  75 g source output — exact 167.7 kcal — active — Planner eligible;
- `CHICKEN_CATEGORY_2_RAW` exists as identity-only FoodIngredient, with no
  invented raw Nutrition;
- `USSR82_697_BOILED_CHICKEN` remains historical/inactive;
- only ENERGY_KCAL is promoted for the prepared pilot; other unreviewed nutrient
  mappings stay UNKNOWN;
- prepared + Composition double authority fails closed;
- replay does not silently reactivate a deliberately deactivated Recipe.

Broad regression debt found/fixed during delivery was limited to strict tests
whose exact migration head/current-table inventory still stopped at 0041.

PR119 is READY FOR FINAL REVIEW. Do not merge autonomously.

After merge, do not jump to R2/R3. Continue R1 catalogue-capacity expansion and
R1-C only under the next explicit authorization.

## R1-F runtime implementation — 2026-09-30

Accepted main:
`e138d615802f7928946e419156f8c6905f04075b` (merged PR117).

Issue #118 / PR #119 / branch `feat/r1f-prepared-output-runtime`.

Implemented:

- migration 0042 prepared-output Recipe Nutrition persistence;
- immutable prepared header + sparse values;
- `PREPARED_OUTPUT_V1` neutral projection;
- fail-closed conflict with Composition authority;
- identity-only `CHICKEN_CATEGORY_2_RAW`;
- `HARD_BOILED_EGG` @ exact 63 kcal;
- `BOILED_CHICKEN_MAIN_PRODUCT` @ exact 167.7 kcal;
- explicit activation after exact-energy + admission proof;
- exact replay does not reactivate deliberate deactivation;
- historical USSR82-697 remains unchanged/inactive.

R1-F publishes ENERGY_KCAL only; unreviewed macro/carbohydrate mappings remain
UNKNOWN.

Focused runtime workflow is green on exact head
`9283a647e24c0c8c03b72005eb8255a07590a1b1`.

Broad exact-head workflows remain required before final review readiness.

Do not expand to 467/492/1081 or start R1-C until PR119 final review/merge.

## R1-F cooked-Nutrition authority gate — 2026-09-30

PR115 merged into main at:
`becc00f0e94c927598f930140c385f84f80aa21d`.

Issue #116 / branch `docs/r1f-cooked-nutrition-authority-gate` own the required
docs-only Implementation Contract Gate before any authoritative runtime change.

Selected contract direction:

- new RecipeVersion-level authority kind `PREPARED_OUTPUT_V1`;
- calculation version `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- migration 0042 with immutable prepared-authority header + sparse nutrient values;
- ENERGY_KCAL mandatory, unreviewed nutrients UNKNOWN;
- no double authority with Composition bindings;
- exact source artifact/hash required before publication.

Pilot evidence:

- 453: hard-boiled only; MR 2.4.0162-19 card 4.1 gives 40 g / 63 kcal;
- historical 697 v1 remains immutable/inactive;
- 1986 697/824 50/50 / 144 kcal is rejected as chicken + sauce;
- 1988 recipe 303 Variant III gives exact 155/107 → 75 g boiled chicken and
  167.7 kcal; it maps to a separate source-neutral Recipe
  `BOILED_CHICKEN_MAIN_PRODUCT` / `Курица отварная без гарнира`;
- historical `USSR82_697_BOILED_CHICKEN / Курица отварная` remains immutable/inactive;
- source receipts and rights are pinned in the gate, not deferred to runtime.

Runtime must not begin until this gate PR is reviewed and merged.

## R1-E corpus blocker clustering — 2026-09-30

Classification result:
547/547 retained identities preserved with evidence scope separated into known
blockers vs unproven later gates.

Reviewed first cooked-authority pilot:
USSR82-453 (breakfast) + USSR82-697 (main).

This replaces the earlier four-breakfast-first sequencing. The mixed pair is used
to decide the truthful cooked consumed-Nutrition authority mode before
mode-dependent Composition work. Mode-independent source/identity/publication
prerequisites close in the same bounded program. USSR82-467 / 492 / 1081 remain
the immediate expansion batch after the authority mode is proven.

PR113 merged at `48707e1e84eff260726609c4508f05407e9f9448`.

Issue #114 now owns the next bounded operation:
evidence-backed blocker classification of all 547 retained recipe identities and
selection of the first high-leverage Planner-capacity production batch.

Branch:
`data/r1e-corpus-blocker-clustering`.

Critical boundary: all recipes may be visible to admission/closure, but SIDE /
SALAD / OTHER are not silently promoted to standalone MAIN candidates. Current R1
batch selection prioritizes truthful BREAKFAST / MAIN capacity.

No Recipe activation, new Nutrition runtime, schema/migration or meal-bundle
implementation is authorized by this classification operation.

## R1-D corpus-wide Planner admission — 2026-09-30

Accepted main: `e350e747a9c6e06e74b2cd450637c25a442c8749` (merged PR111).

Issue #112 now owns corpus-wide Planner admission rather than a one-recipe pilot.
Branch: `data/r1d-planner-capacity-candidate-audit`.

Phase A adds full published-catalogue admission visibility while keeping selection
fail-closed. Inactive, unsupported-role, Nutrition-unavailable and exact-energy
blocked recipes remain visible with explicit blockers instead of disappearing
before Planner diagnostics.

No schema/migration or authority weakening is part of Phase A. The next data step
is a machine-readable closure inventory across retained Russian source families,
then blocker-based production batches.

## R1 candidate universe widened — 2026-09-29

PR110 merged into main at:
`076de7026a48809d68f314189455b29f35e32a04`.

The user explicitly approved expanding R1 beyond the narrow USSR82 set.

R1 may now select candidates from all retained/reviewable recipe source families
under DATA-CORPUS-V1, including USSR82, School2022 and RU-MR-2019.

This is not blanket publication authority. Every recipe still needs exact
source/variant, FoodIngredient/form, Nutrition/Composition, consumed-Nutrition,
immutable RecipeVersion and activation authority.

Next bounded operation after this docs/state decision:
Recipe Nutrition Consumed-Authority Implementation Contract Gate.

No runtime/schema/data publication starts automatically.

## R1 cross-corpus consumed-Nutrition feasibility review — 2026-09-29

PR109 merged into main at:
`03984aae526ddcd7765f6df6f43608bd4ef0e3fa`.

Current bounded operation is docs-only:
`docs/family-food/r1-cross-corpus-consumed-nutrition-review.md`.

Retained evidence reviewed from the hash-pinned
`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip` plus current repository contracts.

Key findings:
- FIC `RU-NUT-DB` is a licensed production source family for bounded exact food
  composition use; old archive rights-unresolved status is superseded by the
  later repository license receipt;
- School2022 has 471 resolved routes, 420 non-clinical, 377 non-clinical material
  executable and 376 non-clinical procurement-mass ready, but zero retained
  Nutrition-ready routes;
- School2022 also retains 976 source-valid nutrient-reconciliation rows across
  244 recipes, all marked do-not-reapply-retention and not-independent food
  profile calculation;
- RU-MR-2019 retained routes are not currently the short ordinary-household path;
- the recurring product gap is consumed Recipe Nutrition authority across
  preparation modes, not only USSR82-697.

No candidate-set change is authorized by this review. Issue #99 still owns the
selected R1 set. If School2022 is to enter R1 before successful R1-C, that requires
an explicit sequencing/candidate-set decision.

No runtime/schema/data publication is authorized.

## R1 activation-authority prerequisite — 2026-09-28

PR108 merged into main at:
`b6973baa2f93ecfaded9c93cb7e5711300f247ee`.

Reviewed authority result for USSR82-697:

- R1-B source truth remains valid;
- USSR82 Table 23 corroborates the exact source-branch boiling mass path
  107 g net → 28% thermal loss → 3% portioning loss → 75 g finished chicken;
- the collection baseline and Table 23 75 g row align the selected recipe branch
  with semi-eviscerated category-II chicken (155 g gross / 107 g net);
- current R1-B binds CHICKEN_CATEGORY_1_RAW / category-I authority, so that
  source-to-canonical mapping is not exact enough for activation and must remain
  historical-only for this recipe;
- this is mass/process evidence, not V2 nutrient-retention evidence;
- current repository has no accepted exact ENERGY_KCAL retention authority for
  this exact chicken/process;
- current RECIPE_COMPOSITION_NUTRITION_V1 rejects transformed Composition
  bindings;
- recipe source has no cooked-output nutrient analysis supporting Route B.

Disposition:
`ROUTE_C / REMAIN_INACTIVE`.

Current branch:
`docs/r1-activation-authority-prerequisite`.

Contract:
`docs/family-food/r1-activation-authority-prerequisite.md`.

No activation/runtime/schema/data publication is authorized by this gate.
Next work remains inside R1: either correct the exact category-II FoodIngredient
authority first and then review exact consumed-Nutrition authority, without
preselecting retention/transformation as the only path, or review another selected
R1 candidate. A transformed Composition route requires exact reviewed
yield/retention evidence; a distinct exact cooked/prepared-product Nutrition route
requires source evidence and its own reviewed publication/calculation contract.
Any new Recipe Nutrition calculation/publication seam requires a versioned
Implementation Contract Gate.
R2 remains blocked until successful R1-C unless sequencing is explicitly changed.

## R1-C production-proof preflight — 2026-09-28

PR107 / #100 merged into main:
`b27ab1e6338fd0ae76f25ce0040416fc15780891`.

User explicitly authorized R1-C.

Preflight found a hard product-data prerequisite:

- R1-B active Planner-eligible RecipeVersions: 0;
- USSR82-697 is published but inactive;
- activation reason is pending reviewed transformation authority;
- four other R1-B candidates remain blocked;
- R1-B input energy 255.892000 kcal is not final cooked-dish Nutrition;
- Step 7 forbids unreviewed numeric transformation/yield/retention publication.

Current branch:
`docs/r1c-production-proof-prerequisite`.

Contract:
`docs/family-food/r1c-production-planner-proof-prerequisite.md`.

R1-C runtime/product proof must not use synthetic candidates or weaken authority.
The next support operation must review a truthful activation-authority route before
a successful R1 Planner week can be claimed.

No R2/R3, Gate1-CLOSE, Shopping or later scope is authorized.

## #100 Planner energy-allocation runtime authorized — 2026-09-27

PR105 merged into main:
`690a17a8c220e7e8f8e93bd63ba46356c73f0503`.

The user explicitly authorized continuation after the merged Contract Gate.

Current branch:
`feat/planner-energy-allocation-v04`.

Runtime contract:
`docs/family-food/planner-energy-allocation-contract.md`.

Bounded work:
- migration 0041;
- reviewed allocation-ready Meal Pattern program versions;
- immutable selection energy shares;
- planner-v0.4 allocation and trace;
- exact replay/conflict/rollback verification;
- preserve planner-v0.3 semantics.

No R1-C / Shopping / Recipe activation work is authorized.

## PR104 post-merge integrity correction — 2026-09-27

PR104 merged into main at:
`75e2854eff82955b5c01ccacaca35fe0fdc534bc`.

A full post-merge audit accepted the R1-B runtime/data result but found that
`state/progress.md` had been accidentally replaced in part by a truncated tool
rendering, deleting 1361 lines of durable historical receipts.

Current correction branch:
`fix/pr104-post-merge-integrity`.

Correction scope:
- restore exact accepted pre-PR104 progress history plus legitimate R1-B entries;
- replace RecipeVersion pre-0040 SQLite PRAGMA introspection with SQLAlchemy
  reflection;
- document the bounded shared transaction ownership used by R1-B atomic
  publication.

No migration, production data, RecipeVersion truth, Planner or R1-C behavior
changes are part of this correction.

PR105 (#100 Contract Gate) exists but must be synchronized after this correction
before merge.

## PR104 R1-B reviewed runtime disposition — 2026-09-27

Five candidates were reviewed against the retained hash-pinned corpus. Only
`USSR82-697` is published, with exact chicken/onion Composition bindings and
inactive status pending Step 7 numeric process authority. `USSR82-453` and
`USSR82-1081` are blocked by missing V2-compatible EGG/BUTTER_UNSALTED
Composition authority; `USSR82-467` and `USSR82-492` are blocked by an
unquantified salt ingredient in verified process text.

The package pins v20 and DC1 row receipts. PR104 must pass exact-head backend,
launcher, Docs, DC1 and nutrition CI before review-ready. Do not merge or begin
#100, R1-C, Shopping or API/UI as part of this operation.

## R1-B runtime authorized — 2026-09-27

PR103 merged into main:
`fb89cfeb84f4052233f82daa7dcc2d1c07aa971a`.

User explicitly authorized:
migration 0040 + publication of the five R1-B RecipeVersions.

Branch:
`feat/r1b-recipe-versions`.

Contract:
`docs/family-food/r1b-source-output-contract.md`.

Runtime scope:
- add immutable RecipeVersion source output fields;
- preserve historical rows as null;
- publish reviewed USSR82-453/467/492/1081/697 selected branches;
- pin exact Composition versions;
- validate deterministic V2 Recipe Nutrition;
- record activation disposition.

No Planner/#100/R1-C/Shopping work is authorized.

## R1-B source-output contract gate active — 2026-09-27

PR101 / R1-A merged into main:

`eb803cda82ce8073443981867291716a0eb0f0ad`.

User authorized continuation in the accepted sequence.

Current bounded operation is **docs-only**:
`#102 — R1-B source output/yield Implementation Contract Gate`.

Branch:
`docs/r1b-source-output-contract`.

Gate document:
`docs/family-food/r1b-source-output-contract.md`.

Reason:
the five R1-B source variants have exact source outputs 40/110/170/160/75 g, but
current RecipeVersion has no structured output/yield field. Persisting immutable
output truth requires a schema contract before runtime.

Proposed minimum:
- RecipeVersion.source_output_g nullable Decimal;
- RecipeVersion.source_output_text nullable text;
- expected migration 0040 after gate approval;
- no output→yield inference;
- no new retention factors;
- Recipe Nutrition remains input-Composition based;
- no Planner/Serving consumption yet.

Five candidate recipes remain:
USSR82-453, USSR82-467, USSR82-492, USSR82-1081, USSR82-697 exact chicken/main branch.

R1-A blockers USSR82-364 and USSR82-208 remain outside R1-B.

Do not start migration/runtime/RecipeVersion publication until this gate is merged
and R1-B runtime is separately authorized.

## R1-A WATER/SALT Planner-energy closure — 2026-09-27

Verified runtime/data head:
`c92a19bdc4f3760bb50f2957068682d62ac126cf`.

Correction after deep review:
- WATER and SALT were previously catalogue-ready but had V2 ENERGY_KCAL unknown;
- exact durable FIC records publish source-backed kcal=0.0;
- both existing identities receive non-current FIC profiles and ATOMIC v2;
- historical current profiles and ATOMIC v1 remain unchanged;
- R1-A result is now 11 publications + 7 late-state reuses + 2 blockers;
- all 5 declared R1-B-ready recipes have exact energy authority at dependency level.

Verification:
Docs #458 / DC1 #320 / Russian #193 / Registry #339 / Partial #251 — SUCCESS.
Registry and Partial focused, all backend shards and launchers are green.

No RecipeVersion or Planner change occurred.

## R1-A review-ready — 2026-09-27

Accepted base:
`9f72f6883e092cbf79930c7ac4a5a1314c7488d8`.

PR:
`#101`.

Verified runtime/data head:
`1f5cc62876a6985eb0d07f119de9b3ccaf9e35d9`.

Result:
- 20 dependencies;
- 9 accepted reuses;
- 9 exact FIC publications;
- 2 blockers;
- 5 of 7 selected recipes dependency-ready for R1-B.

Ready:
USSR82-453, USSR82-467, USSR82-492, USSR82-1081, USSR82-697 exact chicken/main branch.

Blocked:
- USSR82-364 on ING-0014 / Жир кулинарный;
- USSR82-208 on ING-0038 / anomalous FIC salted-cucumber source row.

The durable corpus archive was independently retrieved and all 11 published
source raw-record hashes rechecked.

Exact runtime verification:
Docs #446 / DC1 #308 / Russian #181 / Registry #317 / Partial #239 — SUCCESS.
Registry focused = 400 passed; all backend shards + launchers are green.

No RecipeVersion publication/activation and no Planner change occurred.

Stop after PR101 review/merge. R1-B requires separate explicit authorization.

## R1-A authorized — 2026-09-27

Accepted base:
`9f72f6883e092cbf79930c7ac4a5a1314c7488d8` (merged PR98).

The user explicitly authorized completing the original product meaning of Russian-data Steps 7–10.

Current bounded operation:
`R1-A — Planner-capacity dependency closure`.

Parent issue:
`#99`.

Separate Planner allocation issue:
`#100`.

R1 selected recipe set:
- USSR82-453 Яйца вареные;
- USSR82-467 Омлет (натуральный);
- USSR82-492 Сырники из творога;
- USSR82-1081 Блины;
- USSR82-697 chicken/main source-supported branch only;
- USSR82-364 Шницель из капусты;
- USSR82-208 Рассольник ленинградский.

R1-A owns only direct FoodIngredient/form/Nutrition dependency closure/publication.
No RecipeVersion publication/activation and no Planner change in R1-A.



## Post-PR96 sequencing correction — 2026-09-26

PR96 is merged into main at:
`7443f56b856184db6ddb040b9d68425db9f8d41a`.

PR97 is closed as **SUPERSEDED / DO NOT MERGE** and none of its commits are in main.

Correction:
- old DC1 statuses are historical inventory/planning evidence, not the current project state by themselves;
- later accepted Steps 4–10 established accepted source-authority decisions and precedents within their bounded scopes, reusable publication mechanics, Russian methodology, transformation applicability infrastructure, RecipeVersion publication precedent, V2 Recipe Nutrition authority, and Planner/MealPlan consumption integration;
- the durable corpus archive was later recorded at
  `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`
  with SHA-256
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- do not create a new per-recipe preflight milestone by default.

Correct continuation:
`accepted DATA-CORPUS-V1 contract/source foundation → dependency-ready DC2 where required → DC3 only after required dependencies are accepted → DC4 → Gate1-CLOSE → PR9`.

Recipe-specific form/Nutrition/classification/provenance checks remain normal bounded publication work when existing accepted publication paths and authority contracts are sufficient. If a batch requires a new or changed authoritative publication path, immutable authority contract, schema/migration boundary or cross-context rule, stop for the repository-required docs-only Implementation Contract Gate before runtime implementation.

PR98 restores sequencing only; it does not select or start the next production batch.

A dependent DC3 batch must not bypass unresolved required DC2 food/form/Nutrition dependencies. After PR98 merge, select one concrete bounded operation under Issue #67 before implementation begins.

## PR96 Step 10-B review-ready — 2026-09-26

Accepted base:
`1ef7d1ffd0896873034034b3eb629e62aa474803` (merged PR95).

Verified runtime/test head:
`8b38053697845c7c63936a6b462e98331f5bb7e1`.

Review:
`#5327127307 — READY TO MERGE STEP 10-B`.

Implemented:
- neutral Recipe Nutrition projection in Planner;
- exact-energy readiness with safe legacy default=false;
- exact `planner-v0.3`;
- unchanged `meal-role-recipe-v2`;
- neutral MealPlan/Serving Nutrition consumption;
- synthetic fully V2-bound PlannerService → MealPlan → Serving/day/week proof.

Verification:
- Docs #414 SUCCESS;
- DC1 #276 SUCCESS;
- Russian #163 SUCCESS;
- Registry #274: focused 391; backend 1074/804/776/968; launcher 643 passed, 2 skipped;
- Partial #207: focused 339; backend 1074/804/776/968; launcher 643 passed, 2 skipped;
- AI_ENABLED=false;
- mergeable=true; 0 behind; threads=0; diff audit clean.

No migration, production activation, meal_type or MealRole compatibility change occurred.

Stop for merge review. No self-merge.
After merge, any production activation/publication requires a separately authorized bounded operation.

## Step 10-B runtime started — 2026-09-26

PR95 / Step 10-A merged into main at:
`1ef7d1ffd0896873034034b3eb629e62aa474803`.

The user explicitly authorized the next bounded step.

Branch:
`feat/step10b-planner-mealplan-v2-nutrition`.

Implemented initial Step 10-B seam:
- PlannerConfig exact version = planner-v0.3;
- compatibility remains meal-role-recipe-v2;
- PlannerCandidate has additive exact_energy_ready=false by default;
- PlannerService reads Step10-A neutral Recipe Nutrition projection;
- legacy INCOMPLETE remains rejected unless exact V2 readiness is proven;
- MealPlan/Serving accepts the same neutral Nutrition consumption contract;
- legacy RecipeVersionNutrition remains structurally compatible;
- synthetic cross-context test proves V2 projection → Planner → MealPlan/Serving.

No migration or production Recipe activation is authorized or present.

Verification pending. Stop after review-ready Step 10-B PR.

## PR95 Step 10-A review-ready — 2026-09-26

Accepted base:
`4f9331a8fa73f8488a07295076b0425c00e6654e` (merged PR94).

Verified runtime head:
`3c779c7a0184be6f6838720b6fde78dbe482e8e8`.

Review:
`#5326633449 — READY TO MERGE STEP 10-A`.

Implemented:
- migration 0039 immutable Nutrition binding;
- exact Step 9 10 g butter binding publisher;
- canonical 54-code V2 Recipe Nutrition;
- RECIPE_COMPOSITION_NUTRITION_V1;
- neutral legacy/V2 consumption projection;
- BY_DIFFERENCE-only legacy carbohydrate mapping;
- fresh/replay/rollback/deactivation/immutability acceptance.

Verification:
- Docs #404 SUCCESS;
- DC1 #266 SUCCESS;
- Russian #153: 380 passed;
- Registry #257: focused 352; backend 1073/836/753/956; launcher 643 passed, 2 skipped;
- Partial #197: focused 300; full backend/launcher green;
- AI_ENABLED=false;
- mergeable=true; 0 behind; diff audit clean.

Production Step 9 Recipe remains inactive.

No Planner/MealPlan/planner-v0.3 work occurred.

Stop for merge review. No self-merge.
Step 10-B remains unauthorized until PR95 is merged and separately authorized.

## Step 10-A runtime started — 2026-09-26

PR94 merged at:
4f9331a8fa73f8488a07295076b0425c00e6654e.

The user explicitly authorized moving to the next bounded step.

Step 10-A branch:
feat/step10a-recipe-v2-nutrition

Draft PR:
#95

Implemented scope:
- migration 0039 binding table;
- Nutrition-owned binding repository/UoW;
- canonical 54-code Recipe V2 calculation;
- RECIPE_COMPOSITION_NUTRITION_V1;
- exact BY_DIFFERENCE-only legacy carbohydrate projection;
- exact Step 9 production binding entrypoint;
- focused migration/service/publication tests.

No Planner/MealPlan/activation work is authorized or present.

Verification pending. Stop after PR95 is review-ready; Step 10-B stays blocked.

 PR94 final compatibility correction review-ready — 2026-09-26

Semantic head:
5e2d9a9336a94798327e3a9445e0dffd41e05ff9.

Review:
#5326221930 — READY TO MERGE FINAL-CORRECTED STEP 10 CONTRACT GATE.

Review #5326205581 blocker is closed.

Exact V2 → legacy crosswalk under RECIPE_COMPOSITION_NUTRITION_V1:
- kcal ← ENERGY_KCAL;
- protein_g ← PROTEIN;
- fat_g ← FAT_TOTAL;
- carbohydrates_g ← CARBOHYDRATE_BY_DIFFERENCE only;
- fiber_g ← FIBER_TOTAL_DIETARY.

No AVAILABLE carbohydrate fallback and no STARCH+SUGARS synthesis.
Step 9 legacy carbohydrates remain None; legacy status remains INCOMPLETE.

Verification:
Docs #375 / DC1 #237 SUCCESS.
Registry focused 328 passed.
Partial focused 276 passed.
Sections 1–29 and acceptance 1–74 sequential.
mergeable=true; 0 behind; diff audit clean.

Stop for merge review. No self-merge.
Step 10-A requires separate authorization after PR94 merge.
Step 10-B remains unauthorized until Step 10-A merges.

## PR94 final compatibility blocker correction — 2026-09-26

Exhaustive review #5326205581 superseded the prior READY receipt and found one
remaining V2 → legacy projection ambiguity.

Correction implemented:

- legacy kcal ← ENERGY_KCAL;
- legacy protein_g ← PROTEIN;
- legacy fat_g ← FAT_TOTAL;
- legacy carbohydrates_g ← CARBOHYDRATE_BY_DIFFERENCE only;
- legacy fiber_g ← FIBER_TOTAL_DIETARY;
- CARBOHYDRATE_AVAILABLE never substitutes for legacy carbohydrates;
- STARCH + SUGARS_TOTAL never synthesizes legacy carbohydrates;
- the crosswalk is part of RECIPE_COMPOSITION_NUTRITION_V1;
- Step 9 legacy carbohydrates remain None and five-field status remains INCOMPLETE.

Adversarial acceptance now covers AVAILABLE/BY_DIFFERENCE disagreement, missing
BY_DIFFERENCE, forbidden starch+sugars synthesis and the exact Step 9 projection.

Current status: corrected semantic verification pending.
No runtime/schema/production mutation occurred.

## PR94 deep-corrected Contract Gate review-ready — 2026-09-26

Corrected semantic head:
560cce41e1c1ce54212052bd95dfc8fe4b0cdb13.

Corrected review:
#5326161326 — READY TO MERGE DEEP-CORRECTED STEP 10 CONTRACT GATE.

Deep review #5326074689 blockers are closed:

- RECIPE_V2_NUTRIENT_SET_V1 is the exact 54-code RU_NUTRIENT_REGISTRY_V2 snapshot;
- canonical Recipe Nutrition preserves every requested concept as AVAILABLE or UNKNOWN;
- RECIPE_COMPOSITION_NUTRITION_V1 separately versions row scaling, unknown
  propagation, aggregation, base-serving division and result rounding;
- V1 is intentionally gram-only, required-row-only and untransformed INPUT-basis;
- FOOD_COMPOSITION_APPLICABILITY_V2 remains the lower-level Composition version;
- Step 10-B Planner version is exactly planner-v0.3;
- meal-role compatibility remains exactly meal-role-recipe-v2;
- historical reads are independent of later mutable FoodIngredient active state;
- exact replay preserves original created_at and binding REPLACE is forbidden.

Verification:
Docs #373 SUCCESS; DC1 #235 SUCCESS; Registry focused 328; Partial focused 276;
54/54 request-set comparison PASS; sections 1–29 and acceptance 1–68 sequential;
mergeable=true; 0 behind; whitespace/conflict audit clean.

Stop for merge review. No self-merge.
Step 10-A requires separate authorization after PR94 merge.
Step 10-B remains unauthorized until Step 10-A merges.

## PR94 deep-review blocker correction — 2026-09-26

Deep review #5326074689 superseded the prior READY receipt and found three
additional Contract Gate gaps:

1. canonical V2 nutrient request set was not frozen;
2. lower-level FOOD_COMPOSITION_APPLICABILITY_V2 did not version the new
   recipe-level scaling/aggregation formula;
3. Planner version remained "planner-v0.3 or equivalent" rather than exact
   persisted replay identity.

Correction implemented:

- RECIPE_V2_NUTRIENT_SET_V1 = exact 54-code RU_NUTRIENT_REGISTRY_V2 snapshot;
- every requested code is AVAILABLE or UNKNOWN; omission is not unknown;
- RECIPE_COMPOSITION_NUTRITION_V1 separately versions Recipe Nutrition scaling,
  aggregation, optional handling, per-serving division and rounding;
- V1 is bounded to required rows and untransformed INPUT-basis Composition;
- historical reads do not depend on later FoodIngredient.is_active;
- Step 10-B Planner version is exactly planner-v0.3;
- meal-role compatibility remains exactly meal-role-recipe-v2.

Current status: corrected semantic verification pending.
No runtime/schema/production mutation occurred.

## PR94 corrected Contract Gate review-ready — 2026-09-26

Corrected semantic head:
c23bca0e6df4787f8f083a976fd6257e454d1777.

Corrected review:
#5325809090 — READY TO MERGE CORRECTED STEP 10 CONTRACT GATE.

Review #5325781916 blockers are closed:

- binding ownership is frozen as Nutrition-owned derived calculation authority;
- one focused Nutrition UoW owns all dependency reads/classification/binding write;
- FRESH and EXACT_REPLAY recheck active Step 8 dependency in that UoW;
- external preflight is fail-fast only;
- calculation policy is exactly FOOD_COMPOSITION_APPLICABILITY_V2 and matches
  CompositionResult.calculation_version;
- race/policy/rollback adversarial acceptance is frozen.

Verification on corrected semantic head:
Docs #368 SUCCESS; DC1 #230 SUCCESS; Registry focused 328; Partial focused 276;
mergeable=true; 0 behind; numbering/whitespace/conflict audit clean.

Stop for merge review. No self-merge.
Step 10-A requires separate authorization after PR94 merge.
Step 10-B remains unauthorized until Step 10-A merges.

## PR94 blocker correction — 2026-09-26

Independent exact-head review #5325781916 superseded the prior READY receipts and
found three Contract Gate blockers:

1. binding owner/UoW was not frozen;
2. active Step 8 dependency was not explicitly rechecked inside the binding UoW;
3. calculation_policy_version was arbitrary nonblank text.

Correction implemented on the same PR branch:

- binding is Nutrition-owned derived calculation authority;
- Step 10-A gets one focused Nutrition-owned authority UoW / one connection and
  transaction;
- Recipe/RecipeVersion/RecipeIngredient, FoodIngredient, Composition, vector and
  registry dependencies are read-only inside that UoW;
- FRESH and EXACT_REPLAY both re-resolve dependencies and require active
  FoodIngredient inside the UoW;
- external preflight is fail-fast only;
- persisted policy is exactly FOOD_COMPOSITION_APPLICABILITY_V2 and must match
  CompositionResult.calculation_version;
- adversarial acceptance covers deactivation-after-preflight, replay recheck,
  policy mismatch and late-write rollback.

Current status: corrected semantic verification pending.
No runtime/schema/production mutation occurred.
No Step 10-A or Step 10-B runtime work is authorized.

## PR94 Step 10 Contract Gate review-ready — 2026-09-26

Accepted base:
d0a1a217d3e23b0b930f14de37405a7ca7ba3d16 (merged PR93).

Semantic head:
761871e36a5a019621eb0c8e7900b2dfcf5e2773.

Review:
#5325759751 — READY TO MERGE CONTRACT GATE.

Canonical contract:
docs/family-food/recipe-v2-nutrition-planner-integration-contract.md.

Key decisions:
- runtime is split into Step 10-A and Step 10-B;
- Step 10-A owns migration 0039, immutable RecipeIngredient→Composition binding,
  canonical V2 Recipe Nutrition and neutral consumption projection;
- Step 10-B starts only after A merge and owns Planner V2 readiness,
  planner-version advance and MealPlan/Serving integration;
- production Step 9 butter Recipe stays inactive through both;
- meal-role compatibility remains unchanged;
- legacy NutritionService remains behavior-compatible;
- no latest/current Composition inference or partial required-row V1/V2 mixing.

Verification on semantic head:
Docs #366 SUCCESS; DC1 #228 SUCCESS; mergeable=true; 0 behind; docs/state-only
scope; numbering/whitespace/conflict audit clean.

Stop for merge review. No self-merge. Step 10-A requires separate authorization
after gate merge. Step 10-B remains unauthorized until Step 10-A merges.

## Step 10 Contract Gate started — 2026-09-26

PR93 is merged into main at:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

The user explicitly authorized continuing to the next bounded operation.

Preflight found that general V2 RecipeVersion Nutrition cannot safely select a
mutable/latest FoodCompositionVersion because RecipeIngredient currently has no
persisted Composition pin.

Current docs-only decision:

- expected migration 0039 adds immutable RecipeIngredient → CompositionVersion binding plus registry/calculation-policy pin;
- legacy NutritionService remains unchanged;
- new canonical V2 RecipeVersion Nutrition path is explicit;
- Planner receives only a bounded V2-safe energy projection;
- legacy INCOMPLETE candidates are not globally enabled;
- ROLE_COMPATIBILITY_V1 stays unchanged;
- production School2022 butter Recipe remains inactive;
- real production activation is a later bounded data-publication decision.

Canonical draft:

docs/family-food/recipe-v2-nutrition-planner-integration-contract.md

No runtime/schema/production mutation belongs in this gate.
Stop after review-ready PR; no autonomous merge or runtime implementation.

## PR93 corrected runtime verified — 2026-09-26

Verified runtime head:
`99f3d2b9ae592e9370a0f432316828da7a3b6cfb`.

Both transaction/replay blockers from the independent exact-head review are closed:
- strict trusted-seed classification rechecks required active FoodIngredients
  inside the Recipe Catalogue write UoW for both FRESH and EXACT_REPLAY;
- loader external preflight is fail-fast only, while postconditions accept the
  actual transactional fresh or exact zero-write replay result.

Adversarial tests cover both races and pass in focused suites.

Verification:
Docs #360; DC1 #222; Russian #123; Registry #201; Partial #152 — SUCCESS.
Focused 328/276; backend 1202/751/650/991; launcher 643 passed, 2 skipped.
`AI_ENABLED=false`.

Current status: READY FOR FINAL RE-REVIEW / explicit merge authorization.
No merge performed. No Step 10 work is authorized.

## PR93 transaction/replay blocker correction — 2026-09-26

Independent exact-head review superseded the earlier READY TO MERGE receipt and
identified two blockers in the preflight/write-UoW boundary.

Correction implemented on the same PR branch:
- strict trusted-seed classification re-resolves required FoodIngredients and
  requires active state inside the Recipe Catalogue UoW;
- loader external preflight is fail-fast only;
- actual transactional result may be either exact fresh publication or exact
  zero-write replay;
- adversarial tests cover dependency deactivation after preflight and a
  concurrent exact publisher winning after a FRESH preflight.

The previous runtime verification at
`31751069adec7ada062c8b4b7fcb291f4cd89bed` is superseded for runtime bytes.

Current status: correction implemented; exact-head verification and final
re-review required. Do not merge yet. No Step 10 work is authorized.

## PR93 Step 9 runtime-data review-ready — 2026-09-26

Accepted main:
`2c50782b17584a5708a946e497d6a628977420e9`.

Branch:
`feat/step9-school2022-recipe-runtime`.

Verified runtime head:
`31751069adec7ada062c8b4b7fcb291f4cd89bed`.

Semantic review:
`#5325378822 — STEP 9 RUNTIME/DATA READY TO MERGE`.

Delivered:
- one inactive School2022 53-19з Recipe;
- one immutable SOURCE_VERIFIED RecipeVersion v1;
- one exact 10 g Step 8 butter ingredient;
- two material RecipeSteps;
- institutional holding/14 °C source context only;
- deterministic 17-value V2 validation;
- strict fresh/replay/conflict/rollback;
- no migration/source-corpus/Step 10.

Important shared seams:
- `TrustedRecipeSeed.initial_is_active: bool = true`;
- strict_history opt-in on trusted reconcile;
- read-only Composition `find_version(food_id, version)`.

Existing callers preserve prior behavior.

Verification on runtime head:
Docs #358; DC1 #220; Russian #121; Registry #198; Partial #150 all SUCCESS.
Focused 326/274; backend 1202/751/648/991; launcher 643 passed, 2 skipped.

Stop for merge review. After merge, Step 10 requires separate authorization.

## Step 9 runtime/data publication authorized — 2026-09-26

Accepted main:
`2c50782b17584a5708a946e497d6a628977420e9` (merged corrected PR92 Contract Gate).

Branch:
`feat/step9-school2022-recipe-runtime`.

Canonical contract:
`docs/family-food/russian-recipe-version-publication-contract.md`.

The user explicitly authorized continuing after PR92 merge.

Bounded runtime:
- one inactive `SCHOOL2022_53_19Z_BUTTER_PORTION` Recipe;
- one immutable SOURCE_VERIFIED v1 RecipeVersion;
- one exact 10 g Step 8 butter ingredient;
- two material source-backed RecipeSteps;
- institutional holding/14 °C stay context only;
- deterministic 17-value V2 composition validation;
- strict fresh/replay/conflict/rollback;
- no migration/source-corpus/Step 10.

Stop after review-ready PR. No self-merge.

## PR92 corrected Step 9 Contract Gate review-ready — 2026-09-26

Accepted main:
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Branch:
`docs/step9-russian-recipe-version-contract`.

Verified corrected semantic head:
`3f7a4276ca623c23b61cb344c75e3751f2f83f54`.

Corrected semantic review:
`#5324890694 — CORRECTED STEP 9 CONTRACT GATE READY TO MERGE`.

Blocker #5324872702 is closed.

Applicability:
- exact process-evidence:40 hash pinned;
- institutional-only refrigerated holding is not a domestic RecipeStep;
- 14 °C remains institutional context;
- home storage remains not granted;
- production RecipeSteps are only material facts: no thermal treatment + cut into
  portions.

Planner/activation:
- fresh Recipe is inactive;
- additive `TrustedRecipeSeed.initial_is_active` defaults true for historical
  callers;
- Step 9 sets false;
- replay preserves current activation state;
- inactive Recipe is absent from Planner candidate enumeration;
- Step 10 owns activation and V2 Planner integration.

Everything else remains as frozen by the Step 9 gate: exact 10 g Step 8 butter,
SOURCE_VERIFIED immutable version, deterministic 17-value V2 validation,
unknown WATER/carbohydrate, no migration/source-corpus/legacy Nutrition change.

Verification on corrected semantic head:
Docs #353 SUCCESS; DC1 #215 SUCCESS; mergeable=true; 0 behind main; threads=0;
scope/whitespace clean.

Stop for final review/merge. No Step 9 runtime until gate merge + separate
authorization.

## PR92 blocker correction — applicability + Planner activation — 2026-09-26

Accepted main:
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Branch:
`docs/step9-russian-recipe-version-contract`.

Independent re-review #5324872702 found two blockers.

### Applicability correction

Pinned exact process-evidence:
`ru-school2022:recipe:53-19з:process-evidence:40`
SHA-256
`5428e818127eceea1c69617e435666c6ce817666ba88bf7486b8c6ce4b60a6e4`.

It is explicitly institutional-only, domestic applicability unestablished and
not an executable domestic rule.

Corrected Gate publishes only:
1. no thermal treatment;
2. cut butter into portion pieces.

Refrigerated holding + 14 °C remain institutional source-context evidence.
`home_storage_status=not_granted` is preserved.

### Planner/activation correction

Current Planner enumerates all active Recipes.

Corrected Gate therefore:
- creates Step 9 Recipe inactive;
- authorizes additive `TrustedRecipeSeed.initial_is_active` with default true;
- Step 9 sets false;
- existing seed behavior remains active;
- replay preserves persisted activation state and never reactivates/deactivates;
- Step 9 Recipe is absent from Planner candidate pool before Step 10;
- Step 10 owns activation + V2 Planner integration.

No schema/migration/source-corpus expansion is introduced.

Current task: corrected Docs/DC1 + semantic re-review. No runtime work.

## PR92 Step 9 Contract Gate review-ready — 2026-09-26

Accepted main:
`88a22a3cdfdd13d5481875dcd499abf06939582c` (merged PR91).

Branch:
`docs/step9-russian-recipe-version-contract`.

Verified semantic head:
`b0b5f890ce850075ea91d43e54bc8f93a6497c0d`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

Semantic review:
`#5324830015 — READY TO MERGE STEP 9 CONTRACT GATE`.

Frozen target:
School2022 `53-19з — Масло сливочное (порциями)`
→ exact Step 8 butter 10 g
→ one immutable SOURCE_VERIFIED RecipeVersion
→ deterministic available V2 nutrition.

Key boundaries:
- exact six-record source lineage hashes pinned;
- factual normative-card rights policy, no PDF/layout/media redistribution;
- historical v0.3 blockers explicitly adjudicated;
- no canonical carbohydrate/WATER invention;
- no legacy NutritionService/current-profile switch;
- read-only exact Composition lookup only if runtime needs it;
- strict fresh/replay/conflict wrapper around Recipe reconcile;
- no source-corpus persistence expansion;
- no migration; 0033 reserved / head 0038;
- no Step 10.

Verification on semantic head:
Docs #350 SUCCESS; DC1 #212 SUCCESS; mergeable=true; 0 behind main; threads=0;
scope/whitespace clean.

Stop for final review. No runtime Step 9 until gate merge + separate authorization.

## Step 9 Russian RecipeVersion Contract Gate — 2026-09-26

Accepted main:
`88a22a3cdfdd13d5481875dcd499abf06939582c` (merged PR91 / accepted Step 8 runtime).

Branch:
`docs/step9-russian-recipe-version-contract`.

Canonical gate:
`docs/family-food/russian-recipe-version-publication-contract.md`.

Target:
School2022 `53-19з — Масло сливочное (порциями)`.

Key preflight:
- one exact 10 g butter dependency is now closed by Step 8;
- exact source-card/variant/demand/process/selection/route hashes are pinned;
- historical v0.3 `publication_ready=false` is explicitly adjudicated rather
  than ignored;
- canonical project policy permits factual normative recipe publication while
  excluding publisher layout/photos/logos/third-party commentary;
- Recipe Catalogue schema/UoW is sufficient, no migration expected;
- narrow preflight must reject unexpected existing Recipe history rather than
  silently append;
- old NutritionService current-profile path is intentionally not used because
  Step 8 FIC profile is non-current;
- deterministic acceptance is exact ATOMIC v1 + V2 composition scaled to 10 g;
- carbohydrate and WATER remain unknown;
- Step 10 Planner integration remains separate.

Current authorization is docs-only. Stop after gate review-ready delivery.

## Step 8 runtime/data review-ready — PR91

Accepted main:
`76ca8f8ffba589576af4e0fad4d7a4817a84089f` (merged PR90).

Branch:
`feat/step8-recipe-dependency-butter-runtime`.

Verified runtime/test/workflow head:
`068847f4a3b886e6b8133558f2d4820a6a01474e`.

Delivered exact production bundle:

```text
BUTTER_PEASANT_72_5_UNSALTED
→ FIC RU-NUT-DB code 1417 / DB/533
→ non-current profile
→ 26 source observations
→ 17-value RU_NUTRIENT_REGISTRY_V2 vector
→ ATOMIC v1 / INPUT
```

Critical guards:
- exact source hash pinned;
- `salt_ad=0.0` is source-only no-added-salt form evidence;
- no sodium inference;
- non-zero/null/missing salt evidence rejects publication;
- `water=null` remains unknown and WATER is absent from vector;
- generic butter/USDA profile unchanged;
- no yield/retention/transformation/applicability;
- no RecipeVersion;
- no migration; 0033 reserved, head 0038.

Fresh publication creates one ingredient/profile/seal/composition with 17 values,
commits once and preserves foreign keys. Exact replay writes zero rows and retains
IDs. Identity conflict and injected late publication failure leave the database
unchanged.

Verified on `068847f4a3b886e6b8133558f2d4820a6a01474e`:
Registry #180 SUCCESS (focused 310; backend 1205/798/614/959; launcher 643/2
skipped), Partial #139 SUCCESS (focused 258; same broad counts), Russian #116,
Docs #347 and DC1 #209 SUCCESS.

An early pre-review GitHub blob transport attempt corrupted UTF-8 Python bytes.
It was detected before review readiness and replaced byte-for-byte from the
syntax-checked local source. Final committed files contain no mojibake/control
characters; CI above ran only after the corrected bytes and explicit Step 8
workflow coverage were in place.

Stop for final review. No self-merge and no Step 9.

## Step 8 runtime/data publication authorized — 2026-09-25

Accepted main:
`76ca8f8ffba589576af4e0fad4d7a4817a84089f` (merged PR90 / corrected Step 8 Contract Gate).

Branch:
`feat/step8-recipe-dependency-butter-runtime`.

Canonical contract:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

The user explicitly authorized continuing after PR90 merge.

Bounded runtime target:
- one new exact FoodIngredient: `BUTTER_PEASANT_72_5_UNSALTED`;
- exact FIC DB/533 / code 1417 profile;
- source-only `salt_ad=0.0` guard for no added salt;
- `water=null` preserved as unknown;
- 17 V2 values;
- non-current profile;
- ATOMIC v1 / INPUT;
- existing generic butter/USDA history unchanged;
- no transformation/applicability;
- no migration.

Stop after review-ready PR. No Step 9.

## PR90 corrected Step 8 Contract Gate review-ready — 2026-09-25

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Verified corrected semantic head:
`f0b2fa24403589de8b6c16a20b3cc326772c0fbe`.

Corrected semantic review:
`#5314905510 — CORRECTED STEP 8 CONTRACT GATE READY TO MERGE`.

Re-review blocker #5312850815 is closed by exact source evidence:

- FIC DB/533 `salt_ad = 0.0`;
- source label `Добавленная соль`;
- disposition remains `SOURCE_ONLY_NO_V2_TARGET`;
- accepted only for the exact no-added-salt form binding;
- not V2 nutrition, not zero sodium, no sodium inference;
- non-zero/null/missing salt evidence fails closed.

All other Step 8 boundaries remain unchanged:
one exact butter food, 17-value sparse V2 vector, WATER unknown, non-current
profile, ATOMIC v1 / INPUT, no transformation, no migration, no Step 9/10.

Verification on corrected semantic head:
Docs #345 SUCCESS; DC1 #207 SUCCESS; mergeable=true; 0 behind main; threads=0;
scope/whitespace clean.

No runtime/schema/production data was changed.

Stop for final review/merge. After merge, Step 8 runtime publication requires
separate explicit authorization.

## PR90 Step 8 Contract Gate blocker correction — 2026-09-25

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

Independent re-review #5312850815 found one blocker:
the contract had not explicitly bound School2022's unsalted requirement to the
salinity-unspecified FIC DB/533 display identity.

Correction:

- exact FIC DB/533 field `salt_ad = 0.0`;
- frozen source label `Добавленная соль`;
- existing Step 4 disposition `SOURCE_ONLY_NO_V2_TARGET` preserved;
- accepted only as Step 8 form-compatibility evidence for **no added salt**;
- not a V2 nutrient and not a zero-sodium claim;
- no inference from sodium;
- changed/non-zero/null/missing `salt_ad` fails closed.

All other Step 8 decisions remain unchanged: one butter food, 17-value V2 vector,
WATER unknown, non-current profile, ATOMIC v1 / INPUT, no transformation and no
migration.

Current task: exact-head Docs/DC1 re-verification and corrected final review.
No runtime/data publication or merge.

## Step 8 Contract Gate review-ready — PR90

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747` (merged PR89 / accepted Step 7 runtime).

Branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical contract:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

Verified semantic head:
`49c291ab5e46a88e34a6f3ae897c32f4cccc6378`.

Review:
`#5303638521 — READY TO MERGE CONTRACT GATE`.

Frozen vertical slice:

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ licensed FIC RU-NUT-DB code 1417 / DB/533
→ non-current V2 profile
→ 17-value sparse sealed vector (WATER unknown)
→ ATOMIC v1 / INPUT
```

Critical preserved boundaries:

- existing generic `BUTTER_UNSALTED` / USDA FDC 173430 unchanged;
- School2022 source calculations are not production food-nutrition authority;
- FIC raw record hash pinned to
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- `water=null` is not coerced/inferred;
- no current selector switch;
- no YieldModel/retention/Transformation/Applicability rows;
- no migration; 0033 remains reserved and head stays 0038;
- no Step 9/10.

Semantic verification:
Docs #343 SUCCESS; DC1 #205 SUCCESS; mergeable=true; 0 behind main;
unresolved review threads 0; patch whitespace/conflict audit clean.

This is a docs-only gate. No runtime/schema/production data was published.

Stop for final review/merge. After merge, Step 8 runtime/data publication needs
separate explicit authorization.

## Step 8 recipe-dependency food batch Contract Gate — 2026-09-24

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747` (merged PR89 / accepted Step 7 runtime).

Current branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

Bounded target:

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ licensed FIC RU-NUT-DB code 1417 / DB/533
→ non-current V2 profile
→ sparse 17-value sealed vector
→ ATOMIC v1 / INPUT
```

Critical evidence:

- School2022 PDF SHA-256
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- §1.4 freezes butter at 72.5% fat for recipe norms;
- procurement-quality page 261 requires unsalted butter and identifies the
  peasant class at at least 72.5%;
- recipe 53-19з has gross=net=10 g and no thermal treatment;
- FIC DB/533 source code 1417:
  `Масло сливочное крестьянское, 72,5%`;
- exact FIC raw record hash:
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- retained FIC archive independently reverified at the accepted
  206692075-byte / `c0d90020...` identity;
- DB/533 `water=null`: do not coerce or infer; expected vector has 17 values.

Preservation:

- generic `BUTTER_UNSALTED` and USDA FDC 173430 history unchanged;
- no current-profile selector switch;
- no transformation/yield/retention/applicability rows;
- no migration; 0033 stays reserved, head stays 0038;
- no Step 9/10.

The one-food size is intentional: it closes one exact Step 9 vertical dependency
without widening catalogue scope.

Boiled egg 54-6о was rejected as the immediate vertical slice because boiling
would require unsupported production transformation nutrition and the retained
FIC cooked-egg candidate is structurally quarantined.

Current authorization is docs/preflight only. Stop after Contract Gate delivery;
no runtime/data publication before review/merge.

## Step 7 runtime review-ready — PR89

Accepted main:
`71e4cfc63908440a54631e68b7507e94311980d2` (merged PR88 / accepted Step 7 Contract Gate).

Branch:
`feat/step7-transformation-applicability-runtime`.

PR:
`#89 — Step 7: transformation applicability runtime`.

Verified runtime/test/workflow head:
`e481b6cda42afa2f33e5239262dae3f3c6780797`.

Delivered contract-preserving runtime:

- one dependent immutable `TransformationApplicability` per exact
  `FoodTransformation`;
- additive `0038_transformation_applicability`, no accepted-table rebuild/backfill;
- registry-aware V2 retention read/write that proves persisted row registry identity;
- explicit V2 transformed-composition publication;
- separate applicability-aware V2 calculator;
- exact food, explicit season and sequential evidence-scope enforcement;
- DB- and repository-level late-applicability rejection;
- same-UoW failure rollback;
- legacy V1 calculator, retention snapshot/digest and legacy publication paths unchanged;
- zero production numeric Book2002 / School2022 / legacy loss-factor publication.

Verification on `e481b6cda42afa2f33e5239262dae3f3c6780797`:

- Russian nutrition methodologies #113 — SUCCESS;
- Nutrient Registry V2 #169 focused — 280 passed, including all three Step 7 suites;
- Partial nutrition profiles #130 — SUCCESS:
  - focused 228 passed;
  - full backend shards 1252 / 768 / 582 / 962 passed;
  - launcher 643 passed, 2 skipped;
- Nutrient Registry V2 launcher — 643 passed, 2 skipped;
- AI_ENABLED=false;
- GitHub PR patch audit: no trailing whitespace/conflict markers, bounded Step 7 scope;
- direct local git shell check unavailable because the container could not resolve github.com.

Review concerns closed during implementation:

- historical tests expecting 0037 as schema head were advanced without removing 0037 from the prefix;
- synthetic V2 persistence fixture now satisfies existing partial-profile invariants;
- rollback is proven by an injected exception after attempted Step 7 publication;
- registry-aware reader is tested against a physically mixed persisted V1/V2 retention profile;
- late applicability is rejected both by repository and direct SQLite trigger;
- focused CI explicitly includes the new Step 7 test suites.

Stop boundary:

- PR89 may be reviewed; no autonomous merge;
- no Step 8 / Step 9 / Step 10;
- no production numeric source-loss publication;
- after PR89 merge, stop and wait for separate Step 8 authorization.

## Step 7 Contract Gate review-ready — PR88

Accepted main:
`6ec1069d867388e5d1f4782ce6cdeed08c017694` (merged PR87).

Branch:
`docs/step7-transformation-applicability-contract`.

Verified semantic contract head:
`7068b4d7af9d0b8817e933daeaa89a08f68feb26`.

Canonical contract:
`docs/family-food/transformation-applicability-contract.md`.

Key frozen boundaries:

- existing CompositionCalculator / retention writer/reader remain V1-compatible;
- old retention snapshot digests are not rewritten;
- V2 retention requires explicit registry-aware publication/read validation;
- no same-code automatic V1→V2 carry-forward;
- TransformationApplicability is a one-to-one dependent record of an immutable
  FoodTransformation;
- exact food / season / source evidence scope are explicit;
- late applicability after composition publication is forbidden;
- explicit V2 transformed publication validates applicability before insertion;
- expected migration is 0038_transformation_applicability;
- initial runtime publishes zero production numeric source-loss factors.

Contract verification:
Docs #335 SUCCESS; DC1 #197 SUCCESS.
Final semantic review #5299903757: READY TO MERGE CONTRACT GATE.

After PR88 merge, stop. Step 7 runtime/0038 requires separate authorization.
Do not start Step 8/9/10 automatically.


## Step 7 transformation applicability Contract Gate — 2026-09-24

Accepted main:
`6ec1069d867388e5d1f4782ce6cdeed08c017694` (merged PR87 / accepted Step 6B).

Current branch:
`docs/step7-transformation-applicability-contract`.

Canonical gate:
`docs/family-food/transformation-applicability-contract.md`.

Current authorization is docs/preflight only.

Critical facts:

- current Composition calculation and retention writer are V1-pinned;
- 0035 made retention rows registry-version-aware but historical retention domain
  snapshots/digests intentionally omit registry identity;
- therefore Step 7 must not mutate old retention snapshot shape;
- V1/V2 same-code identity is not sufficient retention authority;
- exact food/season/operation/source applicability must be explicit;
- supplied loss/retention corpus evidence is not production-ready numeric
  authority.

Gate direction:

- one-to-one dependent `TransformationApplicability` per immutable
  `FoodTransformation`;
- no late applicability after a transformation is used by composition history;
- explicit registry-aware V2 retention publication seam;
- legacy `CompositionCalculator` remains V1;
- separate applicability-aware V2 calculator;
- expected additive migration `0038_transformation_applicability`;
- zero production numeric loss-factor publication in initial Step 7 runtime.

Stop after Contract Gate review/merge. No runtime 0038, Step 8, Step 9 or Step 10
without separate authorization.


## Step 6B runtime review-ready — PR87

Accepted main:
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc` (merged PR86).

Branch:
`feat/step6b-meal-plan-reference-methodology-pins`.

Verified runtime/test head:
`8853d2a09240d26997c83915bc4167ab39979323`.

Step 6B implementation is review-ready.

Key delivered semantics:

- one optional complete-or-zero methodology pin set per MealPlan revision;
- pin references exact immutable Step 6A selection;
- member birth_date / sex / height / weight / activity / goal / updated_at are
  frozen from authoritative HouseholdMember state;
- member updated_at is guarded by SQLite-safe CAS/write intent before plan write;
- Russian group-reference selections are revalidated at `MealPlan.week_start`;
- methodology pins persist atomically with MealPlan, meal-pattern pins, events
  and Servings;
- old MealPlans remain zero-pin and receive no backfill;
- revision history preserves old snapshot/selection while a later revision may
  pin newer member state or methodology selection;
- Planner does not provide methodology IDs and remains zero-pin until Step 10.

Migration:
`0037_meal_plan_reference_methodology_pins`.

Exact runtime verification:
Docs #331 SUCCESS; DC1 #193 SUCCESS; Russian #98 380 passed; Registry #139
focused 257 + 4/4 backend shards + launcher 643/2 skipped; Partial #109 focused
228 + 4/4 backend shards + launcher 643/2 skipped.

After final docs/state verification, PR87 may be reviewed for merge. No autonomous
merge. Stop before Step 7 / Steps 8–10.


## Step 6B runtime authorized — 2026-09-23

Accepted main:
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc` (merged PR86).

Branch:
`feat/step6b-meal-plan-reference-methodology-pins`.

Read first:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Bounded runtime target:

- MealPlan-owned reference-methodology pins only;
- migration `0037_meal_plan_reference_methodology_pins`;
- exact Step 6A selection ID per pinned member;
- immutable authoritative member target-input snapshot;
- complete-or-zero pin coverage;
- MealPlan.week_start reference date;
- Russian applicability revalidation at week_start;
- member updated_at CAS guard before plan commit;
- zero backfill for historical plans;
- no Planner/default/API/UI/source-native-policy change.

After review-ready delivery, stop. No merge or Step 7/Step 10 without separate
authorization.


## Step 6A runtime review-ready — PR86

Accepted main:
`e38692f7839ecab2da9499dc968dd01638227046` (merged PR85).

PR86:
`feat/step6a-member-reference-methodology-selection`.

Verified runtime head:
`e03be7b0c4a9b7766a961026cdf8de7d1f56d8d8`.

Step 6A implementation is review-ready.

Important final corrections:

- migration 0036 DDL is rollback-atomic under the custom runner;
- global `acceptance_request_id` cross-scope reuse fails closed;
- real SQLite concurrent Household/member writer is converted to a deterministic
  Step 6A conflict through an exact-token CAS/write-intent guard;
- semantic no-op is zero-write and intentionally does not persist/consume its new
  request ID; later reuse is an ordinary new command.

Exact runtime verification:
Docs #314 SUCCESS; DC1 #176 SUCCESS; Russian #81 358 passed; Registry #110
focused 257 + 4 backend shards + launcher 643/2 skipped; Partial #92 focused 228
+ 4 backend shards + launcher 643/2 skipped.

No MealPlan/0037/Planner/API/UI/source-native-policy change is in Step 6A.

After PR86 merge, stop. Step 6B / migration 0037 requires separate explicit
authorization.


## Step 6A runtime authorized — 2026-09-23

Accepted main:
`e38692f7839ecab2da9499dc968dd01638227046` (merged PR85).

Branch:
`feat/step6a-member-reference-methodology-selection`.

Read first:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Bounded runtime target:

- MemberReferenceMethodologySelection only;
- migration `0036_member_reference_methodology_selection`;
- FAMILY_FOOD_NUTRITION_V1 baseline + optional Step 5 Russian group-reference;
- acceptance_request_id exact retry identity;
- expected_current_selection_id ordinary concurrency;
- Household/member token binding and stale-read protection;
- no MealPlan/0037/Planner/API/UI changes.

After review-ready delivery, stop. No merge and no Step 6B without separate
authorization.


## Step 6 corrected Contract Gate — PR85 re-review blockers resolved

Accepted base:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Branch:
`docs/step6-persisted-methodology-selection-contract`.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

PR85 re-review blockers are now resolved in the contract:

1. **Split signal:** runtime Step 6 is mandatory Step 6A/6B, not one migration.
   - 6A: member reference-methodology selection, expected 0036.
   - 6B: MealPlan reference pins/snapshots, expected 0037.
2. **Policy ownership:** `RU_SOURCE_NATIVE_*` is removed from member selection;
   it remains food/calculation policy for a later calculation/plan receipt.
3. **Replay identity:** persisted `acceptance_request_id` identifies exact retry;
   stale `expected_current_selection_id` remains a conflict unless the exact
   request ID is replayed.

Member selection now owns only personal reference configuration:
`FAMILY_FOOD_NUTRITION_V1` plus optional Step 5 Russian group-reference table.

Existing plans are never backfilled. Step 6B later supports zero-pin legacy plans
or complete pins only.

Current task remains docs-only PR85. No runtime migration/code is authorized.


## Step 6 persisted methodology selection Contract Gate — frozen 2026-09-23

Accepted base:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Branch:
`docs/step6-persisted-methodology-selection-contract`.

Canonical gate:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Key decisions:

- methodology choice is a Household-owned immutable/versioned member selection,
  not a mutable HouseholdMember field;
- it is separate from MemberMealPatternSelection;
- `FAMILY_FOOD_NUTRITION_V1` remains the required personal baseline;
- Russian group reference is optional/additive and must pair with an explicit
  Russian source-native policy;
- published-zero estimate remains opt-in;
- MealPlan historical replay requires an immutable member methodology pin plus a
  snapshot of birth_date/sex/height/weight/activity/goal/member_updated_at;
- existing historical plans remain zero-pin legacy state; no invented backfill;
- methodology-pinned plans must use complete-or-zero member pin sets;
- expected next migration is 0036; reserved 0033 remains untouched;
- Step 6 does not change current Planner/NASEM behavior.

Current work is docs-only Contract Gate. Do not implement 0036/runtime until the
gate is merged and separately authorized.


## Step 6 persisted methodology selection Contract Gate — 2026-09-23

Accepted main:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Current branch:
`docs/step6-persisted-methodology-selection-contract`.

The user explicitly authorized Step 6. Under the repository-wide
Implementation Contract Gate rule, current work is docs/preflight only.

Preflight facts:

- Step 5 reviewed Russian reference table is merged and available explicitly;
- current personalized target path is `FAMILY_FOOD_NUTRITION_V1` /
  NASEM/DRI-based and remains the existing default;
- Russian source-native policy is explicit/versioned
  (`RU_SOURCE_NATIVE_STRICT_V1` or
  `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`);
- `HouseholdMember` is mutable and has no historical profile revisions;
- `MealPlan` is immutable/revisioned and already pins
  `MemberMealPatternSelection`, but not nutrition methodology;
- historical target replay therefore cannot rely on current member state;
- no current migration uses `0036`; reserved `0033_recipe_template_catalogue`
  must remain reserved.

The Step 6 gate must decide the immutable selection + plan-pin/snapshot contract
before implementation. No runtime/schema change is authorized on this branch.

After contract review/merge, stop. Do not begin Step 6 runtime automatically.


## Step 5 runtime publication — authorized 2026-09-23

Accepted main:
`f12a3f58279eb07c710d1ff889cc70d933da3310` (merged PR83).

Current branch:
`feat/step5-russian-reference-table-runtime`.

The user explicitly authorized runtime Step 5 after merging the Contract Gate.

Read first:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Frozen runtime target:

- methodology `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`;
- exact 48 rows / 24 definitions × male/female;
- tables 11/12 + 16/17 only;
- completed age 19+;
- KFA-independent;
- exact Decimal source values/source units;
- exact source claim/page/table/row/column provenance;
- all canonical codes/units validated against `RU_NUTRIENT_REGISTRY_V2`;
- existing `ReviewedRussianReferenceTable`, provider and selector reused;
- unknown/tampered/drifted package fails closed;
- no DB write, schema or migration;
- NASEM/default Planner/API/UI paths unchanged.

Important source-semantic boundary:
`BETA_CAROTENE` preserves source/reference `mg/day` while registry canonical
unit is `µg`; this is same-definition mass-unit compatibility, not source
rewriting or nutrient substitution.

Tables 13/18 remain deferred because adequate-level semantics are not represented
by the current row model. Do not add `reference_kind` in this runtime PR.

Before publishing rows, bind the runtime package to the pinned source transport
hashes and exact source claim identities. If the exact transport evidence cannot
be reproduced, stop rather than fabricate claim IDs.

After review-ready delivery, stop. No merge and no Step 6 without a separate
explicit instruction.

## Step 5 reviewed Russian reference table contract gate — 2026-09-22

Accepted main:
`aa5ebcb4c70c9adee0fd1242f520ef1298f6b167` (merged PR82).

Current branch:
`docs/step5-reviewed-russian-reference-table-contract`.

The user authorized Step 5. Under the repository Implementation Contract Gate
rule, current work is docs/preflight only.

Preflight source facts from the supplied corpus:

- source: `RU-NEEDS-MR-2.3.1.0253-21`;
- official PDF SHA-256:
  `cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79`;
- population-reference package: 147 groups / 218 source nutrient rows /
  872 claims / 735 scalar lookups / 137 withheld;
- source package itself is transport evidence, not runtime authorization.

Proposed first production table is intentionally only 48 adult micronutrient
rows:

- tables 11/12 men;
- tables 16/17 women;
- 24 exact V2 definition mappings per sex;
- source `Старше 18 лет` maps to completed age 19+;
- KFA-independent;
- no source null-sex coercion.

Important deferrals:

- tables 9/14 energy/macros: Far-North adjustment applicability is not represented
  by the current row model;
- tables 10/15 percent-energy/ranges: not current daily-amount comparison truth;
- Vitamin D and Calcium: source footnotes change >65 values and the corpus
  withholds those cells;
- tables 13/18 are adequate-level references and are deferred because the
  current row model does not preserve reference kind; fluoride is therefore
  deferred with them;
- folate/Vitamin K: no accepted exact target-definition mapping for this table;
- cobalt/silicon/vanadium: no V2 target;
- children and pregnancy/lactation: outside current selector/publication contract.

Read:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Do not publish numeric rows or start runtime until this gate is merged and the
user separately authorizes runtime Step 5.

## Step 4C runtime publication — 2026-09-22

Accepted main: `be6eed3591752d38ece3de5892e4306134e8d762` (merged PR81).
Branch: `feat/step4-ru-nut-db-runtime-publication`.

Authorized scope: publish the exact five licensed RU-NUT-DB records through the
merged Step 3 V2 publication path.

Runtime design:
- refactor Step 3 to expose one transaction-neutral bundle application operation;
- preserve public `ReviewedNutritionPublicationService.publish(bundle)` behavior;
- add `ReviewedNutritionBatchPublicationService.publish_batch(...)` owning one
  UoW and one commit;
- fresh batch = five bundles / two new identities / 90 V2 values / five seals /
  five ATOMIC versions;
- replay = zero writes and stable IDs;
- conflict/failure on any food = rollback entire attempted batch;
- no migration/schema;
- all FIC profiles non-current; current USDA profiles preserved.

Data package:
`data/curation/ru-nut-db-step4-runtime/`.
It contains only the five reviewed source records, exact license attribution and
source link. The full FIC database is not republished.

Verification is pending on the runtime implementation head. Stop after PR review;
no self-merge or Step 5.


## Step 4B RU-NUT-DB semantic closure — 2026-09-22

Accepted main: `f7ac885dde055900b3a6397aa64a15fe698abe5b` (merged PR80).
Current branch: `data/step4-ru-nut-db-semantic-closure`.

The licensed five-record source mapping is frozen in:
`data/curation/ru-nut-db-step4-semantic-closure/`.

Result: 18 approved numeric fields and **90 V2 values — 18 per food**.
Source-published zero is retained as numeric zero with `VALUE` source state and
explicit provenance; it is not reclassified as missing/below-detection.

Eight fields remain deferred/source-only:
`carbh, a_vit, pp, carot, cholest, ethanol, sugar_ad, salt_ad`.

No migration/schema change is required by the semantic closure.

After Step 4B merge/review, runtime can implement the accepted five-food batch
using the exact mapping manifest.

Read:
- `docs/family-food/first-russian-food-batch-contract.md`;
- `data/curation/ru-nut-db-step4-semantic-closure/README.md`.

## Step 4 licensed RU-NUT-DB source correction — 2026-09-22

PR80 remains the docs-only Step 4 Contract Gate.

The user supplied a signed FIC license plus the original corpus archive. The
source-authority blocker is cleared for the pinned electronic `RU-NUT-DB`
snapshot; do not treat Book2002 as production numeric authority.

Exact FIC records are codes 1150,1187,1184,1204,66 with DB indices
252,126,69,254,103.

User decision: DB126 `Морковь свежая красная` creates new
`CARROT_RED_RAW`; it must not reuse generic `CARROT`. The five-food batch is
3 reuse + 2 create (`CARROT_RED_RAW`, `RICE_GROATS`).

The archive shows RU-NUT-DB and Book2002 values differ, especially rice, so they
must not be merged.

The next blocker is scientific field semantics, not rights:
`carbh` definition unresolved; hidden field bindings unresolved; source zero
semantics unresolved.

Do not seal a 13-row sparse vector yet because the seal is immutable. First
complete the bounded mapping closure, then implement the one-UoW five-food batch.

Read:
- `docs/family-food/first-russian-food-batch-contract.md`;
- `docs/family-food/fic-nutrition-license-receipt.md`.


## Step 4 first Russian food batch contract gate — 2026-09-21

Accepted main: `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6` (merged PR79).
Current branch: `docs/step4-first-russian-food-batch-contract`.

Step 3 transactional publication is accepted. Current work is docs-only Step 4A.

Candidate batch is exactly five Book2002 records:
`SUGAR`, `CARROT`, `CABBAGE_GREEN`, `BEET`, and new
`RICE_POLISHED_DRY`.

The contract freezes:

- identity reuse/new-rice decisions;
- explicit ATOMIC versions 2/2/2/1/1;
- all profiles non-current;
- 60 retained source cells / 37 positive V2 values;
- source-native carbohydrate → V2 `CARBOHYDRATE_AVAILABLE`;
- below-detection → no numeric row;
- ash/organic acids → source-only evidence;
- one atomic five-food batch transaction;
- a new batch-orchestration seam because Step 3 `publish()` currently owns and
  commits its own UoW; Step 4 must reuse a transaction-neutral bundle operation
  and commit all five once;
- no migration/schema change.

Source-authority update: accepted repository evidence still says
`BLOCKED_PENDING_RIGHTS_REVIEW`, but on 2026-09-21 the user explicitly stated
that they possess permission. Treat the remaining gate as permission
evidence/scope review, not an assumption that permission is absent. Runtime/data
publication starts only after the permission is inspected and an authority receipt
records the applicable use/distribution scope.

Read:
`docs/family-food/first-russian-food-batch-contract.md`.

Do not publish numeric Book2002 values, change current profiles, or start Step 5
automatically.


## Step 3 transactional V2 publication runtime — 2026-09-21

Accepted main: `e5466121e4958cf4fb95ba9041d1c7926daab17e` (merged PR78).
Current branch: `feat/transactional-nutrition-publication-v2`.
Delivery PR: #79.

Read the merged contract first:
`docs/family-food/transactional-nutrition-publication-contract.md`.

Runtime implementation is bounded to publication mechanics only. Key seams:

- generic complete-profile `add()` remains historical V1 behavior;
- Step 3 uses a dedicated `add_unsealed()` writer inside its publication UoW;
- V2 persisted evidence uses `FFO_NUTRIENT_VALUE_EVIDENCE_V2`; V1 JSON/decoder
  remains unchanged;
- existing or replayed V1 seals cannot be rebound to V2;
- Step 3 profiles are always non-current;
- vector values are inserted before the immutable V2 seal; ATOMIC follows the
  readable seal; commit occurs once;
- exact replay is zero-write; authoritative conflicts/partial state fail closed;
- legacy CompositionCalculator remains V1-pinned; V2 transformation applicability
  remains Step 7.

No migration/schema change, Book2002 numeric publication, rights decision,
Russian food batch, target table, methodology persistence, recipes, Planner,
Gate1, Shopping, API/UI or AI work is included.

After PR79 final review/merge, stop before Step 4. Do not publish a Russian food
batch automatically.


## Step 3 transactional publication contract gate — 2026-09-21

Accepted main: `5343734e620c9f36d24aad54320c2196588b004d` (merged PR #77).
Current branch: `docs/step3-transactional-publication-contract`.

The user accepted the new pre-implementation process. This branch contains no
runtime/schema/data publication. It freezes the Step 3 contract before code.

Critical preflight finding: generic complete-profile repository insertion
automatically creates a V1 vector seal. Since one profile can have only one
immutable seal, Step 3 requires a specialized reviewed profile writer that
persists the profile/observations without legacy V1 bootstrap. Existing generic
behavior must remain unchanged.

No new migration is expected: 0034 supports partial profiles, 0035 supports
versioned nutrient values/seals, and ATOMIC Composition already references the
sealed profile. If implementation later needs a schema change, stop.

Two further preflight boundaries are frozen:

- the current vector reader decodes historical V1/FDC-shaped provenance; Step 3
  must add source-neutral V2 provenance decoding without fabricating FDC fields
  or rewriting V1 evidence; `source_nutrient_nbr` becomes optional legacy/source
  metadata for V2 while historical V1 reads retain their exact value;
- legacy CompositionCalculator intentionally reads V1 definitions. Step 3 must
  not make it V2-aware. V2 ATOMIC validation uses the version-aware vector reader
  and NutritionMethodologyService; transformation applicability remains Step 7.

Read:
`docs/family-food/transactional-nutrition-publication-contract.md`.

After this contract PR is reviewed/merged, do not start runtime implementation
without the next explicit authorization. Step 4 production food publication and
source-use decisions remain separate.


## Nutrient Registry V2 handoff — 2026-09-21

Accepted base: PR76 merge `011f4b74abd29f7b5ec77ab0f15998f781f43c43`.
Current branch: `feat/nutrient-registry-v2-adapters`.

Step 2 owns versioned nutrient identity and adapters only. V1 remains immutable;
V2 uses `(registry_version, code)`, adds RE/NE/tocopherol-equivalent concepts
and requires explicit method provenance for V2 source-native calculations.
Existing Composition retention lookups stay V1-pinned.

Migration: `0035_versioned_nutrient_registry`; reserved 0033 remains unused.
No product publication, source-rights decision, target-table publication or
Planner/API/UI switch is in scope.

After final review/merge, stop before step 3 transactional publication.

## PR76 final verification trigger — 2026-09-20

Final task-local corrections are complete: historical regression jobs restore
full Git history for provenance tests, and the current-table guard now includes
`food_nutrition_profile_observations`. No production/domain semantics changed in
these last corrections.

The next `Partial nutrition profiles` workflow run on this exact head is the
final acceptance target. After it, do not modify the branch; record review
evidence only in the PR.

## Partial nutrition profile storage handoff — 2026-09-20

Accepted base: PR75 merge `33659866348bbc56d705bb764bb3c864c2cce0be`.
Current branch: `feat/partial-nutrition-profiles`.

This is plan step 1 only. Partial profiles persist SQL NULL plus immutable source
observation state/literal/method/locator; they remain non-current for the legacy
selector and intentionally have no automatic V1 vector seal. Existing complete
profiles and pinned vector/composition history must remain unchanged.

Schema work is `0034_partial_nutrition_profiles`; reserved
`0033_recipe_template_catalogue` is not consumed. Future 0033 must be appended
after accepted 0034 in the explicit migration list to preserve existing exact
prefix histories.

Required final verification: focused domain/repository/migration/vector tests,
populated upgrade + failure rollback + backup restore/re-upgrade, full backend and
full launcher regression, AI disabled.

Do not start registry/adapters (plan step 2) until this PR is reviewed/merged.

## PR75 Russian methodology sync — 2026-09-20

PR74 is accepted at `4c9598b623b9042924bb1f8d864c56d3d0a407c4`; PR75 has been
synchronized with that main state.

The user explicitly confirmed authorization for the PR75 Russian methodology
implementation and explicitly approved
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`. The policy is opt-in only:
below-detection provenance and unknown detection limit remain, interpreted zero
is estimated, and it is not exact-zero/allergen/default-Planner authority.

PR75 trial evidence is now bound to accepted PR74 input/verification receipts and
nonnumeric profile reviews. A numeric-free CI receipt owns merge-review evidence;
the earlier external byte-identical trial claim is not required for acceptance.
Source reuse remains blocked and no canonical profiles are imported.

After PR75 review/merge, schema/profile persistence, registry publication,
source-use approval, target-table publication and Planner/API/UI enablement remain
separate gated work.

## Preserved pre-PR74-sync Russian methodology receipt — historical

The following block records the original PR75 branch state before PR74 merged.
Its base/status, local A/B-trial and “PR74 not presumed merged” wording are
superseded by the PR75 synchronized section above. It is historical evidence only.

### Original Russian methodology layer — 2026-09-20

User approved Russian method support and broader compatibility adaptation.
Base a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0. New policy layer and internal
services preserve V1 rather than relabel its USDA/NASEM semantics.
322 focused/regression tests passed; SQLite vector/ATOMIC read tested.
Independent audits caught held-observation provenance and energy partition issues;
fixed with explicit held state, original evidence receipt, basis/form checks and
reviewed disjoint energy partition requirement.

Five locked book profiles:25 core observations,50 evaluations;5 source-native
available carbs accepted per policy,3 unknowns in strict mode,3 explicitly marked
zero estimates in alternate mode. Two final trial files byte-identical. Numeric
trial stays in local deliverables/ru-methodology-trial-v1-final.json outside Git.
No source profiles imported, no automatic Russian norm table enabled.

Read docs/family-food/russian-nutrition-methodologies.md before continuation.
The next implementation dependencies (already directionally authorized) are
partial-profile persistence/registry, accepted target tables and method selection
in Planner/API/UI. Source rights and scientific mapping remain separate gates.
PR74 is not presumed merged. No new migration or live production write.


## PR73 blocker corrections handoff — 2026-09-20

User authorization is now explicit for fixing PR73 blockers and completing this
bounded evidence review only. The package remains non-production: 211 exact
source-input annotations, four route holds, no canonical IDs, no nutrient
equivalence, no retention authority.

The validator now fails closed on form authority, mapping semantics/flags and the
separate School2022 §1.5 heat-loss policy. Current-focus is merge-stable. Reverify
the final head; after review/merge stop for separate authorization before any
DC2 production publication payload.

## Exact source-input mappings — 2026-09-20

Base PR72 merge: `0322d0a74a0edf53802adc394446011a7d8acc06`.
Continuation authorized by user. Prepared211 school2022 occurrence annotations:
sugar89, carrot69, cabbage24, beet12, rice17. Two suspicious source rows hold
four execution routes. Source evidence confirms polished rice and puree20%.
Immutable corpus0.3.0 and previous packages preserved. No runtime publication.

Verification: eight offline tests (including adversarial authority, mass,
exception, route, summary and manifest changes); two full builds byte-identical.
Independent source audit identified exceptions and validator gaps, now covered.
See [package](../data/curation/dc2-exact-input-mappings/README.md).
Next: review this bounded overlay, resolve nutrient method/reuse and exact
canonical profile equivalence before a separately reviewed production payload.
The user has not yet answered the nutrient-method choice; no approval inferred.


## PR72 review hardening handoff — 2026-09-20

The first DC2 source/form review remains evidence-only. Review blockers were
addressed by expanding CI input triggers, adding fail-closed committed-output
validation for input receipt/routes/summary, and making current-focus valid
before and after PR72 merge. Reverify the final head; after review/merge stop
pending explicit authorization for a production DC2 publication payload.

## Current update — first DC2 batch review, 2026-09-20

PR71 merged at `9b1d5c73da4f1d779336a35e0e7e2c2d32363e85`.
The user authorized the next source/form review stage. See
[first-batch review](../data/curation/dc2-first-batch-review/README.md) and
[current focus](current-focus.md), which supersede older execution statuses below.
25 group decisions account for1532 occurrences and24 source-record candidates;
14 profiles have earlier visual evidence. No publication, accepted canonical
mapping or nutrient-policy change. The next exact blockers are documented in
publication-decisions.md; do not restart source discovery without reading them.


Updated: `2026-09-20`.

## Current handoff after PR70 merge

Accepted main is `b9768984392982bd05d28fc0f7793453fe8378b5` (merged PR #70).
PR #71 is being synchronized and verified for the user-authorized merge.
See [current focus](current-focus.md), [integration plan](../docs/family-food/corpus-v03-integration-plan.md)
and [reconciliation package](../data/curation/corpus-v03-reconciliation/README.md).

The PR70 recovery artifacts and source input hashes are preserved. Its final
head `514c6b1` has the same tree as the historical `c23227b` input pin used by
v0.3 reconciliation. Generated historical merge-status flags remain capture
metadata, not live project state. All current statuses are owned by this section
and current-focus; the receipt below is historical.

Reconciliation retains 547 crosswalk records, 2693 food occurrences and 46
review queues, all without production publication. Exact form/source/rights/
nutrient decisions are next proposed work, not automatically authorized.
After the authorized PR71 merge, stop. DC2/DC3/DC4, Gate1 and PR9 remain open.

## Preserved pre-merge PR70 handoff receipt — historical

The following text records the earlier delivery state. Its REVIEW-READY and
not-merged wording is superseded by the current handoff above.

### Original handoff

Updated: `2026-09-20`.

## Accepted base and governance

Accepted current main:

`d8c76a64483e3d5814e702be33c12cbe2e144160`

Current bounded operation:

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` — ACTIVE under
Issue #67.

Recovered implementation is REVIEW-READY on:

`data/data-corpus-v1-dc1`

Accepted SQLite migration head remains:

`0032_meal_plan_serving`

Reserved future migration remains:

`0033_recipe_template_catalogue`

DC2, DC3, DC4, Gate1-CLOSE and PR9 are NOT STARTED.

## Recovery checkpoint

The inconsistent pre-rebuild GitHub package is preserved for recovery under:

`data/curation/data-corpus-v1-dc1/recovery/pre-rebuild-b7bc19e8881ddc90/`

The exact original pre-rebuild bytes remain available at commit
`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`. The copied recovery README was
later whitespace-normalized only for repository Docs verification; its metrics/data
content was not changed.

Known pre-rebuild commit:

`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`

Recovery checkpoint completion commit:

`0c311848341da397b837abf12fcca4b442de8acd`

The old package is historical evidence only.

## Root cause recovered

The interrupted package consumed a text-rendered spreadsheet view as if it were
the complete v22.5 relationship-row shards.

The raw source contract requires:

`1550 + 1550 + 1550 + 1529 = 6179` rows.

Direct raw-XLSX parsing recovers all 68 candidate families and 991 relevant
source relationship/calculation rows. Missing rendered rows had previously been
misinterpreted as zero ingredient demand.

## Rebuilt package

Evidence package:

`data/curation/data-corpus-v1-dc1/`

Generator and validator:

- `scripts/build_data_corpus_v1_dc1.py`;
- `scripts/validate_data_corpus_v1_dc1.py`.

Current reconciliation:

- 68 candidate families;
- 991 relationship/calculation rows;
- 96 external ingredient identities;
- 33 accepted existing/alias mappings;
- 63 identities requiring later DC2-level closure if pursued;
- full accepted PR39 input contract: 350 recipe rows / 363 ingredient identities;
- structural source-Variant split: 31 one / 37 multiple;
- safe publication-branch split: 5 simple / 63 review-required;
- 33 existing mappings have exact current USDA FDC profile provenance identified,
  but recipe-form suitability remains review-required;
- 28 non-existing identities have a preferred source-family search target;
  exact source presence, record identity and form compatibility remain unverified;
- 35 identities are blocked on identity/form semantics before exact authority
  assignment.

The previous 95-demand result is not retained: it depended on unsafe
display-name deduplication. In particular `ING-0014` and `ING-0069` remain
separate identities; the v22.5/v22.13 label conflict is explicit evidence debt.

## Compatibility limits

For all 68 candidates:

- v22.5 calculation rows match v22.13 `CalcRows`;
- accepted PR #39 mapping aggregates are reproduced;
- v22.5 Variant counts match v22.13 `VariantBlocks`.

Full row-level relationship equivalence is not claimed because the exact
v22.13 row-nutrient shards were unavailable during recovery.

Recorded blockers include:

- 20 candidates with additional v22.13 non-calculation relationship rows;
- 20 used identities with v22.5/v22.13 label differences;
- 63 candidate families needing variant/choice/optional/boundary/compatibility/
  semantic review;
- all 33 existing profiles still need exact recipe-form suitability review;
- preferred source-family search targets are not evidence that a compatible
  source record exists and are not exact-record authority closure;
- assortment gaps in the preserved 68-family funnel.

## Verification evidence

Current review-fix verification:

- exact GitHub package audit: PASS for 68 candidates / 991 relationships /
  96 demands / 33 existing mappings / 63 non-existing mappings;
- safe branch split: 5 simple / 63 review-required;
- full PR39 input metadata: 350 / 363;
- current production nutrition seed metadata: 183 rows and exact Git blob identity;
- DC2/DC3 batch partitions: exact coverage with no overlap;
- authority assignment state present for all 96 demands;
- package SHA-256 manifest: PASS for all 11 generated artifacts;
- committed adversarial harness:
  `scripts/test_data_corpus_v1_dc1.py`.

Current heavy verification applies to the generator/generated-package bytes
finalized on branch head `78c81ff7f55c6878be9112b75f766c78fe73c639` before the following state-only
finalization commits:

- exact repository PR39 mapping inputs restored byte-for-byte: PASS;
- exact production nutrition seed restored byte-for-byte: PASS;
- raw XLSX generator source-hash enforcement: PASS;
- build A: PASS;
- build B: PASS;
- validator A/B: PASS;
- 15-case adversarial suite: PASS;
- build A == build B: PASS.

The generated package at `78c81ff...` is the output of the current generator.
Subsequent finalization commits are state-only and do not alter the generator or
generated package bytes covered by this evidence. Final-head automatic package
verification rechecks checksums, validator behavior and the formatted
15-case adversarial suite.

Raw source XLSX bytes are operator-managed external evidence. Exact required
filenames/hashes are recorded in `source-artifacts.json`. The ZIP/container
hash is diagnostic only; canonical source identity is the exact file set plus
per-file SHA-256. The raw source ZIP must not be uploaded as a GitHub Actions
artifact in this public repository. Automatic PR CI runs package verification;
full raw-source rebuild is manual `workflow_dispatch` against explicit
`target_ref`, using the temporary authenticated URL only through
`DC1_SOURCE_BUNDLE_URL`.

Final Docs verification and automatic package verification must be GREEN on the
review head before merge.

## Scope boundary

No production FoodIngredient/Nutrition/Composition/RecipeVersion publication,
schema, migration, Planner, API or UI change belongs to this PR.

## Stop condition

After DC1 review/merge, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
