# R1-G — Catalogue-capacity expansion evidence and contract gate

**Status:** ACTIVE — docs/data evidence only
**Issue:** #120
**Accepted base:** `879d68087845dea09454089e822f5d8d8238d12d` (merged PR #119)
**Runtime authority seam:** `PREPARED_OUTPUT_V1 / RECIPE_PREPARED_OUTPUT_NUTRITION_V1`

## 1. Purpose

PR #119 proved a reusable, source-backed prepared-output Recipe Nutrition path
for one breakfast and one main Recipe. R1-G decides the next catalogue-capacity
batch without weakening source truth.

This gate must determine:

1. whether USSR82-1081 can truthfully reuse the prepared-output seam;
2. whether exact source evidence closes the missing salt quantities for
   USSR82-467 and USSR82-492;
3. which additional MAIN candidates are the shortest evidence-backed route toward
   R1-C Planner feasibility;
4. the exact next runtime/data batch.

R1-G does not publish or activate any Recipe.

## 2. Authority hierarchy

Use current repository truth in this order:

1. explicit later user decisions;
2. `AGENTS.md`;
3. canonical `docs/family-food/*`;
4. accepted R1-E / R1-B / R1-F evidence packages;
5. retained private source artifacts only after independent hash/source verification.

External datasets are evidence artifacts, not FamilyFoodOS domain identity.

## 3. FACT — accepted base

PR #119 merged into `main` at:

`879d68087845dea09454089e822f5d8d8238d12d`.

It proved:

- immutable `PREPARED_OUTPUT_V1` RecipeVersion authority;
- sparse reviewed values with explicit UNKNOWN for unreviewed nutrients;
- exact positive prepared ENERGY_KCAL as Planner readiness input;
- guarded activation after exact authority + Planner admission;
- ordinary authoritative Planner loading through the normal application boundary.

The new seam does not authorize raw→cooked inference, retention assumptions,
source scaling or arbitrary prepared recipe publication.

## 4. FACT — USSR82-1081 / Блины

Accepted R1-B / R1-E evidence currently establishes:

- source identity: `USSR82-1081`;
- selected variant: `III — с маслом`;
- source output: 160 g;
- seven quantified required rows:
  - WATER — 118 g;
  - MARGARINE_MILK_TABLE — 5 g;
  - BUTTER_UNSALTED — 10 g;
  - FLOUR_WHEAT_HIGH_GRADE — 75 g;
  - SUGAR — 3 g;
  - SALT — 1.5 g;
  - YEAST_BAKERS_COMPRESSED — 3 g;
- prior R1-E blockers include consumed-Nutrition authority and Recipe publication;
- the former V2 Composition blocker was mode-dependent.

Current retained raw/reference nutrition readiness is not prepared-output
authority. A raw/input sum, output/input ratio or retained workbook READY_RAW
status must not be promoted to exact cooked ENERGY_KCAL.

### Required R1-G decision

1081 may be marked `PREPARED_OUTPUT_READY` only if an exact durable source
receipt proves consumed/prepared ENERGY_KCAL for the exact selected 160 g output,
with compatible source identity, version/hash and reviewed rights scope.

Otherwise it remains blocked with an explicit evidence reason.

If ready, the future runtime batch must reuse the existing R1-F authority kind and
calculation version; no new Nutrition authority model is authorized.

## 5. FACT — USSR82-467 / Омлет (натуральный)

Accepted evidence establishes:

- selected source variant: `selected_1982_variant`;
- source output: 110 g;
- quantified rows:
  - MARGARINE_MILK_TABLE — 5 g;
  - BUTTER_UNSALTED — 5 g;
  - MILK_PASTEURIZED_3_2 — 30 g;
  - EGG — 80 g;
- the verified source process requires salt;
- retained quantified rows contain no exact salt mass.

Current blocker:

`REQUIRED_QUANTITY_UNRESOLVED / UNQUANTIFIED_PROCESS_INGREDIENT_SALT`.

R1-G must not invent a pinch/default/zero-mass salt row and must not drop salt
because its energy contribution is zero.

Allowed dispositions:

- exact salt quantity proven and pinned;
- an already-approved canonical quantity/process representation is proven
  applicable by exact source semantics;
- remain blocked.

A new quantity semantic requires a separate explicit decision/gate.

## 6. FACT — USSR82-492 / Сырники из творога

Accepted evidence establishes:

- selected variant: `1-й вариант, со сметаной`;
- source output: 170 g;
- quantified rows:
  - MARGARINE_MILK_TABLE — 5 g;
  - FLOUR_WHEAT_HIGH_GRADE — 20 g;
  - SUGAR — 15 g;
  - SOUR_CREAM_30 — 20 g;
  - TVOROG_9 — 135 g;
  - EGG — 5 g;
- the verified source process requires salt;
- retained quantified rows contain no exact salt mass.

The same no-inference rules as 467 apply.

## 7. FACT — current MAIN evidence

The accepted R1-E blocker map assigns explicit MAIN capacity roles only to:

- USSR82-697;
- USSR82-364;
- USSR82-208.

PR #119 delivered a new source-neutral active main Recipe,
`BOILED_CHICKEN_MAIN_PRODUCT`, using exact 1988 prepared-output authority while
preserving historical USSR82-697 inactive.

USSR82-364 and USSR82-208 still carry source-structure / food-identity publication
blockers under the accepted R1-E evidence.

Therefore R1-G must not automatically select 364/208 merely because they were the
old R1 set. It must rank the currently allowed cross-corpus universe using current
evidence closure and ordinary household role semantics.

## 8. R1-C capacity rule

The current Planner hard repetition default is three uses per RecipeVersion.

That fact alone does not justify hardcoding a fixed number of additional breakfast
or main Recipes: R1-C explicitly requires materially different repository-backed
meal patterns, and the concrete opportunity schedule determines required role
capacity.

R1-G must calculate capacity against the actual proposed R1-C fixture/scenarios
and report:

- active eligible RecipeVersions by role before the future runtime batch;
- projected counts after the batch;
- maximum feasible role occurrences under the unchanged repetition limit;
- whether at least one required R1-C repository-backed week becomes feasible;
- any remaining bounded infeasibility.

No Planner algorithm or repetition-limit change is authorized.

## 9. Evidence tasks

### 9.1 1081 prepared-output receipt

- independently retrieve/verify the exact source artifact;
- pin source identity/variant/output;
- verify source hash and rights;
- determine whether exact source prepared ENERGY_KCAL exists for the exact output;
- distinguish source-declared cooked value from calculated raw/reference values;
- record UNKNOWN for every unreviewed nutrient.

### 9.2 467 / 492 salt closure

For each recipe:

- inspect primary/durable source material;
- determine whether an exact salt quantity exists;
- retain exact source wording and artifact/hash;
- fail closed if the quantity remains absent.

### 9.3 MAIN shortlist

Audit the allowed cross-corpus candidate universe.

Rank candidates by:

1. supported standalone MAIN semantics;
2. ordinary household applicability;
3. exact source variant/required quantities;
4. existing FoodIngredient/form closure;
5. source-backed output/process evidence;
6. shortest exact consumed-Nutrition authority route;
7. reuse of the proven prepared-output seam without new schema/runtime;
8. marginal R1-C capacity value.

Source family preference is not a ranking criterion.

## 9.4 Current research findings

### 9.4.1 Durable source archive

The project-owned private corpus archive was independently retrieved during R1-G:

- locator: `private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`;
- size: `206692075` bytes;
- SHA-256: `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

The retained School2022 source PDF inside that archive was also independently
verified:

- path: `corpus-work/packages/school2022/raw/source.pdf`;
- size: `4102547` bytes;
- SHA-256: `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

### 9.4.2 467 / 492

No exact source salt quantity has been proven.

Their current dispositions are therefore:

- USSR82-467 → `BLOCKED_REQUIRED_QUANTITY_UNRESOLVED`;
- USSR82-492 → `BLOCKED_REQUIRED_QUANTITY_UNRESOLVED`.

The R1-G gate does not authorize a default/pinch/zero/omitted salt value.

### 9.4.3 1081

The retained III-with-butter source branch remains exact at 160 g output.

A separate normative menu table was discovered with recipe 1081, butter,
`150/10` output and 370 kcal. That row is useful corroboration but is **not yet
prepared-output authority for the selected III branch** because recipe 1081 has
materially different I/II/III ingredient columns and the discovered nutrient row
does not itself pin the source column/variant.

Current disposition:

`BLOCKED_PREPARED_ENERGY_VARIANT_LINKAGE_UNPROVEN`.

No value from that external table may be attached to the selected III RecipeVersion
until the exact column/variant linkage and durable source receipt are pinned.

### 9.4.4 Historical MAIN candidates

USSR82-208 is not a clean `PREPARED_OUTPUT_V1` candidate under the current V1
contract: the retained source Recipe basis is 1000 g while the discovered prepared
nutrient row is 250 g. Using it would require source scaling, which R1-F V1
explicitly forbids.

USSR82-364 is more promising:

- accepted R1-E role: MAIN;
- 1982 column III output with a 5 g serving-fat branch is 150/5;
- a normative nutrient table contains recipe 364 at 150/5 and 252 kcal;
- the nutrient row labels the serving-fat branch as margarine;
- the existing retained R1-B selection used the III butter branch.

Therefore 364 is **not yet runtime-ready**, but it is a strong exact-output
candidate if R1-G pins the III+margarine source branch and a durable nutrient
receipt. The remaining accepted mode-independent ingredient blocker is exact
`Жир кулинарный` identity/form truth.

### 9.4.5 School2022 MAIN shortlist

The verified private archive contains exact same-card output and source-published
energy for many material/procurement-ready non-clinical cards.

Current leading MAIN candidates are recorded in:

`data/curation/r1g-catalogue-capacity-expansion/school2022-main-shortlist.json`.

Top candidates:

1. `ru-school2022:recipe:54-29м` — Фрикадельки из говядины — 80 g — 153 kcal;
2. `ru-school2022:recipe:54-2м` — Гуляш из говядины — 80 g — 185.6 kcal;
3. `ru-school2022:recipe:54-1р` — Котлета рыбная (треска) — 100 g — 112.6 kcal.

However accepted R1-E truth explicitly stops 264 unpublished School2022 identities
at `HOUSEHOLD_APPLICABILITY`. Retained process evidence also contains
`institutional_school_catering_only / domestic_applicability=unestablished`
markers.

Therefore exact output+kcal **does not** make these Recipes runtime-ready.

A bounded per-recipe household-applicability decision/review is required before a
School2022 candidate can enter the next runtime batch. R1-G must not silently
generalize one School2022 review to all 264 blocked identities.

### 9.4.6 Current runtime-batch conclusion

At this research checkpoint, **no additional Recipe is yet authorized for runtime
publication/activation**.

This is intentional fail-closed behavior. The next runtime batch remains empty
until at least one candidate simultaneously closes:

- exact source Recipe/variant/process/output identity;
- required FoodIngredient/form identities;
- household applicability;
- exact prepared-output Nutrition authority;
- role suitability and ordinary Planner prerequisites.

## 10. Required evidence package

Path:

`data/curation/r1g-catalogue-capacity-expansion/`

Required outputs before review-ready:

- `candidate-dispositions.json`;
- durable receipt references/hashes/rights;
- 1081 prepared-output disposition;
- 467 salt disposition;
- 492 salt disposition;
- reviewed MAIN shortlist + selection;
- projected Planner capacity;
- exact next runtime batch;
- explicit unresolved blockers.

## 11. Frozen architecture constraints

- `AI_ENABLED=false`;
- no new migration;
- no new authority kind or calculation version;
- no raw→cooked inference;
- no implicit retention;
- no source scaling;
- UNKNOWN != zero;
- source output/portion mass does not become Recipe identity;
- production RecipeVersion truth remains immutable and provenance-backed;
- existing R1-F guarded activation remains the only prepared activation path;
- no Planner scoring/role/repetition changes.

If evidence requires a new persisted identity, quantity semantic, process model,
authority kind, migration or cross-context contract, stop and request a separate
Implementation Contract Gate decision.

## 12. Non-goals

R1-G does not authorize:

- Recipe/RecipeVersion publication;
- activation;
- migration 0043;
- Food/Nutrition publication unrelated to the selected batch;
- retention/transformation runtime;
- R1-C execution;
- Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- R2/R3.

## 13. Verification

Use the data-curation + docs/state verification tiers.

Required before review-ready:

- source existence/retrieval checks;
- artifact size/hash verification;
- rights/use classification;
- exact recipe/variant/output checks;
- exact required ingredient quantity/form checks;
- explicit rejection of READY_RAW/input calculations as prepared-output authority;
- deterministic candidate shortlist generation or reproducible selection evidence;
- R1-C role/repetition capacity calculation;
- no runtime/schema diff;
- docs verification and state consistency.

## 14. Exit criteria

R1-G is review-ready only when:

1. 1081 is either exact prepared-output ready or explicitly blocked;
2. 467 has exact salt closure or remains explicitly blocked;
3. 492 has exact salt closure or remains explicitly blocked;
4. a reviewed minimal MAIN batch is selected from current evidence;
5. every proposed runtime target has all mode-independent publication facts and
   exact consumed-Nutrition authority proven;
6. projected R1-C capacity is calculated without changing Planner rules;
7. the exact next runtime/data batch is frozen;
8. no runtime/schema changes are present.

## 15. Follow-up

After this gate is reviewed and merged, create one bounded runtime/data PR for
only the targets authorized by this document and its evidence package.

Do not start that runtime PR automatically.
