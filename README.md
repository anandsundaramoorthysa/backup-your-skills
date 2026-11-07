# backup-your-skills

[![CI](https://github.com/anandsundaramoorthysa/backup-your-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/anandsundaramoorthysa/backup-your-skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An agent skill that backs up your skills to a GitHub repo, keeps that backup up to date, and reinstalls them anywhere.

- **Backs up** user-level skills, project-level skills and the custom skills you wrote. You choose which.
- **Updates**: months later, run it again. Only new or changed skills are copied and pushed.
- **Restores** on a new machine, for all skills or a pick. Existing skills are never overwritten unless you say so (old copy kept as `.bak`).
- **Safe**: scans for API keys and private keys before anything is pushed; you choose private or public.
- **Plugins**: marketplace plugin skills are not copied. Their names are saved so you can reinstall them.
- Cross-platform (Windows, macOS, Linux). Needs Python 3.9+ and git. No other dependencies.

## Install

Copy the skill folder into your skills directory:

```bash
git clone https://github.com/anandsundaramoorthysa/backup-your-skills
cp -r backup-your-skills/skills/backup-your-skills ~/.claude/skills/
```

(Windows PowerShell: `Copy-Item -Recurse backup-your-skills\skills\backup-your-skills $HOME\.claude\skills\`)

## Use

Tell your agent: "back up my skills", "sync my new skills to my backup repo", or "restore my skills from <repo url>". The agent asks what to include and where, then does the rest.

You can also run the script directly:

```bash
python skills/backup-your-skills/scripts/skillvault.py discover --cwd
python skills/backup-your-skills/scripts/skillvault.py backup --repo ~/skills-backup --select all --cwd
python skills/backup-your-skills/scripts/skillvault.py status --repo ~/skills-backup --cwd
python skills/backup-your-skills/scripts/skillvault.py restore --repo ~/skills-backup --select all --project-dir ~/code/app
```

Flags: `--project DIR` (repeatable), `--scan-root DIR` (search a tree for projects), `--prune`, `--overwrite`, `--allow-secrets`.

## Backup repo layout

```
skills/user/<name>/                 user-level skills
skills/project/<project>/<name>/    project-level skills
manifest.json                       hashes, dates, plugin names
```

## Support for other agents

Skills use the open [Agent Skills](https://agentskills.io/specification) format. Claude Code is supported today; to add another agent, add its paths to the `AGENTS` table in `skillvault.py` and send a PR.

## Test

```bash
python tests/test_skillvault.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: [SECURITY.md](SECURITY.md). Changes: [CHANGELOG.md](CHANGELOG.md).

## License

[MIT](LICENSE)
