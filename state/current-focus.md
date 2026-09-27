# Current focus

Updated: 2026-09-27.

## Accepted state

PR101 / R1-A is merged into `main` at:

`eb803cda82ce8073443981867291716a0eb0f0ad`.

R1-A result accepted into main:

- 7 selected R1 recipes;
- 20 unique food/form/Nutrition dependencies;
- 11 exact FIC publications;
- 7 accepted reuses;
- 2 explicit blockers;
- 5 recipes dependency-ready for R1-B.

Dependency-ready:

- `USSR82-453 — Яйца вареные`;
- `USSR82-467 — Омлет (натуральный)`;
- `USSR82-492 — Сырники из творога`;
- `USSR82-1081 — Блины`, variant III — с маслом;
- `USSR82-697` exact chicken/main branch without garnish/sauce.

Still blocked:

- `USSR82-364` on `ING-0014 / Жир кулинарный`;
- `USSR82-208` on `ING-0038 / Огурцы соленые`.

## Current bounded operation

**R1-B SOURCE OUTPUT IMPLEMENTATION CONTRACT GATE — AUTHORIZED / ACTIVE.**

Issue:

`#102 — R1-B Gate: persist source recipe output before RecipeVersion publication`.

Branch:

`docs/r1b-source-output-contract`.

Canonical gate document:

`docs/family-food/r1b-source-output-contract.md`.

## Why this gate is active

R1-B source review confirmed exact source outputs:

- USSR82-453: 40 g;
- USSR82-467: 110 g;
- USSR82-492: 170 g;
- USSR82-1081: 160 g;
- USSR82-697 selected chicken/main branch: 75 g.

Current immutable `RecipeVersion` has no structured source-output/yield field.

Hiding output mass in RecipeStep/change_note is prohibited because output mass is
critical recipe/portion truth.

Adding persisted RecipeVersion output truth changes schema/immutable replay
semantics, therefore repository AGENTS.md requires a docs-only Implementation
Contract Gate before runtime implementation.

## Gate decision under review

Minimal additive RecipeVersion truth:

```text
source_output_g: Decimal | None
source_output_text: str | None
```

Important boundaries:

- exact source output only;
- no inferred output from ingredient sum;
- no automatic output/input yield coefficient;
- no implicit transformation/retention publication;
- no Recipe Nutrition rescaling;
- historical RecipeVersions remain null;
- Step10 Nutrition remains input-Composition authoritative;
- Planner/Serving does not consume output in this gate/R1-B by default.

Expected migration after gate approval:

`0040_recipe_version_source_output`.

## Source audit result

For all five selected recipes the retained v22.13 coverage evidence reports:

- 100% relationship resolution;
- 100% input-mass coverage;
- one selected variant block;
- one ready output scenario;
- zero proxy rows;
- `READY_RAW`.

The retained legacy extraction rows remain
`UNVERIFIED_LEGACY_EXTRACTION / ready_for_integration=false`.

R1-B runtime must build a new reviewed hash-pinned publication package rather than
promoting legacy extraction status.

## Stop boundary

This branch/PR is docs/state only.

Do not start:

- migration 0040;
- RecipeVersion schema/runtime changes;
- R1-B RecipeVersion publication;
- Recipe activation;
- #100 Planner energy-allocation implementation;
- R1-C;
- Shopping/PR9;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After this Contract Gate is reviewed and merged, R1-B runtime requires separate
explicit authorization.
