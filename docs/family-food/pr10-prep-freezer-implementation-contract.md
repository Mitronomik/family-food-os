# PR10-ARCH — Prep / Freezer implementation contract gate

**Status:** PROPOSED, docs-only; independent review and merge required before PR10 runtime.
**Issue:** #191.
**Accepted base:** main@545c86b4dd39ba3b14e0c36fcbc4733da1137d14 (PR #190 merged 2026-10-10).
**Owning sequence:** PR9 Shopping merged → this PR10-ARCH contract → bounded PR10 implementation → PR10-PDF → Gate 2 MVP0 backend.
**Authorities:** [root AGENTS](../../AGENTS.md), [roadmap](master-roadmap.md), [2026-09-13 addendum](master-roadmap-addendum-2026-09-13.md), [architecture](architecture.md), [architecture compatibility](architecture-addendum-2026-09-13.md), [food composition](food-composition-and-assembly.md), [Russian display](russian-language-contract.md), [security](security-architecture.md), [verification policy](verification-policy.md).

**Document rule:** All decisions below are *proposals*, not accepted product/runtime contracts until this docs-only gate is independently reviewed and merged. An implementation preflight that disproves a proposal must reopen the gate, not quietly redesign production.

## 1. Goal, rationale, and excluded work

PR10 makes a verified week's meals easier to execute by deriving a deterministic, versioned, Household-owned preparation plan from authoritative MealPlan and RecipeVersion facts. It should identify what can be done in advance, what cannot safely be inferred, and what remains to be done, in Russian.

The plan is an **immutable proposal**, not evidence that anything was cooked, frozen, consumed, reserved or placed into a freezer. PR10 does not invent cooking duration, yield, food safety, prepared inventory, reheating instructions, delivery, grocery prices or purchase availability.

In this gate: documents/state only. **No** production code, SQLite migration, recipe publication, new freezer/shelf-life data, AI, PWA, Retail, PDF, Auth/PostgreSQL or Pantry writes. No claim that Gate 2 passed.

## 2. FACT — accepted main preflight (2026-10-10)

- PR9-A (#186), PR9-B (#188) and PR9-C (#190) are merged. The generic Shopping Engine uses versioned immutable snapshots, Decimal scaling, dated FEFO provenance and Household-scoped HTTP. Shopping generation **does not mutate Pantry**. Shopping V1 supports quantity COMPLETE/INCOMPLETE and independently UNKNOWN prices.
- In **backend/app/domain/meal_plans.py**, MealPlan has Household ownership, week_start, immutable revision_number/id and supersedes_plan_id. HouseholdMealEvent has local_date, position, source_kind, nullable recipe_version_id/source_reference; Serving has a member and exact Decimal portion_servings. Current MealSourceKind values are COOK_RECIPE, ASSEMBLY, LEFTOVER, PREPARED, READY_MEAL, ORDER_OUT and EAT_OUT. Only COOK_RECIPE is directly pinned to RecipeVersion in the accepted PR7 model.
- In **backend/app/domain/food_recipes.py**, RecipeVersion has nullable prep_time_minutes, cook_time_minutes, total_time_minutes, batch_friendly, freezable, storage_days_fridge and storage_days_freezer. RecipeVersionDetail has version-pinned ingredients, ordered RecipeSteps (instruction and optional stage_code), and equipment codes. RecipeVersion has source/version/verification/rights provenance. **Nullable metadata is not proof of source-backed, complete or safe preparation guidance.**
- The current RecipeVersion model does **not** expose source-backed, structured freeze_stage, defrost_method, reheat_method, storage_instruction, per-step active/passive duration or a reusable cross-recipe prep-component identity. RecipeStep.stage_code is not by itself a verified dependency graph or storage-safety assertion.
- Pantry has FoodIngredient-based items and movements with Household scope, amount, location and expiry. There is no accepted Household PreparedBatch or consumed-serving inventory contract. The last active custom SQLite migration on accepted main is **0043_shopping_engine**. The next identifier must be revalidated when runtime starts.
- Gate 2 is **after PR10 and PR10-PDF**: one Household, three members, thirty verified recipes, 80–120 FoodIngredient, seven-day MealPlan/Servings, Pantry-aware ShoppingList, PrepPlan and backend PDF; AI disabled and no Retail connector. PR10 alone does not close Gate 2.

**ASSUMPTION TO TEST:** Enough accepted recipes have trustworthy time, batch and storage metadata to produce useful early-prep suggestions. The existing code fields do not prove coverage or verified freezer instructions. Runtime may need a separate, bounded metadata-readiness decision *before* freezer recommendations can be claimed.

## 3. Source and capability authority matrix — PROPOSED

| MealEvent source kind | PR10 V1 prep input | Treatment |
| --- | --- | --- |
| COOK_RECIPE | Exact pinned verified RecipeVersion, step instructions, eligible servings | Can produce source-backed planning tasks; positive Decimal scale is checked, and unsafe/unknown early-prep guidance is withheld |
| ASSEMBLY | No accepted production RecipeAssembly execution graph for Prep V1 | Explicit unsupported task/obligation, never decompose ingredient work from arbitrary source_reference |
| LEFTOVER | Requires a confirmed household remaining-serving inventory record | Do not suggest fresh ingredient prep or assert the leftovers physically exist; represent supply uncertainty |
| PREPARED | Requires confirmed Prep execution/PreparedBatch authority | Do not assume a planned task created stock or claim reheating/storage facts |
| READY_MEAL | Separately sourced ready-food preparation information | No invented home-cooking steps; optionally explicitly unsupported if needed by UX |
| ORDER_OUT / EAT_OUT | Not kitchen-prep demand | No kitchen prep task, no fabricated unresolved quantity |

A mixed-source week may have a **reviewable partial PrepPlan** with explicit unresolved work. An entirely out-of-home week may correctly have zero tasks. Never force one recipe onto nonrecipe events just to fill a plan.

**Safety:** A missing recipe version, invalid Serving/Household/event join, conflicting required quantity, corrupted provenance or unsafe required conversion is **BLOCKING** (no purported authoritative plan persisted). Valid but incomplete recipe time/storage/reheat information gives **explicit UNKNOWN/UNSUPPORTED** capabilities, not guessed minutes or storage advice.

## 4. V1 deterministic calculation — PROPOSED

1. Input is one verified MealPlan revision with exact events/Servings, frozen RecipeVersionDetails, and accepted Household local timezone. Compute each event's desired servings as the exact sum of its participating Servings; use Decimal, never float, and reuse accepted scale_recipe semantics without introducing Shopping-equivalent nutrient or grocery authority in Prep.
2. **Minimum executable baseline:** render ordered, source-backed RecipeStep-derived tasks for COOK_RECIPE events; order by (Household-local meal_date, event.position, event UUID, step.position, stable ID). This yields a truthful plan even when batch grouping is unsupported. Retain exact source recipe version and step pins for replay and localized display.
3. Same RecipeVersion on multiple meal dates is only a **batch candidate** when the immutable version explicitly says batch_friendly=true and accepted storage/cooking guidance proves compatibility across dates and states. Aggregating two unrelated foods with the same FoodIngredient code, or two recipes with similar text, **does not** prove identical intermediate preparation or mass/form equivalence. No cross-recipe merge in V1 without a separate accepted shared-component authority.
4. Preparation earlier than required meal date requires safe, versioned storage/hold/defrost/reheat facts applicable to the exact food, stage and duration. Existing storage_days_fridge/freezer and freezable flags can filter **candidates**, but cannot alone create specific freezing instructions, cooked shelf-life guarantees or safe transitions. When evidence is insufficient, schedule on the meal date or show an explicit review-required suggestion; never silently backdate cooking to Sunday.
5. Proposed default scheduling is conservative and **sequential**. The accepted total/prep/cook time fields can be displayed as source-level optional estimates only when present and meaningful; a sum is not automatically active work duration or wall-clock optimized time. There is no source authority for step-level active/passive minutes or automatic equipment-parallel constraints. Unknown time remains null and must not become 0 minutes.
6. A verified RecipeStep's Russian text can be presented verbatim when display readiness is established. Machine source/stage codes may be included as technical fields but never used as English consumer labels or instructions; no LLM-authored source authority. Unexpected language/display readiness becomes an explicit blocker/unsupported state, not a fallback label.
7. Prep output must be **independent of Retail and AI**. It does not allocate Pantry lots, overwrite Shopping quantities, consume a lot twice, infer purchase requirements, or invent a frozen household stock record. If a later PR proposes using Shopping/Pantry availability in prep decisions, the source snapshot and transaction dependency contract must first be amended under review.

**Versioning rule:** Stable sorted canonical input + deterministic policy/config/engine version must yield identical semantic task order, amounts, warnings and content fingerprint. Generated UUIDs/created_at may differ but are not part of semantic identity.

## 5. Immutable schema/lifecycle proposal (NOT YET AUTHORIZED)

Use the least persisted surface that genuinely supports reproducibility:

- **PrepPlan** immutable header: UUIDv4 id, household_id, source_meal_plan_id, source_plan_revision_number, Household-local as_of_date where it affects policy, prep_engine_version, policy/config version, source_fingerprint, content_fingerprint, derivation status COMPLETE or INCOMPLETE, original-source provenance descriptor, supersedes_prep_plan_id optional, UTC created_at.
- **PrepTask** immutable child: UUIDv4 id, prep_plan_id, household_id, ordinal, source_meal_event_id, pinned recipe_version_id and optional recipe_step_id, Household-local scheduled date, source-backed Russian instruction/reference, exact target servings or units only where authorized, optional time/equipment metadata, explicit capability and warnings. Do not persist a task as COMPLETED in the immutable derived snapshot.
- **Unresolved prep work and warnings** must be distinguishable from executable tasks and contain event-level source/reason and Russian display. The exact representation (separate third table versus strongly typed immutable payload) remains a **review decision** because both traceability and no-schema-bloat matter. It must never be encoded as an invented zero-duration task.
- **Dependency graph:** V1 ordered sequence is authoritative; a richer predecessor DAG/table is deferred unless accepted recipe process metadata and a concrete test require it. A fabricated edge from similar ingredient names is not permitted. Upgrade must not introduce optional-null FKs that allow cross-household task access.

**Lifecycle:** generate atomically, keep prior revisions readable, get/current/history scoped by Household, detect stale when current MealPlan revision or pinned recipe process metadata/policy changes, and regenerate an immutable successor. Identical input/source fingerprints must replay idempotently (no fork). When inputs return exactly to an earlier fingerprint, an old immutable version may become current again; do not rely on mutable is_current.

**Schema boundary:** the approved main currently ends at SQLite migration 0043, so **0044 is a candidate only**, not reserved until current main/branch ownership is reconciled. No runtime Prep schema, recipe metadata migration or PreparedBatch migration is authorized by merging this contract alone. Preserve historical migration lineage and backups.

**Cross-context:** PR10 plans from MealPlan and pinned recipe process truth; **no hard dependency on ShoppingList creation** for V1 planning. The eventual PR10-PDF must separately validate MealPlan, ShoppingList and PrepPlan source revisions before combining them. If a stricter Shopping-input pin is required, amend this contract rather than implementing a hidden transitive dependency.

## 6. Transaction and failure semantics — PROPOSED

- A backend-owned PrepService coordinates immutable plan+task persistence through protocol-owned repositories and one SQLAlchemy Core / SQLite UoW. Domain/service imports no SQLAlchemy, DBAPI or FastAPI.
- For any generation write: physical SQLite BEGIN IMMEDIATE **before** authoritative MealPlan/Recipe/process-data reads and before checking an existing PrepPlan, so no competing writer can invalidate the snapshot before commit. Reuse the accepted Shopping UoW locking approach where compatible, without extending Shopping ownership to Prep.
- Insert header, tasks and unresolved source data atomically; validate source/revision pins while the writer reservation is held; commit once. Any unexpected error, FK violation, duplicate source conflict or failed child insert rolls back **everything**. Busy/locked returns an application-level retryable conflict, not a raw DBAPI exception.
- Never create PantryMovement, change PantryItem, reserve stock, create PreparedBatch or mark instructions completed during generation, retry, staleness query or rollback.
- Tenant scope is mandatory on every read/write, including guessed UUIDs and history. This is Household selection/scoping, **not Auth**. Auth/membership comes at the shared-deployment gate.

**Separate future command:** confirmed user execution of a task would need its **own** reviewed persisted identity, idempotent execution history, stock/food-safety and Pantry transaction design. This contract explicitly does not approve execution or prepared inventory publication in the PR10 planning slice.

## 7. Proposed API and Russian consumer representations

Support Household-scoped generate, immutable detail, current/missing/stale, explicit regenerate and history using the same minimal response discipline as accepted Shopping V1. Exact route paths and response DTO are implementation details **only within** the accepted capability contract. Use typed IDs, strict body/query validation (including unexpected parameters), Russian-safe 404/409/422/503, no database driver details.

Response separates: machine status/reason, Russian message, ordered task actions, scheduled dates, nullable truthful durations, source IDs, storage/freezer readiness, warnings and explicit unresolved obligations. No unsupported consumer text (English/free-form source) is surfaced as verified guidance. For no safe freezer action, say in Russian that the required guidance is unavailable; never show a guessed freezer expiry as fact.

## 8. Required adversarial verification matrix

| Surface | Minimum executable evidence |
| --- | --- |
| Pure calculation | Exact Serving scaling for 3-member Household; stable order/replay; 7 days; deterministic identical input; without AI |
| Source kinds | All seven kinds; COOK_RECIPE verified pins, ASSEMBLY unsupported, LEFTOVER/PREPARED no fabricated supply, out-of-home zero prep |
| Process metadata | Nullable time/batch/freezer/storage; mismatched/absent steps; Russian display; invalid/negative quantities; no guessed stages, storage time or duration |
| Sharing | Same exact recipe repeated; candidate only under accepted safe metadata; unrelated recipes sharing food are not silently merged; unknown yield/form blocked |
| Dates | Household-local days; same-day vs prior-day holds; expiry/storage boundary when proven; daylight-saving edge; no guaranteed Sunday cook |
| Source revisions | New MealPlan or revised recipe instructions => STALE, immutable successor, old read, exact source revert and idempotent replay |
| Persistence | Fresh/upgrade migration and lineage, FK, real rollback after header and after child, source-read atomicity, separate-connections same-input concurrent generation |
| Household | Cross-home guessed plan/task/history/GET/current/POST => nondisclosing not found; no data exposure |
| Side effects | Before/after PantryItems and PantryMovements identical on success, stale, conflict and failure; no prepared/freezer stock |
| API | Russian-safe typed status/errors; no client-supplied truth; invalid query/body/UUID 422; no raw provenance or unsafe English fallback |
| Gate 2 readiness | One Household, 3 members, 30 verified recipes, 80–120 canonical foods; actual 7-day MealPlan + Shopping + proposed Prep (PDF later); report blockers, never mislabel partial proof as Gate 2 COMPLETE |

**Verification tier:** docs-only contract: source/link checks, scope audit, whitespace. Runtime PR10-B involving migration/UoW must execute fresh+upgrade/rollback/concurrency tests and full backend **plus launcher** regression on exact frozen head. PR10-A pure tests and PR10-C API tests are scoped appropriately; run broader checks when shared startup is changed. Record exact tests and evidence; never weaken acceptance.

## 9. Proposed bounded implementation order (AFTER gate merge)

1. **PR10-A — pure deterministic Prep calculator:** source-kind matrix, exact servings/process tasks, uncertainty and proposed scheduling, stable fingerprint; no DB/API. Recheck data-readiness without importing unverified freezer/storage facts.
2. **PR10-B — Prep persistence/transaction:** only the accepted minimal schema and next valid migration; immutable snapshot, atomic UoW, retries/staleness, Household isolation, rollback and concurrent requests.
3. **PR10-C — Prep API:** typed Russian consumer-safe generate/get/current/regenerate/history, strict input rejection, no execution or Pantry writes.
4. **Optional separately scoped source-metadata/evidence correction** if trustworthy batch/storage/freezing process data is insufficient. This is not permission to publish LLM-invented steps or silently expand PR10-A/B/C.

These are candidate slice names/order for reviewer approval, **not independently authorized runtime PRs**. PR10-PDF starts only after the accepted Prep planning capability exists, followed by its own artifact-specific contract/review if required. Gate 2 closure waits for the full real service/repository-backed fixture, not a component-level green suite.

## 10. Preservation matrix and reviewer challenges

| Accepted authority | Required preservation |
| --- | --- |
| PR7/PR8 MealPlan and Serving | Versioned plan, mixed meal sources, member-specific portion scale, local dates, revision/staleness |
| PR4/PR6 recipe/food/nutrition | Immutable verified RecipeVersions, source rights, Russian steps, form/unit and exact numeric provenance |
| PR9 Shopping | Immutable purchase quantities, Pantry FEFO/fingerprints, UNKNOWN price and Household isolation; no new Retail linkage |
| PR5 Pantry | Quantities, expiry/location, movement ledger and side-effect-free plan generation |
| SQLite/CI | Sole custom migration lineage, portable UUID/UTC, BEGIN IMMEDIATE proof, all historical regressions |
| Security and UX | Russian display, no code/secret leak, Household scope, AI=false, no invented safety truth |
| Later PR10-PDF/Gate 2 | Derivation/staleness pins and transparent UNKNOWN/PARTIAL states rather than fake complete vertical slice |

**Reviewer must challenge:** (1) Is the minimal model sufficient to demonstrate useful prep rather than merely reprint recipes? (2) Is any accepted recipe actually freezer-ready with supported stage/reheat/storage instructions? (3) Is a separate unresolved entity required? (4) Is the chosen Prep source identity independent of Shopping correct for Gate 2 and PDF? (5) Does recipe process metadata change require a new RecipeVersion rather than in-place edits? (6) Does any proposed early-prep schedule violate storage/food-safety uncertainty? (7) Are we mistakenly treating nullable cookbook metadata as an approved authority?

## 11. Explicit decisions, assumptions and open questions

**FACT:** PR9 merged; Gate 2 not complete; current recipe metadata is nullable and lacks structured freeze-stage and reheating methods; no accepted PreparedBatch execution authority.

**ASSUMPTION:** A deterministic task-by-recipe baseline with limited proven grouping is the smallest useful PR10 V1. This must be evaluated on actual accepted verified recipes; do not claim time savings without evidence.

**PROPOSED DECISION:** immutable PrepPlan/PrepTask planning separate from confirmed execution; no automatic freezing/storage claims without verified instructions; versioned deterministic source snapshot and Household transaction; no dependency on Retail, AI or mutable Pantry.

**OPEN QUESTION / reviewer decision:** exactly two Prep tables vs a separate unresolved-obligation table; how much structured shared-work identity is needed to make an actually useful batch plan; whether verified freezer execution guidance requires a separately accepted recipe metadata/publication extension; source-linked process step completeness for the Gate 2 fixture; and whether any Prep calculation must pin Shopping beyond the PDF composition boundary. Close these before accepting runtime design—do not assume away unresolved safety or immutability issues.

**Stop condition:** deliver this document as a docs-only independently reviewed PR, with corresponding state updates. Never use the docs PR itself as authority to start PR10 runtime before merge and accepted decisions. Do not begin PR10-PDF, PWA, Retail or AI.
