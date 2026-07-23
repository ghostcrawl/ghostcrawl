# Security Policy

## Scope

This policy covers the public GhostCrawl surface: the Python and Node SDKs, the CLI, and the
documentation. Backend and engine internals are handled privately by the operator and are out
of scope for community security reports.

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.** Public issues expose the vulnerability
to everyone before a fix is available, which puts all users at risk.

Instead, use one of the two private channels below:

### Option 1 — GitHub Private Security Advisory (preferred)

Use GitHub's built-in private reporting flow:

> **[Report a vulnerability](https://github.com/ghostcrawl/ghostcrawl/security/advisories/new)**

This opens a private draft advisory visible only to you and the maintainers. You can include a
description, affected versions, and any proof-of-concept details. GitHub keeps the conversation
private until a fix is ready and a CVE can be issued.

### Option 2 — Email

Send a report to **security@ghostcrawl.io** with:

- A description of the vulnerability and the affected component (SDK name + version, CLI version).
- Steps to reproduce or a proof-of-concept (even a rough outline is helpful).
- The potential impact as you see it.
- Your preferred way to be credited when the fix ships (or "no credit" if you prefer).

PGP-encrypted email is welcome; ask for the public key in your first message.

## Response SLA

We acknowledge every report **within 72 hours**. For valid vulnerabilities we aim to:

1. Confirm the issue and triage severity within 5 business days.
2. Ship a patch release and public disclosure within 30 days for critical/high severity; 90 days
   for medium/low.

If you have not heard back within 72 hours, please send a follow-up email to
security@ghostcrawl.io.

## Disclosure Policy

We follow coordinated disclosure. We ask that you:

- Give us reasonable time to investigate and patch before public disclosure.
- Avoid accessing, modifying, or deleting data that does not belong to you.
- Report only the vulnerability, not any lateral data you may encounter.

In return, we will work with you on timing and credit, and we will not pursue legal action for
good-faith security research conducted under this policy.
