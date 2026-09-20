# DC2: exact source-input mappings and mass safeguards

Base: `0322d0a74a0edf53802adc394446011a7d8acc06` (PR72 merged).
Version: `dc2-exact-input-v1`. User authorized continuation after PR72.

## Task contract

Goal: resolve source input forms for five priority school2022 groups and
prevent unsafe use of their net quantities. Scope: 211 exact occurrences,
five source form proposals, targeted exception and route overrides.
Non-goals: production publication, canonical UUID allocation, nutrient registry
changes, rights decisions, API/UI/Planner, migration or next milestone.
Architecture remains FoodIngredient/profile/vector/ATOMIC; these source-form IDs
are review identifiers, not another runtime food identity system.

## Concrete outcome

| Source form | Occurrences |
|---|---:|
| Sugar, dry granulated | 89 |
| Carrot, raw root | 69 |
| White cabbage, fresh head | 24 |
| Beet, raw root | 12 |
| Rice groats, dry polished | 17 |

Matching is source-specific: row identity, source procurement specifications and
recipe process are retained through the locked inputs. Book IDs remain candidates;
source food identity does not establish nutrient equivalence to the book or to
existing USDA-backed runtime ingredients. No MR2019 occurrence inherits these
school-specific conclusions.

School2022 §1.4 (PDF p4) defines standard raw-material consumption. Its net mass
is a normative accounting quantity, not universal proof of a physical weighing
before heat. `source_quantity` preserves the original record, including its old
mass-state label; `net_mass_semantics_override` is the explicit correction.
Consumers must apply the overlay, not interpret the preserved old label as an
accepted conclusion. A source raw input can be boiled then peeled (beet).

The two carrot demands in 54-8с row3 and54-9с row3 occur in suspicious repeated
source prefixes (PDF p35–36). Four execution routes containing them receive
`material_execution_ready_override=false`. Do not delete either source row or
silently decide which recipe composition the editor intended.
Carrot in54-20м row3 and54-43м row3 is a broth aromatic; the fraction eaten is not
established. Cabbage54-8г row1 retains its exact178/157.5g ratio; no blanket20%
loss is applied. Rice drainage and absorption need recipe-specific treatment.

## Source corrections to PR72

- PDF p262 table1 explicitly specifies polished rice; p271 §6.2 corroborates
  white rice groats. The rice-form gap is narrowed for this source only.
- PDF p4 §1.4 explicitly sets tomato puree dry matter to20%. The earlier
  group-level claim that concentration is unestablished is incomplete for
  school2022. This correction does not approve all tomato candidates or MR2019.
- PDF p4 §1.5 says published nutrition already accounts for generalized heat
  losses. Published values and independent raw-input calculations must stay
  separate; no second application of those losses to published values.

These findings are professional-source evidence about institutional recipes,
not domestic storage advice. No new storage/allergen facts are inferred.

## Reproduce and validate

Obtain the immutable corpus0.3.0 as described in the preceding reconciliation
package. `input-lock.json` pins exact source PDF, extracted records and local
crosswalks. No source material is overwritten.

```sh
python3 scripts/build_dc2_exact_input_mappings.py --corpus /path/to/corpus-v03
python3 scripts/test_dc2_exact_input_mappings.py
python3 scripts/build_dc2_exact_input_mappings.py --validate-committed
```

A full build verifies external input hashes. Offline CI verifies repository
inputs, output checksums, exact coverage, authority restrictions, exception
propagation and route completeness. Offline checks do not substitute for reading
the external PDF or rerunning extraction.

## Dictionary and integration order

`forms.json`: stable review form ID, Russian name, source input state, expected
coverage, source pages, book candidate and unaccepted canonical mapping.
`exceptions.json`: exact demand ID and reason; no fuzzy label matching.
`generated/mappings.json`: one occurrence per source input, original quantities,
source locator, full-process hash, evidence-page record hashes, semantic override,
retained fraction unknown, disposition and version.
`route-holds.json`: overlay keyed by existing execution ID. False dominates any
older material-ready assertion. Apply before selecting any recipe for import.
`input-receipt.json`: locked inputs plus builder/configuration hashes.
`summary.json` and `checksums.json`: quantitative receipt and integrity.
Page-record hashes use sorted, indented UTF-8 JSON plus final newline, exactly
as implemented by `dumps`; they are not PDF-page image checksums.

1. Review source-form decisions and source errata; merge this overlay package.
2. In a separate publication payload, resolve exact book-to-canonical food
   equivalence, nutrient method and source reuse scope. Allocate/reuse canonical
   identity only after checking existing food form. Preserve unknown values.
3. Reconcile source-table ambiguities before lifting route holds. Require exact
   corrected edition/page or explicit reviewed editorial disposition.
4. Stage accepted direct profiles/vectors with ATOMIC validation in isolated
   storage; demonstrate idempotence and rollback before runtime import.

Acceptance: all211 selected occurrences accounted for, exceptions propagated to
all4 affected routes, provenance recoverable, reproducible output and tests.
Risk: these annotations do not prove retention, yield or nutrient equivalence.
Readiness: source-form review artifact READY FOR REVIEW; production payload and
DC2 completion NOT READY. Existing method/rights conditions remain in
[publication decisions](../dc2-first-batch-review/publication-decisions.md).
Rollback: remove this version's overlay from staging, preserve original corpus;
no production database/schema changes exist to roll back.
