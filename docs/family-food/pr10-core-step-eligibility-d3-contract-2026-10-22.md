# PR10-CORE-D3 — reviewed Russian RecipeStep eligibility publication/read contract

**Status:** **PROPOSED / DOCS-ONLY / awaiting independent review and merge**. Does **not** authorize classification publication, an executable PrepTask, PR10-A/B/C implementation or Gate2.
**Accepted base:** `main@04da57bd02df493336036ec1f52b9df626c721ab` ([PR #236](https://github.com/Mitronomik/family-food-os/pull/236) merged 2026-10-22).
**Tracking:** [Issue #237](https://github.com/Mitronomik/family-food-os/issues/237).
**Read with:** [Option B technical/release gates](pr10-option-b-staged-delivery-gates-2026-10-17.md), [PR10-ARCH](pr10-prep-freezer-implementation-contract.md) §§3–9, [D1/D2/D3](pr10-data-recovery-approved-decisions-2026-10-11.md), [PR10-CORE bounded preflight](pr10-core-positive-preflight-2026-10-20.md) and [its pinned evidence](pr10-core-positive-preflight-evidence-2026-10-20.json), [DATA-CORPUS-V1](data-corpus-v1.md), [Master Roadmap](master-roadmap.md) and [Russian instruction contract](russian-language-contract.md).
**Current review queue:** [exactly two non-authoritative entries](pr10-core-step-eligibility-review-queue-2026-10-22.json).

## 1. Purpose and minimal decision

The accepted Option B requires **two distinct `COOK_RECIPE` MealEvents with at least one genuinely executable, reviewed, Russian, same-day preparatory task each** for technical Gate2. Merge of #236 proved **two historical candidates**, NOT executable approvals. This gate proposes the **smallest trusted source/read boundary** capable of later supplying reviewed step eligibility. It deliberately avoids rebuilding recipe ingestion, re-publishing recipes, inventing physical time/holding authority or adding a fourth Prep table.

**FACT:** the reviewed School2022 recipe versions already have source/rights, structured ingredient quantities and immutable process steps. `RecipeStep.instruction` is recipe source truth; **being a source-verified step, or having no digits, does not by itself approve scale-appropriate executable Prep instructions**.

**PROPOSED DECISION:** record separate **numeric-instruction classification** and **same-day executable eligibility** under one immutable, source-/version-/step-hash-pinned curation receipt, reviewed independently of the original source curator. A future trusted, read-only **application-layer** reader verifies the receipt and supplies a typed, versioned eligibility result to a pure Prep domain calculator. No extra persisted Prep identity or table is needed **under the explicit assumption** that this immutable resource can be deployed, pinned, validated and rolled forward without a database migration. If that assumption fails, STOP for a separate docs-only high-coupling implementation gate; never smuggle new SQL fields or an unpinned sidecar reader into PR10-A.

**No automatic authority:** this PR's accompanying JSON is a **review queue only**, with zero independently approved steps. It must **never** be a runtime allowlist, publication payload or a feature flag. `NO_GO_TO_PR10_CORE_RUNTIME` from #236 remains in force.

## 2. Exact bounded candidate evidence (no implicit approval)

| Historical synthetic 2026-09-16 source event | Recipe source/process | First RecipeStep text | Proposed review state |
| --- | --- | --- | --- |
| `LUNCH` — `SCHOOL2022_54_17R_SALMON_TOMATO_VEGETABLES` | R3-C reviewed School2022 source, historical RecipeVersion `155f5283-2f2a-4487-83ac-895877197b45`, Step `82a7cf80-6aee-42b0-91bb-b318cbf41e47` | «Подготовить корень петрушки, морковь и репчатый лук; лук бланшировать, затем пассеровать вместе с морковью и петрушкой и добавить томатное пюре.» | `PENDING_INDEPENDENT_REVIEW` |
| `DINNER` — `SCHOOL2022_54_7R_POLLOCK_IN_MILK` | R2-B reviewed School2022 source, historical RecipeVersion `16a04325-d532-45f6-82ca-2f30630467a6`, Step `00dc9916-dc34-44eb-8518-ff7299920149` | «Репчатый лук подготовить, нашинковать и бланшировать.» | `PENDING_INDEPENDENT_REVIEW` |

Both source texts were found *exactly* in the accepted [R3-C batch](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json) and [R2-B spec](../../data/curation/r2b-fish-main-diversity/publication-specs.json); their hashes and the historical member Decimal `Serving.portion_servings` strings are in the [#236 receipt](pr10-core-positive-preflight-evidence-2026-10-20.json). The document SHA-256 is `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

**FACT with limits:** the literal first-step strings have no numeric tokens and describe preparation actions. However salmon's source step bundles prepare/blanch/sauté/tomato-purée actions and pollock says blanch without an independent household-duration/equipment treatment in this preflight. Neither an onion source net amount nor a syntactic lack of numbers proves how an actual multi-person batch should be prepared. A reviewer must approve the **whole step as used**, not create imaginary new substeps, shorten the source instruction, fill in `°C`/minutes, or declare safe intermediate storage.

The original fixture IDs are **historical disposable SQLite IDs**, never current production identifiers. The future curation publisher must re-bind and independently confirm **current accepted recipe, process, step and source identities** on the frozen actual Gate2 input. Source code/name alone is insufficient. The two events on one calendar date do **not** justify a shared onion operation or a single preparation session.

## 3. Future immutable eligibility receipt and review policy (proposed)

**Owner:** Recipe/Data curation team proposes each per-step record; an **independent Domain/QA reviewer** assesses exact numeric/source/form/scale/process applicability, provenance, rights and Russian instruction. The Product/Architecture owner accepts/rejects the bounded publication contract and any expanded capability. No unfilled reviewer field, self-review or AI decision becomes approval. Concrete reviewer identity and review timestamp **must be supplied by the actual review process**; this document never invents them.

**Proposed `ReviewedRecipeStepEligibilityV1` envelope**, separate from immutable RecipeVersion content:

| Field / evidence | Required meaning and protection |
| --- | --- |
| `receipt_schema`, `eligibility_revision`, `publication_id`, `published_at`, reviewer and curation decision | Versioned independently reviewed immutable record; `APPROVED` is impossible with missing review/provenance; publication ID/revision is not reused for conflicting contents |
| `recipe_version_id`, `recipe_version_source_version`, `source_document_sha256`, source card/variant if present, rights review | Exact **current** verified original recipe identity, form and legal factual data scope; never match by recipe code alone |
| `recipe_process_hash`, `recipe_step_id`, `step_position`, `step_instruction_sha256` | Same immutable step as the application's source RecipeVersion read. Any hash/position/process conflict = fail closed |
| `numeric_direction_classification` | One existing PR10-ARCH §4.1 classification. Proposed for these two **only after review**: `NO_NUMERIC_DIRECTION`. A regex/no-digit check can **reject or flag**, never grant this classification |
| `immediate_same_day_eligibility`, allowed `MealSourceKind`, form/scale/equipment applicability and explicit disallowed transitions | A **separate reviewed** scoped verdict: possible `APPROVED_IMMEDIATE` only if the complete action is executable with authoritative structured ingredient quantities and no invented time/temperature/capacity. Inapplicable or under-evidenced => `REVIEW_REQUIRED/UNSUPPORTED` |
| `review_source_refs`, rationale, original instruction or its immutable hash and context dependencies | Auditable explanation of why whole-step quantitative/operational consistency holds, with accepted original text unchanged |
| `supersedes_revision`, `revoked_at` or explicit revocation record and `reason` | Revocation and review invalidation are **append-only**; do not rewrite previously published eligibility or historical Prep snapshots |
| `receipt_sha256`, release/trusted snapshot pin | Canonical deterministic serialization, independently re-computed receipt hash and **externally trusted repo/release pin**, not just a self-declared checksum |

**Never publish** raw prototype `PENDING_INDEPENDENT_REVIEW` entries as executable; do not implicitly default `reviewed=true` or `APPROVED_IMMEDIATE` because a numbered recipe exists. Numeric class and actionable eligibility must pass **independently**. A later reviewer may return `NO_GO` for either or both, with the precise absent method/process source and a bounded stop.

**Source rights boundary:** accepted normative factual recipe data rights/provenance are still pinned and limited; this contract does not grant external text reuse or license rights for new sourced safety instructions. Instructions shown to consumers are only reviewed existing Russian text or a **separately accepted** versioned Russian quantity-neutral rendering tied to the original step and exact structured quantities. No AI drafting used as executable authority.

## 4. D3 publisher → reader boundary (proposed, not implemented)

```text
accepted RecipeVersion + RecipeStep (immutable)
        + exact source/rights/context evidence
        → Data curator candidate package
        → INDEPENDENT Domain/QA review and owner source decision
        → trusted versioned immutable eligibility publication
        → application-layer validated read (source/version/step hashes checked)
        → typed reviewed eligibility for pure PR10-A calculator
        → either same-day executable task OR explicit unresolved obligation
```

**Publisher path:** propose a **dedicated source-reviewed, repo-local curation payload** distributed with a specific approved backend revision; it is **not** a second recipe catalogue, runtime GitHub/web fetch, user-uploaded file, arbitrary seed JSON, hidden LLM memory or a SQLite migration by default. Review/publish in one bounded later PR with independent approver, pinned exact source bytes/process hashes and recorded trusted Git commit/receipt SHA; policy version changes create new immutable revisions, never silently mutate old ones. No external downloadable artefact is trusted solely because it has the right filename or a self-hash.

**Reader path:** the future Prep **application/composition boundary** reads a **trusted locally deployed, release-pinned eligibility package** through a typed repository/protocol adapter. The backend must revalidate policy status/version/rights and exact *current* RecipeVersion/RecipeStep/process hashes, source form and age/scope if relevant before admitting a task. Domain calculations receive already validated data, never perform filesystem, GitHub, SQLAlchemy, web, LLM or direct database reads. Strict `AI_ENABLED=false` coverage required.

**Fail closed:** absent/untrusted package, unknown enum/revision, duplicate conflicting keys, unresolved rights, unsupported MealSourceKind/form/scale, hash drift, revoked/stale record or missing reviewer → `PROCESS_STEPS_UNVERIFIED` / `STEP_QUANTITY_REVIEW_REQUIRED` as applicable, **no executable task**. If the underlying structured ingredient/Serving/Household join is itself invalid, **BLOCKING/no write**, not a merely incomplete plan. A stale already generated PrepPlan remains immutable history but is **not** presented as current; dependent PDF/Prep states invalidate and regenerate only after accepted new review. All scopes are Household-checked.

**Recipe/fingerprint ownership:** RecipeVersion remains the immutable culinary source of ingredient quantities and original steps, not the eligibility package. Eligibility only establishes *which previously published action is allowed under precisely what validated conditions*. The Prep source fingerprint must include the released eligibility receipt revision/hash plus original MealPlan/RecipeVersion/Step/policy pins and actual member Decimal Servings, without generated UUID/created_at driving semantic identity. Shopping numbers remain Shopping-owned; neither eligibility publication nor Prep planning mutates Pantry, changes `Serving`, creates PreparedBatch, or asserts an actual time/safe storage state.

## 5. Fresh, replay, conflict, invalidation and rollback contract

| Scenario | Required future behavior |
| --- | --- |
| First trusted reviewed package | Validate exact source/rights/steps, reviewer independence, complete applicability, accepted package version/hash; accept **only** matching scoped entries for current fixture. No unreviewed fallback |
| Exact replay/restart | Same code/payload/release pin resolves identical typed verdicts, stable eligibility fingerprint and deterministic Prep semantic trace; idempotent generated PrepPlan revision |
| Same `publication_id` with changed bytes, conflicting duplicate keys or altered instruction | **CONFLICT**, reject entire new publication/read; do not quietly choose latest or accept a self-consistent forged hash |
| New RecipeVersion, corrected Step/process hash or changed applicability/source review | Earlier eligibility does not match; issue `UNKNOWN/REVIEW_REQUIRED`, stale any newer derived Prep/PDF until independently reapproved |
| Revoked source right/policy or withdrawn reviewer approval | New generation fails closed to unresolved/no accepted executable task; historical immutable plans remain auditable **but not current usable instruction** |
| Missing publication file/deployment resource or corrupt serialization | Startup/read must report explicit unavailable authority; never default `APPROVED` or re-parse source prose as executable instructions |
| Unexpected publish/reader failure during plan generation | Never commit partial Prep parent/tasks/obligations. Correctly classified unknown permits a truthful `INCOMPLETE` plan only with validated authoritative MealPlan and quantities |
| Rolling back published package or deploying older release | Pin to accepted immutable revision; previously created newer Prep/PDF marked stale/unavailable; no in-place rewrite of history or guessed task status |

**No migration currently proposed:** frozen three-table Prep model (`prep_plans`, `prep_tasks`, `prep_unresolved_obligations`) and existing accepted reason/status codes are assumed sufficient for **same-day ungrouped** tasks (`shared_work_group_key=NULL`), with review/classification provenance on the accepted header/step fields. This assumption must be tested in PR10-A/B preflight; if package publication introduces new authoritative storage, identity, reader, DB transaction or schema field, the implementation gate must explicitly reopen **before runtime**. No number `0044` is reserved by this PR.

## 6. Bounded future acceptance / adversarial reviewer challenges

**Positive publication acceptance — later, not exercised here:** one independently approved, release-pinned `NO_NUMERIC_DIRECTION + APPROVED_IMMEDIATE` package entry for **each** of the two actual current fixture COOK_RECIPE first steps, with full source/RecipeVersion/hash/rights and actual scaled Decimal ingredients verified. Show accepted reviewer decision; if either does not qualify, explicit `NO_GO` and no substitute new recipe hunt. Two distinct events/one actionable task each are only the **positive task sub-gate**; Gate2 additionally requires at least one **honest unresolved negative case** and the full real-service Planner → Shopping → Prep → PDF chain.

**Negative acceptance matrix for later executable verification:**

1. Numeric direction hidden in ranges, Cyrillic decimal, ingredient split, time/equipment/process parameters or changed factor → no false `NO_NUMERIC_DIRECTION`; `STEP_QUANTITY_REVIEW_REQUIRED` when needed.
2. Right text with wrong RecipeVersion/Step UUID, step position/hash, source original/rights pin or process revision → **reject**.
3. Same canonical recipe code/ingredient identity but a different immutable version → no inherited eligibility.
4. Curator approves self; independent reviewer identity missing; pending/revoked/expired status, unknown/duplicate package key, wrong binary hash, untrusted repo artifact → **reject**.
5. Source text says blanch/sauté but no independently sufficient same-day process/equipment/source applicability for actual scale → classification remains **unapproved**, no invented temperature, time or safe holding.
6. Wrong Household, moved Serving, non-finite/invalid Decimal, mixed meal-source fake recipe or member excluded from a recipe → fail source/Household validation, **no partial authoritative Prep writes**.
7. Exactly one approved event, or **all-UNKNOWN/zero-actionable** fixture → technical Gate2 **NO_GO** (not an empty `COMPLETE` shortcut).
8. Changed MealPlan, current classification revocation or source hash under stale Prep/PDF → versioned invalidation, no silent history mutation.
9. Same-day recipe prep must **not** be grouped across lunch/dinner, asserted cooked-stock, advance-prep, fridge/freezer suitability, savings or guaranteed time. `PR10-FD-META=BLOCKED/TIME_UNRESOLVED` remains true.

**Verification tier:** This document and queue are **docs only**. Validate links, source equality and prior pins, JSON syntactic integrity, complete header/dependency and preservation obligations, current branch diff/whitespace and exact-head Docs CI. No production tests, migration, schema, backend service, live source-read, physical kitchen procedure or real-family proof is claimed.

## 7. Contract result, stop and post-merge next bounded task

**FACT:** two explicit historical source steps and credible immediate action candidates; current independently approved executable count = **0**. No accepted eligibility publisher/read contract is implemented.

**DECISION PROPOSED:** adopt the *source ownership and typed read boundary* above **after independent docs review and merge**, then perform **one independently reviewed curation/publication proof for those exact two steps** (with a current actual fixture re-pin) and explicit `GO/NO_GO` before authorizing PR10-A. This eliminates vague "find more recipe" work while protecting against false positive approval.

**STOP RULE:** if a reviewer rejects either step for unclear/process-unsafe scale or publication/read cannot preserve the accepted source authority, report the precise blocker and **return to the owner**; do **not** expand to more recipes, revise Planner/Serving, implement new Prep tables or enable runtime by documentation fiat.

**UNCHANGED:** `NO_GO_TO_PR10_CORE_RUNTIME` today; `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`; `SAFE_BATCH_READY` and measured `PORTION_RELEASE_READY=PASS` unmet; Gate2/Gate3/real-family release unchanged. Nothing here decides future confirmed PreparedBatch/stock, safe freezing, child nutrition, medical advice or consumer claims.
