# PR10-CORE Candidate A — one-recipe successor publication Implementation Contract Gate

**Status:** `PROPOSED / DOCS-ONLY / IMPLEMENTATION_NOT_READY`.
**Accepted base:** `main@f7193dd6c66f11fae82fe874de971f5945b9a1c9` ([PR #279 merged](https://github.com/Mitronomik/family-food-os/pull/279) 2026-11-03).
**Owner task:** after the merged Candidate A [immutable-correction decision](pr10-core-candidate-a-immutable-correction-decision-2026-11-03.md), formalize the **minimum testable approval and implementation contract** for a **single later** corrected RecipeVersion. **No publication, runtime implementation or data-authority approval occurs in this PR**. Track the existing [Issue #275](https://github.com/Mitronomik/family-food-os/issues/275); avoid a new recipe-pair research cycle.

## 1. FACT — what is already accepted and what remains unavailable

- Candidate A `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE`, original School2022 card `54-20к`, source SHA256 `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`. PR #279 traced weakening of the source's explicit **«упаривают при закрытой крышке»** to the published v1 Step 4 **«завершить приготовление под крышкой»** in R2-C [initial publication](https://github.com/Mitronomik/family-food-os/pull/132). This finding supports **`IMMUTABLE_CORRECTION_REQUIRED`**, not editing v1.
- Existing Step 4 text SHA `b800669831dec3f3bed61959c1c4fa300e14b163e308f389c8d53e93c10f135d`, existing ordered process SHA `d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b`. The [review-only proposed Step 4 and four-step array](pr10-core-candidate-a-immutable-correction-decision-2026-11-03.md#3-review-only-beforeafter-and-hash-receipt) yield proposed Step SHA `bc3ae87475b4e12b4c54582f65899641d043e7dacc6619558e73258086cda48d` and process SHA `f5dfab46d1e6f98cbb48ba9dae43afd97c7821ea8c76762548be35128344de19`. **These are proposed review witnesses, not an accepted replacement publication payload.**
- `SOURCE_VERIFIED` version selection is highest verified revision in [food recipe repository](../../backend/app/persistence/sqlalchemy_core/food_recipe_repositories.py). [append_trusted_version_in_scope](../../backend/app/services/food_recipes.py) creates an immutable version **in caller-owned UoW** and increments the currently latest persisted version; it is not permission to select a proposed `@2` blindly.
- The accepted v1 source nutrition declaration was **`source_output_g=200` and `ENERGY_KCAL=187.3`, with the other 53 codes UNKNOWN** per [PR #279 decision](pr10-core-candidate-a-immutable-correction-decision-2026-11-03.md#nutrition-and-current-version-coupling). No proof yet establishes that this complete source-output/nutrition assertion transfers unchanged to the proposed process-restoration successor.
- Accepted frozen `PR10_FF_FORWARD_3M_7D_V1` is **test-only energy-only evidence** with 3 members, 7 dates, 21 MealEvents, 42 Decimal Servings; its immutable input A/B, original RecipeVersion/Step identity and semantic digest `45c8773b6bd51fdb9f69f8c887dc2c66ae8a7674756b4787e72995a6d84df5e2` remain untouched. It is **not** the actual target production database readback.
- **Not available at this gate:** a version/child/authority readback from the real intended target SQLite database, a qualified independently identified reviewer and signed original-process approval, a distinct successor prepared-output/nutrition applicability decision, or executed post-successor historical R2-C replay/failure-injection evidence. Therefore `IMPLEMENTATION_NOT_READY` remains mandatory even after this document merges.

## 2. Exact ownership and no-silent-supersession matrix

| Contract boundary | Preserved authority | Contract requirement before publication |
| --- | --- | --- |
| Source/rights | [Normative corpus rights](ru-normative-recipe-corpus.md), School2022 card and [R2-C provenance](../../data/curation/r2c-breakfast-grain-diversity/publication-specs.json) | Actual independent source/process reviewer confirms the **whole** source process, copy scope and bounded process-restoration text; no invented cooking parameters |
| Immutable Recipe | PR4 `Recipe` / `RecipeVersion` / `RecipeStep`, [PR #279](pr10-core-candidate-a-immutable-correction-decision-2026-11-03.md) | Append exactly one *separately approved* successor only to the pinned real predecessor; retain v1, all children, historical authority and MealPlan/Serving references |
| Source nutrition | [Prepared nutrition revision-targeted publication service](../../backend/app/services/recipe_nutrition_v2.py) | A distinct qualified/reviewed decision determines whether output basis, `187.3 kcal` and 53 UNKNOWN codes are valid for the successor; **no inherited authority by identical ingredients** |
| Current/Planner | `get_current_verified` chooses latest verified | Explicit product-owner consent for the change of current version on an already-active Recipe; no hidden deactivate/reactivate, scoring/candidate-padding change or unreviewed activation exception |
| Transaction | Existing [Recipe/Nutrition UoW](../../backend/app/persistence/sqlalchemy_core/recipe_nutrition_v2.py), [DC4 existing pattern](../../backend/app/seed/dc4_a3_russian_step_corrections.py) | Atomic append + new revision-targeted prepared authority + in-UoW validation + **one commit**; never split writes; qualified new evidence required despite code reuse |
| Historical loaders/replay | [R2-C seed](../../backend/app/seed/r2c_breakfast_grain_diversity.py) and accepted prior evidence | A historical replay resolves **exact v1** and proves zero writes after a successor; no accidental repair of older nutrition authority, implicit current rollback or new seed |
| D3 / Prep | [D3 trusted eligibility contract](pr10-core-step-eligibility-d3-contract-2026-10-22.md) | No automatic Step 1 approval by unchanged text; full new RecipeVersion/process/scale review and rollback-independent trusted ACTIVE/REVOKED reader remain separate, unimplemented |
| Frozen fixture / consumer | Owner-accepted 3/7/21/42 technical fixture, [Option B](pr10-option-b-staged-delivery-gates-2026-10-17.md) | No A/B rewrite, fixture swap, source hash relabel, repinning historic meal to successor, assumed pantry/batch stock, safe-freezer claim or Gate2/release promotion |

The accepted three-table Prep schema, the active custom SQLite migration runner, domain dependency direction and `AI_ENABLED=false` are **unchanged**. No migration number is reserved. **If actual dependency inventory reveals a schema/authority/transaction change, reopen a new high-coupling gate before any runtime edit.**

## 3. Mandatory target readback and explicit human decisions — still BLOCKED

Before a separately authorized implementation PR is even **implementation-ready**, require one **read-only target-environment receipt**, not a synthetic rerun or derived fixture UUID. It must pin:

1. Target DB identity/context (non-secret, no real household PII), timestamp and accepted schema revision; recipe canonical code and Recipe ID; current activation state; actual `RecipeVersion.id`, `version_number`, `created_from_version_id`, all later versions (or verified absence), `verification_status`, rights status/source identifiers/rights basis and current verified selection.
2. The exact predecessor's immutable ordered `RecipeIngredient`, `RecipeStep` and `RecipeEquipment` **persisted identifiers, positions, quantities, units, original text, original SHA and full process SHA**; source card/version hash. Compare with accepted R2-C and reject unexpected differences before writes.
3. Its actual revision-targeted prepared nutrition authority ID, source output and energy values, UNKNOWN partition, code/version and linked records. Record missing or conflicting authority explicitly as `BLOCKED`.
4. A named independent qualified source/process reviewer with a dated, traceable source evidence/reference and a **separate** approved nutrition/output basis disposition for the proposed successor. An AI agent, old DC4 language-only approval or unsigned draft cannot satisfy this. Include independent publication/data owner consent for the current-version impact.

**No accessible target DB receipt or qualified sign-off is available in this chat/repository review.** Do not fabricate any ID, review timestamp, permission or decision. On missing or unexpected history: **stop `NO_GO_TO_CORRECTION_PUBLICATION`**.

## 4. Exact one-recipe publication state machine — future implementation only

The following is a **conditional design contract**, not a runnable publisher or new source of authority.

| State | Required operation / outcome |
| --- | --- |
| `UNREVIEWED` | No writes. Require all §3 pins and source/nutrition/owner decisions |
| `READY_FOR_FRESH` | Inside one shared Recipe/Nutrition UoW (atomic on the active Recipe), re-read exact predecessor, current selection, full later lineage/authority and pre-approved correction identity; reject drift before append |
| `FRESH` | Append exactly one immutable corrected RecipeVersion under same Recipe; only reviewed Step 4 and necessary new version/child/authority identities differ; publish *its own* approved prepared authority targeted to the new revision; verify stored records and commit once |
| `EXACT_REPLAY` | Pre-existing exact successor + matching new authority, same approved correction receipt and predecessor → **zero writes** (no new IDs, values, timestamp, activation or history changes) |
| `CONFLICT` | Different source/rights/Step/process/ingredient/energy/UNKNOWN partition, wrong predecessor/current, unexpected version, duplicate correction identity, partial successor or authority → fail closed **zero writes**, not an automatic repair |
| `FAILURE` | Error before/during append, authority insert or before commit → full rollback, unchanged original current and v1; no orphan successor/authority |
| `POST_COMMIT_ROLLBACK` | Rolling back application code cannot rewrite successor/current/authority or revive obsolete process/step permission. Older R2-C loader compatibility must be tested; block incompatible rollback/replay path |

**Key subtlety:** the [R2-C `_assert_replay_not_partial` path](../../backend/app/seed/r2c_breakfast_grain_diversity.py) currently reads **latest** authority and calls public `nutrition.publish_prepared(old_spec)` (which can commit `FRESH`) **before** demanding `EXACT_REPLAY`. This is **an unexecuted code-path inference**, not a verified vulnerability. The future corrective design must *first* verify the exact historical v1 authority **read-only**, and must never mutate historical authority while testing replay. A post-successor R2-C replay with missing old authority must return `CONFLICT/no writes`, including deliberate deactivation.

## 5. Required future acceptance/tests and verification tier

**Read-only prerequisites (to close before any code):** §3 target DB receipt, qualified whole-process review, separate successor nutrition/output applicability decision, explicit current-version owner approval, accepted complete implementation contract and exact successor correction identity. Do **not** treat this current proposed gate as approval by itself.

**Future executable tests (not performed here):**
- Fresh happy path with one reviewed successor and its **own** approved prepared-output authority; verify expected source version, parent, process SHA, all ingredient/equipment source facts and new current-selection readback in one transaction. Old v1 IDs/authority and frozen fixture remain unchanged.
- Exact replay idempotence with distinct DB snapshots/byte-equal relevant rows; repeated call produces no IDs/authority/history/activation changes.
- Conflict tests for wrong parent, extra unseen later revision, changed Step4 hash, duplicate correction identity, missing or altered nutrition/UNKNOWN authority, inactive active-Recipe assumption and unexpected source/rights drift. No partial writes.
- Failure injection after append and during/before prepared authority publication/commit: full rollback and no partial authority or successor.
- **Historical R2-C adversarial replay:** original seed chain after corrected successor; old spec must resolve original v1, current must stay successor, and no historical authority rows are created or repaired. Deliberately remove v1 or successor authority in isolated DB and assert fail-closed zero writes, including deactivated Recipe. This exact scenario is **not covered** by existing ordinary R2-C replay checks.
- Old-release compatibility and versioned dependent result staleness: no automatic MealPlan/Serving rewrite, no re-enabling D3 eligibility, no surprise current-version change without accepted consent; AI disabled.
- Only **after separately authorized code/schema-sensitive PR** apply [verification policy](verification-policy.md): focused recipe/authority/seed transaction tests, fresh/upgrade/migration only if needed, full backend and launcher regressions for touched shared UoW/persistence, exact-head CI. Do not weaken existing tests.

**This docs-only PR verification:** changed-path scope, whitespace, repo-relative links, status accuracy, preservation and first-order source/hash/code reference checks, exact-head Docs CI. No new target SQLite readback, real signer, runtime tests, recipe publication, fresh Planner run or safe cooking proof is claimed.

## 6. Decision, next authorization and hard stop

**FACT:** the old Candidate A v1 differs from the pinned original process; restored Step 4 is documented as review-only evidence, without current target DB lineage or source/nutrition approval.

**PROPOSED DECISION:** adopt this **conditional one-recipe correction implementation contract** as a testable **gate**, not as permission for execution. Current verdict = `CONTRACT_PROPOSED / IMPLEMENTATION_NOT_READY / NO_GO_TO_CORRECTION_PUBLICATION`.

**OPEN:** who will produce the authoritative target DB readback and who will provide the qualified independent whole-recipe process and nutrition-applicability sign-off? A dry-run replay test may inform a later implementation, but cannot replace the evidence or write a successor.

**Next ONLY after independent review/merge:** request **one separately authorized bounded read-only predecessor/authority receipt and qualified source/nutrition review**. No successor publication, R2-C production edit, new RecipeVersion, D3 publisher/reader, PR10-B/C/PDF or Gate2 implementation without an additional explicit owner decision.

**Unchanged gates:** `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` for exact technical kcal-only fixture only; `APPROVED_IMMEDIATE=0`; `NO_GO_TO_PR10_CORE_RUNTIME` (executable/persistent); `SAFE_BATCH_READY=false`; `PORTION_RELEASE_READY=NOT_PROVEN`. Candidate A original fixture remains `NO_GO`, Candidate B `INSUFFICIENT_EVIDENCE`. Both remain outside any trusted Step approval.
