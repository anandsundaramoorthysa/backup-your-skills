# Contributing

Thanks for helping. This project is small on purpose: one skill, one stdlib-only Python script.

## Ground rules

- **No dependencies.** `skillvault.py` must run on a bare Python 3.9+ install, on Windows, macOS and Linux.
- **Never delete user data silently.** Anything that overwrites or removes files needs an explicit flag and, where possible, keeps a `.bak`.
- **Secrets stay out.** Don't weaken the secret scan. New patterns are welcome.
- Keep `SKILL.md` under 500 lines and follow the [Agent Skills spec](https://agentskills.io/specification).

## Setup and tests

```bash
git clone https://github.com/anandsundaramoorthysa/backup-your-skills
cd backup-your-skills
python tests/test_skillvault.py
```

Add a check to that file for any new behavior. The test uses temp folders and `CLAUDE_CONFIG_DIR`, so it never touches your real skills.

## Adding support for another agent

1. Verify, from the agent's official docs, where it keeps user-level and project-level skills.
2. Add an entry to the `AGENTS` table in `skillvault.py`, and link the docs in your PR.
3. Extend the test and the README's supported list.

## Pull requests

1. Open an issue first for anything bigger than a small fix.
2. Branch from `main`, keep the PR focused, and make sure CI passes.
3. Update `README.md` and `CHANGELOG.md` (under "Unreleased") when behavior changes.

## Reporting security problems

Don't open a public issue. See [SECURITY.md](SECURITY.md).

By contributing you agree your work is released under the [MIT License](LICENSE) and that you'll follow the [Code of Conduct](CODE_OF_CONDUCT.md).
