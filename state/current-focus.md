# Current focus

Updated: `2026-09-01`

## Project

FamilyFoodOS is a separate product bootstrapped from the verified engineering baseline of CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

## Completed lifecycle

`PR0 — Frozen Fork — COMPLETE`

`PR1 — Identity Detox — COMPLETE`

PR1 separated active FamilyFoodOS project, runtime, launcher, frontend and agent
identity from CosmeticWorkshopOS while preserving inherited runtime behavior.
Accepted source provenance, historical evidence, explicitly classified legacy
documentation and negative/legacy tests remain intentionally present.

## Next authorized task

`PR2-A — FamilyFoodOS Architecture & Persistence Contract`

PR2-A is a documentation and architecture contract that must be reviewed before
production food-domain implementation begins. It defines the seams and ownership
boundaries for later PR2 implementation; it does not create food entities,
migrations, APIs or frontend behavior.

PR2-A must define at minimum:

- FamilyFoodOS bounded contexts;
- dependency direction: `UI → API → services/domain → repositories → persistence`;
- repository interfaces that keep domain services independent of database technology;
- SQLite as the MVP/local persistence implementation;
- an explicit future SQLite → PostgreSQL seam;
- transaction and unit-of-work boundaries;
- the household ownership boundary;
- separation of canonical `FoodIngredient` from `RetailSKU`;
- deterministic Nutrition, Planner and Shopping boundaries;
- the `MealPlan → Serving` pipeline;
- Pantry and Prep boundaries;
- recipe provenance requirements;
- optional AI with a deterministic core that works under `AI_ENABLED=false`;
- retailer connectors only after the generic Shopping Engine.

## PR2-A boundary

Do not implement Household or other production food-domain code in PR2-A. Do
not migrate to PostgreSQL, add AI, build retailer parsers/connectors, or start
the consumer PWA. Production food-domain implementation begins only after the
architecture and persistence contract has been reviewed.
