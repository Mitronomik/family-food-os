# PR10-FF — forward Planner input freeze: source-backed review packet

**Status:** DOCS-ONLY PRE-RUN INPUT PROPOSAL / **NO_GO_INPUT_MANIFEST_UNVERIFIED**. Not a frozen or owner-accepted input manifest, a Planner run, or a release/Prep authority.
**Date:** 2026-10-30.
**Accepted repository base:** `main@b734656562bca29cfb877e4e2827ff0adb81598f` — [PR #263 merged](https://github.com/Mitronomik/family-food-os/pull/263) at 2026-10-30T12:39:04Z.
**Authority:** [forward-week contract](pr10-fixture-forward-contract-amendment-2026-10-29.md) §3–§6; [implementation preflight](pr10-fixture-forward-implementation-preflight-2026-10-30.md) §2–§4; [typed identity contract](pr10-ff-typed-test-identity-implementation-contract-2026-10-30.md) and [publication-key amendment](pr10-ff-publication-key-binding-amendment-2026-10-30.md), both accepted; [implemented test-only manifest spec](pr10-ff-test-only-manifest-implementation-2026-10-30.md); [historical negative #254](pr10-option-a-issue252-two-process-no-go-2026-10-29.md).

## 1. FACT / PROPOSAL / OPEN / DECISION GATE

**FACT.** PR #263 delivered an opt-in Recipe/RecipeVersion/Ingredient/Step v4-shaped typed identity seam, a validated `PR10_FF_PUBLICATION_MANIFEST_V1` reader and ordinary-providerless regression tests. Its QA exercised the real R1-F → R3-D → DC4-A3 nested SQLite seed chain with **51 original RecipeVersion v1 and seven corrected v2** (58 immutable version records total), then exact replay. This is a **seed identity proof**, not an independently approved production catalogue snapshot for a new Planner input or a real 3/7/21/42 Planner output.

**FACT.** The [old fixture builder](../../scripts/audit_pr10_meta_gate2_fixture.py) constructs a real synthetic Household and calls `PlannerService.generate_authoritative`, but invokes `seed_dc4_a3_russian_step_corrections(config)` and `create_household_service(engine)` without typed fixture injection and uses the historical `WEEK_START=2026-09-14` from [DC4 audit utilities](../../scripts/audit_dc4_corpus_readiness_rerun.py). It is **not** the new forward fixture runner. The old #254 two fresh processes produced valid shapes but divergent UUID-free selections; both NO_GO receipts must remain immutable.

**PROPOSED next bounded deliverable:** separately freeze and independently review one complete `PR10_FF_INPUT_MANIFEST_V1` plus its externally pinned SHA-256 **before** any forward Planner candidate selection. The already accepted `PR10_FF_PUBLICATION_MANIFEST_V1` is a nested **source-version identity** input, not a substitute for complete Household/Member/Planner/Candidate/Nutrition inputs. Only after both are accepted may a different bounded runtime proof PR execute the current real Planner twice.

**OPEN:** new-week exact date approval, independently verified full source/candidate/rights/energy projections, actual target kcal and heterogeneous selection parity, persistent member ID binding and independent digest review. No actual Planner input SHA or new week output digest exists here.

**DECISION:** This document proposes values and review checks; **nothing in this PR authorizes a run, generates a positive fixture, approves an input hash or changes D3/Gate2**. Reviewer may approve/revise the proposed fixture parameters before a separate versioned input artifact is frozen, or record NO_GO.

## 2. Three-layer immutable trust model — no conflation

| Layer | Content | Authority / when pinned |
| --- | --- | --- |
| A. Reviewed source/identity | Existing trusted 12-stage seed, 51 v1 + 7 DC4-A3 v2; per-version complete `TrustedRecipeVersionSeed`, source/rights/Step/process and immutable predecessor chain; closed six-kind typed key allowlist as applicable | `PR10_FF_PUBLICATION_MANIFEST_V1` via [loader](../../backend/app/services/pr10_ff_manifest_loader.py). Independently pin actual raw bytes, stage inventory, correction artifact hashes and source revision **outside** the file. Current #263 QA manifest is self-pinned, **not** the accepted A artifact |
| B. Forward Planner logical input | Exact source A pin, code/PlannerConfig, date/time zone, profile and energy truth, 3/2/1 accepted member roles, exclusions, complete candidate/admission/nutrition fingerprint, empty-or-actual Pantry/history/fixed-event data, operation-scoped test IDs, expected structural criteria | `PR10_FF_INPUT_MANIFEST_V1`. **Must** be independently approved, hashed and frozen in repository/evidence before either execution. This packet is not B |
| C. Genuine output evidence | Two independent processes/SQLite DBs, independently assembled real `PlannerService.generate_authoritative` requests, ordinary UoW persisted and readback 21 actual MealEvents + 42 exact Decimal Servings, UUID→source mapping, full canonical semantic-week comparison | Generated **after** A+B review. Success alone is not authoritative until independent raw-receipt and hash review. Old historical #196 output never replaces A or B |

**Forbidden:** self-hash computed by the same builder as its own independent approval; output-derived candidate manifest; selecting a different week, preferences, seed/UUID sequence or Planner scoring until a desirable pair matches; global UUID patches; copying old or new MealEvents/Servings; direct SQL FK/row rewriting.

## 3. Proposed one-time forward input — all facts tied to existing source

The following values are **review candidates only** and cannot become an accepted manifest simply by this docs PR.

| Field / proposed value | Source and constraint | Review status |
| --- | --- | --- |
| `fixture_id=PR10_FF_FORWARD_3M_7D_V1`, source policy `PR10_FF_TYPED_ID_POLICY_V1` | Existing exact namespace/fixture ID in [typed ID service](../../backend/app/services/pr10_ff_typed_ids.py); distinguish logical input schema `PR10_FF_INPUT_MANIFEST_V1` from source publication schema | Source policy FACT; B pin pending |
| `source_commit=b734656562bca29cfb877e4e2827ff0adb81598f` | HEAD after accepted #263; future actual artifact must pin this or an explicitly reviewed replacement; no floating `main` | Proposed reviewer freeze |
| `week_start=2026-11-02`, 7 days through `2026-11-08`; `timezone=Europe/Moscow`; `city=Санкт-Петербург` | New calendar Monday proposed **before any selection**, distinct from historical 2026-09-14. Time zone/city reuse [existing synthetic fixture builder](../../scripts/audit_pr10_meta_gate2_fixture.py) | **PROPOSED; owner/reviewer acceptance required** |
| Household with three **synthetic** active members, ordinal 1–3, source names `Участник 1/2/3` | [Original synthetic constructor](../../scripts/audit_dc4_corpus_readiness_rerun.py) `_add_member`, not actual user data | Source shape FACT; frozen B required |
| DOB `1990-01-01`, `1990-01-02`, `1990-01-03`; sex female/male/female; height 170 cm, weight 65 kg each; activity `active`; goal `maintain` | Existing `_add_member` uses 1990-01-index, alternating sex and identical profile/goal. Never add medical attributes. Need exact current target-energy derivation at the chosen week/start date | Source profile FACT; exact target kcal **OPEN** |
| Daily accepted CUSTOM role patterns `[BREAKFAST,LUNCH,DINNER]`, `[BREAKFAST,DINNER]`, `[DINNER]`, in ordinal order for all seven days | [Gate1 role shapes](../../scripts/gate1a_fixture_spec.py) `GATE1_ROLE_SHAPES[2]` and [existing accepted pattern writer](../../scripts/audit_dc4_corpus_readiness_rerun.py) | Source pattern FACT; actual selection/version, UUID and full energy-share readback **OPEN** |
| Role energy shares: breakfast `0.30`, lunch `0.35`, dinner `0.25` (exact Decimal), assigned as in existing CUSTOM schedule | [Existing pattern helper](../../scripts/audit_dc4_corpus_readiness_rerun.py) `_accept_custom_pattern`. **Do not normalize** these into a fabricated sum of 1 | Source share FACT; reviewer parity readback pending |
| Ordinal 3 excludes `BEEF_CATEGORY_1_RAW`; ordinals 1 and 2 no exclusions; no new tactical preferences | [Existing synthetic exclusions](../../scripts/audit_dc4_corpus_readiness_rerun.py) `_fixture_exclusions(3,...)`; real FoodIngredient UUID bound from current catalogue per run | Source exclusion FACT; run-specific FK and review pending |
| `PlannerConfig(version="planner-v0.5", compatibility_version="meal-role-recipe-v2", preference_weight="20", pantry_weight="4", batch_weight="2", time_weight="0.01", repetition_weight="7", max_recipe_repetitions=3)` | [Current deterministic config defaults](../../backend/app/domain/planner.py) and [source fixture explicit version](../../scripts/audit_dc4_corpus_readiness_rerun.py). All numerical fields stored and checked as exact Decimal strings | Source definition FACT; code blob + config pin pending |
| Pantry/history/prior plans/fixed events empty **only for genuinely fresh synthetic Household** | Confirm actual scoped readback before the run; never insert fixed `COOK_RECIPE` events to bias selection | **OPEN until genuine DB read** |
| Active eligible recipe candidates, nutrition source forms, kcal/Serving and exact meal type admissions | From **real trusted SQLite seed and current Planner candidate preflight**, not from a successful/selected week. Record complete candidate order, source/current-version/rights/Step/nutrition and tie-sort witness, including every rejection/UNKNOWN | **OPEN / blocking** |
| Structural requirements: 3 members, 7 local days, 21 genuine COOK_RECIPE MealEvents, 42 finite positive six-place Decimal Servings with correct ordinal participation | Accepted [forward fixture contract](pr10-fixture-forward-contract-amendment-2026-10-29.md). Requirement fixed before run, **not an assertion that Planner produces it** | Constraint FACT, runtime PASS **NOT_PROVEN** |

**Do not infer target kcal or candidate coverage from generic assumptions.** The current `PlannerService.compose_authoritative_request` obtains current member energy via accepted services and candidate admission. The future B artifact must record every exact value from trusted pre-selection readbacks and an independent authority check. Any changed/UNKNOWN critical field means `NO_GO_INPUT_MANIFEST_UNVERIFIED`.

## 4. Source/artifact pin inventory — verified code locations, not a self-approval

| Evidence | Current Git blob SHA / expected status |
| --- | --- |
| [Planner domain](../../backend/app/domain/planner.py) | `7793e6d55f475b06b15e01e902e3144e3f5d1944`; must additionally pin service `backend/app/services/planner.py` at intended B source revision |
| [Planner service](../../backend/app/services/planner.py) | `1dde67b026b3c2cab99622482979f3e1fe2d0751` |
| [Synthetic role program](../../scripts/gate1a_fixture_spec.py) | `88688d7ba981b2c14f6987cf4748a66a262e7e24` |
| [Existing member/pattern audit helpers](../../scripts/audit_dc4_corpus_readiness_rerun.py) | `04b7c9c2bb88d95b8024e94f2174302a4fcc565a`; **not** an authorized forward runner |
| [Old historical builder](../../scripts/audit_pr10_meta_gate2_fixture.py) | `874757e4a4527e8c519b387ec8f5e36664b8e45d`; keep unchanged as historical QA |
| [New publication manifest loader](../../backend/app/services/pr10_ff_manifest_loader.py) | `9fd507c74086f97484e91f566f4769edfdc4ebae`; source-only typed ID validation, does not supply Planner fields |
| [Seven accepted DC4-A3 raw corrections](../../data/curation/dc4-a3-russian-step-corrections/corrections.json) | Git blob `ec1f8fca9ff8d3c4ac844f6eab0c3411ece54c68`; raw UTF-8 SHA-256 `157f2ce76cc86baae2b288ce80da069154bc6d44ca1620b2b9f0c521b92e7759` from accepted #264 source review |
| [QA 51-v1 / 7-v2 trusted chain](../../backend/app/tests/test_pr10_ff_full_trusted_chain.py) | Accepted passing #263 code and regression coverage; `_qa_provider` currently self-hashes its just-built manifest, hence **cannot be re-labeled independently approved raw A evidence** |

**Critical separation:** immutable Git blob SHA-1 identifies repository source bytes; SHA-256 of whole raw input JSON is a separate, externally pinned digest. Neither is an existing run output hash. Any changed source/rights/process/energy invalidates the pending input version and requires explicit re-review, not quiet re-freeze.

## 5. Household/member identity construction — already-approved operation-scoped approach

The [accepted #262 signature matrix](pr10-ff-typed-test-identity-implementation-contract-2026-10-30.md) §4.1 allows the current `HouseholdService(..., id_factory=uuid4)` **without changing its public constructor**:

1. Load the independently reviewed `PR10_FF_PUBLICATION_MANIFEST_V1` and checked `HOUSEHOLD` key; construct a short-lived `HouseholdService` instance with `id_factory` bound to that **one semantic key only** during one `create_household`. Verify actual persisted ID and Household/timezone immediately.
2. For each reviewed ordinal 1, 2 and 3, derive the **complete** frozen profile SHA-256 from the approved B input (not the creation order or database), then use a **new one-operation** scoped `HouseholdService` with an `id_factory` bound to exactly that `HOUSEHOLD_MEMBER` key. Verify persisted ordinal/profile → UUID from real household repository. Never install a factory that chooses the next ID by mutable counter/queue.
3. Subsequent MealPlan/Selection IDs may be run-local only if independent input parity and selection results prove they do **not** affect recipe/member tie ordering. The stable Household/Member and RecipeVersion UUIDs are test-only v4-*shaped* identifiers, never production/security identities. Output Plan/Event/Serving IDs must still be generated naturally by actual services/UoW.
4. If an operation-scoped binding cannot reproduce current source/service behavior or a new production signature becomes required, **STOP** for a separately approved amendment. Do not rewrite `HouseholdService` or Planner silently.

The current [normal Household composer](../../backend/app/persistence/sqlalchemy_core/household_composition.py) remains providerless. The test-only driver is a **separate future implementation** and may not alter it just to simplify wiring.

## 6. Review checklist and exact STOP/GO boundary

A reviewer can accept the **proposal to prepare B** while still rejecting a completed B freeze. Full B acceptance requires independent evidence for every field group below.

| Required check before the first Planner run | Current disposition |
| --- | --- |
| Owner/reviewer accepts proposed distinct forward week, profiles, schedule, shares and exclusions with no outcome-based tuning | **PENDING OWNER** |
| Accepted immutable source revision and separate reviewed **raw** A manifest with complete unique v1/v2 records and six-kind allowlist; external `expected_sha256`, `expected_stage_membership`, correction SHA pins | **NOT FROZEN** |
| Accepted immutable B `PR10_FF_INPUT_MANIFEST_V1`, external digest/pin and exact normalized PlannerConfig + logical household/members/selection profiles | **NOT FROZEN** |
| Full trusted candidate projection: active/verified, source/rights/process and version history; all current nutrition/form/energy/admission fields, plus UUID tie-order witness; no missing/UNKNOWN | **NOT VERIFIED** |
| Current accepted target energy and genuine selection/participation semantics for all three supported synthetic members; no fabricated kcal | **NOT VERIFIED** |
| Empty or actual Pantry/history/fixed events proved by independent readbacks; no fixed COOK_RECIPE injection | **NOT VERIFIED** |
| Trusted input hash and stage pins reviewed **outside the prospective run** before two separate processes start; no output-based changes | **NOT VERIFIED** |

**Current disposition:** `NO_GO_INPUT_MANIFEST_UNVERIFIED`. This new packet has **zero** positive Planner/MealPlan/Serving claims. A later B acceptance must be a **separate owner decision** tied to exact hashes and input revisions; this PR's merge does not approve B.

**Next permissible unit, after review:** one separately scoped, strictly **test-only** pre-run source/input **materialization + independent validation** PR (no Planner candidate week generation and no source/Schema/Planner code changes), reporting a complete proposed A and B byte artifact and deterministic frozen input inventory. Only after independent acceptance of those exact artifacts can another PR perform the actual **two independent Python/SQLite real-Planner runs**, preserve full raw receipts and request `PR10_FF_FIXTURE_REPRODUCIBLE=PASS`. If any input is missing, record NO_GO and stop.

**Adversarial acceptance for future materialization:** corrupt input A/B SHA or reviewer source commit; swap Member 2/3 ordinal/profile; change one preference/exclusion/energy share; change a source rights/status/ingredient form/nutrition Decimal or Step order; alter candidate order/tie witness; stale/revoked RecipeVersion; duplicate/missing/extra v2; rehash altered input without external pin; mismatched real Household/Member UUID/FK; nonempty hidden Pantry/history/fixed events; self-pinned after-run manifest. All fail closed **before** any Planner generation; no silent retry with different dates/seeds/inputs.

## 7. Scope and downstream flags

**This PR only:** one independently reviewable docs/source pre-run freeze packet and concise `state/current-focus.md`, `state/progress.md`, `state/handoff.md`. **No** code, source curation, synthetic household creation, Planner generation, schema/migration, Nutrition, Shopping, Prep, PDF, UI, AI, Retail, source hashes accepted as new evidence, release signals or automatic merge. Verification: exact-head docs CI, diff scope/whitespace, relative links and repository source SHA check.

**Still hard blocked:** `PR10_FF_FIXTURE_REPRODUCIBLE=NOT_PROVEN`, `NO_GO_TO_PR10_CORE_RUNTIME`, `APPROVED_IMMEDIATE=0`, `SAFE_BATCH_READY=false`, `PORTION_RELEASE_READY=NOT_PROVEN`. D3 active reviewed actionable steps, Gate2, safe batch and portion release remain independently gated. The historical #196/#246/#254 receipts are immutable and **never** treated as the new forward week.
