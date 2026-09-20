# DC1 recovery checkpoint — pre-rebuild

Captured from branch `data/data-corpus-v1-dc1` after known commit
`b7bc19e8881ddc90b95bd8d13c75e72ee4623295` and before any regeneration.

This directory preserves the inconsistent six-file package exactly as it existed
before recovery work. It is historical evidence only and must not be used as the
final DC1 result.

Local source-artifact checkpoint was also created outside the repository before
regeneration. Its retained source files and hashes are described in the rebuilt
DC1 `source-artifacts.json`.

Known pre-rebuild symptoms:
- 68 candidate rows remained;
- some candidate rows had empty category / zero variant and ingredient demand;
- summary reported 55 demands / 23 existing / 32 requiring work;
- variant split reported 27/41;
- README mixed numbers from different computations.

Do not edit files in this recovery directory during rebuild.
Note: after the recovery checkpoint was created, repository docs verification required removal of Markdown hard-break trailing spaces from this copied README. The exact original pre-rebuild bytes remain preserved in commit `b7bc19e8881ddc90b95bd8d13c75e72ee4623295`; no data/metric content was changed by that formatting correction.
