# PR10-META-DATA — reviewed reusable raw-vegetable stage authority gate

**Status:** PROPOSED docs-only implementation/source-publication preflight; **`BLOCKED_RECIPE_STAGE_BINDING_NOT_PUBLISHED`**.
**Issue:** #203.
**Accepted base:** `main@577bbeab86ba77f1d05ae8c6a4cabd042e98d05d` (#202 merged on 2026-10-10).
**Existing binding authorities:** [accepted PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META BLOCKED](pr10-meta-readiness-decision.md), [same-day 21-pair receipt](pr10-meta-same-day-pair-evidence.json), [DATA-CORPUS-V1](data-corpus-v1.md) and [Food composition/form](food-composition-and-assembly.md).
**Evidence JSON:** [reviewed-stage authority preflight](pr10-meta-reviewed-stage-authority.json).

This is a **proposal for independent review**, not publication of verified Prep stages, freezer/storage safety, a new domain identity or an instruction to perform meal prep. It explicitly preserves the accepted **three Prep persistence tables** and `AI_ENABLED=false`.

## 1. FACT — actual event, version and source evidence

The accepted three-member **synthetic** PR #196 fixture pins Tuesday 2026-09-15 lunch `MR2019_2_11_BEEF_VEGETABLE_RAGOUT`, event `cf0e3fe3-4c59-4447-9fbd-7a9e19c6ff49`, RecipeVersion `063694fb-92cf-4731-adf6-041d36a532e4`, and dinner `MR2019_1_16_POTATO_SPLIT_PEA_SOUP`, event `d000a213-d169-4f10-a2ad-08180f40aea6`, RecipeVersion `116e25fa-12f3-4926-8a2a-7aa2cf99bb9c`. Both versions use canonical `CARROT` and `ONION_BULB_FRESH`, but their **step 2 hashes differ**. The frozen [PR #202 receipt](pr10-meta-same-day-pair-evidence.json) records exact step/version IDs and individualized Decimal Servings from original PR #196 JSON SHA256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`.

The [R3-D reviewed recipe publication input](../../data/curation/r3d-final-dc3-batch-gate/frozen-batch.json) pins both source cards from Russian `RU_MR_2_4_0162_19`, **2019-12-30** source version, raw source document SHA256 `973acb53eee7a04c76853dff80988a0f9b70e704495b715639cd8a34a747293e`, and recipe-specific card SHA256s:

| Authority | Ragout MR 2.11 | Split-pea soup MR 1.16 |
| --- | --- | --- |
| [Original source card](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/miasnye-bliuda/tekhnologicheskaia-karta-n-2.11/) | R3-D card `89ef921166ece243277dc3f1106e340769f3a99a89195ff10028bd78f529a295` | [Soup card](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.16/), card SHA256 `f4d70b7eb24de3fc10fd239ad6dcb2d7047c8e458541a0a1f8d6e15256ee8731` |
| **Source original technology** | Prepared onion and carrot are finely chopped, then cooked with water/butter | Original source preamble **explicitly calls for sorting, peeling, washing vegetables**, then separate steps prepare the soup |
| **Accepted published `consumer_steps_ru`** | Step 2 instructs fine chopping and poaching; does **not** publish a separate `WASH/PEEL` PrepStep | Step 2 says prepare carrot/onion and poach; **does not separately publish** the original wash/peel preamble as an immutable RecipeStep |
| `CARROT` base amount, g / source serving | 35 | 14 |
| `ONION_BULB_FRESH` base amount, g / source serving | 9 | 5 |
| **Missing authority** | Which exact wash/peel stage is bound to published version? | How is the source preamble assigned to a reviewed immutable stage? |

**Critical distinction:** The original soup source explicitly contains preparation operations, whereas the accepted *production-published process steps* compress them. The ragout source uses the word “prepared” but does not independently define the same wash/peel stage. Neither currently published immutable RecipeVersion provides **two verified, identical input/output Prep-stage bindings**. A source-card preamble may justify **future reviewed process curation**, not automatic runtime behavior. This is a more precise blocker than “the RecipeStep strings differ.”

The source document targets institutional special-diet recipe cards; acceptance as factual recipe provenance does not automatically grant a universal household shared-work or storage policy. The two MealEvents have the same local **date**, but no common prep-session timestamp, no confirmed sanitation/storage transition and no measurement of household equipment/handling operations.

## 2. Independent hygiene context — evidence vs extrapolation

[Роспотребнадзор, 16 June 2026 — «Мыть или не мыть: правила обработки овощей и фруктов»](https://zpp.rospotrebnadzor.ru/news/federal/574886) gives **general** produce hygiene guidance. It is relevant to considering cleaning of carrots and onions as a safe process category; it **does not** define a process component shared by these exact two immutable recipe versions, does not supply their quantities, establish clock time or eliminate separate steps. Do not adopt its general hygiene wording as newly authoritative recipe instruction or a claim that prewashing and storing produce hours before a later meal is safe in every home.

**Source/evidence categories (frozen for review):**

| Claim | Supported status |
| --- | --- |
| These are two actual pinned `COOK_RECIPE` MealEvents | **FACT**, synthetic fixture |
| Same canonical raw vegetable inputs at recipe composition level | **FACT**, R3-D selected variants |
| Soup card explicitly includes sort/peel/wash before cooking | **FACT**, original source card |
| Ragout card defines a distinct, identical wash/peel operation | **NOT SHOWN**; “prepared” is underspecified |
| Each *published* RecipeStep contains a reviewed, separately identifiable `RAW_WASH/PEEL` output stage | **FALSE / NOT YET PUBLISHED** |
| Matching current input FoodIngredient ⇒ equivalent staged output | **INVALID INFERENCE** |
| Same calendar date ⇒ same prep session / zero hold | **INVALID INFERENCE** |
| Batch washing once reduces net physical operations | **ASSUMPTION**, not measured or accepted |
| Combining water/butter poaching or cutting into one task is allowed | **NO**, source cuts and water distribution differ |

## 3. Proposed `ReviewedPrepStageBindingV1` curation contract — NOT new runtime schema

**Proposed representation (for reviewer approval only):** a **versioned, repository-local reviewed publication receipt** whose entries are tied to immutable accepted `RecipeVersion` and `RecipeStep` hashes. This is **not a fourth Prep table, migration, runtime data authority, or hidden FoodIngredient property**. It would be a proposed source/curation input that a later independently reviewed publication contract must validate and expose to the deterministic calculator. If that calculator needs new authoritative persisted identity, transaction/version mapping or re-published `RecipeVersion`, stop for another docs-only contract before touching production.

Each proposed `ReviewedPrepStageBindingV1` record must include these required typed boundaries, none of which can be inferred merely from recipe names:

- **Immutable pins:** `binding_id`, `binding_version`, `recipe_version_id`, `recipe_step_id`, `step_instruction_sha256`, full `recipe_process_hash`, original source URL/card SHA256/source-version, rights decision, reviewer identity/time, immutable publication identity and hash.
- **Process semantics:** reviewed `operation_type` (e.g. `SORT_WASH_PEEL` *only where source-backed*), exact canonical `FoodIngredient`, `input_form`, `output_form`, separately traceable original and revised Russian direction, `source_authority_class`, plus rejected substitutions and affected equipment.
- **Numeric authority:** `quantity_binding_kind` points to structured recipe ingredient + exact Decimal member `Serving`, with units/raw-vs-net form and quantization handled by existing backend semantics. No recipe-step prose number becomes a purchase/Prep quantity. Stage-specific mass split/yield **UNKNOWN** unless reviewed and authoritative.
- **Shared-work eligibility:** `batch_compatibility_decision` (APPROVED / REJECTED / REVIEW_REQUIRED), joined stage outcome identity, deterministic event participation/contribution mapping, remaining recipe-specific dependencies and source-backed compatibility of prep-session/holding state. Before approval, stage IDs stay CANDIDATE; UI may not render executable grouping.
- **Safety and time:** reviewed food-state transition, as-of real prep/use clock or explicit **same-session no hold** conditions, source/authority scope; missing information is `UNKNOWN` and blocks advance/freezer guidance. No generic storage-day value, early-prep action or clock invented from a weekday/date.
- **Version drift:** new RecipeVersion/step hash, altered process authority, ingredient form, Household plan revision or scale invalidates reviewed grouping until independently reapproved. Exact source and recipe history remain immutable.

The planned `PrepTask.shared_work_group_key` from accepted PR10-ARCH **may be used only after** these versioned stage bindings and exact event contributions are approved through their owning publication boundary. A machine-readable `CANDIDATE` marker is **not** a persisted household PreparedBatch, proof of cooking, or proof of a shared safe component.

### Publication strategy decision requested, not silently assumed

**Option A (preferred candidate for review):** augment recipe-process authority through reviewed immutable publication referencing existing RecipeVersion/step bindings, keeping existing process text untouched until its owner approves a new immutable version when necessary. Proof required: the accepted recipe catalogue has a supported, reviewable authoritative retrieval path for the new stage binding without an unsafe mutable overlay. If not, **STOP** and open a separate docs-only source-publication implementation contract including migrations/source ID/fingerprints.

**Option B:** curate versioned step-level authority and re-publish corrected immutable RecipeVersions if accepted raw source preambles genuinely need new separately actionable Russian steps; requires its own source/rights, nutrition/output invariants, corrected provenance and downstream staleness verification. Not allowed within this PR.

Neither option is approved for runtime by this docs gate. The reviewer must accept/reject the data publication boundary **before** a production recipe or domain contract changes.

## 4. Deterministic net physical-action test — not a text-hash trick

Let `A` be the number of separate actual, source-backed cleaning/prep actions when the two meals are prepared independently. Let `B` include the combined action **plus** any new separating/splitting/holding, retrieving, equipment-cleaning or other required work. The accepted PR10 benefit requires `B < A`, with unchanged source-verified output food forms, per-event quantities and hygiene/hold rules. Source text alone does **not** populate either side with verified counts.

The limited theoretical case “wash a vegetable batch once instead of twice” could save one repeated action, but **splitting and separate form-specific chopping may add actions**. There is no accepted evidence that these two actual events are cooked in one prep session; no measured active time, no equipment capacity and no authoritative stage outputs. Therefore this evidence cannot report `B < A`, even when the abstract action names sound reusable. No numeric minutes are claimed.

**Adversarial cases before release of any stage:** wrong/unknown ingredient form; source step mutated but hash retained externally; one version reviewed but other not; mixed raw/cooked state; overlapping FoodIngredient without equal `output_form`; changed scaled Decimal Servings; same-day events at different cooking times; new storage/retrieval cancels a nominal saved action; frozen or handled produce without reviewed condition; batch sizes exceeding equipment; current MealPlan revision different from fixture. Every case must yield REVIEW_REQUIRED/INCOMPLETE or no derived grouping, never silent success.

## 5. Decision, next bounded move and exit

**FACT:** two event pins and shared canonical raw input identities are accepted, but a **reviewed step-level shared raw-vegetable identity is not published** for either exact RecipeVersion. Only the soup's original source text unambiguously states wash/peel; neither published process exposes it separately. The ragout and soup have different cuts/poaching processes and unspecified internal water distribution.

**ASSUMPTION:** appropriate stage curation could eventually prove a reusable safe cleaning operation in an explicitly reviewed single prep session. This has **not** been proved on the actual fixture.

**DECISION / current gate:** `BLOCKED_RECIPE_STAGE_BINDING_NOT_PUBLISHED`. PR10-META remains **BLOCKED**, not READY. Do not auto-create a `PrepTask` group, `PreparedBatch`, source step, fridge safety fact, task-time savings or RecipeVersion correction.

**OPEN reviewer decisions:** is a separate versioned process-stage authority that pins source+RecipeVersion+step hashes sufficient, or must existing immutable RecipeVersions be re-published to expose an honest executable stage? Does any accepted current service/DB schema support that without another gate? Can a *real* positive net action count and no-hold session be verified instead of hoped for?

**Next gated operation after independent acceptance:** a **separate source-data/publication contract or bounded stage-curation evidence PR** that resolves these questions and validates the ragout's implicit preparation and soup preamble with a reviewed stage output/form. If source evidence cannot reach two credible bindings and `B < A`, record the pair BLOCKED and consider alternative accepted recipes/fixture choices without weakening Gate2 or PR10 acceptance criteria.

**Non-goals:** runtime Prep service/DB/API/UI, extra production table, migrations, recipe publication, Shopping/Planner/Pantry changes, source-free recipes, arbitrary AI/Retail, freezer or safety recommendations, backend PDF and Gate2 closure.

**Docs-only verification:** source link/hash reconciliation, bounded schema proposal vs accepted three-table scope, status and whitespace; backend regression unnecessary when shared runtime remains byte-identical.
