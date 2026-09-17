# FamilyFoodOS — Master Roadmap Addendum, 2026-09-17 post-PR51

**Status:** canonical addendum to `master-roadmap.md` and later roadmap addenda  
**Authority:** explicit user-approved post-PR51 sequencing decision  
**Scope:** close the Meal Pattern Catalogue supporting operation, define the next bounded milestone, and resolve the next SQLite migration-number reservation.

## 1. Verified repository state

PR #51 (`feat: add versioned meal pattern catalogue`) is MERGED.

- completed supporting operation: `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` / Issue #47;
- verified PR head before merge: `7d9442075d7f616c338baf1d2f73745f7fcee88b`;
- merge commit / accepted `main`: `0648d9483bd9261451194668c274b3c08ad716b3`;
- accepted SQLite migration head: `0031_meal_pattern_catalogue`.

The supporting operation established platform-owned immutable/versioned `MealPatternProgram` truth, deterministic publication validation, reviewed adult seed data, eligibility/safety behavior, repository/UoW persistence, and migration `0031_meal_pattern_catalogue`.

Issue #47 is complete. It is no longer an active milestone operation.

## 2. Next functional milestone

The next functional milestone in the canonical sequence is:

`PR7 — MealPlan / Serving`

PR7 is **NEXT / NOT STARTED**. This addendum identifies the next operation but does not itself authorize implementation work beyond the post-PR51 documentation/state synchronization. PR7 implementation requires separate explicit authorization.

The active sequence is therefore:

```text
PR6 / Nutrition Core                          COMPLETE
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE         COMPLETE (#47 / PR #51)
→ PR7 MealPlan / Serving                     NEXT / NOT STARTED
→ PR8 Planner v0                             NOT STARTED
→ GATE 1 — Planning Core                     NOT STARTED
→ PR9 Shopping Engine                        NOT STARTED
→ PR10 Prep / Freezer                        NOT STARTED
→ PR10-PDF Backend Weekly PDF                NOT STARTED
```

## 3. PR7 ownership boundary

PR7 owns Household-owned accepted planning state and the manually constructible MealPlan/Serving domain required before Planner automation.

At minimum, PR7 must preserve these already-canonical boundaries:

- `MealPatternProgram` remains platform-owned catalogue truth;
- `MemberMealPatternSelection` is Household-owned accepted state;
- selection may reference an exact published program version or represent `CUSTOM`;
- member meal patterns may differ within one household;
- the initial product must represent one to six meal opportunities per member/day without making `6` a permanent database-law maximum;
- `MealRole != RecipeVersion.meal_type_code`;
- one shared household meal event may produce different member `Serving` allocations;
- Nutrition Engine remains authoritative for nutrient targets and calculations;
- PR7 does not implement Planner ranking/recommendation logic owned by PR8;
- deterministic core must work with `AI_ENABLED=false`;
- no Retail, Auth/shared deployment, AI Gateway, Shopping or Prep scope is pulled forward.

Exact PR7 schema/API details remain an implementation decision inside the future explicitly authorized PR7 task and must follow repository architecture and verification contracts.

## 4. SQLite migration reservation decision

### DECISION

The next actual SQLite migration number, `0032`, is reserved for the next authorized PR7 MealPlan / Serving persistence change.

This is a sequence reservation, not permission to create a migration before PR7 is explicitly authorized. The exact migration identifier suffix will be chosen by the PR7 implementation task to match the final bounded schema.

The previous future-only reservation:

`0032_recipe_template_catalogue`

is superseded by:

`0033_recipe_template_catalogue`

unless a later explicit approved decision changes the sequence again.

No existing migration history is rewritten:

```text
0030_recipe_source_corpus
→ 0031_meal_pattern_catalogue
→ 0032 <reserved for PR7 MealPlan / Serving>
→ 0033_recipe_template_catalogue <future reservation only>
```

Recipe Constructor / RecipeTemplate work remains a separately scoped capability and is not restored as a blocker before PR7/PR8.

## 5. Effect on earlier documents

This addendum supersedes only stale post-merge sequencing/reservation wording in earlier state and roadmap material:

- `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is COMPLETE rather than active/next;
- PR7 MealPlan / Serving is the next functional milestone;
- migration `0031_meal_pattern_catalogue` is now the accepted migration head;
- `0032` is reserved for PR7 rather than RecipeTemplate;
- future RecipeTemplate catalogue migration reservation moves to `0033`.

All unaffected product, architecture, evidence, safety, Russian-language, dataset-independence, web-corroboration and `AI_ENABLED=false` rules remain in force.

## 6. Stop condition

After this post-PR51 docs/state synchronization is reviewed and merged, stop.

Do not begin PR7 automatically. Start PR7 only after separate explicit user authorization with a bounded task contract.