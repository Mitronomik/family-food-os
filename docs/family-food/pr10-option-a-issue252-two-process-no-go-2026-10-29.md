# Issue #252 — two fresh real-Planner executions, source-pinned NO-GO (2026-10-29)

**Status:** **`NO_GO_CURRENT_UNSTABILIZED_SEED`**. This is **not** `NO_GO_OPTION_A_UNACHIEVABLE_AS_SCOPED`: the approved test-only ID binding was **not** implemented or demonstrated by this bounded first diagnostic. It is also **not** a Gate2/Prep pass. **PR #254 is explicitly a negative-evidence PR**; its CI is only allowed to report that the observed NO_GO is independently and truthfully reproduced, never that the original Option A 21×42 week has been regenerated.

**Task:** [#252](https://github.com/Mitronomik/family-food-os/issues/252) remains OPEN for the original positive fixture goal; [PR #254](https://github.com/Mitronomik/family-food-os/pull/254) contains only the negative-evidence checkpoint.
**Accepted initial base:** `main@794302534a9f02a8452892aef62375daf0a13de2`.
**Runner/workflow:** [GitHub Actions run 40897666121](https://github.com/Mitronomik/family-food-os/actions/runs/40897666121) at code HEAD `900c353fa33ab31f5a221f4c252d797af8e5bfb8`, [artifact 12907507093](https://github.com/Mitronomik/family-food-os/actions/runs/40897666121/artifacts/12907507093) (expires 2026-11-28). The CI job **FAILED intentionally at semantic reproduction** (exit 3), after **14/14 independent adversarial tests, Ruff and Ruff format PASS**; no missing dependencies or test syntax errors.

## FACT — independent raw source preservation

All three raw CI files below were downloaded from the real Actions ZIP, independently byte-hashed, then published to this PR's repository evidence directory. GitHub blob hashes were fetched back and match the original downloaded raw file bytes.

| File / meaning | Raw JSON SHA-256 | Git blob SHA-1 |
| --- | --- | --- |
| [Run 1 actual full persisted receipt](evidence/pr10-option-a-issue252-2026-10-29-run1.json) | `87789288aadfeca6f2a3bd4ec63cb1c69d19630df0d8dce933928224979a53b5` | `ad6982e0aeeaf1e9c3f7d609f2bf1d3ac99d6ca9` |
| [Run 2 actual full persisted receipt](evidence/pr10-option-a-issue252-2026-10-29-run2.json) | `b8c90d753447e4781b97f6e3207ca29d8809919c1e1b546ac1813ca3a0d7c4c5` | `fb9c905b0ecfc68c2d1f0e2d11d08be77ad1430e` |
| [Machine result (two processes)](evidence/pr10-option-a-issue252-2026-10-29-report.json) | `7ef0ba589c09bdb43e2d68b6a938937bedc4f2de21a118fc0f39e3bec8decf79` | `7f722e5d31f60e618553fb5712f10bf4134def74` |

**Independent original reference:** [accepted PR #196 historical raw JSON](evidence/pr196-original-synthetic-fixture-receipt.json), **110511 bytes** / SHA256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`; original UUID-free week SHA256 **`731ef32e7137740ed5b46a6044a85d8b2f818a847fdc039842460d442df5aeb6`**. The reference itself is never changed by this task.

## FACT — true two-process result and scope

Each subprocess executed the **existing** `scripts.audit_pr10_meta_gate2_fixture.build_fixture_receipt(DatabaseConfig(path=fresh_temp_sqlite))`, which calls the unchanged `PlannerService.generate_authoritative` and verifies actual MealPlan persistence and independent current-plan readback before creating its receipt. Two independent Python interpreters and SQLite databases, not a snapshot reconstruction, were used; production ranking/candidate filtering and source-corpus seed code were not modified.

| Check | PR #196 trusted original | New run 1 | New run 2 |
| --- | --- | --- | --- |
| Structural counts | 3 members / 21 MealEvents / 42 Servings | 3/21/42 PASS | 3/21/42 PASS |
| Exact historical date/position source recipe matches | 21/21 | **0/21** | **1/21** |
| Complete per-slot source + member Decimal semantic match | 21/21 | **0/21** | **1/21** |
| Active catalogue source identity and ordered Step-content equality | baseline 51 | **51/51** | **51/51** |
| Source active RecipeVersion UUID equal to historical | baseline | **0/51** | **0/51** |
| UUID-free canonical SHA256 | `731ef32e…` | `4c1c574c26b5262edd64687cde292f16ecfc262111233bf60ad003cfbd47fb0f` | `a7948dcc11e36131b11cd4397436ba30b9257a5b344d928d6430023258d36f04` |
| Actual persisted readback | historical PASS | PASS | PASS |

Only **1/21** scheduled recipe slot matches between the two *new* runs themselves. Both contain 21 distinct selected recipes and maintain existing synthetic scope/blocked-gate status. No production Planner/RecipeVersion/DB/MealPlan changes were committed.

**Verification method:** sort 21 MealEvents by `(local_date, position)`, resolve current RecipeVersion UUID to accepted canonical code/source recipe ID/version/source-document SHA via the same **current persisted** 51-recipe receipt, map each member UUID to its test `fixture_ordinal`, attach exact six-decimal Serving strings sorted by ordinal; JSON `sort_keys=True, ensure_ascii=False, separators=(',', ':')` UTF-8, SHA256. This is independent of transient UUIDs. A parallel independent Python implementation re-hashed both downloaded run files and matched the machine result. Source identity/Step order comparison omits ephemeral step IDs and run-local `process_hash`.

## FACT / ASSUMPTION / OPEN

**Independent feasibility inventory:** [test-only ID propagation and historical PlannerRequest review](pr10-option-a-issue252-test-only-id-feasibility-review-2026-10-29.md) documents the complete nested seed/composition dependency, role-sensitive UUID creation and original-input gaps. The missing end-to-end safe factory seam is not repaired by changing normal Planner defaults; a separate reviewed implementation gate and explicit owner approval is necessary if that seam changes production-facing service composition.


**FACT:** historical and current `backend/app/domain/planner.py` blobs are identical (`7793e6d55f475b06b15e01e902e3144e3f5d1944`), as are the historical/current fixture builder script `scripts/audit_pr10_meta_gate2_fixture.py` and DC4-A3/R3A/R3B/R3C/R3D seed implementation blobs. `FoodRecipeCatalogueService` accepts `id_factory`, but `create_food_recipe_catalogue_service(engine)` and nested seed entrypoints do not pass an ID factory through. No end-to-end historical identity binding seam is proven.

**FACT:** historical versus current `backend/app/services/planner.py` differs: original `list_active(limit=200) + get_current_verified` candidate read was replaced with `list_all() + active filtering + skip unavailable nutrition`. The final 51-member source catalogue matches by source identity/steps; **candidate scoring and original input-level parity are not independently proven equal**. There is no standalone archived original `PlannerRequest` containing exact target energies, memberships, source UUID ordering, nutrition projections and exclusions.

**ASSUMPTION, NOT DECISION:** randomized RecipeVersion UUID tie-break likely contributes to run-to-run recipe choice, but the evidence **does not prove it is the sole cause** or that a permitted factory seam can recreate PR #196 without changing production behavior.

**OPEN / STOP:** approved Option A needs a **separately reviewed, minimal test-only identity/seed injection seam**, full historical input reconstruction and *two new real Planner persisted runs* matching `731ef32e…`. Existing general-purpose service factory and nested seed chain do not currently expose that seam. Do not force codes/Servings into snapshots, monkeypatch global UUID, change Planner tie-break/weights/candidate pool, modify source rights/quantities, or pretend a negative fresh week is a positive fixture proof. If the seam requires unapproved production changes, stop with `NO_GO_OPTION_A_UNACHIEVABLE_AS_SCOPED` and request a new owner decision.

**Non-goals / release:** `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME`, D3 publisher/anti-rollback, Gate2, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. The synthetic diagnostic is never user/real-family planning authority.

## Verification / review / follow-up

- Test-only [probe](../../scripts/pr10_option_a_probe.py) + [14 offline adversarial checks](../../backend/app/tests/test_pr10_option_a_probe.py) + [dedicated workflow](../../.github/workflows/pr10-option-a-two-process-probe.yml).
- The real probe **intentionally exits 3** on semantic NO_GO. The **negative-evidence CI wrapper** checks for that exact return code, two independently generated persisted receipts, raw SHA, source+Step parity, unchanged external reference and `NO_GO_CURRENT_UNSTABILIZED_SEED`. Only when these verifications all pass does this **evidence-only** job succeed. This is *not* weakening the positive Option A PASS condition: if the test unexpectedly returns a positive fixture or infrastructure failure, the negative-evidence job itself fails. The historical red CI run remains an immutable artifact of the first experiment.
- PR #254 may become **review-ready solely as NO_GO evidence** after exact-head green CI and independent review; it is **never** a merge-ready positive Option A fixture implementation. The original Issue #252 remains OPEN and its acceptance unmet. Reviewers must challenge inputs/normalization/source rights and the missing factory seam; no automatic merge or milestone transition.
