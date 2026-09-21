# Current focus

Updated: `2026-09-21`.

## Accepted state

PR79 is merged into `main` at `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6`.

The accepted Russian-data integration sequence remains:

`partial profile storage → registry/adapters → transactional publication → first
Russian food batch → Russian reference table → persisted methodology selection →
transformation applicability → recipe-dependency food batch → executable Russian
recipes → Planner integration`.

Steps 1–3 are accepted. Current bounded work is **Step 4A — Implementation
Contract Gate for the first Russian source-native food batch**.

## Current authorization

This branch is docs/state only.

It may:

- freeze the exact five-record batch scope;
- freeze FoodIngredient identity decisions;
- freeze explicit ATOMIC versions;
- freeze V2 nutrient mappings and expected row counts;
- define batch-level atomic/replay/conflict/rollback semantics;
- freeze the transaction-neutral bundle-operation + one-UoW batch orchestration seam;
- record the source-authority gate and public-repository coupling;
- define adversarial acceptance for the later data/runtime PR.

It must not publish source numeric values or change runtime/schema/data seeds.

Canonical contract:
`docs/family-food/first-russian-food-batch-contract.md`.

## Preflight result

Technical publication plumbing is available from merged Step 3.

Candidate batch:

- `10.1.1 → SUGAR`;
- `8.1.5.1 → CARROT`;
- `8.1.2.1 → CABBAGE_GREEN`;
- `8.1.5.12 → BEET`;
- `6.5.3 → new RICE_POLISHED_DRY`.

Expected V2 positive rows: `4 + 8 + 8 + 8 + 9 = 37`, with all 60 reviewed
source cells retained and 15 below-detection cells remaining nonnumeric.

No migration is expected. Step 4 does require a bounded application refactor:
the existing committing single-bundle publisher remains public/unchanged, while a
transaction-neutral bundle operation is reused by a new five-bundle batch service
that owns one UoW and one commit.

## Blocking gate

Step 4 runtime/data publication is **PENDING REVIEW OF THE USER'S REPORTED PERMISSION**.

Accepted repository evidence remains `BLOCKED_PENDING_RIGHTS_REVIEW` because it
predates the user's 2026-09-21 statement that they possess permission.

Before implementation, that permission must be reviewed. A repository authority
receipt must confirm its exact scope for machine extraction, retention, commercial
calculation and public derived-data distribution, or record any narrower limits.
If the permission does not cover the current public-repository publication model,
a separate data-distribution architecture decision is required.

## Stop boundary

After this Contract Gate is review-ready/merged, stop.

Do not start the Step 4 numeric publication PR until source authority is explicitly
cleared. Do not start Step 5 target tables, methodology persistence,
transformations, recipes, Planner, Gate1, Shopping, API/UI or AI automatically.
