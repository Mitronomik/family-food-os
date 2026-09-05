# PR4 Recipe Catalogue seed — DATA2 integration pending

Latest pass: official canonical/equivalent URLs are authorized by
[Orchestrator](https://github.com/Mitronomik/family-food-os/pull/10#issuecomment-5554016049).
Current Easter PDF/page/collection and linked MyPlate routes failed acquisition.
The [current review](../../../docs/family-food/pr4-retrieval-provenance-review.md)
records exact fallback URLs and outcomes. No fresh production artifact or
successor was accepted; drift remains unassessed. The earlier attempts below
remain historical evidence; their exact-URL restriction is superseded.

The JSON files in this directory and the existing builder/loader still contain
the obsolete PR10 corpus. They have not been regenerated from accepted DATA2
because the authorized fresh-source acquisition could not obtain complete
current representations through the tested permitted paths.
Do not use these files as DATA2 production acceptance evidence.

The authoritative successor is
[`data/curation/pr4-data2/recipe-corpus.json`](../../curation/pr4-data2/recipe-corpus.json),
accepted in PR #13 and merged at `2f5fba991f1f612ce7b4b8dfda8ebd41ad6333e7`.
Its contract is exactly 30 recipes, 189 selected ingredient mappings, 81 existing
FoodIngredient codes and 86 ordered source-backed equipment rows / 34 codes.
Source servings vary. The exact production step count remains to be derived from
reviewed source instructions; it is not an inherited invariant.

The earlier rights decision is
[superseded](../../../docs/family-food/pr4-rights-review.md) by the narrow
direct-FNS project risk posture, with source-specific evidence and attribution.
The current [provenance blocker and recovery options](../../../docs/family-food/pr4-retrieval-provenance-review.md)
record the authorized fresh retrieval attempts for 27 recipes / 22 artifacts:
20 TLS EOF and 2 HTTP 403 failures. Three exact historical source retrieval
records are reused. Fresh byte-identical artifacts and presentation-only
successors accepted in this pass: zero; authoritative drift remains unassessed. No invented midnight
instant, filesystem timestamp or generic ARS rationale is endorsed.

After that blocker is resolved, the bounded compiler must consume repository-local
accepted evidence and reviewed ordered step transcription, emit deterministic
committed JSON, and run without network in production/tests. Preserve selected
source quantities and optional/conditional wording, use only g/ml/pcs, and do not
invent densities, food-specific weights, yields, instructions or equipment.
Cooking measures (cup=240 ml, tablespoon=15 ml, teaspoon=5 ml, quart=960 ml) are
a documented normalization convention, not exact physical equivalence.

Fresh seed first/second run evidence is pending. PR4 is not COMPLETE, PR #10
must not be merged, and PR5 remains unauthorized.
