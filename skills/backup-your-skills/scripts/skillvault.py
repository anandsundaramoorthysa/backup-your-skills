#!/usr/bin/env python3
"""skillvault: back up, diff and restore agent skills into a plain folder (a git repo).

Stdlib only, cross-platform. Commands: discover, backup, status, restore.
All commands print JSON so an agent can read them.
"""
import argparse, datetime, hashlib, json, os, re, shutil, sys
from pathlib import Path

# Agent registry: add a new agent here, nothing else changes.
AGENTS = {
    "claude": {
        "home_env": "CLAUDE_CONFIG_DIR", "home_default": "~/.claude",
        "user_skills": "skills", "project_skills": ".claude/skills",
        "plugins_file": "plugins/installed_plugins.json",
    },
}
IGNORE = {".git", "__pycache__", ".DS_Store", "node_modules", ".venv"}
SKIP_SCAN = IGNORE | {"AppData", "Library", "Windows", "Program Files", ".cache", ".npm", "dist", "build"}
MANIFEST = "manifest.json"
SECRET_PATTERNS = {
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "AWS access key": r"\bAKIA[0-9A-Z]{16}\b",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",
    "Anthropic/OpenAI key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "Slack token": r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b",
    "generic secret": r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]",
}


def agent_home(agent):
    a = AGENTS[agent]
    return Path(os.environ.get(a["home_env"]) or os.path.expanduser(a["home_default"]))


def skill_hash(d):
    h = hashlib.sha256()
    for p in sorted(x for x in Path(d).rglob("*") if x.is_file() and not (set(x.parts) & IGNORE)):
        h.update(p.relative_to(d).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def skills_in(root):
    root = Path(root)
    if not root.is_dir():
        return []
    return sorted(d for d in root.iterdir() if (d / "SKILL.md").is_file())


def slug(path):
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(path).resolve().name) or "project"
    return base


def find_projects(roots, depth=4):
    """Find project dirs containing .claude/skills under the given roots."""
    found = []
    for r in roots:
        r = Path(r).expanduser().resolve()
        base = len(r.parts)
        for cur, dirs, _ in os.walk(r):
            dirs[:] = [d for d in dirs if d not in SKIP_SCAN and len(Path(cur, d).parts) - base <= depth]
            if Path(cur, ".claude", "skills").is_dir():
                found.append(Path(cur))
    return found


def discover(agent, projects):
    """Return local skills as {id: info}. id = user/<name> or project/<slug>/<name>."""
    out, a = {}, AGENTS[agent]
    for d in skills_in(agent_home(agent) / a["user_skills"]):
        out[f"user/{d.name}"] = dict(scope="user", name=d.name, path=str(d), project=None)
    used = {}
    for p in dict.fromkeys(Path(x).resolve() for x in projects):
        s = slug(p)
        used[s] = used.get(s, 0) + 1
        if used[s] > 1:  # same folder name in two places
            s = f"{s}-{used[s]}"
        for d in skills_in(p / a["project_skills"]):
            out[f"project/{s}/{d.name}"] = dict(scope="project", name=d.name, path=str(d), project=str(p), slug=s)
    for v in out.values():
        v["hash"] = skill_hash(v["path"])
    return out


def load_manifest(repo):
    f = Path(repo) / MANIFEST
    return json.loads(f.read_text("utf-8")) if f.exists() else {"version": 1, "skills": {}}


def repo_path(repo, sid):
    return Path(repo) / "skills" / sid


def scan_secrets(d):
    hits = []
    for p in Path(d).rglob("*"):
        if not p.is_file() or (set(p.parts) & IGNORE) or p.stat().st_size > 1_000_000:
            continue
        try:
            text = p.read_text("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, rx in SECRET_PATTERNS.items():
            for m in re.finditer(rx, text):
                hits.append(dict(file=str(p), line=text.count("\n", 0, m.start()) + 1, kind=label))
    return hits


def plugin_list(agent):
    f = agent_home(agent) / AGENTS[agent]["plugins_file"]
    try:
        data = json.loads(f.read_text("utf-8"))
    except (OSError, ValueError):
        return []
    plugins = data.get("plugins", data)
    return sorted(plugins) if isinstance(plugins, (dict, list)) else []


def select(ids, wanted):
    if wanted in (None, ["all"]):
        return list(ids)
    bad = [w for w in wanted if w not in ids]
    if bad:
        sys.exit(f"unknown skill id(s): {bad}")
    return wanted


def copy_skill(src, dst):
    if Path(dst).exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*IGNORE))


def cmd_discover(a):
    projects = [Path.cwd()] if a.cwd else []
    projects += [Path(p) for p in a.project] + find_projects(a.scan_root)
    found = discover(a.agent, projects)
    print(json.dumps(dict(agent=a.agent, skills=found, plugins=plugin_list(a.agent)), indent=2))


def cmd_status(a):
    projects = [Path(p) for p in a.project] + find_projects(a.scan_root) + ([Path.cwd()] if a.cwd else [])
    local, m = discover(a.agent, projects), load_manifest(a.repo)["skills"]
    res = dict(new=[], changed=[], unchanged=[], only_in_backup=[])
    for sid, v in local.items():
        res["new" if sid not in m else "unchanged" if m[sid]["hash"] == v["hash"] else "changed"].append(sid)
    res["only_in_backup"] = [s for s in m if s not in local]
    print(json.dumps(res, indent=2))


def cmd_backup(a):
    repo = Path(a.repo)
    projects = [Path(p) for p in a.project] + find_projects(a.scan_root) + ([Path.cwd()] if a.cwd else [])
    local = discover(a.agent, projects)
    m = load_manifest(repo)
    ids = select(local, a.select)
    blocked = {sid: scan_secrets(local[sid]["path"]) for sid in ids}
    blocked = {k: v for k, v in blocked.items() if v}
    if blocked and not a.allow_secrets:
        print(json.dumps(dict(ok=False, error="possible secrets found; fix or pass --allow-secrets", findings=blocked), indent=2))
        sys.exit(2)
    done = []
    for sid in ids:
        v = local[sid]
        if m["skills"].get(sid, {}).get("hash") == v["hash"]:
            continue
        copy_skill(v["path"], repo_path(repo, sid))
        m["skills"][sid] = dict(scope=v["scope"], name=v["name"], project=v["project"], hash=v["hash"],
                                backed_up_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
        done.append(sid)
    pruned = []
    if a.prune:
        for sid in [s for s in m["skills"] if s not in local]:
            shutil.rmtree(repo_path(repo, sid), ignore_errors=True)
            del m["skills"][sid]
            pruned.append(sid)
    m["plugins"] = plugin_list(a.agent)  # names only: reinstall these, don't copy them
    repo.mkdir(parents=True, exist_ok=True)
    ga = repo / ".gitattributes"  # keep skills byte-identical across OSes (no CRLF rewriting)
    if not ga.exists():
        ga.write_text("* -text\n", "utf-8")
    (repo / MANIFEST).write_text(json.dumps(m, indent=2), "utf-8")
    print(json.dumps(dict(ok=True, backed_up=done, pruned=pruned, secret_findings_ignored=blocked), indent=2))


def cmd_restore(a):
    repo, m = Path(a.repo), load_manifest(a.repo)["skills"]
    ids = select(m, a.select)
    res = dict(restored=[], skipped_exists=[], needs_project_path=[])
    for sid in ids:
        info, src = m[sid], repo_path(repo, sid)
        if info["scope"] == "user":
            dst = agent_home(a.agent) / AGENTS[a.agent]["user_skills"] / info["name"]
        else:
            proj = a.project_map.get(sid.split("/")[1]) if a.project_map else None
            proj = proj or (a.project_dir if a.project_dir else None)
            if not proj:
                res["needs_project_path"].append(sid)
                continue
            dst = Path(proj) / AGENTS[a.agent]["project_skills"] / info["name"]
        if dst.exists():
            if not a.overwrite:
                res["skipped_exists"].append(sid)
                continue
            shutil.move(str(dst), str(dst) + ".bak")  # never destroy what's there
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        res["restored"].append(sid)
    print(json.dumps(res, indent=2))


def main():
    p = argparse.ArgumentParser(prog="skillvault", description=__doc__)
    p.add_argument("--agent", default="claude", choices=AGENTS)
    sub = p.add_subparsers(dest="cmd", required=True)

    def scope_args(s):
        s.add_argument("--project", action="append", default=[], help="project dir (repeatable)")
        s.add_argument("--scan-root", action="append", default=[], help="folder to search for projects with .claude/skills")
        s.add_argument("--cwd", action="store_true", help="include current directory as a project")

    s = sub.add_parser("discover"); scope_args(s); s.set_defaults(f=cmd_discover)
    s = sub.add_parser("status"); s.add_argument("--repo", required=True); scope_args(s); s.set_defaults(f=cmd_status)
    s = sub.add_parser("backup"); s.add_argument("--repo", required=True); scope_args(s)
    s.add_argument("--select", nargs="+", help="skill ids, or 'all'")
    s.add_argument("--prune", action="store_true", help="remove from backup skills deleted locally")
    s.add_argument("--allow-secrets", action="store_true"); s.set_defaults(f=cmd_backup)
    s = sub.add_parser("restore"); s.add_argument("--repo", required=True)
    s.add_argument("--select", nargs="+", help="skill ids, or 'all'")
    s.add_argument("--project-dir", help="where to restore project-scope skills")
    s.add_argument("--project-map", type=lambda x: dict(kv.split("=", 1) for kv in x.split(";")),
                   help="slug=path;slug2=path2 for several projects")
    s.add_argument("--overwrite", action="store_true"); s.set_defaults(f=cmd_restore)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
