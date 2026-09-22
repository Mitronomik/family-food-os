# Current focus

Updated: `2026-09-22`.

## Accepted state

PR79 is merged into `main` at
`0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6`.

Steps 1–3 of the Russian-data integration sequence are accepted.

Current bounded work is **Step 4A — corrected Implementation Contract Gate for
the first licensed Russian electronic-database batch**.

Canonical contract:
`docs/family-food/first-russian-food-batch-contract.md`.

Authority receipt:
`docs/family-food/fic-nutrition-license-receipt.md`.

## Source decision

The project owner supplied both:

- a signed 2026-09-10 FIC license covering the electronic database
  «Химический состав пищевых продуктов, используемых в Российской Федерации»;
- `FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`.

The corpus proves the five Step 4 candidates exist in the official
`RU-NUT-DB` snapshot from `ion.ru`.

**RU-NUT-DB is now the production numeric authority for Step 4.**

Book2002 remains historical/corroborating evidence only.

## Exact first-batch source rows

- `1150 /DB/252` — Сахар-песок → `SUGAR`;
- `1187 /DB/126` — Морковь свежая красная → new `CARROT_RED_RAW`;
- `1184 /DB/69` — Капуста белокочанная свежая → `CABBAGE_GREEN`;
- `1204 /DB/254` — Свекла свежая → `BEET`;
- `66 /DB/103` — Крупа рисовая → new `RICE_GROATS`.

Do not attach the red-only carrot source row to generic `CARROT`.
Do not reuse `RICE_WHITE` or the earlier Book2002-derived
`RICE_POLISHED_DRY`.

## Current blocker

Source rights are no longer the blocker.

The remaining Step 4 gate is **source-semantic mapping**.

The corpus confirms per-100-g edible basis and units for `kcal/prot/fat/carbh`,
but explicitly leaves:

- the `carbh` nutrient definition unresolved;
- hidden DB field unit/definition binding unresolved;
- numeric-zero scientific semantics unresolved.

Only positive `kcal/prot/fat` values are currently safe canonical mappings
(13 values across the five records).

Because a Step 3 vector seal is immutable, do not prematurely publish that sparse
13-row projection. First freeze the final intended mapping set for this snapshot.

## Architecture

Step 4 still requires:

- no schema/migration;
- all new Russian profiles non-current;
- existing USDA current profiles preserved, including generic `CARROT`;
- transaction-neutral one-bundle operation;
- one five-food batch UoW / one commit;
- exact replay zero-write;
- whole-batch rollback on one-food failure.

## Stop boundary

PR80 may merge as the corrected gate.

After merge, do not start numeric publication automatically. The next bounded
task is Step 4 source-semantic mapping closure for these five licensed RU-NUT-DB
records. Runtime publication begins only after that mapping set is reviewed.
