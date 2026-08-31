# Current focus

Updated: `2026-08-31`

## Project

FamilyFoodOS is now a separate project bootstrapped from CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

The original source repository is retained only as engineering provenance and a read-only reference.

## Current lifecycle

PR0 — Frozen Fork — IN PROGRESS

Verified baseline before FamilyFoodOS-specific implementation:

- backend + launcher tests: `2546 passed`
- macOS package tests: `146 passed, 1 skipped`
- frontend build: passed
- npm audit during `npm ci`: `0 vulnerabilities`

## Current task

Complete only PR0 — Frozen Fork.

Current PR0 scope:

- preserve and document the verified source baseline;
- establish FamilyFoodOS canonical product documents;
- establish the root FamilyFoodOS `AGENTS.md`;
- replace legacy execution-state files with FamilyFoodOS state;
- verify the resulting documentation/governance diff;
- commit and open the PR.

## Canonical documents for this task

Read:

- `AGENTS.md`
- `docs/family-food/project-operating-manual.md`
- `docs/family-food/technical-spec.md`
- `docs/family-food/data-ingestion.md`
- `docs/family-food/migration-plan.md`
- `docs/migration-source.md`

## Non-goals

PR0 must not:

- change backend runtime behavior;
- change frontend runtime behavior;
- change database schema;
- rename runtime packages or environment variables;
- begin food-domain model implementation;
- remove legacy CosmeticWorkshopOS bounded contexts;
- add AI;
- add retailer integrations;
- add PostgreSQL/Auth;
- begin PR1 Identity Detox.

Legacy application code is intentionally still present after PR0.

## Next allowed milestone

After PR0 is reviewed and merged, the next planned milestone is:

`PR1 — Identity Detox`

Do not begin PR1 work from this branch.
