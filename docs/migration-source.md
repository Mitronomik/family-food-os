# FamilyFoodOS — Migration Source

**Status:** verified frozen bootstrap baseline
**Bootstrap date:** 2026-08-31

## Source repository

FamilyFoodOS was bootstrapped from:

- Repository: `Mitronomik/cosmetic-workshop-os`
- Source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- Source commit title: `CR-017 — Decide single-client operator-assisted install/update`
- Bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`

The original repository is retained locally as a read-only reference remote:

- fetch remote: `cosmetic-upstream`
- push URL: `DISABLED`

FamilyFoodOS repository:

- origin: `https://github.com/Mitronomik/family-food-os.git`

## Migration rule

FamilyFoodOS preserves useful engineering foundations from CosmeticWorkshopOS, but is a separate product.

Do not perform blind domain renames such as:

- `Client → HouseholdMember`
- `Order → MealPlan`
- `ProductionBatch → PrepBatch`

Migration strategy:

`introduce new food-domain bounded context → move dependencies → verify → remove obsolete cosmetic context`

Git history is preserved for provenance and engineering reference.

## Frozen baseline verification

The unmodified bootstrap runtime was verified before FamilyFoodOS-specific runtime implementation began.

Environment:

- macOS
- Python 3.12.10
- pytest 8.4.2
- isolated local `.venv`
- frontend dependencies installed with `npm ci`

### Backend + launcher

Command:

`make test`

Results:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- no test failures

### Frontend build

Command:

`make build`

Results:

- TypeScript compilation passed
- frontend build passed

### Frontend tests

The non-aggregate frontend `test:*` scripts were executed individually.

Results:

- frontend test scripts passed: `22`
- frontend test scripts failed: `0`

The aggregate `test:core-workspace-feedback` alias was not rerun because it only repeats two test scripts already executed individually.

### Application startup smoke

A temporary development runtime was started using an isolated temporary SQLite database.

Verified:

- backend `/health`: HTTP `200`
- frontend root: HTTP `200`
- frontend `/api/health` proxy: HTTP `200`
- proxied health payload matched the backend health payload
- launcher/backend startup succeeded
- frontend server startup succeeded
- temporary test processes were stopped after verification
- interactive shell remained alive after cleanup

Result:

`STARTUP_SMOKE=PASS`

### npm

`npm ci` reported:

- `0 vulnerabilities`

## Baseline conclusion

Commit `0ac96deace602248e0d31e7e56c7aed7fb63c62b` is the verified frozen starting point for FamilyFoodOS.

The verified baseline covers:

- backend tests
- launcher tests
- macOS package tests
- frontend build
- frontend tests
- full local startup smoke

All FamilyFoodOS-specific runtime changes must occur after this point through reviewable commits and pull requests.

Do not alter the bootstrap tag.
