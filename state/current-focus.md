# Current focus

Updated: 2026-09-27.

## Accepted base

PR98 is merged into `main` at:

`9f72f6883e092cbf79930c7ac4a5a1314c7488d8`.

PR98 restored dependency-driven DATA-CORPUS-V1 sequencing and required one
explicit bounded operation before production work.

## Current bounded operation

**R1-A — Planner-capacity dependency closure is REVIEW-READY / NOT MERGED.**

Parent issue:

`#99 — R1: restore Steps 7–10 product meaning with Planner-capacity recipe batch`.

PR:

`#101 — R1-A: close Planner-capacity recipe dependencies`.

Verified runtime/data head:

`c92a19bdc4f3760bb50f2957068682d62ac126cf`.

## R1-A result

R1-A reconciles the selected seven recipes against current late-state authority,
not against historical DC1 flags alone.

Exact dependency result:

- 7 selected recipes;
- 32 source relationship rows;
- 20 unique dependencies;
- 7 accepted late-state reuses;
- 11 exact R1-A FIC publications;
- 2 explicit blockers;
- 5 recipes dependency-ready for R1-B;
- 2 recipes remain blocked.

### Dependency-ready for R1-B

- `USSR82-453 — Яйца вареные`
- `USSR82-467 — Омлет (натуральный)`
- `USSR82-492 — Сырники из творога`
- `USSR82-1081 — Блины`
- `USSR82-697` — exact chicken/main branch only

### Still blocked

- `USSR82-364 — Шницель из капусты`
  - blocker: `ING-0014 / Жир кулинарный`;
  - no exact accepted authority; pork fat/shortening substitution is forbidden.
- `USSR82-208 — Рассольник ленинградский`
  - blocker: `ING-0038 / Огурцы соленые`;
  - exact FIC record exists but has retained source-layout anomaly;
  - no silent repair/reinterpretation.

## R1-A publications

Nine exact FIC authorities are published through the existing Step 3/Step 4
transactional path:

- `MARGARINE_MILK_TABLE`
- `MILK_PASTEURIZED_3_2`
- `SOUR_CREAM_30`
- `TVOROG_9`
- `YEAST_BAKERS_COMPRESSED`
- `CHICKEN_CATEGORY_1_RAW`
- `POTATO` — reuse existing identity with exact FIC profile/ATOMIC authority
- `ONION_BULB_FRESH`
- `FLOUR_WHEAT_HIGH_GRADE`
- `WATER` — existing identity, exact FIC profile + ATOMIC v2
- `SALT` — existing identity, exact FIC profile + ATOMIC v2

Each uses the frozen Step 4B mapping:

- 18 canonical V2 values;
- 26 retained source observations;
- 198 V2 values total;
- 286 source observations total.

Existing current profiles are preserved. New exact-form FIC profiles remain
non-current.

The FIC nutrient snapshot is not treated as allergen-label authority. R1-A makes
no automatic allergen claims; explicit ingredient exclusions remain authoritative.

## Source authority

Durable source:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Verified on 2026-09-27:

- size `206692075`;
- archive SHA-256
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- embedded RU-NUT-DB HTML SHA-256
  `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`;
- all 11 published source code/name/raw-substring hashes independently rechecked.

No production numeric value was reconstructed from LLM output, OCR or web snippets.

## Verification

On exact runtime/data head `c92a19bdc4f3760bb50f2957068682d62ac126cf`:

- Docs #458 — SUCCESS;
- DC1 #320 — SUCCESS;
- Russian #193 — SUCCESS;
- Nutrient Registry V2 #339 — SUCCESS;
  - focused SUCCESS;
  - all 4 backend regression shards SUCCESS;
  - launcher SUCCESS;
- Partial Nutrition Profiles #251 — SUCCESS;
  - focused SUCCESS;
  - all 4 backend regression shards SUCCESS;
  - launcher SUCCESS.

A date-sensitive historical Step 9 test defect was fixed by deriving the activation
timestamp from the persisted recipe timestamp; production Step 9 behavior was not
changed.

Planner-capacity energy authority is now closed for all five ready recipes. WATER
and SALT use source-published FIC `ENERGY_KCAL=0.0`; historical V2 unknowns were
not coerced to zero.

## Stop boundary

R1-A is review-ready, not complete until merged.

Do not start automatically:

- R1-B RecipeVersion/process publication;
- #100 Planner energy-allocation implementation;
- R1-C Planner product proof;
- Gate1-CLOSE;
- PR9 Shopping;
- Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After R1-A merge, stop and obtain explicit authorization for R1-B.
