# Current focus

Updated: 2026-10-01.

## Accepted state

PR #119 / R1-F prepared-output Nutrition runtime is merged into `main` at:

`879d68087845dea09454089e822f5d8d8238d12d`.

R1-F proved the reusable authority seam:

- `PREPARED_OUTPUT_V1`;
- `RECIPE_PREPARED_OUTPUT_NUTRITION_V1`;
- exact reviewed AVAILABLE/UNKNOWN partition;
- guarded prepared Recipe activation;
- ordinary authoritative Planner loading.

## Current bounded operation

**R1-G — catalogue-capacity expansion evidence and contract gate.**

Issue:

`#120`.

Branch:

`docs/r1g-catalogue-capacity-expansion-gate`.

Accepted base:

`879d68087845dea09454089e822f5d8d8238d12d`.

This operation is docs/data evidence only.

## Goal

Freeze the exact next runtime batch after R1-F by answering:

1. whether USSR82-1081 has exact prepared-output source authority for its selected
   160 g output;
2. whether exact source evidence closes the missing salt quantities for USSR82-467
   and USSR82-492;
3. which additional MAIN candidates are the shortest truthful route toward R1-C;
4. what projected Planner role capacity the next runtime batch would create.

## Current evidence state

### USSR82-1081 — Блины

Known:

- variant `III — с маслом`;
- output 160 g;
- seven quantified required ingredient rows;
- prior consumed-Nutrition blocker.

Current disposition:

`PREPARED_OUTPUT_RECEIPT_RESEARCH_REQUIRED`.

READY_RAW/input-reference calculations are not accepted as cooked prepared-output
authority.

### USSR82-467 — Омлет (натуральный)

Known blocker:

`REQUIRED_QUANTITY_UNRESOLVED / UNQUANTIFIED_PROCESS_INGREDIENT_SALT`.

No salt quantity may be inferred, defaulted or omitted.

### USSR82-492 — Сырники из творога

Same exact salt-quantity blocker as 467.

### MAIN capacity

R1-E's explicit MAIN set was USSR82-697 / 364 / 208.

- capacity for the former 697 path is now supplied by the separate active
  `BOILED_CHICKEN_MAIN_PRODUCT` from R1-F;
- 364 and 208 still have source-structure / food-identity blockers;
- R1-G must rank the current cross-corpus universe rather than automatically reuse
  those historical candidates.

## Architecture / scope boundaries

Do not:

- publish or activate Recipes;
- add migration 0043;
- change schema;
- add a new Nutrition authority kind/calculation version;
- infer raw→cooked Nutrition;
- infer retention;
- infer missing salt;
- treat READY_RAW as prepared-output authority;
- change Planner scoring/roles/repetition limits;
- execute R1-C;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3.

If evidence requires a new persisted identity/quantity/process/authority contract,
stop and request a separate Implementation Contract Gate decision.

## Durable outputs

- `docs/family-food/r1g-catalogue-capacity-expansion-gate.md`;
- `data/curation/r1g-catalogue-capacity-expansion/*`;
- exact source/hash/rights receipts;
- final dispositions for 1081 / 467 / 492;
- reviewed MAIN shortlist and selection;
- projected R1-C capacity;
- exact next runtime batch.

## Next step

Complete the R1-G evidence research and candidate ranking.

Do not start the runtime follow-up until this gate is reviewed and merged.
