# FIC Nutrition Database — License Authority Receipt

**Status:** project source-authority receipt
**Reviewed for:** FamilyFoodOS Step 4 Russian nutrition publication
**Permission date:** 2026-09-10
**Evidence supplied by:** project owner
**Signed scans committed publicly:** no

## Licensed parties and object

Licensor identified in the supplied permission:

`ФГБУН «ФИЦ питания и биотехнологии»`.

Licensee:

`сервис FamilyFoodOS`.

Appendix №1 identifies the licensed electronic database:

`«Химический состав пищевых продуктов, используемых в Российской Федерации»`.

The appendix also lists a table of food/energy value of dishes/rations and other
data. Step 4 uses only the electronic food-composition database scope.

## Project-use scope recorded from the supplied permission

The permission supplied to the project grants FamilyFoodOS a non-exclusive use
right that includes, as relevant to Step 4:

- copying/reproduction and storage;
- use in paid/commercial services and applications;
- calculations and algorithms;
- inclusion in program code and a public repository, with source attribution;
- creation of derivative databases subject to the stated restrictions;
- worldwide territory;
- three-year term from the dated permission, subject to the original instrument.

The permission restricts sublicensing/transfer of the source database as a
standalone product without the additional conditions stated in the instrument.

This receipt is a project governance record of the supplied permission, not an
independent legal opinion.

## Required attribution

FamilyFoodOS must use the §7.1 wording from the supplied permission verbatim:

> Данные о химическом составе продуктов предоставлены ФГБУН «ФИЦ питания и биотехнологии» (база «Химический состав пищевых продуктов, используемых в Российской Федерации»).

Under §7.2 the public repository must also retain the source link in the relevant
README and/or header comments of published data files.

Runtime/data implementation must treat both the exact attribution string and the
source link as acceptance criteria, not optional documentation.

## Evidence hashes

The signed scan itself is not committed to the public repository.

User-supplied evidence hashes:

```text
main license image SHA-256:
98c6e1715141c60adbee4957442d41d664bc0fa54f3987164283e242f81ef4b5

Appendix №1 image SHA-256:
37c8b8f54edb8a292fa4d571989c05afdad777641bce0a4ea1ed80e060be0eb4
```

## Licensed electronic source used by Step 4

User-supplied corpus:

```text
FamilyFoodOS-corpus-0.3.0-2026-09-20.zip
SHA-256:
c0d90020798b2998e841328b9081f06f8197efda084b852aa8457fd41a5ce8ea
```

Pinned official FIC database snapshot inside that corpus:

```text
source_id: RU-NUT-DB
URL:
https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/1-1-baza-dannykh/1.1_baza%20dannih.html
captured_date: 2026-09-20
raw HTML SHA-256:
155107ddb381c14721c77fe995d604a5197982441446b54034e4d84645efbd6d
rows: 3216
```

The source registry in the corpus also identifies the official FIC database
section:

`https://ion.ru/nauka/baza-dannykh-khimicheskogo-sostava/`.

## Authority decision

For FamilyFoodOS project governance, the previous corpus status
`rights_use_unresolved` / repository
`BLOCKED_PENDING_RIGHTS_REVIEW` is superseded for the pinned RU-NUT-DB
electronic source by the later reviewed user-supplied license.

This receipt does not extend that grant to unrelated publications or silently
make Book2002 the licensed production numeric source.

Step 4 production provenance must point to RU-NUT-DB records and this authority
receipt.

Scientific field semantics, unit bindings, zero semantics and food-form mapping
remain separate data-quality gates.
