# Progress

Updated: `2026-09-05`

## Current execution — PR4 DATA2 integration

PR4-DATA2 — COMPLETE. PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.
Accepted head: `918bf81b5da306fc65a57643de515ca1b3fbd1e4`.
Merge commit / synchronized main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
Final review submitted at `2026-09-05T16:06:13Z`; merged at
`2026-09-05T16:26:20Z`.

PR4 — IN PROGRESS on existing open PR #10, branch
`migration/pr4-recipe-catalogue`; starting head
`cd2285802c94735e0c9015042f9f4c0b52d68b85`.
Current main is being synchronized by normal merge, with accepted DATA2
preserved. No rebase, force-push, new PR or PR merge is authorized.

Existing PR4 Recipe/domain/application/persistence code and migration
`0024_food_recipe_catalogue` remain present. Production seed/compiler still
require DATA2 correction. The prior rights blocker is superseded by accepted
DATA2 source-specific review under the narrow direct-FNS project risk posture.
Source retrieval instants are under investigation before seed regeneration;
no date-only value may be converted into invented midnight provenance.

PR4 is neither COMPLETE nor ready for final review. PR5 remains unauthorized.
The accepted-main records below are retained as historical execution evidence;
their pre-merge DATA2 status/next-action sentences are superseded here.


## Current supporting operation

PR4-DATA2 correction is READY FOR REVIEW. The initial regional-browser blocker is superseded; see the corrected evidence record at the end of this file.

## FamilyFoodOS bootstrap

FamilyFoodOS was created as a separate repository using the verified engineering baseline of CosmeticWorkshopOS.

Source:

- repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- target repository: `Mitronomik/family-food-os`

Detailed provenance:

- `docs/migration-source.md`

Legacy CosmeticWorkshopOS lifecycle history remains available in Git history, the bootstrap tag and inherited historical documentation. It is not the active FamilyFoodOS roadmap.

## PR0 — Frozen Fork

Status: **COMPLETE**

Completed PR0 deliverables:

- [x] separate FamilyFoodOS repository created;
- [x] complete Git history preserved;
- [x] bootstrap tag created;
- [x] source remote retained as read-only reference;
- [x] FamilyFoodOS `main` bootstrap pushed;
- [x] frozen source baseline verified;
- [x] `docs/migration-source.md` added;
- [x] FamilyFoodOS technical specification added;
- [x] FamilyFoodOS data-ingestion specification added;
- [x] FamilyFoodOS migration plan added;
- [x] FamilyFoodOS Project Operating Manual added;
- [x] root `AGENTS.md` migrated to FamilyFoodOS;
- [x] active `state/current-focus.md` migrated;
- [x] active `state/progress.md` migrated;
- [x] active `state/handoff.md` migrated;
- [x] documentation/governance diff reviewed;
- [x] runtime paths verified unchanged;
- [x] obvious-secret/privacy audit passed;
- [x] `git diff --check` passed;
- [x] backend + launcher tests passed;
- [x] macOS package tests passed;
- [x] frontend build passed;
- [x] frontend test scripts passed;
- [x] full application startup smoke passed;
- [x] PR0 GitHub review performed.

GitHub PR/merge metadata remains authoritative in GitHub history and is not maintained as a mutable checklist in this file.

## Verified baseline

Results:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- frontend test scripts: `22 passed, 0 failed`
- frontend build: passed
- startup smoke: `PASS`
- npm: `0 vulnerabilities`

Startup smoke verified:

- backend HTTP `200`;
- frontend HTTP `200`;
- frontend API proxy HTTP `200`;
- proxy payload matched backend health payload.

## Runtime implementation

No FamilyFoodOS runtime/domain implementation was introduced by PR0.

The runtime remains intentionally inherited from CosmeticWorkshopOS at the PR0 boundary.

## PR1 — Identity Detox

Status: **COMPLETE**

Verified closure:

- active project, runtime, launcher and frontend identity is FamilyFoodOS;
- active project-owned UI guidance is `.agents/skills/family-food-ui/SKILL.md`;
- inherited root and current-location documentation is explicitly classified;
- old identity remains only as accepted provenance/history, immutable legacy
  evidence, explicit legacy documentation and negative/legacy tests;
- backend + launcher regression: `2573 passed, 0 failed, 0 skipped`;
- frontend build: passed;
- all 25 defined frontend `test:*` scripts: passed;
- isolated FamilyFoodOS source-runtime startup smoke: passed;
- static identity gate: zero active blockers;
- final PR1 acceptance worktree: clean.

PR1 changed identity while preserving inherited runtime, API, schema and
transitional frontend behavior.

## PR2-A — FamilyFoodOS Architecture & Persistence Contract

Status: **COMPLETE**

Completion evidence:

- canonical `docs/family-food/architecture.md` created;
- ADR 0032 accepted;
- migration plan aligned with the persistence and shared-deployment gates;
- adversarial architecture review initially returned `CHANGES REQUIRED`;
- all three blocker classes were resolved: persistence technology, migration
  authority and derived-state invalidation;
- final corrections also resolved Unit-of-Work read/write scopes, canonical
  ingredient naming, Food Product Type disposition, Household/Auth semantics
  and UTC versus household-local timezone rules;
- documentation-only verification passed;
- no runtime, schema, migration or dependency changes occurred in PR2-A.

## PR2-B — Persistence Foundation

Status: **COMPLETE**

Acceptance evidence:

- synchronous SQLAlchemy 2.x Core foundation implemented with dependency
  constraint `SQLAlchemy>=2.0.52,<2.1`;
- driver-independent application Unit of Work contract and SQLite SQLAlchemy
  adapter established;
- explicit transaction ownership implemented; commit and rollback are terminal
  and immediately revoke the active connection;
- failed commit or rollback cannot contaminate a later pooled command;
- SQLite foreign keys and structured, special-character-safe path handling are
  enforced by the adapter;
- identifiers are application-generated `uuid.UUID` values using UUIDv4 and
  generic SQLAlchemy `Uuid` persistence;
- UTC-normalizing instant persistence primitive established;
- the custom migration runner remains the sole SQLite schema authority;
- no production food tables, food migrations or runtime rewiring were added;
- adversarial final review: `PR2-B FINAL REVIEW: ACCEPT`;
- readiness decision: `READY FOR HOUSEHOLD`;
- targeted persistence suite: `30 passed`;
- backend + launcher regression: `2603 passed`.

## PR2-C — Household Foundation

Status: **COMPLETE**

Acceptance evidence:

- new `Household` and `HouseholdMember` domain models use application-generated
  UUIDv4 identifiers and aware UTC instants;
- Household validates an IANA timezone through standard-library `zoneinfo`;
- Household persists optional city, Decimal-safe weekly budget and generic
  cooking profile without adding Auth or currency/FX behavior;
- HouseholdMember persists birth date, optional sex, explicit `height_cm` and
  `weight_kg`, activity level, goal and active state without medical semantics;
- application-facing repository and Household-specific UoW/read-scope contracts
  remain driver-independent;
- concrete repositories use one active PR2-B SQLAlchemy Core connection and
  never open or complete their own transaction;
- migration `0022_household_foundation` creates `households` and
  `household_members` beside all inherited tables, with a real foreign key;
- the custom `schema_migrations` lineage remains the sole SQLite schema truth;
- all required POST/GET/PATCH Household and nested member routes are wired
  through application operations;
- complete acceptance flow with three members passes through FastAPI to SQLite;
- wrong-Household member lookup/update returns no entity and the API returns
  `404` without cross-Household data;
- unsupported fields, including fake `owner_id`, are rejected;
- rollback, no-partial-state, independent-read visibility, UUID/UTC/Decimal
  round trips and foreign-key enforcement are covered by tests;
- correction-pass terminality tests prove repositories are revoked after
  successful and failed commit/rollback attempts and later UoWs are clean;
- non-finite, extreme-exponent and negative sub-cent Decimal input follows
  stable domain/API validation instead of leaking `decimal.InvalidOperation`;
- future birth-date validation uses an injected aware clock and the persisted
  Household timezone rather than process-local time;
- PR2-C correction-pass targeted suite: `196 passed`;
- full backend + launcher regression: `2684 passed`;
- Ruff checks, Ruff formatting checks and `git diff --check`: passed.

Closure evidence:

- final adversarial review: `PR2-C FINAL REVIEW: ACCEPT`;
- GitHub PR `#5`: **MERGED**;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`;
- merged at: `2026-09-01T21:23:23Z`;
- no remaining PR2-C blocker.

Deliberately deferred:

- Household membership/Auth/principal roles;
- FoodPreference and excluded ingredients until the canonical FoodIngredient
  catalogue exists;
- member role, meals-at-home scheduling, portion adjustment and detailed
  planner/nutrition semantics;
- controlled vocabularies and calculation meaning for activity level and goal.

## PR2-DOCS — Canonical Roadmap & PR2-C Closure Sync

Status: **COMPLETE**

This documentation-only governance sync:

- adds `docs/family-food/master-roadmap.md` as the canonical implementation
  sequence and delivery-gate contract;
- aligns the migration plan without changing its migration-strategy ownership;
- adds narrow compatibility notes to older source-style specifications;
- synchronizes repository state with the accepted and merged PR2-C result.

Closure evidence:

- GitHub PR `#6`: **MERGED**;
- accepted head: `351a0a7e374312d6dda4b7e0e746d6a54579de61`;
- merge commit: `a5b6ca5d210b2401a2fa7e4037a957ec7b846774`.

## PR3 — FoodIngredient Catalogue

Status: **COMPLETE**

Implementation evidence:

- canonical platform-owned `FoodIngredient`, `IngredientAlias` and
  `FoodNutritionProfile` domain types use application UUIDv4, aware UTC instants,
  deterministic Unicode search keys and total exact-Decimal validation;
- allergen review state distinguishes unknown, reviewed-empty and reviewed with
  structural codes; the technical seed remains explicitly unreviewed;
- driver-independent repository, Food Catalogue UoW and read-scope contracts
  compose the accepted synchronous SQLAlchemy 2.x Core adapter without exposing
  SQLAlchemy, DBAPI or `sqlite3` through application/domain APIs;
- migration `0023_food_ingredient_catalogue` adds `food_ingredients`,
  `food_ingredient_aliases`, `food_nutrition_profiles` and
  `food_ingredient_allergens` after `0022_household_foundation` with real foreign
  keys, uniqueness, current-profile and lookup indexes;
- fresh and `0022 → 0023` upgrades preserve the legacy `ingredients` and
  Household schemas; the custom migration chain remains the only SQLite schema
  authority;
- checked-in trusted seed contains exactly `100` active FoodIngredients and
  `89` aliases, backed by USDA FoodData Central Foundation Foods `2026-04-30`
  (`87` records) and final SR Legacy `2018-04` (`13` records);
- first seed run inserts `100` ingredients, `89` aliases and `100` nutrition
  profiles; the second identical run inserts zero and reports all rows existing;
- every active seed item has exactly one current profile with source name, FDC
  identifier, exact release, data type and verification instant;
- `греч` deterministically returns `BUCKWHEAT` first; `СВЕКЛА` resolves `BEET`
  through Python NFKC/casefold/`ё → е` normalization;
- deactivation preserves identity, aliases and nutrition history, hides the
  ingredient from default search and is not reversed by seed reruns;
- atomic seed conflict, failed UoW cleanliness and terminal repository-handle
  revocation are covered;
- direct PR3 focused suite: `77 passed`;
- expanded PR3 + affected migration/lineage suite: `154 passed`;
- full backend + launcher regression: `2761 passed`;
- Ruff format/check and `git diff --check`: passed.

Closure evidence:

- final adversarial review: `PR3 FINAL REVIEW: ACCEPT`;
- GitHub PR `#7`: **MERGED**;
- accepted head: `b4d886824989a67711fca0b28821e60934279e6b`;
- merge commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`.

Deliberately deferred:

- `IngredientUnitProfile` because all technical-slice defaults are mass-based
  and no reviewed `pcs → grams` conversion is required;
- density, edible fraction, storage-duration and regulatory allergen claims when
  this slice has no authoritative reviewed value;
- public mutation/read HTTP endpoints and all frontend work;
- Recipe, Pantry, Nutrition Engine calculations, Planner, Shopping, Prep,
  Retail, Data Program automation, PostgreSQL, Auth, HouseholdMembership and AI.

## PR4-DATA — Recipe Corpus FoodIngredient Coverage

Status: **READY FOR REVIEW**

PR4-DATA is a supporting data operation, not a product milestone. It runs on
branch `data/pr4-recipe-ingredient-coverage` from accepted PR3 merge commit
`1a67fd96e9d2921ed986dc887081bbfe57c4dd83`.

The initial 30-recipe corpus required 126 unique FoodIngredient concepts. Exact
marginal analysis identified `Roasted Potato and Turkey Hash` at six exclusive
concepts and `Brown Rice Pilaf` at three. Replacing them with the already
reviewed six-serving `Vegetable Frittata Bites` and `Cauliflower Rice`
candidates contributes one new concept each. One replacement could reach only
121, so two replacements are the minimum needed to preserve Gate 2 unchanged.

Durable curation evidence under `data/curation/pr4/` now freezes the corrected
30 directly published USDA FNS CACFP six-serving recipe cards and proves:

- 363 represented source ingredient rows;
- 358 per-recipe concept occurrences after within-recipe deduplication;
- 310 distinct transcribed source ingredient texts;
- 119 unique canonical FoodIngredient codes in the exact MVP0 manifest;
- 36 concepts pre-existed in the accepted PR3 catalogue;
- 83 corpus-required concepts were added;
- 0 source ingredient rows were dropped;
- 0 ambiguous or unresolved required rows remain.

The global catalogue now contains 183 active FoodIngredients, 172 aliases and
183 nutrition profiles. The 83 additions use 15 USDA FoodData Central
Foundation Foods records from the `2026-04-30` release and 68 SR Legacy records
from the `2018-04` release. A fresh-database seed inserted all 183/172/183 rows;
an identical second run inserted zero rows and reported all rows as existing.

The production loader's historical `80–120` milestone-cardinality restriction
was removed. It still rejects an empty catalogue and retains record, collision,
nutrition, provenance and domain validation. The exact 119-code Gate 2 bound is
instead enforced by curation/data-quality tests and the MVP0 manifest.

Verification evidence:

- focused seed suite: `13 passed`;
- PR4-DATA curation suite: `4 passed`;
- full backend + launcher regression: `2766 passed`;
- Ruff format/check and `git diff --check`: passed.

No FoodIngredient schema, migration, domain, repository, UoW, search, allergen,
API or frontend behavior changed. No Recipe schema, domain, persistence or
implementation was started. `PR4 — Recipe Catalogue` remains the next product
milestone and waits for PR4-DATA acceptance/merge. PR5 remains unauthorized.


## PR4-DATA2 — Russia/SPB Recipe Corpus Re-curation

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). This direction-consumables
correction begins at reviewed head `66a30403e3463248bb9b66e5a40920ef3fb136b5`.
The delivered head is recorded exactly in PR #13 after push, not as a
self-referential commit hash in its own contents.

Final: **30 recipes**, **28 retained / 2 replaced in this correction pass**;
relative to historical PR4: **3 retained / 27 replaced**. Both forbidden ICN
cards remain absent. **225 source-audit rows / 189 selected rows** (185 required,
3 source-explicit optional, 1 conditional); exact **81 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**86 source-backed equipment rows / 34 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 5 / side 5 / salad 6 /
sandwich 1 / other 10**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 5 /
SIDE_DISH 11 / SOUP 2 / DESSERT 3 / SNACK 4 / CONDIMENT 1 / SANDWICH 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **11 pure sides**;
six primary-protein families: **DAIRY 1 / EGG 2 / FISH 2 / LEGUME_TOFU 1 /
MEAT 1 / POULTRY 1** among anchors.

All 30 actual sources were audited beyond ingredient lists: **281 consumable
audit rows**. At the reviewed head, **9 recipes / 19 direction-only edible
rows** included two required unquantified pan-release sprays. Honey Lime
Chicken and Local Harvest Bake were replaced, not silently edited. The final
corpus has **9 recipes / 24 direction-only edible rows**, all explicitly
resolved; **zero unresolved required direction consumables**. Process water
discarded after preparation is excluded from those direction-only edible
counts; selected retained water is not.

**83 non-water purchase forms: 3 RU_MASS_MARKET / 80 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: **70 one-chain / 10 two-chain /
3 three-chain** forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: **187 raw / 179 unique observations,
142 AVAILABLE / 37 UNCERTAIN** (includes rejected research).
Compatibility is not momentary store stock.

All final sources have nine reviewed consistency dimensions, including
direction-only consumables; missing that ninth dimension fails closed. Exact
artifacts/hashes, attribution and notices remain under the approved narrow
direct-FNS project risk posture, including the ONIE-attributed deviled eggs.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **164 passed in
3.40s**; historical PR4-DATA/FoodIngredient affected suite **82 passed in 1.71s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` **PASS**. Five final artifacts reproduce byte-for-byte from
reviewed source/form/consumable inputs. Final staged scope audit **PASS**: 24
authorized text files, no runtime/database/binary or unrelated files. Full runtime suite
and PR4 production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

## Historical correction context

The earlier four-blocker review at `36c0cb82680fbc8a57ab4a78a41f363f3420d39d`
exposed Local Harvest's false pork/main claim, incompatible meal vocabulary,
side-heavy selection and the below-floor union. The correction delivered at
`66a30403e3463248bb9b66e5a40920ef3fb136b5` replaced five recipes and introduced
source-backed role/protein, pinned PR4 vocabulary and diversity/80..120 guards.
That was not acceptance: the later consumables review found required spray
outside ingredient lists. Its prior corpus/equipment/market aggregates are
superseded by the final counts above. Local Harvest is historically a vegetable
side, never a pork main, and is now absent for the separate spray-quantity defect.
The original `data/curation/pr4/` evidence remains immutable.

See [final review evidence](../data/curation/pr4-data2/review-report.md) for sources, replacements and consumable resolutions.
