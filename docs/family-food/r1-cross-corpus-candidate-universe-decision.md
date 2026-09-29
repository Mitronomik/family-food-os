# R1 Cross-Corpus Candidate Universe Decision

**Status:** explicit user-approved sequencing/candidate-set decision
**Decision date:** 2026-09-29
**Accepted base:** `076de7026a48809d68f314189455b29f35e32a04` (merged PR #110)
**Supersedes:** the assumption that R1 production candidate selection is confined to the seven USSR82 recipes from Issue #99
**Preserves:** #99 product goal, #109 authority boundary, #110 cross-corpus findings, successful R1-C before R2/R3

## DECISION

R1 is no longer restricted to the narrow USSR82 candidate set.

The R1 candidate universe may draw from **all retained, reviewable recipe source
families available to DATA-CORPUS-V1**, including at minimum:

- USSR82;
- `ru-school2022`;
- `RU-MR-2019` / МР 2.4.0162-19;
- later retained source families accepted under the same corpus contract.

This is a candidate-universe decision, not blanket publication authority.

A source family enters R1 selection only through the normal DATA-CORPUS-V1
authority path:

```text
retained source evidence
→ exact card/variant selection
→ exact FoodIngredient/form resolution
→ authoritative Nutrition/Composition
→ consumed-Nutrition authority
→ immutable RecipeVersion publication
→ explicit activation
→ Planner eligibility
```

## Selection rule

R1 batches should be selected for the shortest **truthful reusable production
path**, not by source loyalty.

Selection should optimize for:

- Planner capacity across materially different meal patterns;
- ordinary household relevance;
- breakfast/main/other role coverage;
- exact source quantities and output semantics;
- exact FoodIngredient/form closure;
- reusable FIC/other accepted Nutrition authority;
- minimal unresolved consumed-Nutrition ambiguity;
- variety and ingredient overlap useful to later Shopping/Pantry/Prep.

USSR82 has no preferred status merely because it was the first R1 source used.

Likewise, School2022 or another corpus does not receive preferred status merely
because it has more structured evidence.

## Preservation

This decision does not:

- activate any recipe;
- convert source-declared Nutrition into production truth;
- weaken unknown != zero;
- weaken raw != cooked;
- bypass FoodIngredient identity/form review;
- authorize implicit retention;
- authorize Recipe Nutrition runtime changes;
- start R2/R3;
- start DC4/Gate1-CLOSE/Shopping;
- invalidate historical USSR82 R1 work.

Historical #99/#101/#104/#108/#109 receipts remain valid for what they actually
proved. Only the **candidate-set restriction** is superseded.

## Immediate next bounded operation

Create the docs-only **Recipe Nutrition Consumed-Authority Implementation Contract
Gate** identified by PR #110.

That gate must support selection across the widened candidate universe and must
distinguish:

1. identity-preserving/no-thermal preparation;
2. applicability-aware transformed Composition;
3. exact source-backed prepared-output Nutrition.

After the gate is accepted, choose a small cross-corpus production batch based on
authority readiness and Planner-capacity value, then publish/activate only through
separately authorized runtime/data PRs.

No runtime/data publication starts from this decision alone.
