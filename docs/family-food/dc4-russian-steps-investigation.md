# DC4 Correction A — seven RecipeStep Russian-language findings

**Status:** EVIDENCE CONFIRMED / publication path NOT authorized
**Issue:** #166
**Accepted main:** `c521e6d89a4d9fcc2900804ff7e05de66f14b093` (merged PR #165)
**Owner:** Recipe Catalogue / curated source publication
**Required sequence:** A1 review → immutable publication Contract Gate → separately reviewed runtime/data correction → DC4 rerun

## FACT — direct source investigation

The seven `RUSSIAN_STEPS_NOT_READY` findings are **genuine language violations** in
the accepted R3-A frozen production seed, not scanner-only false positives.

Authoritative retained evidence:

- `data/curation/r3a-school2022-main-batch/publication-specs.json`,
  `recipes.<canonical_code>.trusted_recipe_seed.version.steps`;
- `backend/app/seed/r3a_school2022_main_batch.py`, which validates exact frozen
  process bindings and source evidence;
- `docs/family-food/russian-language-contract.md`;
- `docs/family-food/dc4-corpus-readiness-report.md`, merged DC4 screening.

All seven rows below contain an English engineering fragment in an otherwise
Russian consumer step. English explanatory metadata is appropriate for the
internal review evidence, but these expressions should not leak into a
consumer-facing `RecipeStep`.

| RecipeVersion family code | Frozen source-step location | English fragment | Disposition |
| --- | --- | --- | --- |
| `SCHOOL2022_54_1R_COD_CUTLET` | step 3 | `source total` | TRUE_VIOLATION |
| `SCHOOL2022_54_2R_PINK_SALMON_CUTLET` | step 3 | `source total` | TRUE_VIOLATION |
| `SCHOOL2022_54_3R_POLLOCK_CUTLET` | step 3 | `source total` | TRUE_VIOLATION |
| `SCHOOL2022_54_10R_PINK_SALMON_TOMATO_VEGETABLES` | step 3 | `total` | TRUE_VIOLATION |
| `SCHOOL2022_54_11R_POLLOCK_TOMATO_VEGETABLES` | step 3 | `total` | TRUE_VIOLATION |
| `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS` | step 1 | `cooking-fat` | TRUE_VIOLATION |
| `SCHOOL2022_54_8M_STEAMED_BEEF_MEATBALLS` | step 3 | `total`, `process placement`, `per-step gram split` | TRUE_VIOLATION |
| `SCHOOL2022_54_11M_BEEF_PILAF` | step 2 | `total` | TRUE_VIOLATION |

The violation covers seven distinct RecipeVersions and eight affected steps.

## Proposed semantics-preserving wording (not yet production authority)

The following are *review candidates*, not a new source recipe or an approved
published RecipeVersion.

| Frozen English phrase | Proposed consumer-facing Russian phrase |
| --- | --- |
| `source total` in a statement that quantity is not distributed over steps | `общий расход по исходной карте` |
| `total` for water or oil quantities | `всего` / `общий расход` |
| `cooking-fat` | `жир для приготовления` |
| `process placement` | `назначение воды по технологическим операциям` |
| `per-step gram split` | `распределение массы в граммах по этапам` |

Preservation examples:

- Fish cutlets: preserve exact source total oil/water and the reviewed
  water-instead-of-fish-broth branch. Do not invent operation-level quantities.
- Tomato-fish recipes: preserve precisely `5,3 г масла` as *one source total*,
  without inventing a split between sautéing and greasing.
- Steamed beef meatballs: preserve `12 г воды` assigned to moistening the rack,
  not invented bread-soaking water. Preserve the source uncertainty.
- Beef pilaf: preserve `313 г воды` total, no invented per-operation split,
  the `5–10 минут` stage and `160 °C 30–40 минут` oven stage.

The full frozen steps and their source commitments, not the abbreviated table,
remain the semantic baseline.

## Immutable provenance / publication blocker

`RecipeVersion` is immutable production truth, and `R3-A` publication
validates frozen seed/source review contracts. Therefore editing the old step
in place, mutating hash-pinned `publication-specs.json`, altering source
evidence, or overwriting an active version is **not authorized**.

Before any runtime/data patch, a *separate, docs-only Implementation Contract
Gate* is required. The gate must establish:

1. exact old version IDs and source/version/card commitments and the permitted
   new immutable version chain;
2. what consumer-language correction may change, and what source facts cannot;
3. whether the current RecipeVersion append/activation policy can safely
   supersede the old version without altering accepted R3-A replay semantics;
4. prepared-output energy authority treatment for the new version (no hidden
   re-use without accepted same-source binding);
5. freshness/idempotent replay/conflict/rollback/failed-publish behavior;
6. how `Planner.compose_candidate_admission()` and active recipe eligibility
   reconcile to 51 after the transition;
7. adversarial checks on source/provenance, Russian steps, historical versions,
   chosen branch, `UNKNOWN` nutrients and no migration `0043`.

**DECISION PROPOSED (not yet approved):** create a bounded immutable
RecipeStep-language correction gate, not an in-place seed edit. Avoid a
separate automatic-translator feature and arbitrary new recipe publication.

## Acceptance for A1 investigation

- Seven codes individually traced to exact frozen step text — DONE.
- Exact offending English phrases recorded — DONE.
- True violation vs heuristic false positive classified — DONE:
  seven true violations, no false positives among these seven.
- Source semantics to preserve and safe replacement candidates identified — DONE.
- Publication change authority — **NOT GRANTED**; next bounded operation is
  a docs-only immutable correction contract gate.

## Non-goals and stop rule

No runtime changes, existing version mutation, seed/source tampering, new
Nutrition/FoodIngredient authority, Planner changes, schema/migration, Gate1-CLOSE
or PR9. This investigation PR is evidence-only. Stop for independent review.
