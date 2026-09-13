from __future__ import annotations

import subprocess
from pathlib import Path


def load(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def save(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def replace_required(
    text: str, old: str, new: str, label: str, count: int = 1
) -> str:
    actual = text.count(old)
    if actual < count:
        raise SystemExit(
            f"{label}: expected at least {count} occurrence(s), found {actual}"
        )
    return text.replace(old, new, count)


# architecture compatibility: source capabilities + MealPattern ownership
path = "docs/family-food/architecture-addendum-2026-09-13.md"
text = load(path)
text = replace_required(
    text,
    "**Scope:** MealPlan / Serving, Planner and Recipe Catalogue compatibility for configurable meal patterns and mixed meal sources",
    "**Scope:** MealPlan / Serving, Planner, Recipe Catalogue, Meal Pattern Catalogue and mixed-source authority compatibility",
    "architecture scope",
)
source_marker = """Where a later source model has not yet been implemented, the Planner may support
only the subset for which authoritative state exists. It must not invent future
PreparedBatch/Pantry/Retail state.
"""
source_contract = source_marker + """
### 4.1 Source capability contract

Representation and automatic Planner eligibility are separate capabilities.
PR7 must be able to represent the approved source kinds without schema redesign,
but the presence of an enum value is never evidence that the Planner may treat
that source as available supply, known nutrition or known cost.

| Source | Authority / reference | Nutrition authority | Shopping demand | Existing supply | Cost authority | Planner availability |
|---|---|---|---|---|---|---|
| `COOK_RECIPE` | immutable verified `RecipeVersion` | Nutrition Engine from RecipeVersion + Serving | authoritative recipe ingredient demand | Pantry subtraction remains Shopping/Pantry behavior, not source truth | generic Shopping estimate; Retail later | PR8 baseline may auto-select |
| `ASSEMBLY` | reproducible validated `RecipeAssembly` | Nutrition Engine from composition/assembly + Serving | authoritative assembly ingredient demand | Pantry subtraction remains Shopping/Pantry behavior | generic Shopping estimate; Retail later | PR8 baseline may auto-select after Assembly B |
| `LEFTOVER` | household leftover/prepared-supply record with origin and confirmed remaining quantity | original immutable origin/version plus confirmed remaining quantity | no new ingredient demand | consumes authoritative represented supply | sunk/unknown unless an owning model records cost | representation/user-fixed before supply model; auto-selection only after authoritative leftover supply exists, normally PR10+ |
| `PREPARED` | `PreparedBatch` / prepared inventory created by confirmed Prep execution | batch origin/version plus confirmed quantity | no new ingredient demand | consumes authoritative prepared supply | authoritative batch cost if later modeled, otherwise unknown | representation/user-fixed before PR10; auto-selection only after PR10 confirmed-execution inventory exists |
| `READY_MEAL` | validated ready-food/product reference from its future owning catalogue/Retail model | authoritative product/source profile when present; otherwise unknown | ready-item purchase demand only; never expand into invented recipe ingredients | only if an owning inventory model says it is already held | authoritative source/Retail snapshot when available | representation allowed; auto-selection deferred until ready-food authority exists, not PR8 baseline |
| `ORDER_OUT` | explicit user-fixed event or future validated provider/order reference | authoritative provider/platform profile when present; otherwise unknown | no grocery ingredient demand | no | user-confirmed/provider cost when authoritative; otherwise unknown | PR8 may preserve/render user-fixed events; automatic selection deferred |
| `EAT_OUT` | explicit user-fixed external event | authoritative provider/platform profile when present; otherwise unknown | no grocery ingredient demand | no | user-confirmed/provider cost when authoritative; otherwise unknown | PR8 may preserve/render user-fixed events; automatic selection deferred |

Rules:

- `representable != Planner-selectable`;
- unknown nutrition/cost stays unknown and cannot be silently counted as meeting a
  deterministic nutrient or budget target;
- `LEFTOVER`/`PREPARED` cannot be auto-selected merely because their source code
  exists; authoritative identity and available quantity are required;
- `ORDER_OUT`/`EAT_OUT` are valid user schedule facts before provider integration,
  but PR8 baseline does not autonomously choose them;
- PR8 Gate 1 deterministic fixture planning may rely on `COOK_RECIPE` and
  `ASSEMBLY`; other source kinds are tested for representation and fail-closed
  behavior until their owning authority is implemented.
"""
text = replace_required(
    text, source_marker, source_contract, "source capability insertion"
)
text = replace_required(
    text,
    "## 10. Read-together rule",
    "## 11. Read-together rule",
    "architecture heading 10",
)
text = replace_required(
    text,
    "## 9. Required compatibility tests for PR7/PR8",
    "## 10. Required compatibility tests for PR7/PR8",
    "architecture heading 9",
)
text = replace_required(
    text,
    "## 8. Compatibility with already implemented work",
    "## 9. Compatibility with already implemented work",
    "architecture heading 8",
)
ownership = """## 8. Meal Pattern Catalogue ownership and readiness

`MealPatternProgram` is platform-owned curated planning data. It belongs to a
**Meal Pattern Catalogue** boundary inside the existing modular monolith; this is
a code/data ownership boundary, not a new deployed service.

The Meal Pattern Catalogue owns:

- `MealPatternProgram` identity and immutable/versioned published revisions;
- Russian display/explanation text;
- eligibility rules and supported wellness goals/contexts;
- evidence/provenance references, review status and safety gates;
- lifecycle/publish/deactivate state;
- deterministic catalogue validation.

A focused platform-scoped `MealPatternProgramRepository` (or equivalently named
repository contract) exposes published eligible versions to application services.
Planner is a consumer of this catalogue; Planner does not author or publish
program truth.

`MemberMealPatternSelection` is separate, Household-owned state. It records the
accepted program ID/version or `CUSTOM`, recommender version when applicable,
user overrides and history. Household scoping applies to every selection read and
write.

Before PR7/PR8 consume production programs, the roadmap requires the bounded
supporting operation `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`. That operation owns the
catalogue schema/repository/validation and initial curated evidence-reviewed
program data. It is not a new product milestone and does not reorder the numbered
roadmap.

Children do not create a readiness exception: if no age-appropriate published
program has approved evidence, automated recommendation returns an
unsupported/safety outcome while manual/custom scheduling remains available.

"""
text = replace_required(
    text,
    "## 9. Compatibility with already implemented work",
    ownership + "## 9. Compatibility with already implemented work",
    "ownership insertion",
)
save(path, text)

# master roadmap addendum: supporting operation, source gating, terminology
path = "docs/family-food/master-roadmap-addendum-2026-09-13.md"
text = load(path)
text = text.replace(
    "initial validated range of 1–6 eating occasions/day",
    "initial supported product range of 1–6 eating occasions/day",
)
for n in range(17, 3, -1):
    text = text.replace(f"## {n}. ", f"## {n + 1}. ")
text = (
    text.replace("### 5.1 ", "### 6.1 ")
    .replace("### 5.2 ", "### 6.2 ")
    .replace("### 5.3 ", "### 6.3 ")
    .replace("### 5.4 ", "### 6.4 ")
)
support = """## 4. Required supporting operation before PR7 — PR7-SUPPORT-MEAL-PATTERN-CATALOGUE

This is a bounded supporting operation, not a new numbered product milestone.
The numbered sequence remains unchanged.

Required order:

```text
RECIPE-ASSEMBLY-B
→ PR7-SUPPORT-MEAL-PATTERN-CATALOGUE
→ PR7 MealPlan / Serving
→ PR8 Planner v0
```

**Goal:** make the deterministic recommender consume reviewed platform truth
instead of forcing PR8 to invent its own program corpus.

**Owns:**

- Meal Pattern Catalogue domain/persistence contract;
- versioned `MealPatternProgram` publication lifecycle;
- focused platform-scoped repository;
- deterministic validator;
- initial curated wellness program data needed by PR8 fixtures;
- provenance/evidence, eligibility, safety review and Russian display text.

**Non-goals:**

- no Planner ranking/reconciliation implementation;
- no clinical/therapeutic diet module;
- no AI-generated program truth;
- no child program without its own approved age-specific evidence;
- no new microservice or datastore.

**Exit criteria:** every published program used by PR8 has an immutable version,
explicit target population/eligibility, provenance/evidence, safety review,
Russian consumer text and deterministic validation. The corpus must be sufficient
for the authorized PR8 fixture scenarios; when no safe eligible program exists,
the recommender must return a bounded unsupported outcome rather than add filler
data.

Any schema change in this supporting operation uses the next authorized forward
migration and does not rewrite accepted migration history.

"""
text = replace_required(
    text,
    "## 5. PR7 scope amendment — MealPlan / Serving",
    support + "## 5. PR7 scope amendment — MealPlan / Serving",
    "roadmap support operation",
)
old_source = """Planner may deliberately use leftovers/prepared/ready/out-of-home sources rather
than require a fresh Recipe in every slot.

Planner records an explicit source choice and source reference where the source
requires one. It must use authoritative represented supply/state and must not
invent a RecipeVersion or future PreparedBatch/Pantry/Retail state merely to make
a source option selectable.
"""
new_source = """The PR8 baseline automatically selects only source kinds whose required authority
already exists at that milestone: `COOK_RECIPE` and validated `ASSEMBLY`.

PR8 may preserve/render user-fixed non-recipe events represented by PR7, but
representation does not make a source automatic Planner supply:

- `LEFTOVER` / `PREPARED`: no automatic selection until authoritative
  leftover/prepared inventory and quantity exist, normally after PR10 confirmed
  Prep execution or another separately approved supply operation;
- `READY_MEAL`: no automatic selection until an owning ready-food/product model
  provides the required identity and truth; Retail is not pulled forward;
- `ORDER_OUT` / `EAT_OUT`: may be explicit user schedule decisions, while
  autonomous selection is deferred to a later explicit decision.

Unknown nutrition or cost remains unknown and cannot be silently credited toward
nutrition or budget targets. Planner records an explicit source choice/reference
and must not invent RecipeVersion, PreparedBatch, Pantry, Retail, provider or
price state merely to make an option selectable.
"""
text = replace_required(text, old_source, new_source, "roadmap source gating")
gate_marker = "- mixed-source MealPlans do not require synthetic RecipeVersions.\n"
gate_extra = (
    gate_marker
    + "- `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is complete before PR7/PR8 consume published programs;\n"
    + "- Planner automatic source selection follows the authority gates in `architecture-addendum-2026-09-13.md`.\n"
)
text = replace_required(text, gate_marker, gate_extra, "roadmap gate additions")
save(path, text)

# meal pattern contract: supported terminology + explicit owner/readiness
path = "docs/family-food/meal-pattern-programs.md"
text = load(path)
text = text.replace(
    "`6` is an initial validated UX/product range,",
    "`6` is an initial supported product range,",
)
for n in range(17, 7, -1):
    text = text.replace(f"## {n}. ", f"## {n + 1}. ")
text = text.replace("### 12.1 ", "### 13.1 ")
owner = """## 8. Ownership and publication readiness

`MealPatternProgram` is platform-owned data in the Meal Pattern Catalogue
boundary. The catalogue owns immutable/versioned program truth, Russian display
text, eligibility, provenance/evidence, safety review and lifecycle status.
Planner only reads published eligible program versions.

`MemberMealPatternSelection` is Household-owned state. It records an accepted
program ID/version or `CUSTOM`, user overrides, recommender version when relevant
and history; it is not part of the platform catalogue.

Before PR7/PR8 rely on production programs, the required supporting operation
`PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` establishes the catalogue
schema/repository/validator and initial curated evidence-reviewed program data.
This operation is a bounded prerequisite, not a new product milestone or network
service.

A program that has not passed that readiness path cannot be ranked as production
truth. Missing safe candidates produce an unsupported/safety result.

"""
text = replace_required(
    text,
    "## 9. Program examples are data, not architecture",
    owner + "## 9. Program examples are data, not architecture",
    "meal pattern owner insertion",
)
roadmap_marker = """Expected implementation ownership:

- PR7 / MealPlan-Serving domain: model meal opportunities, participation and
  accepted member pattern reference;
"""
roadmap_repl = """Expected implementation ownership:

- `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE`: publish the initial reviewed platform
  program catalogue and deterministic validation before PR7/PR8 consume it;
- PR7 / MealPlan-Serving domain: model meal opportunities, participation and
  accepted member pattern reference;
"""
text = replace_required(
    text, roadmap_marker, roadmap_repl, "meal pattern roadmap ownership"
)
save(path, text)

# product strategy: terminology and activation distinction
path = "docs/family-food/product-strategy.md"
text = load(path)
text = text.replace(
    "- `architecture.md` — architecture, ownership and persistence boundaries;",
    "- `architecture.md` + `architecture-addendum-2026-09-13.md` — architecture, ownership, mixed-source authority and persistence boundaries;",
)
text = text.replace(
    "Initial validated product range is one to six planned eating occasions",
    "Initial supported product range is one to six planned eating occasions",
)
source_note_marker = """The exact enum/API representation belongs to the owning implementation PR, but
Planning must not assume every slot has a Recipe.
"""
source_note = source_note_marker + """
Representable source kinds are not automatically Planner-selectable. Automatic
selection is enabled only when the source's identity, quantity/supply, nutrition
and other required truth have an owning authoritative model. PR8 baseline
automatically chooses RecipeVersion/RecipeAssembly-backed sources; other source
families follow the capability gates in `architecture-addendum-2026-09-13.md`.
"""
text = replace_required(
    text, source_note_marker, source_note, "product source gate note"
)
save(path, text)

# technical spec addendum: terminology precision
path = "docs/family-food/technical-spec-addendum-2026-09-13.md"
text = load(path)
text = text.replace(
    "initial validated configuration\nrange",
    "initial supported configuration\nrange",
)
old = """Historical recipe categories such as `breakfast`, `lunch`, `dinner` and `snack`
remain useful recipe/meal-role metadata. They must **not** be interpreted as a
fixed global daily schedule.
"""
new = """Historical examples such as `breakfast`, `lunch`, `dinner` and `snack` are
not a frozen shared enum. Recipe classification and a member's planning
`MealRole` are separate concepts and neither may be inferred from the other
without explicit deterministic suitability rules.
"""
text = replace_required(text, old, new, "technical spec meal type wording")
save(path, text)

# research integration: stale canonical list + readiness implication
path = "docs/research/household-food-os-package-integration-2026-09-13.md"
text = load(path)
old = """Canonical additions:

- `docs/family-food/product-strategy.md`;
- `docs/family-food/meal-pattern-programs.md`;
- `docs/family-food/security-architecture.md`.
"""
new = """Canonical additions/companions:

- `docs/family-food/product-strategy.md`;
- `docs/family-food/meal-pattern-programs.md`;
- `docs/family-food/security-architecture.md`;
- `docs/family-food/security-tooling-plan.md`;
- `docs/family-food/architecture-addendum-2026-09-13.md`;
- `docs/family-food/master-roadmap-addendum-2026-09-13.md`;
- `docs/family-food/technical-spec-addendum-2026-09-13.md`.
"""
text = replace_required(text, old, new, "research canonical list")
follow = """3. PR8 should accept heterogeneous member schedules and implement deterministic
   recommendation/reconciliation behavior at a bounded baseline.
"""
follow_new = """3. `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` must establish reviewed program truth before PR7/PR8 consume it.
4. PR8 should accept heterogeneous member schedules and implement deterministic
   recommendation/reconciliation behavior at a bounded baseline.
"""
text = replace_required(text, follow, follow_new, "research follow-up")
text = (
    text.replace("\n4. Planning should acquire", "\n5. Planning should acquire")
    .replace("\n5. Shared deployment/Auth", "\n6. Shared deployment/Auth")
    .replace("\n6. Arbitrary external", "\n7. Arbitrary external")
    .replace("\n7. Retail and AI", "\n8. Retail and AI")
)
save(path, text)

# root AGENTS: discovery + durable invariants
path = "AGENTS.md"
text = load(path)
marker = """- [Product Strategy](docs/family-food/product-strategy.md);
- [Meal Pattern Programs](docs/family-food/meal-pattern-programs.md).
"""
repl = """- [Product Strategy](docs/family-food/product-strategy.md);
- [Meal Pattern Programs](docs/family-food/meal-pattern-programs.md);
- [Architecture Compatibility Addendum](docs/family-food/architecture-addendum-2026-09-13.md).
"""
text = replace_required(text, marker, repl, "AGENTS architecture addendum link")
invariant_marker = """- Household planning optimizes shared execution as well as individual targets.
  Shared-base/variant behavior may reduce duplicate cooking, but hard exclusions
  always dominate sharedness. Leftovers, prepared food, ready food and eating
  outside may be legitimate meal sources; not every meal slot implies a Recipe.
"""
invariant_repl = invariant_marker + """  Representability does not grant automatic Planner availability: each source
  follows the authority/capability matrix in the architecture addendum, and
  unknown nutrition/cost/supply stays unknown.
- `MealPatternProgram` is platform-owned curated catalogue truth;
  `MemberMealPatternSelection` is Household-owned accepted state. The required
  `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` supporting operation establishes reviewed
  program truth before PR7/PR8 consume it; Planner never invents program data.
"""
text = replace_required(text, invariant_marker, invariant_repl, "AGENTS new invariants")
save(path, text)

# backlinks from canonical originals
path = "docs/family-food/architecture.md"
text = load(path)
marker = "**Related decision:** ADR 0032, `FamilyFoodOS persistence portability and shared-deployment tenancy gate`\n"
addition = marker + """
> **Later canonical addendum — 2026-09-13:**
> [Architecture Compatibility Addendum](architecture-addendum-2026-09-13.md)
> must be read with this document for MealPlan/Planner mixed-source authority,
> `MealRole` vs Recipe classification and Meal Pattern Catalogue ownership.
"""
text = replace_required(text, marker, addition, "architecture backlink")
save(path, text)

path = "docs/family-food/master-roadmap.md"
text = load(path)
marker = "**Updated:** `2026-09-12`\n"
addition = marker + """
> **Later canonical addendum — 2026-09-13:**
> [Master Roadmap Addendum](master-roadmap-addendum-2026-09-13.md) must be read
> with this roadmap for PR7+ meal-pattern, mixed-source/replan and security scope,
> including the required Meal Pattern Catalogue supporting operation.
"""
text = replace_required(text, marker, addition, "roadmap backlink")
save(path, text)

path = "docs/family-food/technical-spec.md"
text = load(path)
marker = "> конфликтует с ними по архитектуре или порядку реализации.\n"
addition = marker + """>
> **Later canonical addenda — 2026-09-13:** read this historical source together
> with [Technical Specification Addendum](technical-spec-addendum-2026-09-13.md),
> [Architecture Compatibility Addendum](architecture-addendum-2026-09-13.md) and
> [Master Roadmap Addendum](master-roadmap-addendum-2026-09-13.md).
"""
text = replace_required(text, marker, addition, "technical spec backlink")
save(path, text)

# current focus: terminology + blocker resolution + verification condition
path = "state/current-focus.md"
text = load(path)
text = text.replace(
    "initial validated range 1–6 eating opportunities/day",
    "initial supported product range 1–6 eating opportunities/day",
)
marker = """Compatibility correction included in PR #37:

- `docs/family-food/architecture-addendum-2026-09-13.md` is the canonical compatibility addendum for these PR7/PR8 seams;
- `meal-pattern-programs.md`, `master-roadmap-addendum-2026-09-13.md` and `technical-spec-addendum-2026-09-13.md` reference and enforce the same rules;
- no runtime/schema/migration/corpus change is introduced by this correction.
"""
repl = marker + """
Review-blocker resolution included in PR #37:

- mixed-source authority/capability matrix separates PR7 representation from Planner auto-selection; PR8 baseline auto-selects only RecipeVersion/RecipeAssembly-backed sources, while LEFTOVER/PREPARED/READY_MEAL/out-of-home sources remain gated by their authoritative state;
- `MealPatternProgram` ownership is assigned to the platform Meal Pattern Catalogue, while accepted member selection remains Household-owned;
- required supporting operation `PR7-SUPPORT-MEAL-PATTERN-CATALOGUE` is inserted after Assembly B and before PR7 without changing numbered milestone order;
- `validated 1–6` terminology is corrected to an initial supported product range; evidence/safety remains program-specific;
- canonical base documents link to their 2026-09-13 addenda;
- `.github/workflows/docs-verification.yml` implements the required docs-tier `git diff --check`, staged `git diff --cached --check`, scope listing and repository-relative link gate.
"""
text = replace_required(text, marker, repl, "state blocker resolution")
old_next = "Next authorized action: human re-review of corrected PR #37. Stop after review-ready publication. Merge requires separate explicit post-review authorization."
new_next = "Next authorized action: current-head docs verification must PASS, then human re-review of corrected PR #37. Merge requires separate explicit post-review authorization."
text = replace_required(text, old_next, new_next, "state next action")
save(path, text)

# Verification workflow: make staged audit a real base-index audit.
path = ".github/workflows/docs-verification.yml"
text = load(path)
old = """          git reset --mixed HEAD
          git add -- "${changed[@]}"
          git diff --cached --check
          printf 'Staged paths:\\n'
          git diff --cached --name-only | sed 's/^/  /'
          git reset --mixed HEAD
"""
new = """          tmp_index="$(mktemp)"
          rm -f "${tmp_index}"
          export GIT_INDEX_FILE="${tmp_index}"
          git read-tree "${base}"
          git add -A
          git diff --cached --check "${base}"
          printf 'Staged paths:\\n'
          git diff --cached --name-only "${base}" | sed 's/^/  /'
          rm -f "${tmp_index}"
          unset GIT_INDEX_FILE
"""
text = replace_required(text, old, new, "workflow staged audit")
save(path, text)

# Remove one-shot automation from final branch state.
for transient in (
    ".github/workflows/pr37-fix-blockers-once.yml",
    ".github/scripts/pr37_fix_blockers.py",
):
    p = Path(transient)
    if p.exists():
        p.unlink()

# Normalize trailing whitespace in the entire final PR diff so exact git checks
# are meaningful and Markdown hard-break spaces do not defeat the canonical gate.
changed = subprocess.check_output(
    ["git", "diff", "--name-only", "origin/main"], text=True
).splitlines()
for item in changed:
    p = Path(item)
    if not p.is_file():
        continue
    try:
        raw = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    normalized = "\n".join(line.rstrip(" \t") for line in raw.splitlines())
    if raw.endswith("\n"):
        normalized += "\n"
    p.write_text(normalized, encoding="utf-8")
