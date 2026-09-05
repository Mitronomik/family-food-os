# PR4 — official equivalent acquisition remains unavailable

## FACT

Latest [Orchestrator decision](https://github.com/Mitronomik/family-food-os/pull/10#issuecomment-5554016049),
`2026-09-05T18:48:54Z`, authorizes official canonical/equivalent retrieval URLs.
It supersedes only the earlier exact-historical-URL constraint. No new permission
is needed to retrieve the same source through an official equivalent endpoint.
Starting head: `7e155013a5c5a3fea42ec91930f7a1a6e06ef582`.
Main and synchronization remain `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`
and `dfcbce2814b46da45cf346762a778170ffc5b36c` respectively.

The blocking source is **SNAP6-HEAVENLY-DEVILED-EGGS**:

- Accepted URL: `https://snaped.fns.usda.gov/snap/cookbooks/EasterMenu.pdf`.
- Accepted SHA-256: `1fdc16568f024a68c7fb8ef94349d7436b0a86c2a6cbd4b310ed1d117720e71f`.
- Current official PDF: `https://snaped.fns.usda.gov/sites/default/files/documents/EnglishEaster508_1.pdf`.
  HTTPS client: TLS EOF; browser: Access Denied.
- Current official recipe: `https://snaped.fns.usda.gov/resources/nutrition-education-materials/recipes/heavenly-deviled-eggs`.
  HTTPS client: TLS EOF; web retrieval: HTTP 403.
- Current official collection: `https://snaped.fns.usda.gov/resources/recipes-and-menus/healthy-thrifty-holiday-menus/easter`.
  Browser: Access Denied.
- Linked official MyPlate recipe: `https://www.myplate.gov/recipes/supplemental-nutrition-assistance-program-snap/heavenly-deviled-eggs`.
  Browser: Forbidden; curl: exit 35, TLS connection failed, no HTTP response body.

The non-print WIC grilled-cheese route returned 403. Current www.fns.usda.gov
paths for tnc-eggs.pdf, tnc-applesauce.pdf and HarvestofRecipes.pdf also failed
with TLS EOF. A discovered public USDA staging recipe URL was inspected only
as a candidate, failed acquisition, and was not adopted as canonical provenance.
[Machine-readable attempt evidence](pr4-provenance-refresh-attempt.json) contains
the exact URLs and failed request times under `official_equivalent_fallback_pass`.
The six-URL Python batch was repeated once while loading its helper; both failed.
The stored batch records are the later attempts, not successful retrieval events.

## ASSUMPTION

The failure may be environment-specific or temporary; it does not establish
worldwide disappearance. Search-reader text suggests an extra handwashing
instruction in current Easter sources, but this cached discovery output is not
accepted as a fresh source or an established authoritative diff. No recipe or
rights change is claimed without complete current bytes and review.

## BLOCKER

**PR4 SOURCE DRIFT BLOCKER — current-source acquisition unavailable.**
The tested official equivalent paths did not yield a complete current source
representation for the exact accepted recipe. Fresh URL/hash/fact comparison
and rights-notice review therefore remain unavailable. Both authoritative drift
and rights drift are **unassessed**; zero drift cannot truthfully be certified.
Production hash/retrieval instant remain null for failed requests. Denial pages
and old locally saved bytes were not promoted to source artifacts.

Historical retrieval evidence remains reusable for **3** artifacts. Fresh
byte-identical artifacts: **0**. Accepted presentation successors: **0**.
Changed-hash successor list and accepted production fallback URL list: **empty**.
Remaining acquisition: **22 distinct artifacts / 27 recipes**. Accepted DATA2
is unchanged; no corpus selection, quantities, rights, mappings or hash was edited.
Production correction and first/second fresh seed remain pending this gate.
No corrected step count or production row-count acceptance is claimed.

## OPTIONS / RECOMMENDED DECISION

1. Obtain complete bytes of these same official sources through a working client
   with URL/redirect lineage and a UTC completion instant recorded at retrieval.
   Keep binaries temporary and run the authorized recipe/rights comparison.
2. Resume acquisition when these official endpoints are accessible from this
   environment. Do not repeat historical-log recovery or substitute recipes.

Recommended: restore/provide a working official acquisition path under the
existing authorization, then continue this same PR through production correction
and the complete verification matrix. Further URL-fallback permission is not
the missing prerequisite. PR4 remains blocked; PR5 remains unauthorized.

## Verification in this pass

Only task-local evidence, documentation and state changed. Current checks:

- DATA2 validator: **PASS: final DATA2 gates**.
- DATA2 focused: **164 passed in 4.71s**.
- Preserved PR4 domain/application/architecture/migration/persistence, excluding
  obsolete seed: **43 passed in 5.41s**.
- Affected PR4-DATA/FoodIngredient regression: **82 passed in 3.02s**.
- Ruff over all 24 PR Python files: **24 files already formatted; All checks passed!**
- `git diff --check`: **PASS**. Accepted DATA2 has no diff against accepted main.
- Staged scope is restricted to six PR4 evidence/README/state files. No binaries,
  source HTML, browser history, private records or production changes.

Full PR4 seed suite, fresh first/second seed and full backend+launcher were **not
run**: the source gate stopped production correction. These baseline checks do
not establish corrected production readiness. Earlier test counts below are
historical results from the previous pass.

---

## Historical previous pass — exact-URL acquisition

# PR4 — authorized refresh: current-source acquisition blocker

## Current decision and FACT

The [Orchestrator decision](https://github.com/Mitronomik/family-food-os/pull/10#issuecomment-5553524319)
posted `2026-09-05T17:26:45Z` authorizes bounded fresh acquisition on this same
PR. It supersedes the historical missing-timestamp stop below. No further
permission to refresh the same corpus is needed. Accepted DATA2 is immutable.

Starting head: `17d23b22340a76dfa79420e74b97ce5703fc29a8`.
Accepted main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
Existing synchronization: `dfcbce2814b46da45cf346762a778170ffc5b36c`.

The three recovered historical completion records are reused exactly, without
searching old logs again. The remaining sources were grouped into **22 distinct
accepted artifacts for 27 recipes**, each requested once by the HTTPS client.
Results: **20 TLS EOF failures / 2 HTTP 403 failures**; no complete successful
source response. Request code was temporary curation tooling, not a new runtime
service or committed ingestion subsystem.

[Exact attempt evidence](pr4-provenance-refresh-attempt.json) records all 22
accepted URLs/hashes and affected recipe IDs. Additional ordinary-client checks:

- `SNAP6-HEAVENLY-DEVILED-EGGS`, exact
  `https://snaped.fns.usda.gov/snap/cookbooks/EasterMenu.pdf`, accepted SHA-256
  `1fdc16568f024a68c7fb8ef94349d7436b0a86c2a6cbd4b310ed1d117720e71f`:
  in-app browser **Access Denied**; Safari **secure connection failed**;
  system curl **exit 35 / SSL_ERROR_SYSCALL**. A web reader returned a PDF
  extraction labelled crawled seven months ago, which is not fresh evidence.
- `WIC1-BEYOND-BASIC-GRILLED-CHEESE`, exact
  `https://wicworks.fns.usda.gov/recipe/beyond-basic-grilled-cheese/printable/print`,
  accepted SHA-256
  `357700264ce2a7340cdab55639c5bc76ef6b25a58120baa9152d5b8f55bfe334`:
  in-app browser **Access Denied**; web reader **403**.
- The in-app browser displayed the tnc-eggs PDF, but a complete-byte export was
  not obtained through available supported controls. Display alone does not
  establish fresh acquisition, byte equality, notices equality or a new hash.

## ASSUMPTION

No source disappearance, recipe drift or rights drift is inferred from these
access failures. The cause could be temporary or environment-specific. Cached
reader output, existing saved files, rendered viewer state and failed request
times are not assigned a successful source retrieval timestamp.

## BLOCKER

**PR4 SOURCE DRIFT BLOCKER — subtype: current-source acquisition unavailable.**
At least EasterMenu.pdf and the WIC printable source cannot currently be
obtained as complete fresh representations through the tested permitted paths.
No accepted/fresh hash comparison or authoritative fact diff exists for them.
Zero authoritative drift cannot be certified; the result is **unassessed**, not
an invented clean comparison. The 22-artifact refresh remains incomplete.

Counts: historical records reused **3**; fresh byte-identical **0**;
presentation-only successors **0**; changed-hash successor list **empty**.
Production hashes/timestamps for failed requests are explicitly null. No new
lineage was marked acceptable. Accepted rights posture is unchanged and was
not reopened as the old blanket blocker.

Production compiler/loader/JSON correction, ordered steps, equipment population,
fresh DB seed runs and production counts remain pending this acquisition gate.
There is no corrected Recipe/Version/Ingredient/Step/Equipment count to report.
The accepted contract remains 30 / 30 / 189 / newly derived steps / 86, with
81 existing FoodIngredient codes and 34 equipment codes. No schema change,
new FoodIngredient, source replacement, future context or PR5 work occurred.

## OPTIONS / RECOMMENDED DECISION

1. Restore access to the same accepted URLs through a permitted retrieval path,
   or provide freshly downloaded complete artifacts with a contemporaneous
   URL/completion-UTC acquisition record. Compare each artifact under the already
   authorized unchanged-content / presentation-successor rules.
2. Retry this bounded refresh after the external access condition changes. No
   new source selection or weaker provenance rule is needed.

Recommended: make the current sources obtainable under option 1, then resume
this same branch immediately through the full PR4 correction and verification
matrix. Do not repeat the historical-log search or generate a timestamp for an
old file. Authorization remains active; the missing input is source access.

## Verification in this pass

DATA2 validator: PASS. The exact 22-artifact / 27-recipe attempt mapping and
three historical completion records are checked against accepted DATA2 and
previous recovery evidence. Accepted DATA2 and production runtime/compiler/seed
JSON remain byte-identical to the starting head. No production acceptance run
is claimed. Current verification:

- DATA2 focused: **164 passed in 4.19s**.
- Preserved PR4 domain/application/architecture/migration/persistence, excluding
  obsolete seed tests: **43 passed in 5.21s**.
- Affected historical PR4-DATA/FoodIngredient regression: **82 passed in 3.01s**.
- Ruff on all 24 Python files in PR #10 versus main: **24 files already formatted;
  All checks passed!** No Python implementation was modified this pass.
- Working/staged correction and PR-versus-main diff checks: **PASS**.
- Staged scope: six task-local documentation/state files; no source binaries,
  HTML, browser databases, credentials, local DBs or runtime changes.
- Full PR4 seed suite, fresh first/second seed and full backend+launcher: **not
  run**, source-acquisition stop before production correction. Frontend unchanged.
- No GitHub CI run is claimed.

## Implementation notes from independent read-only quantity audit

After acquisition succeeds, join the 189 purchase-form source-quantity rows to
the verbatim coverage CSV. Required/optional/conditional flags come from selected
semantics. Correct the old parser's mixed ASCII fractions and full unit words;
do not select an unselected frozen-spinach weight for a fresh bunch. Preserve
`2/3 package (10 ounces)` ambiguity without a mass conversion. Keep cooked pasta
and juice amounts with explicit preparation notes. Conditional retained water
must preserve both the 1-or-2-tablespoon choice and the source browning trigger.
These findings are implementation guidance, not a new DATA2 quantity decision.

## Historical report before refresh authorization — superseded execution status

The complete earlier report follows unchanged as evidence of the prior pass.
Its instruction to seek a fresh-acquisition authorization is no longer current.

# PR4 — DATA2 retrieval provenance blocker

## FACT

PR #13 has final ACCEPT on `918bf81b5da306fc65a57643de515ca1b3fbd1e4`.
Its merge is accepted main `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
PR #10 was synchronized by normal merge
`dfcbce2814b46da45cf346762a778170ffc5b36c`, preserving DATA2 byte-for-byte
and the existing PR4 implementation. Only state files conflicted; accepted-main
records were preserved with current execution/closure state layered above them.

The accepted corpus has exactly 30 source IDs, 189 selected ingredient rows,
81 existing FoodIngredient codes, 86 source-backed ordered equipment rows and
34 equipment codes. Forbidden ICN cards, Honey Lime Chicken and Local Harvest
Bake are absent. Rights are reviewed under the accepted narrow direct-FNS
project risk posture with source-specific evidence and contributor attribution.
This decision supersedes the old PR10 rights blocker; it is not unrestricted
reuse permission or blanket public-domain status.

All 30 final recipe entries record `checked_at: 2026-09-05`. The DATA2
`source-downloads.json` ledger likewise records a date, without per-artifact
retrieval instants. Exact market-research timestamps concern retail observations,
not recipe retrieval. The final ACCEPT event at `2026-09-05T16:06:13Z` is a real
review instant, not evidence of when a source was retrieved.

[Task-only recovery evidence](pr4-retrieval-provenance-review.json) lists the
exact final 30 sources, accepted hashes, artifact types and recovery results.
Three completed browser download records match both the accepted URL and the
current retained file's SHA-256, with complete byte counts:

| Accepted source | Recorded download completion (UTC) |
| --- | --- |
| CACFP6-CORN-EDAMAME-BLEND | 2026-09-04T04:35:40.896467+00:00 |
| CACFP6-TABBOULEH | 2026-09-04T04:35:52.082224+00:00 |
| CACFP6-CREAMY-COLESLAW | 2026-09-04T04:34:53.373753+00:00 |

No equivalent retrieval instant was established for the remaining **27 recipes /
22 distinct accepted artifacts**. The evidence file identifies each one rather
than treating every source as blocked indiscriminately. Browser download records
were queried read-only; a temporary copy of the locked browser history/WAL was
deleted after the task-specific query. No browser database, unrelated browsing
history, source binary, private path or local development DB is committed.

## ASSUMPTION

No date, file mtime, quarantine-registration time, Git commit time, review time,
or source PDF publication/creation date is assumed to be retrieval time.
A currently retrievable page is not assumed byte-identical to an accepted saved
HTML or browser-printed PDF artifact. Recovery may still be possible from an
original curator's acquisition log that was not available in the checked evidence.

## BLOCKER

The explicit PR10 correction instruction requires a real timezone-aware
`source_retrieved_at` and says to STOP when the exact accepted artifact lacks
one that can be truthfully recovered. The current schema requires an instant;
there is no authorized date-only substitution. The missing 27 instants prevent
an accepted DATA2 production seed without inventing provenance.

The compiler, loader, seed JSON and runtime tests have therefore **not** been
corrected or regenerated in this pass. Their obsolete corpus/rights/equipment
assumptions remain outstanding implementation defects. Existing seed flags are
not acceptance of those old records. The DATA2 corpus itself is unchanged and
remains accepted. PR4 is BLOCKED, not READY FOR FINAL REVIEW or COMPLETE.

## OPTIONS

1. Recover original acquisition/completion logs tied to the exact 22 hashes,
   persist the task-only timestamp evidence, then resume PR4 correction.
2. Explicitly authorize fresh acquisition of the same 30 selected sources with
   real completion timestamps. Compare original PDFs with accepted hashes;
   review any changed saved HTML/printed-PDF representation and approve its
   provenance successor before it drives production. Keep original DATA2 evidence.
3. Explicitly approve a date-precision provenance model and migration strategy.
   This changes the current schema/acceptance contract and is not implemented.

## RECOMMENDED DECISION

Seek exact acquisition logs first. If unavailable, authorize option 2 as a bounded
provenance refresh of the same corpus, preserving source selections, quantities,
servings, rights posture and historical hashes; escalate any source-content drift.
Do not substitute a new timestamp onto an old saved artifact without evidence.
No option has been silently implemented. No source replacements, schema expansion,
PR merge or PR5 work occurred.

## Verification of synchronization and preserved contracts

- DATA2 validator: **PASS: final DATA2 gates**.
- DATA2 focused: **164 passed in 3.25s**.
- Historical PR4-DATA / FoodIngredient affected regression: **82 passed in 2.31s**.
- Preserved PR4 domain/application/architecture/migration/persistence suite,
  excluding the obsolete production-seed suite: **43 passed in 4.29s**.
- Fresh DATA2 seed first/second runs and exact production Recipe/Version/
  Ingredient/Step/Equipment counts: **not produced**, mandatory provenance stop.
  The new step count is not derived; no old step total is reused as acceptance.
- Full PR4 seed suite and full backend + launcher regression: **not run** after
  the blocker; preserved component results above are not full PR4 acceptance.
- Ruff format/check on all **24 Python files in PR #10 versus accepted main**:
  **24 files already formatted; All checks passed!** No Python implementation
  edits in this correction. Frontend unchanged; no build required.
- Working diff, final staged diff and PR diff against accepted main: **PASS**.
  Staged correction scope: exactly seven task-local documentation/state files;
  no runtime, source corpus, binary, database, credential or environment changes. Normal merge's staged diff against old PR10 flags 11 pre-existing
  Markdown hard-break lines in the localization policy imported unchanged from
  main. Diff against accepted main passes; the policy was not altered for this.

Only synchronization, source-evidence report, supersession documentation and
state changed in this pass. Planner, MealPlan, Serving, Nutrition, Pantry,
Shopping, Retail, Auth/PostgreSQL, frontend and AI remain untouched.
