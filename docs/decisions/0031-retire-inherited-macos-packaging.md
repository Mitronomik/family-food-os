# ADR 0031 — Retire inherited macOS consumer packaging

## Status

**ACCEPTED FOR PR1 — NORMATIVE ONLY WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS is a separate product fork that reuses verified engineering
foundations from CosmeticWorkshopOS. ADR 0030 establishes a hosted responsive
Web/PWA as the target consumer delivery architecture. The inherited macOS
package instead builds a self-contained local desktop product distributed as an
application bundle inside a ZIP.

Renaming that package to `FamilyFoodOS.app` would establish and maintain a local
desktop delivery commitment that the target product does not have. Retaining
the CosmeticWorkshopOS package identity would make an old-branded application
run current FamilyFoodOS launcher, backend and data paths. A neutral development
bundle would add another packaging system without a current product need.

Backend, launcher, SQLite development and source-run Restore correctness do not
depend on the package topology. The package delegates to those components; they
do not depend on it.

## Decision

The inherited macOS consumer `.app` and ZIP packaging are retired from the
active FamilyFoodOS repository build, test, verification and release surfaces.
No `FamilyFoodOS.app`, new bundle identifier, compatibility alias or neutral
development package replaces them. No supported repository command builds or
verifies the old-branded consumer package.

Generic source-run backend, launcher and SQLite development remain available as
transitional migration scaffolding. Source-run Restore, backup, migration and
native-picker behavior remain intact.

Historical package decisions, verification results, hashes and lifecycle
evidence remain source-product provenance. They do not become current
FamilyFoodOS delivery gates. Existing installed or built source-product
artifacts outside the repository are not discovered, inspected, renamed,
deleted, moved, migrated or otherwise adopted by FamilyFoodOS.

## Considered alternatives

1. **Rename the package to FamilyFoodOS.** Rejected because it would create a
   false local-desktop product commitment and require ongoing package-specific
   distribution and lifecycle work unrelated to the hosted target.
2. **Preserve the CosmeticWorkshopOS package.** Rejected because active
   source-product identity cannot be a compatibility mode for a separate
   product and would mislabel current FamilyFoodOS runtime and data behavior.
3. **Retire the inherited package.** Selected because it removes the false
   delivery surface while preserving the reusable application core and the
   historical evidence of what was previously verified.
4. **Build a neutral development package.** Rejected because source-run
   development already supplies the required migration scaffolding; a second
   package would add technology and maintenance without product value.

## Consequences

- Exact-package, clean-Mac and D5 package rehearsal are no longer current
  FamilyFoodOS gates. Their previous results remain historical evidence.
- Repository-supported development continues through the source-run backend,
  launcher, SQLite workflow and normal frontend build.
- Local Restore and backup infrastructure may remain while inherited bounded
  contexts exist, but hosted backup, recovery and deployment require separate
  later architecture under the established migration gates.
- The repository no longer supplies Finder/Dock package lifecycle, bundled
  runtime, consumer ZIP, package verification or package-install workflows.
- No PostgreSQL, authentication, tenant isolation, containers, SaaS
  infrastructure or consumer PWA implementation is authorized by this ADR.

## Scope and supersession

This ADR becomes normative only when PR1 is merged to `main`.

It supersedes only the forward FamilyFoodOS use of the inherited macOS consumer
packaging and the still-open D5 package-delivery path. ADRs 0019–0024 and their
accepted exact-package evidence remain accurate historical records. This
decision does not reopen Restore, backup, migration or update-safety semantics,
does not change backend or launcher behavior, and does not authorize work ahead
of the FamilyFoodOS migration plan.
