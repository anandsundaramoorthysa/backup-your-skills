# Changelog

All notable changes are listed here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-11-14

### Security
- Credential files (`.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa*`, `.npmrc`, `.netrc`, `.pypirc`, `credentials.json`, keystores) are no longer copied, hashed or scanned. Templates such as `.env.example` are kept. Backup output lists them under `credential_files_not_copied`.
- The secret scan now catches unquoted `NAME_KEY=value` lines and `sk_`/`rk_`/`pk_` style keys. Previously a `.env` holding an unquoted `sk_...` key was copied and not flagged.
- Added a regression test for this case.

## [0.1.0] - 2026-11-07

### Added
- `backup-your-skills` skill with `skillvault.py` (discover, backup, status, restore).
- User-level and project-level skill support for Claude Code; plugin skills are listed, not copied.
- Secret scan before backup; `--allow-secrets`, `--prune` and `--overwrite` opt-ins.
- Round-trip test, CI on Windows, macOS and Linux.
