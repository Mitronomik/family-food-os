# Progress

Updated: `2026-08-31`

## FamilyFoodOS bootstrap

FamilyFoodOS was created as a new repository using the verified engineering baseline of CosmeticWorkshopOS.

Source:

- repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- target repository: `Mitronomik/family-food-os`

Detailed provenance:

- `docs/migration-source.md`

Legacy CosmeticWorkshopOS lifecycle history remains available in Git history, the bootstrap tag and inherited historical documentation. It is not the active FamilyFoodOS roadmap.

## Verified baseline

Before FamilyFoodOS-specific changes:

- Python environment created successfully;
- backend dependencies installed successfully;
- frontend dependencies installed with `npm ci`;
- npm reported `0 vulnerabilities`;
- backend + launcher tests: `2546 passed`;
- macOS package tests: `146 passed, 1 skipped`;
- frontend TypeScript/build: passed;
- no baseline test failures.

## PR0 — Frozen Fork

Status: **IN PROGRESS**

Completed:

- [x] created separate local FamilyFoodOS repository;
- [x] preserved complete Git history;
- [x] created bootstrap tag;
- [x] disabled push to `cosmetic-upstream`;
- [x] created public GitHub repository `Mitronomik/family-food-os`;
- [x] pushed `main`;
- [x] pushed bootstrap tag;
- [x] verified frozen baseline;
- [x] added `docs/migration-source.md`;
- [x] added FamilyFoodOS technical specification;
- [x] added FamilyFoodOS data-ingestion specification;
- [x] added FamilyFoodOS migration plan;
- [x] added FamilyFoodOS Project Operating Manual;
- [x] replaced root `AGENTS.md` with FamilyFoodOS agent contract;
- [x] replaced legacy `state/current-focus.md`;
- [x] replaced legacy active progress state.

Remaining PR0 work:

- [ ] replace/update `state/handoff.md`;
- [ ] inspect documentation/governance diff;
- [ ] verify no unintended runtime changes;
- [ ] run appropriate lightweight checks after documentation changes;
- [ ] commit PR0;
- [ ] push branch;
- [ ] open PR0;
- [ ] review and merge PR0.

## Runtime implementation

No FamilyFoodOS runtime implementation has started.

Current runtime remains the inherited CosmeticWorkshopOS application intentionally.

PR0 must not change:

- backend runtime behavior;
- frontend runtime behavior;
- database schema;
- runtime package identity;
- food-domain models.

## Next milestone

After PR0 merges:

**PR1 — Identity Detox**

PR1 will begin separating runtime/project identity from CosmeticWorkshopOS while preserving behavior.

Do not begin PR1 from the PR0 branch.
