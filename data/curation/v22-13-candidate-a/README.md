# V22-13-CANDIDATE-A — bounded Assembly A candidate recovery

**Status:** research/evidence; no production publication
**Reviewed:** 2026-09-16
**Accepted base:** `2707fab16f003c9942d0eb09edf99c790d98a16f` (PR #39 merged)
**Source checkpoint:** `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

## Goal

Take exactly three candidate leads from the accepted `V22-13-MAP-A` funnel and
attempt to reduce the three still-open Recipe Assembly A evidence objectives
without changing production FoodIngredient/Nutrition/Composition or publishing a
RecipeTemplate/RecipeAssembly.

The candidates are deliberately different:

1. `USSR82-323 — Картофель отварной`: low-debt `family_count` fallback;
2. `USSR82-267 — Суп-пюре из моркови или репы`: primary recovery lead because it
   carries both an explicit optional food role and an explicit source alternative;
3. `USSR82-459 — Яичница глазунья (натуральная)`: secondary low-debt source-choice
   lead for substitution semantics.

R1/R2/R3/R4 accepted evidence remains frozen. The two existing individually-ready
families remain R1-21 and R1-23 only.

## Result

**Assembly A remains BLOCKED at 2/3 individually-ready families.** No collective
gate is marked complete.

| Objective | Candidate-A result | Gate |
| --- | --- | --- |
| `family_count` | A primary recovery path is identified, but no third family is individually ready | OPEN |
| `optional_role` | Recipe 267 explicitly permits omitting the rice garnish and gives exact source input masses where rice is present | OPEN |
| `verified_substitution` | Recipe 267 has carrot-or-turnip and recipe 459 has margarine-or-butter source alternatives, but full-variant kitchen applicability is not established | OPEN |

The important progress is narrower: the research now distinguishes **source
semantics established** from **production gate satisfied**.

## Primary recovery lead — USSR82-267

The 1982 Ministry collection gives three recipe columns for `Суп-пюре из моркови
или репы`. Candidate-A narrows the next recovery work to **column II**, with the
source-authorized **water** branch instead of inventing a broth identity.

Exact source net inputs for this bounded column are:

- carrot 320 g **or** turnip 360 g;
- parsley root 10 g;
- onion 20 g;
- wheat flour 20 g;
- rice groats 20 g;
- butter 20 g;
- milk 150 g;
- egg 10 g;
- broth or water 700 g;
- dish output 1000 g.

Primary source index/text: `https://www.mosculport.ru/templates/kitchen_instr/recipes_master.pdf`.
The source says the rice is used as a crumbly-rice garnish and explicitly states
that the soup may be prepared without rice. That is sufficient to establish the
**source meaning of an optional rice role**. It is not yet a production
RecipeTemplate rule.

The source also gives `carrot OR turnip` with exact different masses. The turnip
branch has an extra blanching step. This is sufficient to establish a source
alternative, but under the already-accepted R2/R3 policy it is **not** a verified
FamilyFoodOS substitution until the two complete variants have applicable
kitchen/form/Composition evidence.

### Identity readiness for the bounded column II + water scope

Already mapped to current FoodIngredient identity:

- `CARROT`;
- `TURNIP`;
- `ONION_YELLOW`;
- `FLOUR_WHEAT`;
- `BUTTER_UNSALTED`;
- `EGG`;
- `WATER`.

Still blocked as exact food/form identities:

- `Крупа рисовая` — MAP-A `FORM_SPLIT_CANDIDATE`; generic rice groats do not prove
  current long-grain `RICE_WHITE`;
- `Молоко пастеризованное 3,2%` — `FORM_SPLIT_CANDIDATE`; do not silently map to
  3.25%, 2% or another current milk;
- `Петрушка (корень)` — `FORM_SPLIT_CANDIDATE`; root is not parsley leaf.

The egg row already has source net mass 10 g, so no piece-to-gram estimate is
needed for the selected source column.

### Process and nutrition boundary

The external checkpoint marks the recipe `READY_RAW`, but retention is not
applied. The optional rice is an input for a **cooked crumbly-rice garnish**. A
production template therefore still needs the correct producer/transformation
binding; raw rice nutrition cannot be presented as cooked garnish output merely
because the input grams are exact.

The collection introduction states that the recipes were recalculated/refined on
the basis of production workups and the collection was approved as a normative
technological document by Order N 310. Candidate-A treats this as positive
collection-level standardization evidence. It does **not** infer that both
carrot and turnip full variants were independently tested as an interchangeable
FamilyFoodOS substitution.

## Secondary source-choice lead — USSR82-459

The same 1982 source gives natural fried eggs with:

- columns I/II: eggs net 120 g, fat 10 g, output 114 g;
- column III: eggs net 80 g, fat 10 g, output 79 g;
- fat choice: **10 g table margarine OR 10 g butter**;
- process: fry 3–5 minutes until the white sets and the yolk remains semi-liquid.

The 1973 Ministry collection independently contains the same margarine-or-butter
structure. That strengthens the fact that the source choice is not a parsing
accident. It still does not prove a FamilyFoodOS tested substitution.

Current MAP-A mapping has butter as an existing exact identity, while the specific
external milk/table margarine identity remains a new-food candidate. This candidate
is also less useful as the final third family because R1-23 already occupies the
egg family and 459 does not supply a clean exact optional-food role.

## Family-count fallback — USSR82-323

MAP-A's direct lead is the fixed column III + butter branch:

- potato net input 258 g;
- source cooked-potato output 250 g;
- butter 10 g;
- dish output 260 g.

Both identities already exist. The source nevertheless describes a broader family
with young-potato and butter/sauce/sour-cream alternatives. Candidate-A does not
promote those alternatives. Even the fixed branch still needs the raw-to-cooked
transformation/output evidence bound correctly before it can become deterministic
production nutrition.

This is a useful fallback for `family_count`, but **not** the preferred final
third family because it does not resolve the collective optional/substitution
coverage that remains after R1-21 + R1-23.

## Source and rights boundary

Order N 310 approved the collection and described it as the main technological
normative document alongside the applicable standards and instructions. The
collection introduction says the formulations were recalculated/refined based on
production workups. Secondary legal text:
`https://internet-law.ru/documents/dop_documents/1/sanpi_44121/0/prika.html`.

The collection also names a developer collective. Candidate-A therefore makes no
claim that the entire publication is public domain or freely republicable. We keep
only factual quantities, identifiers, bounded process observations and source URLs
as research evidence. Expressive source text, layout, images and complete source
assets are not imported. Publication rights remain a separate gate.

## Decision

`USSR82-267` is the **primary third-family recovery lead**. It is the strongest
reviewed candidate because one family potentially contributes both missing
collective capabilities without relaxing the architecture:

```text
fixed carrot branch
+ exact optional rice semantics
+ explicit carrot/turnip alternate branch
```

But it is **not individually ready**. The next useful work is not RecipeTemplate
implementation and not bulk FoodIngredient creation.

Proposed next bounded operation, requiring separate authorization:

`V22-13-267-ENABLE-A`

Goal: resolve only the three exact food/form blockers for recipe 267 (`Крупа
рисовая`, `Молоко пастеризованное 3,2%`, `Петрушка (корень)`), define the optional
rice producer/transformation binding, and search for candidate-specific evidence
sufficient to decide full carrot-vs-turnip kitchen/substitution applicability.

If variant-specific kitchen evidence is still absent, `verified_substitution`
remains OPEN even after the food-form blockers are solved.

## Non-goals

- no FoodIngredient mutation or creation;
- no Nutrition/Composition profile promotion;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- no migration/schema/runtime/API/UI change;
- no guessed yield/retention;
- no declaration that a source OR is a verified substitution;
- no Assembly B or PR7 work.

## Files

- `candidate-decisions.json` — three-candidate decision and gate state;
- `identity-readiness.json` — exact candidate-267 identity path and blockers;
- `quantity-process-review.json` — source quantities/process boundaries;
- `source-observations.json` — source URLs, observations and rights limitations;
- `checksums.json` — integrity pins for this bounded evidence package.
