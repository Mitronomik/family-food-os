# ADR — PR10 data recovery decisions D1/D2/D3

> **Scope-preserving Option B follow-up — PROPOSED 2026-10-17:** [Two-stage PR10 contract](pr10-option-b-staged-delivery-gates-2026-10-17.md) proposes that **technical PR10-CORE/Gate2 uses the already accepted household fixture and does not require an alternate fixture or safe shared-stage batch proof**. D2's approval requirement for *future replacement fixtures* and the accepted FD-ARCH's cooked-dish-specific D2-FD exception remain intact, applying only when proposing those later changes; **neither authorizes a fixture swap today**. D3 remains mandatory before publishing or reading any **new authoritative shared-stage/finished-dish process, storage/time or step-classification policy**; existing immutable recipe reads can be used for narrowly reviewed same-day tasks, subject to a PR10-CORE source/read preflight. This proposal does **not** change D1–D3 retroactively or unblock `PR10-FD-META`. Effective only after independent review/merge; no runtime authorization.

**Later owner-directed amendment proposal (2026-10-12):** [Finished-Dish-First PR10](pr10-finished-dish-first-amendment-2026-10-12.md) explicitly proposes a **narrow D2-FD fixture-proposal eligibility exception** for a reviewed, safely storable fully cooked dish batch covering two MealEvents without a preliminary net physical-action `B<A` proof. It retains separate fixture review and D3 publication/read-path requirements. **This historic D2 approval is not silently edited; the original D2 rule still controls unless/until the later amendment is independently reviewed and merged.**

**Status:** APPROVED per explicit 2026-10-11 product-owner message in the FamilyFoodOS ChatGPT project conversation; GitHub decision provenance is a [verbatim assistant transcription](https://github.com/Mitronomik/family-food-os/pull/214#issuecomment-6112139382), **not** independent GitHub-authenticated owner approval. Repository publication pending review/merge.
**Approval evidence:** On 2026-10-11, following PR #212 merge, the user wrote: “Утверждаю решения PR10-DATA-RECOVERY: D1=yes, D2=yes, D3=yes. Зафиксируй согласованные решения и приступай к следующему ограниченному этапу в GitHub без автоматического merge.” Source: private FamilyFoodOS ChatGPT conversation, transcribed verbatim in the linked PR comment. Original chat cannot be independently inspected via GitHub; if GitHub-native owner attestation is required, seek a separate direct confirmation there.
**Approved reference:** [PR10-DATA-RECOVERY proposal](pr10-data-recovery-proposal.md), merged [PR #212](https://github.com/Mitronomik/family-food-os/pull/212).
**Base:** `main@700bdea2c9a08e3cb250aa6a9d65e01e76139a12`.

## Decision D1 — approved: bounded evidence-first source curation

Review exact existing source cards only when already accessible and independently identifiable. If they do not establish compatible input/output food forms and processing authority, move to a **small, curated, source-backed batch-prep recipe/process set** with reviewable rights and provenance. Stop repetitive arbitrary same-ingredient/string-search audits. This authorizes a bounded **research/evidence operation**, not publication of new authoritative RecipeVersions or a generalized ingestion platform.

## Decision D2 — approved: eligibility to propose a different Gate 2 fixture

A replacement fixture **may be proposed only after** a candidate demonstrates safe shared work for at least two distinct accepted MealEvents with a full physical-action comparison `B < A`. Original frozen fixture remains authoritative until a **separately reviewed and explicitly accepted** replacement pins MealPlan, RecipeVersion, RecipeStep hashes, Decimal Servings, source snapshots, and regression preservation. D2 is permission to propose, **not approval of a replacement fixture today**.

## Decision D3 — approved: mandatory publication/read-path implementation contract

Before any production shared-stage metadata or cross-recipe reuse, independently review and merge a docs-only implementation contract specifying source owner, immutable stage/process identity, recipe/version/step pins, provenance and rights, approved reader/publisher, version/replay/conflict semantics, invalidation, Household scope, Russian instructions, numerical reconciliation, transaction/failure paths and security tests. No sidecar JSON becomes runtime authority by virtue of existing in the repo. New migration/table or change to PR10-ARCH three Prep tables needs its own architecture decision.

## Preserved gates and architecture

- `PR10-META=BLOCKED`, `PR10-A/B/C`, `PR10-PDF` and Gate 2 **not authorized** until their actual evidence gates pass.
- No changes to deterministic Nutrition, Recipe or Shopping truth, immutable historical MealPlans, Pantry mutation rules, existing source provenance, release acceptance threshold or migration authority.
- No invented storage duration, temperature, blanch form or claimed time saving. UNKNOWN stays UNKNOWN.
- Current technical stack and Master Roadmap sequencing remain intact; this decision authorizes the **supporting research step before PR10-META**, not runtime delivery.
- One bounded review unit: a maximum of three candidate **stage families**; no requirement to manufacture a positive outcome. If none qualifies, return NO-GO for a new product decision.

## First authorized bounded operation

**PR10-SOURCE-SHORTLIST (research/evidence only):** inspect a maximum of three plausible stage families from existing immutable cards when sources and rights are verifiable, and otherwise independent credible/rights-reviewable batch-friendly source material. Produce a source/rights matrix and one candidate recommendation with raw/input/output form, process, quantity authority, timing/holding applicability, known unknowns and explicit rejection reasons. Do **not** promote any candidate to production. If adequate source evidence is absent, publish a negative receipt without changing Gate 2.

The full requirements and proposed stop conditions live in [PR10-DATA-RECOVERY](pr10-data-recovery-proposal.md). Further stage publication and fixture decisions require their own reviewed PR.

## FACT / ASSUMPTION / DECISION / OPEN QUESTION

**FACT:** PR #210 recorded UNKNOWN source-form equivalence for the School2022 onion pair; PR #212 reviewed the recovery proposal and is merged.

**ASSUMPTION:** a limited set of external or existing recipe cards can provide usable staged-process facts. Neither availability nor rights have yet been established for new sources.

**DECISION:** D1, D2 and D3 approved as bounded above. No acceptance requirement was weakened.

**OPEN QUESTION:** which verifiable source-backed stage, if any, will satisfy the actual two-event safe-work and net `B<A` requirement without a changed stage-authority architecture?
