# V22-13-267-ENABLE-A — bounded enablement review for USSR82-267

**Status:** research/data-enablement review; production delta withheld
**Reviewed:** 2026-09-16
**Accepted base:** `3144997f0464a741eb429325db6497887309a32b` (PR #40 merged)
**External checkpoint SHA-256:** `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

## Goal

Execute the separately authorized follow-up from Candidate-A for exactly one
candidate, `USSR82-267 — Суп-пюре из моркови или репы`.

The operation attempts to:

1. resolve the three exact food/form blockers (`Крупа рисовая`,
   `Молоко пастеризованное 3,2%`, `Петрушка (корень)`);
2. determine whether the optional-rice garnish can be bound to an authoritative
   cooked producer/transformation without raw/cooked substitution or hidden
   scaling;
3. seek candidate-specific evidence sufficient to decide carrot ↔ turnip
   substitution applicability.

This is an enablement review, not permission to weaken existing gates. Production
FoodIngredient/Nutrition/Composition and RecipeTemplate/RecipeAssembly truth remain
unchanged unless every owning authority is satisfied.

## FACT — accepted Candidate-A scope

The accepted recovery scope remains **column II + water**:

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

The source states that crumbly rice is used as garnish and that the soup may be
prepared without rice. Candidate-A already established this as source-level
optional semantics, not a production-ready template rule.

## FACT / DECISION — three food/form blockers

### 1. `Крупа рисовая`

**FACT:** ГОСТ 6292-93 defines rice groats as a food category. The current
ГОСТ Р 702.1.029-2022 scope explicitly includes polished rice made from long-,
medium- and short-grain rice. Current Russian retail likewise exposes materially
different polished round- and long-grain products.

**DECISION:** the unqualified source identity is broader than current
`RICE_WHITE / Рис белый длиннозёрный`. It must not reuse that identity.
`RICE_GROATS_POLISHED` is a valid **future distinct FoodIngredient candidate**.

**BLOCKER:** no new production profile is accepted here. The checkpoint's legacy
reference profile remains evidence only; different grain-type labels demonstrate
that one retail SKU must not become a generic composition authority.

### 2. `Молоко пастеризованное 3,2%`

**FACT:** ГОСТ 31450-2013 explicitly recognizes drinking milk with 3.2% fat and
pasteurized processing. Current Russian retail has exact 3.2% pasteurized products;
the inspected Lenta label reports 3.0 g protein, 3.2 g fat, 4.7 g carbohydrate
and 60 kcal per 100 g.

**DECISION:** `MILK_PASTEURIZED_3_2` is a valid **future distinct FoodIngredient
candidate**. It must not silently reuse current 3.25% or 2% identities.

**BLOCKER:** identity and market availability do not establish the full
FamilyFoodOS nutrient vector. No v22.13 micronutrient row is promoted.

### 3. `Петрушка (корень)`

**FACT:** parsley root is sold as a separate food form from parsley leaf. A
bounded current search found an SPB/LO B2B supplier and a consumer e-commerce
listing.

**DECISION:** `PARSLEY_ROOT_RAW` is a valid **future distinct FoodIngredient
candidate** and cannot reuse current `PARSLEY`.

**BLOCKER:** accepted full nutrient-profile authority is still absent. Current
market evidence supports availability, but not the ordinary mass-market/default
pool standard used by the accepted RU food-data policy.

### Food-form result

All three **identity/form ambiguities are resolved conceptually**, but all three
remain **production-data blocked**. Therefore this operation creates no
FoodIngredient, profile, vector, composition or seed row.

## FACT / DECISION — optional rice producer binding

The same 1982 collection contains reusable-looking rice preparations:

- recipe 747 `Рис отварной`: 352 g rice in column I or 360 g in II/III,
  60/45 g added fat, output 1000 g; the process boils rice in salted water,
  drains/rinses it, then adds fat;
- recipe 748 `Рис припущенный`: 340/345/350 g rice, 715/725/735 g broth or
  water, 60/45/35 g fat, output 1000 g; half the fat is used before cooking and
  half after.

These are useful producer candidates, but they do **not** close the binding.

**DECISION — `BINDING_BLOCKED`:**

- recipe 267 contains only 20 g raw rice for the garnish and does not name 747
  or 748;
- the candidate producer recipes have their own fat and salt/liquid semantics;
- recipe 267 already has its own 20 g butter row, so silently nesting 747/748
  can double-count or reallocate fat;
- accepted Assembly-A evidence does not permit proportional scaling from a
  published institutional batch merely because arithmetic is possible.

No raw-rice nutrition is relabelled as cooked-rice nutrition, and no guessed
cooked output mass is created.

`optional_role` therefore remains **OPEN**: the source meaning is established,
but the production identity/process/output binding is not.

## FACT / DECISION — carrot ↔ turnip substitution

The alternative is strongly corroborated:

- the 1982 Ministry collection lists carrot 320 g **or** turnip 360 g for
  recipe 267 and gives turnip an additional blanching step;
- the 1973 Ministry collection repeats the same carrot/turnip family and optional
  rice semantics;
- the 1987 professional culinary textbook again describes one soup-puree family
  prepared from carrot or turnip and served with crumbly rice.

**DECISION:** this is strong cross-edition culinary-family evidence, but it is
not enough to redefine the accepted FamilyFoodOS `verified_substitution` gate.
The bounded research did not find candidate-specific evidence identifying the
complete carrot and turnip branches as separately tested interchangeable variants.

`verified_substitution` remains **OPEN**.

## RU familiarity and market implications

The repeated 1973/1982/1987 professional treatment supports dish-family
familiarity for Russian/Soviet culinary context. That editorial signal is no
longer the primary blocker.

Food availability remains more granular:

- polished rice category: mass-market supported;
- pasteurized 3.2% milk: mass-market supported;
- fresh parsley root: availability supported, but bounded evidence is
  specialty/B2B/e-commerce rather than accepted mass-market default coverage.

No live-stock or price claim is committed.

## DECISION — production delta withheld

`data-enablement-plan.json` records:

```text
status = WITHHELD_AUTHORITY_GATES
production_delta = null
```

This is intentional. Creating three food identities without accepted nutrition
authority, or inventing a rice transformation/substitution rule, would violate
the existing FoodIngredient/Composition/Assembly contracts.

Assembly A therefore remains:

```text
individual_ready_count = 2
family_count = OPEN
optional_role = OPEN
verified_substitution = OPEN
status = BLOCKED
```

R1/R2/R3/R4 and Candidate-A remain frozen accepted evidence.

## OPEN QUESTIONS / bounded follow-up

The research has reached two separable remaining problems rather than another
broad donor search:

1. **Profile authority** — obtain production-grade full nutrient/profile evidence
   for `RICE_GROATS_POLISHED`, `MILK_PASTEURIZED_3_2` and
   `PARSLEY_ROOT_RAW`, and decide whether parsley root can satisfy the default
   RU availability policy.
2. **Kitchen/process authority** — establish the exact 20 g rice garnish
   transformation/batch applicability and obtain candidate-specific complete
   carrot/turnip variant verification.

Suggested separate operations, both requiring explicit authorization:

- `V22-13-267-PROFILE-A`;
- `V22-13-267-KITCHEN-A`.

Neither is started by this PR.

## Non-goals

- no production FoodIngredient/profile/vector/composition mutation;
- no schema or migration;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- no proportional institutional-batch scaling;
- no inferred yield or retention;
- no relaxation of `verified_substitution`;
- no Assembly B, PR7, Retail, AI or Auth work.

## Files

- `food-form-decisions.json` — identity/form decisions and profile blockers;
- `rice-garnish-binding.json` — candidate producer analysis and binding refusal;
- `substitution-evidence.json` — cross-edition evidence and gate decision;
- `market-evidence.json` — bounded Russian availability observations;
- `source-manifest.json` — source URLs, purpose and authority limits;
- `data-enablement-plan.json` — explicit withheld production delta;
- `checksums.json` — package integrity pins.
