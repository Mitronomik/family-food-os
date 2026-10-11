# PR10-META-FORM — exact School2022 onion cut/form verification

**Date:** 2026-10-11  
**Issue:** [#209](https://github.com/Mitronomik/family-food-os/issues/209)  
**Accepted base:** `main@0a45188f79cf2eecdbd476715882e0f7cb97e4d6` (#208 merged)  
**Verdict:** **UNKNOWN — SOURCE_FORM_NOT_INDEPENDENTLY_VERIFIED**  
**PR10-META:** **BLOCKED**. Neither PR10-A/B/C nor PR10-PDF/Gate2 is authorized.

## FACT — exact accepted evidence

The reviewed R3-C [frozen publication](../../data/curation/r3c-post-r3b-catalogue-gate/frozen-batch.json) binds salmon `ru-school2022:recipe:54-17р`. The reviewed R2-B [publication](../../data/curation/r2b-fish-main-diversity/publication-specs.json) binds pollock `ru-school2022:recipe:54-7р`. Both identify the same **source document SHA256**:

`c9264cf521ae699fb30a964d5668caec8f31ff1efc1f13a3dd055df40ebafb5d`.

Their accepted source-reviewed published process explicitly includes onion blanching, but the salmon published process does **not** specify an exact pre-blanch cutting form; the pollock process requires shredding. They are different cards in one source document, not two independent authorities. Consult [PR10-META-ONION](pr10-meta-onion-blanch-preflight.md) and [pinned evidence receipt](pr10-meta-onion-blanch-evidence.json) for exact MealEvent, RecipeVersion, RecipeStep and SHA pins.

## External corroboration is not the pinned source

An accessible indexed 2021 recipe collection at [nsergi16.profiedu.ru](https://nsergi16.profiedu.ru/file/download?id=2695) includes comparable preparation language about shredding onion before blanching. **Document identity is not established.** The external document's downloaded bytes could not be obtained/hashed in this review; there is no demonstrated equality to the pinned 2022 SHA256 above. Similar numbering and process wording are not a sufficient identity proof.

Do **not** promote the 2021 wording into the immutable School2022 salmon RecipeVersion, assert the School2022 original card has a specific unreviewed cut, or alter existing step text. This is corroboration/discovery only, not accepted publication authority.

## Source-form decision matrix

| Question | Salmon 54-17р | Pollock 54-7р | Verdict |
| --- | --- | --- | --- |
| Canonical onion identity | `ONION_BULB_FRESH` | `ONION_BULB_FRESH` | MATCH |
| Onion blanching in published source-reviewed instructions | Yes | Yes | MATCH |
| Independently confirmed same original-card pre-blanch cut/form | UNKNOWN | Shredded in accepted published process | **UNKNOWN** |
| Common source-reviewed post-blanch output form and physical batch compatibility | Unpublished | Unpublished | **UNKNOWN** |
| Same preparation session, safe holding or storage across lunch/dinner | Unverified | Unverified | **UNKNOWN** |
| Positive net physical-action reduction after cutting, splitting and cleaning | Unverified | Unverified | **UNKNOWN** |

**Decision: UNKNOWN**, not YES or NO. No evidence supports a definitive mismatch either. Form uncertainty alone blocks shared grouping. Independent hold, equipment and net `B < A` constraints also remain unproven.

## Exact next evidence required

Obtain the **byte-identical** School2022 source PDF with SHA256 `c9264cf5…af b5d` (full value above) or an immutable, independently accepted original-card capture traceable to that exact document; visually inspect both cards and their respective preparation sequences. Record document/card/page/hash and precise pre-blanch input form. If unavailable, close this pair as evidence-insufficient and seek **separate user-approved** source/fixture/data-strategy change; do not run open-ended similarity scans.

A future form YES only authorizes *further reviewed evidence work*: source-published compatible intermediate stage, same-session or safe hold, exact structured Decimal allocation, documented net saved actions, plus separate pre-implementation publication/read-path contract. It does **not** unblock PR10 runtime by itself.

## Scope and verification

Docs/evidence only. No production RecipeVersion/RecipeStep append, shared-stage registry, migration, Prep runtime, Pantry mutation, PDF, AI/Retail, or Gate2 closure. GitHub connector source manifests and #208 were inspected; external PDF **was not byte-verified**. No full backend regression is claimed or required for byte-identical runtime. Independent source review and docs CI are required before merge.
