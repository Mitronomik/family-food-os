# R1-D Planner source admission inventory

Accepted base: `e350e747a9c6e06e74b2cd450637c25a442c8749`

This package turns the retained Russian recipe universe into one closure queue.

Counts:
- total retained recipe identities: **547**
- USSR82: **68**
- School2022: **265**
- RU-MR-2019: **214**
- known current Russian production Recipe publications in the R1 path: **2**
- retained source recipes still requiring production reconciliation: **545**

The two known current Russian publications are intentionally inactive:
- USSR82-697 — blocked on consumed-Nutrition/source identity authority;
- School2022 53-19з — valid no-thermal control but Planner-role unsupported (`other`).

Important: `NOT_PUBLISHED_IN_CURRENT_RUSSIAN_R1_PATH` does not mean rejected.
It means the retained source recipe has not yet been reconciled into an authoritative
production RecipeVersion in the current R1 path.

This inventory does not grant activation, Nutrition authority or household
applicability. It exists so future batches are selected from the complete corpus
instead of one showcase recipe at a time.
