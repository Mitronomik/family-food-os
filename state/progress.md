# Progress

Updated: `2026-09-01`

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
- targeted Household/persistence/migration suite: `142 passed`;
- full backend + launcher regression: `2647 passed`;
- Ruff checks, Ruff formatting checks and `git diff --check`: passed.

Deliberately deferred:

- Household membership/Auth/principal roles;
- FoodPreference and excluded ingredients until the canonical FoodIngredient
  catalogue exists;
- member role, meals-at-home scheduling, portion adjustment and detailed
  planner/nutrition semantics;
- controlled vocabularies and calculation meaning for activity level and goal.

## Next milestone

`PR3 — FoodIngredient Catalogue`

Do not begin PR3 until PR2-C is reviewed and accepted. PR3 owns the canonical
platform food catalogue; it must not merge `FoodIngredient` with `RetailSKU` or
start later Nutrition, Recipe, Retail, Planner or AI work.
