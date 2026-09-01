# ADR 0026 — FamilyFoodOS Restore workspace identity

## Status

**ACCEPTED FOR PR1 — NORMATIVE ONLY WHEN PR1 IS MERGED TO `main`**

Date: `2026-08-31`

## Context

FamilyFoodOS is a separate product fork bootstrapped from CosmeticWorkshopOS.
Its current migration chain ends at `0021_family_food_identity`, and that
migration records the stable machine marker `workspace.source = family-food-os`
in `app_settings`.

The inherited Restore validation accepted any database whose migration history
was an exact known ordered prefix and whose expected foundational tables were
present. That rule cannot distinguish a CosmeticWorkshopOS database ending at
`0020_artifact_audit_operations` from a hypothetical unmarked FamilyFoodOS
database at the same point. There was no released FamilyFoodOS product or
database format before migration 0021.

Accepting an unmarked 0020 database through Restore would therefore collapse the
separate-product boundary and allow CosmeticWorkshopOS data to be migrated as
though it were already a FamilyFoodOS workspace.

## Decision

A Restore candidate is a FamilyFoodOS database only when both conditions hold:

1. its valid ordered migration lineage includes
   `0021_family_food_identity`;
2. `app_settings` contains exactly
   `workspace.source = family-food-os`.

A candidate ending before 0021 is not a FamilyFoodOS Restore source. A candidate
with a missing, malformed or different `workspace.source` value is not a
FamilyFoodOS Restore source. The marker alone is also insufficient: a candidate
with the exact value but no recorded identity migration is rejected.

Restore does not use `product.name` as machine identity because it is
human-facing and mutable. Filename, containing directory, backup name and
database filename are also not identity proof. Restore never applies migrations
to a rejected candidate to make it pass. The selected source remains immutable
and read-only under the existing Restore contract.

Lineage validation remains earlier than identity validation. Malformed, unknown,
reordered, skipped, duplicated or newer migration histories retain their
specific rejection categories and do not reach the FamilyFoodOS identity check.
Ordinary user-facing errors remain bounded and non-technical; they do not expose
migration IDs or settings values.

The same shared workspace validation continues to verify the mandatory current
`before_restore` safety copy. A current FamilyFoodOS safety copy contains both
the identity migration and exact machine marker and must pass without any weaker
verification path.

## Considered alternatives

1. **Accept any known CosmeticWorkshop-era lineage.** Rejected because an
   unmarked 0020 database is indistinguishable from CosmeticWorkshopOS and would
   erase the separate-product boundary.
2. **Trust `product.name`.** Rejected because it is a human-facing mutable
   setting, not stable machine identity.
3. **Trust filename or path.** Rejected because names and locations can be
   copied or changed and say nothing authoritative about database contents.
4. **Require only `workspace.source`.** Rejected because a manually inserted
   value without the identity migration would be spoofable and would not prove
   FamilyFoodOS lineage.
5. **Require both 0021 lineage and exact `workspace.source`.** Selected because
   the two independent persisted facts establish the first released
   FamilyFoodOS database boundary without trusting mutable presentation data.

## Consequences

- FamilyFoodOS had no released database format before 0021, so rejecting every
  earlier lineage does not strand a released FamilyFoodOS Restore format.
- An unmarked 0020 database cannot be distinguished from CosmeticWorkshopOS;
  accepting it would collapse the separate-product boundary.
- Old or unmarked CosmeticWorkshopOS databases require a separately designed
  import or migration mechanism, not Restore.
- The ADR 0016 phrase “historical application backup from a supported schema
  version” is intentionally narrowed to historical FamilyFoodOS backups whose
  lineage includes the FamilyFoodOS identity migration.
- A backup of a deliberately supplied pre-0021 database taken immediately before
  identity migration is not a supported FamilyFoodOS Restore source. It remains
  a safety/source artifact; supporting migration or import of that source
  product requires a separate decision.
- No other ADR 0016 safety semantics are reopened. Candidate immutability,
  read-only validation, mandatory safety copy, atomic replacement, rollback,
  recovery and audit boundaries remain unchanged.

## Scope and supersession

This ADR becomes normative only when PR1 is merged to `main`.

It supersedes only the inherited product-recognition portion of ADR 0016 Restore
validation. ADR 0018's shared validation-session reuse follows that bounded
recognition rule, but none of ADR 0018's interaction or session semantics is
superseded. This ADR does not rewrite either older ADR and does not alter ADR
0016's twelve-phase state machine, transition graph, startup recovery matrix,
`replacement_intent`, launcher ownership, immutable-source rule, mandatory
`before_restore` safety copy or AuditLog boundary. It does not redesign the
Restore UI or authorize a new import/migration workflow.
