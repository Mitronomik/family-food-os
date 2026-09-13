# FamilyFoodOS — Master Roadmap Addendum, 2026-09-13

**Status:** canonical addendum to `master-roadmap.md`  
**Authority:** later explicit user-approved product/security decisions  
**Sequence effect:** no reboot and no reordering of the existing numbered product milestones

## 1. Purpose

This addendum integrates the September 2026 Household Food OS product/security
research and the explicit decision to support configurable meal frequency plus a
deterministic meal-pattern recommender.

Where this addendum changes the scope/acceptance of a future milestone, it
supersedes the older milestone wording to that extent. The existing order of
milestones and current Recipe Assembly gates remains unchanged.

## 2. No architecture reboot

The following are **not** introduced by this addendum:

- NestJS/Prisma core rewrite;
- new greenfield repository scaffold;
- immediate PostgreSQL cutover;
- mandatory optimizer microservice;
- OR-Tools before baseline evidence;
- Redis/NATS/Temporal/Kubernetes;
- AI or Retail in the core path.

Current FastAPI/Python + repository/UoW + SQLAlchemy Core + ordered SQLite
migration lineage remains the active architecture until its existing gates say
otherwise.

## 3. Current state after PR #36

PR #36 is merged. Main at the time of this addendum:

`077d054373cc5f8e1813acdc2cbacb3746e1c11a`

Migration head:

`0030_recipe_source_corpus`

Source-corpus ingestion does not publish RecipeTemplate/RecipeVersion and does
not change FoodIngredient/Nutrition/Composition authority.

Recipe Assembly A remains blocked on its existing evidence gates. Assembly B and
PR7+ remain not started unless separately authorized.

## 4. PR7 scope amendment — MealPlan / Serving

PR7 must establish a planning model that is flexible enough for the product from
the first implementation.

In addition to the existing MealPlan/Serving requirements, PR7 must be able to
represent:

- configurable member meal opportunities;
- initial validated range of 1–6 eating occasions/day without hardcoded
  breakfast/lunch/dinner-only schema;
- different patterns for different HouseholdMembers;
- participation of a subset of members in a Household meal event;
- reference to the member's accepted MealPatternProgram version or CUSTOM
  selection;
- meal sources where a Recipe may be absent (`LEFTOVER`, `PREPARED`,
  `READY_MEAL`, `ORDER_OUT`, `EAT_OUT` or equivalent approved representation);
- immutable plan history/revision semantics.

PR7 does **not** need to implement the complete recommendation algorithm. It
creates the domain/history boundary needed by PR8.

### PR7 added acceptance cases

At minimum the domain/tests must represent:

- dinner-only;
- breakfast-only;
- breakfast + dinner;
- 3 meals;
- 5 meals;
- 6 meal opportunities;
- heterogeneous household schedules;
- one shared meal event with different member Servings.

The exact enum/table/API design remains the PR7 implementation responsibility
within `architecture.md` and `meal-pattern-programs.md`.

## 5. PR8 scope amendment — Planner v0

PR8 remains deterministic filters + scoring/heuristics first.

In addition to the older Planner v0 requirements, it must establish a bounded
baseline for:

### 5.1 Meal Pattern Recommender v0

- input: structured member profile/goals/activity/schedule/preferences supported
  by the wellness product;
- output: ranked versioned curated MealPatternPrograms;
- deterministic and reproducible;
- user acceptance required before a program becomes active;
- unsupported/safety outcome instead of invented medical recommendation;
- no universal rule such as `weight_loss -> five meals`;
- adult programs do not silently apply to children outside eligibility.

### 5.2 Household reconciliation

Planner should compile accepted member patterns into household meal events and
reward shared preparation where hard constraints allow it.

Planner may vary Serving/final validated variant while keeping one shared base.
Hard exclusions dominate sharedness.

### 5.3 Meal source selection

Planner may deliberately use leftovers/prepared/ready/out-of-home sources rather
than require a fresh Recipe in every slot.

### 5.4 Replan foundation

PR8 should define a versioned deterministic replan/change contract for future
meal slots. It may start with schedule/participation/source changes that are
possible with PR8 state.

Richer preservation of PreparedBatch/freezer/perishable state is extended when
PR10 Prep exists; PR8 must not invent state from future contexts.

## 6. Gate 1 — Planning Core amendment

Gate 1 still occurs after PR8. It additionally requires evidence that:

- Planner is not hardcoded to a fixed daily meal count;
- at least the representative 1/2/3/5/6-opportunity cases are supported;
- heterogeneous member patterns can compile into one household week;
- deterministic recommendation is versioned and user-controlled;
- shared household meal behavior is tested;
- simple replan/version behavior is reproducible;
- medical/unsupported cases fail safely rather than generating a pseudo-clinical
  program.

The original core Gate 1 requirements (exclusions, complete week, individualized
servings, trace, deterministic behavior) remain.

## 7. PR9 Shopping amendment

No sequence change.

Shopping should be ready to consume a MealPlan containing mixed meal sources.
Only meal events that create ingredient demand contribute recipe/assembly demand.
LEFTOVER/PREPARED handling must use authoritative represented supply rather than
silently count the same demand twice.

Retail/package optimization remains later.

## 8. PR10 Prep / Freezer amendment

No sequence change.

Prep should evolve toward an explicit dependency graph with:

- active/passive time;
- equipment;
- predecessors;
- resulting storage state;
- shared ingredient/component work.

A sophisticated scheduler/solver is optional and requires evidence that a simpler
baseline is inadequate.

## 9. PR13 consumer UX amendment

Consumer UX must expose the new product flexibility without turning onboarding
into a nutrition dashboard.

Required direction:

- system proposes a meal pattern where the user asks for help;
- user can accept, select another preset or choose CUSTOM;
- dinner-only and other reduced schedules remain easy;
- different members may have different patterns without forcing the household
  operator through excessive forms;
- "plans changed" / replan flow becomes a first-class weekly action;
- replan shows an understandable diff and does not silently rewrite history.

## 10. PR15 Feedback / History amendment

Feedback should be able to capture adherence to the accepted pattern and later
improve deterministic ranking.

Real-family analytics should include:

- Planned Meal Execution Rate;
- decision-free meal events;
- Prep adoption;
- replan invocation/acceptance;
- plan/recipe replacement;
- waste signal;
- budget variance where actual spend exists;
- Week 2 / Week 4 repeat trust.

No LLM is required for these signals.

## 11. Shared deployment security amendment

SHARED-1/2/3 remain in the same sequence but must satisfy
`security-architecture.md`.

In particular before multiple real households share a deployment:

- secure OIDC/session architecture;
- RFC 9700 / RFC 10017-aligned browser flow where OAuth/OIDC is used;
- HouseholdMembership object authorization and negative BOLA tests;
- secrets/backups/monitoring baseline;
- repository/deployment security controls appropriate to a public shared system.

Passkeys/WebAuthn are the preferred phishing-resistant path when the chosen IdP
and product UX support them; admin/support requires strong MFA/passkey.

## 12. Data/Importer security amendment

Existing controlled platform corpus ingestion keeps its current trust contract.

Any future arbitrary user URL/file import is a new hostile-content boundary and
must not ship until the sandbox/SSRF/file-parser controls in
`security-architecture.md` exist.

## 13. Retail security amendment

Retail still begins after generic Shopping and product evidence.

Before connector enablement:

- scoped credentials;
- provider-specific anti-corruption layer;
- strict response validation;
- timeout/retry/circuit behavior;
- webhook verification if applicable;
- stale-data handling;
- no Planner dependency on provider availability.

Checkout/write actions require server revalidation and explicit user confirmation.

## 14. AI security amendment

AI still begins after deterministic Planner/core value.

Progression:

```text
read-only parsing/explanation
→ minimal read-only household context
→ proposed typed actions
→ allowlisted Tool Broker only after separate security gate
```

AI does not receive direct SQL/shell/filesystem/general-network/payment/secrets
privileges.

Direct and indirect prompt-injection/tool-abuse regression tests are required
before tool-enabled runtime AI.

## 15. Supply-chain / release security amendment

Security controls mature with risk rather than waiting for a final hardening PR.

Before shared staging/production, the project must plan/enable appropriate:

- secret scanning;
- SAST/SCA;
- dependency/lockfile policy;
- migration/authz tests;
- SBOM and release-artifact vulnerability scanning;
- provenance/signing by production release maturity;
- protected deployment/repository workflow;
- backup restore evidence.

This does not authorize a new platform stack.

## 16. Canonical supporting documents

Future work in these scopes must read:

- `product-strategy.md`;
- `meal-pattern-programs.md`;
- `security-architecture.md`;
- `../research/household-food-os-package-integration-2026-09-13.md` for the
  source-integration rationale.

## 17. Next-step rule

This addendum changes future requirements, not current execution authorization.

No Assembly B, PR7, Retail, AI, Auth or other future implementation begins merely
because the documents now describe it. `state/current-focus.md` remains the
source of current task authorization.
