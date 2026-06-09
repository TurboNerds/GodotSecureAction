# Security Policy

## Supported versions

Only the latest release of GodotSecureAction is actively maintained. Security
fixes are applied to the current release and the `v1` major tag — older
releases do not receive back-ported patches.

| Version | Supported |
|---------|-----------|
| Latest release / `v1` tag | ✅ |
| Older releases | ❌ |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**
Public issues are visible to everyone, including potential attackers, before a
fix is available.

Instead, use **GitHub's Private Vulnerability Reporting**:

1. Go to the [Security tab](https://github.com/emabrey/GodotSecureAction/security)
   of this repository.
2. Click **"Report a vulnerability"**.
3. Fill in the form with as much detail as you can provide (see below).
4. Submit — the report is visible only to repository maintainers.

GitHub's documentation on the process:
https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability

## What to include in your report

A useful report includes as many of the following as apply:

- **Summary** — a brief description of the issue and its potential impact.
- **Affected component** — which step, input, or workflow (`build.yml`,
  `release.yml`, `action.yml`, or the example) is involved.
- **Reproduction steps** — the minimal workflow configuration or input
  combination that triggers the issue.
- **Expected vs. actual behavior** — what should happen vs. what does happen.
- **Proof of concept** — a sample workflow, annotated job log, or test
  configuration if available. Limit any included encryption keys or tokens to
  obviously fake test values.
- **Suggested fix** — optional, but appreciated if you have one.
- **Your contact information** — if you would like to be credited in the
  security advisory.

You do not need to have a complete proof of concept to file a report. Partial
information is still useful and will be investigated.

## Response timeline

| Milestone | Target |
|-----------|--------|
| Initial acknowledgement | Within 5 business days |
| Triage and severity assessment | Within 10 business days |
| Fix or mitigation available | Depends on complexity; you will be kept informed |
| Public advisory published | After fix is released |

If you have not received an acknowledgement within 5 business days please
follow up on the same private report thread — do not open a public issue.

## Scope

Reports are in scope if they involve:

- The composite action definition (`action.yml`) and its bundled steps.
- The reusable workflows (`.github/workflows/build.yml`,
  `.github/workflows/release.yml`).
- **Secret handling** — including any scenario where an `encryption-key`,
  security token, or other secret could leak into job logs, the build cache,
  uploaded artifacts, the process argument list, or workflow outputs.
- **Workflow injection** — any path where untrusted input (e.g. a branch name,
  PR title, or action input) could be interpolated into a shell step and
  executed.
- Cache poisoning or artifact-tampering scenarios specific to this action's
  caching and upload steps.
- Pinning or supply-chain weaknesses in how this action invokes third-party
  actions.

Reports are **out of scope** if they describe:

- Vulnerabilities in the `godot_secure.py` script itself — report those to the
  [Godot-Secure repository](https://github.com/emabrey/Godot-Secure/security),
  which has its own security policy.
- The fundamental limitation of client-side encryption (a determined attacker
  with debugger access to the running exported game can always extract the key —
  this is documented and by design).
- Vulnerabilities in Godot Engine, mbedTLS, GitHub Actions runners, or any
  third-party action (report those to the respective upstream projects).
- Misconfiguration in a *consumer's* workflow that is not caused by a defect in
  this action (e.g. printing a secret in their own custom step).
- Theoretical attacks with no practical path to exploitation.

## Credits

Reporters who disclose vulnerabilities responsibly will be credited by name (or
handle) in the published GitHub Security Advisory for the issue, unless they
prefer to remain anonymous.
