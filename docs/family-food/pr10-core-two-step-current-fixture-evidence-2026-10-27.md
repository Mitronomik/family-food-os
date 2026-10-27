# PR10-CORE — exact two-step persisted fixture read-back gate (Issue #245)

**Status:** DIAGNOSTIC EVIDENCE ONLY; `APPROVED_IMMEDIATE=0`; `NO_GO_TO_PR10_CORE_RUNTIME`. New exact-head CI receipt required and external qualified Domain/QA approval not provided by this PR.
**Accepted main:** `3c4645a27d675bb4464c913785aef3cd88de8681` ([PR #244 merged](https://github.com/Mitronomik/family-food-os/pull/244), 2026-10-27T10:47:49Z); [PR #242](https://github.com/Mitronomik/family-food-os/pull/242) was closed without merge.
**Task:** [Issue #245](https://github.com/Mitronomik/family-food-os/issues/245). Only the R2-E cottage-cheese casserole first step and R3-B corn-milk porridge first step from the accepted historical 21-event synthetic week. No new candidate search, source publication, planner change, migrations or Prep runtime.
**Sources:** [21-event/87-step source triage](pr10-fixture21-action-class-review-2026-10-23.md), [historical PR #196 fixture contract](pr10-meta-gate2-fixture-evidence.md), [D3 eligibility/anti-rollback](pr10-core-step-eligibility-d3-contract-2026-10-22.md), [Option B positive/negative technical Gate2](pr10-option-b-staged-delivery-gates-2026-10-17.md).

## 1. Why a new persisted fixture is needed

The merged [#244 source receipt](pr10-fixture21-action-class-triage-2026-10-23.json) includes 21 recipe codes, 87 ordered steps, a minimal candidate pair and manifest blob pins, but **does not include fresh current MealEvent IDs, member Decimal `Serving.portion_servings` or freshly read RecipeStep UUID/hash**. Historical generated IDs cannot be copied into a present production database.

An independent previous [PR #196 GitHub Actions run](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826) yielded a **retained, downloadable** short-lived persisted three-member synthetic fixture artifact `pr10-meta-synthetic-fixture-receipt` (artifact 11672432141; JSON SHA-256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`). Its independent **Planner semantic SHA-256** is `2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d`, tied to the historical approved synthetic Planner selection (3 members / 21 events / 42 Servings / 7 days). That digest is an **independent baseline** used to reject a changed fixture, NOT a reusable identity for current MealEvent/Step UUIDs.

Reading that retained **historical** artifact now provides two pinned sample events, under no circumstances asserted to be the new CI run:

| Historic MealEvent only | Historic member Decimal factors | Source base quantity | Derived historic net input |
| --- | --- | --- | --- |
| 2026-09-18 `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` (BREAKFAST) | `2.362341 + 2.746504 = 5.108845` | `TVOROG_5` `139.5 g` / 1 source serving | **`712.6838775 g`** research projection |
| 2026-09-19 `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE` (BREAKFAST) | `3.422496 + 3.979062 = 7.401558` | `CORN_GROATS` `40 g` / 1 source serving | **`296.062320 g`** research projection |

These are *input-ingredient Decimal multiplications*, **not** validated physical kitchen capacity, individual portion adequacy, energy suitability or a safe prepared yield. Different fixtures may mint different UUIDs; the workflow is designed to **fail** if independently pinned Planner semantics change unexpectedly.

## 2. New evidence tooling (no production code)

**Reused unchanged:** `scripts.audit_pr10_meta_gate2_fixture.build_fixture_receipt` creates a fresh temporary SQLite DB, seeds accepted source recipes, constructs three heterogeneous member patterns, calls actual `PlannerService.generate_authoritative`, reads back 21 persisted MealEvents and 42 individualized Servings with `AI_ENABLED=false` and checks independent Planner semantics and source catalogue pins. No live user database is used.

**Added:** [`scripts/audit_pr10_core_two_step_fixture.py`](../../scripts/audit_pr10_core_two_step_fixture.py) selects the exact current MealEvents by independently verified `RecipeVersion.canonical_code`, date and breakfast role, then joins their **current** immutable `recipe_version_id` and first ordered `recipe_step_id` / instruction SHA-256 / full process hash to member Serving rows. It resolves precise source-based `TVOROG_5` (139.5 g) and `CORN_GROATS` (40 g) from R2-E/R3-B **trusted Git-blob-pinned** manifests with the expected School2022 original PDF SHA/rights/version, and calculates source grams × each `Decimal` member factor and total. No LLM, regex promotion, rounding or prose-based ingredient quantity.

**Adversarial / reproducible tests:** [focused pytest](../../backend/app/tests/test_pr10_core_two_step_fixture.py) checks exact 3/21/42 counts, independently accepted Planner baseline, true two-event source/Step/Serving joins, all per-member amounts, current hashes, source manifest tampering, forged approvals, out-of-fixture IDs, `NaN`/infinite/invalid source amounts, and no possible `APPROVED_IMMEDIATE` promotion. Existing full PR #196 fixture tamper tests also run.

**CI:** [`pr10-core-two-step-fixture-evidence.yml`](../../.github/workflows/pr10-core-two-step-fixture-evidence.yml) installs only the accepted backend[test]/Ruff environment, runs focused existing and new tests, regenerates an **ephemeral fresh fixture and per-event review receipt on the exact PR HEAD**, checks that the gate remains NO_GO and uploads **both** JSON files as one time-limited evidence artifact. The output's full SHA-256 and independently printed Planner semantic SHA must be compared to the CI run; a self-contained JSON hash alone is not a signature. This document does **not** claim the new artifact exists until successful CI is inspected.

## 3. The exact independent two-step reviewer packet

| Event/Step requiring review | Independent process and input scope | What is withheld |
| --- | --- | --- |
| R2-E `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` Step 1, «Творог протереть.» | Check current immutable `TVOROG_5` form, exact source quantity/real member scaling, whether *rubbing the whole step* is useful and feasible same-day without inventing equipment, time, intermediate form/output or holding | `numeric_direction_classification` and `immediate_same_day_eligibility` remain **PENDING / UNAPPROVED**; no accepted rendering or mass rounding |
| R3-B `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE` Step 1, «Перебрать и промыть кукурузную крупу, несколько раз меняя воду.» | Confirm `CORN_GROATS` source grain form and exact member scale, practical relevance and source-valid immediate prep; **rinsing water is not the recipe's measured 68 g cooking water** | No inferred rinse water grams, soak time, safe advance preparation, equipment/humidity/storage instruction or saved operation |

**Independent Domain/QA reviewer** (different from the original curator/evidence author) must issue separate version/source/hashes and **numeric class** vs **same-day actionable eligibility** verdicts for both **entire** instructions, with reviewer identity, evidence, timestamp, context and revocation. This is not automatically achieved by a CI-success receipt or a class keyword. A negative unsupported whole step remains unresolved. The status reader must later authenticate an immutable trusted eligibility publication and check rollback-resistant **current** permission before every executable admission, per D3 §4.1. No production eligibility payload exists yet.

## 4. Acceptance / negative controls / next explicit gate

**Current evidence publication result:** `TWO_SOURCE_STEPS_PINN_NOT_APPROVED` *only after successful exact-head CI readback*. Until the CI run passes, treat the new current fixture proof as **PENDING_EXECUTION**; the historical artifact remains independently attested but dated.

**Positive research acceptance:** two real current MealEvent IDs on distinct dates; correct RecipeVersion/Step hashes, source/rights, actual member IDs/factors and exact ingredient projections; zero semantic deviations from independent Planner expected pin. This **does not** assert two executable PrepTasks.

**Negative adversarial acceptance:** tampered member or out-of-Household Serving, wrong RecipeVersion/Step/hash or source manifest blob, one missing event, no independent reviewer, forged `APPROVED_IMMEDIATE`, numeric/UNKNOWN source and unavailable/revoked policy remain NO_GO. `ALL_UNKNOWN` and `ONLY_ONE_APPROVED_EVENT` technical Gate2 negative branches must be evaluated when trusted Prep runtime exists; this evidence script cannot truthfully execute those absent services.

**Next after independent review and owner approval:** a qualified reviewer accepts/rejects these two full source processes for actual family-scale same-day use. If **both** pass and publisher/read trust implementation contract is approved, deliver the separate D3 eligibility source/reader (including rollback-independent revocation and fail-closed) **before** PR10-A. If one fails, report a bounded NO_GO and request an explicit new product decision; no third recipe hunt or silently weaker Gate2.

**Preservation:** original RecipeVersion/Step texts/ingredients unchanged, source/rights immutable, no Planner/Nutrition/Shopping/Pantry/Prep production runtime, no schema/migration, no Household user data, no safe storage/freezer/reheat or cooking-time claims, no new current-stock assertion. `NO_GO_TO_PR10_CORE_RUNTIME`, `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=PASS` still unproven, and full technical Gate2 remains untested.
