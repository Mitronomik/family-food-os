# PR4-DATA2 — Russia/SPB re-curation research

Status: **IN PROGRESS / BLOCKED — current regional market evidence**.
Reviewed: `2026-09-05`. Task: [issue #12](https://github.com/Mitronomik/family-food-os/issues/12).
Base: `26af749be0f6446de1d88cad2e2e03158a9830a0`.
Branch: `data/pr4-data2-russia-spb-recuration`.

This directory is a partial research handoff, **not the corrected technical
corpus**, not an accepted retailer matrix and not production availability.
No final 30-recipe successor, new Gate 2 union or accepted replacements have
been published. Do not feed these research files into the PR4 seed generator.

## FACT

The authorized policy is
[`recipe-localization-and-substitution.md`](../../../docs/family-food/recipe-localization-and-substitution.md).
It requires current SPB/LO evidence for the required ingredient forms and
explicitly authorizes replacing both ICN cards and other unsuitable recipes.
The existing corpus has 30 sources, 363 coverage rows and 119 distinct codes;
the accepted global catalogue has 183 entries. Those inputs remain unchanged.

All 30 source ingredient lists were screened for exact-form risks; this is
not equivalent to completing a retailer audit of all 119 ingredient concepts.
`research-candidates.json` preserves all 30 per-recipe findings, 96 exact
source-text/code form checks, eight rejected candidate screens and an uncleared
additional source pool. No candidate passed the full acceptance gates.

The five-chain access investigation found:

| Chain | Result | Why it cannot yet satisfy the regional gate |
| --- | --- | --- |
| Пятёрочка | Human-verification challenge | Current regional catalogue not reached; not bypassed. |
| Перекрёсток | Human-verification challenge | Indexed edamame flyers were historical; explicitly regional flyer expired in April 2025. |
| Лента | Catalogue reachable, Moscow selected | SPB URL parameter/title did not change the actual store; visible selectors did not establish SPB/LO. |
| О'КЕЙ | Forbidden / HTTP403 | No usable current regional catalogue obtained through the attempted official routes. |
| Магнит | Product pages reachable, store unset | SPB shopCode/title leads do not establish active regional assortment when the live UI still requires choosing a shop. |

Primary-source URLs, observed wording, dates, form mismatches and failed
alternatives are retained in `research-x5.json`, `research-lenta-okey.json` and
`research-magnit.json`. These are heterogeneous investigation notes, not the
final normalized evidence schema required by issue12. No CAPTCHA, access
restriction, certificate validation or browser security control was bypassed.
No credentials, home address, precise personal location or cart operations were
used. Public store addresses are not household records.

Examples requiring exact-form review include canned unsalted cream-style corn,
reduced-fat cheddar, frozen orange concentrate, canned pimientos and canned
low-sodium Pinto beans. Ordinary sweetcorn, another light cheese, drinking
orange juice or dry beans are not automatically interchangeable evidence.
Some source rows offer alternatives, but each selected alternative must itself
resolve to an existing global FoodIngredient and pass the same source/market
gate; this operation must not invent a conversion or a new catalogue entry.

## ASSUMPTION

Matching products may exist in SPB/LO despite the failed access/search probes.
No store absence, universal unavailability, or impossibility of every possible
30-recipe solution has been proved. A current permitted regional view or
reviewed offline retailer evidence may unblock the operation.

## BLOCKER

The required evidence cannot currently be established with the inspected
accessible sources. Promoting national/other-region listings, old flyers or
wrong-form products to `AVAILABLE` would weaken the explicit gate. Therefore
the operation stops before accepting replacements or publishing a successor
corpus. No final `RU_MASS_MARKET` / `RU_AVAILABLE` totals are claimed.

Both `CACFP6-VEGETABLE-FRITTATA-BITES` and `CACFP6-CAULIFLOWER-RICE` are excluded
from any future DATA2 selection by the approved decision. They remain only in
the unchanged previous corpus pending an atomic valid 30-recipe replacement; leaving
28 recipes or mislabelling an unfinished selection as final would fail issue12.
The requested actual corpus replacement is **not complete**.

This is not a renewed blanket FNS rights blocker: main's accepted direct-FNS
risk classification controls this operation. Final sources still require
exact document retrieval/hash, attribution and notice review. ICN exclusion
remains mandatory. No new source has been labelled rights-cleared by inference.

## OPTIONS

1. Establish an authorized usable SPB/LO catalogue session, including human
   completion of retailer access challenges where necessary, then resume
   evidence collection without changing criteria.
2. Supply or obtain current official regional catalogues/exports or reviewed
   store-level evidence with URL/source ID, date, city, product wording and
   exact forms. Use them as offline curation inputs, not a production connector.
3. If subsequent complete evidence still cannot support 30 suitable recipes
   using the existing catalogue and <=120 union, escalate that specific data
   constraint with the tested candidate set; do not expand it silently.

## RECOMMENDED DECISION

Use option 1 or 2 to resolve the evidence-access blocker while retaining every
approved hard gate. Resume candidate selection only with reviewable regional
evidence. Do not authorize ingredient substitution, catalogue expansion or a
weaker geography/recency rule merely to make this research pass.

## Verification and scope

Unchanged PR4-DATA and FoodIngredient regressions:

```sh
backend/.venv/bin/python -m pytest \
  backend/app/tests/test_pr4_data_coverage.py \
  backend/app/tests/test_food_ingredient_domain.py \
  backend/app/tests/test_food_ingredient_application.py \
  backend/app/tests/test_food_ingredient_architecture.py \
  backend/app/tests/test_food_ingredient_seed.py \
  backend/app/tests/test_food_ingredient_migration.py \
  backend/app/tests/persistence/test_food_ingredient_repository.py -q
```

Result: **82 passed in 2.25s**. This verifies the existing baseline, not an
accepted DATA2 corpus. Research-integrity assertions passed: four JSON files
parse; all 30 source IDs match the previous corpus; all 96 flagged code/text
pairs match actual coverage rows and existing global codes; nine observations
are unique, dated, source-linked and explicitly `UNCERTAIN`. Observation totals
are Перекрёсток 2 / Лента 5 / Магнит 2; Пятёрочка and О'КЕЙ have access records
only. Accepted `AVAILABLE` count is zero for every chain, not proof of zero
available products. No final market-class or single-retailer-only counts exist.

`git diff --check` passed. Backend, scripts, all seeds and historical corpus
are byte-unchanged from the exact base. Final DATA2 acceptance checks are not
passed because the final dataset does not exist. No tests were weakened.

Full backend/launcher suite and Ruff: not applicable to these JSON/Markdown
research-only changes; issue12 explicitly makes full runtime regression
unnecessary for isolated data-only work. No Python files were changed.

No global FoodIngredient, historical corpus, PR4 runtime/seed/test, migration,
retailer integration, PR #10 or PR5 changes. No local database or downloaded
source PDF is committed. The research PR is a **draft**, not ready for final
acceptance, and does not close issue12.
