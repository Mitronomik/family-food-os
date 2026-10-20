# PR10-CORE positive-data and three-table preflight

**Status:** **NO_GO_TO_PR10_CORE_RUNTIME_ON_CURRENT_EVIDENCE**; positive source candidates identified, but **zero independently approved executable PrepTasks**.
**Date / accepted base:** 2026-10-20, `main@094ded5edfa13874bf63f1bc3b83e18c9218dc67` ([PR #234 merged](https://github.com/Mitronomik/family-food-os/pull/234)).
**Scope:** [Issue #235](https://github.com/Mitronomik/family-food-os/issues/235), **one bounded, docs/evidence-only preflight**. No schema, source, data, Planner, Prep runtime, PDF or Gate2 change.
**Authoritative rule:** [Option B staged gates](pr10-option-b-staged-delivery-gates-2026-10-17.md) §§3–6; [PR10-ARCH](pr10-prep-freezer-implementation-contract.md) §§4.1, 5–9 and [D2/D3 ADR](pr10-data-recovery-approved-decisions-2026-10-11.md).
**Machine-readable receipt:** [two-event step candidate and compatibility evidence](pr10-core-positive-preflight-evidence-2026-10-20.json).

## 1. FACT — what was verified on repository data

The accepted DC4 [historical three-member Planner fixture](../../data/curation/dc4-corpus-readiness/rerun-summary.json) generated **21 MealEvents and 42 Servings over seven days**, with three heterogeneous accepted MealPatterns and `planner-v0.5`. It is evidence of the earlier normal Planner, **not** evidence of the new Option B Prep runtime.

The [persisted synthetic PR #196 receipt](pr10-meta-gate2-fixture-evidence.md) and [later two-event provenance review](pr10-meta-onion-blanch-evidence.json) pin two distinct historical `COOK_RECIPE` events on **2026-09-16**. Their original **member-specific Decimal Serving strings**, RecipeVersion and RecipeStep UUIDs, process/step hashes and source provenance are preserved in the machine receipt. The exact **first-step Russian texts** independently match the currently checked repo publication manifests:

| Historic event | Pinned RecipeVersion and Step | Original Russian step | Evidence result |
| --- | --- | --- | --- |
| `LUNCH`, salmon with tomato/vegetables | RecipeVersion `155f5283-2f2a-4487-83ac-895877197b45`; Step `82a7cf80-6aee-42b0-91bb-b318cbf41e47` | «Подготовить корень петрушки, морковь и репчатый лук; лук бланшировать, затем пассеровать вместе с морковью и петрушкой и добавить томатное пюре.» | Matches [R3-C frozen batch](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json); **candidate only** |
| `DINNER`, pollock in milk | RecipeVersion `16a04325-d532-45f6-82ca-2f30630467a6`; Step `00dc9916-dc34-44eb-8518-ff7299920149` | «Репчатый лук подготовить, нашинковать и бланшировать.» | Matches [R2-B verified publication spec](../../data/curation/r2b-fish-main-diversity/publication-specs.json); **candidate only** |

Both instructions are Russian, name concrete food and actions, and contain **no literal numeric direction in the inspected first-step string**. The step hashes are retained from accepted historical research evidence; the text was checked for equality with the repo-pinned publication manifests. This was **not** a re-hash of current live RecipeStep bytes or proof that future immutable versions share those UUIDs.

**Source identity:** the School2022 source-document SHA-256 is `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`; factual-recipe rights are marked reviewed in the source publication lineage. In their source-base ingredient records, `ONION_BULB_FRESH` is **9.8 g net** for salmon and **16 g net** for pollock. Historical portions in the receipt are `5.916796` (salmon) and `5.631030`, `5.631030`, `6.546747` (pollock). **No claimed physical kilogram amounts or consumer instruction scaling were generated from prose**; the future backend must use canonical `scale_recipe` with exact member `Serving` data.

**Why this is useful:** unlike earlier PR10-META research, these two events do **not need** a shared component, cross-meal preparation, fridge/freezer holding, or claimed time savings. Each is a separate **same-meal-day candidate** for preparing an ingredient. The evidence avoids another open-ended source hunt.

## 2. What remains unproven before ANY executable task

A nonnumeric instruction is **not automatically executable or independently reviewed**. The recipe steps combine preparation and cooking: e.g. salmon says blanch and sauté, and the pollock source does not supply an independently certified home-equipment/time recipe-specific protocol. A reviewer must confirm whether each proposed step is sufficiently clear and applicable **for same-day immediate execution** at its actual Decimal scaled quantity **without inventing equipment capacity, time, food form, temperature or kitchen safety**. If not, the step remains unresolved.

**Missing review/publisher contract:**

1. Confirm the exact RecipeVersion, RecipeStep ID/hash, source rights/recipe form and original process step against the **current** pinned reviewer fixture; prior disposable UUIDs cannot be assumed current.
2. Independently review step eligibility, source-language accuracy, no numeric contradictions in the **whole step**, any hidden process-size/ingredient split, and whether source cardinality/household batch scaling changes execution safety. `NO_NUMERIC_DIRECTION` is currently **only a suggested candidate classification**, not a published authority.
3. Freeze a **versioned, immutable, reviewed step classification** tied to step/process hashes, source version, applicability, curator, review date, status and invalidation. Demonstrate accepted read/replay/staleness semantics and no substitution of LLM source facts.
4. If this requires publishing a new authoritative classification payload, revision identity or reader, use a **separate docs-only D3-style source-publication/read-path Implementation Contract Gate** before any PR10-A. Do not turn this research JSON or a regex into runtime truth.
5. On actual accepted three-member Gate2 fixture, independently prove **at least two different MealEvents** with one qualifying task each **and** one intentionally unresolved legitimate case. A negative zero-task/all-UNKNOWN week must remain `NO_GO`, not `COMPLETE` by presentation trick.

**Current status:** `reviewed_step_classification_count=0` **within this audited evidence**, `approved_executable_task_count=0`. This is not an assertion that no other recipes anywhere can be reviewed. **No PR10-A runtime is authorized.**

## 3. Existing three-table Prep architecture fit

| Reviewed contract boundary | Preflight result | What future implementation must prove |
| --- | --- | --- |
| `prep_plans` immutable Household-owned snapshot | **Conceptually compatible** with one exact accepted MealPlan revision and step-classification source fingerprint | Revision/supersession, same-Household source pins, `COMPLETE`/ `INCOMPLETE` as **step coverage only** |
| `prep_tasks` per-event Step rows | **Conceptually compatible** with two distinct events and `shared_work_group_key=NULL` for each | Correct `scheduled_local_date = required_meal_date` for same-day work; exact event/member Decimal Servings and source-hash/version, no inferred clock time |
| `prep_unresolved_obligations` | **Conceptually compatible** for denied/missing/ambiguous steps without any new reason enum or status | `PROCESS_STEPS_UNVERIFIED` or `STEP_QUANTITY_REVIEW_REQUIRED` where applicable; no fake freezer/hold/capacity data |
| Transaction & staleness | **Contractual only, not executed** | Single SQLite UoW, begin-before-read lock, three-table atomicity/rollback/idempotence, Household FK/scope, versioned source/MealPlan/step classification invalidation |
| Migration registry | Repo `backend/app/migrations/versions` ends at `0043_shopping_engine.py`; **no Prep table migration exists** at this preflight | `0044` only a **candidate**, never reserved/created by this docs PR; inspect future exact main and fresh/upgrade/backups before any PR10-B |
| Derived Shopping/PDF/stock | No change now | Shopping untouched during Prep generation; PDF accurately displays immutable positive and UNKNOWN tasks; `PrepPlan.COMPLETE` is not `SAFE_BATCH_READY`; no PreparedBatch/Pantry writes |

No structural contradiction with the **proposed** existing three-table design was identified for **ungrouped same-day per-event tasks**. This is **not** a proof of actual schema/UoW implementation: no tables, SQL constraints, concurrency or migration tests were created/executed. If data-authority/read review or later testing reveals the need for a different table/status/identity, **reopen the applicable docs-only Implementation Contract Gate**, do not expand a runtime PR silently.

## 4. Adversarial checks, negative controls and stop rule

- Both identified steps **lack** independently accepted classification → **0 authoritative executable PrepTasks**, explicit unresolved and **technical Gate2 NO_GO** regardless of source-text completeness.
- Only one of two MealEvents qualifies → **Gate2 NO_GO**; the contract requires at least **two** distinct eligible events and reviewed positive instructions.
- Unreviewed numeric steps, stale hashes, changed RecipeVersion, missing source rights, unresolved structured units or member Serving mismatch → withheld step or **blocking error/no partial PrepPlan write** as applicable.
- Same local date does not prove simultaneous prep, holding or an optimizable single session. **Never** group these two steps into one onion-blanch operation, claim `B<A`, invent fridge/freezer instructions, say cooked stock exists, or assume pantry stock was consumed.
- Full seven-day Gate2 remains the accepted Household/MealPattern/RecipeVersion fixture and real Planner → Shopping → Prep → PDF runtime path. The two historic candidates **alone** do not pass Gate2.

**Stop rule / next bounded task (proposal, not automatically authorized runtime):** obtain **one independent source and numeric/operational review for precisely these two immutable first steps** and, only if new authority must be read/published, prepare a **single D3-style docs-only classification publisher/read contract**. If either cannot be made independently executable, return a small `NO_GO` with the exact gap—**no new arbitrary recipe-pair search**. Review/merge of this receipt **never** authorizes PR10-A/B/C without a separate explicit decision.

## 5. FACT / ASSUMPTION / DECISION / OPEN and verification

**FACT:** Two historic source-backed MealEvents/RecipeVersions/steps and Decimal portions are traceable in accepted research; both step texts match corresponding repo publication inputs; no reviewed executable classification is shown.

**ASSUMPTION:** after expert review these two nonnumeric first-step actions may support useful same-day Prep tasks. They may still fail once actual household scaling/time/safety applicability is checked.

**DECISION (preflight evidence):** `NO_GO_TO_PR10_CORE_RUNTIME_ON_CURRENT_EVIDENCE` until source-read eligibility is independently accepted; **not** a decision against the approved Option B roadmap and **not** a global catalogue failure.

**OPEN:** exact positive step publisher/reader authority and current fixture re-pin; whether source steps are executable without process/equipment safety data; when a separate authorised PR10-A would start. PR10-FD-META **remains `BLOCKED / TIME_UNRESOLVED`**; `SAFE_BATCH_READY` and `PORTION_RELEASE_READY` remain unproven. Gate2, PDF, PWA and real-family release are not advanced by this preflight.

**Verification:** inspected source/manifests and historical event pin receipts on accepted repo base, checked text equality and no numeric tokens for the two candidate steps; audited versioned schema/migration references and documented source/reader failure conditions. No live application fixture, CI research script, authoritative classifier publication, migration, runtime tests, actual food preparation or freezer-safety evaluation executed. Exact-head Docs CI and independent review remain required before merging the evidence.
