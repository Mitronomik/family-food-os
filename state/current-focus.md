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

## Current bounded direction

Continue ordinary DATA-CORPUS-V1 delivery through bounded **DC2/DC3 production
publication batches** using the already accepted corpus and the infrastructure
delivered through Steps 4–10.

Recipe-specific validation remains required where relevant:

- exact FoodIngredient/form compatibility;
- deterministic Nutrition authority;
- transformation/yield/retention only when actually required;
- Recipe classification;
- current Planner compatibility;
- provenance/rights;
- activation suitability.

These checks belong inside the bounded publication batch unless they reveal a
genuinely new architecture/data-authority decision that requires a separate stop.

Do **not** introduce a new per-recipe preflight/contract milestone by default.

## Active programme sequence

```text
DATA-CORPUS-V1 accepted foundation
→ bounded DC2/DC3 production batches
→ DC4 corpus readiness audit + Gate1 consumption
→ GATE1-CLOSE
→ PR9 Shopping Engine
```

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
