# FamilyFoodOS — Migration Source

**Status:** frozen bootstrap baseline
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

The unmodified bootstrap commit was verified locally before FamilyFoodOS-specific implementation began.

Environment:

- macOS
- Python 3.12.10
- pytest 8.4.2
- isolated local `.venv`
- frontend dependencies installed with `npm ci`

### Backend + launcher tests

Command: `make test`

Results:

- backend + launcher: `2546 passed`
- macOS package: `146 passed, 1 skipped`
- no test failures

### Frontend

Command: `make build`

Results:

- TypeScript compilation passed
- frontend build passed

### npm

`npm ci` reported:

- `0 vulnerabilities`

## Baseline conclusion

Commit `0ac96deace602248e0d31e7e56c7aed7fb63c62b` is the verified frozen starting point for FamilyFoodOS.

All FamilyFoodOS-specific changes must occur after this point through reviewable commits and pull requests.

Do not alter the bootstrap tag.
