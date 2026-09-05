# FamilyFoodOS — Project Operating Manual

**Status:** canonical operational contract
**Purpose:** rules for ChatGPT, Codex and other agents working on FamilyFoodOS.

## 1. Required reading order

Before any significant product, architecture, research or implementation task, read in this order:

1. `AGENTS.md`
2. `docs/family-food/project-operating-manual.md`
3. `docs/family-food/agent-git-pr-workflow.md`
4. `state/current-focus.md`
5. `docs/family-food/master-roadmap.md`
6. the relevant canonical FamilyFoodOS documents:
   - `docs/family-food/architecture.md`
   - `docs/family-food/technical-spec.md`
   - `docs/family-food/data-ingestion.md`
   - `docs/family-food/migration-plan.md`
7. relevant implementation code and tests
8. `state/handoff.md` when continuing previous work

Later, more focused canonical documents may be added under `docs/`. Read them when relevant.

Do not reconstruct project architecture from source code alone when a canonical document exists.

## 2. Source-of-truth priority

When information conflicts, use this order:

1. latest explicit user-approved decision;
2. repository `AGENTS.md`;
3. current canonical `/docs`;
4. this Operating Manual;
5. older project documents;
6. historical chat context;
7. agent assumptions.

Never silently change an approved architecture decision.

If a change appears necessary, state:
- current decision;
- reason for changing it;
- consequences;
- proposed replacement.

## 3. Product mission

FamilyFoodOS helps a person or family answer:

> What should we eat, what should we buy, how much will it cost, and what should we prepare in advance?

Inputs may include:

- household members;
- age;
- sex;
- height;
- weight;
- physical activity;
- food goals;
- preferences;
- excluded foods;
- budget;
- available cooking time;
- food already at home.

Core flow:

`Household → MealPlan → Servings → Recipes → Shopping → Pantry → Prep/Freezer → Daily Use → Feedback → Next Week`

The system must become smarter inside while remaining simpler for the user.

## 4. Product goals

Architecture should support, progressively:

- normal family food;
- balanced / healthy food;
- weight maintenance;
- weight reduction;
- sports-oriented nutrition;
- child/family nutrition;
- budget mode;
- easy-cooking mode;
- pantry-cleanup mode;
- batch cooking;
- freezer preparation.

A mode must not be implemented until its rules, data sources, safety boundaries and tests are defined.

## 5. Minimal-input UX

Use the principle:

> complexity inside, simplicity outside.

If the system can infer, retrieve, remember, calculate or safely default a value, do not require the user to enter it manually.

Prefer:

`system proposes → user confirms or adjusts`

over:

`user fills a complex form → system stores it`.

Consumer UI is mobile-first.

Primary user sections should stay conceptually close to:

- Сегодня
- Неделя
- Купить
- Заготовки
- Дома

Administrative catalogs, ingestion, SKU matching, audit and technical controls do not belong in primary consumer navigation.

## 6. Recipe truth

Production recipes must have verifiable provenance.

A recipe must not become production truth solely because an LLM generated it.

Preferred sources include:

- trusted professional culinary sources;
- established editorial recipes;
- recipes with stable community feedback;
- practically tested internal recipes;
- licensed datasets or data legally usable by the project.

Store provenance where possible:

- source;
- source URL or identifier;
- retrieval date;
- original servings;
- normalized ingredients;
- verification status;
- recipe version.

Recipe pipeline:

`source → raw recipe → parsing → ingredient resolution → unit normalization → structured recipe → nutrition calculation → sanity validation → review → publish`

LLM may assist parsing and normalization, but final quantities and nutrition are calculated by deterministic code.

## 7. Nutrition truth

Nutrition Engine must be deterministic and versioned.

LLM is not a source of truth for:

- calories;
- proteins;
- fats;
- carbohydrates;
- fiber;
- serving mass;
- allergens;
- ingredient quantities.

Nutrition data must have provenance.

When exact data is unavailable, represent uncertainty explicitly instead of inventing precision.

FamilyFoodOS MVP is a wellness/productivity product, not a medical treatment system.

Do not claim diagnosis or treatment.

## 8. Planner

Planner is the central decision engine.

It should consider:

- household;
- member targets;
- recipes;
- preferences;
- exclusions;
- nutrition;
- recent history;
- budget;
- cooking time;
- pantry;
- leftovers;
- repetition;
- batch cooking;
- freezer compatibility.

Start with the simplest deterministic baseline capable of producing a usable week.

Do not add OR-Tools or another advanced solver merely because it is technically interesting.

A more complex planner must outperform the baseline on measurable criteria.

Planner runs should be explainable and traceable.

Prefer storing:

- planner version;
- candidate pool;
- constraints;
- rejected candidates;
- rejection reasons;
- scores;
- selected recipes;
- warnings;
- duration.

## 9. Shopping

Base pipeline:

`MealPlan → RecipeIngredients → scale → aggregate → subtract Pantry → ShoppingList`

Retail integration is a separate layer:

`FoodIngredient → RetailSKU → PriceSnapshot → Package Selection`

Never merge `FoodIngredient` and `RetailSKU` into one concept.
`CanonicalIngredient` is a historical alias for the current canonical
repository-domain name `FoodIngredient`, not a second aggregate.

Prices must have timestamps.

Stale prices must never be presented as current without qualification.

## 10. Retail research

For every retailer investigate separately:

1. official API;
2. partner API;
3. public structured endpoints;
4. public web catalogue;
5. lawful parser options;
6. deep-link support;
7. basket/cart creation;
8. affiliate/CPA possibilities;
9. regional/store-specific pricing;
10. terms and technical restrictions.

Do not assume that an API or basket integration exists.

Do not design around bypassing website protections.

Retailers should be isolated through a `RetailConnector` abstraction.

## 11. Prep and freezer

Prep/Freezer is a core feature, not decoration.

The system should answer:

- what can be prepared in advance;
- what operations can be combined;
- how much to prepare;
- what to freeze;
- when to defrost;
- how to finish the dish quickly later;
- how to reuse overlapping ingredients.

Optimize not only money, but also:

- cooking time;
- number of actions;
- cognitive load;
- food waste.

## 12. AI boundary

The core product must work with:

`AI_ENABLED=false`

AI may assist with:

- natural-language input;
- preference interpretation;
- feedback interpretation;
- recipe ingestion;
- SKU matching;
- explanations;
- substitution suggestions.

Critical results must pass deterministic validation whenever possible.

Use a provider abstraction rather than coupling the product to one model vendor.

## 13. Backend ownership

Critical business facts belong to backend.

Use:

`UI → API → services/domain → repositories → database`

Frontend may:
- collect input;
- display data;
- provide local form validation;
- explain results.

Frontend must not become the source of truth for nutrition, planner, shopping, pantry or other critical calculations.

## 14. Migration from CosmeticWorkshopOS

Reuse engineering foundations where useful:

- backend layering;
- transactions;
- versioning;
- validation;
- imports;
- audit;
- backup/export safety;
- tests;
- human-readable UX patterns.

Do not blindly reuse cosmetic-domain semantics.

Never use mechanical transformations such as:

- `Client → HouseholdMember`
- `Order → MealPlan`
- `ProductionBatch → PrepBatch`

Preferred migration:

`introduce new food bounded context → move dependencies → test → remove obsolete cosmetic context`

The bootstrap tag must remain unchanged.

## 15. Agent roles

### Orchestrator

Owns:
- scope;
- architecture;
- dependency order;
- final synthesis;
- merge order.

### Research Agent

Owns:
- external evidence;
- datasets;
- standards;
- retailers;
- competitors;
- source limitations.

### Domain Agent

Owns:
- models;
- services;
- planner;
- nutrition;
- shopping;
- pantry.

### Data Agent

Owns:
- ingredients;
- recipes;
- normalization;
- ingestion;
- provenance.

### Frontend Agent

Owns:
- PWA;
- mobile UX;
- accessibility;
- consumer flows.

Frontend work should follow stable API/domain contracts.

### QA / Reviewer

Owns:
- adversarial review;
- regressions;
- missing tests;
- unsafe assumptions;
- architecture-contract violations.

Only one Orchestrator owns cross-domain architecture decisions.

## 16. Research protocol

For important external questions distinguish:

**FACT** — supported by evidence.
**ASSUMPTION** — plausible but not established.
**DECISION** — project choice.
**OPEN QUESTION** — still unresolved.

Prefer primary sources:

- official documentation;
- original research;
- official datasets;
- API documentation;
- retailer sources.

Community sources are useful for real-world recipe quality and user experience, but should not silently replace authoritative factual sources.

Important research should be preserved under:

`docs/research/`

## 17. Codex task discipline

Each implementation task must be bounded.

Required structure:

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

Use `N/A` for irrelevant sections.

Do not combine unrelated bounded contexts in one PR.

Within that approved bounded task, Codex should execute routine implementation and Git mechanics autonomously according to:

`docs/family-food/agent-git-pr-workflow.md`

The default is not to return each ordinary staging/commit/push step to the user. The agent should implement, test, correct, verify, commit, push the feature branch and create/update the PR when those actions remain inside the authorized task.

If resolution requires a new architecture, roadmap, scope, authoritative-data, licensing/rights or acceptance decision, Codex must stop with a concrete blocker instead of guessing.

## 18. Git discipline

`main` must remain working.

Use small reviewable branches and PRs.

Canonical execution workflow:

`docs/family-food/agent-git-pr-workflow.md`

Default implementation lifecycle:

```text
read contracts
→ implement bounded task
→ focused tests
→ fix implementation defects
→ repeat verification
→ full required regression/lint/build/diff checks
→ staged scope audit
→ commit feature branch
→ push feature branch
→ create/update Pull Request into main
→ READY FOR FINAL REVIEW
→ stop
```

Routine actions inside approved scope do not require repeated manual user confirmation.

Agents MAY autonomously fix task-local implementation defects and make correction commits on the same feature branch.

Agents MUST NOT:

- push implementation commits directly to `main`;
- merge their own PR without explicit post-review merge authorization;
- force-push shared history without explicit authorization;
- start the next milestone before current acceptance/merge unless canonical sequencing explicitly allows it;
- weaken tests or acceptance criteria merely to obtain a green run;
- silently change architecture, roadmap, scope, source-of-truth data, accepted corpus, migration authority or another gated decision.

Before merge:

- tests pass;
- build passes;
- diff is reviewed;
- acceptance criteria are checked;
- relevant documentation/state is updated.

Before committing, audit staged scope and exclude local-only artifacts. At minimum use shell-equivalent checks for:

```text
git status --short
git diff --cached --check
git diff --cached --stat
```

Do not commit:

- secrets;
- API keys;
- tokens;
- real user personal data;
- `.env`;
- local databases;
- local development environments.

If a required verification cannot run, state the exact reason. Do not claim an unexecuted check passed.

Implementation state is not acceptance state: an agent may set `READY FOR REVIEW` when implementation evidence is complete, but must not mark a milestone `COMPLETE` solely because code was committed or a PR was opened.

## 19. Documentation and state

If the next agent will need a decision, do not leave it only in chat.

Persist it in repository documentation.

Use:

`state/current-focus.md`
for the exact current task and immediate next action.

Use:

`state/progress.md`
for verified completed work.

Use:

`state/handoff.md`
for information required by the next agent/session.

Canonical product/architecture knowledge belongs under `docs/`, not `state/`.

## 20. Scope gates

Do not prioritize before core value is demonstrated:

- fridge computer vision;
- voice assistant;
- wearables;
- native mobile apps;
- complex medical regimes;
- marketplace;
- social network;
- many retailer integrations.

First prove:

`Household → Planner → Week → Shopping → Pantry → Prep → Feedback`

Retail integration comes after generic Shopping Engine.

AI comes after deterministic Planner.

PostgreSQL, Auth, `HouseholdMembership`, tenant isolation and a hosted
operational baseline are required before multiple real families share one
deployment. They do not block isolated core-loop validation. Billing remains a
later commercial concern.

## 21. Product quality test

The primary test is not:

> Is the technology sophisticated?

It is:

> Can a normal person actually live through this week using the plan?

Check:

- ingredients are obtainable;
- recipe instructions are realistic;
- quantities make sense;
- nutrition fits the intended goal;
- menu is sufficiently varied;
- shopping list is usable;
- price estimate is credible;
- prep genuinely saves time;
- food waste is reduced.

## 22. Main product signal

A key success signal is:

> The household trusts FamilyFoodOS to plan the next week again.

Therefore retention and repeat weekly use matter more than:

- number of recipes;
- number of AI requests;
- number of generated plans.

FamilyFoodOS exists to reduce the recurring cognitive and operational burden of feeding a household.
