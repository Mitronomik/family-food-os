# FamilyFoodOS — Security Tooling Plan

**Status:** implementation-planning companion to `security-architecture.md`
**Decision date:** 2026-09-13
**Principle:** add security controls by trust-boundary/risk trigger; do not create scanner/platform sprawl

## 1. Purpose

`security-architecture.md` defines the security properties FamilyFoodOS must
have. This document maps those properties to practical tooling candidates and
admission gates.

Tool names are not architecture truth. A tool may be replaced if another option
provides equal or better coverage with lower operational cost. Security
requirements remain even if a named tool changes.

No tool in this file is permission to re-platform the application.

## 2. Tooling principles

1. Prefer a small set of maintained tools with distinct coverage over multiple
   overlapping scanners that generate unowned alerts.
2. Prefer GitHub-native controls where they cover the need well and are available
   for the repository/account.
3. Pin/review CI actions and security-tool versions according to the project's
   dependency policy; do not run floating `latest` in production release paths.
4. A scanner is useful only if findings have an owner, severity policy and
   remediation workflow.
5. Security gates should be proportional: docs/local deterministic work should
   not wait for a production container-signing platform, while shared/public
   deployment must not ship without the controls appropriate to that exposure.
6. Never upload production secrets, real household data or sensitive corpora to
   an external scanner merely for convenience.

## 3. Repository / source control baseline

Before shared/public staging:

- protect `main` using a GitHub ruleset/branch protection appropriate to the
  repository plan;
- require pull requests rather than direct pushes;
- require the relevant test/security status checks;
- require human review for protected/security-sensitive paths where practical;
- restrict force pushes and deletion of protected branches;
- protect deployment environments and production credentials separately from CI.

**Current evidence at 2026-09-13:** the GitHub branch API reports `main` as
`protected: false`. This is a real operational gap and must be remediated before
shared/public production use. Documentation does not close that gap by itself.

## 4. Secret detection

### Preferred baseline

Use GitHub secret scanning/push protection when available to the repository.

### CI/local complementary candidate

**Gitleaks** is a suitable open-source candidate for repository/history/CI secret
scanning when a portable explicit check is useful.

Admission:

- before shared staging;
- earlier if external/provider credentials begin to exist.

Requirements:

- reviewed allowlist for known false positives;
- never suppress a finding solely to make CI green;
- rotate/revoke a real leaked credential rather than only deleting the text.

## 5. Static application security testing

### Preferred GitHub-native candidate

**CodeQL** is a strong fit for the current Python backend and the future
JavaScript/TypeScript PWA. GitHub documents CodeQL support for Python,
JavaScript/TypeScript and GitHub Actions workflows.

Start with the maintained default security queries. Consider `security-extended`
only after reviewing alert volume and ownership.

Admission:

- before shared/public staging;
- may be introduced earlier if CI cost/noise is acceptable.

### Optional targeted supplement

A targeted linter/scanner may be added only for a concrete gap not adequately
covered by CodeQL/current linters. Avoid duplicating every finding across three
SAST tools.

Primary reference:
https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-code-scanning

## 6. Dependency / SCA controls

For the current Python application:

- keep dependencies constrained/pinned under the repository's accepted policy;
- use GitHub dependency graph/Dependabot security alerts when available;
- use **pip-audit** or an equivalent Python Advisory Database-aware audit in CI
  when dependency scanning becomes a required gate.

For the future Next.js/TypeScript consumer app:

- use the ecosystem lockfile;
- enable Dependabot/security updates or an equivalent reviewed update mechanism;
- dependency updates do not bypass tests merely because they are security-labeled.

Admission:

- dependency inventory/audit before shared staging;
- blocking policy based on exploitable/relevant severity, with explicit handling
  for accepted temporary exceptions.

## 7. Container / filesystem / IaC scanning

When deployable images and IaC exist, **Trivy** is a practical candidate for a
single scanner covering image/filesystem vulnerabilities and common
misconfiguration/IaC checks.

Do not introduce container scanning before there is a release image to scan.

Admission:

- image scan before shared staging deployment;
- IaC scan when deployment IaC becomes authoritative.

## 8. SBOM

At production release maturity, generate an SBOM per release artifact/image.

Preferred formats:

- CycloneDX;
- SPDX.

Candidate generators include ecosystem-native CycloneDX tooling or **Syft**.
Choose one mechanism and make the output reproducible/versioned rather than
creating multiple divergent SBOMs.

Current standards baseline is owned by `security-architecture.md`; CycloneDX 1.7
is stable at this decision date.

## 9. Artifact signing and build provenance

When immutable production release artifacts/images exist:

- build in a controlled CI identity;
- record build provenance appropriate to the deployment platform;
- sign release artifacts/images;
- deploy by immutable digest when supported.

**Sigstore/Cosign** is a preferred candidate for container/release signing where
it fits the deployment platform.

Target a practical SLSA Build L2-equivalent property first; increase assurance
only when threat/risk justifies the operational cost.

## 10. Dynamic testing

When a public/shared staging endpoint exists, add a bounded DAST smoke/baseline
stage.

**OWASP ZAP** is a reasonable candidate for automated baseline checks against
staging.

Rules:

- never run destructive active scans against production by default;
- authenticate with dedicated non-production test principals where auth coverage
  is required;
- seed only synthetic household data;
- tune false positives transparently.

DAST complements, not replaces, API authorization/security tests.

## 11. API and authorization security tests

The highest-value tests for FamilyFoodOS are not generic scanners alone.

Repository tests must explicitly cover:

- cross-household read/write attempts;
- object-ID substitution/BOLA;
- role/membership revocation;
- CSRF/session cases when cookie-auth is introduced;
- concurrency/version conflicts for shared mutable state;
- idempotency for external write actions;
- error responses not leaking stack/secrets.

These are product-specific and remain required regardless of SAST/DAST output.

## 12. Importer security corpus

Before arbitrary URL/file import, maintain an adversarial test corpus for:

- loopback/private/link-local/metadata URLs;
- alternate IP encodings where relevant;
- redirect to forbidden address;
- DNS-rebinding-style resolution changes;
- oversized response;
- misleading MIME vs magic bytes;
- nested/oversized archives;
- malformed PDFs/office files;
- parser timeout/resource exhaustion;
- external text containing prompt-injection strings.

The purpose is to verify the sandbox boundary, not to ask AI whether a file is
safe.

## 13. AI / LLM security tests

Before runtime AI is enabled, maintain a golden/adversarial suite per AI task.

Read-only AI tests:

- structured-output schema pass/fail;
- PII/context minimization;
- direct prompt injection;
- indirect injection inside recipe/product/import text;
- context-exfiltration requests;
- provider timeout/invalid output fallback.

Tool-enabled AI additionally requires:

- unknown tool rejected;
- unknown/extra parameters rejected;
- cross-household object denied;
- policy/amount/frequency limits;
- side effect not executed without required confirmation;
- replay/idempotency behavior;
- malicious tool result cannot add authority.

OWASP LLM Top 10 and LLMSVS can guide the test catalogue, but FamilyFoodOS trust
boundaries remain the source of specific acceptance criteria.

## 14. Observability

Use vendor-neutral **OpenTelemetry** instrumentation when hosted production
telemetry is introduced.

Security-relevant structured signals include:

- authentication failures;
- authorization denies;
- rate-limit triggers;
- invalid webhook signatures;
- importer SSRF blocks;
- provider circuit opens;
- AI structured-output/policy/tool rejects;
- privileged setting/membership changes.

A redaction test must prove that Authorization headers, cookies/tokens and other
known sensitive fields do not reach normal telemetry.

## 15. Backup / restore / incident controls

Before shared deployment:

- automated database backups;
- documented recovery objective appropriate to the product stage;
- test restore into an isolated environment;
- leaked-secret revocation procedure;
- auth compromise/session invalidation procedure;
- provider outage/degraded-mode runbook;
- migration rollback/forward-fix strategy.

A backup that has never been restored is not sufficient evidence of recoverability.

## 16. Proposed admission sequence

```text
NOW / pre-shared work
  secret hygiene
  dependency inventory
  explicit authz/security tests for existing boundaries
  secure docs/contracts
  fix repository protection gap before shared/public use

SHARED STAGING
  branch/ruleset + required checks
  secret scanning
  CodeQL (Python; JS/TS when PWA exists)
  dependency/SCA audit
  migration/authz tests
  staging secrets isolation
  backup + restore proof

DEPLOYABLE IMAGES / IaC
  Trivy or equivalent image/IaC scan
  SBOM generation

PRODUCTION RELEASE MATURITY
  signed immutable artifacts/images
  build provenance
  deploy by digest
  DAST baseline against staging
  restore drills and incident runbooks

AI / RETAIL / IMPORTER
  add their dedicated threat-model gates and adversarial suites only when those
  boundaries are authorized
```

## 17. Non-goals

This plan does not authorize:

- migrating the application to another framework;
- Kubernetes solely to gain security controls;
- installing every listed tool immediately;
- scanning real household data through third-party SaaS without review;
- treating a green scanner dashboard as proof that the service is secure.

The goal is layered, testable risk reduction with clear ownership and minimal
unnecessary operational complexity.
