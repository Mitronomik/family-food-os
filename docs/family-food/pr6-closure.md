# PR6 closure decision

Decision: **PR6 COMPLETE**. **PR6-CLOSE — COMPLETE.**
Reviewed baseline: `3caa95e636c02e8f34657b1b6c885f646451114c`, fetched `origin/main`
and merge of [PR #29](https://github.com/Mitronomik/family-food-os/pull/29).
PR6-DATA-B2-B2-REDESIGNED is MERGED / delivered. Migration remains
`0029_food_composition_core`. This is a review/evidence publication, not a
production implementation. The closure result is submitted for human PR review.

## Decision and authority limits

The Nutrition bounded context is deterministic, versioned, provenance-aware and
fail-closed under its approved interfaces. All 20 closure criteria pass. The
[blocker register](../../data/curation/pr6-close/blocker-register.json) has no
milestone blockers and retains the reviewed boundary interpretations.

This PASS does not make the 30 FNS recipes consumer-ready or Planner candidates.
It does not permit INCOMPLETE origins, execute the 40 estimates, promote the five
deferred forms, solve yield gaps, complete Recipe Assembly or pass Gate 1.
Nutrition provides usable known calculations and explicit refusals/unknowns;
complete catalogue/kitchen coverage remains a separate sequenced obligation.

**Legacy v1 and normalized authority remain distinct.** VECTOR-B explicitly
preserves accepted `FAMILY_FOOD_NUTRITION_V1` values, including source-reported
zeros. `NutritionService` returns that versioned contract, its exact input
provenance, optional separation and uncertainty. It does not claim a normalized
full nutrient vector or exact measured food composition. `FOOD_COMPOSITION_V1`
uses only sealed normalized vectors and exposes requested-set availability,
explicit mass states and pinned replay. It never substitutes legacy fields.
These are existing result/config boundaries, not a new closure-only convention.

For SALT and WATER, direct 100 g v1 requests return five numeric zeros and
`COMPLETE_WITH_WARNINGS`, with `ESTIMATION_STATUS_UNKNOWN`. Their valid sealed
vectors contain zero values and composition replay is `INCOMPLETE`. Current
recipe contributions retain the same intentional distinction: **185 nutrient
occurrences on 57 rows / 15 foods**, including **179 required occurrences**.
All carry explicit source-estimation uncertainty. The direct-service inventory
finds this on 17 foods. The audit proves every available matching composition
keeps those normalized nutrients UNKNOWN. These are legacy observations, not
new exact-zero authority or silently completed vectors.

No new unified API or automatic recipe/vector migration is required by the
accepted contracts. A downstream consumer must select the existing contract it
needs and honor its version, availability, mass basis and uncertainty. Treating
v1 numbers as exact normalized/cooked output would violate that contract. The
separate normalized reader/calculator already fails closed; no absent runtime
guard needs to be deferred to Recipe Assembly to obtain this PASS.

## Baseline and evidence

PR29 merged at `2026-09-12T07:42:03Z`. Its accepted head is
`8a80ce26e7155ab17a5623d07294fbfd1124d9bf`; both full trees equal
`f953fb4d3693c4eead77fad301342359dc8bd206`. Backend, launcher, frontend, data and
existing scripts also equal tested implementation
`d0a238ce32193d5884d61ee384d5eb7f242bcaed`. The accepted **3826 passed with
AI_ENABLED=false** regression is historical evidence, not a new execution.
Closure adds only documentation, state, read-only tooling and closure evidence.

The [JSON package](../../data/curation/pr6-close/README.md) owns measured evidence;
this document owns the written decision submitted for human review. The script reconstructs only a
disposable accepted production seed and applies the merged populated-0029 B2-B2
upgrade. It does not open a user database, fetch sources or repair data. Its
measurements do not infer milestone acceptance from test success.

| Current measurement | Reproduced result |
| --- | ---: |
| Recipes / ingredient rows | 30 / 189 (185 required, 4 optional) |
| APPROVED_EXACT / APPROVED_NO_CONVERSION | 71 / 23 |
| REVIEW_REQUIRED_ESTIMATE / BLOCKED | 35 / 60 |
| INCOMPLETE / CONDITIONAL | 29 / 1 |
| COMPLETE / COMPLETE_WITH_WARNINGS recipes | 0 / 0 |
| Current non-executable estimate usages | 40 (35 review + 5 blocked) |
| Required food union / total catalogue | 82 / 185 |
| Current-food ATOMIC composition / no composition | 63 / 19 |
| All sealed profile versions / composition versions | 188 / 63 |
| Stale current assessment/profile bindings | 0 |

All 30 current versions and all 82 referenced foods are classified, including
optional usages. Required assessment counts are also retained separately. The
51-code unknown inventory is a coverage inspection, **not** a new required nutrient
set. A sealed vector has 0–37 values in this food union; a seal certifies complete
snapshot publication, never complete nutrient coverage.

## One-by-one closure criteria

Each PASS is scoped to the current canonical contract and the explicit limitations
below. The result is a reviewed decision, not an inference from passing tests.

| # | Criterion | Result | Evidence and limit |
| --- | --- | --- | --- |
| 1 | FoodIngredient calculation deterministic | **PASS** | Direct scaling repeats with private Decimal context; focused domain tests. Determinism does not certify normalized authority. |
| 2 | RecipeVersion calculation deterministic | **PASS** | All 30 current results repeat identically; required failures propagate null totals, optional contributions remain separate. |
| 3 | Member target/config deterministic and versioned | **PASS** | 16 adult/child sex/PAL fixture outputs retained; focused tests cover growth, birthdays, missing inputs and versions. |
| 4 | AI_ENABLED=false sufficient | **PASS** | All executed runtime audits/tests use AI_ENABLED=false. No network calculation or AI dependency. |
| 5 | Decimal rounding/config deterministic | **PASS** | Private precision 80, HALF_UP, six-place result boundary; domain, member and composition context-independence tests pass. |
| 6 | Nutrition provenance retained | **PASS** | Profiles, exact source versions, recipe source hashes, assessments and measure keys retained. Null retrieval instants remain null. |
| 7 | NutrientVector registry/provenance/seals immutable and replayable | **PASS** | 188 seals read; all 185 old seals unchanged. Only approved profile selector metadata retires. All 51 definitions requested in composition replay; corruption/immutability tests pass. |
| 8 | Unknown nutrient differs from zero | **PASS** | None remains distinct from Decimal zero. Complete sealed reads return None for absent codes; missing composition contributions propagate unknown. The retained legacy/normalized boundary is evaluated separately in criterion 9. |
| 9 | Unresolved source zero cannot silently acquire exact authority | **PASS** | PASS in the explicitly separate versioned contracts: normalized imports hold unresolved zeros and composition returns UNKNOWN, never legacy fallback. All 185 retained v1 zero occurrences carry ESTIMATION_STATUS_UNKNOWN; direct results are COMPLETE_WITH_WARNINGS. They remain source-reported legacy values, not certified exact normalized zeros. |
| 10 | FoodIngredient form identity authoritative | **PASS** | Separate approved frozen forms; all five deferred forms absent. Nine directly affected current rows have no mass/nutrients; no parent fallback executes. |
| 11 | Mass states not silently equated | **PASS** | Composition state continuity is enforced; row assessments block known gross/edible/form mismatches. v1 required-input totals are not cooked mass or cooked totals. |
| 12 | Composition replay pins immutable profile/vector versions | **PASS** | All 63 ATOMIC compositions replay against explicit profile IDs; all 60 old compositions unchanged. No mutable profile fallback. |
| 13 | Missing yield/retention explicit unknown | **PASS** | Three named rows remain blocked with null mass and nutrients. Production has no yield/retention facts; focused missing-yield/retention tests verify unknown propagation. |
| 14 | Row-specific exact mass or fail closed | **PASS** | 71 exact and 23 direct-g assessments; all other current row masses unavailable. No global recipe density fallback. |
| 15 | Estimate cannot execute as exact authority | **PASS** | 40 current usages = 35 review-required + 5 blocked; all have null mass/nutrients. Three independently superseded usages do not relabel old evidence. |
| 16 | Stale assessment/profile binding fails closed | **PASS** | Zero stale current links; focused stale/review replacement tests pass. Old pinned profile remains diagnostic after invalidation. |
| 17 | Historical truth remains replayable | **PASS** | All old rows preserved; 35 pre-upgrade captured RecipeVersion input/config snapshots replay, all 37 post-upgrade snapshots replay. RecipeVersion ID alone is expressly not historical replay; consumers must retain exact snapshots/refs. |
| 18 | Downstream distinguishes authoritative/usable from incomplete/blocked without guessing | **PASS** | Existing result types/configurations distinguish FAMILY_FOOD_NUTRITION_V1 input arithmetic from FOOD_COMPOSITION_V1 requested-set authority. v1 exposes status, nullable nutrients, optional separation, exact inputs and source uncertainty. Composition exposes per-nutrient availability, mass state and pinned replay. No automatic conversion between them exists; no additional guard is required for the approved scope. |
| 19 | Unresolved current data cannot enter Planner/Serving as authoritative | **PASS** | All unresolved required current rows return null mass/nutrients and INCOMPLETE totals; optional blockers are excluded. The normalized path never falls back to legacy values. Later consumers must honor those existing contracts, source uncertainty and explicit versions; ignoring them would violate the interface, not reveal missing Nutrition truth. |
| 20 | RU/data obligations partitioned across PR6, Assembly and later gates | **PASS** | Technical nutrition authority is PR6-owned. Russian display, market readiness, kitchen verification and gate counts remain separate explicit obligations; none waived or newly reclassified. |

## Current corpus and retained blockers

The 29 INCOMPLETE recipes are safely bounded technical evidence: required
unavailable contributions produce null totals, not partial authoritative sums.
Their incompleteness alone does not block Nutrition milestone closure. They
remain unusable as complete downstream nutrition origins until their required
facts are resolved in separately authorized work. Diagnostic known contributions
do not rescue the total.

`WIC1_OVERNIGHT_OATS_CINNAMON_APPLE:v2` is CONDITIONAL. Its two required rows
(milk and oats) produce the accepted v1 required-input subtotal: 112.007500 kcal,
5.434475 g protein, 2.099300 g fat and 17.956850 g carbohydrate; fiber is unknown.
Three optional rows are excluded, including the blocked APPLE row. This is usable
under the explicitly limited v1 input-subtotal contract; it is not a selected
apple dish, normalized full-vector origin, verified cooked output or consumer
candidate. No new consumer eligibility enum or policy is created here.

All **40 estimates** have null executable mass and all five contribution values
null. They consist of 35 REVIEW_REQUIRED_ESTIMATE plus 5 BLOCKED usages. PR29's
three independent exact supersessions retain every old estimate record; there
is no confidence threshold, density assumption, default piece mass, 1 ml = 1 g
rule, same-category substitution or estimate-to-exact relabelling. Those blocks
are sufficient for the mass-authority criterion; accepting estimates is not a
prerequisite to this milestone closure.

The **five deferred forms** remain absent from production. Nine direct mismatch
rows are enumerated with source/review references in closure-evidence.json:
APPLE_PEELED (salsa), LEMON_JUICE (five recipes), ORANGE_JUICE (pear/orange sauce),
PASTA_COOKED (pasta salad), SPINACH_BABY (spinach/apple salad). Each is BLOCKED,
with null mass and nutrients despite the existing parent food/profile. Parent
fallback cannot execute in these rows. Other APPLE usages and source choices
remain blocked as separately recorded. These promotions are not reopened.

The three **yield/edible-basis cases** retain their exact current identities:

- SNAP4_BRAISED_CHICKEN_SPINACH / CHICKEN_THIGH: gross bone-in mass versus edible profile.
- SNAP4_SPANISH_FRITTATA / POTATO: pre-peeling purchase mass versus peeled edible profile.
- WIC4_BUTTERNUT_SOUP / BUTTERNUT_SQUASH: whole mass before discarded parts.

Their existing runtime FOOD_FORM_MISMATCH / IDENTITY_MISMATCH assessments block
all mass/nutrients; PR29 evidence additionally records YIELD_EVIDENCE_REQUIRED.
No runtime yield enum is invented. No numerical yield, retention or implicit
100% factor is supplied. These existing blocks are sufficient for PR6 safety;
solving their data is not a closure prerequisite. Composition tests separately
prove missing transformation yield/retention propagates unknown. Recipe input
sums cannot be re-labelled cooked totals, even when v1 arithmetic succeeds.

## Historical replay and provenance

The audit compares every pre-existing table/row through the actual PR29 upgrade.
Only the accepted three profile and seven assessment current markers retire.
All 185 old seals and 60 old compositions retain their facts; all 188 final
seals and 63 final compositions are read, with replay over all 51 registry codes.
All 35 pre-upgrade RecipeVersion input/config snapshots reproduce their original
results after the upgrade; all 37 final snapshots also reproduce. Exact row,
profile, evidence and configuration objects are retained in that replay.

This does not invent a historical service lookup: `recipe_version(id)` reads
current profiles/reviews and may now signal stale history. The canonical contract
already says RecipeVersion ID alone is insufficient. Later persisted origins
must retain the exact input/config references or captured coherent result. All
immutable source rows remain retrievable; the audit uses preserved snapshots
and independently checks the underlying historical facts.

Original recipe/profile source identities, versions, hashes and review evidence
remain intact. Closure performs no new external source/market retrieval. Missing
source retrieval instants remain null; accepted hash evidence is not relabelled
as a fresh inspection. The B1, B2-A, B2-B1, VECTOR-A/B, Composition, PR28 and PR29
packages retain their historical meanings and are unchanged.

## Member target and configuration foundation

The original PR6 exit criterion remains included: 16 independent published-equation
fixtures cover adults and children, both supported sexes and all four activity
levels. The executed target tests also cover birthdays, under-3 failure, the
18→19 equation boundary, growth/fiber bands, leap-day policy, absent/unsupported
sex/activity/anthropometry, nonpositive EER, unchanged reference EER for goals,
versioned coefficients/config and caller-Decimal-context independence.

Reference targets always carry REFERENCE_ESTIMATE. They are reproducible reference
calculations, not measured individual needs or diagnosis/treatment. No therapeutic
claim, calorie-deficit policy, pregnancy/lactation inference or medical mode is
introduced. Exact version identifiers and synthetic fixture outputs are in the
closure evidence; no personal/health records are used.

## Ownership and downstream contracts

PR6 owns technical nutrition authority, deterministic formulas, exact row mass
binding, explicit unknowns and immutable profile/vector/composition provenance.
No PR6-owned blocker is transferred into Assembly by this decision.

Recipe Assembly A/B remain NOT STARTED. Following review/merge of this closure and separate authorization, they may rely on canonical FoodIngredient identities, valid sealed
vectors, explicit immutable composition versions, unknown propagation, exact
mass evidence where approved and Nutrition fail-closed results. They may not
assume blocked FNS rows are valid, estimates executable, raw/cooked equivalent,
yield 100%, deferred forms present, or RU_READY foods kitchen-verified recipes.
A recipe/assembly integration must preserve exact inputs and distinguish input
nutrition from evidenced transformed output; it cannot invent missing truth.

Later PR7 may reuse the existing Nutrition calculations and immutable origin
provenance, honoring their existing versioned uncertainty and mass-basis contracts.
It must never reinterpret INCOMPLETE/blocked origins as authoritative, use
partial totals, include unresolved optional rows, or infer history from an
origin ID alone. No Planner/Serving implementation is required in PR6-CLOSE.

PR28 RU readiness is retained as a dated reviewed classification: 60 RU_READY
and 22 NOT_READY records in the current 82-food union. PR29 separately upgrades
nutrition profiles/compositions for mayonnaise, oats and tomato; it does not
silently rewrite the original RU review. Both facts are retained in each inventory.
All referenced foods have Russian display text. This proves food display only,
not Russian recipe titles/steps, market completeness or kitchen verification.

Recipe Assembly owns separately authorized Russian templates/rules, culinary
familiarity, curated substitutions and kitchen verification. Consumer/admin
publication must satisfy the Russian-language contract without English fallback.
Later Gate 1 still requires its 3 household fixtures, 30 verified recipes and
80+ foods; broader Data Readiness retains 50–80+ recipes, 100% required coverage
and its broader food target. Existing FNS technical counts do not pass these gates,
and Assembly counts do not silently replace recipe counts. No gate is weakened.

## Verification and stopping point

The [execution record](../../state/progress.md#pr6-close--closure-verification)
contains commands, exact results and scope/link checks. Required audits pass;
the one-by-one contract review, rather than test counts, establishes **PR6 COMPLETE**. The audited
runtime/data/test tree is unchanged, so the accepted PR29 full regression is
reused proportionally. No new full 3826-test run is claimed.

The next roadmap candidate is **RECIPE-ASSEMBLY-A — NOT STARTED** and requires
separate explicit authorization after reviewed closure. Recipe Assembly B and
PR7 remain NOT STARTED. No automatic next operation and no autonomous merge.
