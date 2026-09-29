# R1 Cross-Corpus Consumed-Nutrition Feasibility Review

**Status:** docs-only research / authority review
**Decision date:** 2026-09-29
**Accepted base:** `03984aae526ddcd7765f6df6f43608bd4ef0e3fa` (merged PR #109)
**Parent:** #99, #109, #67
**Runtime/data publication authorized by this document:** no

## 1. Goal

Determine whether the shortest truthful path to the first Planner-capacity active
R1 production recipes is still confined to the selected USSR82 candidates, or
whether retained cross-corpus evidence shows a materially better authority path.

The review compares:

- the current selected USSR82 R1 candidates;
- retained `ru-school2022` recipe/process evidence;
- retained `RU-MR-2019` / МР 2.4.0162-19 evidence;
- licensed FIC `RU-NUT-DB` food-composition authority.

The review does **not** change the authorized R1 candidate set. Issue #99 currently
defines the selected R1 set, and PR108/PR109 preserve the rule that R2 or another
material sequencing change requires explicit user approval.

## 2. FACT — retained corpus reviewed

Durable source artifact:

`private-library:/FamilyFoodOS/source-artifacts/FamilyFoodOS-corpus-0.3.0-2026-09-20.zip`

Archive SHA-256:

`c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea`

Archive size:

`206692075` bytes.

The review used the retained archive plus current repository contracts. No numeric
authority was reconstructed from an LLM or unpinned web snippet.

The reconciled recipe-source namespaces represented by current retained evidence
are:

- USSR82 — 68 historical candidate families in the current DC1/R1 funnel;
- `RU-MR-2019` / МР 2.4.0162-19 — 214 section-scoped cards;
- `ru-school2022` — 265 source cards in the cross-corpus recipe inventory.

The cross-corpus reconciliation contains 1473 resolved recipe execution routes
across the retained non-USSR82 packages.

Presence in the retained source corpus is evidence only. It is not automatic
RecipeVersion publication authority.

## 3. FACT — FIC is already an accepted source family for production Food Nutrition

The pinned official FIC database snapshot inside the retained corpus is:

- source: `RU-NUT-DB`;
- raw HTML SHA-256:
  `155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d`;
- source records: 3216.

The later project-owner-supplied FIC license receipt supersedes the archive's
older `rights_use_unresolved` status for this pinned electronic database within
the reviewed FamilyFoodOS use scope.

Therefore the cross-corpus review must not treat FIC as globally rights-blocked.

This does **not** make every FIC row an exact FoodIngredient authority
automatically. Exact food/form semantics, nutrient definitions, basis and
publication provenance remain separate review requirements.

## 4. FACT — current selected R1 remains blocked before Planner proof

Accepted R1-B / PR109 state:

- active Planner-eligible R1 RecipeVersions: 0;
- `USSR82-697` is published inactive;
- `USSR82-453` is blocked on V2-compatible exact EGG Composition authority;
- `USSR82-1081` is blocked on V2-compatible exact BUTTER_UNSALTED Composition
  authority;
- `USSR82-467` is blocked on an unquantified required salt amount;
- `USSR82-492` is blocked on an unquantified required salt amount.

PR109 additionally proves that `USSR82-697` has a category-I/category-II source
identity conflict and no accepted exact consumed-Nutrition authority.

Closing those local blockers does not by itself prove that the resulting cooked
recipes can be represented by the current
`RECIPE_COMPOSITION_NUTRITION_V1`.

## 5. FACT — School2022 has much stronger material readiness than current R1 uses

The retained `ru-school2022` resolved execution set contains:

- 471 resolved routes total;
- 420 non-clinical routes;
- 377 non-clinical routes with material execution ready;
- 376 non-clinical routes with procurement mass ready;
- 0 non-clinical routes marked Nutrition-ready by the retained closure package;
- 0 non-clinical routes marked production-ready by that retained closure package.

This is a critical distinction:

> the retained corpus already understands how to execute hundreds of recipes
> materially, but the historical closure package did not establish production
> consumed-Nutrition authority for them.

The recurring blocker is not lack of recipe text alone. It is the authority
boundary between input food Composition and the consumed prepared output.

## 6. FACT — School2022 contains useful no-thermal control cases

The retained source explicitly contains simple one-component cards with no
thermal treatment and exact source output equal to the selected source net input,
including:

- `53-19з` — butter portion, 10 g → 10 g;
- `54-1з` — sliced semi-hard cheese, 15/30 g → 15/30 g;
- `54-2з` — sliced cucumber, 30/60 g → 30/60 g;
- `54-3з` — sliced tomato, 30/60 g → 30/60 g;
- `54-4з` — sliced sweet pepper, 30/60 g → 30/60 g.

The already accepted Step 9/10 butter path proves that a no-thermal,
identity-compatible ingredient can be calculated through the existing canonical
V2 Recipe Nutrition path when exact FoodIngredient/Composition authority exists.

The other simple cards are **not** automatically authorized by mass equality.
Their exact FoodIngredient/form basis still needs review. For example, retained
cucumber evidence records a cultivation/form ambiguity rather than silently
equating the source row with a specific FIC cucumber form.

**Decision:** these cards are useful control cases for identifying whether a new
Recipe Nutrition authority model is genuinely needed. They are not sufficient
Planner-capacity by themselves.

## 7. FACT — School2022 also carries source-published nutrient reconciliation

The retained School2022 package contains:

- 976 `published_nutrient_reconciliation` rows;
- covering 244 recipe IDs;
- all 976 rows marked `source_valid`;
- all 976 rows carry `do_not_reapply_retention=true`;
- all 976 rows carry
  `not_independent_food_profile_calculation=true`.

This evidence is stronger than the USSR82 recipe 697 evidence because it preserves
source-published prepared-recipe nutrient calculations/reconciliation.

However the current DATA-CORPUS-V1 and Russian normative recipe contracts still
treat source-declared recipe Nutrition as reference/cross-check evidence unless a
separate canonical contract grants it calculation authority.

Therefore this package does **not** currently authorize a RecipeVersion Nutrition
result merely because the published values reconcile.

## 8. FACT — RU-MR-2019 is not the short path for household R1-C

The retained recipe-closure interpretation currently contains 1002
`RU-MR-2019` resolved routes.

Under that retained interpretation:

- non-clinical routes: 0;
- material-execution-ready non-clinical routes: 0;
- Nutrition-ready routes: 0.

This is a property of the current retained interpretation, not a claim that the
214 source cards are intrinsically unusable.

Using RU-MR-2019 for ordinary household Planner capacity would first require a
separate applicability/source-scope review. It is therefore not the shortest
current R1-C path.

## 9. DECISION — the bottleneck is now a reusable consumed-Nutrition authority seam

The cross-corpus evidence changes the framing.

The project does **not** primarily have a "USSR82 chicken loss-factor problem".

The reusable product problem is:

```text
source-backed RecipeVersion
+ exact FoodIngredient input Composition
+ source-backed preparation/process/output truth
→ exact consumed RecipeVersion Nutrition
→ Planner exact-energy readiness
```

Current authority modes are incomplete for that full space.

Three materially distinct cases exist:

### A. Identity-preserving / no-thermal preparation

Example class:

- portioning;
- slicing;
- source net input equals source output;
- no nutrient-changing process is established.

This class may be compatible with the existing
`RECIPE_COMPOSITION_NUTRITION_V1` **only after** exact food/form/mass semantics
prove that the bound input Composition is the consumed edible basis.

Mass equality alone is not authority.

### B. Applicability-aware transformed Composition

Example:

- boiling;
- baking;
- frying;
- meaningful yield/loss/process transformation.

This path requires exact source-applicable yield/retention authority and a
versioned Recipe Nutrition calculation path able to consume transformed
Composition.

No implicit 100% retention is allowed.

### C. Exact source-backed prepared-output Nutrition

School2022 shows that source-published prepared-recipe nutrient calculations may
exist.

This is distinct from a reusable FoodTransformation retention profile.

Promoting such source output Nutrition to production authority would require a
separate reviewed versioned calculation/publication contract that proves:

- exact card/variant/output identity;
- nutrient-definition compatibility with `RU_NUTRIENT_REGISTRY_V2`;
- output basis and portion mass;
- source calculation semantics;
- no double application of retention;
- immutable provenance/replay;
- compatibility with Planner/Serving consumption.

No such contract is authorized by this review.

## 10. DECISION — do not build a per-recipe retention workaround

The retained corpus demonstrates that the same consumed-Nutrition boundary
appears across a large prepared-recipe set.

Therefore creating a special transformation/retention implementation only to
activate `USSR82-697` would risk solving the wrong abstraction.

A reusable Recipe Nutrition authority decision should be made before large-scale
cooked RecipeVersion activation.

This does not weaken PR109. `USSR82-697` remains correctly inactive.

## 11. DECISION — current R1 sequencing is preserved

Issue #99 still owns the selected R1 set.

This review does **not** authorize replacing or extending that set with
School2022 cards.

The following remain true:

```text
successful R1-C
→ R2/R3
```

unless the user explicitly approves another sequencing/candidate-set decision.

Cross-corpus research may inform that decision; it cannot make it implicitly.

## 12. Candidate-path comparison

| Path | Food input authority | Recipe/process authority | Consumed-Nutrition authority | Current disposition |
| --- | --- | --- | --- | --- |
| USSR82 selected cooked R1 | partially closed / local blockers remain | strong for selected branches | missing under current production contracts | blocked |
| School2022 no-thermal controls | promising FIC-backed candidates | strong | may fit current V1 only after exact edible/form review | feasibility controls only |
| School2022 cooked routes | FIC can close many input foods | strong; hundreds material-ready | source reconciliation exists but is reference-only under current contract | promising, new authority contract likely |
| RU-MR-2019 | unresolved for household path | retained source cards exist | unresolved | not shortest path |

## 13. Reviewed recommendation

The best next architecture/product operation is **not** a runtime publication PR.

The next bounded operation should be a docs-only Recipe Nutrition authority
Contract Gate that defines the permitted consumed-Nutrition modes needed for
production RecipeVersion activation.

That gate should cover:

1. exact identity-preserving/no-thermal eligibility under the existing V1
   calculation;
2. the separate transformed-Composition authority mode;
3. the separate source-backed prepared-output Nutrition mode;
4. exact calculation-version identities and provenance pins;
5. unknown propagation;
6. no implicit retention;
7. no raw→cooked fallback;
8. Planner/Serving consistency;
9. replay/conflict/history preservation;
10. adversarial acceptance for at least one simple no-thermal control and one
    cooked source-evidence case.

**Important:** implementing a School2022 production batch after that gate would
still require an explicit candidate-set/sequencing decision if it changes the
authorized R1 set.

## 14. OPEN QUESTION — user sequencing decision

Cross-corpus evidence supports two legitimate continuations:

### Path 1 — preserve the exact current R1 set

Continue with one of the already selected USSR82 candidates, but use the reusable
consumed-Nutrition Contract Gate rather than creating a recipe-specific shortcut.

### Path 2 — explicitly widen R1 to a bounded cross-corpus pilot

Amend the R1 candidate set to include a small reviewed School2022 pilot chosen for
Planner capacity and authority closure.

A reasonable future pilot shape would be:

- one no-thermal control;
- one breakfast candidate;
- one main candidate;

with exact FIC input authorities and source-backed process/output evidence.

This review does not choose Path 2 on the user's behalf.

## 15. R1-C impact

Before this review:

- active Planner-eligible R1 RecipeVersions: 0;
- exact-energy-ready active R1 RecipeVersions: 0.

After this docs-only review:

- active Planner-eligible R1 RecipeVersions: 0;
- exact-energy-ready active R1 RecipeVersions: 0.

R1-C remains blocked.

The value of the review is that the blocker is now identified as a reusable
cross-corpus consumed-Nutrition authority problem rather than a single USSR82
recipe defect.

## 16. Non-goals

This review does not authorize:

- Recipe activation;
- Food/Nutrition publication;
- YieldModel / RetentionProfile / TransformationApplicability publication;
- a new Recipe Nutrition runtime version;
- schema/migration changes;
- changing the R1 candidate set;
- R2/R3;
- DC4 / Gate1-CLOSE;
- Shopping/Prep/Retail/API/UI/Auth/PostgreSQL/AI.

## 17. Sequence after review

```text
PR109 merged
→ cross-corpus consumed-Nutrition feasibility review
→ review/merge this docs-only finding
→ explicit sequencing/candidate-set decision if needed
→ Recipe Nutrition consumed-authority Contract Gate
→ separately authorized runtime/data publication
→ active Planner-capacity production recipes
→ R1-C production Planner proof
→ R2/R3
→ DC4 / Gate1-CLOSE
→ PR9 Shopping
```

Do not interpret this review as permission to activate source-corpus recipes
directly from source-declared nutrient totals.
