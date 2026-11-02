# PR10-FF — independent final evidence review of merged PR #269

**Date:** 2026-11-02  
**Scope:** read-only Architecture/Domain/QA verification of the *technical synthetic energy-only* forward Planner reproducibility fixture; docs-only state reconciliation.  
**Review verdict:** `PR10_FF_FIXTURE_REPRODUCIBILITY_REVIEW=PASS`.  
**Project gate:** `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN` pending **separate explicit owner acceptance** of the reviewed fixture/digest. A passed technical evidence review does not itself grant PR10 runtime, D3, Prep, Gate2, safe-batch, or portion/release permission.

## FACT — accepted repository and authority

- [PR #269](https://github.com/Mitronomik/family-food-os/pull/269) is merged into `main` at `366f40d9dc3a69b44e2262e18d6a4b407b0371de` (2026-11-02T09:36:45Z), from head `a73b8d850d92cba0c799621f3b07fe13dc7897b7`; [Issue #268](https://github.com/Mitronomik/family-food-os/issues/268) is closed.
- PR #269 changed only `.github/workflows/pr10-ff-two-process-proof.yml`, `scripts/pr10_ff_two_process_proof.py`, `scripts/pr10_ff_proof_evidence.py`, `backend/app/tests/test_pr10_ff_two_process_proof.py`, and three `state/*` files. No production Planner/Recipe/Nutrition/DB/schema/API/UI/seed/frozen A/B changes.
- Frozen A and B remain the exact [PR #267 owner-accepted technical-only input pins](evidence/pr10-ff-forward-input-v1-pins.json): A raw SHA256 `d160b995b680d11cf9e04f3f97c0d01cd1c65ecd2518e685b8e3cfa783e0a885`, Git blob `27f6ea8284b30785fe3c0fd512b3963b1166efb9`; B raw SHA256 `9a9260a4a8d849fa4284ff64b861d8c2db74d15777b04ca5d3741d25f1f0089f`, Git blob `d2dd93987ec48109a73cbf1c7efe0ac0a56d9bbe`. Their unchanged names ending `-PROPOSED.json` do not supersede the external pin/owner decision.

## Independent raw evidence examination

Source: final-HEAD [GitHub Actions run #41309700338](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338), actual [raw ZIP artifact #13084512933](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338/artifacts/13084512933), originally uploaded 2026-11-01; artifact retention expiration 2026-12-01. Independently downloaded and unpacked the original ZIP, not just re-used the CI summary. ZIP SHA256: `6a9943ed1819231ac6bb52005b9b8b8af8e912749efa98d4260b46f2a9bb7fb2`.

Raw files and independently computed raw SHA256:
- `process-1.json`: `cdff1e29ecfd7bf92820e4fd7898b272cc10d8a3e5e937b44849ba5daf667ef7`, 122583 bytes.
- `process-2.json`: `ebe4f83f185028cd18c25f5a586500831729bef6af4539bcc7010cc963d532a4`, 122583 bytes.
- `comparison.json`: `3509af682c9bb8f3d65e6c6b53de4d7547ca2c0d7c759f64b24526cd7fed9fcc`, 705 bytes.

Independently canonicalized each extracted JSON payload with UTF-8, sorted keys, compact separators and non-ASCII retention; SHA256 digests matched for both workers:

| Domain projection | Both-process canonical SHA256 |
| --- | --- |
| V1 semantic week | `45c8773b6bd51fdb9f69f8c887dc2c66ae8a7674756b4787e72995a6d84df5e2` |
| V2 normalized *working* PlannerRequest | `5f812e41de2d3f2b11526503e72a1bc1b1371345b9ea68a64f55e21d7aa27966` |
| V2 source/version/process/rights provenance | `6e03e03865ce95bcca5d61d77652b4b1c4af4243bdfca966dae4d88902c0558c` |

Independent raw-structure assertions passed for **each** process: exactly three distinct member selections, seven local dates 2026-11-02..08 Europe/Moscow, 21 unique COOK_RECIPE events and 42 unique event/member Servings; each day has BREAKFAST for member ordinals 1+2, LUNCH for 1, DINNER for 1+2+3. Every persisted Serving was a positive finite exact six-decimal value and matched the corresponding V1 event. All plan/event/selection/serving FKs and event/RecipeVersion source references matched. The selected 21 recipes matched B candidate code/version/source_name/source_version/source_document_sha256/process_sha256/rights/verification/ingredient codes, and participant-specific exclusions, including third member's `BEEF_CATEGORY_1_RAW` exclusion. All 51 candidates are `exact_energy_ready=true` but `nutrition_status=INCOMPLETE`.

Code inspection confirmed: each worker subprocess creates independent fresh temporary SQLite databases; it verifies frozen A/B and independently regenerated pre-generation inputs, then assembles the real Household/MealPattern/Candidate input, checks the **working** `PlannerRequest` against B *before* calling unchanged `PlannerService.generate_authoritative`. It persists using the ordinary MealPlan service/repository/UoW and reads back `get_current_plan`. `compare()` invokes each worker once and never rerolls or tunes output; unexpected worker failure produces a structured `NO_GO_FORWARD_FIXTURE_UNSTABLE` comparison. No preselected recipe/Event/Serving arrays drive production Planner.

## Opaque raw fingerprint divergence — investigated, not ignored

- Process 1 raw request: `42d6c231ffa31d7a68bee3f4a27812902802c4f2fe9344d89d96d790ce97d56f`; trace: `df0ef5fa78e707d87200781e18545f4cffc53a2d2f4f75ee700af29fc432f1f0`.
- Process 2 raw request: `207af376b1f23df5356171da3265f000d87553dad93e049166497325738db79a`; trace: `df4fd574aac4ec6f6a70b56b8fd76c394c8020a0b5b84ea2f23467074c647bae`.
- Actual candidate-input RecipeVersion UUID order, candidate UUID tie order, canonical-code tie order and member UUID/ordinal order **match**; selection UUID bindings and FoodIngredient UUID→code bindings differ across fresh databases. The Planner's raw request hash covers `asdict(request)`, including these runtime IDs and selection snapshot fields. Its trace hash also incorporates selection IDs, exclusion UUIDs and raw request hash. This explains why the opaque fingerprints cannot be used as a cross-database semantic equality predicate.
- The independently compared normalized working input, complete candidate and member semantics, source-backed provenance, role/member/portion choices, and persisted 21×42 result **do match**. Thus this divergence does **not** defeat reproducibility of the reviewed technical fixture. We **do not** assert byte-identical raw request objects or exact attribution of every raw hash bit solely to UUIDs; run-local snapshot metadata can also differ. No Planner fingerprint algorithm was changed.

## CI and negative QA

[Exact PR head `a73b8d8`](https://github.com/Mitronomik/family-food-os/pull/269): **26/26 PR workflows completed SUCCESS**, zero failed/pending. Focused workflow [#41309700338](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338): **17 tests PASS**, Ruff lint and format PASS, one-shot two-process proof PASS, raw ZIP successfully persisted. Negative QA covers changes to RecipeVersion, role, event order, member, portion, normalized input, provenance, candidate UUID/tie order, duplicate Food/Selection IDs, and child-process failure/NO_GO receipt. These are evidence from the exact PR HEAD; no new backend regression was run as part of this docs-only review.

**Findings:** P0 none; P1 none blocking this *technical energy-only* review. P2 scope limitations remain explicitly recorded: no macronutrient completeness or portion plausibility, no independent cooking/RecipeStep eligibility, no operational safety claims. Raw trace SHA parity is not a requirement for UUID-free semantic reproducibility. These are **not** accepted production/release constraints.

## Decision and gate boundary

**Independent technical review:** `PR10_FF_FIXTURE_REPRODUCIBILITY_REVIEW=PASS`.

**Do not infer owner acceptance or reopen the next implementation milestone.** Until a separate explicit owner decision records acceptance of this specific technical fixture/digest, maintain:

```text
PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN
NO_GO_TO_PR10_CORE_RUNTIME
APPROVED_IMMEDIATE=0
SAFE_BATCH_READY=false
PORTION_RELEASE_READY=NOT_PROVEN
```

Even after owner acceptance of this technical fixture, PR10-A / D3 source-step eligibility, complete authoritative Russian same-day actions for at least two distinct actually generated COOK_RECIPE events, a reviewed unresolved negative case, full Shopping→Prep→PDF technical Gate2 integration, and separate safe batch/real-family release gates remain separately blocked until their own evidence/authorization. The finished-dish-first direction, D3 revocation/anti-rollback and historic #196/#254 negative archives are preserved.

**Next permitted action:** independent review and owner approval/merge of the *docs-only state reconciliation PR*. Then separately request the owner's explicit decision on whether to accept the precise reviewed forward technical fixture digest; do not start PR10-A/Prep implementation automatically.
