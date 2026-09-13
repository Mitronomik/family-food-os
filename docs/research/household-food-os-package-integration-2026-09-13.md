# Research Integration Review — Household Food OS package, 2026-09-13

**Status:** evidence/integration record, not a runtime specification
**Repository:** FamilyFoodOS
**Reviewed against main:** `077d054373cc5f8e1813acdc2cbacb3746e1c11a` (PR #36 merged)

## 1. Source package reviewed

The following external working documents were reviewed against the current
FamilyFoodOS repository contracts:

1. `Household_Food_OS_Grocery_Weekly_Planner_v1_1_AI_Security (1).docx`
2. `Household_Food_OS_Technical_Architecture_Specification_v1_0.docx`
3. `Household_Food_OS_Repository_Bootstrap_Specification_v1_0.docx`
4. `Household_Food_OS_Repository_Bootstrap_v1_0.zip`

The package is useful research/reference material. It is **not** imported as a
second architecture or repository baseline.

## 2. Current FamilyFoodOS state used for comparison

At review time:

- PR0–PR6 are complete;
- PR #36 is merged and main is
  `077d054373cc5f8e1813acdc2cbacb3746e1c11a`;
- current SQLite migration head is `0030_recipe_source_corpus`;
- source-corpus ingestion exists without publishing RecipeTemplate/RecipeVersion;
- Recipe Assembly A remains blocked on evidence gates;
- Assembly B and PR7+ have not started.

This matters because the external TAS/RBS describe a greenfield bootstrap while
FamilyFoodOS already has accepted domain, persistence, migration, nutrition,
composition, provenance and data contracts.

## 3. Integration rule

For each idea from the package, use one of four outcomes:

- **ADOPT** — becomes a FamilyFoodOS invariant/requirement now;
- **ADAPT** — useful concept, integrated using current architecture rather than
  copied literally;
- **DEFER** — valid later capability but not current scope;
- **REJECT AS BASELINE** — would replace accepted architecture without evidence.

## 4. Product integration matrix

| External concept | Outcome | FamilyFoodOS integration |
|---|---|---|
| Household Food OS positioning | ADOPT | `product-strategy.md` makes weekly household execution/replanning the product thesis |
| Household Reconciliation / shared base | ADOPT/ADAPT | Planning objective; not a mandatory network service |
| Dinner-only MVP | REJECT AS DOMAIN LIMIT / ADAPT AS CONFIG | meal pattern is configurable; dinner-only is one valid user pattern/test cohort |
| 1–6 meal opportunities / flexible pattern | ADOPT (user decision) | `meal-pattern-programs.md`; heterogeneous per-member schedules |
| Deterministic program recommendation | ADOPT (user decision) | curated/versioned wellness programs; user confirmation; no clinical diet prescription |
| Planned leftovers | ADOPT | first-class planning supply/source |
| Prepared batches | ADOPT direction | Prep/Pantry integration when owning milestone arrives |
| READY_MEAL / EAT_OUT / ORDER_OUT | ADOPT | legitimate meal sources; not every slot has Recipe |
| Reality Loop / Dynamic Replanning | ADOPT/ADAPT | Planning/revision capability; preserve committed state, explain diff |
| Cross-recipe ingredient reuse | ADOPT | Planner/Shopping/Prep objective |
| Prep Graph | ADOPT direction | Prep DAG/scheduling evolution, solver only if justified |
| Real Package Optimizer | DEFER | Retail enrichment after generic Shopping |
| G5 cross-retailer optimizer | DEFER | after core value + official/partner retail paths |
| Decision-free dinners | ADAPT | generalized to decision-free meal events |
| Planned Meal Execution Rate | ADOPT | real-family validation metric |
| Replan success | ADOPT | real-family validation metric |
| Concierge PROBE | ADAPT | evidence model absorbed into existing real-family testing; no repository rewind |
| AI as reasoning/interface layer | ADOPT | optional, late, structured/proposal-only |

## 5. Architecture integration matrix

| External TAS/RBS item | Outcome | Reason |
|---|---|---|
| Modular monolith first | ADOPT (already aligned) | existing repository architecture already follows modular application boundaries |
| TypeScript/NestJS as Core backend | REJECT AS BASELINE | current accepted backend is FastAPI/Python; rewrite has no demonstrated product benefit |
| PostgreSQL as immediate bootstrap source of truth | REJECT AS CURRENT SEQUENCE | PostgreSQL remains mandatory at Shared Deployment gate, not local core work |
| Prisma ORM | REJECT | conflicts with accepted SQLAlchemy Core/repository/UoW path |
| Python stateless OR-Tools optimizer service from start | DEFER | Planner baseline must first prove need for solver/service extraction |
| OpenAPI/JSON Schema explicit contracts | ADAPT | useful boundary practice; apply where repository/API maturity justifies it |
| Transactional outbox / background worker | DEFER BY TRIGGER | useful with async side effects; not required before workload exists |
| Temporal/NATS/Valkey | DEFER BY TRIGGER | consistent with FamilyFoodOS scope discipline |
| Retail anti-corruption layer / capabilities | ADOPT direction | compatible with existing FoodIngredient != RetailSKU invariant |
| Isolated URL/file importer | ADOPT for future arbitrary imports | security requirement before hostile external-content ingestion |
| OpenTelemetry from production | ADOPT direction | vendor-neutral telemetry for hosted maturity; avoid PII |
| Kubernetes | REJECT AS STARTING POINT | only by measured platform/scaling trigger |
| Bootstrap ZIP schema as new source of truth | REJECT | regresses existing RecipeVersion/composition/provenance/pantry/migration contracts |

## 6. Why the bootstrap ZIP is not merged

The ZIP is a coherent educational greenfield scaffold but is not compatible with
the current repository as a drop-in baseline.

Important regressions relative to accepted FamilyFoodOS truth include:

- replacing `FoodIngredient` terminology/model with a new `ingredient_concept`
  schema;
- missing the accepted immutable RecipeVersion/composition authority model;
- a simplified Pantry current-state model vs accepted movement/audit semantics;
- Meal slots tied directly to Recipe rather than immutable RecipeVersion or
  validated RecipeAssembly;
- mandatory identity/`created_by_user_id` in a phase where no-auth isolated core
  work is explicitly allowed;
- independent PostgreSQL migration `0001` conflicting with the accepted SQLite
  migration lineage now at `0030`;
- an optimizer service boundary before Planner evidence exists.

The useful parts of the scaffold are retained as design references, especially
security boundaries, contract discipline, least privilege and technology
admission criteria.

## 7. Security integration matrix

| External security concept | Outcome | Canonical owner |
|---|---|---|
| Zero trust / no implicit trust | ADOPT | `security-architecture.md` |
| External content = untrusted data | ADOPT | `security-architecture.md` + ingestion contracts |
| BOLA/object authorization | ADOPT | architecture/security shared-deployment gate |
| AI no direct DB/shell/filesystem/network/payment access | ADOPT | `AGENTS.md` + `security-architecture.md` |
| Prompt injection architecture, not prompt-only defense | ADOPT | AI security gate |
| Tool Broker + typed allowlisted tools | ADOPT as late gate | security architecture |
| User confirmation for financial actions | ADOPT | Retail/commerce gate |
| SSRF-safe importer sandbox | ADOPT for arbitrary URL/file import | security architecture |
| Webhook replay/signature validation | ADOPT when webhooks exist | Retail/Auth integrations |
| OAuth token minimization/rotation | ADOPT when integrations exist | security architecture |
| PII/context minimization | ADOPT | security/privacy contract |
| Children data minimization | ADOPT | security/privacy contract |
| SAST/SCA/secret scanning | ADOPT by shared staging gate | secure SDLC |
| SBOM/provenance/signing | ADOPT by production release maturity | supply-chain gate |
| SLSA target | ADAPT | practical release-platform target, not infrastructure rewrite |
| DAST/restore drills | ADOPT when shared/public staging exists | production hardening |

## 8. Standards re-verified during integration

Primary sources were checked again on 2026-09-13.

### Confirmed current baseline

- OWASP ASVS latest stable: **5.0.0**.
- OWASP API Security Top 10 current published edition: **2023**.
- OWASP Top 10 for LLM Applications: **2025**.
- NIST AI RMF Generative AI Profile: **NIST AI 600-1**.
- OAuth 2.0 Security BCP: **RFC 9700 / BCP 240**.
- WebAuthn Level 3 became a W3C Recommendation on **2026-08-25**.
- SLSA **v1.2** Build requirements are approved/current.
- CycloneDX **1.7** is the current stable 1.x specification at review time;
  announced 2.0 should not be treated as stable merely because it is newer.

### Additional current standard added beyond the external package

**RFC 10017 / BCP 212 — OAuth 2.0 for Browser-Based Applications** was published
in August 2026 and should be used together with RFC 9700 when FamilyFoodOS designs
browser OAuth/OIDC flows.

Primary references:

- https://owasp.org/projects/asvs
- https://owasp.org/API-Security/editions/2023/en/0x11-t10/
- https://genai.owasp.org/llm-top-10/
- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- https://www.rfc-editor.org/info/rfc9700
- https://www.rfc-editor.org/rfc/rfc10017.html
- https://www.w3.org/TR/webauthn-3/
- https://slsa.dev/spec/v1.2/build-requirements
- https://cyclonedx.org/specification/overview/

## 9. Meal-frequency evidence check

The new user decision requires a meal-frequency constructor and recommendation
layer. External evidence was checked specifically to prevent encoding folklore as
medical truth.

Findings:

- USDA/NESR for the 2025 Dietary Guidelines Advisory Committee found insufficient
  evidence to conclude that a particular meal/snack frequency generally produces
  a dietary pattern better aligned with the Dietary Guidelines.
- A 2023 systematic review/meta-analysis of randomized trials found no clear
  overall advantage of higher vs lower eating frequency for cardiometabolic
  outcomes in generally healthy adults; certainty was very low.
- Evidence around timing/frequency can differ by population and specific goal;
  therefore program recommendation needs eligibility, provenance and uncertainty,
  not simplistic rules such as `weight_loss -> five meals`.
- Age-specific guidance exists for some child populations (for example WHO
  complementary-feeding minimum frequency for 6–23 months), confirming that
  children need separate curated rules rather than adult defaults.

This evidence supports a **deterministic curated-program recommender** while
rejecting a universal "correct number of meals" algorithm.

References:

- https://nesr.usda.gov/2025-dietary-guidelines-advisory-committee-systematic-reviews/frequency-meals-snacks_diet-quality
- https://pubmed.ncbi.nlm.nih.gov/37964316/
- https://www.who.int/data/gho/data/indicators/indicator-details/GHO/minimum-meal-frequency-6-23-months

## 10. Market/product research treatment

The competitive/market material from the Grocery Weekly Planner document is
retained as research evidence rather than converted wholesale into product truth.

Useful strategic signals include:

- meal planning by itself is increasingly commoditized;
- stronger differentiation may come from household reconciliation, execution,
  prep, leftovers and replanning;
- recipe-to-cart execution is valuable but insufficient as the entire moat;
- real household state and repeated execution/feedback are more defensible than
  LLM access;
- Russian product behavior should support repeat meals, leftovers and a mixed
  cook/ready-food week rather than assuming every meal is a new recipe.

Exact competitor counts, pricing, catalogue sizes and integration claims must be
re-checked before external publication or investment/legal use.

## 11. Repository changes created from this review

Canonical additions/companions:

- `docs/family-food/product-strategy.md`;
- `docs/family-food/meal-pattern-programs.md`;
- `docs/family-food/security-architecture.md`;
- `docs/family-food/security-tooling-plan.md`;
- `docs/family-food/architecture-addendum-2026-09-13.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-13.md`;
- `docs/family-food/technical-spec-addendum-2026-09-13.md`.

Governance/state should point agents to these documents before implementation in
their scopes.

No runtime code, migration, accepted corpus, Nutrition authority or current
Assembly evidence is changed by this documentation integration.

## 12. Follow-up implementation implications

These are future authorized-scope implications, not automatic work:

1. PR7 must not hardcode breakfast/lunch/dinner or dinner-only structure.
2. PR7 should retain member pattern/program version in planning history.
3. `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` must establish reviewed program truth before PR7/PR8 consume it.
4. PR8 should accept heterogeneous member schedules and implement deterministic
   recommendation/reconciliation behavior at a bounded baseline.
5. Planning should acquire a versioned replan contract; richer preservation of
   prepared batches/perishables grows when Prep exists.
6. Shared deployment/Auth work must use the new security contract.
7. Arbitrary external URL/file import must pass the importer sandbox security
   gate.
8. Retail and AI must pass their respective trust-boundary gates before runtime
   enablement.

The Master Roadmap sequence itself is not rebooted.
