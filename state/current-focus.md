# Current focus

Updated: 2026-10-03.

## Accepted state

PR #142 / R2-F runtime is merged into `main` at:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

DATA-CORPUS-V1 / DC3 remains active. The project has intentionally moved from
single-recipe micro-publication to enlarged reviewable recipe batches.

## Current bounded operation

**R3-A — School2022 ten-recipe MAIN batch Contract Gate.**

Issue: `#144`.

Branch:

`docs/r3a-school2022-main-batch-gate`.

Accepted base:

`da6d1e05fd44ecc2733e1a6f472eae3e54b60604`.

Status:

`READY_FOR_FINAL_REVIEW`.

Canonical contract:

`docs/family-food/r3a-school2022-main-batch-gate.md`.

## Frozen batch after final review corrections

Exactly 10 School2022 MAIN cards remain selected:

- `54-1р`, `54-2р`, `54-3р`;
- `54-10р`, `54-11р`;
- `54-4м`, `54-6м`, `54-7м`, `54-8м`, `54-11м`.

New identity-only FoodIngredients are exactly:

- `COD_FILLET_RAW`;
- `PARSLEY_ROOT_RAW`;
- `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE`.

No NutritionProfile or Composition authority is granted.

## Transaction decision — option B

The future runtime remains one PR for the whole batch:

1. publish each inactive RecipeVersion + prepared authority atomically per recipe;
2. a publication failure may leave only an exact inactive subset;
3. rerun is zero-write for exact rows and converges missing rows;
4. activation starts only after all ten exact publications pass full-batch preflight;
5. all inactive -> activate all ten in one caller-owned UoW / one commit;
6. all active -> zero-write replay;
7. mixed active/inactive -> fail closed;
8. any pre-commit activation failure rolls back the whole activation UoW.

The existing single-recipe prepared-activation path owns an inner commit, so it
must not be looped ten times. The same runtime PR is authorized to extract/add a
transaction-neutral activation-policy + in-scope mutation seam, with all fallible
batch admission validation completed before the single commit. Existing
single-recipe behavior must remain regression-safe. No extra activation PR is
required.

## Final independent-review source corrections

- `54-8м`: the source does not identify the liquid used to pre-soak stale bread.
  `WATER=12 g` remains exact at recipe level; explicit water placement is rack
  wetting; any other placement and per-step gram split stay UNKNOWN.
- `54-11м`: consumer steps retain the source-backed 5–10 minute weak boil and
  covered 160 °C / 30–40 minute oven finish. `WATER=313 g` remains exact without
  an invented per-step split.
- stale `SOUR_CREAM_15` / flour dependency wording is removed from the final
  selected-batch inventory.
- `54-9р` and `54-18м` remain rejected for unresolved multiple-fat placement;
  source-clean `54-6м` and `54-7м` remain their replacements.

## Source boundary

Durable archive independently re-materialized/re-hashed on 2026-10-03:

- Library file id: `libfile_26d95a7a50108191944b97db85a5c008`;
- ZIP size: 206692075 bytes;
- ZIP SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- embedded School2022 PDF size: 4102547 bytes;
- PDF SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Both match pinned authority receipts.

## Scope boundaries

Do not:

- publish/activate R3-A runtime data before this gate merges;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- add Nutrition/Composition to new identities;
- split the ten recipes into separate PRs;
- create a separate activation PR;
- start DC4/Gate1-CLOSE/PR9;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## Review-correction verification

Corrected content freeze:

`6ee960e979666e939ec7bed87bca1f70f3ed1ae4`.

Local/read-only audit on that content:

- selected/spec/household/process/source sets align 10/10 — PASS;
- exactly 3 identity-only FoodIngredients — PASS;
- old `54-8м` water-soak inference removed — PASS;
- old `54-11м` `частью воды` inference removed — PASS;
- source-backed 54-11м timing/temperature restored — PASS;
- transaction-neutral batch activation seam frozen — PASS;
- ENERGY_KCAL-only + 53 UNKNOWN partition preserved — PASS;
- durable ZIP/PDF size + SHA-256 readback — PASS.

Verification head `ff245c517c00b3c83716916cc5350b6478cf01b4`: Docs #858 SUCCESS; DC1 #715 SUCCESS. Final status-only state commits must remain byte-identical for docs/data content and receive exact-head Docs/DC1 before merge.

Status:

`READY_FOR_FINAL_REVIEW`.

Runtime remains blocked until PR #146 is independently re-reviewed and merged.
