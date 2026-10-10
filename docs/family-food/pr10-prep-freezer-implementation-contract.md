# PR10-ARCH — Prep / Freezer implementation contract gate

**Status:** PROPOSED, docs-only; independent review and merge required before PR10 runtime.
**Issue:** #191.
**Accepted base:** main@545c86b4dd39ba3b14e0c36fcbc4733da1137d14 (PR #190 merged 2026-10-10).
**Owning sequence:** PR9 Shopping merged → this PR10-ARCH contract → mandatory PR10-META readiness evidence/publication gate → separately approved bounded PR10 implementation → PR10-PDF → Gate 2 MVP0 backend.
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

**FACT — bounded readiness audit:** [30 recipe candidates checked against accepted DC4](pr10-prep-metadata-readiness-audit.md) (all are from the accepted 51-recipe DC4 list): batch_friendly **0/30 non-null**, freezable **0/30**, fridge/freezer storage days **0/30**, prep_time **0/30**, total_time **0/30**, cook_time **1/30**. Across 109 source steps, a conservative numeric-text prefilter identified 16 potentially quantitative steps in 12 recipes; classification is not proven. This **does not** certify the future Gate 2 fixture or live SQLite versions. The previously stated assumption that published recipes already support useful batch/freezer optimization is **disproved for this audited sample**.

**PROPOSED DECISION:** PR10-META is a **mandatory separately reviewed readiness gate** (source inspection and, if needed, separately authorized immutable recipe metadata publication) before batch/freezer runtime can be accepted. No early cooking, freezing, storage duration or claimed time-saving may be inferred from missing metadata. The actual pinned Gate 2 recipes must also pass source/step readiness validation.

## 3. Source and capability authority matrix — PROPOSED

| MealEvent source kind | PR10 V1 prep input | Treatment |
| --- | --- | --- |
| COOK_RECIPE | Exact pinned verified RecipeVersion, step instructions, eligible servings | Can produce source-backed planning tasks; positive Decimal scale is checked, and unsafe/unknown early-prep guidance is withheld |
| ASSEMBLY | No accepted production RecipeAssembly execution graph for Prep V1 | Explicit unsupported task/obligation, never decompose ingredient work from arbitrary source_reference |
| LEFTOVER | Requires a confirmed household remaining-serving inventory record | Do not suggest fresh ingredient prep or assert the leftovers physically exist; represent supply uncertainty |
| PREPARED | Requires confirmed Prep execution/PreparedBatch authority | Do not assume a planned task created stock or claim reheating/storage facts |
| READY_MEAL | Separately sourced ready-food preparation information | No invented home-cooking steps; emit READY_MEAL_PREP_UNSUPPORTED until reviewed process truth exists |
| ORDER_OUT / EAT_OUT | Not kitchen-prep demand | No kitchen prep task, no fabricated unresolved quantity |

A mixed-source week may have a **reviewable partial PrepPlan** with event-level unresolved work in the dedicated entity frozen in §5. An entirely out-of-home week may correctly have zero tasks. Never force one recipe onto nonrecipe events just to fill a plan.

**Safety:** A missing recipe version, invalid Serving/Household/event join, conflicting required quantity, corrupted provenance or unsafe required conversion is **BLOCKING** (no purported authoritative plan persisted). Valid but incomplete recipe time/storage/reheat information gives **explicit UNKNOWN/UNSUPPORTED** capabilities, not guessed minutes or storage advice.

## 4. V1 deterministic calculation and instruction authority — PROPOSED

1. Read one verified immutable MealPlan revision (Household-local dates, mixed sources and member Servings) plus pinned RecipeVersionDetails. For each COOK_RECIPE event, `target_servings = Σ participating Serving.portion_servings` exactly in Decimal. Scale the **structured RecipeIngredients** with the accepted `scale_recipe` formula; do not derive amounts from RecipeStep prose or mutate Shopping quantities. Validate recipe pins and Household/event/Serving relationships, failing closed on invalid sources.
2. Build an event-to-task baseline in deterministic order: (local_date, event.position, event UUID, RecipeStep.position, stable task key). A source step may become an **executable task only after** Russian-display and numeric-instruction safety validation (§4.1). Unverified steps are not executable instructions; represent the event/step as an unresolved obligation (§5).
3. **Minimum PR10 usefulness contract:** chronological restatement of recipe steps alone is NOT a PR10 Prep/Freezer exit. The frozen Gate 2-like 3-member, 7-day fixture must demonstrate at least **one** verified, actually actionable *ahead-of-use or reusable preparation* operation serving **two or more distinct MealEvents**, where version-pinned process/portion and storage transitions prove that one preparation safely replaces duplicate individual work. The acceptance trace must identify the input events, origin RecipeVersion/process evidence, total output/portions, scheduled preparation and later required dates, safe holding/reheat/defrost evidence, and compare **baseline per-event execution actions** versus **deduplicated actual prep actions** (at least one fewer duplicated action). This is a work-count proof; never claim minutes saved without measured authority. The 30-candidate audit currently cannot pass this gate.
4. Group repeated source work only when a reviewed, versioned **shared-preparation identity and compatible state transition** explicitly binds all grouped events (same RecipeVersion alone is not sufficient). Preserve every event's needed servings and source step. V1 must **not** merge unrelated recipes by ingredient names or assume raw/cooked/storage equivalence.
5. Early cooking, refrigeration and freezer actions require reviewed stage-specific hold/storage/reheat/defrost evidence for the actual resulting food form and entire interval. Nullable `batch_friendly`/`freezable`/storage flags can indicate candidates, **never a safe procedure by themselves**. If the source lacks evidence, no early/reusable executable task is scheduled. Same-day source-backed tasks may remain reviewable but `PR10 usefulness` remains **BLOCKED** until the #3 criterion is demonstrated.
6. Known RecipeVersion time estimates can be displayed as **optional source estimates only**; there is no per-step active/passive duration authority, equipment-parallelism model, or trusted elapsed time benefit in the current catalogue. Null time remains UNKNOWN (not zero). Scheduling is sequential unless reviewed dependency/equipment evidence supports otherwise.
7. Prep planning is strictly independent of Retail/AI and never writes Pantry, creates PreparedBatch, consumes/reserves Shopping supply or invents prices. A future dependency on Shopping source state requires a separately reviewed amendment to fingerprints/UoW.

### 4.1 Numeric instructions: fail-closed rules

**Canonical quantity authority:** pinned structured RecipeIngredient/UnitCode and scaled Decimal totals for the specific MealEvent; optional ingredient rows and unresolvable form/units retain their existing domain safety semantics. **Never multiply, replace or recompute quantities by parsing RecipeStep text.** HTTP/UI shows a distinct Russian block of authoritative scaled ingredient quantities (ingredient identity, form/unit, exact amount, target servings and original RecipeVersion ID). Source instructions are not a competing ingredient list.

Classify every source RecipeStep **per immutable RecipeVersion + step hash** before it becomes a scaled executable instruction:

- `NO_NUMERIC_DIRECTION`: source-verified, Russian-ready text with no quantity/process-size/time/temperature/vessel numbers; safe to show unchanged alongside structured scaled quantities.
- `REVIEWED_INVARIANT_PROCESS_NUMBER`: reviewed and explicitly typed as *per-piece cutting/forming size, fixed working-batch size, stage temperature, time, vessel dimension or other non-ingredient-total process parameter* that **does not contradict** scaled structured amounts at the proposed batch size. Retain original source text and show separate Russian context that the number is a process parameter. Temperature/time do not automatically scale; a changed batch size that invalidates equipment/cook safety **revokes this classification** and yields review-required.
- `REVIEWED_INGREDIENT_AMOUNT`: source contains a concrete ingredient quantity. Its corresponding canonical `RecipeIngredient`, unit/form/basis, scope (whole recipe vs step fraction) and source serving basis must be explicitly mapped and checked against the exact scaled input. **Source step text with base-recipe numbers must not be passed off as the new exact quantity if target_servings differs**. The original remains immutable provenance; a reviewed version-linked, scale-safe **quantity-neutral Russian instruction** may be shown, with exact scaled ingredient amounts separately. No LLM text substitution or in-place RecipeStep edit. Without that vetted instruction, create `STEP_QUANTITY_REVIEW_REQUIRED` and withhold the executable step.
- `AMBIGUOUS_OR_UNREVIEWED_NUMBER`: anything not fully typed/mapped/reconciled (including apparent `г`, `мл`, `шт`, totals embedded in prose, implicit source fractions, ranges or ambiguous yield) is `STEP_QUANTITY_REVIEW_REQUIRED`; do **not** show source text as a scaled executable step. Keep original text only in restricted immutable provenance/review context, with safe Russian explanation and separately displayed source-backed scaled ingredients.

Classification is a **reviewed publication/evidence decision**, not an automatic regex result. A regex can flag candidates but cannot whitelist them. Every new RecipeVersion/process correction invalidates prior classification until revalidated. Store explicit step hash, classification/version, reviewed source reference and mapping (or review block) in the Prep source fingerprint. An absent/invalid classification fails closed for executable action; the source snapshot and the unresolved reason remain inspectable.

**Examples from [30-recipe audit](pr10-prep-metadata-readiness-audit.md):** `75–100 г` cuts, `15–20 г` formed balls, `2–3 штуки` cracked eggs are *possible process-size parameters*, not silently scaled total ingredients; `5,3 г масла total` requires ingredient/step-split reconciliation. Even at scaling factor 1 an unreviewed numeric step is not automatically cleared. Tests must cover scale factors 1, noninteger and >1, mixed per-step/whole-recipe amounts, temperature/time/portion size, changed RecipeVersion hash and disagreement between source text and canonical ingredient totals.

**Status effect:** If required COOK_RECIPE steps are withheld due to numeric conflict/unreviewed language, persist a reviewable **INCOMPLETE** PrepPlan with `STEP_QUANTITY_REVIEW_REQUIRED` or `PROCESS_STEPS_UNVERIFIED` obligation, **never** an executable task that contradicts quantities. If the structured authoritative ingredient mapping itself is corrupt, reject generation entirely (BLOCKING/no snapshot). This distinction preserves both safety and meaningful partial history.

**Versioning rule:** canonical ordered authoritative inputs + approved step classifications/process metadata + policy/config/engine versions yield stable source/content fingerprints. Generated UUIDs and created_at never enter semantic identity.
## 5. Immutable three-table schema/lifecycle — FROZEN PROPOSAL (NOT YET AUTHORIZED)

**Decision before merge:** exactly **three normalized, immutable, Household-owned tables**. The former two-table-vs-payload option is closed. These names are Prep-owned; they do not inherit legacy ProductionBatch, Shopping obligations or future confirmed execution semantics.

1. **`prep_plans`** (PrepPlan): `id UUIDv4 PK`, `household_id NOT NULL`, `source_meal_plan_id NOT NULL`, `source_plan_revision_number > 0`, `as_of_date DATE NOT NULL` (Household-local snapshot as-of), `engine_version`, `policy_version`, `config_fingerprint SHA256`, `source_fingerprint SHA256`, `content_fingerprint SHA256`, `status` CHECK IN (`COMPLETE`, `INCOMPLETE`), immutable `provenance_json` (internal authoritative source pins, process/step classification hashes and safe metadata), `supersedes_prep_plan_id NULL`, `created_at UTC-aware`. Unique `(household_id, source_meal_plan_id, source_fingerprint)`; `UNIQUE(id, household_id)`; indexed `(household_id, source_meal_plan_id, created_at)`. `supersedes` points to a PrepPlan of the **same Household**; immutable history is retained.
2. **`prep_tasks`** (PrepTask): `id UUIDv4 PK`, `prep_plan_id NOT NULL`, `household_id NOT NULL`, `ordinal > 0`, `source_meal_event_id NOT NULL`, `recipe_version_id NOT NULL`, `recipe_step_id NOT NULL` for executable source steps, `scheduled_local_date DATE NOT NULL`, `required_meal_date DATE NOT NULL`, exact `target_servings DECIMAL TEXT > 0` with explicit versioned precision, reviewed `instruction_ru NOT NULL`, source `step_hash`, numeric safety `classification_version/reference`, optional source-backed `duration_minutes`/`equipment` (NULL if unknown), and optional reviewed `shared_work_group_key`. `UNIQUE(prep_plan_id, ordinal)`, `UNIQUE(prep_plan_id, source_meal_event_id, recipe_step_id)`. Each task row remains the **reviewed executable step contribution of one event**, not necessarily one distinct physical kitchen operation. Only explicitly reviewed compatible rows can share a deterministic non-null `shared_work_group_key`: one unique group key equals one physical prep action. Total combined Decimal target servings, ordered MealEvent IDs and per-event contributions must be retained in the immutable source descriptor. Null group keys each count as one action. Validate all group member event IDs against the source MealPlan; the UI can coalesce them into one action without losing references. No `completed` flag, zero-duration placeholder or Pantry write.
3. **`prep_unresolved_obligations`** (PrepUnresolvedObligation): `id UUIDv4 PK`, `prep_plan_id NOT NULL`, `household_id NOT NULL`, `ordinal > 0`, `source_meal_event_id NOT NULL`, `source_kind NOT NULL` (exact accepted seven-kind enum), `reason NOT NULL` in frozen V1 reason set below, `recipe_version_id NULL`, `recipe_step_id NULL`, `review_ref NULL`, `description_ru NULL`, source/provenance pin in header. `UNIQUE(prep_plan_id, ordinal)` and `UNIQUE(prep_plan_id, source_meal_event_id, reason, recipe_step_id)` enforced by a SQLite **unique expression index** on `(prep_plan_id, source_meal_event_id, reason, COALESCE(recipe_step_id, ''))`, so NULL step IDs cannot evade uniqueness (all actual recipe_step_id values are nonempty UUIDs). Multiple distinct problematic steps must remain identifiable; per-event issues must not silently collapse.

**Frozen unresolved V1 reason codes:**

| Code | When emitted | Required source fields |
| --- | --- | --- |
| `ASSEMBLY_UNSUPPORTED` | ASSEMBLY lacks accepted process graph | meal_event_id, source_kind |
| `LEFTOVER_SUPPLY_UNVERIFIED` | LEFTOVER lacks actual confirmed prior supply | meal_event_id, source_kind |
| `PREPARED_SUPPLY_UNVERIFIED` | PREPARED lacks confirmed batch/execution | meal_event_id, source_kind |
| `READY_MEAL_PREP_UNSUPPORTED` | READY_MEAL lacks reviewed household prep/handling path | meal_event_id, source_kind |
| `PROCESS_STEPS_UNVERIFIED` | COOK_RECIPE lacks verified source steps or Russian-ready executable direction | meal_event_id, recipe_version_id |
| `STEP_QUANTITY_REVIEW_REQUIRED` | COOK_RECIPE step contains ambiguous, conflicting, or unmapped numeric text | meal_event_id, recipe_version_id, recipe_step_id |
| `SAFE_BATCH_METADATA_MISSING` | Shared-work candidate exists, but safe stored/held reuse is not substantiated | meal_event_id, recipe_version_id; nullable step |
| `STORAGE_TRANSITION_UNVERIFIED` | Requested/considered advance prep cannot safely reach required meal day | meal_event_id, recipe_version_id; nullable step |

The first four reasons correspond only to their source kinds; the latter four correspond only to COOK_RECIPE. `ORDER_OUT` / `EAT_OUT` create no kitchen tasks or obligations. `reason` and `source_kind` constraints, positive ordinals/dates, `NOT NULL` pins for applicable reasons, and deterministic ordering are mandatory. Unknown reasons are **BLOCKING** rather than silently inserted.

**Referential/Household boundaries:** every task/obligation has a composite FK `(prep_plan_id,household_id)` to `prep_plans(id,household_id)`, and a validated event FK to the event of the header's exact pinned MealPlan revision. Check `source_meal_event_id` belongs to that plan before writes; use composite constraints or explicit migration triggers where the current MealEvent DB schema does not expose an eligible composite key—no implicit cross-plan join. `recipe_step_id` must belong to the pinned immutable `recipe_version_id`; validate and enforce at adapter/DB boundary with existing keys plus safe checked constraints/triggers where needed. Header supersession is same-Household. All read/write paths remain Household-scoped; no row leaks via guessed child IDs. CHECK/ FK / trigger failures rollback the full UoW. Immutability UPDATE/DELETE guards and foreign-key cascade semantics preserve published snapshots.

**Status algorithm:** `COMPLETE` **iff** all mandatory COOK_RECIPE event steps for that plan have reviewed Russian, scale-consistent executable tasks, and **zero** `prep_unresolved_obligations` remain. `INCOMPLETE` iff at least one unresolved obligation exists; the non-grocery/out-of-home events alone do not force incompleteness. Fail closed (no persisted snapshot) for invalid plan revision/Serving, missing pinned required RecipeVersion, corrupt structured input quantities, unresolvable required food/form, or inconsistent source identity. Source-backed uncertainty alone creates explicit unresolved rows and reviewable INCOMPLETE, not fabricated tasks. The validator asserts header status equals unresolved/task-coverage calculation **inside the same locked transaction**; DB CHECK enforces enum but not cross-table count. `COMPLETE` denotes **process-step coverage**, NOT proven weekday time saving or freezer readiness. The separate PR10-META usefulness gate (§4 and [audit](pr10-prep-metadata-readiness-audit.md)) is mandatory even when some sample plans have `COMPLETE` step coverage.

**Lifecycle:** generate atomically; earlier rows remain accessible; get/current/history are Household-scoped; staleness reacts to newer MealPlan revisions or changed immutable process/step-classification/policy/Household date where material. Same fingerprints replay idempotently (no fork); input returning to a past exact fingerprint may restore an older snapshot as CURRENT. No mutable `is_current` truth.

**Migration:** custom SQLite migration `0044` is only a **candidate** until runtime starts and current registry/revisions are reconciled. The accepted lineage currently ends at `0043`; migration must be additive, prove fresh/upgrade/backup/rollback and no in-place rewrite of Shopping/Recipe/Pantry. Do not add actual tables in this docs PR.

**Cross-context:** PR10 input is authoritative MealPlan/Recipe process evidence; ShoppingList is NOT a required Prep source in V1. PR10-PDF must validate current MealPlan, ShoppingList and PrepPlan versions together. Any decision requiring a Shopping fingerprint pin is a separate contract amendment.
## 6. Transaction and failure semantics — PROPOSED

- A backend-owned PrepService coordinates immutable plan+task persistence through protocol-owned repositories and one SQLAlchemy Core / SQLite UoW. Domain/service imports no SQLAlchemy, DBAPI or FastAPI.
- For any generation write: physical SQLite BEGIN IMMEDIATE **before** authoritative MealPlan/Recipe/process-data reads and before checking an existing PrepPlan, so no competing writer can invalidate the snapshot before commit. Reuse the accepted Shopping UoW locking approach where compatible, without extending Shopping ownership to Prep.
- Insert header, tasks and **third-table** unresolved obligations atomically; validate source/revision pins, grouped-event membership/contributions, and the COMPLETE iff zero-unresolved/all-covered rule while holding the writer reservation; commit once. Any unexpected error, FK violation, duplicate source conflict or failed child insert rolls back **everything**. Busy/locked returns an application-level retryable conflict, not a raw DBAPI exception.
- Never create PantryMovement, change PantryItem, reserve stock, create PreparedBatch or mark instructions completed during generation, retry, staleness query or rollback.
- Tenant scope is mandatory on every read/write, including guessed UUIDs and history. This is Household selection/scoping, **not Auth**. Auth/membership comes at the shared-deployment gate.

**Separate future command:** confirmed user execution of a task would need its **own** reviewed persisted identity, idempotent execution history, stock/food-safety and Pantry transaction design. This contract explicitly does not approve execution or prepared inventory publication in the PR10 planning slice.

## 7. Proposed API and Russian consumer representations

Support Household-scoped generate, immutable detail, current/missing/stale, explicit regenerate and history using the same minimal response discipline as accepted Shopping V1. Exact route paths and response DTO are implementation details **only within** the accepted capability contract. Use typed IDs, strict body/query validation (including unexpected parameters), Russian-safe 404/409/422/503, no database driver details.

Response separates: machine status/reason, Russian message, ordered task actions, scheduled dates, nullable truthful durations, exact reviewed scaled RecipeIngredient quantities in a **separate structured block**, source IDs, numeric-instruction classification, grouped-event provenance, storage/freezer readiness, warnings and explicit rows from `prep_unresolved_obligations`. Unreviewed numeric RecipeStep text is **not** an executable instruction: provide only a safe Russian review-needed explanation and the authoritative scaled ingredient list. No unsupported consumer text (English/free-form source) is surfaced as verified guidance. For no safe freezer action, say in Russian that the required guidance is unavailable; never show a guessed freezer expiry as fact.

## 8. Required adversarial verification matrix

| Surface | Minimum executable evidence |
| --- | --- |
| Exact mathematics | Serving Decimal scaling for 3-member/7-day fixture; pinned structured ingredients separately from prose; noninteger factors, unit mismatch, overflow fail closed |
| Source kinds | All seven; unsupported sources have correct unresolved enum; out-of-home requires no prep |
| Numeric RecipeStep | No numbers; cutting size (15–20 г), working batch (2–3 eggs), temperature/time/dimensions versus ingredient-total (5,3 г oil); ambiguous withheld, changed scaling and corrections revalidated |
| Metadata readiness | Source-backed 30-candidate audit; zero batch/freezer/storage authority; pinned actual Gate 2 recipe versions; negative all-UNKNOWN fixture without invented safe prep |
| Measured usefulness | >=1 verified shared/advance operation for >=2 MealEvents with valid hold/safety evidence and strictly fewer unique physical operations than ungrouped baseline |
| Shared grouping | Reviewed `shared_work_group_key`, per-event contributions, stable grouping, no lost source event |
| Schema/status | Three tables with third unresolved, reason/code CHECK, NULL-safe UNIQUE expression index, composite Household FK and correct COMPLETE/INCOMPLETE |
| Revision/history | Changed MealPlan or RecipeVersion/step classification => STALE; immutable successor; exact revert gives older CURRENT; idempotent replay |
| Persistence | Migration fresh/upgrade, rollback after header/task/unresolved, busy conflicts, two independent concurrent writers/no fork |
| Safety and household | Cross-Household guessed child/plan IDs nondisclosing; Pantry/PreparedBatch read-only for generation, conflict and failure |
| API/display | Russian messages, no raw unreviewed instruction as scaled task, authoritative quantities separate; strict body/query/UUID and safe errors |
| Gate 2 | 1 Household, 3 members, 30 actual pinned verified recipes, 80–120 foods; full Planner/Shopping/Prep + future PDF; AI=false and no Retail |

**Verification tier:** docs-only link/scope/whitespace checks; full backend regression not necessary when runtime unchanged. PR10-META must provide separately reviewed source evidence and readiness proof. PR10-B migration/UoW requires fresh/upgrade/rollback/concurrency plus full exact-head backend and launcher regression. PR10-A and PR10-C require focused tests and appropriately broader checks for shared startup changes.
## 9. Proposed bounded implementation order (AFTER gate merge)

1. **PR10-META — MANDATORY separately reviewed readiness/evidence gate:** freeze >=30 actual Gate 2 verified RecipeVersion IDs, current process text and classifications; review storage/hold/reheat/defrost/shared-work authority; prove >=1 source-backed safe shared or advance operation for >=2 MealEvents and strictly fewer unique physical operations. The [current 30-candidate audit](pr10-prep-metadata-readiness-audit.md) cannot pass. If evidence is insufficient, return **BLOCKED** and require a separately approved immutable recipe/process publication correction; do not fabricate data.
2. **PR10-A — deterministic pure Prep calculator (after META READY):** exact Servings, reviewed numeric text handling, explicit unresolved obligations, safe grouping and stable fingerprint; no database/API.
3. **PR10-B — persistence/UoW:** frozen three-table schema and next free migration, source locking, atomic rollback, tenant scope, staleness and concurrent idempotent generation.
4. **PR10-C — HTTP API:** typed Russian-safe generate/get/current/regenerate/history, strict validation, separate authoritative ingredient amounts and source-reviewed executable instructions.

This order is proposed for independent review, not autonomous runtime authorization. A mere ordered restatement of RecipeSteps is insufficient to close PR10. PR10-PDF and Gate 2 are later, distinct stages.
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

**Reviewer must challenge:** (1) Is the measured shared/advance operation real and safe across >=2 events? (2) Does PR10-META prove current RecipeVersion process/storage authority rather than nullable flags? (3) Are third-table unresolved enum/Household/FK and NULL-safe step uniqueness sound? (4) Do source numeric amounts agree with exact scaled structured ingredients, with unsafe steps withheld? (5) Is process/classification history immutable? (6) Is Prep independence from Shopping safe for PDF? (7) Does any early-prep action rely on guessed hold/freezer data?

## 11. Explicit decisions, assumptions and open questions

**FACT:** PR9 merged; Gate 2 remains pending. [Audited 30 verified catalogue candidates](pr10-prep-metadata-readiness-audit.md) have 0/30 non-null `batch_friendly`, `freezable` or fridge/freezer duration, 0/30 prep/total time and 1/30 cook time. Source text contains 109 steps, of which a heuristic prefilter flags 16 potentially quantitative steps across 12 recipes. This does not certify the actual as-yet-unfrozen Gate 2 recipe set.

**PROPOSED DECISIONS FROZEN FOR REVIEW:** three normalized immutable Prep tables including mandatory `prep_unresolved_obligations`, fixed reason enum and status rule; authoritative structured scaled RecipeIngredient quantities shown separately; fail-closed numeric-step review and withholding of unsafe executable prose; mandatory PR10-META before batch/freezer usefulness claims; measurable physical-operation reduction across >=2 MealEvents.

**ASSUMPTION FOR PR10-META:** enough trustworthy process and storage facts can be reviewed/published with immutable provenance to satisfy the minimum usefulness proof. Current audit does NOT establish this.

**OPEN for PR10-META/runtime preflight, not deferred schema decisions:** which exact RecipeVersion IDs form Gate 2; whether safe shared-work/hold/reheat/defrost evidence exists; whether source publication correction needs another contract/migration; whether PDF composition needs additional Shopping pins. Three-table unresolved representation and numeric-step contract are closed decisions for this review.

**Stop condition:** docs-only PR, no migration, Prep runtime, source-data mutation, Pantry execution, PDF or Gate 2 until gates are reviewed and merged.
