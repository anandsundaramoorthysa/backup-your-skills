# Security Policy

## Reporting a vulnerability

Please report privately through GitHub: **Security tab → "Report a vulnerability"** on this repository. Don't open a public issue.

Include what you found, steps to reproduce, and the impact. You'll get a first reply within about 7 days. This is a volunteer project, so fixes are best-effort.

## Scope

In scope: path traversal or unintended file overwrite or deletion in `skillvault.py`, secret-scan bypasses that push credentials, and unsafe handling of a malicious backup repo during restore.

Out of scope: secrets a user chooses to publish with `--allow-secrets`, and vulnerabilities in the skills a user backs up.

## Supported versions

Only the latest release.

## For users

Skills can contain API keys, tokens and personal paths. The secret scan is a safety net, not a guarantee. Keep your backup repo private unless you've reviewed everything in it.
