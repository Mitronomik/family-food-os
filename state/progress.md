# Progress

Updated: `2026-09-04`

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

Status: **COMPLETE**

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
API or frontend behavior changed in PR4-DATA, and no Recipe implementation was
started in that supporting operation. PR4-DATA was then accepted and merged;
PR5 remains unauthorized.

Closure evidence:

- final review: `PR4-DATA FINAL REVIEW: ACCEPT`;
- GitHub PR `#8`: **MERGED**;
- accepted head: `59cc1073ac1f951da5b172eb111ed162765b5eaf`;
- merge commit: `704c588387a28e18ac1aa947ded398f168875ea0`.

## PR4 — Verified Recipe Catalogue

Status: **READY FOR REVIEW**

Branch `migration/pr4-recipe-catalogue` is based on and currently has working-
tree HEAD `704c588387a28e18ac1aa947ded398f168875ea0`. The review candidate appends
migration `0024_food_recipe_catalogue` and adds the platform-owned Recipe,
RecipeVersion, RecipeIngredient, RecipeStep and RecipeEquipment model without
altering legacy recipe tables.

Implementation evidence:

- Recipe and RecipeVersion identities use application-generated UUIDv4;
- complete version aggregates are written atomically through driver-independent
  contracts and a Recipe Catalogue UoW over synchronous SQLAlchemy Core;
- versions and version-owned children have direct SQLite update/delete guards;
- v2 appends to v1, links through same-Recipe `created_from_version_id`, and
  advances current verified lookup without changing the v1 snapshot;
- deterministic read-only scaling uses exact Decimal arithmetic: 6→3 maps
  600 g→300 g and 1 pcs→0.5 pcs; 6→9 maps 600 g→900 g and 1 pcs→1.5 pcs;
- successful and failed commit/rollback terminality revokes repositories and a
  later UoW remains clean;
- no HTTP API, frontend, nutrition calculation or PR5+ context was added.

Corpus and rights evidence:

- 30 active Recipes and 30 current `SOURCE_VERIFIED` v1 records;
- 365 RecipeIngredients, 315 RecipeSteps and 0 RecipeEquipment rows;
- source mix: 3 Breakfasts, 8 Main Dishes, 11 Side Dishes, 3 Salads,
  3 Sandwiches and 2 Standardized Recipes Project 2024 cards;
- all 30 manifests have unique full SHA-256 values, original servings of six,
  reviewed rights basis and USDA attribution evidence;
- exact accepted FoodIngredient subset: 119 codes; unresolved required lines: 0;
  FoodIngredients introduced by PR4: 0;
- the 363-row PR4-DATA matrix becomes 365 RecipeIngredients: one non-consumable
  Bean Burrito Bowl structural marker is omitted, while three water rows with
  two explicit semicolon-plus quantities are each represented by two lines;

Seed and verification evidence:

- exact source-PDF rebuild matches both checked-in JSON artifacts byte-for-byte;
- first fresh run inserted Recipes/Versions/Ingredients/Steps/Equipment
  `30/30/365/315/0`, conflicts `0`;
- second identical run inserted `0/0/0/0/0`, reported all rows existing, and
  conflicts remained `0`;
- PR4-focused and affected migration suite: `80 passed`;
- backend suite within final regression: `2174 passed`;
- full backend + launcher regression: `2819 passed`;
- Ruff format/check and `git diff --check`: passed.

PR4 remains a review candidate, not COMPLETE. PR5 is unauthorized.
