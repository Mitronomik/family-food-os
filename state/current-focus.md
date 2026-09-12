# Current focus

Updated: `2026-09-12`

- **PR6-RU-FOOD-DATA — MERGED / delivered**, [PR #28](https://github.com/Mitronomik/family-food-os/pull/28).
  GitHub merged state and fetched starting `origin/main` independently verified:
  `4180297d47d68a0e0d9efbe7a7a27f3900c4f388`.
- Verified populated production baseline: migration `0029_food_composition_core`,
  185 FoodIngredients, 30 current recipes / 189 ingredient rows. PR28 contributes
  exactly CAULIFLOWER_FROZEN and STRAWBERRY_FROZEN_UNSWEETENED.
- **PR6-DATA-B2-B2-REDESIGNED — current explicitly authorized bounded operation**,
  branch `codex/pr6-data-b2-b2-redesigned`. REVIEW-READY in
  [PR #29](https://github.com/Mitronomik/family-food-os/pull/29); awaiting review.
- Audit universe re-resolved: 37 target rows / 23 recipes / 19 original foods;
  all 46 current uses retained. Only the two approved frozen forms may be remapped.
- Five PR28-deferred forms, APPLE profile/bindings and three yield cases retain
  their blockers. Estimates remain non-executable unless independently superseded
  by reviewed exact evidence. No catalogue expansion or estimate execution policy.
- Preflight clarification: none of the four candidate foods has a composition
  v1 on this main (PR28 classified them NOT_READY). The v2 rule is conditional
  on existing v1; the supported candidates receive their first ATOMIC v1.
- **PR6 — NOT COMPLETE.** No autonomous merge or automatic PR6-CLOSE,
  Recipe Assembly, Serving or PR7+ start. PR6-CLOSE is a later review/gate only.

Evidence: [B2-B2 package](../data/curation/pr6-data-b2-b2-redesigned/README.md).
Verification and continuation: [progress](progress.md), [handoff](handoff.md).
