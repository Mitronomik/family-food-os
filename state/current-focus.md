# Current focus

Updated: 2026-09-26.

## Accepted state

PR96 / Step 10-B is merged into `main` at:

`7443f56b856184db6ddb040b9d68425db9f8d41a`.

Accepted Step 10 result:

```text
composition-backed V2 Recipe Nutrition
→ neutral consumption projection
→ Planner exact-energy readiness
→ planner-v0.3
→ MealPlan / Serving nutrition consumption
```

The Step 9 School2022 butter Recipe remains inactive.

## Sequencing correction after PR96

PR97 is closed as **SUPERSEDED / DO NOT MERGE**.

Reason:
PR97 incorrectly treated historical DC1 statuses as if they were still the current
unresolved project state, without applying later accepted Steps 4–10 decisions.

Do not re-open accepted corpus/source-foundation work merely because old DC1
artifacts contain historical blocker/status fields.

Accepted durable corpus/source foundation includes the later recorded archive:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`.

## Current bounded state

**PR98 restores programme sequencing only. It does not authorize a specific
production batch.**

The next action after PR98 is merged is to select and explicitly authorize one
concrete bounded DATA-CORPUS-V1 operation under Issue #67.

No DC2 or DC3 production batch starts merely because PR98 merges.

The broader programme direction remains bounded DC2/DC3 production publication
using the already accepted corpus/source foundation and the infrastructure
delivered through Steps 4–10.

Recipe-specific validation remains required where relevant:

- exact FoodIngredient/form compatibility;
- deterministic Nutrition authority;
- transformation/yield/retention only when actually required;
- Recipe classification;
- current Planner compatibility;
- provenance/rights;
- activation suitability.

Recipe-specific validation belongs in the bounded publication batch when that
batch uses existing accepted publication paths and authority contracts.

If a batch requires a new or changed authoritative publication path, immutable
authority contract, schema/migration boundary or cross-context rule, stop before
runtime implementation and create the repository-required docs-only
Implementation Contract Gate.

Do **not** introduce a new per-recipe preflight/contract milestone by default when
existing accepted paths/contracts are sufficient.

## Dependency-driven programme sequence

```text
accepted DATA-CORPUS-V1 contract/source foundation
→ dependency-ready DC2 food/form/Nutrition publication where required
→ DC3 RecipeVersion publication only after its required dependencies are accepted
→ DC4 corpus readiness audit + Gate1 consumption
→ GATE1-CLOSE
→ PR9 Shopping Engine
```

A DC3 batch must not bypass unresolved required DC2 food/form/Nutrition
dependencies.

Do not combine unrelated DC2 food expansion and DC3 recipe publication in one PR
merely for convenience.

The DATA-CORPUS-V1 baseline is still incomplete; Issue #67 remains active until
its corpus exit criteria are satisfied.

PR9 remains NOT STARTED until Gate1-CLOSE.

## Hard boundaries

No automatic:

- Gate1-CLOSE;
- PR9 Shopping;
- Retail;
- AI authority;
- Auth/PostgreSQL;
- generalized Data Ingestion Platform.

One bounded publication PR = one reviewable production-data goal.

Selecting the next batch and authorizing its implementation are explicit scope
decisions; agents must not choose an unspecified production batch autonomously.
