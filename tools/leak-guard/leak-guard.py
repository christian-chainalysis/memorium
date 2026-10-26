#!/usr/bin/env python3
"""Block private terms from reaching a public repo.

The term list lives outside the repo, so the list itself never goes public.
Default: ~/.config/leak-guard/terms.txt, or set LEAK_GUARD_TERMS.

Term file format, one term per line:
  word or phrase   matches as a whole word, ignoring case and accents
  ~fragment        matches anywhere, even inside a longer word
  !phrase          allowed: removed from a line before matching, such as your own
                   public account name when it contains a blocked word
  # comment        ignored
A line in the repo can opt out with the marker `leak-guard: allow` on the same line.

Commands:
  leak-guard.py push           pre-push hook mode. Reads refs from stdin and checks
                               every new commit's added lines, message, and author.
  leak-guard.py history        check every commit in the repo's history.
  leak-guard.py tree           check tracked and new files in the working tree.
  leak-guard.py install        install the pre-push hook in this repo.

Exit code 1 means a term was found. Matches print as file, line, and the term.
"""

import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ZERO = "0" * 40
ALLOW = "leak-guard: allow"


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).casefold()


def load_terms():
    path = Path(os.environ.get("LEAK_GUARD_TERMS", Path.home() / ".config/leak-guard/terms.txt"))
    if not path.exists():
        sys.exit(f"leak-guard: no term list at {path}. Refusing to push without one.")
    words, frags, allowed = [], [], []
    for raw in path.read_text().splitlines():
        t = raw.strip()
        if not t or t.startswith("#"):
            continue
        if t.startswith("!"):
            allowed.append(re.escape(norm(t[1:])))
        elif t.startswith("~"):
            frags.append(re.escape(norm(t[1:])))
        else:
            words.append(re.escape(norm(t)).replace(r"\ ", r"[\s_-]+"))
    if not words and not frags:
        sys.exit(f"leak-guard: {path} is empty. Refusing to push without terms.")
    parts = []
    if words:
        parts.append(r"(?<![\w])(?:" + "|".join(sorted(words, key=len, reverse=True)) + r")(?![\w])")
    if frags:
        parts.append("(?:" + "|".join(frags) + ")")
    allow = re.compile("|".join(sorted(allowed, key=len, reverse=True))) if allowed else None
    return Matcher(re.compile("|".join(parts)), allow)


class Matcher:
    def __init__(self, rx, allow):
        self.rx, self.allow = rx, allow

    def finditer(self, text):
        if self.allow:
            text = self.allow.sub(lambda m: " " * len(m.group(0)), text)
        return self.rx.finditer(text)


def git(*args, input=None):
    return subprocess.run(["git", *args], capture_output=True, text=True, input=input, check=True).stdout


def scan_text(rx, text, where, hits):
    for n, line in enumerate(text.splitlines(), 1):
        if ALLOW in line:
            continue
        for m in rx.finditer(norm(line)):
            hits.append(f"{where}:{n}: {m.group(0)!r}")


def scan_commit(rx, sha, hits):
    short = sha[:8]
    meta = git("show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", sha)
    scan_text(rx, meta, f"{short} message/author", hits)
    diff = git("show", "--format=", "--unified=0", "--no-color", "--no-renames", sha)
    current = "?"
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
            scan_text(rx, current, f"{short} path", hits)
        elif line.startswith("+") and not line.startswith("+++"):
            if ALLOW not in line:
                for m in rx.finditer(norm(line[1:])):
                    hits.append(f"{short} {current}: {m.group(0)!r}: {line[1:].strip()[:120]}")


def report(hits, what):
    if not hits:
        print(f"leak-guard: {what} clean.", file=sys.stderr)
        return 0
    print(f"leak-guard: {len(hits)} private term(s) found in {what}:", file=sys.stderr)
    for h in hits[:200]:
        print("  " + h, file=sys.stderr)
    if len(hits) > 200:
        print(f"  ... and {len(hits) - 200} more", file=sys.stderr)
    print("Remove them, or add `leak-guard: allow` on a line that is truly safe.", file=sys.stderr)
    return 1


def cmd_push():
    rx = load_terms()
    hits = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == ZERO:
            continue
        rng = [local_sha, "--not", "--remotes"] if remote_sha == ZERO else [f"{remote_sha}..{local_sha}"]
        for sha in git("rev-list", *rng).split():
            scan_commit(rx, sha, hits)
    return report(hits, "the commits being pushed")


def cmd_history():
    rx = load_terms()
    hits = []
    for sha in git("rev-list", "--all").split():
        scan_commit(rx, sha, hits)
    return report(hits, "the full history")


def cmd_tree():
    rx = load_terms()
    hits = []
    for f in git("ls-files", "--cached", "--others", "--exclude-standard").splitlines():
        p = Path(f)
        scan_text(rx, f, f"{f} (path)", hits)
        try:
            scan_text(rx, p.read_text(), f, hits)
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            pass
    return report(hits, "the working tree")


def cmd_install():
    hooks = Path(git("rev-parse", "--git-path", "hooks").strip())
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-push"
    if hook.exists() and "leak-guard" not in hook.read_text():
        sys.exit(f"leak-guard: {hook} exists and is not ours. Add `{Path(__file__).resolve()} push` to it by hand.")
    hook.write_text(f'#!/bin/sh\nexec python3 "{Path(__file__).resolve()}" push\n')
    hook.chmod(0o755)
    print(f"leak-guard: installed {hook}")
    return 0


def main():
    cmds = {"push": cmd_push, "history": cmd_history, "tree": cmd_tree, "install": cmd_install}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    sys.exit(cmds[sys.argv[1]]())


if __name__ == "__main__":
    main()
