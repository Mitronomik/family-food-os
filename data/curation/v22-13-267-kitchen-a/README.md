# V22-13-267-KITCHEN-A — bounded kitchen/process evidence review

**Status:** research/evidence + proposed measurement protocol; no kitchen execution
**Reviewed:** 2026-09-16
**Accepted base:** `c9fcaa782a9cb6b1a48d877fb251f3ee69cb4e7d` (PR #42 merged)
**External checkpoint:** `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

## Goal

Resolve the two remaining candidate-specific non-profile blockers for
`USSR82-267 — Суп-пюре из моркови или репы` without weakening the accepted
Recipe Assembly A gates:

1. decide whether source evidence is sufficient to mark the complete carrot and
   turnip branches as a verified substitution;
2. determine whether the optional 20 g raw-rice garnish can be bound to a
   deterministic cooked-rice process/output at the selected scope.

This operation does not physically cook food. It distinguishes source/process
evidence from the retained measurement evidence that is still required.

## Result

**Recipe 267 remains a strong recovery candidate but is not individually ready.**

- carrot ↔ turnip remains `verified_substitution = OPEN`;
- source-level rice optionality remains established, but the production
  `optional_role` gate remains OPEN;
- Assembly A remains BLOCKED at 2/3 individually-ready families;
- no production FoodIngredient/Nutrition/Composition/RecipeTemplate delta is
  justified by this review.

The bounded source search did not recover a completed candidate-specific record
that separately proves successful execution of both exact complete branches.
Repeated normative/professional publication is strong culinary-family evidence,
but the accepted gate does not allow us to promote a source `OR` into a tested
FamilyFoodOS substitution.

## FACT — exact selected soup scope

The selected scope remains recipe 267, column II + water, published output
1000 g:

| Input | Carrot branch | Turnip branch |
| --- | ---: | ---: |
| principal vegetable | carrot 320 g | turnip 360 g |
| parsley root | 10 g | 10 g |
| onion | 20 g | 20 g |
| wheat flour | 20 g | 20 g |
| rice groats, optional garnish input | 20 g | 20 g |
| butter | 20 g | 20 g |
| milk | 150 g | 150 g |
| egg | 10 g | 10 g |
| water | 700 g | 700 g |
| published dish output | 1000 g | 1000 g |

The turnip branch has an additional 1–2 minute blanching step. The 1982 Ministry
collection, the 1973 Ministry collection and the 1987 professional culinary
textbook all preserve the carrot-or-turnip family.

## DECISION — carrot ↔ turnip kitchen gate

The evidence is sufficient for:

`STRONG_CROSS_EDITION_CULINARY_FAMILY`

It is **not** sufficient for:

`VERIFIED_COMPLETE_VARIANT_SUBSTITUTION`.

The project already requires kitchen evidence to apply to the exact reusable
variant scope. Collection-level standardization, repeated publication and
training assignments do not identify retained successful execution records for
both selected branches.

A teaching assignment found in the bounded search explicitly asks students to
prepare this soup and conduct brakerazh. That is useful evidence that the dish is
treated as a practical training object, but it is a procedure/request, not a
completed test record.

Therefore:

`MEASURED_COMPLETE_VARIANT_KITCHEN_VERIFICATION_REQUIRED`.

## FACT / DECISION — crumbly-rice process

The earlier Ministry collection materially improves the rice decision.

Its normative table for crumbly rice states, per 1 kg raw rice:

- 2.10 L water;
- 28 g salt;
- 180% cooking gain;
- 2.80 kg output;
- 70% moisture with ±1.5 percentage-point tolerance.

The same source also says liquid demand changes with vessel size/shape: large
kettles need less liquid, while small/low vessels need more. Therefore the table
supports the transformation family and the scaling method, but it does not make
the 20 g household garnish an exact deterministic rule without a retained
small-vessel measurement.

Recipe 203 in the same collection independently gives:

- 72 g raw rice + 151 g water → 200 g cooked crumbly rice;
- 90 g raw rice + 189 g water → 250 g cooked crumbly rice.

Its process allows fat during cooking but does not require fat for the base rice
transformation. This removes the earlier assumption that every candidate rice
producer must consume additional fat and therefore double-count recipe 267's
butter.

For protocol planning only, the 1 kg table arithmetically corresponds to 20 g
raw rice → 42 ml base water, 0.56 g salt and 56 g theoretical output. These are
**not production values**: the source itself makes the small-vessel water amount
equipment-dependent and gives output/moisture tolerance.

Decision:

`INSTITUTIONAL_CRUMBLY_RICE_PROCESS_ESTABLISHED__EXACT_20G_BINDING_BLOCKED`.

## Proposed measured verification

`kitchen-verification-protocol.json` defines the minimum future retained test:

- execute the exact published 1000 g carrot branch;
- execute the exact published 1000 g turnip branch, preserving the blanching
  step;
- record all actual input/output masses, equipment and process deviations;
- prepare a separate 20 g raw-rice garnish without added fat, recording actual
  water, salt, vessel, cooking time and cooked output;
- evaluate each soup branch both with and without the separate rice garnish;
- preserve the measured record rather than converting the source table into a
  guessed household yield.

The retained soup quality criteria are the professional-source criteria:
homogeneous puree, no flour lumps/unpureed pieces or surface film, thick-cream-like
elastic consistency, appropriate colour and a delicate moderately salted taste
characteristic of the selected vegetable.

This protocol is **proposed, not executed** in this PR.

## Assembly A impact

| Gate | KITCHEN-A result |
| --- | --- |
| `family_count` | OPEN — recipe 267 is still not individually ready |
| `optional_role` | OPEN — source optionality is clear; exact cooked-garnish binding still needs measurement |
| `verified_substitution` | OPEN — both complete variants still need applicable retained kitchen evidence |

Accepted ready families remain only R1-21 and R1-23.

## Decision

Do not spend `PROFILE-B` implementation work on recipe 267 yet.

The source/profile research has reached the point where another source-only PR is
unlikely to close the accepted kitchen gates. The next useful action depends on
whether measured human kitchen execution is available:

- if available: `V22-13-267-KITCHEN-B` executes and retains the two complete
  soup branches plus the 20 g rice transformation;
- if unavailable: `RECIPE-ASSEMBLY-A-RECOVERY-B` should stop the 267 path and
  choose the smallest alternate candidate path rather than weakening the gate.

Neither follow-up is authorized automatically by this PR.

## Non-goals

- no physical kitchen execution claimed;
- no FoodIngredient/profile/vector/composition creation;
- no guessed yield or retention;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- no migration/schema/runtime/API/UI change;
- no production seed;
- no change to accepted R1/R2/R3/R4 evidence;
- no Assembly B or PR7 work.

## Files

- `substitution-kitchen-review.json` — complete-branch evidence decision;
- `rice-process-review.json` — institutional rice process and exact 20 g blocker;
- `kitchen-verification-protocol.json` — proposed measured execution protocol;
- `source-manifest.json` — source/rights/use boundary;
- `decision.json` — Assembly-A and next-path decision;
- `checksums.json` — package integrity pins.
