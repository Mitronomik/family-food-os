# Handoff

## Step 8 Contract Gate review-ready — PR90

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747` (merged PR89 / accepted Step 7 runtime).

Branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical contract:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

Verified semantic head:
`49c291ab5e46a88e34a6f3ae897c32f4cccc6378`.

Review:
`#5303638521 — READY TO MERGE CONTRACT GATE`.

Frozen vertical slice:

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ licensed FIC RU-NUT-DB code 1417 / DB/533
→ non-current V2 profile
→ 17-value sparse sealed vector (WATER unknown)
→ ATOMIC v1 / INPUT
```

Critical preserved boundaries:

- existing generic `BUTTER_UNSALTED` / USDA FDC 173430 unchanged;
- School2022 source calculations are not production food-nutrition authority;
- FIC raw record hash pinned to
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- `water=null` is not coerced/inferred;
- no current selector switch;
- no YieldModel/retention/Transformation/Applicability rows;
- no migration; 0033 remains reserved and head stays 0038;
- no Step 9/10.

Semantic verification:
Docs #343 SUCCESS; DC1 #205 SUCCESS; mergeable=true; 0 behind main;
unresolved review threads 0; patch whitespace/conflict audit clean.

This is a docs-only gate. No runtime/schema/production data was published.

Stop for final review/merge. After merge, Step 8 runtime/data publication needs
separate explicit authorization.

## Step 8 recipe-dependency food batch Contract Gate — 2026-09-24

Accepted main:
`8ae941a1f5c4f07177b2e80272e582f8690dd747` (merged PR89 / accepted Step 7 runtime).

Current branch:
`docs/step8-recipe-dependency-food-batch-contract`.

Canonical gate:
`docs/family-food/recipe-dependency-food-batch-contract.md`.

Bounded target:

```text
School2022 53-19з — Масло сливочное (порциями)
→ BUTTER_PEASANT_72_5_UNSALTED
→ licensed FIC RU-NUT-DB code 1417 / DB/533
→ non-current V2 profile
→ sparse 17-value sealed vector
→ ATOMIC v1 / INPUT
```

Critical evidence:

- School2022 PDF SHA-256
  `c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`;
- §1.4 freezes butter at 72.5% fat for recipe norms;
- procurement-quality page 261 requires unsalted butter and identifies the
  peasant class at at least 72.5%;
- recipe 53-19з has gross=net=10 g and no thermal treatment;
- FIC DB/533 source code 1417:
  `Масло сливочное крестьянское, 72,5%`;
- exact FIC raw record hash:
  `b21345dd5ffa8b1348931808067b116940a252abec6c26b01870c192829a711d`;
- retained FIC archive independently reverified at the accepted
  206692075-byte / `c0d90020...` identity;
- DB/533 `water=null`: do not coerce or infer; expected vector has 17 values.

Preservation:

- generic `BUTTER_UNSALTED` and USDA FDC 173430 history unchanged;
- no current-profile selector switch;
- no transformation/yield/retention/applicability rows;
- no migration; 0033 stays reserved, head stays 0038;
- no Step 9/10.

The one-food size is intentional: it closes one exact Step 9 vertical dependency
without widening catalogue scope.

Boiled egg 54-6о was rejected as the immediate vertical slice because boiling
would require unsupported production transformation nutrition and the retained
FIC cooked-egg candidate is structurally quarantined.

Current authorization is docs/preflight only. Stop after Contract Gate delivery;
no runtime/data publication before review/merge.

## Step 7 runtime review-ready — PR89

Accepted main:
`71e4cfc63908440a54631e68b7507e94311980d2` (merged PR88 / accepted Step 7 Contract Gate).

Branch:
`feat/step7-transformation-applicability-runtime`.

PR:
`#89 — Step 7: transformation applicability runtime`.

Verified runtime/test/workflow head:
`e481b6cda42afa2f33e5239262dae3f3c6780797`.

Delivered contract-preserving runtime:

- one dependent immutable `TransformationApplicability` per exact
  `FoodTransformation`;
- additive `0038_transformation_applicability`, no accepted-table rebuild/backfill;
- registry-aware V2 retention read/write that proves persisted row registry identity;
- explicit V2 transformed-composition publication;
- separate applicability-aware V2 calculator;
- exact food, explicit season and sequential evidence-scope enforcement;
- DB- and repository-level late-applicability rejection;
- same-UoW failure rollback;
- legacy V1 calculator, retention snapshot/digest and legacy publication paths unchanged;
- zero production numeric Book2002 / School2022 / legacy loss-factor publication.

Verification on `e481b6cda42afa2f33e5239262dae3f3c6780797`:

- Russian nutrition methodologies #113 — SUCCESS;
- Nutrient Registry V2 #169 focused — 280 passed, including all three Step 7 suites;
- Partial nutrition profiles #130 — SUCCESS:
  - focused 228 passed;
  - full backend shards 1252 / 768 / 582 / 962 passed;
  - launcher 643 passed, 2 skipped;
- Nutrient Registry V2 launcher — 643 passed, 2 skipped;
- AI_ENABLED=false;
- GitHub PR patch audit: no trailing whitespace/conflict markers, bounded Step 7 scope;
- direct local git shell check unavailable because the container could not resolve github.com.

Review concerns closed during implementation:

- historical tests expecting 0037 as schema head were advanced without removing 0037 from the prefix;
- synthetic V2 persistence fixture now satisfies existing partial-profile invariants;
- rollback is proven by an injected exception after attempted Step 7 publication;
- registry-aware reader is tested against a physically mixed persisted V1/V2 retention profile;
- late applicability is rejected both by repository and direct SQLite trigger;
- focused CI explicitly includes the new Step 7 test suites.

Stop boundary:

- PR89 may be reviewed; no autonomous merge;
- no Step 8 / Step 9 / Step 10;
- no production numeric source-loss publication;
- after PR89 merge, stop and wait for separate Step 8 authorization.

## Step 7 Contract Gate review-ready — PR88

Accepted main:
`6ec1069d867388e5d1f4782ce6cdeed08c017694` (merged PR87).

Branch:
`docs/step7-transformation-applicability-contract`.

Verified semantic contract head:
`7068b4d7af9d0b8817e933daeaa89a08f68feb26`.

Canonical contract:
`docs/family-food/transformation-applicability-contract.md`.

Key frozen boundaries:

- existing CompositionCalculator / retention writer/reader remain V1-compatible;
- old retention snapshot digests are not rewritten;
- V2 retention requires explicit registry-aware publication/read validation;
- no same-code automatic V1→V2 carry-forward;
- TransformationApplicability is a one-to-one dependent record of an immutable
  FoodTransformation;
- exact food / season / source evidence scope are explicit;
- late applicability after composition publication is forbidden;
- explicit V2 transformed publication validates applicability before insertion;
- expected migration is 0038_transformation_applicability;
- initial runtime publishes zero production numeric source-loss factors.

Contract verification:
Docs #335 SUCCESS; DC1 #197 SUCCESS.
Final semantic review #5299903757: READY TO MERGE CONTRACT GATE.

After PR88 merge, stop. Step 7 runtime/0038 requires separate authorization.
Do not start Step 8/9/10 automatically.


## Step 7 transformation applicability Contract Gate — 2026-09-24

Accepted main:
`6ec1069d867388e5d1f4782ce6cdeed08c017694` (merged PR87 / accepted Step 6B).

Current branch:
`docs/step7-transformation-applicability-contract`.

Canonical gate:
`docs/family-food/transformation-applicability-contract.md`.

Current authorization is docs/preflight only.

Critical facts:

- current Composition calculation and retention writer are V1-pinned;
- 0035 made retention rows registry-version-aware but historical retention domain
  snapshots/digests intentionally omit registry identity;
- therefore Step 7 must not mutate old retention snapshot shape;
- V1/V2 same-code identity is not sufficient retention authority;
- exact food/season/operation/source applicability must be explicit;
- supplied loss/retention corpus evidence is not production-ready numeric
  authority.

Gate direction:

- one-to-one dependent `TransformationApplicability` per immutable
  `FoodTransformation`;
- no late applicability after a transformation is used by composition history;
- explicit registry-aware V2 retention publication seam;
- legacy `CompositionCalculator` remains V1;
- separate applicability-aware V2 calculator;
- expected additive migration `0038_transformation_applicability`;
- zero production numeric loss-factor publication in initial Step 7 runtime.

Stop after Contract Gate review/merge. No runtime 0038, Step 8, Step 9 or Step 10
without separate authorization.


## Step 6B runtime review-ready — PR87

Accepted main:
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc` (merged PR86).

Branch:
`feat/step6b-meal-plan-reference-methodology-pins`.

Verified runtime/test head:
`8853d2a09240d26997c83915bc4167ab39979323`.

Step 6B implementation is review-ready.

Key delivered semantics:

- one optional complete-or-zero methodology pin set per MealPlan revision;
- pin references exact immutable Step 6A selection;
- member birth_date / sex / height / weight / activity / goal / updated_at are
  frozen from authoritative HouseholdMember state;
- member updated_at is guarded by SQLite-safe CAS/write intent before plan write;
- Russian group-reference selections are revalidated at `MealPlan.week_start`;
- methodology pins persist atomically with MealPlan, meal-pattern pins, events
  and Servings;
- old MealPlans remain zero-pin and receive no backfill;
- revision history preserves old snapshot/selection while a later revision may
  pin newer member state or methodology selection;
- Planner does not provide methodology IDs and remains zero-pin until Step 10.

Migration:
`0037_meal_plan_reference_methodology_pins`.

Exact runtime verification:
Docs #331 SUCCESS; DC1 #193 SUCCESS; Russian #98 380 passed; Registry #139
focused 257 + 4/4 backend shards + launcher 643/2 skipped; Partial #109 focused
228 + 4/4 backend shards + launcher 643/2 skipped.

After final docs/state verification, PR87 may be reviewed for merge. No autonomous
merge. Stop before Step 7 / Steps 8–10.


## Step 6B runtime authorized — 2026-09-23

Accepted main:
`ef021c44e3166fbd2aa930c35b57dcb258e11bcc` (merged PR86).

Branch:
`feat/step6b-meal-plan-reference-methodology-pins`.

Read first:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Bounded runtime target:

- MealPlan-owned reference-methodology pins only;
- migration `0037_meal_plan_reference_methodology_pins`;
- exact Step 6A selection ID per pinned member;
- immutable authoritative member target-input snapshot;
- complete-or-zero pin coverage;
- MealPlan.week_start reference date;
- Russian applicability revalidation at week_start;
- member updated_at CAS guard before plan commit;
- zero backfill for historical plans;
- no Planner/default/API/UI/source-native-policy change.

After review-ready delivery, stop. No merge or Step 7/Step 10 without separate
authorization.


## Step 6A runtime review-ready — PR86

Accepted main:
`e38692f7839ecab2da9499dc968dd01638227046` (merged PR85).

PR86:
`feat/step6a-member-reference-methodology-selection`.

Verified runtime head:
`e03be7b0c4a9b7766a961026cdf8de7d1f56d8d8`.

Step 6A implementation is review-ready.

Important final corrections:

- migration 0036 DDL is rollback-atomic under the custom runner;
- global `acceptance_request_id` cross-scope reuse fails closed;
- real SQLite concurrent Household/member writer is converted to a deterministic
  Step 6A conflict through an exact-token CAS/write-intent guard;
- semantic no-op is zero-write and intentionally does not persist/consume its new
  request ID; later reuse is an ordinary new command.

Exact runtime verification:
Docs #314 SUCCESS; DC1 #176 SUCCESS; Russian #81 358 passed; Registry #110
focused 257 + 4 backend shards + launcher 643/2 skipped; Partial #92 focused 228
+ 4 backend shards + launcher 643/2 skipped.

No MealPlan/0037/Planner/API/UI/source-native-policy change is in Step 6A.

After PR86 merge, stop. Step 6B / migration 0037 requires separate explicit
authorization.

# Handoff

## Step 6A runtime authorized — 2026-09-23

Accepted main:
`e38692f7839ecab2da9499dc968dd01638227046` (merged PR85).

Branch:
`feat/step6a-member-reference-methodology-selection`.

Read first:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Bounded runtime target:

- MemberReferenceMethodologySelection only;
- migration `0036_member_reference_methodology_selection`;
- FAMILY_FOOD_NUTRITION_V1 baseline + optional Step 5 Russian group-reference;
- acceptance_request_id exact retry identity;
- expected_current_selection_id ordinary concurrency;
- Household/member token binding and stale-read protection;
- no MealPlan/0037/Planner/API/UI changes.

After review-ready delivery, stop. No merge and no Step 6B without separate
authorization.


## Step 6 corrected Contract Gate — PR85 re-review blockers resolved

Accepted base:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Branch:
`docs/step6-persisted-methodology-selection-contract`.

Canonical contract:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

PR85 re-review blockers are now resolved in the contract:

1. **Split signal:** runtime Step 6 is mandatory Step 6A/6B, not one migration.
   - 6A: member reference-methodology selection, expected 0036.
   - 6B: MealPlan reference pins/snapshots, expected 0037.
2. **Policy ownership:** `RU_SOURCE_NATIVE_*` is removed from member selection;
   it remains food/calculation policy for a later calculation/plan receipt.
3. **Replay identity:** persisted `acceptance_request_id` identifies exact retry;
   stale `expected_current_selection_id` remains a conflict unless the exact
   request ID is replayed.

Member selection now owns only personal reference configuration:
`FAMILY_FOOD_NUTRITION_V1` plus optional Step 5 Russian group-reference table.

Existing plans are never backfilled. Step 6B later supports zero-pin legacy plans
or complete pins only.

Current task remains docs-only PR85. No runtime migration/code is authorized.


## Step 6 persisted methodology selection Contract Gate — frozen 2026-09-23

Accepted base:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Branch:
`docs/step6-persisted-methodology-selection-contract`.

Canonical gate:
`docs/family-food/persisted-nutrition-methodology-selection-contract.md`.

Key decisions:

- methodology choice is a Household-owned immutable/versioned member selection,
  not a mutable HouseholdMember field;
- it is separate from MemberMealPatternSelection;
- `FAMILY_FOOD_NUTRITION_V1` remains the required personal baseline;
- Russian group reference is optional/additive and must pair with an explicit
  Russian source-native policy;
- published-zero estimate remains opt-in;
- MealPlan historical replay requires an immutable member methodology pin plus a
  snapshot of birth_date/sex/height/weight/activity/goal/member_updated_at;
- existing historical plans remain zero-pin legacy state; no invented backfill;
- methodology-pinned plans must use complete-or-zero member pin sets;
- expected next migration is 0036; reserved 0033 remains untouched;
- Step 6 does not change current Planner/NASEM behavior.

Current work is docs-only Contract Gate. Do not implement 0036/runtime until the
gate is merged and separately authorized.


## Step 6 persisted methodology selection Contract Gate — 2026-09-23

Accepted main:
`3de3c58ee898284f8d2168af1aae04af754a6bfc` (merged PR84).

Current branch:
`docs/step6-persisted-methodology-selection-contract`.

The user explicitly authorized Step 6. Under the repository-wide
Implementation Contract Gate rule, current work is docs/preflight only.

Preflight facts:

- Step 5 reviewed Russian reference table is merged and available explicitly;
- current personalized target path is `FAMILY_FOOD_NUTRITION_V1` /
  NASEM/DRI-based and remains the existing default;
- Russian source-native policy is explicit/versioned
  (`RU_SOURCE_NATIVE_STRICT_V1` or
  `RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`);
- `HouseholdMember` is mutable and has no historical profile revisions;
- `MealPlan` is immutable/revisioned and already pins
  `MemberMealPatternSelection`, but not nutrition methodology;
- historical target replay therefore cannot rely on current member state;
- no current migration uses `0036`; reserved `0033_recipe_template_catalogue`
  must remain reserved.

The Step 6 gate must decide the immutable selection + plan-pin/snapshot contract
before implementation. No runtime/schema change is authorized on this branch.

After contract review/merge, stop. Do not begin Step 6 runtime automatically.


## Step 5 runtime publication — authorized 2026-09-23

Accepted main:
`f12a3f58279eb07c710d1ff889cc70d933da3310` (merged PR83).

Current branch:
`feat/step5-russian-reference-table-runtime`.

The user explicitly authorized runtime Step 5 after merging the Contract Gate.

Read first:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Frozen runtime target:

- methodology `RU_MR_2_3_1_0253_21_ADULT_MICRONUTRIENT_V1`;
- exact 48 rows / 24 definitions × male/female;
- tables 11/12 + 16/17 only;
- completed age 19+;
- KFA-independent;
- exact Decimal source values/source units;
- exact source claim/page/table/row/column provenance;
- all canonical codes/units validated against `RU_NUTRIENT_REGISTRY_V2`;
- existing `ReviewedRussianReferenceTable`, provider and selector reused;
- unknown/tampered/drifted package fails closed;
- no DB write, schema or migration;
- NASEM/default Planner/API/UI paths unchanged.

Important source-semantic boundary:
`BETA_CAROTENE` preserves source/reference `mg/day` while registry canonical
unit is `µg`; this is same-definition mass-unit compatibility, not source
rewriting or nutrient substitution.

Tables 13/18 remain deferred because adequate-level semantics are not represented
by the current row model. Do not add `reference_kind` in this runtime PR.

Before publishing rows, bind the runtime package to the pinned source transport
hashes and exact source claim identities. If the exact transport evidence cannot
be reproduced, stop rather than fabricate claim IDs.

After review-ready delivery, stop. No merge and no Step 6 without a separate
explicit instruction.

## Step 5 reviewed Russian reference table contract gate — 2026-09-22

Accepted main:
`aa5ebcb4c70c9adee0fd1242f520ef1298f6b167` (merged PR82).

Current branch:
`docs/step5-reviewed-russian-reference-table-contract`.

The user authorized Step 5. Under the repository Implementation Contract Gate
rule, current work is docs/preflight only.

Preflight source facts from the supplied corpus:

- source: `RU-NEEDS-MR-2.3.1.0253-21`;
- official PDF SHA-256:
  `cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79`;
- population-reference package: 147 groups / 218 source nutrient rows /
  872 claims / 735 scalar lookups / 137 withheld;
- source package itself is transport evidence, not runtime authorization.

Proposed first production table is intentionally only 48 adult micronutrient
rows:

- tables 11/12 men;
- tables 16/17 women;
- 24 exact V2 definition mappings per sex;
- source `Старше 18 лет` maps to completed age 19+;
- KFA-independent;
- no source null-sex coercion.

Important deferrals:

- tables 9/14 energy/macros: Far-North adjustment applicability is not represented
  by the current row model;
- tables 10/15 percent-energy/ranges: not current daily-amount comparison truth;
- Vitamin D and Calcium: source footnotes change >65 values and the corpus
  withholds those cells;
- tables 13/18 are adequate-level references and are deferred because the
  current row model does not preserve reference kind; fluoride is therefore
  deferred with them;
- folate/Vitamin K: no accepted exact target-definition mapping for this table;
- cobalt/silicon/vanadium: no V2 target;
- children and pregnancy/lactation: outside current selector/publication contract.

Read:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Do not publish numeric rows or start runtime until this gate is merged and the
user separately authorizes runtime Step 5.

## Step 4C runtime publication — 2026-09-22

Accepted main: `be6eed3591752d38ece3de5892e4306134e8d762` (merged PR81).
Branch: `feat/step4-ru-nut-db-runtime-publication`.

Authorized scope: publish the exact five licensed RU-NUT-DB records through the
merged Step 3 V2 publication path.

Runtime design:
- refactor Step 3 to expose one transaction-neutral bundle application operation;
- preserve public `ReviewedNutritionPublicationService.publish(bundle)` behavior;
- add `ReviewedNutritionBatchPublicationService.publish_batch(...)` owning one
  UoW and one commit;
- fresh batch = five bundles / two new identities / 90 V2 values / five seals /
  five ATOMIC versions;
- replay = zero writes and stable IDs;
- conflict/failure on any food = rollback entire attempted batch;
- no migration/schema;
- all FIC profiles non-current; current USDA profiles preserved.

Data package:
`data/curation/ru-nut-db-step4-runtime/`.
It contains only the five reviewed source records, exact license attribution and
source link. The full FIC database is not republished.

Verification is pending on the runtime implementation head. Stop after PR review;
no self-merge or Step 5.

# Handoff

## Step 4B RU-NUT-DB semantic closure — 2026-09-22

Accepted main: `f7ac885dde055900b3a6397aa64a15fe698abe5b` (merged PR80).
Current branch: `data/step4-ru-nut-db-semantic-closure`.

The licensed five-record source mapping is frozen in:
`data/curation/ru-nut-db-step4-semantic-closure/`.

Result: 18 approved numeric fields and **90 V2 values — 18 per food**.
Source-published zero is retained as numeric zero with `VALUE` source state and
explicit provenance; it is not reclassified as missing/below-detection.

Eight fields remain deferred/source-only:
`carbh, a_vit, pp, carot, cholest, ethanol, sugar_ad, salt_ad`.

No migration/schema change is required by the semantic closure.

After Step 4B merge/review, runtime can implement the accepted five-food batch
using the exact mapping manifest.

Read:
- `docs/family-food/first-russian-food-batch-contract.md`;
- `data/curation/ru-nut-db-step4-semantic-closure/README.md`.

## Step 4 licensed RU-NUT-DB source correction — 2026-09-22

PR80 remains the docs-only Step 4 Contract Gate.

The user supplied a signed FIC license plus the original corpus archive. The
source-authority blocker is cleared for the pinned electronic `RU-NUT-DB`
snapshot; do not treat Book2002 as production numeric authority.

Exact FIC records are codes 1150,1187,1184,1204,66 with DB indices
252,126,69,254,103.

User decision: DB126 `Морковь свежая красная` creates new
`CARROT_RED_RAW`; it must not reuse generic `CARROT`. The five-food batch is
3 reuse + 2 create (`CARROT_RED_RAW`, `RICE_GROATS`).

The archive shows RU-NUT-DB and Book2002 values differ, especially rice, so they
must not be merged.

The next blocker is scientific field semantics, not rights:
`carbh` definition unresolved; hidden field bindings unresolved; source zero
semantics unresolved.

Do not seal a 13-row sparse vector yet because the seal is immutable. First
complete the bounded mapping closure, then implement the one-UoW five-food batch.

Read:
- `docs/family-food/first-russian-food-batch-contract.md`;
- `docs/family-food/fic-nutrition-license-receipt.md`.


## Step 4 first Russian food batch contract gate — 2026-09-21

Accepted main: `0ee9e5a3335e876d5a1de6a2c32ea245efe8e5e6` (merged PR79).
Current branch: `docs/step4-first-russian-food-batch-contract`.

Step 3 transactional publication is accepted. Current work is docs-only Step 4A.

Candidate batch is exactly five Book2002 records:
`SUGAR`, `CARROT`, `CABBAGE_GREEN`, `BEET`, and new
`RICE_POLISHED_DRY`.

The contract freezes:

- identity reuse/new-rice decisions;
- explicit ATOMIC versions 2/2/2/1/1;
- all profiles non-current;
- 60 retained source cells / 37 positive V2 values;
- source-native carbohydrate → V2 `CARBOHYDRATE_AVAILABLE`;
- below-detection → no numeric row;
- ash/organic acids → source-only evidence;
- one atomic five-food batch transaction;
- a new batch-orchestration seam because Step 3 `publish()` currently owns and
  commits its own UoW; Step 4 must reuse a transaction-neutral bundle operation
  and commit all five once;
- no migration/schema change.

Source-authority update: accepted repository evidence still says
`BLOCKED_PENDING_RIGHTS_REVIEW`, but on 2026-09-21 the user explicitly stated
that they possess permission. Treat the remaining gate as permission
evidence/scope review, not an assumption that permission is absent. Runtime/data
publication starts only after the permission is inspected and an authority receipt
records the applicable use/distribution scope.

Read:
`docs/family-food/first-russian-food-batch-contract.md`.

Do not publish numeric Book2002 values, change current profiles, or start Step 5
automatically.


## Step 3 transactional V2 publication runtime — 2026-09-21

Accepted main: `e5466121e4958cf4fb95ba9041d1c7926daab17e` (merged PR78).
Current branch: `feat/transactional-nutrition-publication-v2`.
Delivery PR: #79.

Read the merged contract first:
`docs/family-food/transactional-nutrition-publication-contract.md`.

Runtime implementation is bounded to publication mechanics only. Key seams:

- generic complete-profile `add()` remains historical V1 behavior;
- Step 3 uses a dedicated `add_unsealed()` writer inside its publication UoW;
- V2 persisted evidence uses `FFO_NUTRIENT_VALUE_EVIDENCE_V2`; V1 JSON/decoder
  remains unchanged;
- existing or replayed V1 seals cannot be rebound to V2;
- Step 3 profiles are always non-current;
- vector values are inserted before the immutable V2 seal; ATOMIC follows the
  readable seal; commit occurs once;
- exact replay is zero-write; authoritative conflicts/partial state fail closed;
- legacy CompositionCalculator remains V1-pinned; V2 transformation applicability
  remains Step 7.

No migration/schema change, Book2002 numeric publication, rights decision,
Russian food batch, target table, methodology persistence, recipes, Planner,
Gate1, Shopping, API/UI or AI work is included.

After PR79 final review/merge, stop before Step 4. Do not publish a Russian food
batch automatically.


## Step 3 transactional publication contract gate — 2026-09-21

Accepted main: `5343734e620c9f36d24aad54320c2196588b004d` (merged PR #77).
Current branch: `docs/step3-transactional-publication-contract`.

The user accepted the new pre-implementation process. This branch contains no
runtime/schema/data publication. It freezes the Step 3 contract before code.

Critical preflight finding: generic complete-profile repository insertion
automatically creates a V1 vector seal. Since one profile can have only one
immutable seal, Step 3 requires a specialized reviewed profile writer that
persists the profile/observations without legacy V1 bootstrap. Existing generic
behavior must remain unchanged.

No new migration is expected: 0034 supports partial profiles, 0035 supports
versioned nutrient values/seals, and ATOMIC Composition already references the
sealed profile. If implementation later needs a schema change, stop.

Two further preflight boundaries are frozen:

- the current vector reader decodes historical V1/FDC-shaped provenance; Step 3
  must add source-neutral V2 provenance decoding without fabricating FDC fields
  or rewriting V1 evidence; `source_nutrient_nbr` becomes optional legacy/source
  metadata for V2 while historical V1 reads retain their exact value;
- legacy CompositionCalculator intentionally reads V1 definitions. Step 3 must
  not make it V2-aware. V2 ATOMIC validation uses the version-aware vector reader
  and NutritionMethodologyService; transformation applicability remains Step 7.

Read:
`docs/family-food/transactional-nutrition-publication-contract.md`.

After this contract PR is reviewed/merged, do not start runtime implementation
without the next explicit authorization. Step 4 production food publication and
source-use decisions remain separate.


## Nutrient Registry V2 handoff — 2026-09-21

Accepted base: PR76 merge `011f4b74abd29f7b5ec77ab0f15998f781f43c43`.
Current branch: `feat/nutrient-registry-v2-adapters`.

Step 2 owns versioned nutrient identity and adapters only. V1 remains immutable;
V2 uses `(registry_version, code)`, adds RE/NE/tocopherol-equivalent concepts
and requires explicit method provenance for V2 source-native calculations.
Existing Composition retention lookups stay V1-pinned.

Migration: `0035_versioned_nutrient_registry`; reserved 0033 remains unused.
No product publication, source-rights decision, target-table publication or
Planner/API/UI switch is in scope.

After final review/merge, stop before step 3 transactional publication.

## PR76 final verification trigger — 2026-09-20

Final task-local corrections are complete: historical regression jobs restore
full Git history for provenance tests, and the current-table guard now includes
`food_nutrition_profile_observations`. No production/domain semantics changed in
these last corrections.

The next `Partial nutrition profiles` workflow run on this exact head is the
final acceptance target. After it, do not modify the branch; record review
evidence only in the PR.

## Partial nutrition profile storage handoff — 2026-09-20

Accepted base: PR75 merge `33659866348bbc56d705bb764bb3c864c2cce0be`.
Current branch: `feat/partial-nutrition-profiles`.

This is plan step 1 only. Partial profiles persist SQL NULL plus immutable source
observation state/literal/method/locator; they remain non-current for the legacy
selector and intentionally have no automatic V1 vector seal. Existing complete
profiles and pinned vector/composition history must remain unchanged.

Schema work is `0034_partial_nutrition_profiles`; reserved
`0033_recipe_template_catalogue` is not consumed. Future 0033 must be appended
after accepted 0034 in the explicit migration list to preserve existing exact
prefix histories.

Required final verification: focused domain/repository/migration/vector tests,
populated upgrade + failure rollback + backup restore/re-upgrade, full backend and
full launcher regression, AI disabled.

Do not start registry/adapters (plan step 2) until this PR is reviewed/merged.

## PR75 Russian methodology sync — 2026-09-20

PR74 is accepted at `4c9598b623b9042924bb1f8d864c56d3d0a407c4`; PR75 has been
synchronized with that main state.

The user explicitly confirmed authorization for the PR75 Russian methodology
implementation and explicitly approved
`RU_SOURCE_NATIVE_PUBLISHED_ZERO_ESTIMATE_V1`. The policy is opt-in only:
below-detection provenance and unknown detection limit remain, interpreted zero
is estimated, and it is not exact-zero/allergen/default-Planner authority.

PR75 trial evidence is now bound to accepted PR74 input/verification receipts and
nonnumeric profile reviews. A numeric-free CI receipt owns merge-review evidence;
the earlier external byte-identical trial claim is not required for acceptance.
Source reuse remains blocked and no canonical profiles are imported.

After PR75 review/merge, schema/profile persistence, registry publication,
source-use approval, target-table publication and Planner/API/UI enablement remain
separate gated work.

## Preserved pre-PR74-sync Russian methodology receipt — historical

The following block records the original PR75 branch state before PR74 merged.
Its base/status, local A/B-trial and “PR74 not presumed merged” wording are
superseded by the PR75 synchronized section above. It is historical evidence only.

### Original Russian methodology layer — 2026-09-20

User approved Russian method support and broader compatibility adaptation.
Base a9472c2a0bb0534b70b41c541aa0ac9b4cb26ba0. New policy layer and internal
services preserve V1 rather than relabel its USDA/NASEM semantics.
322 focused/regression tests passed; SQLite vector/ATOMIC read tested.
Independent audits caught held-observation provenance and energy partition issues;
fixed with explicit held state, original evidence receipt, basis/form checks and
reviewed disjoint energy partition requirement.

Five locked book profiles:25 core observations,50 evaluations;5 source-native
available carbs accepted per policy,3 unknowns in strict mode,3 explicitly marked
zero estimates in alternate mode. Two final trial files byte-identical. Numeric
trial stays in local deliverables/ru-methodology-trial-v1-final.json outside Git.
No source profiles imported, no automatic Russian norm table enabled.

Read docs/family-food/russian-nutrition-methodologies.md before continuation.
The next implementation dependencies (already directionally authorized) are
partial-profile persistence/registry, accepted target tables and method selection
in Planner/API/UI. Source rights and scientific mapping remain separate gates.
PR74 is not presumed merged. No new migration or live production write.


## PR73 blocker corrections handoff — 2026-09-20

User authorization is now explicit for fixing PR73 blockers and completing this
bounded evidence review only. The package remains non-production: 211 exact
source-input annotations, four route holds, no canonical IDs, no nutrient
equivalence, no retention authority.

The validator now fails closed on form authority, mapping semantics/flags and the
separate School2022 §1.5 heat-loss policy. Current-focus is merge-stable. Reverify
the final head; after review/merge stop for separate authorization before any
DC2 production publication payload.

## Exact source-input mappings — 2026-09-20

Base PR72 merge: `0322d0a74a0edf53802adc394446011a7d8acc06`.
Continuation authorized by user. Prepared211 school2022 occurrence annotations:
sugar89, carrot69, cabbage24, beet12, rice17. Two suspicious source rows hold
four execution routes. Source evidence confirms polished rice and puree20%.
Immutable corpus0.3.0 and previous packages preserved. No runtime publication.

Verification: eight offline tests (including adversarial authority, mass,
exception, route, summary and manifest changes); two full builds byte-identical.
Independent source audit identified exceptions and validator gaps, now covered.
See [package](../data/curation/dc2-exact-input-mappings/README.md).
Next: review this bounded overlay, resolve nutrient method/reuse and exact
canonical profile equivalence before a separately reviewed production payload.
The user has not yet answered the nutrient-method choice; no approval inferred.


## PR72 review hardening handoff — 2026-09-20

The first DC2 source/form review remains evidence-only. Review blockers were
addressed by expanding CI input triggers, adding fail-closed committed-output
validation for input receipt/routes/summary, and making current-focus valid
before and after PR72 merge. Reverify the final head; after review/merge stop
pending explicit authorization for a production DC2 publication payload.

## Current update — first DC2 batch review, 2026-09-20

PR71 merged at `9b1d5c73da4f1d779336a35e0e7e2c2d32363e85`.
The user authorized the next source/form review stage. See
[first-batch review](../data/curation/dc2-first-batch-review/README.md) and
[current focus](current-focus.md), which supersede older execution statuses below.
25 group decisions account for1532 occurrences and24 source-record candidates;
14 profiles have earlier visual evidence. No publication, accepted canonical
mapping or nutrient-policy change. The next exact blockers are documented in
publication-decisions.md; do not restart source discovery without reading them.


Updated: `2026-09-20`.

## Current handoff after PR70 merge

Accepted main is `b9768984392982bd05d28fc0f7793453fe8378b5` (merged PR #70).
PR #71 is being synchronized and verified for the user-authorized merge.
See [current focus](current-focus.md), [integration plan](../docs/family-food/corpus-v03-integration-plan.md)
and [reconciliation package](../data/curation/corpus-v03-reconciliation/README.md).

The PR70 recovery artifacts and source input hashes are preserved. Its final
head `514c6b1` has the same tree as the historical `c23227b` input pin used by
v0.3 reconciliation. Generated historical merge-status flags remain capture
metadata, not live project state. All current statuses are owned by this section
and current-focus; the receipt below is historical.

Reconciliation retains 547 crosswalk records, 2693 food occurrences and 46
review queues, all without production publication. Exact form/source/rights/
nutrient decisions are next proposed work, not automatically authorized.
After the authorized PR71 merge, stop. DC2/DC3/DC4, Gate1 and PR9 remain open.

## Preserved pre-merge PR70 handoff receipt — historical

The following text records the earlier delivery state. Its REVIEW-READY and
not-merged wording is superseded by the current handoff above.

### Original handoff

Updated: `2026-09-20`.

## Accepted base and governance

Accepted current main:

`d8c76a64483e3d5814e702be33c12cbe2e144160`

Current bounded operation:

`DATA-CORPUS-V1 / DC1 — Source authority + coverage inventory` — ACTIVE under
Issue #67.

Recovered implementation is REVIEW-READY on:

`data/data-corpus-v1-dc1`

Accepted SQLite migration head remains:

`0032_meal_plan_serving`

Reserved future migration remains:

`0033_recipe_template_catalogue`

DC2, DC3, DC4, Gate1-CLOSE and PR9 are NOT STARTED.

## Recovery checkpoint

The inconsistent pre-rebuild GitHub package is preserved for recovery under:

`data/curation/data-corpus-v1-dc1/recovery/pre-rebuild-b7bc19e8881ddc90/`

The exact original pre-rebuild bytes remain available at commit
`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`. The copied recovery README was
later whitespace-normalized only for repository Docs verification; its metrics/data
content was not changed.

Known pre-rebuild commit:

`b7bc19e8881ddc90b95bd8d13c75e72ee4623295`

Recovery checkpoint completion commit:

`0c311848341da397b837abf12fcca4b442de8acd`

The old package is historical evidence only.

## Root cause recovered

The interrupted package consumed a text-rendered spreadsheet view as if it were
the complete v22.5 relationship-row shards.

The raw source contract requires:

`1550 + 1550 + 1550 + 1529 = 6179` rows.

Direct raw-XLSX parsing recovers all 68 candidate families and 991 relevant
source relationship/calculation rows. Missing rendered rows had previously been
misinterpreted as zero ingredient demand.

## Rebuilt package

Evidence package:

`data/curation/data-corpus-v1-dc1/`

Generator and validator:

- `scripts/build_data_corpus_v1_dc1.py`;
- `scripts/validate_data_corpus_v1_dc1.py`.

Current reconciliation:

- 68 candidate families;
- 991 relationship/calculation rows;
- 96 external ingredient identities;
- 33 accepted existing/alias mappings;
- 63 identities requiring later DC2-level closure if pursued;
- full accepted PR39 input contract: 350 recipe rows / 363 ingredient identities;
- structural source-Variant split: 31 one / 37 multiple;
- safe publication-branch split: 5 simple / 63 review-required;
- 33 existing mappings have exact current USDA FDC profile provenance identified,
  but recipe-form suitability remains review-required;
- 28 non-existing identities have a preferred source-family search target;
  exact source presence, record identity and form compatibility remain unverified;
- 35 identities are blocked on identity/form semantics before exact authority
  assignment.

The previous 95-demand result is not retained: it depended on unsafe
display-name deduplication. In particular `ING-0014` and `ING-0069` remain
separate identities; the v22.5/v22.13 label conflict is explicit evidence debt.

## Compatibility limits

For all 68 candidates:

- v22.5 calculation rows match v22.13 `CalcRows`;
- accepted PR #39 mapping aggregates are reproduced;
- v22.5 Variant counts match v22.13 `VariantBlocks`.

Full row-level relationship equivalence is not claimed because the exact
v22.13 row-nutrient shards were unavailable during recovery.

Recorded blockers include:

- 20 candidates with additional v22.13 non-calculation relationship rows;
- 20 used identities with v22.5/v22.13 label differences;
- 63 candidate families needing variant/choice/optional/boundary/compatibility/
  semantic review;
- all 33 existing profiles still need exact recipe-form suitability review;
- preferred source-family search targets are not evidence that a compatible
  source record exists and are not exact-record authority closure;
- assortment gaps in the preserved 68-family funnel.

## Verification evidence

Current review-fix verification:

- exact GitHub package audit: PASS for 68 candidates / 991 relationships /
  96 demands / 33 existing mappings / 63 non-existing mappings;
- safe branch split: 5 simple / 63 review-required;
- full PR39 input metadata: 350 / 363;
- current production nutrition seed metadata: 183 rows and exact Git blob identity;
- DC2/DC3 batch partitions: exact coverage with no overlap;
- authority assignment state present for all 96 demands;
- package SHA-256 manifest: PASS for all 11 generated artifacts;
- committed adversarial harness:
  `scripts/test_data_corpus_v1_dc1.py`.

Current heavy verification applies to the generator/generated-package bytes
finalized on branch head `78c81ff7f55c6878be9112b75f766c78fe73c639` before the following state-only
finalization commits:

- exact repository PR39 mapping inputs restored byte-for-byte: PASS;
- exact production nutrition seed restored byte-for-byte: PASS;
- raw XLSX generator source-hash enforcement: PASS;
- build A: PASS;
- build B: PASS;
- validator A/B: PASS;
- 15-case adversarial suite: PASS;
- build A == build B: PASS.

The generated package at `78c81ff...` is the output of the current generator.
Subsequent finalization commits are state-only and do not alter the generator or
generated package bytes covered by this evidence. Final-head automatic package
verification rechecks checksums, validator behavior and the formatted
15-case adversarial suite.

Raw source XLSX bytes are operator-managed external evidence. Exact required
filenames/hashes are recorded in `source-artifacts.json`. The ZIP/container
hash is diagnostic only; canonical source identity is the exact file set plus
per-file SHA-256. The raw source ZIP must not be uploaded as a GitHub Actions
artifact in this public repository. Automatic PR CI runs package verification;
full raw-source rebuild is manual `workflow_dispatch` against explicit
`target_ref`, using the temporary authenticated URL only through
`DC1_SOURCE_BUNDLE_URL`.

Final Docs verification and automatic package verification must be GREEN on the
review head before merge.

## Scope boundary

No production FoodIngredient/Nutrition/Composition/RecipeVersion publication,
schema, migration, Planner, API or UI change belongs to this PR.

## Stop condition

After DC1 review/merge, stop.

Do not automatically start DC2, DC3, DC4, Gate1-CLOSE or PR9.
