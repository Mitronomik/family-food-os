# PR10-CORE-A — reproducible synthetic Gate2 fixture, ID-independent semantic identity

**Status:** **DOCS-ONLY IMPLEMENTATION CONTRACT GATE — PROPOSED FOR INDEPENDENT REVIEW.** Owner approved **Option A** on 2026-10-27: **preserve the 2026-09-14..20 accepted three-member, 21-event, 42-Serving semantic week** from PR #196 / merged PR #244, without changing production Planner behavior. This document does not authorize or implement the future fixture runtime, SQL changes, eligibility policy or PR10-A.

**Accepted base:** `main@3c4645a27d675bb4464c913785aef3cd88de8681` ([PR #244 merged](https://github.com/Mitronomik/family-food-os/pull/244), 2026-10-27). [PR #242](https://github.com/Mitronomik/family-food-os/pull/242) was closed **without merge**. [PR #246](https://github.com/Mitronomik/family-food-os/pull/246) is **OPEN**, with independent actual-week drift evidence, not yet accepted in main; Option A must not silently merge/rewrite it or claim its source drift result was accepted by merge.
**Tracking:** [Issue #247](https://github.com/Mitronomik/family-food-os/issues/247).
**Proposed machine snapshot:** [all original 21 source-coded events, 42 exact member Decimal factors and independently computed UUID-independent digest](pr10-core-option-a-frozen-semantic-reference-proposal-2026-10-27.json).
**Authorities:** [Operating Manual](project-operating-manual.md), [Master Roadmap Gate2/PR10](master-roadmap.md), [Option B technical versus safe-release gates](pr10-option-b-staged-delivery-gates-2026-10-17.md), [D3 eligibility/anti-rollback](pr10-core-step-eligibility-d3-contract-2026-10-22.md), [21-event research triage](pr10-fixture21-action-class-review-2026-10-23.md), [PR10 #196 fixture integrity receipt](pr10-meta-gate2-fixture-evidence.md), [Planner member-pattern architecture](architecture-addendum-2026-09-13.md).

## 0. Independent review corrections — 2026-10-29 (docs-only)

These corrections respond to [the independent PR #248 review](https://github.com/Mitronomik/family-food-os/pull/248#issuecomment-6491422149). They **do not** approve a runtime fixture, establish a portable source right, replace production process hashes, or relax Gate2/D3. The 21/42 candidate reference and accepted Option A decision remain unchanged.

### P1: original-source archive — **PUBLISHED ON PR BRANCH; byte integrity independently verified**

The real PR #196 ZIP contains exactly one `pr10-meta-fixture-receipt.json` member, **110,511 uncompressed bytes**, raw JSON SHA-256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`. PR #246's equivalent has the same uncompressed length and SHA-256 `2caa45e1e50639eef2b6f9023496cbce9fc35a88bd4c71f86e2b8a9daee0c78d`. Both were independently downloaded and byte-hashed; the original is synthetic QA evidence, **not** a customer record or production seed. GitHub API currently reports artifact #11672432141 expires **2026-11-09T14:24:01Z**, and #12730572293 expires **2026-11-26T11:19:28Z**. These dates describe ephemeral Actions storage, not an archive policy.

The **complete, unchanged, synthetic** raw PR #196 JSON has now been published directly in the PR branch as [`docs/family-food/evidence/pr196-original-synthetic-fixture-receipt.json`](evidence/pr196-original-synthetic-fixture-receipt.json). [Evidence provenance and verification instructions](evidence/README-pr196-original-synthetic-fixture.md) pin the source GitHub Actions run/artifact, original ZIP member, 110511-byte length, SHA-256 `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec` and Git blob SHA-1 `e82f147be4f7d1c67fe298ce973a968223910d03`. The archived GitHub blob was fetched back and independently **SHA-256 hashed from its raw UTF-8 bytes**; it equals the original artifact digest. The original test evidence has no detected emails or credentials. The historical 21-event compact reference is **not** a substitute for this full receipt. Long-term availability in `main` remains subject to a separately authorized PR merge; archiving in an open PR does not itself accept its architecture or runtime proof.

Independent reviewers MUST fetch the archived object directly from the PR branch, compute SHA-256 of its raw JSON **bytes** (do not parse/reformat before hashing), assert `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec`, then independently derive the UUID-free `731ef32e…` comparator. A missing/mutated/unreadable archive reopens **`NO_GO_EVIDENCE_NOT_DURABLY_PINNED`** and forbids merge/runtime; the archive is presently **PUBLISHED_AND_BYTE_VERIFIED_ON_PR_BRANCH**, pending independent human review and authorized merge. No short-lived signed artifact download URL belongs in versioned docs.

### P1: distinguish run-local RecipeStep IDs from portable process content

Independently comparing the two actual raw receipts at equal canonical codes gives **51/51 matching** source name/recipe ID/version/document SHA and **51/51 matching** ordered `(position, instruction_sha256, stage_code)` tuples, but **0/51 matching** `catalogue[].process_hash` values. Reason: `scripts/audit_pr10_meta_gate2_fixture.py` hashes whole `steps`, including per-run `recipe_step_id`. Therefore the existing `process_hash` remains a **run-local persisted Step-binding pin**; equality of that field across fresh databases is *not* required and cannot safely diagnose source-process drift by itself.

**Proposed QA-only portable process-content V1**, computed independently for each recipe (NOT a production hash/RecipeVersion identity):

```python
payload = {
    "canonical_code": recipe["canonical_code"],
    "source_name": recipe["source_name"],
    "source_recipe_id": recipe["source_recipe_id"],
    "source_version": recipe["source_version"],
    "source_document_sha256": recipe["source_document_sha256"],
    "ordered_steps": [
        {
            "position": step["position"],
            "instruction_sha256": step["instruction_sha256"],
            "stage_code": step["stage_code"],
        }
        for step in sorted(recipe["steps"], key=lambda s: s["position"])
    ],
}
digest = sha256(json.dumps(
    payload, sort_keys=True, ensure_ascii=False,
    separators=(",", ":")
).encode("utf-8")).hexdigest()
```

Assert unique consecutive positions, nonempty instruction digest and no duplicate canonical code; reject changed source identity/version/document SHA, step text/order/stage. A catalogue-level diagnostic can hash a map `{canonical_code: per_recipe_digest}` with the same JSON canonicalization. On both verified 51-recipe source receipts this **QA-only aggregate** equals `d19f11a0074d095eaac02fc1d414a1f3d6a5088a884c78d27436984a63023d36`. This digest is independently derived diagnostic evidence, **not** a new accepted platform catalogue hash or authoritative eligibility status.

**2026-10-29 reviewer P2 correction:** the originally written `2e04ea180cfcad031bad763aedec16be802fcbdcad2e9d1763c43d4c0b4edac9` was wrong for the published algorithm. The independently recalculated SHA-256 above (`d19f11a0074d095eaac02fc1d414a1f3d6a5088a884c78d27436984a63023d36`) uses **exactly** SHA-256 of the canonical JSON map `{canonical_code: per_recipe_digest}`. Both independently acquired #196 and #246 JSON receipts yield this corrected value. Keep the historical UUID-independent **weekly meal** digest `731ef32e7137740ed5b46a6044a85d8b2f818a847fdc039842460d442df5aeb6` unchanged; that is a different comparator.

Offline regression: `python -m pytest -q backend/app/tests/test_pr10_option_a_process_content.py`. The test reads the repository-archived original 110,511-byte receipt, checks its raw-byte SHA256 and 3/21/42 source semantics, calculates the documented portable digest, asserts that changing disposable Step UUIDs and run-local `process_hash` does **not** change it, and detects source/ordered-Step tampering and duplicate recipe codes. It does not call `PlannerService`, publish eligibility, or assert cross-run historical Planner input parity. To compare a new outside CI receipt, apply exactly the same published algorithm to that independently hash-pinned JSON; never substitute an ephemeral CI digest without raw provenance.

The raw receipts **do not expose rights review fields**, current RecipeVersion lineage or complete source-process text. A matching portable content digest alone **does not** approve source rights or a Prep action. Future implementation must separately rebind actual current `RecipeVersion` and ordered `RecipeStep` with verified rights/status and live run-local UUID/process hashes, and fail closed on missing rights or Step changes. Retain current source/Step-version/anti-rollback requirements.

### P2: seed/ID dependency inventory — injection **not yet available end to end**

Observed production interfaces:
- `backend/app/services/food_recipes.py::FoodRecipeCatalogueService(..., id_factory=uuid4)` accepts a constructor ID factory; `_new_detail` obtains RecipeVersion, RecipeIngredient and RecipeStep UUIDs from it.
- `backend/app/persistence/sqlalchemy_core/food_recipe_composition.py::create_food_recipe_catalogue_service(engine)` **does not expose** an `id_factory` parameter.
- Existing fixture calls `seed_dc4_a3_russian_step_corrections(config)` → `seed_r3d_final_dc3_batch(config)` → `seed_r3c_school2022_main_batch(config)` (with additional earlier R3/R2 prerequisites); those seed modules construct catalogue services through the normal composition entrypoint. This is a **partial dependency map**, not a claim that the full seed chain accepts stable IDs.
- `scripts/audit_pr10_meta_gate2_fixture.py` creates Household/Member/MealPattern after source seed; its run-local IDs, exclusions and persisted MealPlan/Serving FKs must be independently resolved. The historic receipt contains UUID-to-canonical RecipeVersion mappings, but reusing them is not yet authorized or proven sufficient.

A later implementation PR must inventory **all** earlier seed constructors and ordering, choose a narrowly scoped test-builder ID factory/identity strategy, document collision and source-history handling, and demonstrate the normal original seeding + `PlannerService.generate_authoritative` + persisted readback. No global UUID monkeypatch, direct SQL mutation, production composition default change, recipe replacement, candidate score/pool/tie-break override or bypass of normal Planner selection. If preserving historical RecipeVersion identity requires a production code change or unavailable rights/source authority, **STOP and reopen the contract**. The existing UUID tie-break is a *plausible* drift mechanism, not a proven sole cause.

### P2: full historical Planner input parity is **not proven by receipts**

The original receipt exposes `planner.version`, a **UUID-bearing** `request_fingerprint`, trace fingerprint, 3 member ordinals, 51 catalogue source rows and the 21×42 output. It **does not contain a serialized original PlannerRequest** or authoritative standalone input manifest. A new fixture needs evidence for:

| Required input | Current evidence / outstanding action |
| --- | --- |
| Historical source code revision and seed chain | PR #196 / Actions run #38059374826 known; exact run code SHA and all nested seed builder versions must be independently pinned before a PASS |
| Algorithm/config | `planner-v0.5` observed in receipt/current `scripts/audit_dc4_corpus_readiness_rerun.py::PLANNER_CONFIG`; weights/repetition/compatibility version must be pinned from historical code, not guessed from today |
| Candidate pool/nutrition | 51 current eligible RecipeVersions with source IDs and calories derived through catalogue/nutrition services; historical admission scores/exclusion/energy readiness and source versions must be checked against accepted run |
| Member patterns and ordering | `GATE1_ROLE_SHAPES[2]`, custom accepted selection and fixture ordinal → generated member UUID mapping; original historical builder revision and exact opportunities/allocation shares required |
| Member reference energies | Derived by the historical fixture member builder and nutrition target service; **not printed in original receipt**; must be reconstructed and reviewed from pinned historical code, not back-solved from output |
| Exclusions, preferences, Pantry, history, fixed events | Current source constructs `_fixture_exclusions` and default request values; prove historical values and absence/presence explicitly from a pinned historical builder |
| Cross-run integrity | Same 21 source/date/role/position codes, 42 exact positive Decimal factors, source rights and current Step pins, normalized external SHA `731ef32e…`, two isolated SQLite processes and independent persisted readback |

If input parity cannot be established, record **`NO_GO_OPTION_A_INPUT_PARITY_UNPROVEN`**, not a snapshot-replay PASS. A code change solely to make the historic digest pass is forbidden. Preserve the independent full Planner→MealPlan Gate2 requirement and all separate Prep/portion/safe-batch blockers.

### Required negative checks for the later fixture-only PR

Besides §5's existing tests, prove that a changed Step instruction digest/position/stage, current rights/status, source code/version/document, altered original raw-archive bytes, one scheduled recipe slot, member ordinal, one exact Decimal digit, wrong Household relation, duplicate slot or non-Planner rehydration **fails closed**. Run-local UUID process hashes may differ while portable content matches; missing archive access or original Planner-input parity must never produce a false PASS.

**Review outcome:** source retention is now **PUBLISHED_AND_BYTE_VERIFIED_ON_PR_BRANCH**; **Option A runtime/input parity is still NOT demonstrated**, and independent contract review plus explicit owner merge remain required. `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME` persists. No automatic merge.

---

## 1. FACT — why the existing fixture is not cross-run reproducible

Two authentic official GitHub Actions artifacts were independently retrieved and their raw **JSON bytes** SHA-256 checked:

| Run | Raw artifact JSON SHA-256 | Planner `expected_semantic_pins_sha256` | 3/21/42 | Source recipe schedule |
| --- | --- | --- | --- | --- |
| [PR #196 / run 38059374826](https://github.com/Mitronomik/family-food-os/actions/runs/38059374826), artifact 11672432141 | `6c157ddead856ca2d109a698f221fc89472fda897c8f6473ceea0672afed04ec` | `2d6cb581649863b7edbd3c0efff2bae2934c6a512c99a45d10e92f92f514cb3d` | PASS | **Accepted historic 21 MealEvents used by #244** |
| [PR #246 / PR10-META run 40495153021](https://github.com/Mitronomik/family-food-os/actions/runs/40495153021), artifact 12730572293 | `2caa45e1e50639eef2b6f9023496cbce9fc35a88bd4c71f86e2b8a9daee0c78d` | `1720db1d309a8a346af81cba37e27b07044c205112d6fdd711b938803567bcf2` | PASS | **0/21 matching date/position recipe codes**, only 7/21 recipe codes overlapping as a set |

The accepted [`scripts/audit_pr10_meta_gate2_fixture.py`](../../scripts/audit_pr10_meta_gate2_fixture.py) `_receipt_semantic_events` and `_planner_semantic_events` include **generated `recipe_version_id` and `member_id` UUIDs**. Its old independent semantic SHA is correct **for that run**, but **must not be used as a portable cross-run equality check**. In fact, the accepted `PlannerService.generate_authoritative` / `generate_week` implementation sorts candidates and uses `candidate.recipe_version_id.hex` as the **third tie-breaking key** under equal eligible count and score (see [Planner domain](../../backend/app/domain/planner.py)). Each fresh SQLite seed can mint different catalogue UUIDs, so the same verified recipe catalogue and Household shapes **may legitimately yield different selected recipe codes**, even when each *within-run* pure Planner replay is deterministic. This dependency is confirmed in source. Its exact causal contribution to the two historical outcomes has **not been isolated experimentally**; do not claim a proven sole root cause or "fix" the production tie-break in this task.

The old week includes on **2026-09-18 BREAKFAST** `SCHOOL2022_54_1T_COTTAGE_CHEESE_CASSEROLE` and on **2026-09-19 BREAKFAST** `SCHOOL2022_54_1K_LIQUID_CORN_MILK_PORRIDGE`. The current drift run included cottage cheese on **2026-09-20 BREAKFAST** and omitted corn milk porridge altogether. Therefore the [#244 candidate pair](pr10-fixture21-action-class-triage-2026-10-23.json) **cannot currently be asserted to exist as two separate actual MealEvents**. `APPROVED_IMMEDIATE=0`, `NO_GO_TO_PR10_CORE_RUNTIME` remains.

## 2. DECISION — Option A scope and immutable semantic reference

**Approved direction:** freeze the **old week as a synthetic QA-only test fixture** and make its identity stable across new test databases without treating historic ephemeral UUIDs as consumer/domain truth. Preserve **exact** 21 event date/order/role/source code, original source recipe identity and **42** member-specific positive Decimal `Serving.portion_servings` values. Member identity in the portable reference is **test-local ordinal 1/2/3**, not an actual HouseholdMember UUID. Source recipe identity is `(canonical_recipe_code, source_recipe_id, source_version, source_document_sha256)`; the reader must bind it to a **fresh current** verified RecipeVersion and ordered RecipeSteps and reject mismatched rights/text/form.

**Proposed reference V1** (same PR, not executable authority): [`pr10-core-option-a-frozen-semantic-reference-proposal-2026-10-27.json`](pr10-core-option-a-frozen-semantic-reference-proposal-2026-10-27.json).

- It was transcribed from the **original PR #196 raw JSON artifact** whose hash is independently pinned above, not from #244's text flags nor the altered fresh run.
- Its **UUID-independent semantic digest**, calculated off-repository by canonical JSON from the original artifact, is `731ef32e7137740ed5b46a6044a85d8b2f818a847fdc039842460d442df5aeb6`. This is a **proposed research proof** until an independent reviewer recalculates it directly from the independently trusted original raw artifact. A self-declared digest in the proposed JSON is not a signature.
- Expansion rule: each compact row `[local_date, position, role, canonical_code, source_recipe_id, [[member_ordinal, portion_servings], …]]` becomes `{local_date,position,role,source_kind:"COOK_RECIPE",canonical_recipe_code,source_recipe_id,source_version,source_document_sha256,servings:[{member_ordinal,portion_servings}]}` where source version/document hash is looked up in the explicitly pinned source prefix table (School2022 and MR2019); sort events by (local_date,position) and member allocations by numeric ordinal; UTF-8 JSON with `ensure_ascii=false`, `sort_keys=true`, `separators=(',', ':')`, SHA-256. Exact finite positive Decimal strings preserved, no float conversion, no generated IDs in normalized reference.
- Normalize the new `main` PR #246 run by the **same algorithm**: its independently calculated UUID-independent semantic SHA is `1db25794cca0fdf8757143c9bb317a12f4765b296bbab865b36c71054cdcb2f2`, still different. This proves mismatch is not merely an artifact of ephemeral UUID fields.

**Do not confuse the three identities:** (i) original PR #196 **raw JSON artifact** is the external audit anchor, (ii) frozen **ID-free semantic week** is an immutable synthetic QA comparator (once reviewed and accepted), (iii) each **current** generated MealPlan/RecipeVersion/RecipeStep/Member UUID is an ephemeral, Household-scoped row binding that must be re-read and validated anew. No historic UUID is presented as a current real-family ID.

## 3. Proposed test-only fixture stabilization seam, before any code

The implementation target is a **stable reproducible synthetic fixture generator** layered around the existing seeding/composition harness, **not** any modification of production `backend/app/domain/planner.py` candidate scoring, ranking, tie-breaks or consumer Planner API. The real existing `PlannerService.generate_authoritative` and repository/UoW path must still execute, persist a genuine MealPlan and produce legitimate Servings.

**Bounded proposed implementation algorithm:**

1. Independently validate the original source artifact JSON SHA, parse the proposed 21-row V1 reference and independently recompute its UUID-independent digest. Reject even a **self-consistently rehashed altered fixture** that fails the external trusted source anchor or accepted source/rights pins. Preserve the original 3 heterogeneous meal patterns, reference energies, exclusions and input food catalogue; they are **inputs**, not values to tune to force the answer.
2. Create each fresh SQLite database in a throwaway temp directory and use **test-only stable ID provenance** at the existing constructor/service/seed **`id_factory`/trusted seed** seams where available. The deterministic identity mechanism must be limited to **fixture builders**, never enabled in ordinary runtime/production seed or user flows. If historical recipe version tie-break IDs must be supplied in the test database to reproduce PR #196, a reviewer must approve an explicit external archived mapping of original `canonical_recipe_code → fixture-only RecipeVersion UUID`, plus source and rights/provenance consistency; the mapping is **not a new domain identity contract**. Do not rewrite live tables, disable FK checks, forge source Version lineage, patch global UUID functions or sneak a product schema change.
3. Run the **unchanged** Planner `generate_week` and `PlannerService.generate_authoritative` real request path from this test-only fixture, persist/read-back with the existing synchronous UoW. Independently verify the request metadata, accepted MealPatterns, exclusions, source forms, meal opportunity order, reference energies and original catalogue provenance, and check that the selected **21 actual MealEvents**, each member's **42 exact finite Decimal `Serving` factors**, roles and source codes match the proposed reference.
4. For every generated event, independently rebind its **actual** Household/Member/RecipeVersion/RecipeStep UUID and source document, process instruction SHA / ordered positions; validate no cross-Household joins. Persisted UUIDs **may differ between runs**; the canonical 21-event semantic digest **must not differ**. If stable seeding requires additional test-only factory hooks, scope the smallest isolated test-helper change and focused tests separately after this gate's merge.
5. Repeat the **complete fresh SQLite seeding + Planner generation + readback at least twice independently** (separate processes/temp databases), requiring the **identical** UUID-free semantic digest `731ef32e…` and identical exact source/participant semantics, as well as within-run pure Planner replay. Re-run after a process restart and CI environment reinstall to challenge reliance on process state, hash randomization or CI ordering. A new catalog version/source process change **fails closed** to a new docs/data review, not a silent reference refresh.
6. Publish a **test-only, independently reviewed evidence artifact** with the externally anchored source digest, synthetic fixture/schema version and both run-specific UUID/source pins plus exact per-member Decimal quantities. The positive **fixture reproducibility** outcome does **not** approve physical Prep actions, source step classifications, Pantry movements, storage/freezing, or Gate2 end-to-end acceptance.

**Critical stop rule:** merely *rehydrating the old MealPlan rows* or manually copying 21 recipe codes into persisted tables is **not proof of current real Planner selection** and cannot qualify as Gate2's Planner→Prep vertical slice. Such a snapshot-only path may be used in isolated downstream unit tests **if separately labelled as replay-only**, but the Gate2 acceptance proof still requires the real backend Planner selection path returning the frozen semantics. **Do not** filter/inject a Planner candidate pool, add per-slot selection overrides, bias preference weights or alter the Planner algorithm just to force a PASS; those change the fixture conditions/architecture and need an explicit revised owner decision. If the unchanged Planner + test-only stable IDs cannot reproduce old source/event/Serving semantics, stop with `NO_GO_OPTION_A_UNACHIEVABLE_AS_SCOPED` and explain exact blocking dependency; do **not** silently switch to Option B.

## 4. Implementation gate inventory, preservation and replay

| Boundary / risk | MUST preserve / required future evidence |
| --- | --- |
| Versioned QA artifact | Stable `fixture_id`, `snapshot_schema_version=1`, external PR #196 raw JSON sha and ID-free digest `731ef32e…`, full 21/42 coverage and immutable member ordinal semantics; no production identity or source-of-truth status |
| Planner, MealPatterns, member energy and exclusions | **Unchanged product behavior**; three heterogeneous accepted patterns, source-backed candidate constraints, actual exclusion checks and original quantity allocation semantics. Test-only ID injection must **not** alter nutritional scoring/configuration/candidate pool |
| Catalogue, RecipeVersion, FoodIngredient and rights | Resolve immutable `canonical_code+source_recipe_id+source_version+source_doc_sha` to current verified/rights-reviewed RecipeVersion, ingredients and ordered steps; only repository-local source pins, no new FoodIngredient normalization or source re-publication |
| ID scope and persistence | Original UUIDs only if used as explicit **isolated synthetic test identity hints**, never production Household/MealEvent/Serving FK facts. SQLite temp, migrations unchanged, synchronous UoW, validated fresh UUID bindings and no cross-Household read/write |
| Fresh and same-payload replay | Each fresh run: 3/21/42, identical 21 codes/date/role and original Decimal per-member amounts, ID-free digest matched to immutable baseline. Exact replay must not append duplicate fixture events or mutate source |
| Conflicting fixture/reference | Wrong source card/hash, changed RecipeVersion/process, member order or Serving, duplicate slots, old receipt tamper, new source rights, changed Planner configuration, seed identity drift, unequal digest → **explicit NO_GO / no false PASS** |
| Rollback and clean-up | Test-only temporary DB discarded on success/failure; no transaction partial write exposed; future failed seed/fixture build must leave no accepted reproducibility receipt. PR/CI rollback never upgrades an unreviewed Prep step |
| Prep/Shopping/PDF derived authority | Fixture is a *test harness input/evidence*, not an accepted MealPlan for users and never authorization to consume Pantry. D3 publisher+live anti-rollback remains separate; `APPROVED_IMMEDIATE=0` before qualified Domain/QA review |
| Source and release gates | This reference cannot prove finished-dish safe holding/freezing/reheat or Planner Serving quality/portion plausibility. `PR10-FD-META=BLOCKED/TIME_UNRESOLVED`; `SAFE_BATCH_READY` and `PORTION_RELEASE_READY=PASS` still unmet |

**Dependency order for the next bounded implementation PR (AFTER contract merge):** independently audited source artifact/reference → fixture-only ID/seed binding → normal Planner generation → persisted MealPlan readback → normalized digest from current rows → focused adversarial tests + 2 independent CI runs → signed-off fixture reproducibility evidence. No new database migration, new web source reader, production API or Consumer surface. If the test-only seed identity seam reveals a new schema/cross-context mutation or cannot preserve source authority, **reopen a docs-only Implementation Contract Gate** rather than expanding code scope.

## 5. Explicit adversarial acceptance and verification tier

A later PR must provide tests **at least** for these source-/identity-specific risks:

- Change one historic recipe code, local date/position/MealRole, source recipe ID/version/document hash, or member ordinal → normalized hash mismatch and **NO_GO**.
- Change one `portion_servings` digit, duplicate a Member/MealEvent pair, remove one of 42 Serving values, introduce negative/zero/`NaN`/`Infinity`, or round through `float` → **NO_GO**. Source weights are Decimal and test-run-scaled grams are projections, not safe-cook capacity.
- Use 21 valid alternative recipes or preserve structural 3/21/42 counts with **different** combinations → **NO_GO** (proven historical bug pattern).
- Same original 51 verified recipe identities but changed source rights/current source document/RecipeVersion process hash or missing catalogue recipe → **NO_GO**, no rebind by name alone.
- Synthetic role-pattern shape/selection/exclusions or Planner config drift → **NO_GO**, not an automatically accepted new reference.
- Two independently seeded SQLite runs with different random UUIDs must give **exactly the same reference week** if Option A claims PASS; do not pass merely from each run's internal pure replay fingerprint.
- Deliberate attempt to bypass Planner with manually rehydrated MealEvents/Serving, change test-time candidate selection/weights or weaken the independent original archive digest → **NO_GO** for full Planner fixture proof.
- Attempt to present either R2-E `Творог протереть` or R3-B `Перебрать и промыть кукурузную крупу` as a **real executable** Prep task from the frozen snapshot, even with correct ingredient grams → **NO_GO** until an independently accepted D3 policy/reader and reviewer verifies both entire steps.
- Anti-rollback eligibility status `approved → revoked → rollback → no executable task` remains a **separate future D3 test**, not part of this test-fixture publication. No storing or freezing claims.

**Verification for this docs-only PR:** check source reference rows and 42 original Decimal values against external PR #196 artifact, independent normalized hash for both source artifacts, links/JSON/counts, absence of production/migration changes, text/JSON consistency, `git diff --check`-equivalent and exact-head Docs CI. No Python/backend tests are claimed for a docs-only contract.

**Verification for later implementation PR:** focus tests on test-only fixture identity, the existing PR #196 `validate_fixture_receipt`, actual Planner/MealPlan persisted service path, source/rights/quantity and negative tamper tests; run exact-head CI **twice in independent temp DBs**, inspect both artifact bytes/digests, and one broader tier only if code beyond isolated harness changes. Any code change after an exact-head receipt invalidates that receipt. Do not claim a PASS until independent QA signs off.

## 6. FACT / ASSUMPTION / DECISION / OPEN — stop for review

**FACT:** both current and original workflow receipts have valid 3/21/42 structural counts, but zero selected code/date matches and distinct UUID-free digests. Existing Planner uses UUID-based tie breaking; the historical week's external raw JSON and full per-member factors are available for audited normalization. Option A has explicit owner direction.

**ASSUMPTION:** an isolated and accepted test-only identifier/seed seam can reproduce exact original Planner candidate selection under unchanged source corpus/real algorithm. **Not demonstrated** by this docs gate; a fixture snapshot alone proves nothing about the reproducibility of backend Planner generation.

**DECISION (owner):** Option A: preserve **exact original 21 MealEvents, 42 Member Servings and source identity** as a versioned synthetic test reference. **Proposed bounded implementation method** must be independently reviewed under the above test-only constraints before any code; no direct runtime/Schema/MealPlan acceptance change.

**OPEN for independent reviewer:** does existing seed/service `id_factory` provide sufficient seam to replay the historically selected recipe-code order without touching production Planner? Is an external archived UUID→source mapping test-only acceptable and sufficient? Do source/RecipeVersion/MemberMealPattern data exactly match historical conditions? How will the fixture generator prove real Planner provenance rather than snapshot masquerading as Planner output? A negative result is an acceptable independent **NO_GO**, not a reason to invent an alternative acceptance.

**NEXT only after independent docs review and owner merge:** one focused fixture-only PR and two independent evidence runs, then independently review two R2-E/R3-B whole process instructions at actual member amounts, then separately authorize D3 trusted publisher/reader and finally PR10-A. **No automatic merge, migration, production Planner change, RecipeVersion republish, Prep/PDF/PWA runtime or Gate2 pass.**
