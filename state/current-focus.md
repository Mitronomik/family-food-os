# Current focus

Updated: `2026-09-21`.

## Accepted state

PR77 is merged into `main` at `5343734e620c9f36d24aad54320c2196588b004d`.

Accepted Russian-data integration sequence:

`partial profile storage → registry/adapters → transactional publication → first
Russian food batch → Russian reference table → persisted methodology selection →
transformation applicability → recipe-dependency food batch → executable Russian
recipes → Planner integration`.

Steps 1 and 2 are accepted. The user approved the new pre-implementation process.
Current bounded work is **Step 3A — Implementation Contract Gate for transactional
profile/vector/ATOMIC publication**.

## Current authorization

This branch is docs/state/instructions only.

It may:

- inventory Step 3 dependencies and hidden coupling;
- freeze fresh/replay/conflict/rollback semantics;
- freeze the preservation matrix and adversarial test plan;
- record the no-new-migration decision;
- update AGENTS so future high-coupling work uses the same contract-gate process.

It must not implement the runtime publisher or publish production nutrition data.

Canonical Step 3 contract:
`docs/family-food/transactional-nutrition-publication-contract.md`.

## Preflight decisions

- no new migration is required by the accepted schema; if implementation disproves
  this, stop for a separate architecture decision;
- generic complete-profile insertion keeps its historical V1 auto-bootstrap;
- Step 3 must use a specialized profile publication writer that does not create a
  V1 seal;
- Step 3 profiles are non-current, including complete profiles;
- V2 registry identity is explicit and fixed to `RU_NUTRIENT_REGISTRY_V2`;
- ATOMIC composition version is explicit input, never silently auto-incremented;
- one existing project UoW owns the whole fresh write;
- exact replay is zero-write; conflicting or partial pre-existing state fails closed.

## Acceptance

The contract gate is review-ready when docs/state/AGENTS agree on:

- dependency inventory;
- preservation matrix;
- fresh/replay/conflict/rollback behavior;
- source/provenance boundaries;
- no-schema-change assumption;
- adversarial implementation tests;
- exact final verification tier.

## Stop boundary

After this docs-only gate is reviewed/merged, stop for runtime Step 3
implementation authorization under the frozen contract.

Do not start Step 4 food publication, source-rights approval, target tables,
methodology selection, transformation applicability, recipes, Planner, Gate1,
Shopping, API/UI or AI work automatically.
