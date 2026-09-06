# FamilyFoodOS — Project Operating Manual

**Status:** canonical operational contract
**Purpose:** rules for ChatGPT, Codex and other agents working on FamilyFoodOS.

## 1. Task-based reading

Ordinary repository work follows the root contract:

`AGENTS.md → state/current-focus.md → applicable scoped AGENTS.md → relevant canonical docs → relevant code → relevant tests`

Read `state/handoff.md` only when continuing previous work. Load this Manual,
the Master Roadmap and relevant architecture references when deciding milestone
authorization, roadmap/gates, product or architecture, cross-context design,
source-of-truth conflicts or substantial research. Broad documents are not a
universal prerequisite for inspecting or correcting a current bounded context.

Use the repository `family-food-pr-delivery` Skill for authorized PR delivery.
Load `agent-git-pr-workflow.md` for unusual workflow questions or human review;
it is not required before every implementation. Detailed routing and task/DoD
requirements: [agent harness](agent-harness.md). Verification selection:
[verification policy](verification-policy.md).

Do not reconstruct project architecture from legacy source code when a relevant
canonical document exists.

## 2. Authority and conflicts

Explicit user-approved instructions define the task/outcome. Root invariants
and current canonical documents define durable project truth; the user may
explicitly authorize changing it. If an ordinary task conflicts with that truth,
stop and report the conflict rather than silently ignoring either source.

Within repository guidance, root invariants govern, scoped rules add compatible
local constraints and canonical documents own their stated subjects. This Manual
is the broad operational reference. Older documents, chat and assumptions do not
override current decisions. Skills are workflow guidance, subordinate to explicit
user instructions and hard project constraints. Legacy source-product material
is context, not current FamilyFoodOS product authority.

Never silently replace an approved decision. A proposed change must state the
current decision, evidence/reason, consequences and proposed replacement, and
receive explicit authorization before implementation depends on it.

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
- Follow-up
- Required final report

Use `N/A` for irrelevant sections.

Do not combine unrelated bounded contexts in one PR.

Within the approved task, use
[family-food-pr-delivery](../../.agents/skills/family-food-pr-delivery/SKILL.md)
for routine implementation and PR delivery. Task-local corrections and reversible
Git mechanics do not require repeated approval. Stop when resolution needs a new
architecture, roadmap, scope, authoritative-data, licensing/rights or acceptance
decision. The [harness contract](agent-harness.md) retains task and DoD detail.

## 18. Git discipline

Root `AGENTS.md` owns persistent Git and scope boundaries even when no Skill
activates. The PR delivery Skill owns normal execution; the
[Git/PR reference](agent-git-pr-workflow.md) owns unusual workflow questions,
staging details and the human PR/report contract.

Keep `main` working and use one bounded goal per feature-branch PR. No direct
main push, autonomous self-merge, unauthorized history rewrite or next-milestone
start. Do not weaken tests or silently change durable project truth.

Before review-ready state, satisfy the task's acceptance criteria and the
[verification policy](verification-policy.md), audit the staged scope and update
relevant docs/state. Report exact results and unavailable checks. Before merge,
required review and verification evidence must be accepted. Implementation
readiness is not acceptance: a commit or open PR never makes a milestone COMPLETE.
Closure requires accepted review/merge evidence under its milestone contract.

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
