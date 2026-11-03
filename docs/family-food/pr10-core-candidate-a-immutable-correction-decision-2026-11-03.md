# PR10-CORE — Candidate A immutable source-process correction decision

**Date:** 2026-11-03. **Tracking:** [Issue #275](https://github.com/Mitronomik/family-food-os/issues/275).
**Accepted base:** `main@1b7d307c7de1bb298611e019cc7e233dfa21040b`, after [PR #278](https://github.com/Mitronomik/family-food-os/pull/278) merged.
**Status:** docs-only decision and prospective correction-contract draft, pending independent review and owner merge. **No source publication or runtime authorization, including after this document merges.**
**Finding:** `SOURCE_PROCESS_DISCREPANCY_CONFIRMED`.
**Recommended disposition:** `IMMUTABLE_CORRECTION_REQUIRED`; the appropriate remedy is a separately reviewed immutable successor under the existing Recipe, not editing v1 or the accepted fixture. Publication remains **NOT_READY** until the prerequisites below are closed.

## 1. Goal, scope and authority

Determine the origin and remedy for one weakened operation in Candidate A, including the consequences of a future correction. This is an AI-assisted technical Source/Data/Architecture/QA assessment, not a named qualified culinary signature, nutrition approval, D3 eligibility receipt or new safety authority. Separate Source/Data and Architecture reviews were performed; their technical findings are captured here. No claim of human professional qualification or curator-independent human approval is made.

Only `SCHOOL2022_54_20K_BUCKWHEAT_MILK_PORRIDGE@1`, School2022 card `54-20к`, and its four-step context are reviewed. The discrepancy is in **Step 4**, although **Step 1** was the proposed Prep candidate. Candidate B is not re-reviewed, corrected or substituted.

The [prior two-step evidence](pr10-core-forward-two-step-source-review-2026-11-02.md) remains historical. This review closes its missing-original-binary evidence gap **for A only** and identifies the Step 4 discrepancy. It does not close persisted Step readback, qualified household-scale review, separate-task value or D3 publication/read requirements.

**Non-goals:** no code, schema/migration, catalogue/authority publication, activation/current-selection write, correction payload consumed by a loader, new fixture/Planner run, change to Serving/Shopping/Pantry, executable PrepTask, D3 publisher/reader, API/UI/PDF, storage/freezer assertion, recipe search or automatic merge. Data/API/UI/migration changes in this PR: **N/A**. Accepted A1 pure non-executable diagnostics remain unchanged.

## 2. FACT — source and publication lineage

The retained full PDF was independently rehashed: **4,102,547 bytes**, SHA-256
`c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.
The title/imprint and selected card were visually checked; this is not a review of every page. Card `54-20к`, **printed/PDF page 64**, is “Каша жидкая молочная гречневая”. Source: *Сборник рецептур блюд и типовых меню для организации питания обучающихся 1—4-х классов в общеобразовательных организациях: Пособие*, Federal Centre for Hygiene and Epidemiology of Rospotrebnadzor, Moscow, 2022.

Reproduction references: [official PDF](https://www.niig.su/images/documents/science/Sbornik_receptur_blud_i_tipovyh_menyu_dlya_organizacii_pitaniya_obuchayushchihsya.pdf), and the retained `packages/school2022/raw/source.pdf` inside the [documented source archive](russian-recipe-version-publication-contract.md#3-fact--durable-source-artifact). The archive locator/hash and bounded factual-data rights are already documented there and in [normative recipe policy](ru-normative-recipe-corpus.md). No PDF, publisher layout or private local path is added to the repository. Rights are not expanded by this review.

| Link in the chain | Verified observation |
| --- | --- |
| Original p64 | Final operation explicitly says: «затем упаривают при закрытой крышке» |
| First R2-C specification | Commit [`a88ccda5c7cb0472ef663be3ce835836b0d0d7aa`](https://github.com/Mitronomik/family-food-os/commit/a88ccda5c7cb0472ef663be3ce835836b0d0d7aa) introduced the weaker Step 4 in `publication-specs.json` |
| Acceptance | [PR #132](https://github.com/Mitronomik/family-food-os/pull/132), merge `463fe46f7c40156c1b8ebab5402ca45698d8c2bc` on 2026-10-03; the subsequent specification commit changed rice source text, not A |
| Current R2-C | [Publication specs](../../data/curation/r2c-breakfast-grain-diversity/publication-specs.json), Git blob `ff8cf2da19e63a13901ce572171ba5b2a7451765`; all four A steps equal frozen A |
| Review rationale | [Household applicability](../../data/curation/r2c-breakfast-grain-diversity/household-applicability-review.json), blob `6eeea54048aca826120a70600bb8a0072a1a1942`, corroborates ordinary porridge and weak-boil saucepan preparation; it does not justify replacing evaporation with generic completion |
| Claimed preservation | [R2-C README](../../data/curation/r2c-breakfast-grain-diversity/README.md) says the source stovetop process is preserved. Only institutional serving-temperature exclusion is documented |
| Frozen fixture | [Publication A](evidence/pr10-ff-forward-input-v1/publication-A-PROPOSED.json) retained the existing R2-C text; the discrepancy was not introduced by PR10 materialization |

The reviewed specification history, applicability record, change note and PR #132 body contain no specific equivalence decision. Available PR comments/reviews were empty. This is a bounded search result, not a claim that no external discussion ever existed.

**Assessment:** “завершить приготовление” does not specify the source's named finishing operation. Complete process equivalence is not established, despite preserved sorting/rinsing in Step 1. The minimal source-faithful remedy restores the explicit operation in a new version. This is not proof that Step 1 or the dish is hazardous. An equivalence-only documentation route is **not supported by the evidence found**; actual contrary qualified evidence would require a new review, not silent relaxation of this finding.

## 3. Review-only before/after and hash receipt

These sentences are a **non-authoritative proposal**, not executable instructions or a publication payload. Steps 1–3 stay byte-identical. Full proposed ordered array:

1. `Гречневую крупу перебрать и промыть, несколько раз меняя воду.`
2. `Засыпать крупу в кипящую воду и варить при слабом кипении, помешивая.`
3. `Через 20–30 минут добавить горячее молоко, йодированную соль и сахар.`
4. `За 2–3 минуты до готовности добавить растопленное сливочное масло, перемешать и упарить под закрытой крышкой.`

| Position | Existing → proposed | Source reconciliation |
| --- | --- | --- |
| 1 | Unchanged | p64 sorting, rinsing, repeated water changes |
| 2 | Unchanged | p64 boiling water, weak boil, stirring |
| 3 | Unchanged | p64 20–30 minute interval, hot milk/salt/sugar; iodized salt is in the ingredient table |
| 4 | `…перемешать и завершить приготовление под крышкой.` → `…перемешать и упарить под закрытой крышкой.` | p64 names evaporation under a closed lid; the existing 2–3 minute butter timing is unchanged |

No new duration, temperature, equipment, endpoint, ingredient amount, yield or storage condition is introduced. Institutional serving temperature remains source context. Other endpoint/completeness questions are not silently resolved by this correction.

| Witness | Independently computed SHA-256 |
| --- | --- |
| Existing Step 4, exact UTF-8 | `b800669831dec3f3bed61959c1c4fa300e14b163e308f389c8d53e93c10f135d` |
| Proposed Step 4, exact UTF-8 | `bc3ae87475b4e12b4c54582f65899641d043e7dacc6619558e73258086cda48d` |
| Existing four-step process | `d6340081a54597250753ef81de33af980212098c7e3a6ba292ac4710fe8af20b` |
| Proposed four-step process | `f5dfab46d1e6f98cbb48ba9dae43afd97c7821ea8c76762548be35128344de19` |
| Unchanged Step 1 | `fc78f3e59e588c116421a44824bfe0e77a53d36bdb64c38355cccceafae25afc` |

Process serialization follows [process_steps_sha256](../../backend/app/services/pr10_ff_manifest_loader.py): canonical UTF-8 JSON `{"steps":[...]}`, `ensure_ascii=False`, `sort_keys=True`, `separators=(",", ":")`, `allow_nan=False`, no trailing newline, NFC strings. This normalized process hash is not the historical source-extraction receipt `exact_process_text_sha256=95b75e2fea80f048d67bc5efbfff2a0d06ded43623b2b5b252159b9a671d611b`.

## 4. DECISION — preserve v1; propose a separately approved successor

The accepted [DC4 language-only correction contract](dc4-a2-russian-step-correction-contract.md) demonstrates same-source immutable revisions, but authorizes seven other recipes with unchanged process meaning. Candidate A restoration is **not covered**. Do not modify that batch, extend its allowlist or reuse its approval as culinary/nutrition authority.

Proposed method, conditional on a separate accepted one-recipe publication contract:

- Retain the same canonical Recipe; preserve every v1 row and historical reference.
- Append one immutable aggregate with `created_from_version_id` targeting the independently read, exact accepted predecessor. Allocate new version/child identities through the normal service. No proposed production UUID or fixed `@2` is assigned here; reject unexpected later lineage rather than silently using “latest”.
- Retain the external source document/card/version when correcting its internal representation. Give the correction a new reviewed identity/reference and changed internal process hash. Preserve historical source-extraction receipts as distinct evidence; never relabel old normalized process bytes with the new hash.
- Freeze the complete successor seed and allowed changes before publication. Version/child IDs, revision metadata, correction note and Step 4 are expected differences; non-step source/ingredient/equipment facts must match the accepted predecessor unless a separately approved scope change is required.
- Do not set a new verification status, reviewer identity, timestamp or eligibility grant through this document. Publication metadata must come from the actual subsequent review and operation.

### Nutrition and current-version coupling

The existing R2-C source declares `output_mass_g=200` and `ENERGY_KCAL=187.3`; the other 53 frozen nutrient codes are UNKNOWN. Unchanged ingredients do **not** by themselves prove that these facts apply to the restored process. A separate source/nutrition review must explicitly confirm the same original output/energy basis and frozen UNKNOWN partition for the proposed complete process. `200 g` remains a source-card assertion, not measured household yield or validation of the 312.193218 g grain batch.

If confirmed, future publication creates the successor's **own** prepared-output authority targeted to its exact revision with a new review reference; it does not treat v1 authority as belonging to the new ID. If applicability is unresolved or materially different, stop: no guessed energy, new yield, broadened nutrient truth or unapproved activation workaround.

Current selection uses the highest `SOURCE_VERIFIED` revision in [get_current_verified](../../backend/app/persistence/sqlalchemy_core/food_recipe_repositories.py). For an active Recipe, committing a verified successor changes the current Planner input. Therefore even a source-text correction is a consequential publication, not a passive annotation.

The future contract must explicitly authorize and verify an already-active atomic correction, including any use of `require_recipe_inactive=false`. No deactivate/reactivate cycle, split commit or implicit exception from DC4 is permitted. If required prepared authority is unavailable, publish nothing.

## 5. Dependency and preservation matrix

| Boundary | This PR / required future preservation |
| --- | --- |
| Source and rights | Original PDF/card/hash and narrow factual-data rights unchanged; no new household safety authority |
| v1 aggregate | RecipeVersion, Step/Ingredient IDs, text, source, quantities, equipment and old nutrition authority untouched; old data remain readable |
| Actual predecessor | Fixture UUID `025fc5c5-95f8-4e37-bffd-937f5630798b` is test-only. No production predecessor is inferred from it; future target DB readback must pin actual Recipe/Version/children and full content |
| Append service | Existing [append_trusted_version_in_scope](../../backend/app/services/food_recipes.py) can append without committing; it uses latest persisted parent, so the bounded caller must check expected lineage/content inside the same transaction |
| Prepared authority | Existing [revision-targeted publication](../../backend/app/services/recipe_nutrition_v2.py) and [shared UoW](../../backend/app/persistence/sqlalchemy_core/recipe_nutrition_v2.py) are reusable mechanisms, not new source approval |
| Current/Planner | No writes now. Future current-version change must be explicitly accepted and checked; no scoring, role, exclusion or candidate-padding change |
| Historical plans/servings | Retain original v1 references and Decimal values. Never rewrite plans on successor publication; any later replan is a separate versioned operation |
| Derived fingerprints | New process/version/child/authority identity must be represented in newly derived outputs. Preserve historical outputs; no blanket retroactive rebinding or automatic regeneration. Determine existing staleness policy in the future contract without inventing new invalidation runtime here |
| D3 | Same Step 1 text hash does not carry approval across a changed RecipeVersion/process identity. Qualified whole-process/scale/value review, independent publication and live revocation-safe read remain separate |
| Storage/household use | No storage, freezer, time-saving, portion or family-scale permission follows from restoring source wording |

### Frozen fixture is not repaired by a successor

Preserve [owner acceptance](pr10-ff-owner-fixture-acceptance-2026-11-02.md), [pins](evidence/pr10-ff-forward-input-v1-pins.json), original A/B and historical receipts byte-for-byte:

| Pin | SHA-256 |
| --- | --- |
| A, 889601 bytes | `d160b995b680d11cf9e04f3f97c0d01cd1c65ecd2518e685b8e3cfa783e0a885` |
| B, 67963 bytes | `9a9260a4a8d849fa4284ff64b861d8c2db74d15777b04ca5d3741d25f1f0089f` |
| Accepted historical week semantic digest | `45c8773b6bd51fdb9f69f8c887dc2c66ae8a7674756b4787e72995a6d84df5e2` |

A remains the 2026-11-03 BREAKFAST pinned to v1; expected Step 1 UUID `11cb3e62-2f6c-4505-87be-cf162053c7d6` is derived fixture identity, **not independent persisted Step readback**. The original fixture's Candidate A remains `NO_GO` on current evidence even if a successor is later published. A new version cannot silently substitute for that MealEvent or retroactively validate its old whole process. Any later fixture proposal/rebinding requires separate owner approval and preservation of original reproducibility evidence. Do not add unapproved successor keys to the frozen typed-ID allowlist.

## 6. Prospective fresh, replay, conflict and rollback contract

These are requirements for a later separately authorized correction, **not operations executed here**.

1. **Fresh:** independently approve full source/process/rights and output/energy applicability; pin actual predecessor and correction contents. Open one shared Recipe/Nutrition UoW, recheck predecessor/current/all later versions and dependencies inside it, append the exact successor, publish separately reviewed authority targeted to that successor, verify in-scope facts and commit once. Then independently read current-version and Planner admission. Existing [DC4 orchestration](../../backend/app/seed/dc4_a3_russian_step_corrections.py) is a structural reference only.
2. **Exact successor replay:** same reviewed correction identity/content, predecessor, successor and matching authority => zero writes; do not append another version, change activation or regenerate plans.
3. **Conflict/partial state:** changed source/rights/ingredients/text/hash, wrong predecessor, unexpected later revision, ambiguous match, duplicate correction identity or missing predecessor/successor authority => reject without writes. Do not repair partial state while claiming replay; recovery requires its own explicit decision.
4. **Failure:** failure after append, during authority/value insertion or before commit leaves neither a partial successor nor partial authority, and preserves the old current version. Verify actual transaction behavior; a preflight outside the UoW is insufficient.
5. **Post-commit rollback:** an application release rollback must not delete/rewrite the successor, recreate v1 as current, or treat an old source package as new approval. Compatibility with historical loaders must be proved before publication. If an older release cannot safely preserve the new history, block that rollback/publication path pending an explicit compatibility decision; do not infer safety from immutable rows alone.

### R2-C replay gap to close before implementation readiness

Read-only code inspection found a relevant coupling in [R2-C _assert_replay_not_partial](../../backend/app/seed/r2c_breakfast_grain_diversity.py): it checks authority for the **current latest** version, then calls the public `publish_prepared(old_spec)`. That public method can commit a FRESH authority before the caller subsequently rejects a non-replay result. With a successor present, missing historical authority and an inactive Recipe, this suggests an unintended historical repair path. **This is a code-path inference, not a reproduced defect or an executed test.**

The future contract must require read-only validation of the exact historical predecessor authority before any mutating publication call, and zero-write rejection of missing historical/current authority. Current [ordinary replay/deactivation tests](../../backend/app/tests/test_r2c_breakfast_grain_diversity.py) and [partial-state tests](../../backend/app/tests/test_r2c_breakfast_grain_diversity_adversarial.py) do not prove R2-C replay after this new successor. R3-A/DC4-specific coverage cannot stand in for it.

Required sequence: original R2-C and prerequisites → approved A successor and its authority → rerun original R2-C including upstream seed chain. Old specs resolve the exact old structure, while current reads resolve the approved successor. Assert zero writes, unchanged old authority, unchanged current successor/authority, no activation change, no changes to unrelated recipes. Repeat with deliberate deactivation and missing historical/current authority; no repair or reactivation. Generic source-lineage checks are not independent approval of changed cooking semantics.

## 7. Acceptance, open decisions and next bounded operation

**This task's result:** the source discrepancy and its R2-C origin are established; `IMMUTABLE_CORRECTION_REQUIRED` is the recommended remedy. A four-step source-backed proposal, preservation matrix and prospective transaction/replay requirements exist. Equivalence was not demonstrated. Exact future target identity, professional source/process approval and successor nutrition applicability remain unresolved rather than invented.

**Before a future implementation-ready contract can be accepted:**

- Obtain a real named independent source/process review of the proposed full process and explicit prepared-output/energy applicability decision. Separate source restoration from household-scale/task-value/D3 approval.
- Read and freeze the actual target predecessor/children/authority; determine exact next revision only after excluding unexpected later history. Obtain source access or return `INSUFFICIENT_EVIDENCE`; a freshly generated fixture is not original target readback.
- Freeze the bounded publisher/replay path, atomic active-Recipe exception, exact zero-write failure behavior and rollback compatibility. No new schema is expected from existing mechanisms, but this is an assumption: any needed migration, new authority boundary or wider transaction change reopens the contract before code.
- Independently review and accept the completed one-recipe contract, then obtain **separate explicit owner authorization** for its implementation/publication. Merge of this decision alone authorizes neither.

**Future tests, not run here:** predecessor aggregate and fixture bytes unchanged; one exact successor; wrong/stale parent and conflicting correction rejected; own successor authority/UNKNOWN partition; zero-write successor and historical R2-C replay; partial-state no-repair; transaction failure injection; no current-version regression; inactive-state preservation; correct new Planner admission with old plans still pinned; unapproved fixture typed keys rejected; unchanged Step 1 hash cannot inherit eligibility. Retain AI-off coverage. Use the publication/persistence verification tier only in the later implementation.

**Current verification tier:** docs/state only. Verify source and proposal hashes, lineage/manifest equality, preservation of all non-doc tracked paths, relative links, status consistency, `git diff --check`, staged scope and `git diff --cached --check`, then exact-head Docs CI. No backend/DB tests, kitchen trial, new Planner run, Step readback, publication or D3 anti-rollback test is claimed by this investigation.

**Local evidence performed:** independent Python SHA-256 recomputation of the PDF, frozen A/B byte counts/hashes, five old/proposed Step/process hashes; `git show` comparison of the initial R2-C/current R2-C/frozen A four-step arrays; repository-relative link and exact four-file scope checks all passed. Separate AI-assisted Architecture/Data and QA document reviews found no outstanding P1/P2 issue. These are technical document checks, not human source approval. Staged checks and exact-head Docs CI are reported with the PR; no unexecuted CI result is asserted here.

**Unchanged gates:** `APPROVED_IMMEDIATE=0`; `NO_GO_TO_PR10_CORE_RUNTIME` and `NO_GO_TO_PR10_A_RUNTIME` for executable/persistent capability; `SAFE_BATCH_READY=false`; `PORTION_RELEASE_READY=NOT_PROVEN`; `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` only for accepted technical energy-only bytes. Pure non-executable A1 remains accepted, unexpanded. Gate 2 still requires two different positive task-bearing MealEvents, truthful unresolved/negative evidence and Planner → Shopping → Prep → PDF. [D3](pr10-core-step-eligibility-d3-contract-2026-10-22.md) still requires independent publication/read and rollback-independent revocation protection, including `ACTIVE → REVOKED → rollback old release → DENIED`.

**Next only:** review this docs-only decision and obtain the owner's distinct merge decision. Subsequent work is closing the identified one-recipe source/authority/target/replay prerequisites under separate authorization; no automatic successor publication, D3 implementation or fixture replacement.
