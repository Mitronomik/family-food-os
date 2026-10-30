# PR10-FF-ID-BINDING — fixture-only publication-key resolution amendment

**Status: DOCS-ONLY PROPOSAL FOR INDEPENDENT ARCHITECTURE / DOMAIN / QA REVIEW; NOT APPROVED FOR RUNTIME.**
**Date:** 2026-10-30. **Base:** `main@b1d6f88d55485fd91f9e6f65a8fb535678f44ef1` (merged [PR #262](https://github.com/Mitronomik/family-food-os/pull/262)).
**Related open draft:** [PR #263](https://github.com/Mitronomik/family-food-os/pull/263) (partial, **not ready to merge**).
**Controlling documents:** [merged typed ID contract](pr10-ff-typed-test-identity-implementation-contract-2026-10-30.md), [forward-fixture preflight](pr10-fixture-forward-implementation-preflight-2026-10-30.md), [accepted forward amendment](pr10-fixture-forward-contract-amendment-2026-10-29.md), [D3 eligibility](pr10-core-step-eligibility-d3-contract-2026-10-22.md), and [original #196 receipt](evidence/pr196-original-synthetic-fixture-receipt.json). This document proposes **one explicit narrow amendment to #262 §4.1**; every unmentioned clause remains controlling.

## 1. FACT / ASSUMPTION / PROPOSED DECISION / OPEN QUESTION

**FACT — observed runtime boundary.** [`FoodRecipeCatalogueService._new_detail(scope, recipe, seed, number, previous_id, now)`](../../backend/app/services/food_recipes.py) has the entire `TrustedRecipeVersionSeed`, the numeric version and the predecessor **database UUID**. Neither the `seed` nor its caller-supplied method arguments contain the approved correction artifact's raw SHA-256 or the predecessor's immutable **semantic key**. The ordinary `id_factory: Callable[[], UUID]` cannot produce typed, content-bound keys. [`dc4_a3._publish_one`](../../backend/app/seed/dc4_a3_russian_step_corrections.py) has the correction artifact and the old/new Steps but forwards only `successor_seed.version` into `append_trusted_version_in_scope`. Existing v1/v2 source-record fields remain intentionally identical.

**FACT — correction authority.** The trusted [DC4-A3 corrections file](../../data/curation/dc4-a3-russian-step-corrections/corrections.json) is Git blob `ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68` at the accepted base; independently computed UTF-8 raw content SHA-256 from that blob is `157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759`. The existing `_load_corrections` checks its Git blob and seven named corrected entries. That SHA-256 is the **whole artifact** witness for `correction_revision_sha256`, not a value derived from `change_note`, a source-version SHA, a UUID-containing DB `process_hash`, or individual changed Steps. Future implementation must re-read *raw bytes*, independently verify both hashes and link each accepted old/new Step pair to its code; a hash match alone does not grant rights or publish permission.

**FACT — draft #263:** a standalone `ManifestPinnedFixtureIds.id_for(kind, key)` has been committed with the six frozen key shapes and the #262 v4-shaped hash algorithm, but no actual Recipe composer/seed propagation is wired. Its unit conformance is **not** a real persisted Planner fixture.

**ASSUMPTION TO PROVE:** A **manifest-bound opt-in provider lookup** can supply the *already frozen* `RECIPE_VERSION` semantic key at the precise existing `_new_detail` boundary by matching the actual trusted seed, version number and real predecessor ID against independently pinned publication evidence. This does **not** prove that the full Planner week will become stable.

**PROPOSED DECISION:** Extend only the optional fixture provider protocol from #262 with one additional **read-only key-resolution method**, `recipe_version_key_for`, as specified below. **Do not** add a new public `publication_context` parameter to each Recipe writer, add a source/correction field to production domain models, or change existing seed/corpus objects. Runtime may adopt this extension **only after this docs-only gate is independently reviewed, merged and explicitly owner-approved for resumption of #263**.

**OPEN:** Independent verification that every existing v1, v2 and conditional seed branch has a unique pre-frozen manifest entry; precise in-scope validation implementation against existing Recipe read-scope and UoW; whether extra tie-sensitive owners are needed beyond the previously approved Member/RecipeVersion set. Any missing authority/data or a third/unlisted version means STOP, not new scope by inference.

## 2. Proposed protocol amendment — exactly one new method

The #262 `id_for(kind, key) -> UUID`, its closed six-kind key schema, namespace, canonical JSON, SHA-256 prefix, v4/variant masks, golden vectors, collision ledger and default-`uuid4` behavior are **UNCHANGED**.

Proposed extended **opt-in only** protocol (illustrative type declarations; no code in this PR):

```python
class FixtureTypedIdProvider(Protocol):
    def id_for(
        self, kind: FixtureEntityKind, key: CanonicalTypedKey
    ) -> UUID: ...

    def recipe_version_key_for(
        self,
        *,
        canonical_code: str,
        seed: TrustedRecipeVersionSeed,
        version_number: int,
        predecessor_id: UUID | None,
    ) -> CanonicalRecipeVersionKey: ...
```

**Binding point:** Inside `FoodRecipeCatalogueService._new_detail` **only when** an explicitly injected `id_provider` exists, call `recipe_version_key_for(canonical_code=recipe.canonical_code, seed=seed, version_number=number, predecessor_id=previous_id)` **before allocating any new RecipeVersion/RecipeIngredient/RecipeStep ID**. The return value is the exact frozen `RECIPE_VERSION.key`; call the previously approved `id_for("RECIPE_VERSION", key)` and derive ingredient/Step keys from that same key plus real positions/source values. `RECIPE` keeps the §3.1 `canonical_code` key. The provider must not create RecipeVersions, publish nutrition or authorize a source; it only resolves and checks an existing pre-reviewed fixture identity.

The `predecessor_id` is permitted as a **lookup/equality witness only**, never as a field in, or salt for, the key. For v2 the resolver obtains the predecessor's full `RECIPE_VERSION` key from the **pre-frozen manifest** and requires `id_for("RECIPE_VERSION", predecessor_key) == predecessor_id`. The Recipe application service must additionally fetch `scope.versions.get_detail(predecessor_id)` in the *same caller-owned UoW* and confirm that this live persisted immutable v1 agrees with the pinned source, ordered Steps, rights, ingredients and lineage **before** append. A provider ledger entry or a matching UUID alone does not establish DB authority. Missing/mismatched predecessor or non-unique manifest entry is `NO_GO_TEST_ONLY_ID_SEAM_UNPROVEN` and rolls back the existing UoW. The provider never accepts a historical run's foreign-key UUID as source authority.

**Why this narrower surface:** All required inputs `recipe.canonical_code`, `seed`, `number`, `previous_id` already reach `_new_detail`. The published correction artifact's SHA and process witness live in the independently pre-frozen manifest, **not** inside the production-facing `TrustedRecipeVersionSeed` or domain. This adds one provider protocol method, while the only production-facing constructor change remains the **optional** `id_provider=None` already proposed in #262. No additional `append_trusted_version_in_scope`, `reconcile_seed_in_scope`, `create_trusted`, `_new_detail` or DC4-A3 function argument is approved here. If those prove necessary, stop for a new documented decision.

### 2.1. Exact impact / non-impact matrix

| Boundary | Existing invocation | Proposed opt-in behavior | Normal-path guarantee |
| --- | --- | --- | --- |
| `FixtureTypedIdProvider` and draft #263 `ManifestPinnedFixtureIds` | `id_for(kind,key)` only | Add `recipe_version_key_for(*, canonical_code, seed, version_number, predecessor_id)`; lookup a **sealed external fixture manifest**, reject missing/ambiguous/mismatched seed and predecessor | No global registry, environment selector, mutable ordering counter or production identity fallback |
| `FoodRecipeCatalogueService.__init__` | `id_factory=uuid4, clock=None` | The **existing #262 proposed** optional `id_provider=None` carries the extended test-only protocol | Absent provider retains the exact `self._id()` call order and existing normal publication checks |
| `FoodRecipeCatalogueService._new_detail` | `scope, recipe, seed, number, previous_id, now` | **Same signature**; if opted in, read/check predecessor in same UoW, resolve version key, allocate version/ingredient/Step IDs with old `id_for` | Without provider: no new reads, checks, IDs or sequence changes |
| `create_food_recipe_catalogue_service(engine)` | `(engine)` | Only #262-approved `(engine, *, id_provider=None)` | `(engine)` still selects old `uuid4` path |
| 12 Recipe seed modules / 22 composer sites | #262 inventory | Forward **only** the previously approved optional `id_provider`; no new `publication_context` argument | Normal CLI, seed, R3-A/B callbacks, rights and nutrition unchanged |
| `dc4_a3._publish_one` / `append_trusted_version_in_scope` | Exact v1 replay → in-scope append trusted v2 → prepared authority → commit; or existing-v2 `EXACT_REPLAY` | **No new arguments**; same seed/old-new Step validation, plus provider resolution within existing Recipe service on actual fresh v2 | Normal path byte-unchanged and previous source/replay conflicts remain mandatory |
| Household, FoodIngredient, Planner, MealPlan/Serving, schema and UI | Current production contracts | **No changes** under this amendment | No new owner or broader identity surface; Planner tie-break and UoW writes remain authentic |

## 3. Manifest and authority: what the resolver must verify

The pre-run manifest must be prepared, source-reviewed and **pinned in a separate trusted commit or equivalent owner-accepted immutable evidence BEFORE any fixture output**. It must contain a complete **unique** record for every expected `(canonical_code, version_number, source_record_key, predecessor semantic key)` in the known fixture corpus. It is not learned by replaying or selecting an attractive week.

For each publication record, at minimum:

- The **exact #262 six-kind canonical key** for `RECIPE_VERSION`, including reviewed source tuple, `publication_kind`, `publication_process_sha256`, `correction_revision_sha256`, full predecessor key/null, and version number. This amendment does not change key JSON fields, canonicalization or the two golden vectors.
- A separately pinned **full trusted-seed projection** against which every live `TrustedRecipeVersionSeed` field is checked: original servings; meal/prep/cook/total times; difficulty; batch/freezer/storage fields; verification and rights status/basis; source name, recipe ID, URL, version, retrieval time/document SHA; source-output data; `change_note`; all ingredients in order (canonical FoodIngredient code, exact canonical Decimal quantity, unit/form, source amount, notes, optional); all ordered Step text; equipment codes; verification timestamps and any other present `TrustedRecipeVersionSeed` field. Use field-complete deterministic typed equality with explicit Decimal canonical strings, NFC strings, enum values, UTC instant formatting and nulls. Never choose a key on just `canonical_code` or `change_note`. An **unrecognized new seed field** is a STOP until its semantic treatment is reviewed.
- Immutable evidence references for original raw source/rights and, for v2, the **same already approved** DC4-A3 artifact with both raw Git blob SHA-1 `ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68` and exact bytes SHA-256 `157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759`, validated from `CORRECTIONS_PATH.read_bytes()`. `publication_process_sha256` is an **independently frozen published process/ordered-Step witness**, not any `process_hash` including transient Step UUIDs. Its exact derivation + accepted value for each version must be pinned before approval of the *fixture run*, not invented by the provider.
- A v2 entry matching **one of exactly seven accepted correction codes**, whose `old_steps` equal the persisted/source-verified predecessor and `new_steps` equal the prospective successor seed. The review reference, rights, ingredients, output mass and in-scope energy authority must not change by virtue of identity injection. Existing DC4-A3 checks remain authoritative.

**Selection and ambiguity rules:** Match the complete version `seed` projection, expected number, source tuple and predecessor from the sealed manifest. Zero matches, multiple matches, changed rights/Steps/ingredient form, unexpected version number, inconsistent source SHA, modified correction file, missing external process evidence or a predecessor not linked to live persisted v1 all **fail closed before ID acceptance**. A match does not confer permission to publish or alter an invalid source; existing application and nutrition policies still apply.

**Trust split:**
- `source loaders + rights/Step/nutrition validation` → authoritative publish eligibility;
- `sealed fixture manifest + typed key resolver` → predictable **test identity only**;
- `real repository/UoW` → live ID, predecessor, immutable version and actual persisted readback.
Do not let one layer substitute for another.

### 3.1. P2 follow-up — explicit test-only manifest loader for draft #263

**Implementation acceptance requirement, not a blocker for merging this docs-only proposal.** The current draft #263 constructor `ManifestPinnedFixtureIds(approved: Sequence[tuple[Kind, Key]])` can validate the allowlist for `id_for`, but **cannot** perform `recipe_version_key_for`: it lacks trusted-seed projections, independently reviewed original/correction provenance and complete predecessor lineage. Continuing #263 must therefore replace or augment this **test-only constructor input** with a fully defined, validated manifest loader; this is not a new production-facing service/seed argument and does not authorize an additional provider protocol method beyond §2.

**Required input contract for the future loader, to be made concrete and tested in #263:**

1. **Explicit input and pin.** Read a dedicated, versioned fixture-manifest artifact by an explicitly supplied path/reference plus independently accepted expected raw SHA-256 and source commit; do not discover it from a database, previous Planner outputs or an ambient environment variable. Specify schema version, fixture policy/namespace/ID, canonical encoding, source commit/revision, review provenance and whether the original artifact bytes are accepted before allocating any UUID.
2. **Two joined immutable datasets.** Include both (a) the existing closed-kind approved `(kind,key)` allowlist and (b) a publication-record index containing canonical `RECIPE_VERSION.key`, the **complete** frozen `TrustedRecipeVersionSeed` projection, source/rights/ordered ingredient+Step evidence, process witness, correction-artifact SHA-256 (or explicit null for original v1), predecessor **semantic key**, expected version number and current reviewed correction code/old→new Step mapping where applicable. Every publication key must be present in the approved allowlist, including the recursive predecessor; neither index may introduce keys missing from the other relevant domain. Explicitly validate the relationship rather than infer it from a generated UUID.
3. **Immutability and ownership.** Validate/deep-freeze nested mappings, sequences and Decimal/enum/instant normalization at load time; the provider receives a sealed read-only snapshot scoped to one disposable fixture run. Mutating a caller's dictionaries after construction, a changed manifest file, sharing between fixture/normal seeds, late registration and fallback to `uuid4` in opt-in mode must be rejected. Any typed-key ledger remains per-fixture and never becomes a source of authority.
4. **Completeness preflight.** Before any DB publication, verify that the manifest covers the externally reviewed expected corpus (all relevant original v1, all seven accepted DC4-A3 v2 corrections and each required intermediate seed stage), with unique `(canonical_code, version_number, full source identity, predecessor key)`, exactly one authorized publication-record match for every expected trusted seed, and no extra/duplicate/unreachable source version. Freeze expected counts and source-stage membership **from independently reviewed input inventory**, not from the selected/generated week or a database scan. Explicitly reconcile conditional R3-A/R3-B/R3-C/R3-D branches and the 12-module/22-composer inventory; audit which branches actually execute separately.
5. **Exact lookup semantics.** `recipe_version_key_for` selects by canonical code, exact complete seed projection, version number and frozen semantic lineage. The supplied `predecessor_id` is only an equality witness against `id_for("RECIPE_VERSION", frozen_predecessor_key)`, plus the live same-UoW repository read specified above; **no reverse search on persisted UUIDs**, no creating/learning a manifest from newly allocated IDs, no version-number-only fallback, no source field repair and no silent new entry on a miss.

**Implementation-spec checkpoint:** In #263 publish the actual test-only manifest schema (field types, record envelope, serialization), loader function and constructor signature, independent raw fixture digest/provenance, closed-coverage audit, immutable snapshot semantics and unit/integration test receipts **before** the 12/22 seed bridge is considered complete. An illustrative acceptable flow is `externally pinned artifact → load + verify → frozen approved-key/publication index → manifest-bound provider → real seed/UoW`. This diagram is not an approval of a particular Python signature or final manifest file format; that exact test-only interface is a required #263 review deliverable.

**P2 negative tests for #263:** approved-ID-only old constructor cannot be used to resolve a publication; missing trusted projection, absent correction artifact, wrong old/new Steps, omitted predecessor, stale/wrong source SHA, unapproved extra version, incomplete seed-stage coverage, mutated input after load, altered artifact bytes, duplicate entries and attempts to resolve by persisted UUID all yield explicit NO_GO **before any accepted fixture IDs/writes**. Prove that a fresh independent process loading the same pinned manifest resolves identical semantic keys without observing another run's database.

## 4. Fresh/replay/conflict, transaction and rollback contract

| Case | Required disposition |
| --- | --- |
| Fresh original v1 | Bind `RECIPE` and complete original `RECIPE_VERSION` keys from reviewed manifest; allocate child IDs from frozen version key; save through unchanged real UoW |
| Fresh DC4-A3 corrected v2 | Require accepted old source exact replay, real v1 predecessor current, exactly one reviewed correction entry, pinned SHA/Steps, `created_from_version_id` equality, in-scope prepared nutrition and existing atomic commit |
| Identical seed replay | Existing `EXACT_REPLAY` resolves **same persisted UUID rows** and unchanged nutrition/rights, without a fresh version or new child IDs; independently audit those IDs against the sealed manifest after replay |
| Current corrected v2 replay | Require exactly one successor v2, correct v1 lineage, same frozen correction artifact and source/Step data, correct current prepared authority; existing `EXACT_REPLAY` only |
| Changed Step/ingredient/rights/process/nutrition/manifest | `NO_GO`; no key re-label, second v2, silent v3, source mutation or compensating fixture output |
| Wrong/missing predecessor or partial R3 prerequisite batch | `NO_GO`; preserve existing partial-state conflict rules and transaction rollback |
| Providerless ordinary seed | Exactly pre-existing `uuid4` factory, default API/CLI, SQL writes, commit/replay and Planner behavior |

On failure, UoW must roll back all Recipe/Version/Ingredient/Step and prepared-nutrition writes. A partially allocated **in-memory** ledger may only be discarded with its test scope; it must never be persisted as production truth. Fixture receipts must record expected keys, derived UUIDs, actual persisted row IDs and source/rights/provenance checks independently, including both inverse mappings. No global cache/contextvar/monkeypatch, environment activation or relaxed domain UUIDv4 validation.

## 5. Mandatory adversarial acceptance tests for a later #263 revision (NOT run here)

1. **Provider unit tests:** frozen 2 golden vectors unchanged; all six key schema tests; v1 and each of seven v2 resolved from explicitly preapproved seed/manifest; malformed SHA, Decimal, NFC, wrong enum, duplicate keys and collisions fail closed.
2. **Missing-correction-source tests:** change a byte in `corrections.json`, replace its Git blob/SHA-256, omit correction record, change old/new Step, swap two correction recipe codes or substitute v1 source SHA for correction SHA → hard NO_GO before ID acceptance, no writes.
3. **Predecessor/live UoW tests:** missing, different-recipe, wrong-v1, unverified, stale or UUID-mismatched predecessor rejected; assert `created_from_version_id` and real child UUID/parent FKs; no reliance on hash of DB-generated `RecipeStep.id`.
4. **Fresh/replay tests:** fresh v1 then v2 append, exact repeated seed and repeated DC4-A3 correction yield the same source-bound UUIDs, one current v2, exact prepared authority and no extra rows; partial prerequisites fail closed.
5. **Full 12/22 propagation audit:** R1-F → R3-D and DC4-A3; R3-A/B publish/activate and conditional R3-C/R3-D prerequisites; log actual **mutating vs read-only** composer paths, no providerless allocations in opted-in fixture.
6. **Ordinary default isolation:** separate fresh SQLite normal seed with no provider remains random UUIDv4, identical source/version/Step and rights behavior; no deterministic test IDs leak to API/regular CLI/another DB/process. Reject simultaneously supplied conflicting `id_factory` and provider.
7. **Failure injection/rollback:** wrong manifest, changed source, failed nutrition publication or mismatched predecessor causes no committed partial publication or source/rights edits; retry after error requires new clean test scope.
8. **Verification tier:** focused UUID/provider tests + Recipe service/repository/UoW + DC4-A3/R3 stage integration and ordinary-default regression; broaden relevant startup/composition checks per [verification policy](verification-policy.md). Record exact-head CI; no test in this docs-only amendment and no existing negative evidence rewritten.

**Separate later proof, NOT a #263 acceptance substitution:** after a fully approved and merged typed-ID implementation, run two independent fresh SQLite/Python processes calling unchanged real `PlannerService.generate_authoritative` and persisted UoW readback. Require 3 members, 7 household-local days, **21 genuine source-bound MealEvents and 42 exact Decimal Servings**, full pre-frozen input/candidate/tie-order parity and identical UUID-free semantic week. A passing ID test never satisfies this. The historical #196 fixture remains archived, not a new generated target.

## 6. Impact, non-goals and owner decision

**This docs PR only:** one new bounded amendment + concise `state/current-focus.md`, `state/progress.md`, `state/handoff.md`. No backend/Python, fixtures, scripts, migrations, source corpus, persisted data, API/UI, Planner, Nutrition, Prep, PDF, Retail or AI modifications. Do not edit merged #262 or partial draft #263 under this docs-only authorization.

**If and only if accepted:** §2 supersedes **only** #262's `FixtureTypedIdProvider` method surface by adding `recipe_version_key_for`; all #262 ID algorithm and optional public composition/seed signatures survive unchanged. Runtime implementation continues in **the existing separate draft PR #263**, after explicit owner resumption authorization; do not open a duplicate runtime PR, merge drafts automatically or conflate its CI with fixture success. Because #263 also edits `state/*`, reconcile those files with this docs amendment **after** any authorized merge; main stays working.

**Owner options after independent Architecture / Domain / QA review:**
- **APPROVE THE NARROW EXTENDED PROVIDER CONTRACT** and authorize a subsequent explicit #263 resumption task; no auto-merge.
- **REQUEST CHANGES**, specifying which manifest/provenance/lineage or API surface lacks proof.
- **REJECT / NO_GO**, retain draft #263 partial and propose an independently reviewed alternative. No call-order UUID queue, additional unapproved producer method/parameter or artificial Planner selection.

**Existing hard stops are unchanged:** `NO_GO_TEST_ONLY_ID_SEAM_UNPROVEN` pending proven bridge; `NO_GO_TO_PR10_CORE_RUNTIME`; `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`; `APPROVED_IMMEDIATE=0`; `SAFE_BATCH_READY=false`; `PORTION_RELEASE_READY=NOT_PROVEN`. D3 anti-rollback, two independently approved real COOK_RECIPE Prep actions, Gate2, safe-batch and portion release remain separately blocked.
