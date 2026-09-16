# V22-13-267-PROFILE-A — profile authority review

**Status:** research/data authority; no production mutation  
**Reviewed:** 2026-09-16  
**Delivery base:** `63e35817503723e4cdc6a82c9000a13f1360d271`  
**Accepted PR #41 merge:** `2b71c76c523c1b8a1ebeda9c5a2ba8fdc7157ced`  
**External checkpoint:** `a42beb529d9e3f4d219908f37fdb2ed430229cee43c18d414ff817ed1ac81b97`

## Goal

For the three exact food-form identities isolated by `V22-13-267-ENABLE-A`,
determine whether a production-grade nutrition/profile source can be identified
without promoting the v22.13 legacy reference rows, mixing incompatible sources
or changing FoodIngredient/Nutrition/Composition truth.

The candidates are:

- `RICE_GROATS_POLISHED` — source `Крупа рисовая`;
- `MILK_PASTEURIZED_3_2` — source `Молоко пастеризованное 3,2%`;
- `PARSLEY_ROOT_RAW` — source `Петрушка (корень)`.

## Result

**Two profile-source candidates are strong enough to continue toward a bounded
production import; one remains blocked. No production delta is made in this PR.**

| Candidate | Profile-source decision | Production promotion |
| --- | --- | --- |
| `RICE_GROATS_POLISHED` | `SOURCE_CANDIDATE_ACCEPTABLE_MAPPING_PENDING` | NO |
| `PARSLEY_ROOT_RAW` | `SOURCE_CANDIDATE_ACCEPTABLE_MAPPING_PENDING` | NO |
| `MILK_PASTEURIZED_3_2` | `BLOCKED_GENERIC_PROFILE_AUTHORITY` | NO |

`production_delta = null`.

The distinction is intentional: **finding a credible source does not itself
create a FoodNutritionProfile**. A later production operation would still need a
pinned source snapshot, deterministic source→registry mappings, an explicit
import/seed path, sealed NutrientVector and atomic Composition creation.

## RICE_GROATS_POLISHED

The official Italian CREA food-composition table has food `000100`:

- Italian: `Riso, brillato`;
- English: `Rice polished, raw`;
- scientific name: `Oryza sativa`;
- edible part: 100%;
- source page: <https://www.alimentinutrizione.it/tabelle-nutrizionali/000100>.

This is a better semantic fit for the accepted generic polished-rice identity
than current FamilyFoodOS `RICE_WHITE`, which is narrower/long-grain.

The source provides, per 100 g, 334 kcal, 6.7 g protein, 0.4 g fat, 80.4 g
available carbohydrate and 1.0 g total fibre, plus analytical mineral and
vitamin observations. Source methods/origins are exposed per value.

Several zeros on the page are explicitly imputed. Those zeros are **withheld**:
FamilyFoodOS does not convert imputation into authoritative numeric zero.

CREA states that its data/text may be copied or reproduced only with clear
indication of the original source. Any later import must preserve attribution
and the exact source/version snapshot used.

Decision: the profile source is **acceptable as a candidate**, but production
mapping/import remains a separate operation.

## PARSLEY_ROOT_RAW

The Norwegian Food Composition Table (`Matvaretabellen`) has exact food ID
`06.051 — Parsley root, Norwegian, raw` with scientific identity
`Petroselinum crispum ... convar. radicosum`, FoodEx2 parsley-root
classification and a raw/no-heat-treatment facet:

<https://www.matvaretabellen.no/en/parsley-root-norwegian-raw/>

Per 100 g it reports 46 kcal, 1.7 g protein, 0.3 g fat, 7.3 g carbohydrate and
4.0 g dietary fibre. The page also exposes per-nutrient source identifiers;
multiple core values cite the Norwegian vegetable/berry nutrient-analysis
source.

Matvaretabellen's official API exposes foods, nutrients and sources in JSON/EDN
and asks users to cite the Food Table. The API is explicitly **not versioned**
and the table is updated annually:

<https://www.matvaretabellen.no/en/api/>

Therefore a future production import must cache/hash the exact response or other
source snapshot and record its retrieval/version identity; a mutable API URL
alone is insufficient historical provenance.

Source code `50` denotes estimated naturally occurring zero rather than an
analysed zero, and source code `10` is missing/unknown. Those values are not
promoted under FamilyFoodOS unknown/zero rules.

Decision: profile source candidate **acceptable**, mapping/import still pending.
The separate Russian default-pool market gate from PR #41 remains unresolved.

## MILK_PASTEURIZED_3_2

Current Russian retailer evidence strongly supports the exact form and common
macros. For example, the current Lenta listing for pasteurized 3.2% milk reports
60 kcal, 3.0 g protein, 3.2 g fat and 4.7 g carbohydrate per 100 g:

<https://lenta.com/product/moloko-lenta-pasterizovannoe-32-pet-bez-zmzh-rossiya-900ml-671968/>

A second exact 3.2% pasteurized listing reports the same values:

<https://lenta.com/product/moloko-pitevoe-pasteriz-32-paket-bez-zmzh-rossiya-900ml-546948/>

These product labels are useful identity/market evidence but do not by themselves
establish a generic category-level canonical full profile.

The Polish National Institute of Public Health PZH describes an extensive
1045-food full composition database, IV edition 2017, with macros, fibre,
minerals and vitamins on a 100 g edible basis, but distributes the XLSX under a
license agreement:

<https://www.pzh.gov.pl/uslugi/tabele-wartosci-odzywczej-produktow/baza-danych-wersja-pelna/>

This repository does not possess that licensed file in this operation. We
therefore do not assert that an exact milk row exists in it and do not quote or
import any row values from it.

Decision: `MILK_PASTEURIZED_3_2` remains
`BLOCKED_GENERIC_PROFILE_AUTHORITY`. No cross-source profile is synthesized from
retailer macros plus unrelated micronutrient evidence.

## FamilyFoodOS mapping boundary

The current NutrientVector registry already has canonical concepts such as
`ENERGY_KCAL`, `PROTEIN`, `FAT_TOTAL`, `CARBOHYDRATE_AVAILABLE`,
`FIBER_TOTAL_DIETARY`, minerals, thiamin and riboflavin. This PR records only
**candidate mapping reviews**.

A later production import must verify exact concept/method/unit compatibility
for every imported source nutrient. It must also preserve the source's own
method/origin and withhold imputed/logical/missing zero values.

No cross-source blending is authorized.

## Assembly A impact

Assembly A remains **BLOCKED at 2/3**.

- `family_count` = OPEN;
- `optional_role` = OPEN;
- `verified_substitution` = OPEN.

This operation removes the broad “no source found” problem for polished rice and
parsley root, but it does not make recipe 267 individually ready. Milk profile
authority remains open, and PR41's kitchen/rice-garnish blockers are independent
of profile provenance.

## Decision

The next useful bounded operation is `V22-13-267-KITCHEN-A`, not immediate
production-profile implementation.

Reason: if candidate-specific carrot/turnip verification or the rice-garnish
process cannot be made authoritative, creating three new production food profiles
solely for recipe 267 would not unblock Assembly A. Kitchen/process viability is
therefore checked first.

A possible later `V22-13-267-PROFILE-B` may implement only the actually needed
FoodIngredient/profile/vector/composition additions after that review.

## Non-goals

- no FoodIngredient creation or mutation;
- no FoodNutritionProfile/NutrientVector/Composition creation;
- no source-to-registry production mapping approval;
- no production seed/import change;
- no RecipeVersion/RecipeTemplate/RecipeAssembly publication;
- no schema/migration/runtime/API/UI change;
- no cross-source hybrid profile;
- no inferred exact zero;
- no Assembly B or PR7 work.

## Files

- `profile-authority-matrix.json` — candidate/source decisions and blockers;
- `source-manifest.json` — source identity, access/use and version limits;
- `nutrient-mapping-review.json` — candidate project-registry mappings only;
- `data-enablement-plan.json` — explicit null production delta and follow-up;
- `checksums.json` — integrity pins for the bounded package.
