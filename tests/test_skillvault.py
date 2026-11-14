"""Round-trip check: backup -> change -> status -> re-backup -> restore. Run: python tests/test_skillvault.py"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

S = Path(__file__).parent.parent / "skills/backup-your-skills/scripts/skillvault.py"


def run(*args, ok=0):
    r = subprocess.run([sys.executable, str(S), *args], capture_output=True, text=True, env=env)
    assert r.returncode == ok, r.stdout + r.stderr
    return json.loads(r.stdout)


def mk(base, name, body="hi"):
    d = Path(base, name); d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n---\n{body}")


with tempfile.TemporaryDirectory() as t:
    t = Path(t); home = t / "home"; proj = t / "app"; repo = t / "repo"
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(home)}
    mk(home / "skills", "alpha"); mk(proj / ".claude/skills", "beta")
    P = ["--project", str(proj)]

    assert set(run("discover", *P)["skills"]) == {"user/alpha", "project/app/beta"}
    assert run("backup", "--repo", str(repo), "--select", "all", *P)["backed_up"]
    assert (repo / ".gitattributes").read_text() == "* -text\n"
    assert sorted(run("status", "--repo", str(repo), *P)["unchanged"]) == ["project/app/beta", "user/alpha"]

    mk(home / "skills", "alpha", "changed"); mk(home / "skills", "gamma")
    st = run("status", "--repo", str(repo), *P)
    assert st["changed"] == ["user/alpha"] and st["new"] == ["user/gamma"]
    assert sorted(run("backup", "--repo", str(repo), "--select", "all", *P)["backed_up"]) == ["user/alpha", "user/gamma"]

    # secret scan blocks
    (home / "skills/gamma/x.md").write_text("key = 'AKIAABCDEFGHIJKLMNOP'")
    run("backup", "--repo", str(repo), "--select", "all", *P, ok=2)

    # regression: an unquoted `sk_` key in a .env must never be copied, and must be detected
    (home / "skills/gamma/x.md").unlink()
    fake = "sk_" + "a1b2c3d4" * 6
    (home / "skills/gamma/.env").write_text(f"SERVICE_API_KEY={fake}\n")
    (home / "skills/gamma/.env.example").write_text("SERVICE_API_KEY=\n")
    (home / "skills/gamma/notes.md").write_text(f"export SERVICE_API_KEY={fake}\n")
    run("backup", "--repo", str(repo), "--select", "all", *P, ok=2)               # env-style + sk_ pattern flag notes.md
    (home / "skills/gamma/notes.md").unlink()
    r = run("backup", "--repo", str(repo), "--select", "all", *P)
    assert not (repo / "skills/user/gamma/.env").exists(), ".env was copied"
    assert (repo / "skills/user/gamma/.env.example").exists()
    assert "user/gamma/.env" in r["credential_files_not_copied"]
    assert fake not in "".join(p.read_text(errors="ignore") for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts)

    # restore onto a fresh machine
    env["CLAUDE_CONFIG_DIR"] = str(t / "home2"); new = t / "app2"
    r = run("restore", "--repo", str(repo), "--select", "all", "--project-dir", str(new))
    assert len(r["restored"]) == 3 and (t / "home2/skills/alpha/SKILL.md").exists() and (new / ".claude/skills/beta/SKILL.md").exists()
    assert len(run("restore", "--repo", str(repo), "--select", "all", "--project-dir", str(new))["skipped_exists"]) == 3
print("ok")
