# Current focus

Updated: `2026-09-12`

- **PR6-COMPOSITION-CORE — MERGED**, [PR #27](https://github.com/Mitronomik/family-food-os/pull/27),
  merge commit / verified starting `origin/main`:
  `d5b5ce3fdc4ec79de5454b3ed23b1d527772c0bc`.
  GitHub merged state independently verified; previous review-pending state is superseded.
- Migration head: `0029_food_composition_core`.
- **PR6-RU-FOOD-DATA — current authorized bounded operation**, branch
  `codex/pr6-ru-food-data`. Implementation verified; REVIEW-READY in
  [PR #28](https://github.com/Mitronomik/family-food-os/pull/28), awaiting review.
- Audit target: 81 existing food codes / 189 current recipe ingredient rows,
  required/optional uses separate; seven mandatory form research candidates.
- Production additions: CAULIFLOWER_FROZEN and STRAWBERRY_FROZEN_UNSWEETENED;
  2 profiles, 66 nutrient values, 2 seals, 60 ATOMIC composition references.
  APPLE_PEELED, LEMON_JUICE, ORANGE_JUICE, PASTA_COOKED, SPINACH_BABY deferred.
- Repository curation evidence only; existing Russian canonical_name is primary
  display. No new availability schema or migration 0030.
- Current recipe/profile/assessment truth unchanged; all 183 old vector seals
  retained/readable. Full readiness report identical: 30 / 189 / 30 INCOMPLETE;
  66 exact / 21 no-conversion / 37 review-required / 65 blocked; 43 estimates non-executable.
- **PR6 — NOT COMPLETE.** Stop for PR review; no autonomous merge or automatic
  B2-B2, Recipe Assembly, Serving or PR7+ start.

Evidence and limitations: [RU package](../data/curation/pr6-ru-food-data/README.md).
Verification: [progress](progress.md). Continuation: [handoff](handoff.md).
