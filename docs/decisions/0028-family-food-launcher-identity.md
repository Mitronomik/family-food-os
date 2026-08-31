# ADR 0028 — FamilyFoodOS launcher identity

## Status

**ACCEPTED FOR PR1 — NORMATIVE ONLY WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS is a separate product fork bootstrapped from CosmeticWorkshopOS.
ADR 0025 established its runtime and persisted workspace identity, ADR 0026
established its Restore identity boundary, and ADR 0027 established its current
artifact identity. The inherited launcher still used source-product names in
visible startup surfaces and in its temporary-file, validation-scratch,
replacement-artifact, native-picker and loopback control-plane identities.

Launcher ownership markers are safety boundaries, not cosmetic strings. Cleanup
uses them to decide which temporary artifacts the current launcher may remove.
Treating CosmeticWorkshopOS markers as FamilyFoodOS markers would let one product
claim or clean technical files owned by another product.

## Decision

The active launcher's visible product identity is `FamilyFoodOS`. Where a
repository/application slug is required, it uses `family-food-os`.

`backend/app/identity.py` remains the canonical runtime identity authority. The
launcher package must load before runtime establishes the backend import path,
so it keeps bootstrap-safe local projections of the canonical product name and
slug instead of importing `app.identity` at package-import time. A focused test
loads the backend through the launcher's normal runtime-path mechanism and
guards those projections against drift. This bounded bootstrap projection does
not authorize independent identity duplication in other packages.

Launcher-owned scratch, validation, replacement, picker and control-plane
identities use only FamilyFoodOS-specific markers. Current filesystem ownership
prefixes use the `.family-food-os-*` namespace, validation scratch lives below
the `family-food-os` application directory, and current marker payloads,
sentinels and diagnostic protocol/server values identify FamilyFoodOS.

Inherited `CWOS`, `.cwos-*`, `cosmetic-workshop-os` and CosmeticWorkshopOS
technical markers are not compatibility aliases. FamilyFoodOS does not discover,
adopt, rename, migrate or clean source-product temporary artifacts. A file with
an old marker is left untouched even when its shape otherwise resembles a
current launcher artifact.

Renaming launcher-owned protocol and marker values changes identity only. It
does not change the loopback-only security model, HTTP semantics, capabilities,
tokens, session lifetime, native-picker behavior, Restore validation, phase
vocabulary, transition graph, cleanup lifecycle or any other Restore safety
semantic.

## Considered alternatives

1. **Retain the old launcher markers.** Rejected because a separate product
   would continue claiming CosmeticWorkshopOS identity and ownership.
2. **Accept both old and new markers.** Rejected because aliases would collapse
   the cross-product cleanup boundary and let FamilyFoodOS act on files it did
   not create under its own identity.
3. **Mechanically rename everything, including history.** Rejected because
   provenance, historical documentation and source-product fixtures are not
   current launcher identity and must remain accurate.
4. **Use only new FamilyFoodOS launcher ownership markers.** Selected because it
   establishes an unambiguous current ownership boundary while leaving source-
   product technical artifacts intact.

## Consequences

- Current launcher presentation, scratch paths, marker files, picker sentinel and
  control-plane server identity consistently identify FamilyFoodOS.
- Old source-product scratch and temporary files may remain on disk. This is
  intentional and safer than cross-product cleanup.
- Current tests and tools must expect FamilyFoodOS launcher markers; old values
  belong only in explicit negative ownership tests or historical material.
- The launcher identity projections must remain equal to the canonical backend
  values, with automated drift detection preserving that relationship.
- No user data is migrated, imported, renamed or deleted.
- No Restore state, transition, validation rule, safety-copy rule, replacement
  rule or recovery behavior changes.

## Scope and supersession

This ADR becomes normative only when PR1 is merged to `main`.

It supersedes only active launcher-owned identity and ownership assumptions
inherited from CosmeticWorkshopOS. It does not rewrite older ADRs or history,
alter backend database/runtime identity, artifact identity, frontend branding,
macOS application/package identity, business-domain semantics, or authorize any
cross-product cleanup or migration.
