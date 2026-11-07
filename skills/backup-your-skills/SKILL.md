---
name: backup-your-skills
description: Back up, update and restore your agent skills (user-level, project-level and custom-made) to a GitHub repo. Use when the user wants to back up skills, sync new or changed skills to their backup repo, reinstall skills on a new machine, or migrate skills between machines.
license: MIT
compatibility: Needs Python 3.9+ and git. GitHub CLI (gh) is optional, used to create the repo.
---

# Backup Your Skills

Helper script: `${CLAUDE_SKILL_DIR}/scripts/skillvault.py` (stdlib Python, prints JSON). Call it as `python <path> <command>`; use `python3` if `python` is missing.

The backup repo layout is `skills/user/<name>/`, `skills/project/<project>/<name>/`, `manifest.json` (hashes, dates, plugin names). Plugin-installed skills are NOT copied; only their plugin names are saved in the manifest, so they can be reinstalled from their marketplace.

## Decide the mode

Ask the user which they want (skip if obvious): **backup / update**, **restore**, or **status**. Ask where the backup repo lives locally (default `~/skills-backup`) and whether an existing GitHub remote exists.

## Backup or update (same flow; the script only copies new or changed skills)

1. **Find project skills.** Ask: "Include project-level skills? Which folders should I search?" Pass `--project <dir>` for known projects (`--cwd` for the current one) or `--scan-root <dir>` to search a folder tree.
2. **Discover:** `skillvault.py discover [scope flags]`. Show the user the list grouped by user / project. Tell them plugin skills are excluded by design.
3. **Ask what to include** (AskUserQuestion, multi-select): everything, or pick skills. Custom skills they authored are in this list like any other.
4. **First time only, set up the repo:**
   - `git init <repo>`; ask **private or public** (no default, the user decides). Warn that skills can embed personal paths or keys.
   - With `gh`: `gh repo create <name> --private|--public --source <repo> --remote origin`. Without `gh`: ask the user to create an empty repo and give the URL, then `git remote add origin <url>`.
5. **Back up:** `skillvault.py backup --repo <repo> --select <ids|all> [scope flags]`.
   - Exit code 2 = possible secrets found. Show the findings (file, line, kind), and let the user fix them or explicitly accept. Only then rerun with `--allow-secrets`. Never add that flag on your own.
   - Add `--prune` only if the user wants skills they deleted locally to be removed from the backup.
6. **Publish:** `git -C <repo> add -A`, commit (message like `Backup skills: N new, M updated`), `git push -u origin HEAD`. If nothing changed, say so and skip the commit.

For later updates, run `skillvault.py status --repo <repo> [scope flags]` first and report `new`, `changed` and `only_in_backup`, then offer to back up the new and changed ones.

## Restore (new machine or reinstall)

1. Get the repo: `git clone <url> <repo>` (or `git -C <repo> pull` if it exists).
2. Read `<repo>/manifest.json`, and list skills for the user to choose from (all or a pick).
3. For project-level skills, ask where each project lives on this machine; use `--project-dir <dir>` for one project or `--project-map "slug=path;slug2=path2"` for several.
4. `skillvault.py restore --repo <repo> --select <ids|all> [...]`. Existing skills are skipped; if the user wants to replace them, rerun with `--overwrite` (old versions are kept as `<name>.bak`).
5. List `plugins` from the manifest and tell the user to reinstall them via `/plugin`.
6. Remind them to restart the session so the skills load.

## Rules

- Never push without the user having chosen the repo visibility.
- Never print file contents of skills with findings; report file, line and kind only.
- Config home is `~/.claude`, or `$CLAUDE_CONFIG_DIR` if set. Other agents are added in the `AGENTS` table of the script.
