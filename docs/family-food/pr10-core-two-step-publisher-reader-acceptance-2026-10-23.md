# PR10-CORE two-step eligibility — bounded publisher/reader implementation acceptance handoff

**Status:** **CONTRACT ADDENDUM PROPOSED / DOCS-ONLY / NO AUTHORITY PUBLISHED**.
**Base:** merged [PR #238](https://github.com/Mitronomik/family-food-os/pull/238), `main@22a7f2ab9d94fe395739f0691e5fff3ba3928594`.
**Parent authority:** [PR10-CORE-D3 trusted source/read contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md) including its **anti-rollback §4.1**, [PR10-ARCH](pr10-prep-freezer-implementation-contract.md) §4.1 and [Option B](pr10-option-b-staged-delivery-gates-2026-10-17.md).
**Source assessment:** [two-step source/process/scale review](pr10-core-two-step-source-process-scale-review-2026-10-23.md) and [JSON evidence](pr10-core-two-step-source-process-scale-decision-2026-10-23.json), Issue [#239](https://github.com/Mitronomik/family-food-os/issues/239).

## 1. Decision requested and preconditions

The owner authorized **one limited review and preparation of necessary contracts**, **not** the actual release of a trusted eligibility file or runtime reader. This addendum freezes exact evidence and acceptance for *at most two first steps*; it does not create the publisher/reader or select a new database/network provider.

**Research disposition now:** `GO_FOR_REVIEW_AND_CONTRACT_ONLY`; both `APPROVED_IMMEDIATE = NO_GO_ON_CURRENT_EVIDENCE`, independent reviewer approval `0/2`, trusted publisher/reader implementation `NOT_STARTED`; `NO_GO_TO_PR10_CORE_RUNTIME`. No curation output from this PR has accepted production publication identity or approval status. Reject an attempt to deploy [research evidence JSON](pr10-core-two-step-source-process-scale-decision-2026-10-23.json) or the earlier [pending queue](pr10-core-step-eligibility-review-queue-2026-10-22.json) as an allowlist.

## 2. Exactly two publication candidates and review ownership

| Task subject | Exact permitted review scope | Current source/method blocker |
| --- | --- | --- |
| R3-C `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES`, *Step 1* | Same-day `COOK_RECIPE`, source-verified original whole preparation/blanch/sauté/tomato-purée step; exact RecipeVersion/Step/hash, family-scaled structured vegetables and source-bounded process validation | Compound step requires independent whole-step approval; source-original industrial vegetable preparation is abbreviated in published step; sunflower oil split sauté vs greased pan is **UNKNOWN**; source capacity/scale not cleared |
| R2-B `SCHOOL2022_54_7R_POLLOCK_IN_MILK`, *Step 1* | Same-day `COOK_RECIPE`, whole prepare/shred/blanch onion step; exact RecipeVersion/Step/hash, verified current member source factors/structured onion and process applicability | Home blanch protocol/temperature/time/equipment/capacity at current scale unreviewed; possible original→published **Step 4 milk-level reference mismatch (tray height vs fish height)** requires Recipe/Data adjudication before claiming whole published cooking process source-clean |

The **Recipe/Data curator** may assemble evidence and propose a scoped `NO_NUMERIC_DIRECTION` classification separately from same-day action eligibility. The **independent Domain/QA reviewer**—a real person/organizational reviewer, not the AI evidence author—must evaluate the full immutable source step and RecipeVersion process at the **actual frozen future Gate2 fixture** scale, disclose additional authority/rights needed, provide named identity, signed decision reference, date/version, applicability, conflicting source resolution and revocation conditions. No self-review and no implied approval from this PR's merge. The **Product/Architecture owner** separately accepts the reviewed publication/deployment capability contract; approval cannot invent missing source facts. Rejection of either exact step returns bounded NO-GO; do not substitute new steps in this task.

## 3. Exact versioned publication identity, freshness and authority

A future `ReviewedRecipeStepEligibilityV1` publication unit MUST include:

- `publication_id`, `eligibility_revision`, `receipt_schema`, canonical payload SHA-256, independently trusted repository/release reference and deployment release identity.
- **Current** `recipe_version_id` and its source version, `recipe_step_id`/position/step SHA-256, `recipe_process_hash`, source-document/card/manifest hashes, exact source rights/applicability form, known target Serving/MealEvent context, no historical fixture UUID reuse without fresh reproving lineage.
- Separate independent **`numeric_direction_classification`** and **`immediate_same_day_eligibility`**, permissible member/food form/scale/equipment/context, explicitly *excluded* batch/holding/freezing/savings contexts. `APPROVED_IMMEDIATE` requires affirmative independent evidence for the whole instruction, not merely absence of digits or a curator label.
- Original reviewed `instruction_ru` bound to immutable RecipeStep; any changed/quantity-neutral replacement consumer text needs its **own** independently accepted source-backed version. Never derive a new instruction by splitting/simplifying process prose without a separate recipe/process authority review.
- Curator, **independent reviewer identity**, review/signed-reference, timestamps, rationale, source facts vs assumptions, policy owner, expiry/revocation identity, supersession and explicit invalidation conditions. Unspecified timestamps/reviewer/source references are **BLOCKED**, never `APPROVED`.

The trusted **reader** lives at the Prep application/composition adapter boundary. It obtains the released immutable package from a validated local/release-pinned deployment source, independently rechecks current source/RecipeVersion/Step/MealEvent/Serving hashes and validated applicability, reads **live rollback-independent eligibility status**, and returns a typed, trusted *verdict* to the pure backend Prep calculator. Domain code never fetches files, GitHub, SQL, network or LLM. No consumer/freezer/Pantry/Shopping truth is emitted by the eligibility package.

**Anti-rollback is a hard prerequisite, not optional optimization:** an independently administered authenticated monotonic current-status/minimum-policy-revision authority, protected from deployment rollback/backup restore, must actively approve the **exact** current package identity before **each executable task admission**. The eventual implementation must specify the status authority's owner, trust keys/proofs, durability, rollback/floor semantics, how revoked records propagate before use, availability/timeout handling and reader/deployment guard protecting old code. A historically correct local hash cannot override newer `REVOKED`. Without an independently approved and tested operational implementation of this status authority, `APPROVED_IMMEDIATE` is *unusable*, even if human review has separately approved the underlying process. This documents an **unresolved high-coupling implementation choice**; it does not silently add PostgreSQL, a new service or another Prep table.

## 4. Fresh, replay, conflict, revoke/rollback and transaction contract

| Condition | Required behavior / negative control |
| --- | --- |
| Current independently approved, exact source identity + status ACTIVE | Allow **only** after numeric and immediate-action review, validated exact member/source scale and accepted trusted reader; verified current published policy epoch |
| No independent reviewer, questionable process, source-original/published mismatch or rights gap | `UNKNOWN/REVIEW_REQUIRED`; **no executable task**. Contradictory required structured ingredients/Serving or Household reference = **BLOCKING/no partial Prep write** |
| Package missing, forged, self-hash only, unknown version, duplicate conflicting key, reverted artifact or self-review | Fail closed to unresolved, no fallback into raw `RecipeStep` text or LLM |
| Fresh publication | Independently approved source/rights/step IDs and process hashes, monotonic eligibility revision, canonical payload and trusted pin; all entries pass validation atomically or publication rejected |
| Exact replay | Same approved bytes/epoch/source produce identical reviewed eligibility verdict and Prep fingerprints, without duplicate snapshots |
| Same `publication_id` with changed bytes, new conflicting version or stale RecipeVersion | `CONFLICT`, no executable task or partial publication; previous history immutable |
| Step or process corrected, source rights withdrawn, eligibility revoked | Revocation advances independently trusted status floor; old versions fail closed; previously generated Prep/PDF remain historical, not current authorized actions |
| **A approved → B revoked → rollback to A** | **Zero executable task**, explicit unresolved/stale Prep/PDF, no Pantry mutation, even if package in A has matching checksum. A non-compliant old reader is barred/disabled by independent deployment guard. Authority unreachable, stale/downgraded epoch or offline: same fail-closed result |
| Multi-event same-day lunch/dinner | Exactly **two separate event-specific tasks** if later reviewed; no grouped onion stage, preparation clock assumption, held ingredient, net saving or freezer claim |
| Failure during three-table Prep UoW (future PR10-B) | No partial parent/task/unresolved publication, Household scope enforced and correct rollback under concurrent conflicts. An ordinary source UNKNOWN can generate an explicit INCOMPLETE plan **only** with valid authoritative MealPlan/ingredient/Serving input |

### Required future adversarial verification (NOT executed here)

A minimal **independent process/source review** test must check both exact current Step hashes against immutable RecipeVersion, all structured ingredients and Decimal Serving factors, Russian language/process adequacy and separate no-digit vs immediate-action determinations; include an explicit whole-recipe original→published milk-level reference adjudication, not a silent fix.

A **publisher/reader** test suite must cover first publish, exact replay, same-key/different-bytes rejection, mismatched source/step/release hashes, stale version rights, revoked/expired reviewer authorization, independent status authority offline/downgraded epoch, and `approved → revoked → rollback → no executable task` with old-reader prohibition. The runtime consumer of the typed result must fail closed on every UNKNOWN, have no Pantry/PreparedBatch writes and preserve old immutable plans with correct staleness.

**Two-event Gate2 positive remains separate:** even a compliant trusted reader with two independently reviewed positives cannot close Gate2 by itself. It still requires the *actual accepted seven-day Household fixture* with at least one reviewed preparatory action per distinct COOK_RECIPE event, independently checked truthful unresolved negative case, complete Planner → Shopping → Prep → PDF path and separate runtime acceptance, per [Option B](pr10-option-b-staged-delivery-gates-2026-10-17.md). `SAFE_BATCH_READY` and `PORTION_RELEASE_READY=PASS` remain separate real-family release conditions.

## 5. Implementation Contract Gate stop and handoff

**No migration/runtime authorization here.** Three immutable Prep tables and existing reason/status fields remain the default design; no `0044` migration reservation. Exact class-binding package publishing/reader mechanism and rollback-independent status authority may cross a high-coupling data/version/deployment boundary. Before writing implementation the **next independently reviewed docs-only gate** must freeze (a) real review approvals, (b) chosen trust/status implementation and deployment/rollback guard, (c) dependency/preservation matrix, (d) fresh/replay/conflict semantics, (e) failure-injection and rollback tests and (f) verification tier. This addendum is a **contract acceptance template and precise blocker handoff**, not a completed deployment design or source publication.

**Decision for this bounded owner-authorized two-step task:** `GO_TO_EVIDENCE_AND_INDEPENDENT_REVIEW_ONLY`; `NO_GO_TO_TRUSTED_PUBLICATION`, `NO_GO_TO_PR10_A_RUNTIME`. Missing qualified process evidence or the source-process discrepancy must never be resolved by inventing recipe directions or broadening candidate search. Return exact source/scale/process gaps and request the next explicit decision; keep Gate2 and real-family gates blocked.
