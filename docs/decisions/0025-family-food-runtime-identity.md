# ADR 0025 — FamilyFoodOS runtime identity

Status: **ACCEPTED FOR PR1 — NORMATIVE WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS is a separate product fork bootstrapped from CosmeticWorkshopOS. The preserved source repository, source commit, bootstrap tag and Git history remain engineering provenance, but they do not define the current product identity.

Historical migrations and historical ADRs are evidence of the source system and must not be rewritten to make their identity strings current.

## Decision

The current FamilyFoodOS runtime identity is:

- application and repository slug: `family-food-os`;
- human product name: `FamilyFoodOS`;
- stable database workspace identity: `workspace.source = family-food-os`.

FamilyFoodOS uses its own runtime data namespace and locations:

- `FAMILY_FOOD_DB_PATH` selects an explicit database;
- `FAMILY_FOOD_USER_DATA_DIR` selects an explicit user-data directory;
- the development database defaults to `.local/family_food.sqlite`;
- the user-data directory defaults to `~/Documents/FamilyFoodOS`;
- the user database defaults to `~/Documents/FamilyFoodOS/data/family_food.sqlite`;
- backend liveness and handshake use `FAMILY_FOOD_BACKEND_LIVENESS_LOCK`, `FAMILY_FOOD_BACKEND_HANDSHAKE_FD` and `FAMILY_FOOD_BACKEND_HANDSHAKE_TOKEN`.

The corresponding `COSMETIC_WORKSHOP_*` variables are not aliases and do not configure FamilyFoodOS. FamilyFoodOS does not automatically discover or adopt the CosmeticWorkshopOS default data directory.

Migration `0021_family_food_identity` projects that current identity into `app_settings`. It updates `product.name`, inserts or updates the stable `workspace.source` marker, and is idempotent. It changes no table schema, changes no business-domain data, creates no AuditLog event, and does not alter Workshop Profile or `app.version`.

Restore compatibility and identity enforcement, export identity and filename grammar, Python and frontend package names beyond the backend distribution, and macOS application/package identity will be handled in later bounded PR1 slices.

## Considered alternatives

1. Keep the CosmeticWorkshopOS environment and path identity. Rejected because the separate product could discover and migrate the source product's database.
2. Support the old variables as compatibility aliases. Rejected because an inherited CosmeticWorkshopOS setting would silently redirect FamilyFoodOS to source-product data.
3. Automatically migrate or adopt the old default data directory. Rejected because automatic adoption would modify ownership and persisted identity without an explicit user-controlled migration decision.
4. Use a completely separate FamilyFoodOS environment and path identity. Selected because it makes ordinary startup isolation deterministic while leaving the source product's data untouched.

## Consequences

- FamilyFoodOS will not automatically open the CosmeticWorkshopOS database.
- Old `COSMETIC_WORKSHOP_*` settings do not configure FamilyFoodOS, and old data remains untouched.
- Tests and tools that configure the current runtime must use `FAMILY_FOOD_*`.
- Any future import or migration mechanism for CosmeticWorkshopOS data requires a separate explicit decision.
- Restore identity remains a later bounded PR1 slice and is not solved by this ADR or the runtime path separation.

## Scope and supersession

This ADR supersedes only current-runtime identity assumptions inherited from CosmeticWorkshopOS documents. It preserves CosmeticWorkshopOS source provenance and does not rewrite historical migrations or historical ADRs.

It does not reopen Restore safety semantics, compatibility policy, or any business-domain decision. The inherited cosmetic business domain remains in place until its separately approved migration slices.
