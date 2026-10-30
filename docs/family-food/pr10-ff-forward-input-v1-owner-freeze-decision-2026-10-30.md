# PR10-FF forward A/B v1 — owner test-only input freeze decision

**Decision date:** 2026-10-30. **Status:** OWNER-ACCEPTED **CONDITIONALLY**, effective only after exact bytes are durably committed, independently verified, this PR is reviewed and merged. Not an independently approved Planner output.

**Accepted owner direction:** after independent [PR #266 raw A/B review](https://github.com/Mitronomik/family-food-os/pull/266), approve the **specific original unmodified JSON bytes and raw SHA** for a **strictly technical synthetic energy-only** experiment. Preserve all restrictions; continue to the distinct genuine two-process Planner proof only after accepted immutable inputs.

**Tracking:** [PR #267](https://github.com/Mitronomik/family-food-os/pull/267) (source/input freeze only). Tool PR [#266](https://github.com/Mitronomik/family-food-os/pull/266) remains a **separate** review/merge decision. Accepted source commit `main@0d390bdf0d620f711916287cf0d656aa9c8a6844`. Exact reviewed materializer HEAD `02cc171d697359644a5638e1ac3e935d3d9e9ae2`.

## A/B immutable content and independent provenance

| Input | Exact retained artifact | Original raw byte count | Verified raw SHA-256 | Verified Git blob SHA-1 |
| --- | --- | ---: | --- | --- |
| A — Source publication/identity, 51 original v1 + seven corrected v2 | [publication-A-PROPOSED.json](evidence/pr10-ff-forward-input-v1/publication-A-PROPOSED.json) | 889601 | `d160b995b680d11cf9e04f3f97c0d01cd1c65ecd2518e685b8e3cfa783e0a885` | `27f6ea8284b30785fe3c0fd512b3963b1166efb9` |
| B — Complete proposed current Planner input for synthetic 2026-11-02..08 | [planner-B-PROPOSED.json](evidence/pr10-ff-forward-input-v1/planner-B-PROPOSED.json) | 67963 | `9a9260a4a8d849fa4284ff64b861d8c2db74d15777b04ca5d3741d25f1f0089f` | `d2dd93987ec48109a73cbf1c7efe0ac0a56d9bbe` |

**External immutable metadata:** [frozen-input-v1-pins.json](evidence/pr10-ff-forward-input-v1-pins.json), not embedded in A/B and not created by the input generator. Stage-membership canonical SHA-256 `47cfbc6b69b5b73bb2c79c133befe08181b1a4aaa2259f90940fd78369737774`, source commit and Git blob hashes are pinned independently.

**Independent verification:** raw ZIP from [workflow 41068645092 / artifact 12984476386](https://github.com/Mitronomik/family-food-os/actions/runs/41068645092/artifacts/12984476386) was downloaded, and A/B raw UTF-8 SHA-256 plus Git blob SHA-1 were computed **outside** the generating job. A separate read-only CI job regenerated proposals using the exact reviewed #266 HEAD and compared those against the externally pinned hashes and stage inventory. A subsequent write-only CI job persisted *exactly* the two files, without executing them, to this feature branch. **Independently fetched actual committed GitHub blob IDs then matched both original expected Git blob SHA-1 values**. The temporary elevated-permission workflow was **removed** after this verification; it is not part of the intended merged tree.

The raw files deliberately retain their original filenames ending `-PROPOSED.json` and A's literal `review_reference=PROPOSED / reviewer must pin raw bytes externally`. Modifying them to claim approval would change their SHA and violate this decision. **The external pin record and this owner decision confer the limited acceptance, not a textual claim inside the source files.**

## What the decision permits — and what it does not

**Permitted after freeze PR merge:** use these *unchanged* exact A/B raw input bytes as the sole input reference for a separately authorized **two independent fresh Python+SQLite** technical proof via unchanged real `PlannerService.generate_authoritative`. Each process must assemble its own real Household, current source and complete candidate authority, persist through existing repository/UoW, read back all 21 genuine MealEvents and 42 exact finite six-place Decimal Servings, and independently compare every source/role/date/position/member/portion semantic field. No output-derived input tuning, no hand-built MealEvents or selected recipe lists, no Planner scoring modifications, no global UUID monkeypatch.

**Not permitted:** marking the generated week reproducible before two independent process receipts match and are reviewed; automatically claiming D3, Prep, safe batch, Gate2, full nutrient/protein/fat/carbohydrate coverage or release authority. This input freeze approves **technical kcal-only Planner evidence**, not a nutritionally comprehensive or clinically suitable meal plan.

**Known limitations retained:**

- 51/51 input candidates are `exact_energy_ready=true` but `nutrition_status=INCOMPLETE`; no conclusion about complete macronutrient/micronutrient or member portion plausibility. Do not hide, replace or upgrade UNKNOWN without authoritative data.
- FoodIngredient and CUSTOM selection UUIDs are run-local bindings in the separate witness; current Planner uses RecipeVersion/Member UUIDs for tie ordering, while selection identifiers appear in Planner trace/allocation metadata. **No real two-process output proof exists**; any differing semantic choice is `NO_GO_FORWARD_FIXTURE_UNSTABLE`, not a request to reroll inputs.
- Rights/RecipeVersion/Steps are matched to the accepted source evidence and 30 critical Git blob pins; this is **not** a new legal review of external recipes. Any source rights or nutrition revocation invalidates future *current authority* until separately reviewed.
- Historic #196 original week and #254 negative evidence remain immutable, unmodified and not the comparison target for the *forward* new technical fixture.

## Acceptance / reviewer checklist for this PR

1. Source A and logical B physically present in Git history with expected **exact raw bytes**, raw SHA-256, byte counts and Git blob SHA-1; independently fetch from this PR and validate.
2. No temporary write-permission workflow survives in the PR diff; no source, domain, Planner, Recipe, Nutrition, schema, API, UI, data-corpus or production flag changes.
3. Review scope and exact-head docs/static checks PASS; explicit independent Architecture/Data/QA and owner merge decision remain required.
4. **Only after merge:** close the raw input pin/evidence entry gate (not reproducibility gate), and start *another* narrowly scoped task to prove or reject two-process real Planner semantic equality.

**Until this PR is merged**, keep `NO_GO_INPUT_MANIFEST_UNVERIFIED` and `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`. Other hard gates stay unchanged permanently until their own acceptance: `NO_GO_TO_PR10_CORE_RUNTIME`, `APPROVED_IMMEDIATE=0`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. No autonomous PR #266/#267 merge or production release.
