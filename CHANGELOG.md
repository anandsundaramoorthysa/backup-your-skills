# Changelog

All notable changes are listed here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-11-07

### Added
- `backup-your-skills` skill with `skillvault.py` (discover, backup, status, restore).
- User-level and project-level skill support for Claude Code; plugin skills are listed, not copied.
- Secret scan before backup; `--allow-secrets`, `--prune` and `--overwrite` opt-ins.
- Round-trip test, CI on Windows, macOS and Linux.
