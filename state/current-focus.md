# Current focus

Updated: `2026-09-05`

## Current execution — PR4 DATA2 integration

PR4-DATA2 — COMPLETE. PR #13 merged after `PR4-DATA2 FINAL REVIEW: ACCEPT`.
Accepted head: `918bf81b5da306fc65a57643de515ca1b3fbd1e4`.
Merge commit / synchronized main: `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
Final review submitted at `2026-09-05T16:06:13Z`; merged at
`2026-09-05T16:26:20Z`.

PR4 — IN PROGRESS on existing open PR #10, branch
`migration/pr4-recipe-catalogue`; starting head
`cd2285802c94735e0c9015042f9f4c0b52d68b85`.
Current main is being synchronized by normal merge, with accepted DATA2
preserved. No rebase, force-push, new PR or PR merge is authorized.

Existing PR4 Recipe/domain/application/persistence code and migration
`0024_food_recipe_catalogue` remain present. Production seed/compiler still
require DATA2 correction. The prior rights blocker is superseded by accepted
DATA2 source-specific review under the narrow direct-FNS project risk posture.
Source retrieval instants are under investigation before seed regeneration;
no date-only value may be converted into invented midnight provenance.

PR4 is neither COMPLETE nor ready for final review. PR5 remains unauthorized.
The accepted-main records below are retained as historical execution evidence;
their pre-merge DATA2 status/next-action sentences are superseded here.


## Project

FamilyFoodOS is a separate product bootstrapped from the verified engineering baseline of CosmeticWorkshopOS.

Source baseline:

- source repository: `Mitronomik/cosmetic-workshop-os`
- source commit: `0ac96deace602248e0d31e7e56c7aed7fb63c62b`
- bootstrap tag: `bootstrap-cosmetic-workshop-2026-08-31`
- FamilyFoodOS repository: `Mitronomik/family-food-os`

## Completed lifecycle

`PR0 — Frozen Fork — COMPLETE`

`PR1 — Identity Detox — COMPLETE`

`PR2-A — FamilyFoodOS Architecture & Persistence Contract — COMPLETE`

`PR2-B — Persistence Foundation — COMPLETE`

`PR2-C — Household Foundation — COMPLETE`

`PR2-DOCS — Canonical Roadmap & PR2-C Closure Sync — COMPLETE`

PR1 separated active FamilyFoodOS project, runtime, launcher, frontend and agent
identity from CosmeticWorkshopOS while preserving inherited runtime behavior.
Accepted source provenance, historical evidence, explicitly classified legacy
documentation and negative/legacy tests remain intentionally present.

PR2-A established the canonical `docs/family-food/architecture.md` contract and
accepted these decisions:

- dependency direction is `UI → API → application/domain → repository interfaces → persistence adapters → database`;
- new food persistence uses synchronous SQLAlchemy 2.x Core and a project-owned Unit of Work;
- the existing custom migration runner remains the sole SQLite schema authority;
- Alembic begins only at an explicit PostgreSQL cutover;
- SQLite remains local/vertical-slice persistence;
- PostgreSQL, Auth and tenant isolation are required before shared multi-family deployment;
- Billing remains later;
- `FoodIngredient` is the canonical name and `FoodIngredient != RetailSKU`;
- persisted derived state has source-revision and staleness rules;
- ShoppingList and PrepPlan generation do not mutate Pantry;
- UTC instants are distinct from household-local planning dates;
- the deterministic core works with `AI_ENABLED=false`.

PR2-B implemented the accepted synchronous SQLAlchemy 2.x Core persistence
foundation while preserving the custom migration runner as the sole SQLite
schema authority. The driver-independent Unit of Work owns one explicit
transaction; commit and rollback are terminal, revoke the active connection,
and prevent failed command state from contaminating later pooled commands.
New entity identifiers are application-generated `uuid.UUID` values using
UUIDv4 and generic SQLAlchemy `Uuid`; true instants use the UTC-normalizing
persistence type, while planning dates remain date-only and household-local.

PR2-C implemented the first production FamilyFoodOS bounded context beside the
legacy schema. The real path now supports creating and updating a Household,
adding and updating HouseholdMembers, and reading complete Household state via:

`FastAPI → HouseholdService → repository contracts → Household Unit of Work → SQLAlchemy Core → SQLite`

Migration `0022_household_foundation` adds `households` and
`household_members` after `0021_family_food_identity`. Member access is always
Household-scoped; there is no `owner_id`, Auth shortcut or Client reuse.

Verification:

- PR2-C correction-pass targeted suite: `196 passed`;
- full backend + launcher regression: `2684 passed`;
- Ruff checks and formatting checks: passed;
- `git diff --check`: passed.

The correction pass preserves terminal Household UoW semantics after successful
and failed commit/rollback attempts, rejects non-finite or unquantizable Decimal
input through stable validation, and evaluates future birth dates against an
injected clock in the persisted Household timezone.

Closure:

- final review: `PR2-C FINAL REVIEW: ACCEPT`;
- GitHub PR `#5`: **MERGED**;
- accepted head: `13f7c7c480469853579912a7836680afc4734ad7`;
- merge commit: `48c72aeba19a1e6ece0dc729f0a80de930be88a8`.

PR2-DOCS closure:

- GitHub PR: `#6` — merged;
- accepted head: `351a0a7e374312d6dda4b7e0e746d6a54579de61`;
- merge commit: `a5b6ca5d210b2401a2fa7e4037a957ec7b846774`.

## PR3 closure

`PR3 — FoodIngredient Catalogue — COMPLETE`

- GitHub PR `#7`: **MERGED**;
- accepted head: `b4d886824989a67711fca0b28821e60934279e6b`;
- merge commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`;
- final review: `PR3 FINAL REVIEW: ACCEPT`;
- PR3-focused suite: `77 passed`;
- full backend + launcher regression: `2761 passed`;
- Ruff and `git diff --check`: passed.

## Current active repository task

PR4-DATA2 — READY FOR REVIEW, not ACCEPTED or COMPLETE (`2026-09-05`).

Issue #12; existing branch `data/pr4-data2-russia-spb-recuration` and
[PR #13](https://github.com/Mitronomik/family-food-os/pull/13).
Exact base: `26af749be0f6446de1d88cad2e2e03158a9830a0` (merged governance #9,
historical PR4-DATA #8 and localization #11). This direction-consumables
correction begins at reviewed head `66a30403e3463248bb9b66e5a40920ef3fb136b5`.
The delivered head is recorded exactly in PR #13 after push, not as a
self-referential commit hash in its own contents.

Final: **30 recipes**, **28 retained / 2 replaced in this correction pass**;
relative to historical PR4: **3 retained / 27 replaced**. Both forbidden ICN
cards remain absent. **225 source-audit rows / 189 selected rows** (185 required,
3 source-explicit optional, 1 conditional); exact **81 existing FoodIngredient**
union within **80..120**, zero new codes and zero unresolved required rows.
**86 source-backed equipment rows / 34 normalized codes**.

Canonical PR4 meal types: **breakfast 3 / main 5 / side 5 / salad 6 /
sandwich 1 / other 10**. Separate curation roles: **BREAKFAST 3 / MAIN_DISH 5 /
SIDE_DISH 11 / SOUP 2 / DESSERT 3 / SNACK 4 / CONDIMENT 1 / SANDWICH 1**.
**8 meal anchors**, **3 soups/substantial one-bowl meals**, **11 pure sides**;
six primary-protein families: **DAIRY 1 / EGG 2 / FISH 2 / LEGUME_TOFU 1 /
MEAT 1 / POULTRY 1** among anchors.

All 30 actual sources were audited beyond ingredient lists: **281 consumable
audit rows**. At the reviewed head, **9 recipes / 19 direction-only edible
rows** included two required unquantified pan-release sprays. Honey Lime
Chicken and Local Harvest Bake were replaced, not silently edited. The final
corpus has **9 recipes / 24 direction-only edible rows**, all explicitly
resolved; **zero unresolved required direction consumables**. Process water
discarded after preparation is excluded from those direction-only edible
counts; selected retained water is not.

**83 non-water purchase forms: 3 RU_MASS_MARKET / 80 RU_AVAILABLE /
0 SPECIALTY_OR_UNCLEAR**. Chain coverage: **70 one-chain / 10 two-chain /
3 three-chain** forms. All five baseline chains assessed; Lenta concentration
remains a limitation. Matrix: **187 raw / 179 unique observations,
142 AVAILABLE / 37 UNCERTAIN** (includes rejected research).
Compatibility is not momentary store stock.

All final sources have nine reviewed consistency dimensions, including
direction-only consumables; missing that ninth dimension fails closed. Exact
artifacts/hashes, attribution and notices remain under the approved narrow
direct-FNS project risk posture, including the ONIE-attributed deviled eggs.
No unresolved selected-source rights blocker; no blanket public-domain or
unrestricted commercial/derivative rights claim.

Verification: final DATA2 validator **PASS**; focused DATA2 **164 passed in
3.40s**; historical PR4-DATA/FoodIngredient affected suite **82 passed in 1.71s**;
Ruff format **2 files already formatted**, Ruff check **All checks passed!**;
`git diff --check` **PASS**. Five final artifacts reproduce byte-for-byte from
reviewed source/form/consumable inputs. Final staged scope audit **PASS**: 24
authorized text files, no runtime/database/binary or unrelated files. Full runtime suite
and PR4 production seed execution are excluded from this isolated curation operation.

Historical `data/curation/pr4/`, global seeds (183 ingredients / 172 aliases /
183 profiles), PR4 runtime, migrations/API/frontend and local development DB
remain unchanged. PR #10 remains at `cd2285802c94735e0c9015042f9f4c0b52d68b85`;
it may consume DATA2 only after ACCEPT + merge. No RetailSKU/retailer production,
Nutrition, Pantry, Planner, Shopping, Auth/PostgreSQL or AI work. PR5 unauthorized.
Next action: project final review, not autonomous merge.

See [final review evidence](../data/curation/pr4-data2/review-report.md) for sources, replacements and consumable resolutions.

## Historical PR4-DATA task record (status superseded)

`PR4-DATA — Recipe Corpus FoodIngredient Coverage — READY FOR REVIEW`

This is a supporting data operation, not a product milestone.

Branch: `data/pr4-recipe-ingredient-coverage`

Base commit: `1a67fd96e9d2921ed986dc887081bbfe57c4dd83`

The corrected 30-card USDA FNS CACFP corpus and all 363 source ingredient rows
are frozen under `data/curation/pr4/`. Two minimal replacements reduce the
required union from 126 to 119 canonical FoodIngredient codes. The exact Gate 2
subset is durable in `mvp0-food-ingredient-codes.txt`; 36 codes resolve in the
accepted PR3 catalogue and the 83 missing corpus concepts have been added with
current USDA FDC provenance.

The global seed now contains 183 FoodIngredients and is no longer constrained
by PR3's historical 80–120 technical-slice range. The bounded MVP0 manifest,
not the production loader, enforces the unchanged `<=120` Gate 2 fixture limit.

No Recipe schema, domain, persistence, migration, seed, scaling, API or frontend
implementation was started. PR5 remains unauthorized.

## Historical next action (superseded by current task above)

Complete PR4-DATA final review and merge it before starting the next product
milestone, `PR4 — Recipe Catalogue`. PR4 implementation is waiting for the
PR4-DATA merge. PR5 remains unauthorized.
