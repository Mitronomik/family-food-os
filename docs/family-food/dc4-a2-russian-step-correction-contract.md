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
advances because the latest SOURCE_VERIFIED immutable version becomes current;
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
Recipe families.

### Fresh

If the latest current version is the accepted A1 predecessor and no exact
language-correction successor exists:

1. validate predecessor identity and all frozen non-step facts;
2. append one immutable RecipeVersion;
3. publish the matching prepared-output authority for that new version;
4. verify Russian-language readiness and Planner admission;
5. commit per Recipe atomically.

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

## 9. Planner and catalogue invariants

After all seven corrections:

- active Recipe count remains dynamically derived and currently expected to stay 51;
- Planner eligible exact-energy supply must reconcile exactly to 51:
  17 breakfast / 33 main / 1 sandwich;
- each affected Recipe current verified version is the new corrected successor;
- all seven predecessor versions remain readable as history;
- no candidate role mapping, scoring, repetitions or exclusion semantics change;
- no gate-only Recipe/Food/Nutrition authority exists.

A count mismatch is a blocker, not permission to publish filler data.

## 10. A3 required artifacts

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

## 11. Adversarial acceptance

A3 must prove:

1. predecessor RecipeVersion is unchanged and immutable;
2. exactly one successor per affected Recipe on fresh publication;
3. successor `created_from_version_id` points to predecessor;
4. only approved RecipeStep language and allowed metadata differ;
5. source URL/hash/version/rights/process/ingredients/equipment remain identical;
6. new prepared authority has same exact energy and 53 UNKNOWN;
7. exact replay is zero-write;
8. changed corrected text fails closed;
9. changed source/process/ingredient/energy commitment fails closed;
10. injected failure cannot leave a partial version/authority pair;
11. Russian-language audit clears all seven findings;
12. Planner exact-energy baseline remains 51 = 17/33/1;
13. migration head remains 0042; no 0043;
14. `AI_ENABLED=false`.

## 12. Verification tier

A3 is data publication + immutable Recipe/Nutrition integration.

Minimum review-ready verification:

- focused A3 publication/replay/conflict/rollback tests;
- affected Recipe Catalogue immutability/history tests;
- prepared-output Nutrition tests;
- Planner admission reconciliation;
- DC4 Russian-language focused audit;
- R3-A source/process regressions;
- migration and AI invariants;
- Ruff/format, diff/scope/whitespace;
- broader backend/launcher only if shared persistence/UoW/startup code changes.

Never claim old R3-A seed bytes were rewritten; they remain historical evidence.

## 13. Non-goals

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

## 14. Exit and stop rule

A2 merge authorizes exactly one separately reviewed A3 correction operation.

**A2 merge alone does not complete Track A and does not authorize DC4 rerun.**

Track A becomes accepted only when A3 is independently reviewed, merged and
verified. After both A3 and B2 are accepted, perform a separate DC4 rerun.
