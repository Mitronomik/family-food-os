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

## Current research checkpoint

No additional Recipe is runtime-authorized yet.

- 467 / 492 remain blocked on exact salt quantity;
- 1081 has a strong 150/10 / 370 kcal external candidate but exact linkage to
  the selected III branch is unproven;
- 208 would require forbidden prepared-value/source-row scaling under R1-F V1;
- 364 is the strongest retained USSR82 MAIN candidate: III output 150/5 aligns
  with a 252 kcal normative row, but exact III+margarine branch receipt and
  `Жир кулинарный` identity/form truth remain to close;
- School2022 has exact same-card output+kcal candidates, but accepted R1-E truth
  stops unpublished cards at `HOUSEHOLD_APPLICABILITY`.

Leading School2022 MAIN shortlist:

- 54-29м — Фрикадельки из говядины — 80 g / 153 kcal;
- 54-2м — Гуляш из говядины — 80 g / 185.6 kcal;
- 54-1р — Котлета рыбная (треска) — 100 g / 112.6 kcal.

These are shortlist evidence, not publication authority.

## Next step

Resolve the R1-G remaining decision/evidence boundary:

1. pin the exact 364 III+margarine prepared receipt + culinary-fat identity route;
2. determine whether a bounded per-recipe School2022 household-applicability review
   is authorized/adequately evidenced for the shortlisted candidates;
3. freeze only then the exact next runtime batch and projected R1-C capacity.

Do not start the runtime follow-up until this gate is reviewed and merged.
