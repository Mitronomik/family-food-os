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
