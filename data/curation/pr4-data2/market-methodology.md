# DATA2 market evidence — clarified method

Reviewed: 2026-09-05. This document applies the Orchestrator's
[issue clarification](https://github.com/Mitronomik/family-food-os/issues/12#issuecomment-5550629546)
and [PR clarification](https://github.com/Mitronomik/family-food-os/pull/13#pullrequestreview-5120531796).
It supersedes the *regional browser access* conclusion in the initial research
commit; it does not change the classification or corpus gates.

## What an observation proves

Market compatibility is representation of the required food/purchase form in
ordinary SPB/LO major-chain retail, **not momentary store-level stock**.
Qualifying evidence is a current official product/category listing plus current
official SPB/LO chain presence. Region-neutral official listings are allowed.
An indexed official URL and exact product wording remain reviewable evidence
when the live page is blocked or empty. An established delivery-platform
storefront must identify the chain, SPB/LO region/store and actual product/form.

An explicitly other-city/store-bound page, expired flyer, third-party assertion
or wrong form cannot qualify. An access error is uncertainty, not product absence.
No CAPTCHA, TLS warning, authentication or browser protection is bypassed.
No purchase, address entry, cart, price snapshot or production retail integration
is involved. Search queries and excluded matches remain in the research files.

Each observation preserves the official URL, observed wording, date, region,
region-evidence URL, method and limitations. `AVAILABLE` qualifies only the
observed food/form. A product containing vanilla extract is not evidence of
standalone extract; canned whole corn is not cream-style corn; raw shell eggs
are not frozen liquid whole eggs. A page can qualify even when its live price
or stock counter is absent. No stock count or price is promoted to product truth.

## Source forms versus preparation

The original 96 flagged source-text rows remain verbatim, with an explicit
`PURCHASE_FORM_CRITICAL` or `PREPARATION_ONLY_OR_NOT_RETAIL_FORM` classification,
purchase concept and collapse reason. Their exact source quantities are not
retailer package requirements. Dicing, chopping, mincing, shredding, peeling,
draining and thawing do not create independent purchase concepts.

Material food forms remain distinct: frozen/fresh, canned/dry, shell/liquid eggs,
specified sodium/salt restrictions, dairy fat, named cheese and relevant grain
or meat form. Additional material forms found while reviewing all 363 historical
coverage rows are retained in `original-corpus-market-review.json`; the 96-row
set is a preserved audit input, not an exhaustive definition of every risk.

Review must join evidence by source purchase concept/form, not just canonical
code. Thus fresh carrot evidence does not clear a source explicitly requiring
frozen carrots. The low-moisture qualifier on Rice and Vegetable Casserole's
mozzarella does not propagate to another recipe that never states it.

## Bounded normalization decisions

- A genuinely unrestricted source category may select an existing member:
  vegetable oil → sunflower oil; unspecified raisins → golden raisins;
  unspecified nuts → a named existing nut. Preserve the source text, quantity,
  selected member and reason. Never replace explicitly named canola or a
  required special form through this rule.
- Source-explicit alternatives and optional omissions are recorded. They are
  not invented substitutions and cannot create artificially duplicated recipes.
- Fresh lime/lemon juice may be evidenced through the fresh fruit as a
  preparation purchase concept. Do not claim an unprinted squeezing step or
  invent whole-fruit/juice mass or yield conversions.
- Generic low-fat/nonfat dairy families do not require mathematical zero or an
  invented exact fat percentage. Plain Greek yogurt made from skim milk at
  0.1% fat is a nonfat-family product; skim milk at 0.05% is likewise residual-fat
  skim milk. Explicit source percentages such as milk 1% remain exact.
- Light sour cream 10% and light mayonnaise-style emulsion 20% are reviewed as
  the generic low-fat families, not as nutrition-identical branded products.
  This does not make ordinary cheddar equivalent to reduced-fat cheddar, or
  fresh brined mozzarella equivalent to explicitly low-moisture mozzarella.
- Plain raw ground turkey with turkey as its sole ingredient and a declared
  7 g fat/100 g supports the existing 93%-lean/7%-fat purchase form. A literal
  English “93%” label is not required when the same numeric composition is stated.
- Cooked quantities remain cooked. Raw product evidence alone cannot silently
  clear a separate cooked-food requirement. A source-supported preparation path
  needs its own review; no raw/cooked weight conversion is invented.
- Product-use limits matter: an oil explicitly unsuitable for heating can
  support a cold dressing, not an unreviewed frying use.

These decisions concern curation matching only. No canonical FoodIngredient,
nutrition value, source quantity or production RecipeVersion is changed.

## Classification and acceptance

Count distinct baseline chains, not products or duplicate observations.
Three qualifying chains yield `RU_MASS_MARKET`. One or two plus documented
ordinary non-specialist plausibility yield `RU_AVAILABLE`. Otherwise the form
is `SPECIALTY_OR_UNCLEAR`, forbidden as a final required ingredient. Tap water
is exempt; ordinary salt/sugar/oil/spice categories still need source evidence.

Research checks are not corpus acceptance. Candidate screens, the historical
30 sources and positive observations cannot by themselves establish a final
30-recipe successor. Final acceptance additionally requires every source row,
exact <=120 union, rights/provenance, per-form evidence, equipment and selection
decisions. The offline validator's default final gate must fail until those
artifacts exist and pass. PR #10 remains untouched until DATA2 ACCEPT + merge.
