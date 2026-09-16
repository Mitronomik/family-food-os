# Current focus

Updated: `2026-09-16`.

## Accepted repository state

- PR6 / PR6-CLOSE = COMPLETE.
- PR #34–#44 = MERGED.
- Exact accepted `main` after PR #44: `25a496977d19666f812f76792a68aee92732186e`.
- Current accepted SQLite migration head: `0030_recipe_source_corpus`.
- Future RecipeTemplate schema reservation remains `0031_recipe_template_catalogue`.
- R1 / R2 / R3 / R4 remain COMPLETE AS BLOCKED RESEARCH.
- R1-21 and R1-23 remain INDIVIDUALLY_READY; accepted ready count remains 2/3.
- Assembly A remains BLOCKED and is described operationally as `HUMAN_EVIDENCE_BLOCKED__2_OF_3`.
- OPEN Assembly-A gates remain `family_count`, `optional_role`, `verified_substitution`.
- Assembly B, `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` and PR7+ remain NOT STARTED.

## Accepted recovery decision

Merged PR #44 (`RECIPE-ASSEMBLY-A-RECOVERY-B`) established that no retained
source-only alternate removes the accepted complete-variant kitchen-evidence
requirement.

Accepted recovery order:

1. `USSR82-267 — Суп-пюре из моркови или репы` remains the preferred third-family recovery candidate.
2. `R1-05 — Local Harvest Bake` remains the first fallback if measured 267 verification fails.
3. `USSR82-369 — Грибы в сметанном соусе` remains the second fallback.

No acceptance criterion, architecture rule or production authority was changed.
No additional source-only recovery PR for 267 is recommended.

## Current authorization boundary

No runtime/data-promotion implementation is automatically authorized by merging
PR #44.

The preferred next evidence path remains the measured protocol from PR #43:

`data/curation/v22-13-267-kitchen-a/kitchen-verification-protocol.json`

Required human evidence includes:

- exact carrot-branch execution measurements;
- exact turnip-branch execution measurements, including blanching;
- measured 20 g raw-rice garnish transformation/process binding;
- service/evaluation with and without the optional garnish.

Repository agents may validate and retain supplied measurements, but may not
claim physical execution, invent measured values or infer successful variant
testing from source publication.

## Next-step rule

- measured PR #43 protocol evidence supplied → separately authorize `V22-13-267-KITCHEN-B`;
- measured 267 execution fails → separately authorize `R1-05-RECOVERY`;
- no measured evidence available → remain BLOCKED.

`V22-13-267-PROFILE-B` remains deferred until the kitchen decision.
Do not start Assembly B, Meal Pattern Catalogue support, PR7, PR8, Retail, AI,
Auth or bulk data promotion automatically.
