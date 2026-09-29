# Current focus

Updated: 2026-09-30.

## Accepted state

PR111 / R1 cross-corpus candidate-universe decision is merged into `main` at:

`e350e747a9c6e06e74b2cd450637c25a442c8749`.

R1 candidate selection may draw from all retained/reviewable DATA-CORPUS-V1
source families. Source diversity is not an acceptance criterion.

## Current bounded operation

**R1-D — CORPUS-WIDE PLANNER ADMISSION AND RECIPE CLOSURE.**

Issue:

`#112`.

Branch:

`data/r1d-planner-capacity-candidate-audit`.

The current implementation removes the Planner active-only visibility blind spot:

- Recipe Catalogue exposes all published recipes for admission review;
- latest SOURCE_VERIFIED RecipeVersion can be inspected regardless of activation;
- Planner classifies every published recipe as eligible or blocked;
- current blocker taxonomy:
  - INACTIVE;
  - NO_VERIFIED_VERSION;
  - ROLE_UNSUPPORTED;
  - NUTRITION_UNAVAILABLE;
  - EXACT_ENERGY_UNAVAILABLE;
- blocked recipes remain non-selectable;
- existing generation semantics are not weakened;
- no migration/schema change is introduced.

The School2022 butter portion remains a technical no-thermal control only. It is
not a product target because `meal_type=other` is not currently usable by Planner
meal roles.

## Product direction

Stop advancing capacity one hand-picked recipe at a time.

Target pipeline:

```text
retained recipe sources
→ production Recipe Catalogue
→ Planner admission for every published verified RecipeVersion
→ explicit blocker per recipe
→ blocker-based production batches
→ active Planner-eligible catalogue
→ R1-C proof
→ R2/R3 catalogue depth
→ Gate1-CLOSE
```

Next after Phase A verification:

1. build a corpus-wide machine-readable closure inventory across USSR82,
   School2022 and accepted RU-MR-2019 scope;
2. group recipes by shared blocker rather than source loyalty;
3. close the highest-leverage Planner-capacity batches;
4. introduce new Nutrition architecture only when a real batch proves a concrete
   missing seam.

## Hard boundaries

Do not:

- bulk-activate recipes without exact production authority;
- treat source-corpus presence as RecipeVersion authority;
- infer raw→cooked Nutrition;
- infer implicit retention;
- promote source-declared recipe totals without an accepted authority path;
- weaken unknown != zero;
- start Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI;
- start R2/R3 before successful R1-C.
