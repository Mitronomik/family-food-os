# FamilyFoodOS — Security Architecture & Secure-by-Design Contract

**Status:** canonical security architecture contract  
**Decision date:** 2026-09-13  
**Applies to:** API, persistence, Auth, imports, Retail, AI, hosted deployment, CI/CD and operations

## 1. Security objective

FamilyFoodOS must be secure by design and secure by default.

The project handles household data, children profiles, food restrictions,
future authentication/session data, imported external content, future Retail
credentials and optional AI. Security cannot be added after these boundaries
exist.

The goal is not to claim that the service is "unhackable". The goal is to make
security properties explicit, testable, least-privileged, observable and hard to
bypass accidentally.

The existing product architecture is retained. This document does **not**
authorize a NestJS/Prisma rewrite, Kubernetes, a separate optimizer service or
another re-platforming operation.

## 2. Governing security principles

1. **No implicit trust.** User input, browser input, uploaded files, URLs,
   Retail/API responses, webhooks, AI output and MCP/tool content are untrusted
   until validated for the specific boundary.
2. **Complete mediation.** Authorization and policy checks happen at every
   sensitive object/action boundary, not only in the UI or first request.
3. **Least privilege.** Services, tools, connectors and credentials receive only
   the permissions they require.
4. **Fail closed for safety/authorization.** Unknown hard food-safety or access
   state does not become permission.
5. **Secure by default.** Dangerous capabilities are disabled until explicitly
   enabled through an approved gate.
6. **Deterministic enforcement.** AI is never the authorization, money or
   food-safety enforcement layer.
7. **Data minimization.** Do not collect or transmit personal data merely because
   it might be useful later.
8. **Traceable changes.** Sensitive actions, policy changes and external side
   effects have bounded audit evidence without logging secrets or unnecessary PII.
9. **Graceful degradation.** AI, Retail, notifications or other external
   providers may fail without corrupting core state.
10. **Technology only by trigger.** Security is not a reason to introduce an
    unrelated infrastructure platform without evidence.

## 3. Security invariants

The following are mandatory architecture invariants.

### 3.1 External content is data, not instructions

Text from a recipe page, uploaded document, product description, Retail API,
MCP connector, webhook or another external source cannot change system policy,
permissions or tool definitions merely because it contains instruction-like
text.

### 3.2 AI has no direct critical privileges

An LLM/provider must not receive direct access to:

- production database writes;
- arbitrary SQL;
- shell / command execution;
- arbitrary filesystem access;
- cloud administration;
- general-purpose outbound HTTP;
- payment credentials;
- Retail master credentials;
- secrets manager contents.

AI output is proposal data and passes typed validation plus deterministic policy
before any state change.

### 3.3 Hard food-safety rules dominate probabilistic output

Allergens, hard exclusions, authoritative quantities, storage-safety rules and
other hard safety constraints are checked outside AI after any AI-assisted
transformation.

### 3.4 Household isolation is mandatory

Opaque UUIDs are not authorization.

Every household-owned read/write is Household-scoped. In shared deployment an
authenticated principal must also have an authorized HouseholdMembership/role.
Application authorization is primary; PostgreSQL RLS may be defense-in-depth but
never replaces application policy.

### 3.5 Financial action is always verified

If later Retail checkout exists:

```text
proposal
→ backend re-resolves SKU / availability / current price
→ authorization + limits / policy
→ final user-visible basket
→ explicit user confirmation
→ delegated retailer/payment action
```

The model never controls payment credentials and never supplies the authoritative
total.

## 4. Threat model

At minimum, threat reviews must consider the following.

| Threat | Example | Required architectural response |
|---|---|---|
| BOLA / cross-household access | guessed object ID reads another family's plan | object authorization on every access; tenant tests; household-scoped repositories |
| Broken authentication/session | stolen/weak session grants account access | managed OIDC/session design, phishing-resistant auth where available, secure cookies/tokens, re-auth for sensitive actions |
| Direct prompt injection | user asks AI to ignore policy and expose data | AI is not enforcement; minimal context; typed output; independent authorization/policy |
| Indirect prompt injection | recipe/product page contains hidden instructions | external content treated as untrusted data; no privilege inheritance; Tool Broker/policy checks |
| Excessive agency | model triggers damaging action chain | least functionality/permissions/autonomy; read-only first; explicit confirmation; bounded tools |
| Sensitive data disclosure | provider sees unrelated household/child data | context minimization, pseudonymous IDs, redaction, provider controls |
| SSRF | imported URL targets internal metadata/private network | isolated fetcher, scheme/DNS/IP validation, redirect revalidation, egress policy |
| Malicious file | archive/PDF exploits parser or exhausts resources | quarantine, type+magic checks, size/depth/time limits, malware scan/sandbox, safe representation |
| Unsafe third-party API consumption | malicious Retail payload changes core state | strict schemas, canonical mapping, bounds, normalization, unknown-field policy |
| OAuth/token theft | Retail or IdP refresh token stolen | encrypted/scoped storage, rotation/revocation, no model/client/log exposure |
| Webhook spoof/replay | fake order-status callback | signature verification, timestamp/nonce, replay window, idempotency |
| Injection/XSS | external/AI text reaches SQL/HTML/command context | parameterized DB access, contextual encoding, schemas; no raw AI output execution |
| Data/model poisoning | untrusted recipes/feedback become authoritative | provenance, trust levels, review/promotion gate, version/rollback, holdout tests |
| Resource/cost exhaustion | huge upload or repeated AI calls | authentication, quotas, rate/body limits, timeouts, budgets, circuit breakers |
| Supply-chain compromise | malicious dependency/build artifact | reviewed lockfiles, SCA, SBOM, provenance, signing, controlled release policy |
| Privileged account takeover | admin modifies catalogue/security | passkey/MFA, least role, short/step-up sessions, immutable audit trail |

Threat-model review is repeated when a new trust boundary is introduced, not only
once per project lifetime.

## 5. Current standards baseline

As of 2026-09-13 the security baseline should reference current stable primary
standards rather than copying a frozen tool stack from the external package.

### Application and API

- **OWASP ASVS 5.0.0** — application-security verification requirements:
  https://owasp.org/projects/asvs
- **OWASP API Security Top 10 2023** — especially BOLA, broken auth, resource
  consumption, SSRF and unsafe consumption of APIs:
  https://owasp.org/API-Security/editions/2023/en/0x11-t10/

### Authentication / authorization

- **RFC 9700 / BCP 240 — OAuth 2.0 Security Best Current Practice**:
  https://www.rfc-editor.org/info/rfc9700
- **RFC 10017 / BCP 212 — OAuth 2.0 for Browser-Based Applications**,
  published August 2026:
  https://www.rfc-editor.org/rfc/rfc10017.html
- **WebAuthn Level 3**, W3C Recommendation published 2026-08-25:
  https://www.w3.org/TR/webauthn-3/

### AI / LLM

- **OWASP Top 10 for LLM Applications 2025**:
  https://genai.owasp.org/llm-top-10/
- **OWASP LLMSVS v2** may be used as a verification checklist when runtime AI is
  actually introduced:
  https://owasp.org/www-project-llm-verification-standard/
- **NIST AI RMF Generative AI Profile (NIST AI 600-1)**:
  https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

### Secure development / supply chain

- **CISA Secure by Design** principles:
  https://www.cisa.gov/securebydesign
- **SLSA v1.2** Build requirements:
  https://slsa.dev/spec/v1.2/build-requirements
- **CycloneDX 1.7** is the current stable 1.x SBOM specification at this
  decision date; announced CycloneDX 2.0 is not adopted until stable and useful:
  https://cyclonedx.org/specification/overview/
- Sigstore/Cosign or an equivalent reviewed mechanism may be used for release
  artifact signing when the release pipeline reaches that gate.

Exact control IDs/tool versions must be re-verified before production rather
than copied indefinitely from this document.

## 6. Authentication and session baseline for shared deployment

Auth is introduced at the existing Shared Deployment gate, not prematurely into
local deterministic core work.

Preferred principles:

- use a managed or mature OIDC identity provider rather than creating a custom
  password protocol;
- prefer passkeys/WebAuthn for phishing-resistant authentication where product
  support allows it;
- follow RFC 9700 and RFC 10017 for browser OAuth/OIDC flows;
- authorization-code flow with PKCE; avoid deprecated implicit/password flows;
- exact redirect URI registration/validation;
- secure session cookies (`Secure`, `HttpOnly`, appropriate `SameSite`) when
  cookie sessions are used;
- CSRF protection for cookie-authenticated mutations;
- short/step-up authentication for privileged or high-impact changes;
- mandatory strong MFA/passkey for admin/support accounts;
- short-lived workload identities where possible instead of shared long-lived
  service secrets.

The exact IdP/session architecture remains an implementation decision of the
Auth milestone and must satisfy this contract.

## 7. Authorization model

Authentication answers who the principal is. It does not prove access to a
Household.

The shared-deployment path remains:

```text
authenticated principal
→ HouseholdMembership / role
→ action policy
→ household-scoped repository operation
→ optional database RLS second barrier
```

Every endpoint that receives a household-owned object ID needs an authorization
case and a negative cross-household test.

High-impact settings such as hard food exclusions, membership/role changes,
Retail connections and privacy controls must use protected application flows.
They must not be changed solely by an unverified conversational instruction.

## 8. Data classification and privacy

### Minimize collection

Prefer:

- age group when exact birth date is unnecessary;
- member alias when legal/full name is unnecessary;
- food restriction when a diagnosis is unnecessary;
- city/retail region rather than precise address when location precision is not
  needed.

### Children

Children's data is a higher-sensitivity class for product design:

- collect only fields required for planning/safety;
- guardian-managed profile;
- avoid unnecessary school/location/behavioral detail;
- do not send child identity to AI/provider when member ID or age group suffices.

### Separation and redaction

- separate identity/PII concerns from food-planning profiles where practical;
- analytics uses pseudonymous identifiers and excludes raw sensitive text;
- logs/traces must not contain access/refresh tokens, cookies, payment data,
  Authorization headers or full sensitive payloads;
- retention/export/delete behavior is a product requirement before production
  scale;
- backups are encrypted/access-controlled and restore is tested.

## 9. Importer / external content boundary

The Core API must not become a generic URL fetcher.

When arbitrary URL/file import is introduced, use an isolated boundary:

```text
URL/file
→ quarantine
→ scheme validation
→ DNS resolution + IP validation
→ private/link-local/metadata ranges blocked
→ redirect hop revalidation
→ time/size/content limits
→ MIME + magic-byte check
→ malware/safe-parser boundary
→ extraction
→ sanitization
→ versioned ImportArtifact
→ deterministic domain validation/review
```

The importer must not have production DB credentials, internal-network access or
unrelated secrets.

Archive nesting and decompressed-size limits are required against zip bombs.
Office/PDF parsing runs with bounded resources and no macro/executable authority.

The source-corpus importer introduced in PR #36 remains a controlled corpus tool;
future arbitrary user URL/file import must not silently reuse its trust level.

## 10. Retail connector security

Every provider is isolated behind the Retail anti-corruption layer.

Required principles when Retail appears:

- separate credentials per provider and environment;
- minimal OAuth scopes;
- encrypted refresh-token/credential storage;
- allowlisted outbound provider endpoints where operationally feasible;
- short timeout/retry budget with jitter only for appropriate idempotent calls;
- circuit breaker/bulkhead behavior so provider failure does not cascade;
- strict response schema/canonical mapping;
- external HTML/Markdown never rendered unsanitized;
- webhook signatures + timestamp/replay protection;
- idempotency for write-side external actions;
- current price/availability revalidation before basket/checkout;
- provider outage falls back to generic Shopping rather than failing Planning.

## 11. AI Gateway security

AI is added only after deterministic core value exists and the corresponding
roadmap gate is authorized.

### Gateway responsibilities

A future AI Gateway should centralize:

- task-specific context minimization / PII redaction;
- versioned prompt/policy registry;
- provider routing, timeout and budget;
- structured output schema validation;
- safety/confidence checks;
- model/provider version observability;
- deterministic fallback.

### Context rule

Do not send an entire household record when a task requires only a few fields.
Use pseudonymous `member_id` unless identity text is required for user-visible
output.

### Output rule

Model output is untrusted data. It cannot be directly inserted/executed as:

- SQL;
- shell;
- HTML;
- URL fetch authority;
- policy;
- price/quantity truth;
- tool permission;
- payment/order action.

## 12. Tool Broker / agentic capability

Agentic tools are a late security gate, not an MVP dependency.

The Tool Broker, when authorized, must:

- expose only allowlisted typed tools;
- separate read and write capabilities;
- reject unknown fields/actions;
- perform object authorization and business-policy checks independently of LLM;
- impose amount/item/frequency/resource limits;
- use short-lived scoped credentials/capabilities where possible;
- require explicit confirmation for financial, destructive, privacy or other
  high-impact actions;
- record an audit event for accepted high-impact actions.

Never expose a generic SQL console, shell, filesystem or unrestricted HTTP tool
to the model.

## 13. Secure software supply chain

Security controls should mature with deployment risk.

### Required before shared staging/production

- reviewed dependency lockfiles;
- automated secret scanning;
- dependency/SCA scanning;
- SAST appropriate to the language/runtime;
- migration tests;
- authorization/BOLA tests;
- reproducible container/release build process where containers are used;
- dependency-update policy;
- no production secret in repository, build logs or coding-agent prompts.

### Required before production release pipeline is considered mature

- SBOM generation (CycloneDX/SPDX acceptable after review);
- vulnerability scan of release artifacts/images;
- build provenance appropriate to the deployment platform, targeting at least
  a practical SLSA Build L2-equivalent property where supported;
- signed immutable release artifacts/images and deploy-by-digest when the chosen
  platform supports it;
- staging security/smoke/DAST checks appropriate to exposed surfaces;
- documented rollback/restore and periodic restore drill.

These controls are gates, not permission to introduce Kubernetes or a platform
team before the workload requires them.

## 14. API/application baseline

At public/shared deployment:

- HTTPS/TLS only;
- strict request schemas and body-size limits;
- parameterized DB operations;
- output encoding and no raw HTML from untrusted sources;
- rate/abuse limits based on measured flows;
- consistent non-leaking error model with request/trace ID;
- cursor pagination on large growing collections where relevant;
- idempotency keys for external side effects;
- optimistic concurrency/version checks for shared mutable plan/pantry state;
- no hidden public debug/admin endpoints;
- API inventory/version ownership documented.

## 15. Observability and audit

Telemetry must make incidents diagnosable without becoming a data-leak channel.

Useful technical signals include:

- request/trace ID;
- route/status/latency;
- DB/worker health;
- external provider latency/circuit state;
- authorization denials;
- rate-limit hits;
- invalid webhook signatures;
- SSRF blocks;
- AI schema/policy/tool-proposal rejects;
- security-sensitive admin/membership/consent changes.

Do not log secrets, session material, unnecessary PII or raw sensitive prompts.

## 16. Security gates aligned to the roadmap

### S0 — deterministic local/core work

Allowed:

- current FastAPI/SQLite deterministic core;
- platform catalogue work;
- Planner/Shopping/Prep without external privileged providers.

Required now:

- input validation;
- migration/transaction safety;
- household scoping;
- secret hygiene;
- dependency review;
- provenance and fail-closed authoritative-data behavior.

### S1 — shared deployment

Before multiple real households share deployment:

- PostgreSQL cutover;
- Auth;
- HouseholdMembership/authorization;
- tenant isolation tests;
- secure session/OIDC design;
- hosted secrets/backups/monitoring baseline.

### S2 — arbitrary external import

Before user URL/file import:

- sandbox/fetcher threat model;
- SSRF controls;
- file quarantine/type/size/resource controls;
- safe parser and review path.

### S3 — Retail read integration

Before live Retail:

- scoped provider credentials;
- provider adapter isolation;
- response validation;
- egress/timeout/retry/circuit controls;
- stale-data behavior.

### S4 — read-only AI

Allowed:

- parsing/classification/explanation with minimal context and structured output.

Forbidden:

- privileged tools;
- direct state writes from model output.

### S5 — AI proposed actions

AI may propose replace/replan/basket changes; backend recomputes and validates all
critical effects.

### S6 — controlled tools / commerce

Only after separate review:

- allowlisted Tool Broker;
- read-only tools first;
- scoped writes;
- policy/authorization/limits;
- explicit confirmation for high-impact actions;
- red-team/adversarial regression.

Autonomous payment remains outside the target architecture unless a later
explicit decision changes it.

## 17. Security verification strategy

Relevant changes require proportional security verification.

Examples:

- Household/API: cross-household BOLA and property-authorization cases;
- Auth: redirect/PKCE/session/CSRF/revocation negative cases;
- importer: private IP, DNS rebinding/redirect, malformed MIME, zip bomb and
  parser resource-limit corpus;
- webhooks: signature/replay/idempotency tests;
- Retail: malicious/malformed provider payloads and timeout/failure injection;
- AI: direct and indirect prompt injection, context-exfiltration attempts,
  poisoned recipe/product text, malformed structured output and tool-abuse cases;
- supply chain: secret/SCA/SBOM/signature/provenance checks at the applicable
  release gate.

Security controls are acceptance criteria when their trust boundary exists; they
are not optional cleanup after feature completion.

## 18. Operational security gaps are explicit work

Documentation alone does not make the repository secure.

Before shared/production use, operational repository/platform settings must also
be reviewed, including:

- protected `main` / repository ruleset;
- required review/check policy;
- least-privileged GitHub/app tokens;
- dependency-update policy;
- protected deployment environments;
- secret management;
- audit/recovery ownership.

These are tracked as real security work rather than assumed from the existence of
this document.

## 19. Technology admission

The external Household Food OS technical package is treated as reference, not a
replacement stack.

The following remain evidence-triggered rather than security defaults:

- separate optimizer microservice;
- Valkey/Redis;
- NATS/Kafka;
- Temporal;
- OpenFGA;
- Kubernetes;
- Go/Rust services;
- multi-provider AI routing.

Security should strengthen the existing architecture before adding operational
complexity.
