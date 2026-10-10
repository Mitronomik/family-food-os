# PR10-META-ALTERNATIVE — same-day source-pair audit of the accepted fixture

**Status:** `BLOCKED_NO_REVIEWED_SHARED_PREP_OPERATION` — one source-supported raw vegetable preparation candidate, no accepted executable reuse.
**Issue:** #201.
**Accepted base:** `main@9a8e978c5aecb5c5390e9189acb0a0536f05e426` (PR #200 merged 2026-10-10).
**Owning contracts:** [PR10-ARCH](pr10-prep-freezer-implementation-contract.md), [PR10-META BLOCKED](pr10-meta-readiness-decision.md), [PR10-META-SAFETY case NO-GO](pr10-meta-safety-source-scope.md).
**Frozen audit data:** [seven-day pair receipt](pr10-meta-same-day-pair-evidence.json).

## 1. FACT — independent recomputation from exact accepted fixture

The accepted **synthetic persisted** PR #196 fixture was recovered from [GitHub Actions run #38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826) artifact 11672432141. Its extracted JSON file SHA256 is `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec` (not the ZIP digest). It belongs to synthetic MealPlan `589ef95a-2158-40a1-af91-0e13087d5744` and has 3 members, 21 events, 42 servings and 51 source-verified current-at-fixture catalogue versions. The independent Planner semantic SHA256 is `2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d`.

**Method:** for each of seven MealPlan-local dates, take all 3 unordered pairs among that date's exactly 3 selected `COOK_RECIPE` MealEvents and intersect their version-pinned `RecipeStep.instruction_sha256` sets. This is a source-instruction equality audit, **not** a semantic review of physical actions; missing identical text does not disprove useful shared work. All 21 comparisons are represented by date and recipe-code triplet in the [JSON evidence](pr10-meta-same-day-pair-evidence.json). Results:

| Date (2026) | Selected roles | Distinct within-day pairs | Pairs sharing an identical pinned RecipeStep hash |
| --- | --- | ---: | ---: |
| 14 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 15 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 16 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 17 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 18 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 19 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| 20 Sep | Breakfast / Lunch / Dinner | 3 | 0 |
| **All seven dates** | **21 events** | **21** | **0** |

The data are derived from **one** accepted temporary-database fixture; the UUIDs are synthetic and ephemeral. This is not a census of every possible seven-day menu or 51 current RecipeVersions, and the result must not be promoted to a Planner invariant.

## 2. FACT — strongest same-date research candidate: Tuesday lunch/dinner

The best narrowed *shared ingredient preparation* candidate on Tuesday 15 September combines **lunch vegetable ragout with boiled beef** and **dinner potato-and-split-pea soup**. Both recipes are accepted in [R3-D source-backed frozen batch](../../data/curation/r3d-final-dc3-batch-gate/frozen-batch.json), sourced from MR 2.4.0162-19. Their canonical input ingredient identities overlap on `CARROT`, `ONION_BULB_FRESH` and `POTATO`. Crucially, the source process instructions are *not identical*.

| Version-pinned evidence | Lunch — ragout | Dinner — soup |
| --- | --- | --- |
| Event UUID | `cf0e3fe3-4c59-4447-9fbd-7a9e19c6ff49` | `d000a213-d169-4f10-a2ad-08180f40aea6` |
| RecipeVersion UUID | `063694fb-92cf-4731-adf6-041d36a532e4` | `116e25fa-12f3-4926-8a2a-7aa2cf99bb9c` |
| Source card | [MR 2.11](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/miasnye-bliuda/tekhnologicheskaia-karta-n-2.11/) | [MR 1.16](https://sudact.ru/law/mr-240162-19-24-gigiena-detei-i-podrostkov/prilozhenie-5/supy/tekhnologicheskaia-karta-n-1.16/) |
| Source recipe 2nd instruction | Finely chop onion and carrot, then poach with water and butter | Prepare onion and carrot, then poach with water and butter, with no identical cut specification |
| 2nd instruction hash | `55519c2f9e26fbb12ea8abd237547f58d94361f17deff6005919d7a86c7ad128` | `a75d7d9fa0b0a77ab6eefd8a7b357c522dfc750662db99126efe89ea4447d850` |
| `CARROT`, source grams / base serving | 35 g | 14 g |
| `ONION_BULB_FRESH`, source grams / base serving | 9 g | 5 g |
| `POTATO`, source grams / base serving | 91 g | 88 g |

Actual fixture portion allocations are also **different**. Ragout lunch has one synthetic member with `Serving.portion_servings=2.470615`; dinner soup has three with `2.707523`, `2.707523`, and `3.147820`. These decimals are **not** a license to rederive consumer masses from source prose; only backend Recipe/Serving/Unit authoritative scaling may compute execution quantities. The JSON pins all actual source-event/member IDs.

**Possible common physical action:** wash and/or peel the required carrots and onions once in a *single reviewed preparation session*, then use separate version-controlled branches for fine chopping, possible different soup cuts and distinct cooking. This is an **ASSUMPTION requiring an independent process/food-form review**, not an approved `shared_work_group_key`. No claim that vegetables, oil, water or cooked intermediate can be freely mixed.

**Important source blockers:** the R3-D ragout binds the exact total water but does not specify its distribution between poaching and sauce. Soup freezes the water branch rather than unspecified broth and does not specify water split between soak/cook/finish. The recipes therefore do **not** authorize merging the two *poaching* operations into one or inventing how much butter/water goes into a shared pan. Soup also includes a separately timed pea soak; no safe dependency/timing reduction follows from carrot/onion overlap.

## 3. Counterexamples and the time boundary

- **Thursday chicken dishes:** lunch steamed chicken soufflé and dinner boiled chicken both mention chicken, but the accepted [DC4 source catalogue](../../data/curation/dc4-corpus-readiness/rerun-summary.json) pins different canonical forms: `CHICKEN_CATEGORY_1_WHOLE_RAW` vs `CHICKEN_BREAST`. Same English/Russian dish noun is **not** validated food-form identity; do not combine them.
- **Friday/Saturday beef pair:** schnitzel and bitochki had exact shared first-step text, but they occur on different days and the accepted [case review](pr10-meta-safety-source-scope.md) ruled out an automatic overnight hold of the raw minced-beef/milk-soaked-bread mixture on available evidence. This comparison remains blocked; it is not magically fixed by the current audit.

The Tuesday events share a **date**, not a confirmed *actual cooking session*. Lunch and dinner can be hours apart. MealPlan carries `local_date`, but no actual start/end kitchen clock, appliance/cold-chain or stage-specific post-prep storage metadata. If shared vegetables are prepared for both at lunch, their later state until dinner must be independently validated. If both dinners and lunches were prepped simultaneously, a source-backed interval, separate stages and distinct safe final dish/use states would still need confirmation. Do not assume same-day means no food safety boundary.

## 4. DECISION: value not yet proved; concrete recovery path

| PR10 acceptance prerequisite | Observed evidence | Status |
| --- | --- | --- |
| Two actually selected MealEvents | Exact Tuesday lunch/dinner event and recipe pins | FACT / PASS |
| Overlapping ingredient identities | Reviewed `CARROT`, `ONION_BULB_FRESH`, `POTATO` | FACT / PASS |
| Identical reviewed executable preparatory step | No identical step hash; source directions differ | **BLOCKED** |
| Same physical ingredient state and shared-component identity | Raw ingredient prep only a hypothesis; cuts/process may differ | **BLOCKED** |
| Approved safe same-session or held form | No real prep times or storage transition | **BLOCKED** |
| Exact backend Decimal allocation, without changing dish results | Versioned Servings pinned, but shared intermediate split not reviewed | **BLOCKED** |
| At least one **net** fewer physical actions | Unverified, may be offset by separate cutting, handling/cleaning/storage | **BLOCKED** |
| Recipe-specific freezer/hold instructions | Source metadata not ready | **UNKNOWN / NOT AUTHORIZED** |

**Decision: PR10-META remains BLOCKED.** We have selected a concrete **lower-storage-risk research candidate**, not an actionable source-verified shared-prep plan. There are **no** new allowable Prep/Freezer storage quantities, dates or instructions in this PR.

**Next bounded decision, not another blind similarity audit:** a **PR10-META-DATA / shared raw vegetable component source-authority contract**. It would require reviewed equivalence of washing/peeling/ingredient form, recipe-stage links (including whether the two cuts can share a physical preparation), honest action-count baseline including cleaning, exact Decimal allocation through current backend and explicit time/state boundary. If suitable provenance cannot be obtained from reviewed source cards/official guidance, declare that candidate BLOCKED and reconsider fixture/recipe selection **without silently changing the existing approved Gate2 fixture or weakening acceptance**. Any change to immutable RecipeVersion/process metadata or new persisted identity needs its own reviewed docs-only gate before publication or runtime.

**Non-goals:** production Prep services, versioned Prep tables/migration, Pantry/Shopping mutations, AI, Retail, Auth, PDF, recipe seed edits, fabricated freezer guidance or introducing a generic food-handling rule as source authority.

**Verification:** machine-readable 21-pair reconciliation, accepted fixture JSON SHA256 and provenance, repo-relative links, docs scope/whitespace; no full backend regression since no runtime changes.
