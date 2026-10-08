# DC4-A3 post-correction focused evidence

**Status:** PASS
**Scope:** post-A3 focused DC4 Layer-A / Russian-readiness verification
**Full DC4 rerun:** NO
**Runtime freeze SHA:** `0aa949c7989f70658c2633e4792371c251bfcd7f`
**Workflow:** `DC4-A3 Russian RecipeStep corrections` run `37762618205`, job `113262471748`
**Uploaded artifact:** `dc4-a3-post-correction-evidence-0aa949c7989f70658c2633e4792371c251bfcd7f` (artifact `11543480822`)
**Committed machine receipt:** `data/curation/dc4-a3-russian-step-corrections/evidence.json`

## FACT — focused post-correction result

The focused audit reuses `scripts/audit_dc4_corpus_readiness.py::_audit_active_catalogue`
after publishing the exact A3 correction set.

Observed on the runtime-freeze evidence database:

- active production catalogue: **51**;
- Layer-A blocked rows: **0**;
- `RUSSIAN_STEPS_NOT_READY`: **0**;
- all seven prior Russian-step blockers cleared: **true**;
- runtime successor IDs match the current audited RecipeVersions: **true**;
- Planner exact-energy supply: **51 = 17 breakfast / 33 main / 1 sandwich**;
- Planner algorithm version: **planner-v0.5**.

This is a focused post-correction receipt. It does not replace the later full DC4 rerun.

## Exact-run RecipeVersion identity receipt

The UUIDs below identify the exact SQLite evidence instance from run `37762618205`.
They are intentionally runtime-instance-specific and are not a cross-database
identity contract. The committed JSON also contains, for every row, the full
old/new RecipeStep arrays, source name/id/version/document hash, rights basis,
output mass and expected prepared ENERGY_KCAL.

| Recipe | predecessor RecipeVersion | successor RecipeVersion | audited current RecipeVersion |
| --- | --- | --- | --- |
| `SCHOOL2022_54_1R_COD_CUTLET` | `aeec4e4a-b25f-486c-9be7-c18c0f71d5f9` | `0d44b2b9-8204-4236-825f-8d5e60affb81` | `0d44b2b9-8204-4236-825f-8d5e60affb81` |
| `SCHOOL2022_54_2R_PINK_SALMON_CUTLET` | `0ef519fe-202d-44d3-b28a-019fcd16d5ea` | `61d2f9cc-5c89-48e4-9739-5d7b96260f85` | `61d2f9cc-5c89-48e4-9739-5d7b96260f85` |
| `SCHOOL2022_54_3R_POLLOCK_CUTLET` | `ca57f0e1-09e3-4a73-b67d-5e7994c6c85d` | `4afaf701-5a51-4aaf-b119-0e9b23db7cf5` | `4afaf701-5a51-4aaf-b119-0e9b23db7cf5` |
| `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` | `43e1caac-d674-4e7b-a88e-e81acb7a2e4c` | `a3890816-28f2-477d-9c97-04f6d60281fe` | `a3890816-28f2-477d-9c97-04f6d60281fe` |
| `SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES` | `8ac74eab-ffb1-441e-8d61-faec9d536b80` | `37d9796b-d4d8-4835-84bd-2955e8aafeff` | `37d9796b-d4d8-4835-84bd-2955e8aafeff` |
| `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS` | `eeb19e6c-b21d-45c7-b79f-4a428d2f00c0` | `154157d1-2d3f-436e-8558-eb33ff03ecc8` | `154157d1-2d3f-436e-8558-eb33ff03ecc8` |
| `SCHOOL2022_54_11M_BEEF_PILAF` | `745d2046-ef0b-444e-b937-509ee557ec83` | `cee0a953-13b3-4294-8565-10bee5dc89f3` | `cee0a953-13b3-4294-8565-10bee5dc89f3` |

## Durable source/provenance boundary

The authoritative correction contract remains:

`data/curation/dc4-a3-russian-step-corrections/corrections.json`

The exact-run receipt binds those frozen corrections to the runtime predecessor
and successor RecipeVersion IDs observed in the evidence run. It does not make
UUIDs stable across independently seeded databases.

The uploaded CI artifact additionally preserves the generated JSON and Markdown
from the exact runtime-freeze execution. Its ZIP SHA-256 is
`3d674cd04fc5fde92cfba4fab6b625e54c8edc6b824799a10eb7a5057ddcf9b2`.

## Explicitly not run here

- the three full DC4 Gate1 fixtures;
- bounded milk+egg infeasibility;
- full DC4 overall blocker/status recomputation;
- Gate1-CLOSE.

Those remain the scope of the **separate DC4 rerun after A3 is reviewed and
merged**.

## Delivery semantics

This report and the state synchronization are delivery/evidence-only changes
after runtime freeze `0aa949c7989f70658c2633e4792371c251bfcd7f`. They do not change A3 runtime bytes.
