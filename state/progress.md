Warning: truncated output (original token count: 39083)
Total output lines: 3221

# Progress

## R1-B PR104 review verification — 2026-09-27

Migration 0040, immutable RecipeVersion source output and exact replay are in
PR104. Five candidate dispositions are recorded: one chicken/main RecipeVersion
published inactive, four blocked for explicit source or V2 Composition reasons.
The package pins source workbook hashes, v20 card/instruction rows and DC1
relationship row identities. Deterministic V2 validation uses input Composition
and does not activate Planner consumption or infer yield/retention.

Local focused source-output/publication tests passed (19), migration and legacy
receipt regression passed (216), and launcher regression passed (645). Exact-head
CI remains the review-ready gate.

## R1-B runtime started — 2026-09-27

Accepted main:
`fb89cfeb84f4052233f82daa7dcc2d1c07aa971a`.

Status:
`R1B_RUNTIME_ACTIVE`.

Authorized:
- migration 0040;
- RecipeVersion source output fields;
- exactly five reviewed R1-B RecipeVersions;
- exact Composition bindings and V2 Nutrition validation.

No #100 / R1-C / Shopping / API/UI work started.

## R1-B source-output contract gate started — 2026-09-27

Accepted main:
`eb803cda82ce8073443981867291716a0eb0f0ad` (merged PR101).

Status:
`R1B_SOURCE_OUTPUT_CONTRACT_GATE_ACTIVE`.

Source audit for five R1-B recipes confirms:
- exact ingredient mass coverage;
- source-backed Russian instructions;
- exact outputs: 40 / 110 / 170 / 160 / 75 g;
- one selected source scenario per recipe;
- no proxy rows.

Architecture gap:
current RecipeVersion cannot persist structured source output/yield.

Current work:
docs-only contract for minimal immutable source-output fields and migration
preservation rules.

No migration, runtime, RecipeVersion publication, Planner change or next milestone
has started.

## R1-A Planner-energy closure verified — 2026-09-27

Verified runtime/data head:
`c92a19bdc4f3760bb50f2957068682d62ac126cf`.

Final dependency result:
- 20 unique dependencies;
- 11 exact FIC publications;
- 7 accepted late-state reuses;
- 2 blockers;
- 5 recipes dependency-ready for R1-B;
- WATER/SALT exact source-published zero-energy authority added via ATOMIC v2;
- 198 canonical V2 values;
- 286 retained source observations.

Verification:
Docs #458, DC1 #320, Russian #193, Registry #339, Partial #251 — SUCCESS.
All focused suites, backend shards and launchers are green.

Status:
`R1A_REVIEW_READY`.

## R1-A review-ready — 2026-09-27

Accepted base:
`9f72f6883e092cbf79930c7ac4a5a1314c7488d8`.

Verified runtime/data head:
`1f5cc62876a6985eb0d07f119de9b3ccaf9e35d9`.

Delivered:
- exact 20-dependency manifest for the selected 7-recipe R1 batch;
- 9 exact FIC authority publications;
- 9 accepted late-state reuses;
- 2 explicit blockers;
- 162 canonical V2 values;
- 234 retained source observations;
- one-UoW fresh publication, zero-write replay, conflict/rollback/tamper tests;
- no silent generic-form substitution;
- existing current profiles preserved;
- explicit allergen authority limitation;
- 5 recipes dependency-ready for R1-B.

Verification:
Docs #446, DC1 #308, Russian #181, Registry #317, Partial #239 — SUCCESS.
Registry focused: 400 passed.
All broad backend shards and launcher regressions are green.

Status:
`R1A_REVIEW_READY`.

No RecipeVersion, Planner, Shopping, Prep, Retail, API/UI or AI work started.

## R1-A started — 2026-09-27

Accepted base:
`9f72f6883e092cbf79930c7ac4a5a1314c7488d8`.

Status:
`R1A_DEPENDENCY_CLOSURE_ACTIVE`.

Selected batch:
7 recipes / 4 breakfast-target candidates / 3 main-target candidates.

Expected new/form dependency review set:
10 external identities.

No RecipeVersion, Planner, Shopping or UI changes have started.



## Post-PR96 sequencing corrected — 2026-09-26

Accepted main:
`7443f56b856184db6ddb040b9d68425db9f8d41a`.

PR97:
`SUPERSEDED_CLOSED_UNMERGED`.

Correction result:
- no regression to DC1-era preflight state;
- accepted DATA-CORPUS-V1 contract/source foundation remains accepted;
- the DATA-CORPUS-V1 baseline remains incomplete and Issue #67 stays active;
- Steps 4–10 remain the later controlling implementation history;
- dependency-driven DC2/DC3 publication sequencing is restored;
- DC3 may not bypass unresolved required DC2 food/form/Nutrition dependencies;
- no specific next production batch is authorized by PR98;
- no per-recipe governance milestone is introduced by default;
- PR9 remains blocked until DC4 + Gate1-CLOSE.

Status:
`POST_PR96_DC23_SEQUENCE_RESTORED`.

No production data/runtime changes occurred in this correction.


Next step after merge:
select and explicitly authorize one concrete bounded DC2 or DC3 operation under
Issue #67; implementation does not start automatically.

## PR96 Step 10-B review-ready — 2026-09-26

Verified runtime/test head:
`8b38053697845c7c63936a6b462e98331f5bb7e1`.

Step 10-B is implemented and fully verified:
- planner-v0.3;
- neutral V2/legacy candidate Nutrition;
- exact-energy readiness semantics;
- neutral MealPlan/Serving consumption;
- unknown-carbohydrate propagation;
- fully V2-bound cross-context application proof.

Review:
`#5327127307 READY TO MERGE`.

Verification:
- Docs #414 / DC1 #276 / Russian #163 / Registry #274 / Partial #207 — SUCCESS;
- focused 391 / 339 passed;
- backend 1074 / 804 / 776 / 968 passed;
- launcher 643 passed, 2 skipped;
- AI_ENABLED=false.

Status:
`STEP10B_RUNTIME_REVIEW_READY`.

No migration or production activation occurred.

## Step 10-B runtime active — 2026-09-26

Accepted base:
`1ef7d1ffd0896873034034b3eb629e62aa474803` (merged PR95).

Initial runtime implementation:
- planner-v0.3;
- exact-energy readiness seam;
- neutral Planner candidate Nutrition;
- neutral MealPlan/Serving consumption;
- legacy compatibility defaults;
- cross-context synthetic proof;
- verification workflow routing.

Status:
`STEP10B_RUNTIME_VERIFICATION_PENDING`.

No migration, activation or Step 11 work occurred.

## PR95 Step 10-A review-ready — 2026-09-26

Verified runtime head:
`3c779c7a0184be6f6838720b6fde78dbe482e8e8`.

Step 10-A is implemented and fully verified:
- 0039 immutable RecipeIngredient composition authority binding;
- exact Step 9 production binding;
- canonical 54-code Recipe V2 Nutrition;
- neutral legacy/V2 projection;
- exact legacy carbohydrate crosswalk;
- replay/rollback/immutability/race protections.

Runtime review:
`#5326633449 READY TO MERGE`.

Verification:
- Docs #404 / DC1 #266 / Russian #153 / Registry #257 / Partial #197 — SUCCESS;
- focused 352 / 300 passed;
- backend 1073 / 836 / 753 / 956 passed;
- launcher 643 passed, 2 skipped;
- AI_ENABLED=false.

Status:
`STEP10A_RUNTIME_REVIEW_READY`.

No Step 10-B work occurred.

## Step 10-A runtime active — 2026-09-26

Accepted base:
4f9331a8fa73f8488a07295076b0425c00e6654e (merged PR94).

Runtime branch and draft PR95 created.

Implemented:
- 0039 RecipeIngredient composition binding persistence;
- immutable binding guards;
- Nutrition-owned read/write scope;
- canonical V2 RecipeVersion Nutrition;
- neutral consumption projection;
- exact Step 9 binding publisher;
- focused acceptance tests.

Status:
STEP10A_RUNTIME_VERIFICATION_PENDING.

No Step 10-B work occurred.

 PR94 final compatibility correction review-ready — 2026-09-26

Semantic head:
5e2d9a9336a94798327e3a9445e0dffd41e05ff9.

Closed review #5326205581:
legacy NutritionValues.carbohydrates_g now maps exactly and only from
CARBOHYDRATE_BY_DIFFERENCE under RECIPE_COMPOSITION_NUTRITION_V1.

Forbidden:
- CARBOHYDRATE_AVAILABLE fallback;
- STARCH+SUGARS synthesis.

Step 9 legacy projection remains INCOMPLETE.

Review #5326221930: READY TO MERGE.

Verification:
Docs #375 / DC1 #237 SUCCESS.
Registry focused 328.
Partial focused 276.

Status:
STEP10_CONTRACT_GATE_FINAL_CORRECTED_REVIEW_READY.

No runtime/schema/production data mutation occurred.

## PR94 final compatibility blocker corrected — 2026-09-26

Review #5326205581 blocked the gate on an unfrozen legacy carbohydrate crosswalk.

Correction:
`NutritionValues.carbohydrates_g` now maps exactly and only from
`CARBOHYDRATE_BY_DIFFERENCE` under
`RECIPE_COMPOSITION_NUTRITION_V1`.

AVAILABLE carbohydrate and STARCH+SUGARS are explicitly forbidden fallbacks.

Status:
STEP10_CONTRACT_GATE_FINAL_COMPATIBILITY_CORRECTION_VERIFICATION_PENDING.

No runtime/schema/production data changed.

## PR94 deep-corrected Contract Gate review-ready — 2026-09-26

Corrected semantic head:
560cce41e1c1ce54212052bd95dfc8fe4b0cdb13.

Closed deep-review blockers from #5326074689:
1. exact canonical V2 request-set identity;
2. separate recipe-level calculation/version policy;
3. exact durable Planner version identity.

Additional bounded closures:
- gram-only Recipe V1 mass authority;
- optional/transformed roots fail closed in V1;
- historical read vs mutable active-state boundary;
- replay created_at preservation;
- SQL REPLACE immutability.

Corrected semantic review:
#5326161326 READY TO MERGE.

Verification:
Docs #373 / DC1 #235 SUCCESS.
Registry focused 328 passed.
Partial focused 276 passed.
54/54 request-set comparison PASS.

Status:
STEP10_CONTRACT_GATE_DEEP_CORRECTED_REVIEW_READY.

No runtime/schema/production data mutation occurred.

## PR94 deep semantic blockers corrected — 2026-09-26

Review #5326074689 blocked the gate on:
- missing canonical V2 request-set identity;
- missing separate recipe-level calculation version;
- non-exact Planner version identity.

Corrections:
- exact RECIPE_V2_NUTRIENT_SET_V1 / 54-code request set;
- exact RECIPE_COMPOSITION_NUTRITION_V1 recipe formula;
- exact FOOD_COMPOSITION_APPLICABILITY_V2 lower-level formula;
- exact planner-v0.3 for Step 10-B;
- historical read / mutable active-state boundary frozen.

Status:
STEP10_CONTRACT_GATE_DEEP_CORRECTION_VERIFICATION_PENDING.

No runtime/schema/production data changed.

## PR94 corrected Contract Gate review-ready — 2026-09-26

Corrected semantic head:
c23bca0e6df4787f8f083a976fd6257e454d1777.

Closed blockers from review #5325781916:
1. binding owner / UoW;
2. in-UoW active dependency validation for fresh and replay;
3. exact immutable calculation-policy identity.

Corrected semantic review:
#5325809090 READY TO MERGE.

Verification:
Docs #368 / DC1 #230 SUCCESS.
Registry focused 328 passed.
Partial focused 276 passed.

Status:
STEP10_CONTRACT_GATE_CORRECTED_REVIEW_READY.

No runtime/schema/production data mutation occurred.

## PR94 Contract Gate blockers corrected — 2026-09-26

Review #5325781916 blocked the gate on ownership/UoW, transaction-time active
dependency validation and unfrozen calculation-policy identity.

All three are corrected in the canonical Step 10 contract:

- Nutrition owns the binding authority;
- one Nutrition-owned UoW owns dependency reads/classification/write;
- fresh and replay recheck active dependency inside that UoW;
- external preflight is non-authoritative;
- policy is exactly FOOD_COMPOSITION_APPLICABILITY_V2;
- returned CompositionResult.calculation_version must match the persisted policy.

Status:
STEP10_CONTRACT_GATE_CORRECTED_VERIFICATION_PENDING.

No runtime/schema/production data changed.

## PR94 Step 10 Contract Gate review-ready — 2026-09-26

Semantic head:
761871e36a5a019621eb0c8e7900b2dfcf5e2773.

The docs-only Step 10 gate is complete and reviewed.

It freezes:
- Step 10-A: migration 0039 + immutable Composition authority binding +
  canonical V2 Recipe Nutrition + neutral consumption projection;
- Step 10-B: Planner V2 readiness + planner version advance + MealPlan/Serving
  consumption, only after Step 10-A merge;
- no production Step 9 Recipe activation;
- no MealRole compatibility expansion;
- legacy Nutrition preservation;
- unknown WATER/carbohydrate preservation.

Verification:
Docs #366 / DC1 #228 SUCCESS.
Semantic review #5325759751 READY TO MERGE.

Status:
STEP10_CONTRACT_GATE_REVIEW_READY.

No runtime/schema/production data mutation occurred.

## PR93 merged / Step 10 gate opened — 2026-09-26

PR93 merged as:

d0a1a217d3e23b0b930f14de37405a7ca7ba3d16

Step 9 is accepted.

The next bounded operation is the docs-only Step 10 Recipe V2 Nutrition / Planner
Integration Contract Gate.

Preflight discovered a required immutable Composition authority seam: persisted
RecipeIngredient currently does not pin FoodCompositionVersion, so general
Nutrition must not infer latest/current Composition.

Status:

STEP10_CONTRACT_GATE_ACTIVE

No runtime/schema/activation work has occurred.

## PR93 corrected runtime verified — 2026-09-26

Runtime correction head:
`99f3d2b9ae592e9370a0f432316828da7a3b6cfb`.

Closed:
1. exact replay now fails closed when the required Step 8 FoodIngredient becomes
   inactive between external preflight and strict write-UoW reconcile;
2. a concurrent exact publication after external FRESH preflight now resolves as
   successful zero-write EXACT_REPLAY rather than a stale-disposition RuntimeError.

Verification on the corrected runtime:
- Docs #360 / DC1 #222 / Russian #123 / Registry #201 / Partial #152 — SUCCESS;
- focused 328 / 276 passed;
- backend 1202 / 751 / 650 / 991 passed;
- launcher 643 passed, 2 skipped;
- `AI_ENABLED=false`.

Status:
`STEP9_RUNTIME_CORRECTED_REVIEW_READY`.

No Step 10 work occurred.

## PR93 transaction/replay correction — 2026-09-26

The later independent exact-head review superseded the earlier READY TO MERGE
status with two blockers:
- inactive Step 8 dependency could pass an exact replay race;
- loader trusted stale external FRESH disposition after the write-UoW recheck.

Both are corrected in PR93 with two adversarial race tests. Default historical
`reconcile_seed()` behavior remains unchanged; the stricter dependency guard is
limited to trusted preflight / `strict_history=True`.

The prior runtime head
`31751069adec7ada062c8b4b7fcb291f4cd89bed` is no longer the current runtime
verification receipt after this code change.

Status:
`STEP9_RUNTIME_CORRECTED_VERIFICATION_PENDING`.

No Step 10 work occurred.

## PR93 Step 9 runtime-data review-ready — 2026-09-26

Verified runtime head:
`31751069adec7ada062c8b4b7fcb291f4cd89bed`.

Step 9 publication is implemented and verified:
- inactive Recipe;
- SOURCE_VERIFIED immutable v1;
- exact Step 8 10 g dependency;
- two material source-backed steps;
- institutional applicability preserved;
- 17-value deterministic V2 validation;
- exact replay zero-write;
- activation-preserving replay;
- strict in-UoW history recheck;
- rollback and Planner exclusion verified.

Verification:
Docs #358 / DC1 #220 / Russian #121 / Registry #198 / Partial #150 SUCCESS.
Semantic review #5325378822 READY TO MERGE.

Status:
`STEP9_RUNTIME_REVIEW_READY`.

No Step 10 work occurred.

## Step 9 runtime authorized — 2026-09-26

PR92 is merged into main at
`2c50782b17584a5708a946e497d6a628977420e9`.

The user explicitly authorized Step 9 runtime/data publication under the merged
corrected Contract Gate.

Status:
`STEP9_RUNTIME_ACTIVE`.

No Step 10 activation or Planner integration is authorized.

## PR92 corrected gate review-ready — 2026-09-26

Both blockers from review #5324872702 are closed.

Corrected semantic head:
`3f7a4276ca623c23b61cb344c75e3751f2f83f54`.

Frozen corrections:
- institutional-only holding/14 °C are source context, not domestic executable steps;
- exact process quarantine hash pinned;
- fresh Step 9 Recipe is inactive;
- default-preserving initial activation seam frozen;
- replay never mutates activation;
- current Planner candidate pool remains unchanged before Step 10.

Verification:
Docs #353 SUCCESS; DC1 #215 SUCCESS; corrected review #5324890694 READY TO MERGE.

Status:
`STEP9_CONTRACT_GATE_CORRECTED_REVIEW_READY`.

No runtime/schema/production RecipeVersion write occurred.

## PR92 blockers corrected — 2026-09-26

Review #5324872702 found:
1. institutional-only refrigerated-holding evidence was being promoted to a
   domestic RecipeStep;
2. active SOURCE_VERIFIED Recipe would enter current Planner enumeration before
   Step 10.

Corrected contract head:
`1c8dc51c889c50713f0027efe0d31a31a9f66f7b`.

Corrections:
- exact institutional process-evidence hash pinned;
- only material preparation facts become RecipeSteps;
- institutional holding/14 °C stay source context;
- home storage remains not granted;
- fresh Step 9 Recipe is inactive;
- additive initial-activation seam is frozen with default-preserving behavior;
- replay never mutates activation;
- Planner candidate pool stays unchanged before Step 10.

Status:
`STEP9_CONTRACT_GATE_CORRECTED_REVERIFYING`.

No runtime/schema/production RecipeVersion write occurred.

## PR92 Step 9 Contract Gate review-ready — 2026-09-26

Step 9 preflight is frozen in:
`docs/family-food/russian-recipe-version-publication-contract.md`.

Verified semantic head:
`b0b5f890ce850075ea91d43e54bc8f93a6497c0d`.

Outcome:
- exact School2022 source lineage and one-food execution route pinned;
- Recipe/RecipeVersion/ingredient/process fields frozen;
- canonical factual-publication rights boundary frozen;
- deterministic 10 g V2 Composition acceptance frozen;
- legacy current-profile Nutrition path explicitly excluded;
- strict replay/conflict semantics frozen;
- no migration/source-corpus/Planner expansion.

Verification:
Docs #350 SUCCESS; DC1 #212 SUCCESS; semantic review #5324830015 READY TO MERGE.

Status:
`STEP9_CONTRACT_GATE_REVIEW_READY`.

No runtime/schema/production RecipeVersion write occurred.

## Step 9 Contract Gate started — 2026-09-26

PR91 is merged at:
`88a22a3cdfdd13d5481875dcd499abf06939582c`.

Step 8 is accepted.

Step 9 preflight selected the same exact School2022 `53-19з` vertical slice and
confirmed:
- source material execution is one exact 10 g ingredient;
- Step 8 closes the required food/composition dependency;
- existing Recipe Catalogue persistence is sufficient without migration;
- canonical normative-recipe rights policy allows narrow factual publication;
- old v0.3 rights/carbohydrate blockers must be adjudicated explicitly;
- legacy current-profile NutritionService cannot be used for the non-current
  Step 8 profile;
- V2 Composition is the Step 9 deterministic calculation authority;
- Planner integration remains Step 10.

Status:
`STEP9_CONTRACT_GATE_ACTIVE`.

No runtime/schema/production RecipeVersion write has occurred.

## Step 8 runtime/data review-ready — 2026-09-25

Accepted base:
`76ca8f8ffba589576af4e0fad4d7a4817a84089f`.

PR91:
`feat/step8-recipe-dependency-butter-runtime`.

Verified runtime/test/workflow head:
`068847f4a3b886e6b8133558f2d4820a6a01474e`.

Status:
`STEP8_RUNTIME_REVIEW_READY`.

Delivered:
- one exact FIC-backed butter FoodIngredient;
- source-only no-added-salt form binding;
- explicit WATER unknown;
- 17-value V2 vector;
- non-current profile;
- ATOMIC v1 / INPUT;
- idempotent fresh/replay semantics;
- conflict and rollback protection;
- generic butter/history preserved;
- no transformation or RecipeVersion;
- no migration/schema change;
- CI focused paths explicitly include Step 4 + Step 8 suites.

Verification:
- Registry #180 SUCCESS: focused 310; shards 1205/798/614/959; launcher 643/2 skipped;
- Partial #139 SUCCESS: focused 258; shards 1205/798/614/959; launcher 643/2 skipped;
- Russian #116 SUCCESS;
- Docs #347 SUCCESS;
- DC1 #209 SUCCESS;
- AI_ENABLED=false;
- bounded patch audit clean.

Step 9 remains not started.

## Step 8 runtime authorized — 2026-09-25

PR90 is merged into main at
`76ca8f8ffba589576af4e0fad4d7a4817a84089f`.

The user explicitly authorized Step 8 runtime/data publication under the merged
Contract Gate.

Status:
`STEP8_RUNTIME_ACTIVE`.

Scope is exactly one FIC-backed butter bundle; no schema/migration/Step 9 work is
authorized.

## PR90 corrected Contract Gate review-ready — 2026-09-25

The unsalted-form blocker from review #5312850815 is closed in the canonical
Step 8 Contract Gate.

Corrected semantic head:
`f0b2fa24403589de8b6c16a20b3cc326772c0fbe`.

Frozen closure:
`FIC DB/533 salt_ad=0.0` is source-only form compatibility for no added salt;
it remains outside the V2 nutrient vector and cannot be inferred from sodium.

Adversarial acceptance now rejects non-zero/null/missing salt evidence.

Verification:
Docs #345 SUCCESS; DC1 #207 SUCCESS; corrected review #5314905510 READY TO MERGE.

Status:
`STEP8_CONTRACT_GATE_CORRECTED_REVIEW_READY`.

No runtime/schema/production data/Step 9 work occurred.

## PR90 blocker correction — 2026-09-25

Re-review #5312850815 identified an unsalted-form authority gap in the Step 8
Contract Gate.

The canonical contract now closes it with exact FIC DB/533 source evidence:

`salt_ad = 0.0` / source label `Добавленная соль`.

The evidence is source-only form compatibility for no added salt. It does not
become canonical V2 nutrition, does not imply zero sodium, and cannot be inferred
from sodium. Non-zero/null/missing salt evidence is an explicit publication
conflict.

No runtime/schema/production data changed.

Status:
`STEP8_CONTRACT_GATE_CORRECTED_REVERIFYING`.

## Step 8 Contract Gate review-ready — 2026-09-24

Accepted base:
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

PR90:
`docs/step8-recipe-dependency-food-batch-contract`.

Verified semantic head:
`49c291ab5e46a88e34a6f3ae897c32f4cccc6378`.

Status:
`STEP8_CONTRACT_GATE_REVIEW_READY`.

Frozen:

- exact Step 9 target School2022 53-19з;
- exact new butter identity;
- exact licensed FIC DB/533 authority;
- 17-value sparse V2 vector with WATER unknown;
- non-current profile + ATOMIC v1 / INPUT;
- zero transformation/applicability publication;
- no migration/schema;
- one-food bounded vertical-slice scope.

Verification:

- Docs #343 SUCCESS;
- DC1 #205 SUCCESS;
- semantic review #5303638521 READY TO MERGE;
- scope/whitespace clean;
- 0 behind main;
- unresolved threads 0.

No production Step 8 data, Step 9 RecipeVersion or Step 10 Planner work occurred.

## Step 8 Contract Gate started — 2026-09-24

PR89 is merged into main at
`8ae941a1f5c4f07177b2e80272e582f8690dd747`.

The user explicitly authorized continuing to the next bounded Russian-data
integration operation.

Under the repository Implementation Contract Gate rule, current work is
documentation/preflight only.

Preflight selected the minimum-risk vertical slice:

- Step 9 target source card: School2022 `53-19з`;
- dependency: exact unsalted 72.5% butter;
- new source-faithful FoodIngredient:
  `BUTTER_PEASANT_72_5_UNSALTED`;
- licensed FIC authority: code 1417 / DB/533;
- exact raw record SHA-256:
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- expected 17-value sparse V2 vector because source `water=null`;
- expected ATOMIC v1 / INPUT;
- no transformation/applicability and no schema migration.

The durable private corpus archive was independently retrieved and hash-verified.

Status:
`STEP8_CONTRACT_GATE_ACTIVE`.

No production Step 8 data or Step 9 RecipeVersion has been published.

## Step 7 runtime review-ready — 2026-09-24

Accepted base:
`71e4cfc63908440a54631e68b7507e94311980d2` (merged PR88).

PR89:
`feat/step7-transformation-applicability-runtime`.

Verified runtime/test/workflow head:
`e481b6cda42afa2f33e5239262dae3f3c6780797`.

Status:
`STEP7_RUNTIME_REVIEW_READY`.

Delivered:

- immutable TransformationApplicability dependent state;
- migration `0038_transformation_applicability`;
- explicit V2 registry-aware retention seams;
- applicability-aware V2 publication/calculation;
- exact food/season/evidence-scope enforcement;
- late-applicability and mixed-registry fail-closed behavior;
- same-UoW rollback proof;
- legacy V1 replay/snapshot semantics preserved;
- no production numeric source-loss publication.

Verification:

- Russian methodologies #113 SUCCESS;
- Registry V2 #169 focused: 280 passed;
- Partial #130 SUCCESS:
  - focused 228 passed;
  - backend shards 1252 / 768 / 582 / 962 passed;
  - launcher 643 passed, 2 skipped;
- Registry V2 launcher: 643 passed, 2 skipped;
- AI_ENABLED=false;
- bounded GitHub patch whitespace/conflict/scope audit clean.

Step 8+ remains not started.
PR89 is not merged; stop for review.

## Step 7 Contract Gate review-ready — 2026-09-24

Accepted base:
`6ec1069d867388e5d1f4782ce6cdeed08c017694`.

PR88:
`docs/step7-transformation-applicability-contract`.

Verified contract head:
`7068b4d7af9d0b8817e933daeaa89a08f68feb26`.

Status:
`STEP7_CONTRACT_GATE_REVIEW_READY`.

Delivered docs-only contract freezes:

- exact transformation applicability ownership;
- V1 historical replay preservation;
- explicit V2 retention registry seams;
- no V1→V2 factor relabelling;
- exact food/season/source scope;
- no late applicability;
- expected additive 0038 migration;
- synthetic-only initial runtime publication boundary;
- 33 adversarial runtime acceptance cases.

Verification:
- Docs #335 SUCCESS;
- DC1 #197 SUCCESS;
- semantic review #5299903757 READY TO MERGE.

No runtime/schema/data publication occurred.
Step 8+ remains not started.


## Step 7 Contract Gate started — 2026-09-24

PR87 / Step 6B is merged into main at
`6ec1069d867388e5d1f4782ce6cdeed08c017694`.

The user explicitly authorized Step 7 transformation applicability.

Under the repository Implementation Contract Gate rule, current work is
documentation/preflight only.

Preflight established:

- legacy Composition retention semantics are V1-pinned;
- 0035 already carries registry identity in retention rows;
- old retention snapshot hashes cannot safely absorb a new registry field;
- no implicit V1→V2 retention reuse is acceptable;
- exact applicability must include food, source/process scope and explicit season
  semantics;
- source corpus loss/retention rows remain non-production evidence.

Canonical gate created:
`docs/family-food/transformation-applicability-contract.md`.

Expected runtime migration after a separately accepted gate:
`0038_transformation_applicability`.

Current status:
`STEP7_CONTRACT_GATE_ACTIVE`.

No runtime/schema/numeric transformation publication is authorized yet.


## Step 6B runtime review-ready — 2026-09-23

PR87 verified runtime/test head:
`8853d2a09240d26997c83915bc4167ab39979323`.

Status:
`STEP6B_RUNTIME_REVIEW_READY`.

Delivered:

- MealPlan reference-methodology dependent pins;
- immutable member target-input snapshots;
- complete-or-zero coverage;
- Step 6A selection ownership validation;
- Russian applicability at week_start;
- SQLite member-state CAS guard;
- migration 0037;
- zero-backfill legacy compatibility;
- Planner default preservation.

Verification:
- Docs #331 SUCCESS;
- DC1 #193 SUCCESS;
- Russian #98: 380 passed;
- Registry #139: 257 focused, 4/4 backend shards, launcher 643/2 skipped;
- Partial #109: 228 focused, 4/4 backend shards, launcher 643/2 skipped.

Step 7+ remains not started and not authorized.


## Step 6B runtime authorized — 2026-09-23

PR86 merged into main at
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc`.

The user explicitly authorized the next bounded Step 6B runtime operation.

Current target:
`MealPlanMemberReferenceMethodologyPin` persistence with additive migration
`0037_meal_plan_reference_methodology_pins`.

Step 7+ remains not started.

Current status:
`STEP6B_RUNTIME_AUTHORIZED`.


## Step 6A runtime review-ready — 2026-09-23

PR86 runtime head:
`e03be7b0c4a9b7766a961026cdf8de7d1f56d8d8`.

Status:
`STEP6A_RUNTIME_REVIEW_READY`.

All independent re-review blockers are closed:

- SQLite cross-connection state revalidation now uses a real CAS/write-intent
  guard and has a real two-connection regression;
- no-op request-id semantics are explicitly consistent with zero-write behavior;
- durable state records final verification.

Runtime verification is fully green:
- Docs #314;
- DC1 #176;
- Russian #81: 358 passed;
- Registry #110: 257 focused, 4 backend shards, launcher 643/2 skipped;
- Partial #92: 228 focused, 4 backend shards, launcher 643/2 skipped.

Step 6B remains not started and not authorized.

# Progress

## Step 6A runtime authorized — 2026-09-23

PR85 merged into main at
`e38692f7839ecab2da9499dc968dd01638227046`.

The user explicitly authorized Step 6A runtime implementation.

Current target:
`MemberReferenceMethodologySelection` persistence with additive migration
`0036_member_reference_methodology_selection`.

Step 6B / migration 0037 remains not started.

Current status:
`STEP6A_RUNTIME_AUTHORIZED`.


## Step 6 PR85 blocker correction — 2026-09-23

Independent re-review found three Contract Gate blockers despite green CI.
All three are now corrected in the canonical Step 6 contract:

- runtime split into Step 6A / 0036 and Step 6B / 0037;
- source-native Russian food policy removed from member reference selection;
- exact retry uses persisted request identity rather than bundle equality.

The contract also preserves:

- NASEM personal baseline;
- optional additive Step 5 Russian group reference;
- no invented historical backfill;
- Household/member stale-read guards;
- `MealPlan.week_start` replay date in Step 6B;
- reserved 0033;
- no Planner/API/UI default switch.

Current status:
`STEP6_CONTRACT_GATE_REVERIFYING`.


## Step 6 Contract Gate drafted — 2026-09-23

Accepted base:
`3de3c58ee898284f8d2168af1aae04af754a6bfc`.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Preflight closed the main hidden couplings before runtime:

1. mutable HouseholdMember cannot own replayable methodology history;
2. methodology version alone cannot reproduce a historical NASEM target;
3. MealPlan must pin the exact methodology selection plus member calculation
   input snapshot;
4. Russian group reference remains additive to NASEM, not a replacement;
5. existing plans must not be backfilled with invented selection state;
6. additive 0036 is expected; reserved 0033 remains reserved.

Current status:
`STEP6_CONTRACT_GATE_REVIEW_PENDING`.

No runtime/schema implementation is included in this gate.


## Step 6 Contract Gate authorized — 2026-09-23

PR84 merged into `main` at
`3de3c58ee898284f8d2168af1aae04af754a6bfc`.

Russian-data integration Steps 1–5 are accepted.

The user explicitly authorized Step 6:
**persisted nutrition methodology selection**.

Current operation is the required pre-implementation Contract Gate only.
No migration/runtime implementation has started.

Preflight already proves that methodology version alone is insufficient for
historical planning replay because HouseholdMember nutrition inputs are mutable.
The gate will freeze an immutable/versioned member selection and MealPlan/member
pin + calculation-input snapshot boundary while preserving existing plans and
current Planner/NASEM behavior.

Current status:
`STEP6_CONTRACT_GATE_ACTIVE`.


## Step 5 Contract Gate merged; runtime authorized — 2026-09-23

PR83 merged into `main` at
`f12a3f58279eb07c710d1ff889cc70d933da3310`.

Accepted Contract Gate:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

The user explicitly authorized the next bounded operation: Step 5 runtime
publication of the reviewed Russian adult micronutrient group-reference table.

Frozen publication target remains:

- 48 rows;
- 24 canonical definitions × 2 sexes;
- tables 11/12 + 16/17;
- age 19+;
- KFA-independent;
- exact source Decimal values and provenance;
- pinned V2 definition/unit compatibility;
- no schema/migration;
- no Planner/API/UI default switch;
- no Step 6.

Current status:
`STEP5_RUNTIME_AUTHORIZED`.

## Step 5 contract gate authorized — 2026-09-22

PR82 Step 4C is merged at
`aa5ebcb4c70c9adee0fd1242f520ef1298f6b167`.

The user authorized the next roadmap item:
**reviewed Russian reference table**.

Contract/adversarial preflight established a bounded first publication shape:

- source `МР 2.3.1.0253-21`;
- population source transport already QA-checked in the supplied corpus;
- first production table will be adult scalar micronutrients only;
- tables 11/12 + 16/17;
- 24 canonical definitions × male/female = 48 rows;
- age 19+ from source `Старше 18 лет`;
- KFA-independent;
- no schema/migration expected;
- existing explicit Russian selector/provider boundary is reused;
- NASEM/default Planner behavior remains unchanged.

Current status:
`STEP5_CONTRACT_GATE_IN_REVIEW`.

No numeric reference-table publication has occurred in this gate.

## Step 4C runtime publication authorized — 2026-09-22

PR81 is merged at `be6eed3591752d38ece3de5892e4306134e8d762`.
The user explicitly authorized the next bounded Step 4 runtime publication.

Implementation target:
- exact five licensed RU-NUT-DB records;
- hash-pinned runtime payload and merged 18-field mapping;
- 90 V2 numeric values total;
- transaction-neutral one-bundle seam;
- one five-food UoW / one commit;
- exact replay zero-write;
- whole-batch rollback on conflict/failure;
- no migration/schema;
- current USDA truth preserved and new FIC profiles non-current.

Runtime verification is not yet recorded here; final readiness depends on the
delivery PR's exact-head focused and regression evidence.

# Progress

## Step 4B RU-NUT-DB semantic mapping closure — 2026-09-22

PR80 is merged at `f7ac885dde055900b3a6397aa64a15fe698abe5b`.

The licensed five-record source-semantic review is complete:

- 26 RU-NUT-DB fields reviewed;
- 18 numeric field mappings approved;
- 8 fields deliberately deferred/source-only;
- 130 source observations retained;
- 87 published numeric / 43 published zero;
- **90 V2 numeric candidate values — 18 per food**;
- published zero is preserved as numeric zero for approved fields with explicit
  source provenance.

The closure confirms PR80's no-migration expectation. Existing `VALUE`
observations represent source-supplied numeric literals including zero; they do
not claim independent analytical exactness.

Status:
`MAPPING_FROZEN_RUNTIME_READY`.

No runtime/schema/production numeric data is changed by this evidence operation.

## Step 4 licensed RU-NUT-DB authority reconciliation — 2026-09-22

The project owner supplied the signed FIC database license and
`FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`.

Verified from the archive:

- archive SHA-256:
  `c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`;
- official RU-NUT-DB raw HTML SHA-256:
  `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`;
- 3216 electronic database rows;
- exact Step 4 candidates at source codes 1150/1187/1184/1204/66;
- corpus identity evidence rejects DB126 as generic `CARROT`; user approved
  new source-faithful `CARROT_RED_RAW / Морковь свежая красная`;
- first batch identity shape is now 3 reuse + 2 create
  (`CARROT_RED_RAW`, `RICE_GROATS`);
- all five are identically corroborated across the second official FIC interface;
- RU-NUT-DB differs numerically from Book2002, so Book2002 is not Step 4
  production numeric truth.

License review clears the historical `rights_use_unresolved` blocker for this
electronic source under the supplied conditions. The exact §7.1 attribution text
and §7.2 repository-link requirement are frozen in the authority receipt.

Remaining blocker is canonical source-field semantics. Across the five rows the
source contains 130 nutrient observations: 87 published numeric and 43 published
zero. Current corpus evidence safely maps only positive kcal/protein/fat values,
13 canonical V2 values total. Carbohydrate definition, hidden-field bindings and
zero semantics remain unresolved.

Because sealed vectors are immutable, no sparse production publication occurs
until the intended mapping set is explicitly frozen.


## Step 4 first Russian food batch contract gate — 2026-09-21

PR79 is merged at `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6`; Step 3 transactional publication is accepted.

The user authorized Step 4 through the mandatory pre-implementation Contract Gate.

Preflight result:

- no new migration is expected;
- exact batch scope is five reviewed Book2002 records;
- four existing FoodIngredient identities are reused without replacing current
  USDA profiles;
- generic polished rice must become new `RICE_POLISHED_DRY`, not `RICE_WHITE`;
- explicit ATOMIC versions are SUGAR2 / CARROT2 / CABBAGE_GREEN2 / BEET1 /
  RICE_POLISHED_DRY1;
- existing V2 policy can map source-native carbohydrate explicitly to
  `CARBOHYDRATE_AVAILABLE`;
- 60 reviewed source cells imply 37 positive canonical V2 values, with
  below-detection values remaining nonnumeric and ash/organic acids retained only
  as source observations;
- Step 4 must be one five-food transaction, not five independent commits;
- adversarial preflight confirmed a hidden transaction-ownership coupling:
  Step 3 `publish()` commits its own UoW, so Step 4 requires a bounded
  transaction-neutral bundle seam plus a batch service owning the single commit.

The user stated on 2026-09-21 that they possess permission for Book2002 use.
Current repository evidence predates that statement and still reads
`BLOCKED_PENDING_RIGHTS_REVIEW`. The remaining task is to inspect the permission
and record its exact scope in an authority receipt before runtime/data publication.
No source numeric values are published by this gate.


## Step 3 transactional V2 publication runtime — 2026-09-21

Accepted base is merged PR78 at `e5466121e4958cf4fb95ba9041d1c7926daab17e`.
The user explicitly authorized Step 3 runtime implementation under the merged
transactional-publication contract.

Implementation on `feat/transactional-nutrition-publication-v2` provides:

- one reviewed publication service for
  `FoodIngredient → non-current FoodNutritionProfile + immutable observations
  → RU_NUTRIENT_REGISTRY_V2 NutrientVector → ATOMIC FoodCompositionVersion`;
- a specialized unsealed profile writer that never invokes historical V1
  auto-bootstrap;
- exact `FFO_NUTRIENT_VALUE_EVIDENCE_V2` decoding with duplicate-key rejection,
  explicit top-level method, source-neutral component identity and no fabricated
  FDC-only metadata;
- V1 provenance decoding unchanged and `source_nutrient_nbr` preserved for V1;
- explicit V2 method validation and fail-closed reviewed mapping status;
- one existing project UoW / one transaction / seal-last persistence;
- exact replay with zero database changes and stable persisted IDs;
- fail-closed profile/vector/composition conflicts, V1-seal conflict and refusal
  to adopt partial pre-existing bundles;
- rollback/failure injection after each fresh-write boundary plus commit failure;
- preservation of existing current profiles and V1-pinned CompositionCalculator
  semantics;
- no schema migration, production numeric source publication or Step 4 work.

An earlier focused exact-head generation passed 253 tests before final acceptance
hardening/state sync. Final review readiness remains tied to the merged contract's
exact-head focused, full backend, full launcher, methodology, Docs and DC1
verification on the final branch head.


## Step 3 Implementation Contract Gate — 2026-09-21

PR77 is merged at `5343734e620c9f36d24aad54320c2196588b004d`. The user accepted a new process: high-coupling
runtime work now receives a docs-only contract/adversarial preflight before code.

Step 3 preflight found the main hidden coupling before implementation: complete
`FoodNutritionProfile` insertion auto-bootstraps historical V1, which conflicts
with publishing one V2 seal for the same profile. The contract therefore requires
a specialized no-V1-bootstrap publication writer while preserving generic legacy
behavior.

The existing 0034/0035/Composition schema is sufficient; Step 3 assumes no new
migration. The contract defines one-UoW write order, non-current publication,
explicit V2 registry/version, explicit ATOMIC version, exact replay with zero
writes, fail-closed conflicts, rollback injection points and the final regression
tier. No runtime code or production Russian values are included in this gate.

Additional preflight found two more hidden cross-context assumptions before code:
the nutrient-vector reader still decodes V1/FDC-shaped provenance, and the legacy
CompositionCalculator deliberately resolves V1 nutrient definitions. The Step 3…19083 tokens truncated…52314f82569d841abf57910eae3a00afa679a71883cc92490`.
Baseline remains 30 recipes / 189 rows / 30 INCOMPLETE; 66 APPROVED_EXACT,
21 APPROVED_NO_CONVERSION, 37 REVIEW_REQUIRED_ESTIMATE, 65 BLOCKED.
All 43 estimate candidates remain non-executable. No existing profile replacement,
recipe remapping, new migration, API/UI, AI, Retail or Assembly runtime changes.

Executed on 2026-09-12, with `AI_ENABLED=false` for runtime checks:

- `backend/.venv/bin/python scripts/audit_pr6_ru_food_data.py`: PASS. Actual full
  baseline, all-row preservation, all 183 old seals read before/after, all 185
  final seals read, 60 exact ATOMIC owners/profile pins replayed, no-op second
  seed, clean foreign keys and scope audit. Retained JSON is the final execution.
- `backend/.venv/bin/python scripts/validate_pr6_ru_food_sources.py
  --source-directory /tmp/pr6-ru-research`: PASS, two primary archives and five
  complete retained profile/nutrient/vocabulary/available-derivation extracts.
- Focused `test_ru_food_data.py`: **41 passed in 4.67s**. Identity/name/alias,
  candidate exclusion, package tamper, market panel/form/region/date/status,
  Russian display, exact same-source sparse import/digest/zeros, transactional
  rollback, sealed immutability, current-profile replacement replay and scope.
  An earlier run had 40 passed / 1 failed because the static test used the wrong
  repository parent directory; corrected the test path and reran all 41.
- FoodIngredient domain/application/seed/repository, NutrientVector and registry,
  Composition Core/domain migration, Nutrition domain/application/catalogue:
  **311 passed in 20.45s**.
- Migration lineage/rebuild, backup consistency/audit, FoodIngredient migration
  and persistence migration coexistence: **154 passed in 21.60s**.
- `scripts/validate_pr6_nutrient_vector_a.py --content-only`: PASS.
- `scripts/promote_pr6_data_b2a.py` without write option and
  `scripts/audit_pr6_data_b2a.py`: PASS; accepted artifacts not modified.
- Ruff check and format check: PASS, all eight new Python files.
- Mypy with `--follow-imports=silent --ignore-missing-imports
  --check-untyped-defs --python-executable backend/.venv/bin/python`: PASS,
  all five new runtime files (two domain, service, Core adapter, seed).
  Initial constructor metadata, protocol typing and lint defects were corrected
  before final passing verification and full-suite launch.

Full backend + launcher command:
`AI_ENABLED=false backend/.venv/bin/python -m pytest -q backend/app/tests launcher/tests`
— **3799 passed in 632.45s (10:32), zero skips**.

Final `git diff --check` passes; 27 relevant local Markdown file links resolve.
A second `git fetch origin main` confirms the exact starting SHA is unchanged.
HTTPS push could not obtain local credentials; SSH returned publickey denial and
`gh` returned HTTP 401. Delivery uses the authenticated GitHub connector instead;
remote blobs are compared to local Git blob hashes before publication.

No production runtime/data/test changes were made after full-suite launch;
remaining edits are documentation and the retained audit result. Delivery uses
only intended files; unrelated local `.DS_Store` is excluded. Stop for review;
no autonomous merge or B2-B2/Recipe Assembly/PR7 start.

Staged review: `git diff --cached --check` PASS; exactly 19 intended files.
No seed CSV/recipe data, old curation, migrations, dependencies, API/UI, private
records or `.DS_Store` are staged. All staged paths and content were reviewed.

Delivery: [PR #28](https://github.com/Mitronomik/family-food-os/pull/28) is OPEN,
not merged, targeting exact main above from `codex/pr6-ru-food-data`.
Implementation commit: `6da0d711d25a172c2b0e5ef308283dd0c698cee6`.
The GitHub API published all 19 reviewed blobs; its tree SHA matched the staged
local tree exactly: `8c519881f45229db6e5a657ed424b53c27e1d6e2`.
Fetched remote branch and advanced the local branch to that identical commit;
only the unrelated `.DS_Store` remained modified. GitHub confirms no merge conflict.
This later delivery receipt changes state documents only; verified runtime,
tests, source package and audit bytes remain unchanged. PR6 remains NOT COMPLETE.

READY FOR PR6-RU-FOOD-DATA FINAL REVIEW

## PR6-DATA-B2-B2-REDESIGNED — implementation and verification

Starting main fetched before editing: `4180297d47d68a0e0d9efbe7a7a27f3900c4f388`.
GitHub independently confirms PR #28 MERGED at that commit. Created requested
`codex/pr6-data-b2-b2-redesigned` from origin/main; unrelated `.DS_Store` preserved.
The complete accepted seed measured 185 foods and migration 0029; all 37 B2-B1
identities and 46 uses re-resolve against this actual database.

[The evidence package](../data/curation/pr6-data-b2-b2-redesigned/README.md)
records two source-backed frozen-form revisions, three SR profile promotions,
PEACH deferral, three exact mass records and complete all-use/assessment review.
There were no prior compositions for the three profile candidates (PR28
NOT_READY): first ATOMIC v1 is the applicable case, while synthetic old-v1 → v2
replay is separately tested. No new FoodIngredient, new policy or schema change.
The explicit populated-0029 data upgrade is atomic/idempotent and has tested
native backup/restore replay. All historical data is preserved except the
allowed 3 profile and 7 assessment current-marker retirements.

Executed with AI_ENABLED=false where applicable:

- `PYTHONPATH=backend:. backend/.venv/bin/python -m pytest -q
  backend/app/tests/test_pr6_data_b2b2.py`: **27 passed in 10.27s**.
  Covers complete production audit, 46-use guards, both immutable remaps,
  six real publication-stage failure injections and retry, sealed profiles,
  all-use reassessments/stale binding, conditional historical composition v2
  replay, deferred/yield/APPLE/estimate boundaries, hash tampering, missing
  frozen composition and changed exact evidence/carry-forward review on rerun.
- `backend/.venv/bin/python scripts/validate_pr6_data_b2b2_sources.py --archive
  /private/tmp/pr6-ru-research/SR-RELEASE.zip`: PASS; 5 complete source/portion
  extracts, 6 CSV member hashes, archive SHA matches accepted SR 2018-04.
- `backend/.venv/bin/python scripts/audit_pr6_data_b2b2.py`: PASS; populated
  0029 upgrade, all historical rows/seals/compositions, no-op second command,
  native backup/restore, integrity/FKs and full report reproducibility.
- `backend/.venv/bin/python scripts/audit_pr6_ru_food_data.py`: PASS; unchanged
  PR28 historical operation reproduces its accepted evidence.
- `backend/.venv/bin/python scripts/validate_pr6_nutrient_vector_a.py --content-only`:
  PASS for unchanged registry/mappings/legacy observations/zero evidence.
- `backend/.venv/bin/python scripts/promote_pr6_data_b2a.py` and
  `scripts/audit_pr6_data_b2a.py`: PASS; immutable correction chain and v3 audit.
- `backend/.venv/bin/python scripts/audit_pr6_nutrient_vector_b.py` and
  `scripts/audit_pr6_composition_core.py`: PASS; historical upgrades/readiness.
- `ruff check` and `ruff format --check`: PASS on all six new Python files.
- `mypy --follow-imports=silent --ignore-missing-imports --check-untyped-defs
  --python-executable backend/.venv/bin/python` on
  `backend/app/domain/b2b2_vector_import.py`, `backend/app/seed/b2b2.py`,
  `backend/app/persistence/sqlalchemy_core/b2b2.py`: PASS (3 source files).

Early task-local checks found wrong environment paths, a repository getter name,
formatting and test comparisons that included the explicitly mutable profile
current marker. These were corrected; actual seal/value/history byte comparisons
remain enforced. A partial full-regression run was interrupted to add the final
mass-evidence and frozen-composition prerequisite checks, and is not claimed as
passing. The final full backend + launcher run passed: **3826 passed in 649.81s (0:10:49)**,
zero skips. This includes FoodIngredient/profile, B1 evidence/assessment, B2-A
immutable revisions, Nutrition catalogue, NutrientVector, Composition Core,
all migration/rebuild/backup/restore/coexistence and PR28 RU regressions:
`AI_ENABLED=false PYTHONPATH=backend:. backend/.venv/bin/python -m pytest -q
backend/app/tests launcher/tests` (local loopback/process access enabled).

Measured readiness: 71 exact / 23 no-conversion / 35 review-required / 60 blocked;
29 INCOMPLETE + 1 CONDITIONAL, zero COMPLETE. Full before/after SHA-256 and all
ten row deltas are retained; only seven assessment statuses improve. Three old
estimate usages gain independent exact authority, while every original estimate
record and the remaining 40 current non-executable usages retain their boundary.
PR6 is NOT COMPLETE. All required checks pass; implementation is review-ready.
Final identity audit: 37 unique target dispositions / 46 complete uses / no UUID
curation keys. All 31 protected inputs and 56 checked local documentation links
pass. Working/staged whitespace and the 19-file scope audit pass; `.DS_Store` is
excluded. Origin/main was fetched again and remains the same verified SHA.
A non-mutating Git push dry-run confirms feature-branch publication access.
Delivery: feature branch pushed normally; [PR #29](https://github.com/Mitronomik/family-food-os/pull/29)
opened into main. Implementation commit `d0a238ce32193d5884d61ee384d5eb7f242bcaed`.
The delivery receipt updates state only; all tested runtime, data, scripts and
tests remain byte-identical. PR6-DATA-B2-B2-REDESIGNED is REVIEW-READY;
**READY FOR PR6-DATA-B2-B2-REDESIGNED FINAL REVIEW**. No merge or next operation.

## PR6-CLOSE — closure verification

Exact main fetched before editing and again before delivery:
`3caa95e636c02e8f34657b1b6c885f646451114c`. Authenticated GitHub metadata confirms
PR #29 MERGED at `2026-09-12T07:42:03Z`, head
`8a80ce26e7155ab17a5623d07294fbfd1124d9bf`. Merge and accepted head full tree:
`f953fb4d3693c4eead77fad301342359dc8bd206`. `git diff --name-only
 d0a238ce32193d5884d61ee384d5eb7f242bcaed 3caa95e636c02e8f34657b1b6c885f646451114c
 -- backend launcher frontend data scripts` is empty. The accepted **3826 passed
with AI_ENABLED=false** is reused historical PR29 evidence; no full rerun.

**PR6 COMPLETE; PR6-CLOSE COMPLETE** under the
[20-criterion closure decision](../docs/family-food/pr6-closure.md).
Measured 30 current recipes / 189 rows / 82 required foods in the inventory;
71 exact, 23 direct-g, 35 review-required, 60 blocked; 29 INCOMPLETE + 1 CONDITIONAL.
No current stale profile links. All 40 estimates, nine rows for five deferred
forms and three named yield cases remain non-executable. All 188 seals / 63
compositions read/replay; 185 old seals / 60 old compositions preserved. All 35
pre-upgrade and 37 final RecipeVersion input/config snapshots replay. Migration
remains `0029_food_composition_core`. No production behavior/schema/data changes.

Exact commands and retained outputs are in
[verification.json](../data/curation/pr6-close/verification.json):

- B2-B2 populated production audit, PR28 RU audit, VECTOR-A content audit,
  VECTOR-B upgrade, Composition Core upgrade and B2-A catalogue/readiness audit:
  **PASS**, each with `AI_ENABLED=false`, using the existing scripts without write flags.
- Nutrition domain/application/catalogue/evidence, target/config and B2-B2 focused
  tests: **178 passed in 11.72s**. Includes adult/child, sex/PAL, age/growth/fiber
  boundaries, missing/unsupported inputs, explicit reference-estimate warnings,
  deterministic precision/config and current/historical authority.
- Composition, NutrientVector and coherent Nutrition read-scope tests:
  **105 passed in 10.67s**. Missing yield/retention, sparse unknowns, corrupt seals,
  immutability, explicit profile pins, stale bindings and history/snapshot behavior.
- New read-only `scripts/audit_pr6_close.py`: **PASS**; independent regeneration
  and comparison of all three measured JSON files. No user database or network.
  Its first development run failed the deferred-form coverage assertion because
  the old artifact stores null new-food fields for deferrals; nine exact reviewed
  row identities replaced the heuristic. Production data/tests were unchanged.
- Ruff check and format check on the audit script: **PASS**.

Legacy zero differences are explicitly reviewed, not hidden: 185 nutrient
occurrences retain v1 uncertainty; normalized composition never substitutes them
for unknown. Distinct accepted result/config contracts provide the boundary;
no new unified API or exact-zero policy is imposed for closure. Sparse food vectors,
optional combinations, Russian consumer/kitchen readiness and Gate 1 remain limited
as documented. Empty milestone blocker register does not erase those limitations.

`gh` metadata access returned HTTP 401; authenticated GitHub connector provided
independent merge verification. Routine fetch succeeded through the required Git
metadata sandbox escalation. Unrelated `.DS_Store` remains excluded.

Final documentation/scope checks: `git diff --check` PASS; **128 local links and
anchors** checked, including every criterion's canonical reference. The check
found an older progress link to a removed handoff anchor; it now points to the
canonical Composition Core contract. Full changed-path allowlist excludes all
production runtime/schema/seed/test paths and unrelated `.DS_Store`. Exact
static results are retained in the closure package.

Staged verification: `git diff --cached --check` PASS; exactly **25 intended
files**, no backend/launcher/frontend/production seed/test changes and no
`.DS_Store`. All 16 package file hashes verified against checksums.json.
READY FOR PR6-CLOSE FINAL REVIEW. No merge or next operation.

Delivery: branch `codex/pr6-close` pushed normally; [PR #30](https://github.com/Mitronomik/family-food-os/pull/30)
opened into `main`, OPEN / not merged. Closure implementation/evidence commit:
`c3590e67bac9d4b884f2f22df6aed7986f988d10`. This delivery receipt changes state
only; measured evidence and verified runtime/data/test bytes remain unchanged.
Stop for final review. RECIPE-ASSEMBLY-A remains NOT STARTED and separately gated.


## RECIPE-ASSEMBLY-A — authorized preflight

2026-09-12: fetched `origin/main` and verified exact SHA
`e8a75e5b828ef935292da593f9f4d5edbd199474`. GitHub connector confirms PR30
MERGED at `2026-09-12T08:32:53Z` with the same merge commit. Created requested
branch `codex/recipe-assembly-a` from that base. PR6 / PR6-CLOSE COMPLETE;
Assembly A explicitly authorized, evidence preflight in progress. Assembly B and
PR7+ NOT STARTED. Ordered migration source head remains 0029.
Local `gh` returned HTTP 401; connected GitHub read succeeded. Git fetch/branch
creation succeeded through the sandbox escalation flow. Unrelated `.DS_Store`
remains excluded. No runtime or production data changes at this point.


### RECIPE-ASSEMBLY-A — blocked preflight result

**BLOCKED / not review-ready / not COMPLETE.** The user's explicit stop condition
was reached: three production families could not be established from the bounded
reviewed evidence. [Evidence package](../data/curation/recipe-assembly-a/README.md)
records all 30 current RecipeVersions screened and three shortlisted families
DEFERRED. Twenty-nine have unavailable required mass; the remaining oats v2
lacks MILK_1_PERCENT composition authority. Kitchen scope, substitution and RU
default eligibility are not inferred. Positive USDA collection testing evidence
and source-access limitations are retained without granting candidate approval.

No runtime/domain/persistence/API/frontend/seed or historical migration changes.
Migration remains 0029; no production templates. 0030 is still required upon
resuming catalogue implementation. Full implementation tests and full
backend/launcher regression NOT RUN because the explicit evidence stop preceded
implementation; those original acceptance gates remain unmet, not waived.

Verification with `AI_ENABLED=false`:

- Existing `audit_pr6_close.measure` on a disposable accepted database reproduces
  recipe-readiness.json and food-readiness.json byte-for-byte. Its old CLI main-head
  guard is unchanged; no actual user database is inspected. Preserved 188 seals,
  63 compositions, 35 old / 37 final captured recipe snapshots; 40 estimates remain
  non-executable and five deferred forms absent.
- `python3 scripts/audit_recipe_assembly_a_preflight.py`: evidence consistency PASS,
  production readiness false; 30 screened / zero carry-forward-ready / three deferred.
- Disposable-copy corruption checks: accepted-input drift and package drift both
  rejected, with no live evidence mutation.
- `ruff check scripts/audit_recipe_assembly_a_preflight.py`: PASS.
- `ruff format --check scripts/audit_recipe_assembly_a_preflight.py`: PASS after
  formatting the new script. Initial format check correctly requested formatting.
- Initial root `.venv` database invocation lacked SQLAlchemy; retry with
  `backend/.venv` passed. Ruff is installed on PATH, not in backend/.venv.
- Affected-runtime mypy is N/A: no runtime files changed.

Draft publication records the blocker; it must not be described as the requested
three-template implementation being ready for review. Assembly B and PR7+ remain
NOT STARTED. No autonomous merge.

Final pre-publication checks: `git diff --check` and staged whitespace PASS;
16-file staged scope excludes runtime, production seed and `.DS_Store`.
Local documentation verification: 71 links/anchors PASS.
The committed auditor also reproduces the temporary baseline with `--database`: PASS.

Draft delivery: [PR #31](https://github.com/Mitronomik/family-food-os/pull/31),
OPEN / DRAFT / not merged. Evidence commit:
`cbccc22ea87a326256891545c715259a0d67e8cf`. This publishes the blocker report,
not a review-ready RecipeTemplate implementation. Stop for evidence review.

## RECIPE-ASSEMBLY-A-R1 — bounded evidence recovery

2026-09-12. Accepted BLOCKED PR31 merged under explicit user authorization;
exact fetched merge/base `3c854f55323c895c1bdc5aabd5f1146fb6514935`.
Branch `codex/recipe-assembly-a-r1` created from that commit.
[Evidence package](../data/curation/recipe-assembly-a-r1/README.md) records 23
screened donors and nine detailed reviews. Thirteen names/cards overlap earlier
PR4 donor research and were re-inspected; ten expand it. The three PR31 deferred
candidates were not privileged. No final three established: **Assembly A BLOCKED;
R1 BLOCKED**, not milestone completion. PR6 COMPLETE; Assembly B / PR7+ NOT STARTED.

Positive evidence: exact source weights and existing compositions for AFRS plain
oatmeal inputs; explicit standardized-card relationships; published optional and
substitution leads. Remaining form/composition, exact mass, verified substitution
and default market gates are retained. No automatic food-data remediation.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r1.py --database`:
  PASS for evidence consistency, not publication readiness. 23 screened / nine deep /
  zero selected; 29 resolved and 24 unresolved mass rows (includes optional/process
  rows; unresolved values are not treated as zero).
- Disposable accepted DB reproduces PR6-CLOSE food/recipe reports byte-for-byte;
  185 foods, 63 compositions, 188 seals; exact natural identities checked.
  Migration head 0029; 40 estimates non-executable; five deferred forms absent;
  three yield blockers and historical replay preserved. Existing PR6-CLOSE CLI
  head guard unchanged; imported measurement function used under the R1 base guard.
- Package SHA-256 inventory, accepted-input hashes, source/provenance review
  completeness, no-float JSON audit, exact-weight/portion arithmetic, FoodIngredient
  resolution, Composition pins/unknowns, market policy and Russian display checks PASS.
- Five disposable-copy negative checks rejected package drift, incorrect source
  weight, JSON float, cross-food portion and missing required terminal input.
  Semantic cases recomputed package checksums before testing rejection.
- `ruff check scripts/audit_recipe_assembly_a_r1.py`: PASS.
- `ruff format --check scripts/audit_recipe_assembly_a_r1.py`: PASS after initial formatting.
- `git diff --check`: PASS. Scope audit allows only R1 evidence/auditor and owning
  docs/state; unrelated `.DS_Store` excluded from delivery.
- Source checks: 12 primary PDF downloads hashed; remaining readable primary/ICN
  sources reviewed through web text, with actual HTML fallback URLs retained.
  Local ICN/military TLS failures, oversized full AFRS PDF, screenshot cache misses
  and search-only third salt-chain evidence remain explicit limitations, not passes.
- Full backend regression NOT RUN, as authorized for research-only scope.

Research PR delivery follows; stop for review, no autonomous merge or implementation.

Delivery: [PR #32](https://github.com/Mitronomik/family-food-os/pull/32), OPEN,
not merged. Evidence commit `4c7f0712875bbb9ad86a1615d6ddb819178b026c`.
Research evidence is ready for review; R1 and Assembly A remain BLOCKED.
Stop for review. No next-phase or merge authorization.

## RECIPE-ASSEMBLY-A-R1-CORRECTION — canonical market semantics

2026-09-12. Continue existing `codex/recipe-assembly-a-r1` / PR32 from reviewed
head `4741e91710e17b86dbc25c5e69ca58ea36c5c635`. Fetched `origin/main` and PR32
base independently match `3c854f55323c895c1bdc5aabd5f1146fb6514935`.
The preceding R1 zero-ready and universal RU_AVAILABLE failure statements are
historical and superseded by this correction.

Corrected R1 to follow canonical localization policy §5 and the composition
contract's existing RU gate. Classification is unchanged and independent of
ordinary retail, exact form, commodity exception, product reason, dependency
risk and actual substitution requirement. Basic table salt remains RU_AVAILABLE
and passes default-use using retained category evidence; no third chain/SKU is
required. Sugar, specific basic oils and named single spices are reviewed
individually. Water's explicit exception remains. Generic oil, unresolved salt
choices and herb blends cannot inherit it. No donor/market search performed.

**R1 BLOCKED; individually ready 1 (R1-21), selected final three 0.** All 23 donor
dispositions recalculated; nine detailed gate records and eight near-misses.
R1-21 passes every individual gate only for the published 100-portion water/oats/
salt variant. No inferred household-scale, substitution or cooked-output authority.
Fourteen screen-only donors retain their non-market failure and explicit
NOT_REVIEWED terminal-level gates; they are not declared unavailable or ready.

Counted residuals among nine deep reviews (overlapping): food/form/composition 7,
exact mass 8, kitchen scope 2, rights 5, familiarity 1, actual form-specific market
evidence 2 (margarine 72% vs retained 80%; olive-oil content of reduced-fat mayo
unconfirmed). Unresolved identities are not counted twice as rare ingredients.
Verified substitution is still a separate final-three feature gap, with zero
providers; it is not an individual market obligation for every RU_AVAILABLE food.

Verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r1.py --database`:
  evidence consistency PASS, R1 BLOCKED / individually ready 1 / selected 0;
  29 exact and 24 unresolved mass rows unchanged. Disposable accepted DB reproduces
  PR6-CLOSE food/recipe reports byte-for-byte: 185 foods / 63 compositions / 188 seals.
  Migration 0029, 40 non-executable estimates, five deferred forms, three yield
  blockers and historical replay unchanged.
- Fourteen re-hashed temporary package mutations rejected: RU_AVAILABLE-only
  refusal; commodity without identity; blanket oils/spices; lost water exception;
  unreasoned substitution; specialty PASS; market repairs to mass/form/composition;
  wrong ready count; omitted terminal; float; cross-food portion.
- Package checksums and accepted-input hashes PASS; no-float audit PASS. Protected
  quantity/Composition/rights/kitchen/familiarity/substitution/baseline/inventory
  evidence equals the reviewed head. No production seed/schema/runtime change.
- Ruff check and format check PASS. Changed/new local file links and anchors: 15 PASS.
- Working and staged whitespace/scope checks performed before delivery. Unrelated
  `.DS_Store` remains excluded. Full backend regression unnecessary and not run.

Deliver correction to existing PR32 and update its body; stop for final re-review.
PR6 COMPLETE; Assembly A BLOCKED; Assembly B / PR7+ NOT STARTED. No merge or
next-phase authorization.


## RECIPE-ASSEMBLY-A-R2 — targeted recovery

2026-09-12. PR32 MERGED, exact fetched main/base
`8730b9fcfdb56cec2215f7e70319241c83431371`; R1 COMPLETE AS BLOCKED RESEARCH,
accepted 1/3. Branch `codex/recipe-assembly-a-r2`, only R1-23/R1-13 reopened.
[R2 evidence](../data/curation/recipe-assembly-a-r2/README.md) derives Outcome A:
2/3 individually ready (fixed R1-21 plus F00400 method 1 / 100 portions),
selected final three = []. Rice rights and garlic mass recovered; exact base
kitchen/process scope unresolved. Substitution and optional-role gates open.
All R1 files remain byte-identical. No production runtime/data/schema/seed
mutation; migration 0029; Assembly A BLOCKED; B/PR7 NOT STARTED.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r2.py --database --adversarial --source-dir <originals>` — PASS; Outcome A, 2/3, selected 0. The source directory held the three exact originals named in the manifest; no production DB path is accepted.
- Disposable accepted DB: PR6-CLOSE food/recipe reports match bytes; 185 foods / 63 compositions / 188 seals / 40 estimate usages; historical replay, five deferred forms and yield rows match the accepted baseline; migration 0029.
- Stable Composition references compare canonical identity/version, INPUT/kind and profile source/version/type/basis. Fresh loader UUIDs and UUID-bearing snapshot hashes differ between disposable DBs; internal snapshot/seal correctness is independently verified by accepted replay, not by equating unrelated DB UUIDs.
- All 19 adversarial cases rejected plus DEFER positive control passed: AP/EP, piece inference, revision mixing, wrong lb constant, garlic food/form/estimate/density, alternative/optional, OR kitchen assumption, incomplete substitution branches/Composition, household claims, unsupported rights and false final-three/count states.
- Full original SHA-256/size, exact AFRS original-to-excerpt pages, source rice/garlic observations, whole-package and frozen R1/accepted-input hashes, no-float, Russian ingredient display and Decimal/rational arithmetic — PASS. Relevant source PDF pages rendered and visually reviewed.
- Local links/anchors — 80 PASS. `ruff check` and `ruff format --check` for the new audit — PASS.
- `git diff --check`, `git diff --cached --check`, staged 25-file scope audit — PASS; `.DS_Store` excluded. Changed scope is R2 evidence, its read-only auditor and five state/canonical documents only.
- Full backend regression was not run: production code/data did not change. Direct local TLS downloads were unavailable; browser downloads supplied the exact source bytes. No original HTML or unavailable Army-PDF byte hashes are invented.

R2 evidence is ready for review. Assembly A remains BLOCKED, not COMPLETE.
Feature branch and PR published; stop for review, with no autonomous merge or follow-up research.


Delivery: [PR #33](https://github.com/Mitronomik/family-food-os/pull/33),
OPEN into main, not merged. Evidence commit:
`bb9254143f2449eeb0e7786ce1f06af91afbe517`.
R2 evidence READY FOR REVIEW; Assembly A BLOCKED. Stop for review.


## RECIPE-ASSEMBLY-A-R3 — Third-Family Closure

2026-09-12. PR33 MERGED at exact fetched main/base
`f2b6bc9015a1b892bb533b5d322d981d5a1782bd`; R1/R2 COMPLETE AS BLOCKED RESEARCH,
accepted ready count 2/3. This supersedes the historical OPEN PR33 delivery
record above. R3 is the current authorized evidence operation on
`codex/recipe-assembly-a-r3`.

[R3 evidence](../data/curation/recipe-assembly-a-r3/README.md): twelve serious
prefilter candidates, none passing, zero deep reviews. R3 BLOCKED; no third
candidate; individually ready 2/3; final three empty. Optional/substitution gates
remain OPEN. Exact published E00100 and F00400 method 1 batches remain frozen;
all bytes of both accepted packages are preserved. No production mutation;
migration 0029, Assembly A BLOCKED, B/PR7+ NOT STARTED.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r3.py --database --adversarial --source-dir <originals>` — PASS; R3 BLOCKED, 2/3, no selected third. After tightening source-weight binding, the affected local semantic/adversarial audit was rerun and passed; production replay inputs were unchanged.
- Disposable accepted DB replay matches PR6-CLOSE food/recipe reports byte-for-byte: 185 FoodIngredients, 63 exact Composition/profile pins, 188 seals, 40 non-executable estimate usages. Historical replay, five deferred forms and yield rows equal the accepted baseline; migration remains 0029.
- Complete R1/R2 package file inventories and SHA-256 match exact merged base. Accepted input hashes and production scope pass; no production truth is published. Stable profile pins compare canonical code, Composition version, INPUT/kind and source/version/type/basis; random disposable UUIDs are not equated.
- Full AFRS and SDSU original SHA-256/size pass. Five retained AFRS pages equal their original pages in the June 2003 system; extracted text equals the retained PDF. N50200 weight/issue alignment was rendered and visually inspected. Missing original hashes for indexed/text-only sources remain explicitly null.
- Package hashes, no-float/Decimal conversions, source weight bindings, optional/group semantics, whole substitution branch rejection, Russian display, corrected market/familiarity policy and local links/anchors (88) — PASS.
- Thirty adversarial cases rejected; complete synthetic positive control passed. Coverage includes missing Composition/mass, alternative-as-optional, processing medium, one-sided/inferred substitution, untested variant/unrelated family, estimates/density/piece/AP, specialty input, English display, household scaling, rights, incomplete branch, frozen bytes, runtime/schema/seed scope and false final-three states. The fixture is a validator test, not an additional donor.
- `ruff check` and `ruff format --check` for the new script — PASS.
- `git diff --check`, `git diff --cached --check` and exact staged 26-file scope audit — PASS; unrelated `.DS_Store` excluded. Scope is the R3 package, read-only auditor and five state/canonical documents only.
- Full backend regression was not run because production code/data did not change. Direct original retrieval was unavailable for several rejected candidates; those sources were never promoted to publication authority.

R3 research evidence READY FOR REVIEW; R3 result and Assembly A remain BLOCKED.
Stop after delivery for review. No merge, follow-up donor search, food-data repair
or migration 0030 is authorized.


Delivery: [PR #34](https://github.com/Mitronomik/family-food-os/pull/34), OPEN
into main, not merged. Evidence commit:
`b2b9fe94737328bd2c16e3e0dc34b34802a185f7`.
R3 research evidence READY FOR REVIEW; R3 result and Assembly A BLOCKED.
Stop for review; no next-operation authorization.


## RECIPE-ASSEMBLY-A-R4 — N50200 deep viability

2026-09-12. PR34 verified MERGED at exact accepted fetched main
`a375f005b09880cf6a63cb5c8b1e964a0f558cb7`; R1/R2/R3 COMPLETE AS BLOCKED RESEARCH.
R4 is the authorized one-candidate evidence operation on
`codex/recipe-assembly-a-r4-n50200`.

[Complete R4 evidence](../data/curation/recipe-assembly-a-r4-n50200/README.md)
and [derived decision](../data/curation/recipe-assembly-a-r4-n50200/final-decision.json):
R4 = BLOCKED. All 13 source rows bound, 11 required base rows retained; exact
Weight EP grams computed with Decimal. Six current INPUT Composition paths
reusable; seven selected rows lack Composition. No 90-to-93 turkey or arbitrary
yellow-onion mapping. Generic onion and six primary missing-profile candidates
reviewed without production promotion. Five exact mandatory input profile/market
issues survive. Published cheese and patty process mass inconsistencies prevent
kitchen verification for all three complete branches. Optional food semantics
PASS; full substitutions UNVERIFIED. Dish identity is familiar, exact recipe
familiarity/default eligibility NOT_ESTABLISHED. Data-enablement plan withheld.

Executed verification:

- `AI_ENABLED=false backend/.venv/bin/python scripts/audit_recipe_assembly_a_r4_n50200.py --database --adversarial` — PASS.
- Same audit with `--source-dir <originals>` — PASS; full AFRS/SR/Foundation hashes,
  exact page/extract lineage and turkey dataset search verified.
- Disposable accepted replay exactly matches PR6 closure food/recipe reports:
  185 foods, 63 Composition pins, 188 seals, 40 non-executable estimates,
  historical replay/deferred/yield evidence and migration 0029 unchanged.
- 51 adversarial negative cases rejected; positive all-gates control accepted.
- Frozen R1/R2/R3 byte hashes, package hashes, no-float Decimal evidence,
  Russian display and local links/anchors — PASS.
- `ruff check scripts/audit_recipe_assembly_a_r4_n50200.py`, corresponding
  `ruff format --check`, and unstaged whitespace check — PASS.

Initial replay comparison exposed random disposable profile/food UUIDs and
insertion timestamps. Auditor now compares all stable food/source/version/value/
seal facts, excluding only those three volatile identity/storage fields;
replayed semantic evidence passes. Root `.venv` lacked SQLAlchemy; actual
verification used `backend/.venv`. Local `gh` returned 401; PR metadata was
verified through the GitHub connector. Web-byte hashes unavailable for fresh
retailer/manufacturer text remain null, with factual notes and access limits explicit.

No full backend regression: production runtime/data/schema are unchanged.
Ready remains 2/3; third candidate none; family_count/optional_role/
verified_substitution OPEN. Assembly A BLOCKED; B/PR7+ NOT STARTED; 0029.
Stop for review after delivery. No self-merge or automatic data PR/search.

Delivery: [PR #35](https://github.com/Mitronomik/family-food-os/pull/35), OPEN
into exact accepted main, not merged. Evidence commit:
`678d8d0e4c3d5f67ccf6645e2f9f95a0719c01f2`.
All 28 intended files were reviewed and staged; unrelated `.DS_Store` excluded.
`git diff --check` and `git diff --cached --check` — PASS before commit.
R4 research evidence READY FOR REVIEW; R4 result and Assembly A BLOCKED.


## PR36 final provenance/idempotency corrections

2026-09-13. Review `5190228147`, existing PR36 branch
`codex/ru-normative-recipe-corpus`; accepted main
`7388d19677cffbf5cd6cb192eabc0b93cad870f7`; prior head
`874879db6467eaebd045b853a1727fde539d1503`.

Bundle-provided card hashes are now required and passed unchanged to domain
validation. Missing/stale hashes fail. Existing document identity now compares
all persisted immutable document/card/child facts before returning idempotent 0;
conflicting facts raise `CorpusImportConflictError` before any write. No update
semantics, schema or shared persistence/UoW changes.
[Canonical comparison contract](../docs/family-food/ru-normative-recipe-corpus.md).

New verification on the correction runtime (with `AI_ENABLED=false`):

```bash
/Users/volkilli/Projects/family-food-os/backend/.venv/bin/python -m pytest -q \
  backend/app/tests/test_recipe_source_corpus.py \
  backend/app/tests/persistence/test_recipe_source_corpus_persistence.py \
  backend/app/tests/test_food_composition_migration.py \
  backend/app/tests/test_migration_lineage.py \
  backend/app/tests/test_migration_runner_rebuild.py \
  backend/app/tests/persistence/test_migration_coexistence.py --tb=short
```

Result: **105 passed in 11.59s**. Includes exact bootstrap/frozen repeats,
34 parameterized metadata/card/structured-child conflict cases, late frozen-card
conflict, unchanged complete DB dumps, and zero additional SQLite changes even
when the caller catches the conflict and commits the transaction. Decimal values,
equivalent timestamp offsets and reordered unordered collections repeat correctly.
Fresh/upgrade/lineage/migration-coexistence checks PASS.

Ruff check and `ruff format --check` on the four changed Python files: PASS
(`All checks passed!`; `4 files already formatted`).
Offline CLI smoke with the frozen `--bundle` and a disposable database: first
import 214, repeat 0, same document ID; stale-hash and valid-rehash conflicting
bundles each exit 1, with the complete DB dump unchanged after each failure.
SQLite foreign keys/integrity PASS; production `food_recipe_versions` remains 0;
migration head `0030_recipe_source_corpus`.

Initial focused run: 4 failed / 7 passed / 35 errors. Strict validation exposed
six pre-existing stale hashes in `bootstrap.json`; all six were corrected to the
existing UTF-8 raw texts, with no text/structured/document change. The new test
also incorrectly indexed the set returned by `current_migrations`; corrected.
Second run: 1 failed / 45 passed due to treating pooled SQLite `total_changes()`
as transaction-local; the assertion now measures its delta. The final 105-test
run above passes; no acceptance criterion was weakened.

Frozen 214-card bundle is byte-identical to prior head, SHA-256
`ee0aad55080ba09294625af57800172862a53293518f7869e1b974ed7e9ab0b7`.
No production data/schema changes in this correction. Only the six bootstrap
hash literals changed among source data files.

Historical full backend + launcher regression and live 214-card acquisition:
PASS at `5f95530472e83748b67dd9efa9fa4542aeb5c546`, GitHub Actions
run `34744992334`, retained in
[the original receipt](../data/curation/ru-normative-recipe-corpus/verification.json).
Not rerun: this correction is confined to corpus domain/repository validation,
with no shared runtime/persistence/startup changes or remaining regression concern.

PR36: **READY FOR FINAL RE-REVIEW**, not merged. Assembly A BLOCKED; Assembly B
and PR7+ NOT STARTED. Same-origin/redirect hardening remains follow-up.
Stop after correction publication; no merge or next milestone authorization.

## Corpus v0.3 reconciliation — 2026-09-20 branch work

The user authorized a separate evidence/curation PR integrating the local v0.3
corpus with the existing DC1 work. This bounded operation does not authorize
DC2/DC3 production publication or a roadmap reorder.

Base: `d8c76a64483e3d5814e702be33c12cbe2e144160`. PR #70 was OPEN / NOT MERGED
at reconciliation, pinned at `c23227be12605c27f3621b38e839085f141ceb8b`.
That was the capture-time state. PR70 is now accepted as recorded below; its recovery package remains unchanged.

See [integration plan](../docs/family-food/corpus-v03-integration-plan.md) and
[reconciliation package](../data/curation/corpus-v03-reconciliation/README.md).
The package accounts for all 68 historical PR70 families, 479 v0.3 cards,
1473 routes and 2693 food occurrences. Lexical review groups are not canonical
food identities. The 46 review queues are not publication-ready batches.

Original delivery boundary: review-ready, without merge authorization at that time.
The later authorization below supersedes only the PR71 merge boundary.

## PR70 accepted; PR71 synchronization — 2026-09-20

PR70 merged as `b9768984392982bd05d28fc0f7793453fe8378b5`. Final PR70 head `514c6b1` and the historical
`c23227b` reconciliation pin have identical trees. No source input correction
or numerical regeneration is implied by the merge.

The user authorized updating, verifying and merging PR71 after PR70.
Current focus/handoff are synchronized; historical receipts remain preserved.
The integration remains curation-only. No production/catalogue/schema/API/UI/
Planner change, no DC2/DC3 publication and no Gate1 closure are included.
