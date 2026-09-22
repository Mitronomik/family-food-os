# Current focus

Updated: `2026-09-22`.

## Accepted state

PR80 is merged into `main` at `f7ac885dde055900b3a6397aa64a15fe698abe5b`.

Steps 1–3 and the Step 4 Implementation Contract Gate are accepted.

Current bounded work is **Step 4B — licensed RU-NUT-DB source-semantic mapping
closure**.

Evidence:
`data/curation/ru-nut-db-step4-semantic-closure/`.

## Mapping result

For the exact five records
`SUGAR / CARROT_RED_RAW / CABBAGE_GREEN / BEET / RICE_GROATS`:

- 26 RU-NUT-DB fields reviewed;
- 18 numeric field mappings approved;
- 8 fields deliberately deferred/source-only;
- 130 source observations retained;
- 87 published numeric + 43 published zero;
- **90 V2 numeric candidate values — 18 per food**;
- source-published zero is preserved as numeric `Decimal("0")` for approved
  fields with `VALUE` source observations and explicit provenance;
- no Book2002 numeric substitution;
- no migration/schema change is required by source-zero semantics.

Deferred/source-only fields:
`carbh, a_vit, pp, carot, cholest, ethanol, sugar_ad, salt_ad`.

## Runtime readiness

After this Step 4B evidence PR is merged/reviewed, runtime may implement the
accepted five-food batch using the exact mapping manifest.

Architecture remains:

- no schema/migration;
- all FIC profiles non-current;
- current USDA profiles preserved, including generic `CARROT`;
- `CARROT_RED_RAW` and `RICE_GROATS` created as distinct identities;
- transaction-neutral one-bundle operation;
- one five-food UoW / one commit;
- exact replay zero-write;
- whole-batch rollback on one-food failure.

## Stop boundary

After Step 4B is review-ready/merged, stop for final review/merge authorization.

Do not start runtime publication or Step 5 automatically.
