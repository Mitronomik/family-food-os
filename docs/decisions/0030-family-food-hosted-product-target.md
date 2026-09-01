# ADR 0030 — FamilyFoodOS hosted product target

## Status

**ACCEPTED FOR PR1 — NORMATIVE ONLY WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS reuses proven engineering infrastructure from CosmeticWorkshopOS.
That reuse provides migration scaffolding and engineering foundations; it does
not preserve the source product's deployment model or user experience as the
FamilyFoodOS target architecture.

The repository temporarily retains the inherited local launcher, SQLite
workflow and vanilla TypeScript frontend because migration is incremental. The
FamilyFoodOS technical specification defines the target product as Web/PWA with
hosted production and shared deployment. The migration plan treats the inherited
frontend as non-target and gates construction of the new consumer PWA as later
work.

Without an explicit durable boundary, continued work on useful transitional
infrastructure could be mistaken for endorsement of a locally deployed
end-user product.

## Decision

The target FamilyFoodOS consumer delivery is a hosted, responsive Web/PWA
service. Its target request flow is:

`Consumer PWA/Web → hosted Application API → domain/services → repositories → production database`

Normal end users must not be expected to run a local launcher, start Python or
Node manually, manage a local SQLite database, or use a terminal or Git for
normal operation.

SQLite remains permitted for development, tests, vertical-slice work and
temporary migration scaffolding where the current incremental migration still
requires it. The inherited launcher and local runtime remain transitional
infrastructure until the hosted consumer architecture replaces their end-user
role. The inherited vanilla TypeScript frontend is likewise transitional and is
not the target FamilyFoodOS consumer application.

The target consumer UI remains mobile-first, responsive and installable as a
PWA. It minimizes user input and retains the conceptual primary sections
`Сегодня`, `Неделя`, `Купить`, `Заготовки` and `Дома`.

This decision does not authorize PostgreSQL, authentication or SaaS
infrastructure implementation inside PR1. Those capabilities must follow the
established migration gates unless a later explicit decision changes their
order. Backend-owned deterministic business logic remains mandatory and must
work independently of AI.

CosmeticWorkshopOS business workflows must not be mechanically ported into the
new hosted consumer UI. New food-domain contexts and consumer journeys must be
introduced deliberately under their own migration gates.

## Considered alternatives

1. **Retain a local desktop or local-first FamilyFoodOS product.** Rejected
   because it would make inherited deployment scaffolding the target user
   experience and conflict with the Web/PWA product specification.
2. **Ship local and hosted product modes as equal targets.** Rejected because it
   would create two deployment products, split architecture and operational
   expectations, and preserve a mode that is not required by the target.
3. **Rebuild everything immediately during PR1.** Rejected because it would
   bypass migration gates, combine unrelated infrastructure and domain work,
   and discard the value of incremental verification.
4. **Keep the current local stack as migration scaffolding while targeting one
   hosted Web/PWA product.** Selected because it preserves reusable engineering
   foundations without confusing temporary implementation state with the target
   product architecture.

## Consequences

- PR1 launcher identity work remains valid while launcher code exists during
  migration, but that work is not evidence that the launcher is the target UX.
- Local Restore and backup infrastructure may continue operating while inherited
  bounded contexts exist. Hosted backup and recovery require their own later
  production architecture.
- PR11 and later consumer-application work must build the actual consumer PWA,
  not merely reskin the inherited vanilla frontend.
- Future architecture documents and implementation tasks must distinguish
  transitional local infrastructure from the target hosted architecture.
- Existing local development and test workflows may continue during migration.
- This ADR alone authorizes no PostgreSQL, authentication or SaaS
  implementation and causes no user-data migration.

## Scope and supersession

This ADR becomes normative only when PR1 is merged to `main`.

It establishes the target delivery and deployment architecture for
FamilyFoodOS and clarifies the transitional role of the inherited local stack.
It does not remove or redesign that stack in PR1, alter current Restore or
backup behavior, implement hosted infrastructure, or authorize work ahead of
the migration plan's gates.
