#!/usr/bin/env python3
"""Log a paper cut: one small piece of friction, written the moment it happens.

Each cut is one JSON line in <vault>/_meta/papercuts/<YYYY-Www>.jsonl (ISO week, local time).
The vault is $NOTES_VAULT, or ~/notes. The worklog skill reads these files each week, then
groups, counts, and finds the root cause. Log every hit, even repeats. The count is the signal.

Commands:
  papercut.py log <category> "<what happened>" [--skill NAME] [--fix-hint TEXT] [--harness NAME]
  papercut.py list [--week YYYY-Www]      print that week's cuts (default: this week)
  papercut.py summary [--week YYYY-Www]   counts by category, skill, and repo
  papercut.py categories                  print the categories

Never put a secret in a paper cut. The script refuses text that looks like a key or token.
"""

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

CATEGORIES = {
    "correction": "The user corrected the agent, or had to repeat an instruction.",
    "stale-docs": "A doc, AGENTS.md, README, or skill said something that is no longer true.",
    "missing-docs": "The agent had to work out something a doc should have said.",
    "skill-gap": "A skill did the wrong thing, skipped a step, or has no step for this case.",
    "dead-end": "A tool call, command, or approach failed and the agent had to back out.",
    "setup": "Local setup, env vars, ports, worktrees, installs, or auth got in the way.",
    "flaky": "A test, CI job, or service failed for reasons outside the change.",
    "slow": "Something worked but took far longer than it should.",
    "agent-mistake": "The agent made an error it caught or the user caught.",
    "other": "Anything else worth counting.",
}

SECRET = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S{8,}|\b(sk|ghp|gho|xox[abp])[-_][A-Za-z0-9]{16,}|\bAKIA[0-9A-Z]{16}\b"
)


def vault():
    return Path(os.environ.get("NOTES_VAULT", Path.home() / "notes")).expanduser()


def week_label(d=None):
    y, w, _ = (d or dt.date.today()).isocalendar()
    return f"{y}-W{w:02d}"


def week_file(label):
    return vault() / "_meta/papercuts" / f"{label}.jsonl"


def repo_info(cwd):
    def git(*a):
        r = subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else ""

    root = git("rev-parse", "--show-toplevel")
    remote = git("remote", "get-url", "origin")
    name = re.sub(r"\.git$", "", remote.rstrip("/").split("/")[-1].split(":")[-1]) if remote else Path(root).name if root else ""
    return name, git("branch", "--show-current")


def guess_harness():
    env = os.environ
    if env.get("OPENCODE") or env.get("OPENCODE_SESSION_ID") or any(k.startswith("OPENCODE") for k in env):
        return "opencode"
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE_ENTRYPOINT"):
        return "claude-code"
    if any(k.startswith("PI_") for k in env):
        return "pi"
    return ""


def cmd_log(a):
    if a.category not in CATEGORIES:
        sys.exit(f"Unknown category {a.category!r}. Use one of: {', '.join(CATEGORIES)}")
    text = " ".join(a.detail).strip()
    if not text:
        sys.exit("Say what happened.")
    for field in (text, a.fix_hint or ""):
        if SECRET.search(field):
            sys.exit("That looks like it holds a secret. Describe the cut without it.")
    cwd = os.getcwd()
    repo, branch = repo_info(cwd)
    cut = {
        "ts": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "category": a.category,
        "detail": text[:1000],
        "skill": a.skill or "",
        "fix_hint": (a.fix_hint or "")[:300],
        "repo": repo,
        "branch": branch,
        "cwd": cwd.replace(str(Path.home()), "~"),
        "harness": a.harness or guess_harness(),
    }
    f = week_file(week_label())
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a") as fh:
        fh.write(json.dumps(cut, ensure_ascii=False) + "\n")
    print(f"logged to {f.name}")


def read(label):
    f = week_file(label)
    if not f.exists():
        return []
    out = []
    for line in f.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def cmd_list(a):
    for c in read(a.week or week_label()):
        extra = " ".join(x for x in (c.get("repo"), c.get("skill") and f"skill:{c['skill']}") if x)
        print(f"{c['ts'][:16]} {c['category']:<13} {extra:<28} {c['detail']}")


def cmd_summary(a):
    cuts = read(a.week or week_label())
    print(f"{len(cuts)} cuts in {a.week or week_label()}")
    for key in ("category", "skill", "repo", "harness"):
        counts = Counter(c.get(key) or "-" for c in cuts)
        print(f"\nby {key}:")
        for k, n in counts.most_common():
            print(f"  {n:>4}  {k}")


def cmd_categories(_):
    for k, v in CATEGORIES.items():
        print(f"{k:<14} {v}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log")
    lg.add_argument("category")
    lg.add_argument("detail", nargs="+")
    lg.add_argument("--skill")
    lg.add_argument("--fix-hint")
    lg.add_argument("--harness")
    for name in ("list", "summary"):
        s = sub.add_parser(name)
        s.add_argument("--week")
    sub.add_parser("categories")
    a = p.parse_args()
    {"log": cmd_log, "list": cmd_list, "summary": cmd_summary, "categories": cmd_categories}[a.cmd](a)


if __name__ == "__main__":
    main()
