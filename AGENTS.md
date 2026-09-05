# AGENTS.md — FamilyFoodOS Agent Contract

Project: **family-food-os**

FamilyFoodOS is a new product bootstrapped from CosmeticWorkshopOS.

The preserved Git history is engineering provenance, not the current product specification.

## 1. First reading order

Before significant work, read in this order:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `docs/family-food/agent-git-pr-workflow.md`
4. `state/current-focus.md`
5. `docs/family-food/master-roadmap.md`
6. relevant canonical architecture/domain documents
7. relevant source code
8. relevant tests
9. `state/handoff.md` when continuing previous work

Canonical FamilyFoodOS foundation documents:

- `docs/family-food/master-roadmap.md`
- `docs/family-food/architecture.md`
- `docs/family-food/technical-spec.md`
- `docs/family-food/data-ingestion.md`
- `docs/family-food/migration-plan.md`
- `docs/family-food/agent-git-pr-workflow.md`
- `docs/migration-source.md`

Do not reconstruct the intended product only from legacy source code.

## 2. Important migration warning

This repository currently contains substantial CosmeticWorkshopOS code and documentation.

Legacy code is intentionally preserved during migration.

Do not assume an existing cosmetic concept is also a FamilyFoodOS concept.

Never mechanically rename:

- `Client` to `HouseholdMember`
- `Order` to `MealPlan`
- `ProductionBatch` to `PrepBatch`
- `PackagingItem` to a retail food package

Preferred migration pattern:

`introduce new food bounded context → move dependencies → test → remove obsolete legacy context`

Do not delete large legacy areas merely because they are no longer part of the target product unless the current migration step explicitly authorizes removal.

## 3. Source-of-truth order

When instructions conflict, use:

1. latest explicit user-approved decision;
2. this root `AGENTS.md`;
3. current canonical FamilyFoodOS documents;
4. `docs/family-food/project-operating-manual.md`;
5. current task specification;
6. legacy CosmeticWorkshopOS documentation;
7. assumptions.

If an approved architecture decision appears wrong, do not silently replace it. Report the issue and propose a change.

## 4. Product core

FamilyFoodOS should eventually support this core loop:

`Household → Planner → MealPlan → Servings → Recipes → Shopping → Pantry → Prep/Freezer → Daily Use → Feedback → Next Week`

The product should minimize user effort.

Guiding principle:

**complexity inside the system, simplicity for the user.**

## 5. Deterministic core

The core must work with:

`AI_ENABLED=false`

Critical calculations belong to deterministic backend code.

LLM must not be the source of truth for:

- calories;
- nutrients;
- ingredient quantities;
- serving sizes;
- allergens;
- prices;
- availability;
- storage duration.

Production recipes require verifiable provenance.

AI may assist with parsing, natural-language input, feedback, matching, explanation, and suggestions, subject to deterministic validation where appropriate.

## 6. Backend ownership

Preserve clear boundaries:

`UI → API → services/domain → repositories → database`

Critical business logic must not live only in frontend.

Reuse strong inherited engineering patterns where suitable:

- transactional writes;
- immutable/versioned history;
- validation;
- migrations;
- auditability;
- safe import drafts;
- backup/export safety;
- structured errors;
- tests.

Do not preserve legacy business semantics merely to maximize code reuse.

## 7. Consumer UX

FamilyFoodOS consumer UX is mobile-first.

Primary conceptual sections:

- Сегодня
- Неделя
- Купить
- Заготовки
- Дома

Administrative functionality such as ingestion, `FoodIngredient` management,
retailer matching and audit must not dominate consumer navigation.

Prefer:

`system proposes → user confirms or changes`

over long manual forms.

## 8. Recipe and nutrition safety

Production recipes must have source provenance.

Preferred recipe pipeline:

`source → parse → resolve ingredients → normalize units → structure → calculate nutrition → validate → review → publish`

Nutrition Engine is deterministic and versioned.

FamilyFoodOS MVP is not a medical treatment system.

Do not claim diagnosis, treatment, or therapeutic effectiveness.

## 9. Planner discipline

Start with the simplest deterministic planner that can generate a useful week.

Advanced optimization must justify itself against a baseline.

Planner behavior should be traceable through:

- planner version;
- constraints;
- candidate pool;
- rejected candidates;
- rejection reasons;
- scores;
- selections;
- warnings.

## 10. Shopping and retail

Generic Shopping Engine comes before retailer integrations.

Base flow:

`MealPlan → RecipeIngredients → scale → aggregate → subtract Pantry → ShoppingList`

Retail is a separate layer:

`FoodIngredient → RetailSKU → PriceSnapshot`

Do not merge canonical food concepts with retailer SKU concepts.

Retail integrations must be isolated behind connector abstractions.

Never assume an API or cart integration exists without research.

## 11. Git workflow

`main` must remain working.

Use small reviewable branches and PRs.

One PR should have one clear goal.

The canonical agent execution contract is:

`docs/family-food/agent-git-pr-workflow.md`

For an already-authorized bounded task, the default agent behavior is self-service execution:

`read → implement → test → fix → re-test → audit scope → commit → push feature branch → create/update PR → stop for final review`

The user should not need to manually drive ordinary staging, commit, push or PR-creation mechanics when the agent has the required repository tools and no stop condition is present.

Agents may autonomously fix implementation defects, failing task-local tests, lint/format failures, migration-registration omissions, staged-file mistakes and PR metadata inside the approved scope.

Agents must stop and escalate rather than silently change project truth when a fix requires changing architecture, roadmap, bounded-context scope, authoritative data, accepted corpus, acceptance criteria, migration strategy or another gated product decision.

Hard boundaries:

- never push implementation work directly to `main`;
- never merge the agent's own PR without explicit post-review merge authorization;
- never start the next milestone merely because the current branch is review-ready;
- never weaken tests or acceptance criteria simply to make the branch green;
- never force-push shared history unless explicitly authorized.

Before coding:

1. read required contracts;
2. inspect existing implementation;
3. inspect relevant tests;
4. identify what can safely be reused;
5. identify legacy assumptions that must not leak into the new domain.

Each implementation task should define:

- Context
- Goal
- Scope
- Non-goals
- Architecture constraints
- Data model impact
- API impact
- Frontend impact
- Tests
- Acceptance criteria
- Risks / limitations
- Required final report

Use `N/A` where a section does not apply.

## 12. Testing

Every domain change requires appropriate tests.

Before considering a PR complete, run the relevant available:

- unit tests;
- integration tests;
- frontend build/type checks;
- smoke checks where applicable.

If a check cannot be run, say exactly why.

Never hide a failing baseline by deleting or weakening tests without explicit justification.

## 13. Schema and migrations

Every persisted schema change requires an explicit migration strategy.

Existing user data must not be silently destroyed.

During the migration period, legacy schema may coexist with new FamilyFoodOS schema until the relevant bounded context is replaced and verified.

## 14. Imports and ingestion

Never allow untrusted parsed data to silently become production truth.

Use drafts, validation, review or explicit trusted-source policies as defined by the FamilyFoodOS ingestion architecture.

Maintain provenance.

## 15. Security

This repository is public.

Never commit:

- passwords;
- API keys;
- tokens;
- secrets;
- `.env`;
- private credentials;
- real user personal data;
- real health-related user records;
- local databases;
- local development environments.

Use placeholders and documented environment-variable names.

## 16. Agent roles

When parallel work is useful, use bounded roles:

- Orchestrator — scope, architecture, dependency and merge order;
- Research — evidence, datasets, standards, retailers;
- Domain — models, nutrition, planner, shopping, pantry;
- Data — recipes, ingredients, ingestion, provenance;
- Frontend — PWA/mobile UX and accessibility;
- QA/Reviewer — adversarial review and regressions.

Only one Orchestrator owns cross-domain architectural decisions.

## 17. Documentation

If a decision must survive the current session, persist it.

Canonical durable knowledge belongs under `docs/`.

Execution state belongs under `state/`.

Use:

- `state/current-focus.md` — exact current work;
- `state/progress.md` — verified completed work;
- `state/handoff.md` — next-session handoff.

Do not use chat history as the sole durable source of an implementation decision.

## 18. Legacy scoped AGENTS files

Nested `AGENTS.md` files inherited from CosmeticWorkshopOS may still contain legacy product rules.

Until each is migrated:

- inspect the applicable nested file before work;
- treat cosmetic-domain requirements in it as legacy unless the current FamilyFoodOS migration step explicitly preserves them;
- preserve generic engineering and safety constraints where compatible;
- flag a conflict instead of guessing.

Updating scoped `AGENTS.md` files is part of the migration and should be done deliberately.

## 19. Current implementation order

Follow:

`docs/family-food/master-roadmap.md`

Use `docs/family-food/migration-plan.md` for migration strategy, legacy
replacement discipline and bounded migration notes.

Only a later explicit decision may change this order.

Do not jump ahead to AI, retailer scraping, complex optimization, native apps or SaaS infrastructure before their migration gate.

## 20. Completion mindset

The goal is not to demonstrate sophisticated technology.

The goal is to build a system a normal household can repeatedly trust to plan realistic food, shopping and preparation.

Every implementation choice should improve at least one of:

- plan quality;
- usability;
- safety;
- reproducibility;
- cost accuracy;
- preparation effort;
- maintainability;
- repeat weekly use.
