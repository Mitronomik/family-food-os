# ADR 0029 — FamilyFoodOS frontend identity

## Status

**ACCEPTED FOR PR1 — NORMATIVE ONLY WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS is a separate product fork bootstrapped from CosmeticWorkshopOS.
ADRs 0025–0028 already establish separate backend/runtime, persisted workspace,
Restore, artifact and launcher identity. The active frontend still used the
source product's npm package name, visible shell title and branding, MCh bitmap
logo and API-proxy environment namespace.

The inherited frontend also still presents cosmetic-domain routes and workflows.
Those screens remain intentionally available until their later bounded domain
migration. Product-shell identity can be separated now without pretending that
the inherited business model has already become the FamilyFoodOS target domain.

## Decision

The current frontend npm package is `family-food-os-frontend`. The document
title, application-shell accessible name, visible brand and product-specific
restart guidance use `FamilyFoodOS`.

Until a later visual-identity decision selects a real logo, the shell uses the
plain text monogram `FF`. The inherited `mch-logo.png` asset and every active
reference to it are removed. This decision does not invent a replacement visual
asset or redesign the existing shell.

The frontend development proxy is configured only by
`FAMILY_FOOD_API_PROXY_TARGET`. The inherited
`COSMETIC_WORKSHOP_API_PROXY_TARGET` variable is not an alias and does not
configure FamilyFoodOS. When the FamilyFoodOS variable is absent, the established
default `http://127.0.0.1:8000` remains unchanged.

Business-domain copy is not mechanically renamed. Terms that still describe
the inherited and still-operational workshop profile, recipes, clients, orders,
inventory and production workflows remain until those bounded contexts are
migrated deliberately. Routes, information architecture and workflow semantics
are unchanged by this decision.

## Considered alternatives

1. **Keep old frontend branding until domain migration.** Rejected because the
   active shell of a separate product would continue claiming source-product
   identity for an indeterminate period.
2. **Accept both old and new proxy environment variables.** Rejected because an
   inherited source-product setting could silently redirect FamilyFoodOS.
3. **Mechanically rename all workshop and business copy.** Rejected because a
   textual substitution would misrepresent unchanged business concepts and
   violate the staged bounded-context migration plan.
4. **Establish FamilyFoodOS shell identity while preserving inherited business
   workflows.** Selected because it creates an honest current-product boundary
   without redesigning or semantically relabeling the legacy domain.

## Consequences

- The UI may temporarily show FamilyFoodOS branding around inherited
  cosmetic-domain workflows. This is deliberate and does not imply that those
  workflows are the target FamilyFoodOS domain.
- No visual logo is selected in PR1; `FF` is a temporary text fallback.
- Old source-product proxy configuration cannot redirect FamilyFoodOS, while the
  existing default proxy behavior remains available.
- Package metadata, HTML title and active frontend product guidance consistently
  identify FamilyFoodOS.
- Existing routes, navigation, API contracts, business behavior and Restore
  safety semantics remain unchanged.
- The later consumer/PWA redesign, food-domain UI migration and project-owned UI
  skill migration remain separately gated.

## Scope and supersession

This ADR becomes normative only when PR1 is merged to `main`.

It supersedes only active frontend shell, package, logo and proxy-namespace
identity inherited from CosmeticWorkshopOS. It does not rewrite historical
documents, migrate business-domain screens, alter launcher or macOS package
identity, change backend behavior, authorize a visual redesign, or select a
permanent logo.

The currently modified vanilla frontend is transitional migration scaffolding;
the target FamilyFoodOS consumer application is the separately gated hosted
mobile-first PWA defined by ADR 0030.
