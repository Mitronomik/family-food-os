# Handoff

## Step 5 reviewed Russian reference table contract gate — 2026-09-22

Accepted main:
`aa5ebcb4c70c9adee0fd1242f520ef1298f6b167` (merged PR82).

Current branch:
`docs/step5-reviewed-russian-reference-table-contract`.

The user authorized Step 5. Under the repository Implementation Contract Gate
rule, current work is docs/preflight only.

Preflight source facts from the supplied corpus:

- source: `RU-NEEDS-MR-2.3.1.0253-21`;
- official PDF SHA-256:
  `cf96c7ea7fab087d16b478b2c8c097406d7572e495b2beb43405e4fd05917d79`;
- population-reference package: 147 groups / 218 source nutrient rows /
  872 claims / 735 scalar lookups / 137 withheld;
- source package itself is transport evidence, not runtime authorization.

Proposed first production table is intentionally only 50 adult micronutrient
rows:

- tables 11–13 men;
- tables 16–18 women;
- 25 exact V2 definition mappings per sex;
- source `Старше 18 лет` maps to completed age 19+;
- KFA-independent;
- no source null-sex coercion.

Important deferrals:

- tables 9/14 energy/macros: Far-North adjustment applicability is not represented
  by the current row model;
- tables 10/15 percent-energy/ranges: not current daily-amount comparison truth;
- Vitamin D and Calcium: source footnotes change >65 values and the corpus
  withholds those cells;
- folate/Vitamin K: no accepted exact target-definition mapping for this table;
- cobalt/silicon/vanadium: no V2 target;
- children and pregnancy/lactation: outside current selector/publication contract.

Read:
`docs/family-food/reviewed-russian-reference-table-contract.md`.

Do not publish numeric rows or start runtime until this gate is merged and the
user separately authorizes runtime Step 5.

