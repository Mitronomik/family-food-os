# Current focus

Updated: 2026-09-27.

## Accepted state

PR98 is merged into `main` at:

`9f72f6883e092cbf79930c7ac4a5a1314c7488d8`.

PR98 restored dependency-driven DATA-CORPUS-V1 sequencing and explicitly required
selection of one concrete bounded operation before production work.

The accepted technical path from Steps 1–10 remains:

```text
partial nutrition profiles
→ versioned nutrient registry/adapters
→ transactional Food profile/V2/ATOMIC publication
→ accepted Russian food/reference data
→ persisted methodology
→ transformation applicability infrastructure
→ exact RecipeVersion V2 Nutrition
→ planner-v0.3 / MealPlan / Serving consumption
```

The Step 9 School2022 butter Recipe remains inactive and is a technical vertical
slice, not the completed product meaning of Steps 7–10.

## Current bounded operation

**R1-A — Planner-capacity dependency closure is AUTHORIZED / ACTIVE.**

Parent issue:

`#99 — R1: restore Steps 7–10 product meaning with Planner-capacity recipe batch`.

Branch:

`data/r1a-planner-capacity-dependencies`.

Accepted R1 recipe set:

### Breakfast

- `USSR82-453 — Яйца вареные`
- `USSR82-467 — Омлет (натуральный)`
- `USSR82-492 — Сырники из творога`
- `USSR82-1081 — Блины`

### Main

- `USSR82-697 — Птица, дичь или кролик отварные с гарниром`
  - only an exact source-supported chicken/main branch may be selected;
  - garnish/sauce boundary remains explicit.
- `USSR82-364 — Шницель из капусты`
- `USSR82-208 — Рассольник ленинградский`

## R1-A goal

Close and publish only the FoodIngredient/form/Nutrition dependencies directly
required by the selected seven recipes, using existing accepted Steps 3–10
publication paths.

Expected new/form dependency review set:

- `ING-0030 — Маргарин молочный`;
- `ING-0034 — Молоко пастеризованное 3,2%`;
- `ING-0047 — Сметана 30%`;
- `ING-0056 — Творог полужирный`;
- `ING-0097 — Дрожжи прессованные`;
- `ING-0025 — Куры I категории`;
- `ING-0014 — Жир кулинарный`;
- `ING-0053 — exact breadcrumbs/breading form`;
- `ING-0024 — exact rice-groats form`;
- `ING-0038 — exact pickled-cucumber form`.

Existing mappings/profiles are reused only after exact recipe-form suitability is
confirmed; an old DC1 review flag is not itself reason to republish authority.

## R1-A acceptance

- exact recipe→ingredient dependency manifest for all seven selected recipes;
- exact identity/form decision for every required dependency;
- exact authority/provenance/rights for each published new/form food;
- V2 vector + ATOMIC publication where required by the current architecture;
- no invented unknowns/zeros or raw↔cooked equivalence;
- idempotent fresh/replay/conflict/rollback behavior;
- no unrelated FoodIngredient expansion;
- exact accepted/blocked disposition for every dependency;
- no RecipeVersion publication in R1-A.

If R1-A discovers a genuinely new/changed authoritative publication path,
immutable authority contract, schema/migration boundary or cross-context rule,
stop for the repository-required docs-only Implementation Contract Gate before
runtime implementation.

## Next sequenced operations

After accepted R1-A:

1. **R1-B** — use existing corpus source/process truth to publish the R1
   RecipeVersions that pass all checks and activate only household-suitable ones.
2. **#100 Planner energy allocation** — correct partial-at-home / mixed-source
   Serving allocation before production Planner proof.
3. **R1-C** — production Planner proof on ordinary active R1 recipes with
   repository-backed household scenarios and individualized Servings.

No R1-B or R1-C work starts automatically from this authorization.

## Hard boundaries

Not part of R1-A:

- RecipeVersion publication or activation;
- Planner/MealPlan algorithm changes;
- energy-allocation fix (#100);
- Shopping / PR9;
- Prep / Freezer;
- Retail;
- API/UI;
- Auth/PostgreSQL;
- generalized ingestion;
- AI authority;
- bulk corpus publication.

Issue #67 remains open; DATA-CORPUS-V1 baseline is not complete.
