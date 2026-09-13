# FamilyFoodOS — Technical Specification Addendum, 2026-09-13

**Status:** canonical addendum to the historical MVP technical specification  
**Purpose:** remove ambiguity introduced by later product/security decisions without rewriting historical source text

## 1. Authority

`technical-spec.md` remains the historical product requirements source. Later
canonical architecture, roadmap and this addendum control where the old text is
now incomplete or conflicts with approved decisions.

Read together with:

- `architecture.md`;
- `master-roadmap.md`;
- `master-roadmap-addendum-2026-09-13.md`;
- `product-strategy.md`;
- `meal-pattern-programs.md`;
- `security-architecture.md`;
- `food-composition-and-assembly.md`;
- `nutrition-core.md`.

## 2. Product definition refinement

The operational week is now explicitly:

```text
Household
→ member meal-pattern selections / schedules
→ household meal events
→ RecipeVersion / RecipeAssembly / other meal source
→ individualized Servings
→ Pantry / leftovers
→ Shopping
→ Prep / freezer
→ daily execution
→ replan
→ feedback
→ next week
```

The product is a household execution/replanning system, not a menu generator.

## 3. HouseholdMember refinement

The old `HouseholdMember` field examples are not a frozen schema.

Planning must be able to associate a member with:

- accepted MealPatternProgram version or CUSTOM pattern;
- configured meal opportunities / schedule;
- participation in household meal events;
- existing goals/activity/context supported by the wellness product;
- individual Serving needs;
- hard exclusions/preferences.

Exact schema belongs to PR7 and must follow `meal-pattern-programs.md`.

## 4. Meal frequency / meal type refinement

Historical recipe categories such as `breakfast`, `lunch`, `dinner` and `snack`
remain useful recipe/meal-role metadata. They must **not** be interpreted as a
fixed global daily schedule.

The product must represent, at minimum in its initial validated configuration
range, 1–6 eating opportunities per member/day and heterogeneous member
patterns.

Examples include dinner-only, breakfast-only, breakfast+dinner, 3 meals, 5 or 6
planned eating opportunities.

## 5. Planner refinement

The Planner receives accepted member meal patterns and compiles them into a
household week.

Planner objectives now explicitly include:

- household sharedness / minimized duplicate cooking;
- cross-recipe ingredient reuse;
- leftovers/prepared food;
- perishability/waste risk;
- configurable meal sources;
- future package-surplus cost when Retail data exists;
- versioned deterministic replan of the remaining horizon.

Planner v0 remains deterministic filters + scoring/heuristics. OR-Tools is not a
required dependency until evidence demonstrates a need.

## 6. Meal source refinement

A planned meal event may be satisfied by something other than a new Recipe.

Planning must be able to evolve to represent at least:

```text
COOK
LEFTOVER
PREPARED
READY_MEAL
ORDER_OUT
EAT_OUT
```

The owning implementation PR chooses exact names/storage.

## 7. Meal-pattern recommendation

A new deterministic Meal Pattern Recommender is approved as product scope.

It does not invent diets. It ranks curated/versioned wellness programs with
provenance, eligibility and safety gates using structured member context.

The user accepts, rejects or customizes the proposal before it controls future
planning.

The system must not encode a universal claim that a particular meal frequency is
always superior for weight loss or health. Medical/therapeutic diet prescription
remains outside MVP.

## 8. Consumer UX refinement

The historical `Today` example listing breakfast/lunch/dinner is illustrative,
not a hardcoded navigation/data rule.

`Today` and `Week` render the accepted member/household pattern. A household may
therefore show one meal event on a day, three events, five events, heterogeneous
member participation or another supported configuration.

The UX remains minimal-input:

```text
system recommends/prefills
→ user accepts / changes / chooses custom
```

## 9. Replan refinement

"Plans changed" is elevated from a convenience action to a core product
capability.

Replan creates a new MealPlan revision for the remaining horizon, preserves
history, explains the diff and prefers minimum disruption to already purchased,
prepared or perishable food as those contexts become available.

Derived Shopping/Prep/PDF state becomes stale when its source plan revision is
no longer current.

## 10. Prep refinement

The historical Batch Cooking Engine direction is extended toward a Prep DAG with
active/passive time, equipment, dependencies and storage transitions.

This is a domain capability, not permission to introduce a separate scheduling
microservice or advanced solver before evidence.

## 11. Retail refinement

The original generic Shopping/Retail separation remains valid.

Future effective basket optimization may consider package surplus, expected
waste, delivery/service fees, additional-store friction and user time, but only
after generic Shopping and official/approved Retail access exist.

## 12. AI refinement

The old AI sections are strengthened by `security-architecture.md`.

AI output is untrusted proposal data. Runtime AI does not get direct DB write,
SQL, shell, filesystem, arbitrary HTTP, payment secrets or unrestricted Retail
credentials.

Tool-enabled AI requires typed allowlisted Tool Broker, deterministic policy,
authorization and explicit confirmation for high-impact actions.

The entire core remains functional with `AI_ENABLED=false`.

## 13. Security refinement

The short security list in the historical technical specification is superseded
by the complete `security-architecture.md` contract.

It adds staged requirements for:

- BOLA/object authorization;
- OIDC/OAuth/browser security;
- passkeys/WebAuthn direction;
- importer SSRF/file safety;
- third-party API safety;
- webhook/token handling;
- prompt injection and excessive agency;
- data/children privacy;
- secret/log redaction;
- SAST/SCA/SBOM/provenance/signing;
- backup/restore and operational gates.

Security controls become mandatory when their trust boundary exists; they do not
force premature infrastructure.

## 14. Technology-stack interpretation

The historical stack section is not permission to replace current accepted
repository implementation.

Current canonical architecture retains:

- Python/FastAPI application backend;
- synchronous SQLAlchemy 2.x Core behind repositories/UoW for new food contexts;
- ordered SQLite migration authority during isolated/local core work;
- PostgreSQL/Auth/HouseholdMembership at the existing shared-deployment gate;
- Next.js/PWA as the target consumer frontend when its roadmap milestone starts.

A NestJS/Prisma greenfield bootstrap from the external research package is not
adopted.

## 15. Metrics refinement

In addition to historical Activation/Retention/Plan Completion metrics, real
family validation should record:

- Planned Meal Execution Rate;
- decision-free meal events;
- Prep adoption;
- replan success;
- waste signal;
- budget variance;
- repeat trust / Week 2 / Week 4 use.

## 16. MVP interpretation

No future MVP/vertical-slice implementation may hardcode "dinner only" merely
because an external research document used dinners as a scope-reduction example.

A test cohort may choose dinner-only. The domain must remain capable of the
approved flexible meal-pattern model from PR7 onward.
