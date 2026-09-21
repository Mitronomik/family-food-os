# Current focus

Updated: `2026-09-21`.

## Accepted state

PR78 is merged into `main` at `e5466121e4958cf4fb95ba9041d1c7926daab17e`.

The accepted Russian-data integration sequence remains:

`partial profile storage → registry/adapters → transactional publication → first
Russian food batch → Russian reference table → persisted methodology selection →
transformation applicability → recipe-dependency food batch → executable Russian
recipes → Planner integration`.

Steps 1 and 2 plus the Step 3 Implementation Contract Gate are accepted.

Current authorized bounded work is **Step 3B — transactional reviewed nutrition
publication runtime implementation** under
`docs/family-food/transactional-nutrition-publication-contract.md`.

## Runtime scope

Implement exactly one reusable deterministic publication path:

`FoodIngredient → non-current FoodNutritionProfile + immutable source observations
→ RU_NUTRIENT_REGISTRY_V2 NutrientVector → ATOMIC FoodCompositionVersion`.

Required seams:

- specialized profile writer that never invokes historical V1 auto-bootstrap;
- registry-version-aware source-neutral V2 provenance decoder using
  `FFO_NUTRIENT_VALUE_EVIDENCE_V2`;
- V1 persisted provenance/decoder behavior remains unchanged;
- one existing project UoW owns the whole fresh transaction;
- nutrient values first, seal last, then ATOMIC composition;
- explicit V2 registry and explicit composition version;
- exact replay performs zero writes and preserves stable IDs;
- conflicting or partially present bundle fails closed;
- rollback/failure-injection coverage at every write boundary;
- Step 3 profiles remain `is_current=false`;
- legacy `CompositionCalculator` remains V1-pinned.

## Architecture constraints

- no schema change and no new migration; if implementation requires one, STOP for
  a separate architecture decision;
- no generic `bootstrap_v1=false` switch on catalogue profile operations;
- no hidden source-method inference;
- no invented source/FDC identifiers;
- no repair/adoption of partial historical bundles;
- deterministic core must pass with `AI_ENABLED=false`.

## Acceptance

The implementation PR must satisfy every adversarial test and verification tier
in the merged Step 3 contract, including fresh complete/partial publication,
source-neutral V2 round-trip, methodology read, V1 preservation, exact replay,
conflict cases, rollback injection, foreign-key integrity, full backend and full
launcher regression.

## Stop boundary

After Step 3 runtime implementation is review-ready, stop for final review and
explicit merge authorization.

Do not start Step 4 production Russian food publication, source-rights approval,
target tables, persisted methodology selection, transformation applicability,
recipes, Planner, Gate1, Shopping, API/UI or AI work automatically.
