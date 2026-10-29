# PR10-CORE Issue #245 — actual fresh fixture drift decision

**Status:** **`NO_GO_EXACT_TWO_STEP_FIXTURE_REPRODUCIBILITY`** on newly obtained persisted CI evidence. The accepted historical recipe week was **not reproduced** on `main`, so the two source steps selected by [PR #244](https://github.com/Mitronomik/family-food-os/pull/244) cannot be validated as the accepted two **current** MealEvents. This docs/evidence-only outcome **does not approve `APPROVED_IMMEDIATE` or PR10-A**.

**Accepted base:** `main@3c4645a27d675bb4464c913785aef3cd88de8681` (PR #244 merged 2026-10-27). [PR #242](https://github.com/Mitronomik/family-food-os/pull/242) was closed without merge.
**Task:** [Issue #245](https://github.com/Mitronomik/family-food-os/issues/245). Compare exact 2026-09-14..20 **historical** synthetic three-member fixture against newly generated current real-application persisted evidence before qualified process/scale eligibility review.
**Machine evidence:** [pinned old/new source/fixture/receipt comparison](pr10-core-two-step-fresh-fixture-drift-2026-10-27.json).

## 1. FACT — two independently retained workflow artefacts compared

| Evidence | Accepted historical PR #196 | Current `main` on PR #246 |
| --- | --- | --- |
| GitHub Actions job | [run 38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826) | [PR10-META run 40495153021](https://github.com/Mitronomik/family-food-os/actions/runs/40495153021), **success** |
| Artifact ID | `11672432141` | `12730572293` |
| JSON SHA256 (bytes extracted from uploaded ZIP) | `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec` | `2caa45e1e50639eef2b6f9023496cbce9fc35a88bd4c71f86e2b8a9daee0c78d` |
| Planner `expected_semantic_pins_sha256` | `2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d` | `1720db1d309a8a346af81cba37e27b07044c205112d6fdd711b938803567bcf2` |
| Persisted Household/MealPlan | **3 members, 21 MealEvents, 42 Servings, 7 days** | **3 members, 21 MealEvents, 42 Servings, 7 days** |
| Event `(local_date,position)` recipe-code matches between runs | — | **0 of 21**, i.e. all 21 recipes in scheduled slots differ |
| E2E source safety and Prep eligibility | NOT EVALUATED | NOT EVALUATED |

**No freshness substitution:** the newly extracted JSON is produced by the existing [`PR10-META persisted fixture evidence`](../../.github/workflows/pr10-meta-fixture-evidence.yml) using real accepted PlannerService and read-back via a **fresh ephemeral SQLite** database under PR #246 HEAD `4dc7b3d5291c22252f5d752a28fba3699f836481`; the entire prior PR #196 artifact is a separately verified historical source. The new CI counts passed, yet its semantic Planner selection did not match PR #196. **Passing 3/21/42 counts or within-run pure Planner replay is not a proof of cross-run historical week identity.** The underlying cause (e.g. seed/IDs/tie-breaking) has **not** been independently proven and cannot be asserted here.

The newly attempted **strict** diagnostic test `PR10-CORE two-step persisted fixture evidence` [run 40495153015](https://github.com/Mitronomik/family-food-os/actions/runs/40495153015) correctly rejected that independently pinned baseline mismatch and **failed**: 26 existing PR10-META tests passed; **13 newly added cases failed at shared fixture setup**, before the candidate negative tests could run. This is **not** a successful two-step validation receipt. The experimental script/test/workflow was **removed from this PR** instead of weakening the baseline or treating the changed current week as the accepted historical fixture.

## 2. Actual two-candidate read-back comparison

| Candidate source first-step | PR #196 accepted historical week | Newly generated current week from CI | Verdict |
| --- | --- | --- | --- |
| `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` — «Творог протереть.» | 2026-09-18 **BREAKFAST**, member Serving factors `2.362341 + 2.746504 = 5.108845` | **Present once but on 2026-09-20 BREAKFAST**, with source-linked factors `2.362341 + 2.746504 = 5.108845`; new ephemeral MealEvent / RecipeVersion / Step UUIDs | **Not the accepted MealEvent/date**, cannot reuse the historically selected event identity as current |
| `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE` — «Перебрать и промыть кукурузную крупу, несколько раз меняя воду.» | 2026-09-19 **BREAKFAST**, member Serving factors `3.422496 + 3.979062 = 7.401558` | **Not selected in any of the 21 current MealEvents**, although its RecipeVersion/Step is present in the current active catalogue | **NO_GO** for the second positive MealEvent |

Historical input-only Decimal projections: `TVOROG_5 139.5 × 5.108845 = 712.6838775 g`; `CORN_GROATS 40 × 7.401558 = 296.062320 g`. The present run independently calculates the **same** cottage-cheese ingredient projection at a **different MealEvent date**, but this does not repair source pin drift. **No current corn-milk MealEvent Serving** exists to project or authorize.

Source steps' literal `instruction_sha256` values remain matching their immutable accepted recipe text when inspected in the current catalogue (cottage `19abb21302cb8b614997da664eeb8afaf2d53e1be0aab3f3821d5aebec34096d`; corn `31805fc2c8e19d61be569f92a54ee91af6c0d703fa00ab9742cf7f9dcf262590`), but the **persisted RecipeVersion/Step UUIDs and full process hashes** belong to this fresh database, not the historical one. This is source identity integrity, **not** a positive same-day action approval.

## 3. Decision — don't relax or silently replace the frozen Gate2 fixture

**FACT:** a fresh current Planner/SQLite receipt with 3 members, 21 events, 42 Servings exists and its source/serving relationship is structurally valid, but it is **not semantically identical** to the week used for the #244 two-candidate discovery. The second target dish is absent. PR #244's valid historical lexical/source inventory was not disproved; it was **never a guarantee of fresh cross-run Planner selection**.

**DECISION (evidence only):**
- `SOURCE_RECIPE_INSTRUCTIONS = HISTORICALLY_VERIFIED`.
- `CURRENT_PLANNER_3_21_42_STRUCTURE = PASS`.
- `HISTORICAL_EXACT_WEEK_REPRODUCTION = NO_GO`.
- `CURRENT_TWO_DISTINCT_TARGET_EVENTS = NO_GO`.
- `INDEPENDENT_APPROVED_IMMEDIATE = 0`.
- `PR10_A_RUNTIME = NO_GO`; `Gate2 = NOT_PASSED`.
- `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=PASS` not established.

**OPEN / one necessary owner decision:** define the accepted **cross-run semantic fixture identity and stabilization strategy** before repeating an eligibility review: either preserve precisely the #244/PR #196 21-event recipe-code/member/Serving semantic snapshot through a deterministic, **versioned synthetic fixture setup**, or formally propose/approve a **new** canonical Gate2 fixture with updated source IDs, both qualified target steps and all negative coverage. This is not authorized merely by the phrase “идем дальше”; requires an explicit Product/Architecture acceptance and independent QA challenge. Changes to Planner tie-breaks, source recipe selection, acceptance fixture, schema or gate must **not** be made silently.

After accepting one tested, independently reviewable fixture identity, run current precise Step/Serving/Household source pin verification, then obtain **named independent Domain/QA process and scaled-home applicability approval** for two genuine same-day actions. Only then proceed with separately accepted D3 trusted publisher/read and rollback-independent revocation, followed by PR10-A. Do not keep hunting recipe pairs or bypass Gate2.

## 4. Verification and preservation

- Downloaded and byte-hashed **both retained GitHub Actions JSON artifacts** through official workflow-artifact downloads, compared all 21 positions by actual source RecipeVersion→canonical code mapping, and validated 3/21/42/51 catalogue counts and both target occurrence joins. No historical generated UUIDs were copied as new current ones.
- Current existing PR10-META workflow **SUCCESS**; experimental strict newer candidate workflow **FAIL** due expected independent fixture semantic mismatch; its transient evidence script/tests/workflow **not retained in this docs-only PR**. Static receipt JSON and relative links remain for independent docs review; exact-head Docs verification after final changes required.
- No mutation of source or user data, no production code, no new data-authority reader, source eligibility package, Prep runtime, schema/migrations, APIs, Shopping/Pantry/PDF/PWA, storage/freezer rule or medical/nutrition assumption. `AI_ENABLED=false` invariant remains.
