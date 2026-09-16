# RECIPE-ASSEMBLY-A-RECOVERY-B — recovery decision after USSR82-267 source boundary

**Status:** research/recovery decision; human evidence blocker identified
**Reviewed:** 2026-09-16
**Accepted base:** `c428899e703f2bf5addd5f910d53ad40617244c5` (PR #43 merged)

## Goal

After PR #43 established that the source-only path for `USSR82-267 — Суп-пюре
из моркови или репы` cannot close the remaining kitchen gates, determine whether
the accepted evidence already contains a smaller alternate route to the third
Recipe Assembly A family.

This operation does not lower any gate. It compares only the strongest retained
recovery paths and decides whether another source-only PR is justified.

## FACT — fixed Assembly A boundary

Accepted individually-ready families remain:

- `R1-21` — oatmeal, only the reviewed published 100-serving water batch;
- `R1-23` — hard-boiled eggs, only the reviewed published 100-serving method.

The target remains exactly three production RecipeTemplate families. Collective
gates still require an optional role and a verified curated substitution. Neither
accepted ready family supplies those two capabilities, so the recovery family
must supply the missing collective evidence unless a separately authorized change
reopens one of the accepted families.

`family_count`, `optional_role`, and `verified_substitution` therefore remain
OPEN until a third family passes the accepted evidence contract.

## FACT — candidate A: USSR82-267

`USSR82-267` is the most-developed recovery path.

Already established across PR #40–#43:

- source-backed 1000 g carrot and turnip branches with exact branch masses;
- explicit optional-rice source semantics;
- strong cross-edition culinary-family corroboration;
- exact identity/form decisions for rice groats, 3.2% pasteurized milk and
  parsley root;
- acceptable profile-source candidates for polished rice and parsley root;
- normative crumbly-rice process evidence.

Remaining blockers are evidence-type blockers, not another missing-source search:

1. complete carrot and turnip branches do not have retained evidence showing
   both selected variants were successfully executed/tested under the accepted
   substitution gate;
2. the 20 g raw-rice garnish still needs an exact measured small-vessel
   transformation/process binding;
3. generic production profile authority for exact 3.2% pasteurized milk remains
   open, but PR #42 intentionally deferred implementation until kitchen viability
   is known.

PR #43 already defines the required measured protocol. No additional source-only
claim can substitute for its execution.

## FACT — candidate B: R1-05 Local Harvest Bake

`R1-05 — Local Harvest Bake` is the strongest retained alternate family.

Positive retained evidence:

- direct USDA/FNS source and rights PASS in the accepted R1 review;
- source-specific kitchen/standardization scope PASS for the published 6-serving
  base recipe;
- RU familiarity, ordered process and source-template scope PASS;
- exact source weights for butternut squash, beet and sweet potato;
- exact olive-oil mass evidence;
- dried parsley is explicitly optional and already has an exact retained mass.

However it is not a source-only escape from the collective gates:

- the source says `Kosher salt or Iodized salt`, but accepted FamilyFoodOS
  evidence does not establish the two complete salt branches as a
  kitchen-verified replacement rule;
- salt mass/form remains unresolved in the retained candidate;
- minced garlic remains without accepted exact mass;
- pan-release spray is a required process input with unresolved form/mass;
- butternut squash and beet still lack accepted candidate composition paths in
  the retained R1 decision.

Current USDA/ICN recipe-standardization guidance reinforces the same evidence
boundary: standardized recipes are tried/adapted/retried for repeatability, while
ingredient modification belongs to verification/evaluation rather than inheriting
automatic equivalence from an `OR` label.

R1-05 therefore offers a clean optional role but still requires new
data/mass work plus retained variant verification. Switching to it would add
work without removing the human-evidence blocker.

## FACT — candidate C: USSR82-369

`USSR82-369 — Грибы в сметанном соусе` is the strongest v22.13 alternate with
source-level optional semantics outside recipe 267.

The normative source explicitly allows the dish to be prepared with sautéed
onion, `10–20 g` per portion, with output increased accordingly. It also contains
multiple mushroom forms/alternatives.

The retained MAP-A result nevertheless classifies this candidate as
`PROCESS_REVIEW`, not production-ready. Its path still includes:

- exact optional quantity rule selection from a source range;
- fresh/dried/marinated/salted mushroom form branches;
- sour-cream sauce as a composite/process output;
- exact sour-cream/margarine form authority;
- no retained complete-variant kitchen evidence establishing the mushroom
  alternatives as a FamilyFoodOS verified substitution.

This route therefore introduces more catalogue/composite/process debt than 267
and still does not remove the same human-evidence requirement.

## FACT — other retained optional-role leads

The accepted MAP-A inventory also contains optional-role leads such as
`USSR82-251`, `USSR82-309`, `USSR82-310`, `USSR82-317`, and `USSR82-671`.
They were not promoted to a deep recovery path because they either have materially
larger identity/composite/unresolved debt, lack a substitution lead, or both.

Strict-raw substitution leads such as milk soups, fried potatoes, baked
potato/egg/tomato dishes, `Макаронник`, fried eggs and egg-powder omelet do not
simultaneously provide the required optional-role evidence.

Within the accepted retained evidence there is therefore no smaller source-only
candidate that closes both missing collective capabilities.

## DECISION

`RECIPE-ASSEMBLY-A` is now classified as:

`HUMAN_EVIDENCE_BLOCKED__2_OF_3`

This is not a new architecture state or a relaxed milestone. It is a more precise
description of the existing BLOCKED result.

Decision:

1. keep `USSR82-267` as the preferred third-family recovery candidate;
2. stop additional source-only PRs for 267;
3. do not start `V22-13-267-PROFILE-B` before measured kitchen evidence;
4. retain `R1-05` as first fallback and `USSR82-369` as second fallback if 267
   later fails measured verification;
5. do not start Assembly B, Meal Pattern Catalogue support or PR7.

Reason: switching candidates now increases production-data debt without eliminating
the evidence type that blocks `verified_substitution`.

## OPEN QUESTION — execution ownership

The next missing evidence cannot be manufactured by repository research.

The PR #43 protocol requires physical execution and retained measurements for:

- the exact carrot branch;
- the exact turnip branch;
- the 20 g raw-rice garnish transformation;
- service/evaluation with and without the optional garnish.

An authorized human operator must perform or provide those measurements. ChatGPT,
Codex and source research must not claim that execution occurred.

After measured evidence exists, a separately authorized
`V22-13-267-KITCHEN-B` may validate and retain it. If the measured result fails,
the recovery sequence should move to `R1-05` rather than reopen broad donor search.

Changing the accepted kitchen/substitution gate instead would be an explicit
architecture/acceptance decision and is not authorized by this recovery PR.

## Architecture / data / API / UI / migration impact

None.

- no runtime/domain/service/repository/API/UI change;
- no schema or migration;
- no FoodIngredient/Profile/NutrientVector/Composition mutation;
- no production seed/import;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- migration head remains `0030_recipe_source_corpus`;
- future RecipeTemplate reservation remains `0031_recipe_template_catalogue`.

## Verification

Verification tier: research/data-curation + state.

Required before review-ready:

- deterministic JSON/checksum integrity;
- candidate decision consistency against accepted R1/R2/MAP-A/PR40–PR43 evidence;
- no production authority promotion;
- `git diff --check`;
- staged scope / whitespace audit;
- repository-relative Markdown links;
- stale-state check against merged PR #43 and current `main`.

Full backend regression is not required because runtime, persistence, schema and
production data do not change.

## Acceptance criteria

- no source `OR` is reclassified as kitchen-tested substitution;
- no proposed kitchen protocol is represented as executed;
- the alternate-candidate comparison uses retained evidence and preserves its
  blockers;
- the operation identifies whether candidate switching removes the evidence-type
  blocker;
- Assembly A remains 2/3 unless actual gates pass;
- downstream Assembly B / PR7 remain not started;
- the next required human evidence is explicit and reproducible.

## Follow-up

No further source-only recovery operation is recommended.

Next project action is conditional:

- measured kitchen evidence available → authorize `V22-13-267-KITCHEN-B`;
- measured 267 evidence fails → authorize focused `R1-05-RECOVERY`;
- no measured evidence available → remain BLOCKED; do not consume additional PRs
  pretending research can replace physical verification.

A later `V22-13-267-PROFILE-B` is justified only after the 267 kitchen decision.
