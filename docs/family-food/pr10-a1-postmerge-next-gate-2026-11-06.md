# PR10-A1 post-merge closure and next authority gate — 2026-11-06

**Status:** `POST_MERGE_VERIFIED / NEXT_CONTRACT_PREFLIGHT_PROPOSED / NO_RUNTIME_AUTHORIZATION`.
**Accepted main:** `80ddc7ba95673681cce2f62b6294ebe0de3f5946`, merged [PR #281](https://github.com/Mitronomik/family-food-os/pull/281), 2026-11-06.
**Task:** continue after the independently merged read-only Planner → Shopping → Prep proof by identifying a single useful *next gate*, without silently starting executable PR10-A2, D3 publication or changing data authority.
**Type:** docs/state-only implementation-readiness and product gate assessment, not runtime code or release.

## 1. Verified result and limits

- [PR #281](https://github.com/Mitronomik/family-food-os/pull/281) merged at the accepted commit above; the accepted PR head was `f3bb53a8b2e45c4f7d91c654b544e5ff608f084d`. Its [exact-head CI](https://github.com/Mitronomik/family-food-os/actions/runs/42256126898) reports **90 passing tests** and Ruff lint/format PASS; [Docs verification](https://github.com/Mitronomik/family-food-os/actions/runs/42256127054) PASS.
- [Retained raw JSON/JUnit artifact](https://github.com/Mitronomik/family-food-os/actions/runs/42256126898/artifacts/13521863262) has `unresolved_step_count=27`, with 27 unresolved reason entries, not 28. Both `source_ingredient_quantities` (35 event-level rows) and `shopping_gross_pantry_net` (10 aggregate rows) carry `food_code` **and** `food_ingredient_id`; matching identity-pair sets allow independent joins. The receipt confirms the test-only comparison flags: exact source gross vs Shopping's 0.001 CEILING aggregate, Pantry reduces purchase but not source demand, and SQLite dump unchanged during read-only calculation.
- These counts and identifiers refer only to the **one synthetic CI run**, not the accepted owner-frozen `PR10_FF_FORWARD_3M_7D_V1` week and not a real household. The prior owner-frozen 3-member/7-day/21-event/42-Serving energy-only proof remains unchanged.
- In the PR #281 test, `CapturedGenerationContext` is explicitly recorded **before** planning and cross-checked against PlannerTrace, current Household and current persisted MealPlan. The existing persisted Household/MealPlan records do **not** independently provide durable semantic member ordinals or complete per-member food exclusions after a fresh process restart. A caller with only a persisted plan must therefore be `BLOCKED`, not synthesize empty exclusions or infer ordinals from UUIDs.
- `PrepDiagnosticStatus.INCOMPLETE`, `executable_tasks=()`, `APPROVED_IMMEDIATE=0`, executable/persistent `NO_GO_TO_PR10_CORE_RUNTIME`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`, and Gate2 NOT PASSED all remain. No current independent whole-Step eligibility, D3 trusted publisher/live anti-rollback reader or source-approved positive tasks exist.

## 2. Why the next engineering milestone is not immediately executable

| Boundary | Present evidence | Missing authority / potential failure |
| --- | --- | --- |
| Planner generation | Real `generate_authoritative` and SQLite persisted/readback in isolated test | Independently durable authoritative member exclusion and semantic-order witness for arbitrary restart |
| Source recipe and food | Pinned immutable RecipeVersion/structured ingredients and canonical FoodIngredient in test | No automatic promotion of test-local IDs or frozen energy-only fixture to production source/food authority |
| Shopping | Deterministic gross + Pantry-net comparison | Receipt equality does not authorize Prep/stock writes or infer prices/supply |
| Prep A1 | Deterministic unrounded per-event quantities, reviewed reason codes and zero tasks | No approved executable Step, D3 live status/revocation/rollback authority or real kitchen applicability |
| Candidate A corrective source | Existing [one-recipe immutable successor contract](pr10-candidate-a-successor-publication-contract-gate-2026-11-03.md) | Actual target DB readback, qualified process/nutrition review, owner consent and safe replay remain unavailable |
| Gate2 / release | [Option B staged gates](pr10-option-b-staged-delivery-gates-2026-10-17.md) and [A1 sequencing](pr10-pure-calculation-sequencing-amendment-2026-11-02.md) | Two distinct genuinely positive actionable MealEvents plus honest negative, full reviewed persisted Shopping→Prep→PDF and all independent release gates |

## 3. Proposed *next bounded task*: generation-context readback authority contract

**Business purpose:** make the next integration seam honestly usable after a process restart without altering source facts, inventing exclusions or admitting unsafe Prep actions.

**Current disposition:** `GO_TO_READ_ONLY_AUTHORITY_PRE-FLIGHT_ONLY`, not `GO_TO_IMPLEMENTATION`.

**The next separately authorized operation** should produce one bounded architecture/data contract and executable negative-test specification for a trusted, complete *generation-context witness* bound to one current Household/MealPlan revision. It must inventory actual storage and service boundaries before choosing persistence, migration, signed sidecar or other deployment mechanism. No new table or external service is approved here.

Required readback contract to evaluate:
1. **Identity:** Household ID, MealPlan ID/current revision, week, Planner config/policy revision and accepted member-selection pins; use real current readback, not test-generated UUID order.
2. **Member meaning:** explicit semantic member-slot ordering originating from the accepted generation command or an owner-approved persisted source; never reconstruct from UUID, display name or demographics.
3. **Exclusions:** an explicit complete per-member exclusion set tied to that generation event (including intentionally empty sets with their own provenance), canonical food identity/source version and deterministic normalization. Missing set is not an empty set.
4. **Provenance/freshness:** accepted generation-request snapshot or other authorized origin, PlannerTrace cross-check, current plan/source/version/Serving fingerprints, revision transition and invalidation on replan.
5. **Access/data ownership:** Household isolation, actual read/write owner, permitted lifetime/retention, non-PII evidence, offline/stale handling, and monotonic constraint-preservation rules where relevant.
6. **Failure semantics:** wrong Household, stale or replaced revision, unbound member, ambiguous ordinal, missing/excluded food, changed trace/config/Serving/RecipeVersion or missing witness → typed `BLOCKED` / zero executable tasks / zero writes; never repair source by deduction.

**Decision options to compare, not pre-approve:** A) a versioned application-owned generation witness persisted atomically with accepted MealPlan; B) a separately trusted, immutable evidence store with independently verifiable attachment to the exact plan revision. Both require an authority/dependency inventory, transaction and crash/restart tests, security/privacy analysis and explicit approval if schema/deployment changes.

**Minimum read-only verification cases for the next task:** fresh process with authoritative witness succeeds on same pinned revision; restart without witness fails closed; shuffled UUIDs do not alter ordinal meaning; deleted/changed exclusion fails; stale revision/replan cannot reuse earlier witness; wrong Household/Serving or altered PlannerTrace rejects; no writes in any failure; full replay produces stable semantic result; no `executable_tasks` regardless of success.

**Ownership:** Architecture + Planner/Household data owner decide where durable generation truth belongs; Prep consumes a validated typed snapshot, never constructs missing truth. A change to persistence, authority, deployment or signing remains an explicit high-coupling decision gate.

## 4. Parallel dependency — keep source review and D3 genuinely independent

After the generation-context contract, **no automatic transition** to PR10-A2. The source and action gates remain separately blocked:
- [Issue #275](https://github.com/Mitronomik/family-food-os/issues/275): the two *actual frozen forward-week* Step 1 candidates still require exact live recipe/Step binding, qualified whole-process source/form/scale review and independent disposition; Candidate A's weakened historical Step 4 is a distinct immutable-correction problem, not a reason to mutate old v1.
- [D3 eligibility contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md) and [bounded reader handoff](pr10-core-two-step-publisher-reader-acceptance-2026-10-23.md): future approved Step eligibility must be independently reviewed and bound to source/Step/revision/hash, with live **rollback-independent** policy/revocation status. A locally matching receipt hash or an old release alone cannot authorize a task.
- [Option B Gate2](pr10-option-b-staged-delivery-gates-2026-10-17.md): two distinct positive MealEvents, legitimate unresolved negative, all-UNKNOWN fail case, and the reviewed end-to-end persistence/API/PDF chain remain unchanged. Confirmed cooked batch/food safety, portion release and real family use are separate gates.

## 5. Review/decision contract

**Acceptance for this docs-only operation:** verify merged #281 exact HEAD and CI evidence; preserve 27/35/10 run-scoped quantities; enumerate the missing production durable witness; separate diagnostic A1, D3 permission, Candidate A correction, Gate2 and release; select exactly one *next preflight proposal* without architecture mutation.

**Not authorized:** backend code, fresh production DB reads, migrations, schema, D3 publisher/reader, Step approval, PrepPlan/Task/Pantry stock changes, API/UI/PDF, new release gate, Gate2 promotion, real household or runtime AI.

**Decision requested after independent Architecture/Data/Domain/QA review:** approve or reject **one bounded read-only generation-context authority preflight**. Only its accepted result can justify a separate implementation design/authorization. The fact that #281 merged does not itself authorize PR10-A2 or production restart-readback.

**Status:** `POST_MERGE_VERIFIED`; `NEXT_PREFLIGHT_PROPOSED`; `NO_GO_TO_EXECUTABLE_PREP`.
