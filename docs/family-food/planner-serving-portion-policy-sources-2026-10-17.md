# Planner Serving — source applicability and policy-ownership decision proposal

**Status:** `RESEARCH_ONLY / PROPOSED / NOT A PLATFORM PORTION POLICY`
**Issue:** [#232](https://github.com/Mitronomik/family-food-os/issues/232)
**Base:** merged [PR #231](https://github.com/Mitronomik/family-food-os/pull/231), `main@702064b85e8f8d8decbd519a04b8d4204246dd5d` (2026-10-17).
**Read with:** [Planner serving feasibility contract](planner-serving-plausibility-contract-2026-10-17.md), [bounded three-recipe NO-GO](planner-serving-research-readiness-2026-10-17.md), [machine-readable source assessment](planner-serving-portion-policy-source-assessment-2026-10-17.json), [Product Strategy](product-strategy.md) and [PR10 Finished-Dish-First](pr10-finished-dish-first-amendment-2026-10-12.md).

## 1. Goal and required distinction

**Question:** which external, source-backed material could support a future narrowly scoped FamilyFoodOS `PortionFeasibilityProfile`, and who must authorize its use? This is a source **assessment**, not an executable source selection.

A legitimate source can contain a **serving range** without proving a person's physiological/physical safe maximum, a recipe's cooked-yield scale applicability, or that the whole planned meal (main + garnish + other food) is acceptable. The three truth layers remain independent:

1. **Recipe fact:** pinned `RecipeVersion` and original prepared output/form, as accepted in the recipe manifest.
2. **Contextual norm/reference:** published quantity for a specified population, organized setting and dish category. Must be applicable to the **particular member, MealEvent, dish and full/partial meal role**.
3. **Production feasibility judgement:** an independently reviewed, versioned FamilyFoodOS rule **explicitly adopted** for that scope and evidenced by validated source form/scale. Only this can eventually justify `PASS_REVIEWED_FEASIBILITY`. A Household preference is a separate scoring signal, never this authority.

## 2. FACT — current Russian legal baseline changed in 2026

The **current** sanitary standard is [СанПиН 2.3/2.4.4282-26, Постановление № 18 от 02.06.2026](https://www.garant.ru/products/ipo/prime/doc/414229257/), officially published under [№ 0001202606020084](https://publication.pravo.gov.ru/document/0001202606020084) (publication identifier independently stated by the legal-text mirror, but the portal URL was **not directly retrievable** during this review). The new standard **entered into force on 2026-09-01**, replacing `2.3/2.4.3590-20`; the [FMBA official update](https://mru31.fmba.gov.ru/press-tsentr/detail/?ELEMENT_ID=87901) independently confirms the transition. It is a regulation for **public catering operations**, including organized child meals, not an instruction to impose universal household serving caps.

**Appendix 9 / Table 1** of the 2026 text gives, for instance, **7–11-year-old children**: a meat/fish/poultry second course **90–120 g** and a breakfast porridge/vegetable/egg/curd/meat dish **150–200 g**. For the **12+ children's category**, it lists a second course **100–120 g**. These are *published institutional dish-category portions*, **not** a universal medically safe min/max and not automatically applicable to an adult because the column says "12 лет и старше". They are research-only examples in this document. **Do not use the superseded 3590-20 as the current executable source.**

The text reviewed was an accessible [legal-text publication](https://www.garant.ru/products/ipo/prime/doc/414229257/), **not an independently byte-pinned copy from the official portal**. An immutable accepted source snapshot, publisher/rights decision and applicability curator are still missing.

## 3. Source comparison, permitted evidence versus rejected authority

| Candidate reference | What it actually covers | Assessment for FamilyFoodOS |
| --- | --- | --- |
| [RU СанПиН 2.3/2.4.4282-26 Appendix 9, Table 1](https://www.garant.ru/products/ipo/prime/doc/414229257/) | Age/dish-based portions in organized child catering; currently in force since 2026-09-01 | **Potential narrow child/dish contextual benchmark**, not automatic household upper bound and not an adult rule; review legislation/version/rights, category semantics and member age |
| [RU МР 2.4.0179-20 Table 2, revision 2026-02-25](https://sudact.ru/law/mr-240179-20-24-gigiena-detei-i-podrostkov/mr-2.4.0179-20/ii/tablitsa-2/) | Recommended portions for school pupils, 7–11 and 12+ years, in school settings | Context only until reviewed; **not numerically identical** to the new СанПиН. The school guidance calls a meat/cutlet portion for 7–11 `80–120 g` versus the СанПиН **second dish** `90–120 g`. Preserve the category/source differences; don't average or silently pick an endpoint |
| [RU Rospotrebnadzor — adult food-group guidance](https://79.rospotrebnadzor.ru/novosti/18558/) | Conditional portions by adult food **groups** and activity: e.g. about `85–90 g` of *cooked meat or fish* as **one conditional group portion** | Helpful for explanatory context; **not** whole multi-ingredient dish mass, daily single-serving limit or proof that larger amounts are physiologically unacceptable |
| [NIDDK — portion vs label serving](https://www.niddk.nih.gov/health-information/weight-management/just-enough-food-portions) | Distinguishes the amount a person chooses to eat from standardized label serving size | Correct conceptual boundary; no executable meal-mass maximum |
| [USDA FNS Food Buying Guide](https://foodbuyingguide.fns.usda.gov/Home/About) | US institutional child nutrition meal components, AP/EP yield and planned serving quantities | Useful to distinguish output yield from meal contribution, but not a Russian household member's acceptable `RecipeVersion` mass |

**FACT / terminology hazard:** Russian source tables and US institutional references have **different categories and target settings**, even when both use grams and the word "порция". Meal-role, dish-form, age interval and component-versus-entire-dish identity must be separately verified. Neither an institution-specified category endpoint nor an adult food-group conditional portion means `PASS_REVIEWED_FEASIBILITY` for any actual member.

**Source status:** the study uses accessible web text and links; the original public documents' bytes were **not downloaded/independently hashed** into an accepted immutable FamilyFoodOS source snapshot. Dates refer to regulation/revision, **not** to a verified binary source version. No copied source prose or official publication rights are assumed. Revalidate legal state and revision at the time of any future publication task.

## 4. Bounded application to the three accepted historical recipes

The identifiers, original outputs and energy values below are **historical DC4 / manifest facts** from [#231 evidence](planner-serving-research-evidence-2026-10-17.json), not new live Household/RecipeVersion runtime output.

| Historical source-backed RecipeVersion | Prepared output on source basis | What is unresolved |
| --- | --- | --- |
| `SCHOOL2022_54_2M_BEEF_GOULASH` — beef goulash | `80 g` | Source output includes meat **with sauce**; not independently classified against institutional "second meat course" versus whole plate including garnish. Actual member age, accepted meal role/energy and scaling unknown |
| `SCHOOL2022_54_6R_PINK_SALMON_IN_MILK` — fish in milk | `80 g` | Fish **with liquid/sauce**, not automatically equivalent to fish-only or complete plate; age/opportunity/validated scale unknown |
| `SCHOOL2022_54_2O_GREEN_PEA_OMELET` — green-pea omelet | `150 g` | Egg dish is a plausible breakfast **category research lead**, but no pinned member age/actual event or scale basis; **150 g does not imply PASS** |

**Hard conclusion:** even if one source example happened to numerically overlap a recipe's `source_output_g`, that would neither prove full-recipe output at the **selected** `portion_servings`, nor the physical acceptability for a specific person, nor the feasibility of the family's entire seven-day week. Missing adult context cannot be defaulted from a child `12+` column; incomplete under-three Nutrition profile remains a **different audit track**.

## 5. Research decision and owner choice

**FACT:** credible age/dish-specific **institutional** references and adult **food-group** illustrations now exist in the source review. They do **not** establish the product-specific source/policy/yield/member intersection required for `PASS_REVIEWED_FEASIBILITY`.

**ASSUMPTION to test:** an independently curated, narrowly scoped **child school-age breakfast egg-dish** contextual policy might be reviewable as a future research pilot, once an applicable actual member/opportunity and the recipe's scaling relation are pinned. No positive case has yet been established; don't stretch this to toddlers, all children, meat/fish-with-sauce, adults or meal-sized physical safety.

**DECISION PROPOSED (NOT APPROVED):** limit the **next** task to a single *source + applicability publication contract proposal* for **one** age/dish scenario using the **current** 2026 Russian primary regulation and existing reviewed School2022 breakfast-omelet source; require independent nutrition-domain/safety applicability review and product-owner approval. Draft the source/reference-version, legal rights, exact portion-category matching, child's age and accepted MealPattern/role, recipe cooked-yield scale evidence, no-source/ambiguous-case `UNKNOWN`, revocation and test-only negative controls. **Do not publish any portion profile or turn these ranges into runtime limits in that task.**

**OPEN — explicit owner decisions required before the follow-on:**
- Approve/refuse researching **this exact** school-age breakfast egg-dish category as **contextual evidence only**, or nominate a different source with exact scope.
- Name the decision/policy owner and who independently reviews nutrition/form applicability; source curation is not authorized merely by finding an official document.
- Decide whether the product ultimately wants a **non-medical plausibility advisory** versus an independently justified hard physical admission policy. Option A/B and `RUNTIME_READY` remain separate **unapproved** decisions.

If the owner declines a viable scoped research path or the primary source/form/role mapping fails independent review, explicitly return `NO_GO` rather than widening source-hunting indefinitely.

## 6. Preservation and verification

**Unchanged:** `RESEARCH_READY=false` as previously established by the bounded #231 proof; `RUNTIME_READY=NOT_EVALUATED`, **no** updated Planner or `PASS_REVIEWED_FEASIBILITY`, no accepted new physical-policy profile. `AI_ENABLED=false`; no arbitrary `max_portion_g`, child/adult kcal defaults, provenance mutation, recipe publication, schema, API, consumer UX, Shopping, Pantry or Prep changes. `PR10-FD-META=BLOCKED`, `TIME_UNRESOLVED`, Gate2 and the original PlannerVersions remain untouched.

**Verification:** docs-only source and status audit, review of source links, source-context-vs-claim matrix and scoped code/data diff. No live DB, new Household fixture, full-week proof or backend regression performed; none is claimed. Exact-head Docs CI and independent human review precede merge.
