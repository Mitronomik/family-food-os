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

## Frozen batch after independent review corrections

Exactly 10 School2022 MAIN cards remain selected:

- `54-1р`, `54-2р`, `54-3р`;
- `54-10р`, `54-11р`;
- `54-4м`, `54-6м`, `54-7м`, `54-8м`, `54-11м`.

New identity-only FoodIngredients are exactly:

- `COD_FILLET_RAW`;
- `PARSLEY_ROOT_RAW`;
- `WHEAT_BREAD_STALE_UNSPECIFIED_GRADE`.

No NutritionProfile or Composition authority is granted.

## Review corrections

The user explicitly selected transaction **option B**.

Future runtime remains one PR for the whole batch:

1. publish each inactive RecipeVersion + prepared authority atomically per recipe;
2. partial exact **inactive** publication is allowed after a failure;
3. rerun is zero-write for exact rows and converges missing rows;
4. publication never activates recipes;
5. activation starts only after all 10 exact publications pass full-batch preflight;
6. all-inactive activation uses one batch-level caller-owned UoW and one commit;
7. all-active activation is zero-write replay;
8. mixed active/inactive activation fails closed;
9. any activation failure rolls back the whole activation UoW.

No extra recipe PRs or activation PR are required.

Process-placement audit is frozen in:

`data/curation/r3a-school2022-main-batch/process-binding-review.json`.

`54-9р` and `54-18м` were removed because both have multiple quantified fats
while sunflower-oil placement is unresolved in technology. They were replaced
inside the same batch by source-clean `54-6м` and `54-7м`.

Single-fat same-card binding is allowed only when exactly one cooking fat exists
and technology has an otherwise unqualified fat-consuming operation. Exact total
grams remain authoritative; any internal per-step split remains UNKNOWN.

## Source boundary

Durable archive was independently re-materialized and re-hashed on 2026-10-03:

- Library file id: `libfile_26d95a7a50108191944b97db85a5c008`;
- ZIP size: 206692075 bytes;
- ZIP SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- embedded School2022 PDF size: 4102547 bytes;
- PDF SHA-256:
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Both match pinned authority receipts.

## Scope boundaries

Do not:

- publish/activate R3-A runtime data before this gate merges;
- add migration 0043 or schema changes;
- change Planner mapping/scoring/repetition;
- add a new Nutrition authority;
- add Nutrition/Composition to new identities;
- resolve process/source ambiguity by inference outside the frozen binding rule;
- split the ten recipes into separate PRs;
- start DC4/Gate1-CLOSE/PR9;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

After review corrections verify green, stop for independent review.


## Corrected gate verification

Corrected content freeze:

`39c1f3e8809e9fd42e6ea061554f81cf3b1c35e6`.

Exact-head evidence:

- 10 unique selected School2022 MAIN cards — PASS;
- candidate/spec/household/process-binding/source-page sets align — PASS;
- exactly 3 identity-only FoodIngredients — PASS;
- `54-5м/54-9р/54-12м/54-15м/54-18м` absent from selected set — PASS;
- `54-6м/54-7м` clean replacements present — PASS;
- process-binding disposition exists for all 10 selected cards — PASS;
- no per-step gram split invented — PASS;
- option-B publication semantics frozen — PASS;
- batch activation semantics frozen: all-inactive one-UoW, all-active replay,
  mixed fail-closed — PASS;
- fresh 2026-10-03 durable archive + embedded PDF readback/hash — PASS;
- ENERGY_KCAL-only + 53 UNKNOWN nutrient partition — PASS;
- Docs #851 — SUCCESS;
- DC1 #708 — SUCCESS.

Only state files change after this corrected content freeze. Runtime remains
blocked until independent review and merge of PR #146.
