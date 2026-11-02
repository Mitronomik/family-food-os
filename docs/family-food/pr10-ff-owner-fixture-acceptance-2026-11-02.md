# PR10-FF — owner acceptance of exact forward technical Planner fixture

**Owner decision date:** 2026-11-02
**Decision reference:** [Issue #271](https://github.com/Mitronomik/family-food-os/issues/271), informed by explicit approval in the FamilyFoodOS project conversation on 2026-11-02.
**Accepted baseline:** `main@1880c76b5891dba6bd8138d0c2a0e64460eb645d` after [PR #270 merged](https://github.com/Mitronomik/family-food-os/pull/270).
**Scope:** one synthetic, test-only, **energy-only** reproducible Planner fixture; no production/release authority.
**Proposed effective gate after review and merge of this documentation-only PR:** `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` **for the exact fixture below and no other input/output**. Before that merge, the accepted `main` still carries `NOT_PROVEN` and must not be represented as already updated.

## FACT — independently reviewed evidence

The owner acceptance applies to the **already independent-reviewed** [final evidence report](pr10-ff-final-evidence-review-2026-11-02.md), which records `PR10_FF_FIXTURE_REPRODUCIBILITY_REVIEW=PASS`. It is not a newly rerun experiment, a new seed, or a license to select an alternative successful week.

- [PR #267](https://github.com/Mitronomik/family-food-os/pull/267) accepted the exact immutable A/B input bytes, not a generated output.
- [PR #269](https://github.com/Mitronomik/family-food-os/pull/269), merged at `366f40d9dc3a69b44e2262e18d6a4b407b0371de`, implemented the real two-process proof without changing production Planner.
- [PR #270](https://github.com/Mitronomik/family-food-os/pull/270), merged at `1880c76b5891dba6bd8138d0c2a0e64460eb645d`, independently reviewed its persisted source/role/member/portion/provenance semantics and raw receipts.
- [Exact #269 HEAD CI](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338): 26/26 associated workflows SUCCESS, 17 focused tests PASS, Ruff lint/format PASS; original [raw process-1/process-2/comparison artifact](https://github.com/Mitronomik/family-food-os/actions/runs/41309700338/artifacts/13084512933), retained until 2026-12-01. The archived [independent report](pr10-ff-final-evidence-review-2026-11-02.md) contains raw file/ZIP hashes and source-to-output validation details.

## DECISION — exact accepted object and digest pins

| Field | Owner-accepted exact value |
| --- | --- |
| Fixture ID | `PR10_FF_FORWARD_3M_7D_V1` |
| Household/date | Three **synthetic** members, seven local days `2026-11-02..2026-11-08`, `Europe/Moscow` |
| Planner execution | Two genuinely independent fresh Python + temporary SQLite processes; unchanged real `PlannerService.generate_authoritative`, normal repository/UoW persistence and independent readback |
| Structural result | 21 genuine `COOK_RECIPE` MealEvents and 42 finite positive exact six-place Decimal Servings; heterogeneous accepted 3/2/1 member patterns, seven-day role/participant/source/exclusion checks |
| Source A raw SHA-256 | `d160b995b680d11cf9e04f3f97c0d01cd1c65ecd2518e685b8e3cfa783e0a885` |
| Planner input B raw SHA-256 | `9a9260a4a8d849fa4284ff64b861d8c2db74d15777b04ca5d3741d25f1f0089f` |
| V1 semantic week SHA-256 | `45c8773b6bd51fdb9f69f8c887dc2c66ae8a7674756b4787e72995a6d84df5e2` |
| V2 normalized working Planner input SHA-256 | `5f812e41de2d3f2b11526503e72a1bc1b1371345b9ea68a64f55e21d7aa27966` |
| V2 source/version/Step/rights provenance SHA-256 | `6e03e03865ce95bcca5d61d77652b4b1c4af4243bdfca966dae4d88902c0558c` |

Authoritative immutable input artifacts remain [frozen external pins](evidence/pr10-ff-forward-input-v1-pins.json), [A](evidence/pr10-ff-forward-input-v1/publication-A-PROPOSED.json), and [B](evidence/pr10-ff-forward-input-v1/planner-B-PROPOSED.json). Their literal `-PROPOSED.json` filenames are retained because renaming or editing would change the reviewed bytes; the external owner freeze + this explicit decision confer authority. This document does not modify any of them.

The raw opaque Planner request/trace fingerprints **differ** between independent databases. The reviewed source demonstrates run-local FoodIngredient and MealPatternSelection UUID/snapshot influence in the raw hashes, while actual normalized request, candidate/member tie-order, source/version/process/rights, selected recipes, member roles, exclusions, Decimal servings and persisted results match. No byte-identical raw `PlannerRequest` claim or Planner fingerprint algorithm change is authorized.

## SCOPE LIMIT — what PASS means and does not mean

**Permitted only after this decision's reviewed docs-only PR is merged:** record `PR10_FF_FIXTURE_REPRODUCIBLE=PASS` for `PR10_FF_FORWARD_3M_7D_V1`, its exact A/B and three output/semantic digest pins, as a technically reproducible synthetic *energy-only* fixture. The independent QA review verdict and owner acceptance are distinct facts; neither is a release gate.

All 51 input candidates have `nutrition_status=INCOMPLETE` despite `exact_energy_ready=true`. **No** complete protein/fat/carbohydrate or micronutrient coverage, nutritional/clinical suitability, portion plausibility, kitchen execution or storage/reheat safety follows from this decision. No new data publication or source-rights reevaluation is implied.

The following independent gates **remain unchanged**:

```text
NO_GO_TO_PR10_CORE_RUNTIME
APPROVED_IMMEDIATE=0
SAFE_BATCH_READY=false
PORTION_RELEASE_READY=NOT_PROVEN
```

Further blockers are independently reviewed D3 RecipeStep eligibility, source/rights/version/scale and revocation/anti-rollback, at least **two distinct** genuine selected MealEvents with independently published executable Russian same-day Prep actions, an honest unresolved negative case, complete Pantry-aware Shopping→Prep→backend PDF technical Gate2 vertical slice and separate finished-dish safe-batch/real-family/release verification. Neither historical [PR #196](https://github.com/Mitronomik/family-food-os/pull/196) nor negative [PR #254](https://github.com/Mitronomik/family-food-os/pull/254) evidence is rewritten or replaced.

**Next authorized action:** seek independent review and an explicit owner merge decision for this *docs-only gate-recording PR*. PR10-A, Prep/Freezer, D3 publication, Gate2, Retail/AI, new source inputs and release actions require **new, separately scoped owner authorization** after their own prerequisites; do not start automatically.

**Invalidation:** if the frozen A/B, source/rights, candidate authority, Planner algorithm or fixture parameters change, do not silently refresh this PASS; require a new versioned freeze, fresh independent proof and explicit owner decision.
