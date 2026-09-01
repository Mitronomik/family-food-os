# help/AGENTS.md

Scope: offline user help under `help/`.

User help rules:

- FamilyFoodOS is the current product. New or updated help must follow the
  current FamilyFoodOS canonical documents and the latest approved product
  decisions.
- Inherited CosmeticWorkshopOS help and workshop-domain terminology may remain
  until the owning bounded context is migrated. Their presence is legacy
  implementation context, not current FamilyFoodOS product identity; do not
  mechanically rewrite it into imaginary food-domain behavior.
- Write user help in Russian.
- Use short, step-by-step guidance.
- Avoid developer jargon, internal IDs, stack traces and implementation details.
- Explain what the user should do next, especially after warnings or errors.
- Help must work offline and must not depend on external websites.
- Do not include real client data or private notes in examples.
