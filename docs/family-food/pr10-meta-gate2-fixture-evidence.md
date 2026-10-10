# PR10-META-FIXTURE — persisted synthetic 3-member source-pin receipt

**Status:** EVIDENCE TASK, not PR10-META READY and not a Prep/Freezer implementation.
**Issue:** #195.
**Accepted base:** `main@05610128ad7c1156e5908b809606a5cb7223acce` (PR #194 merged 2026-10-10).
**Current PR10-META decision:** [BLOCKED](pr10-meta-readiness-decision.md). The [accepted Prep contract](pr10-prep-freezer-implementation-contract.md) still requires a safe, source-backed shared operation for two actual MealEvents and fewer distinct physical operations.

## Goal and truthful boundaries

Produce one **persisted** MealPlan and member/Serving/source-RecipeVersion pin receipt through the approved repository-backed Planner path. The preexisting [DC4 3-member evidence](../../data/curation/dc4-corpus-readiness/rerun-summary.json) proves 21 events and 42 servings, but its published summary does not include event/RecipeVersion UUID mappings. A read-only analysis of that summary cannot reconstruct those mappings honestly.

The new `scripts/audit_pr10_meta_gate2_fixture.py` reuses existing synthetic DC4 fixture helpers, accepted recipe publication/seed and real `PlannerService.generate_authoritative` / MealPlan repository read-back, all against an **ephemeral SQLite database** created in a temporary directory. The script does not open user or production data. It emits a file after the DB is disposed. A dedicated [workflow](../../.github/workflows/pr10-meta-fixture-evidence.yml) tests and uploads the JSON as a short-lived evidence artifact.

## Captured fields and provenance

- Fresh synthetic Household ID, timezone and seven-day MealPlan UUID, revision and configuration version. UUIDs are minted by the accepted domain services and **not expected to repeat across separate fresh DB runs**.
- All 3 member IDs and their accepted selection pins; 21 persisted MealEvent UUID/date/position/role/source_kind/RecipeVersion references; 42 Serving UUID/event/member/Decimal portion_servings rows. The tool validates foreign-owner/event/code references, positive servings, 7 days and exact counts.
- Entire active verified RecipeVersion catalogue of **at least 30** current-at-the-audited-runtime versions, with canonical code, immutable version ID, provenance source/version/document hash, base/original servings, exact nullable batch/freezer/storage/time metadata, ordered RecipeStep IDs, positions and instruction SHA256 fingerprints.
- The accepted Planner-v0.5 semantic trace hash, pure planning replay equality and exclusion-check result. The semantic Planner trace is deterministic; generated fixture row UUIDs are not stable across separate seed builds.
- A deliberate `gate_decision: BLOCKED`. The receipt proves **fixture lineage only**, not storage/holding/reheating/freezing safety, shared-work evidence, completed Prep or food inventory.

## Independent Planner baseline and receipt integrity — review correction

The initial PR #196 reviewer found that the receipt's old structural validator accepted fake counts, alternative valid-catalogue recipe pins, remapped valid-event Servings, arbitrary 64-character process hashes and nonfinite Decimal strings. The originally downloaded artifact **is not claimed corrupt**; its historical SHA-256 (`507bf8a18192f3edaec3d5ee295d3b8fab6fda872370c44ff74a598290b6158a`) refers only to the **pre-correction** run and must not be reused as new exact-head evidence.

The corrected `validate_fixture_receipt()` recomputes all five `counts`, requires positive **finite** Decimal strings, unique (event_id, member_id) participation and each event's complete participant/quantity allocation against the independent planner-derived semantic fixture baseline. Its `planner.expected_semantic_pins_sha256` is computed from **pure `generate_week` output**, NOT copied from persisted receipt events: the baseline covers date/position/role/source/RecipeVersion and every event's member/Decimal Serving allocation. The issued receipt recomputes the same canonical semantics from the read-back persisted MealPlan and compares hashes. A swap to another valid catalogue RecipeVersion or a Serving move to another valid event therefore fails. The validator also recomputes each RecipeVersion `process_hash` from **included, ordered steps**, rejects malformed step hash strings and checks the event/date/Household reference boundary.

**Trust limit:** A self-contained hash is a **consistency check, not a signature**. An attacker replacing both the receipt rows and its claimed baseline could still manufacture a self-consistent JSON. An external verifier must use `trusted_semantic_pins_sha256=` obtained independently from the exact CI Planner run, and verify the separately logged SHA256 of the **entire JSON artifact** before accepting it as the emitted evidence. The CI log prints the independent semantic hash and JSON hash; no supplied receipt field can substitute for that external anchor. UUIDs remain ephemeral across fresh DB runs and numeric ingredient/freezer process authority remains absent.

New adversarial TestClient-equivalent focused tests specifically mutate declared counts, a valid catalogue pin, a Serving to another valid event, duplicate event/member, `Infinity`/`NaN` and a forged process hash/step, plus a forged receipt baseline under an independent externally pinned semantic digest. This remains an **evidence-only integrity correction**, not a change to the Planner or persistence architecture.

## Execution, constraints and acceptance

Use `python -m pytest -q backend/app/tests/test_pr10_meta_gate2_fixture.py` to validate fresh DB construction, persisted source pins and tamper resistance; use `python -m scripts.audit_pr10_meta_gate2_fixture --output /tmp/pr10-meta-fixture-receipt.json` to issue a separate disposable receipt. `AI_ENABLED=false`.

The workflow uploads `pr10-meta-synthetic-fixture-receipt` as a JSON artifact and prints its SHA256. The exact artifact SHA and GitHub Actions job must be recorded for review; documentation must not claim the JSON file exists until the workflow proves it and is inspected. The artifact is temporary and cannot be substituted for a permanent, reviewed source/readiness publication.

**Tests required:** counted 3/21/42/7, >=30 current verified versions, nonempty process hashes, proper event/Serving/Household scopes, Decimal positive amounts, deterministic Planner trace. Tampering with an event pin, Serving owner/amount, plan relation, counts or gate status must fail validation. No existing Shopping or Pantry production behavior changes.

**Scope/non-goals:** evidence tooling + focused tests + isolated CI + docs/state only; no schema migration, no change to current Planner/Recipe/Shopping/Pantry engine, no Prep tables/logic, no new shelf-life values, no private person records, no PDF, no Retail or AI.

## After this evidence PR

Even if the persisted fixture proof passes and the receipt is accepted, **PR10-META remains BLOCKED** until a separate reviewed source-backed shared/advance-preparation candidate proves its process/form, safe holding/transition and at least one reduced physical work action spanning two selected MealEvents. The actual Gate 2 final fixture may be re-pinned later; receipt provenance and candidate catalogue must be carried into that decision rather than assumed current forever.

No PR10-A/B/C or Prep execution is authorized merely by this evidence.
