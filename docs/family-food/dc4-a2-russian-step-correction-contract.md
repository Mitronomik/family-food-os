# DC4-A2 — Immutable Russian RecipeStep Correction Contract Gate

**Status:** implementation contract / docs-only gate
**Issue:** #172
**Accepted base:** `3257e99d894c7355d6e1f080b3b4f6ce19f5d989`
**Preceded by:** PR #168 / Issue #166
**Authorizes after merge:** one separate A3 runtime/data correction PR
**Does not authorize:** DC4 rerun, Gate1-CLOSE or PR9

## 1. Goal

Correct the seven confirmed Russian-language RecipeStep violations without
mutating accepted immutable RecipeVersions, weakening provenance, changing
source recipe semantics or inventing new nutrition/ingredient truth.

A2 freezes the A3 publication contract. It changes no runtime or production data.

## 2. Accepted evidence

A1 established seven affected Recipe families / eight affected steps:

1. `SCHOOL2022_54_1R_COD_CUTLET` — step 3: `source total`
2. `SCHOOL2022_54_2R_PINK_SALMON_CUTLET` — step 3: `source total`
3. `SCHOOL2022_54_3R_POLLOCK_CUTLET` — step 3: `source total`
4. `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` — step 3: `total`
5. `SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES` — step 3: `total`
6. `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS` — steps 1 and 3:
   `cooking-fat`, `total`, `process placement`, `per-step gram split`
7. `SCHOOL2022_54_11M_BEEF_PILAF` — step 2: `total`

The underlying source/process decisions remain accepted. Only the consumer
language is defective.

## 3. Immutable revision model

A3 must create **new immutable RecipeVersions** under the same Recipe identities.

Repository migration 0027 explicitly permits multiple immutable internal
RecipeVersion revisions with identical external provenance. Therefore the new
version may retain the exact same:

- `source_name`;
- `source_recipe_id`;
- `source_url`;
- `source_version`;
- `source_retrieved_at`;
- `source_document_sha256`;
- `source_original_servings`;
- `source_output_g/source_output_text`;
- rights review.

The old version is never updated or deleted. The new version must reference the
previous current version through `created_from_version_id`.

The current Recipe identity remains one active Recipe. Current verified selection
advances because the latest SOURCE_VERIFIED immutable version becomes current.

A3 must **not** expose an active Recipe whose newest verified version lacks its
required prepared-output Nutrition authority. Therefore the new RecipeVersion and
its prepared authority must be staged and committed in one shared transaction.
Recipe activation is not toggled off/on merely to append a text correction.

## 4. Exact mutation boundary

For each affected Recipe, the new version must be byte/semantic-equivalent to
the previous current version for all fields and children **except**:

- RecipeVersion identity/version number/created timestamps;
- `created_from_version_id`;
- `change_note`, which must identify this bounded Russian-language correction
  and retain a review commitment to the unchanged source/process contract;
- the exact affected `RecipeStep.instruction` strings.

The following are forbidden to change in A3:

- Recipe canonical code/name;
- base servings;
- meal_type_code;
- prep/cook/total time;
- difficulty/batch/freezer/storage attributes;
- verification status and rights semantics;
- source identity, URL, version, retrieval timestamp and document hash;
- source output;
- RecipeIngredient identity mapping, quantity, unit, source amount text,
  normalization/prep notes and optionality;
- equipment list;
- process-branch decisions;
- household applicability;
- prepared energy amount;
- Nutrition availability semantics.

No new source fact may be inferred from the language correction.

## 5. Frozen Russian replacement rules

A3 may replace only the confirmed engineering fragments with Russian consumer
wording that preserves the accepted meaning:

- `source total` → `общий расход по исходной карте`;
- quantity `total` → `всего` or `общий расход`, according to sentence grammar;
- `cooking-fat` → `жир для приготовления`;
- `process placement` → `назначение воды по технологическим операциям`;
- `per-step gram split` → `распределение массы в граммах по этапам`.

A3 must freeze the full before/after instruction text in a reviewable curation
artifact before publication. Review must compare complete sentences, not just
substring replacement.

The accepted technical facts must remain explicit where they already were:
source totals are not silently split among operations; the water/broth branch,
12 g water placement, 313 g water total, 5.3 g oil total, and cooking
time/temperature commitments remain unchanged.

## 6. Prepared-output Nutrition authority

Every new RecipeVersion has a new immutable ID. Nutrition authority must
therefore be bound explicitly to the new version; the old version's authority
cannot be implicitly treated as belonging to the new ID.

### 6.1 Required revision-targeted publication seam

Current prepared-output publication resolves external provenance and requires
that exactly one RecipeVersion exists for that provenance. Migration 0027
explicitly permits multiple immutable internal revisions with identical external
provenance, so that existing resolution rule cannot publish A3 safely once the
successor exists.

A3 is therefore authorized to make this **bounded application-contract change**:

- add a backward-compatible optional
  `recipe_version_number: int | None = None` target to
  `ReviewedPreparedRecipeNutritionSpec`, following the explicit
  revision-targeting pattern already used by
  `ReviewedRecipeIngredientBindingSpec`;
- when the target is `None`, enumerate all exact same-provenance revisions,
  filter them through full `trusted_recipe_seed_matches(...)`, and require
  **exactly one structurally matching RecipeVersion**;
- backward compatibility therefore means existing callers need not supply the
  new parameter; it does **not** preserve the old `len(candidates) == 1`
  assumption;
- external provenance plus the trusted seed must resolve to exactly one
  structurally matching immutable RecipeVersion;
- when the target is provided, resolve all same-provenance revisions and require
  exactly one row with that exact positive `recipe_version_number`, which must
  also pass the full trusted-seed structural match;
- every A3 correction spec **must** provide the exact successor version number;
- version-number targeting does not relax structural/provenance checks;
- no implicit "latest" target is introduced and unrelated existing prepared-spec
  callers need not be rewritten merely for A3.

These `None` semantics are identical to the historical replay resolution rule
in §9.2; A2 defines no separate legacy provenance-cardinality rule.

No schema migration is needed for this application contract.

### 6.2 Required shared-transaction RecipeVersion append seam

Current public `append_trusted_version()` owns and commits its own UoW. That is
not sufficient for an active Recipe correction because the newly current
SOURCE_VERIFIED version would otherwise become visible before its new prepared
authority exists.

A3 is authorized to add a bounded
`append_trusted_version_in_scope(scope, recipe_id, seed)` (exact naming may vary)
that:

- uses a caller-owned UoW;
- validates Recipe identity and active FoodIngredient dependencies;
- appends exactly the next immutable version linked by
  `created_from_version_id`;
- performs no commit;
- contains no Nutrition decision.

A3 orchestration must use one shared SQLAlchemy UoW that structurally exposes
Recipe Catalogue repositories and prepared Nutrition repositories:

```text
preflight accepted predecessor + exact correction
→ open shared UoW
→ append successor RecipeVersion in scope
→ publish prepared authority targeted to successor version number in scope
→ verify in-scope canonical prepared nutrition / exact energy
→ commit once
```

For this language-only correction, the prepared spec uses
`require_recipe_inactive=false` **only because** RecipeVersion + authority are
created atomically in the same transaction for an already-active Recipe. This
does not change the default inactive-first rule for ordinary fresh production
recipe publication.

If the shared transaction rolls back, neither the successor RecipeVersion nor
its authority may remain.

For each corrected version A3 must publish/reconcile a new
`PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1` authority whose
reviewed source facts are identical to the previous accepted authority:

- exact `ENERGY_KCAL` remains the same;
- the other 53 frozen nutrient codes remain UNKNOWN;
- registry/nutrient-set/calculation versions remain current accepted values;
- source locator, data type, source/provenance and rights commitments remain
  identical;
- no FoodIngredient Nutrition/Composition authority is added.

The new authority is not a recalculation from invented ingredient nutrition. It
is the same reviewed prepared-output source fact explicitly rebound to the new
immutable RecipeVersion identity.

## 7. Publication and replay semantics

A3 must provide one bounded deterministic publication seam for exactly the seven
Recipe families. It may add only the two reusable application seams frozen above:
caller-owned RecipeVersion append and exact revision-targeted prepared
publication.

### Fresh

If the latest current version is the accepted A1 predecessor and no exact
language-correction successor exists:

1. validate predecessor identity and all frozen non-step facts;
2. compute/freeze the exact successor version number;
3. open one shared UoW;
4. append one immutable RecipeVersion in scope;
5. publish the matching prepared-output authority in scope targeted to that exact
   successor version number;
6. verify in-scope prepared canonical Nutrition and exact energy;
7. commit once;
8. after commit, verify Russian-language readiness and Planner admission.

The active Recipe must never expose the successor as current outside the
transaction before its authority exists.

### Exact replay

If the exact successor version and exact prepared authority already exist,
re-running A3 performs zero writes and reports exact replay.

### Conflict

Fail closed with no new version when any of the following differs from the frozen
A2/A3 contract:

- predecessor version is not the expected accepted version lineage;
- any non-step RecipeVersion field differs;
- any RecipeIngredient/equipment/process/source/rights fact differs;
- corrected step text is not the exact reviewed text;
- same correction marker exists with different data;
- prepared energy/provenance/UNKNOWN partition differs;
- partial RecipeVersion or partial Nutrition publication exists.

Do not append a second correction revision to hide a conflict.

## 8. Atomicity / rollback

The target is **per-Recipe atomic publication** of:

`new RecipeVersion aggregate + prepared-output authority`.

If current service/UoW seams cannot provide that atomic boundary without
changing a cross-context transaction contract, A3 must stop and reopen a
docs-only contract gate before implementation.

Failure injection must prove no partial new RecipeVersion/authority pair remains
after a failed fresh publication.

Publishing the seven corrections as one all-or-nothing transaction is not
required. A3 must be safely resumable across recipes and exact replay must
converge to zero writes.

## 9. Historical R3-A replay compatibility after A3

A3 must preserve the historical R3-A operation as a safe zero-write replay on a
database where the Russian-language successor already exists.

This is an explicit compatibility requirement of A2, not an implementation
detail to discover later.

### 9.1 `preflight_trusted_seed()` with same-provenance revisions

The current `preflight_trusted_seed()` requires
`len(list_by_provenance(...)) == 1`. That rule predates migration 0027
same-source immutable revisions and is not valid after A3.

A3 is authorized to change trusted-seed preflight resolution as follows:

1. resolve all RecipeVersions with the exact external provenance;
2. evaluate full `_seed_matches(...)` structural equality against the historical
   trusted seed;
3. if **exactly one** same-provenance revision structurally matches the seed,
   return `EXACT_REPLAY`, regardless of later non-matching internal successors;
4. if no provenance revision exists, retain the existing missing-provenance
   conflict semantics for an existing Recipe;
5. if provenance revisions exist but zero structural matches exist, fail closed;
6. if more than one structural match exists, fail closed as ambiguous duplicate
   immutable history.

The method must not select `latest` merely because it has the greatest version
number. Historical replay is identity-by-reviewed-structure, not current-version
selection.

`reconcile_seed(...)` already searches same-provenance candidates for a
structural match; A3 must keep preflight and reconciliation semantics aligned.

### 9.2 Historical `publish_prepared()` specs

For `ReviewedPreparedRecipeNutritionSpec.recipe_version_number is None`, the
post-A3 backward-compatible semantics are:

1. list exact same-provenance revisions;
2. filter them by full `trusted_recipe_seed_matches(...)`;
3. require exactly one structural match;
4. publish/replay prepared authority against that matched historical
   RecipeVersion;
5. never reinterpret `None` as "latest".

Thus the original R3-A prepared spec continues to resolve the original R3-A
RecipeVersion even after a language-only successor exists.

For A3 correction specs, `recipe_version_number` is mandatory and targets the
new successor exactly as frozen in §6.1.

### 9.3 `publish_r3a_school2022_main_batch()` post-A3 replay

On a database after A3:

- `_assert_replay_not_partial(...)` must resolve the historical seed/spec target
  by the structural-match rules above, not by `get_latest_verified()`;
- the historical predecessor must still have its exact prepared authority;
- `nutrition.publish_prepared(old_spec)` must return `EXACT_REPLAY` for that
  predecessor with zero writes;
- the operation must separately read `get_latest_verified()` and accept the A3
  successor as current only if it has its own valid prepared authority and exact
  energy;
- the operation must not append another historical R3-A version, overwrite the A3
  successor, or change current-version selection.

The publication result may report the current verified successor as the Recipe's
current version while the old prepared spec reports historical
`EXACT_REPLAY`; tests must make this distinction explicit rather than assuming
the replay target and current target are the same immutable ID.

### 9.4 `activate_prepared_recipe_batch()` with historical specs

The current activation path assumes the spec replay target and
`get_latest_verified()` are the same RecipeVersion. That assumption becomes
false after A3 and must be revised without weakening activation policy.

For an **already-active** Recipe after A3:

1. resolve the historical spec to its unique structural-match predecessor;
2. require the predecessor's prepared publication to be exact replay;
3. read the current latest SOURCE_VERIFIED RecipeVersion;
4. require that current version is either:
   - the same matched version; or
   - a descendant through the immutable `created_from_version_id` chain whose
     intermediate/current revisions preserve the A2-approved source identity and
     whose differences are authorized immutable internal revisions;
5. require the current version to have its **own** valid prepared-output authority;
6. require Planner admission to resolve the current version, active, eligible,
   exact-energy ready and blocker-free;
7. return `activated=False` and the **current** version ID;
8. perform zero writes.

The historical prepared spec is evidence for the predecessor; it is never
silently treated as the successor's authority.

For an **inactive** Recipe, existing activation semantics remain strict: the spec
must target the exact version being activated. Historical predecessor specs must
not activate a newer successor implicitly.

### 9.5 `activate_r3a_school2022_main_batch()` post-A3 replay

Rerunning the historical R3-A activation operation after A3 must be a compatibility
check, not a rollback operation.

For the seven corrected Recipe families it must:

- leave the Recipe active;
- retain the A3 successor as current;
- verify the historical predecessor replay and the current successor authority as
  separate facts;
- return no activation change;
- create no RecipeVersion, Nutrition authority/value, activation or deactivation
  write.

The three unaffected R3-A recipes continue through their ordinary exact-replay
path.

### 9.6 Mandatory zero-write compatibility proof

A3 must include an adversarial integration test with the exact sequence:

```text
seed/publish/activate historical R3-A
→ capture all 10 R3-A version histories + authorities + active/current IDs
→ apply all seven A3 successors + successor authorities
→ capture post-A3 database state
→ rerun publish_r3a_school2022_main_batch()
→ rerun activate_r3a_school2022_main_batch()
→ capture database state again
```

Required assertions:

- historical R3-A rerun succeeds;
- no new RecipeVersion is added;
- no current RecipeVersion rolls back to predecessor;
- no prepared authority or nutrient value is added, replaced or deleted;
- no Recipe activation state changes;
- seven corrected successors remain current;
- each old R3-A spec still resolves exactly one historical structural match;
- each corrected successor retains its own exact prepared authority;
- Planner admission remains on the corrected current successor;
- all ten R3-A Recipe families remain active and exact-energy ready;
- transaction/write counters or before/after persisted snapshots prove
  **zero-write replay**, not merely equal final values.

Any historical operation that attempts to "repair" current state back to the old
R3-A version is a contract violation.

## 10. Planner and catalogue invariants

After all seven corrections:

- active Recipe count remains dynamically derived and currently expected to stay 51;
- Planner eligible exact-energy supply must reconcile exactly to 51:
  17 breakfast / 33 main / 1 sandwich;
- each affected Recipe current verified version is the new corrected successor;
- all seven predecessor versions remain readable as history;
- no candidate role mapping, scoring, repetitions or exclusion semantics change;
- no gate-only Recipe/Food/Nutrition authority exists.

A count mismatch is a blocker, not permission to publish filler data.

## 11. A3 required artifacts

A3 must include:

- machine-readable seven-row before/after correction artifact containing
  canonical code, predecessor version ID, full old/new step arrays, source
  commitments and expected prepared energy;
- deterministic publication/replay implementation;
- focused tests;
- updated DC4 audit evidence only as a post-correction verification result, not
  as a substitute for the later separate full DC4 rerun;
- state/progress/handoff synchronization after review-ready evidence.

The curation artifact is review evidence, not a new external source.

## 12. Adversarial acceptance

A3 must prove:

1. predecessor RecipeVersion is unchanged and immutable;
2. exactly one successor per affected Recipe on fresh publication;
3. successor `created_from_version_id` points to predecessor;
4. only approved RecipeStep language and allowed metadata differ;
5. source URL/hash/version/rights/process/ingredients/equipment remain identical;
6. new prepared authority has same exact energy and 53 UNKNOWN;
7. exact replay is zero-write;
8. prepared publication targets the exact successor version number even when
   predecessor and successor share identical external provenance;
9. ordinary prepared publication still defaults to inactive-first behavior;
10. changed corrected text fails closed;
11. changed source/process/ingredient/energy commitment fails closed;
12. injected failure between version append and authority publication leaves
    neither committed;
13. historical R3-A preflight resolves exactly one old structural match despite
    the same-provenance successor;
14. historical R3-A publish + activation rerun after A3 is proven zero-write and
    leaves all corrected successors current;
15. historical predecessor authority and current successor authority remain
    distinct and unchanged;
16. Russian-language audit clears all seven findings;
17. Planner exact-energy baseline remains 51 = 17/33/1;
18. migration head remains 0042; no 0043;
19. `AI_ENABLED=false`.

## 13. Verification tier

A3 is data publication + immutable Recipe/Nutrition integration.

Minimum review-ready verification:

- focused A3 publication/replay/conflict/rollback tests;
- affected Recipe Catalogue immutability/history tests;
- prepared-output Nutrition tests;
- Planner admission reconciliation;
- DC4 Russian-language focused audit;
- R3-A source/process regressions, including the mandatory post-A3 historical
  publish/activation zero-write replay sequence;
- migration and AI invariants;
- Ruff/format, diff/scope/whitespace;
- broader backend/launcher only if shared persistence/UoW/startup code changes.

Never claim old R3-A seed bytes were rewritten; they remain historical evidence.

## 14. Non-goals

A2/A3 do not authorize:

- editing old RecipeVersions/RecipeSteps in place;
- mutating the historical R3-A source package to make the old version appear clean;
- changing source quantities/process branches/ingredients/equipment;
- changing prepared energy or filling UNKNOWN nutrients;
- new FoodIngredient authority;
- Planner algorithm changes;
- migration 0043/schema changes;
- unrelated recipe growth;
- Gate1-CLOSE, Shopping, Prep, UI, Retail, AI, Auth/PostgreSQL.

## 15. Exit and stop rule

A2 merge authorizes exactly one separately reviewed A3 correction operation.

**A2 merge alone does not complete Track A and does not authorize DC4 rerun.**

Track A becomes accepted only when A3 is independently reviewed, merged and
verified. After both A3 and B2 are accepted, perform a separate DC4 rerun.
