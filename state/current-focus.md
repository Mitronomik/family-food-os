# Current focus

Updated: `2026-09-20`.

## Accepted state

PR6, PR7 supporting meal-pattern catalogue, PR7 and PR8 are COMPLETE.
Gate1-A audit baseline and DATA-CORPUS-V1 / DC0 are COMPLETE.
PR #70 is MERGED at `b9768984392982bd05d28fc0f7793453fe8378b5`.
Its accepted DC1 recovery package remains in `data/curation/data-corpus-v1-dc1/`.
This accepts evidence/curation, not production food or recipe truth.
Issue #67 remains open; the broader corpus program is not complete.
SQLite head remains `0032_meal_plan_serving`; `0033_recipe_template_catalogue`
remains reserved. PR #66 remains closed without merge and superseded.

## Current authorized operation

Finish PR #71 after merging the accepted PR #70 base, synchronize state,
verify the updated PR and merge it under the user's explicit instruction.
No new product milestone or production publication is authorized by that instruction.

See [integration plan](../docs/family-food/corpus-v03-integration-plan.md) and
[reconciliation package](../data/curation/corpus-v03-reconciliation/README.md).
PR #71 accounts for all 68 historical PR70 families, 479 v0.3 cards,
1473 routes and 2693 food occurrences. Its 46 queues are review queues,
not publication manifests; lexical groups are not canonical food equivalence.

The generated package retains its original historical comparison pins
`main@d8c76a6` and `PR70@c23227b`. Its `pr70_merged=false` describes that
capture, not current GitHub status. The accepted PR70 head `514c6b1` has
byte-identical source inputs; do not rewrite historical receipts.

## Sequence and next boundary

DC1 recovery evidence is accepted through #70; v0.3 reconciliation is delivered
through #71, pending completion of this authorized merge operation.
DC2/DC3/DC4, Gate1-CLOSE and PR9 remain NOT STARTED.

After #71 merge, the next proposed bounded task is to resolve exact food/form,
source, rights and nutrient-method decisions for a useful first DC2 party.
That task and any production publication require their own explicit scope.
Stop after #71 merge; do not start DC2/DC3, Shopping, Retail, AI, Auth/PostgreSQL
or generalized ingestion. Follow the canonical DATA-CORPUS-V1 contract.
