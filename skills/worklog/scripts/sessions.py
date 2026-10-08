#!/usr/bin/env python3
"""List and dump agent sessions for the worklog skill.

Sources:
  opencode        full transcripts from the OpenCode database
  pi              full transcripts from Pi session files
  claude          full transcripts from Claude Code project files
  claude-history  Claude Code prompts only (the user's side), kept after transcripts expire

Other harnesses (Codex, Cursor, Gemini CLI, Amp, and others) are not read yet. To add one, write a
<name>_list and <name>_dump pair that return the same shapes as pi_list and pi_dump, register them
in main(), and add the tool name to the dump choices. The bootstrap prompt walks you through it.

Commands:
  sessions.py list [--since ISO] [--until ISO] [--all]
  sessions.py dump <tool> <id> [--since ISO] [--out DIR]
  sessions.py memory [--since ISO]
  sessions.py stats --since ISO --until ISO [--out FILE]
  sessions.py checkpoint [--set ISO]
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
OPENCODE_DB = HOME / ".local/share/opencode/opencode.db"
PI_SESSIONS = HOME / ".pi/agent/sessions"
CLAUDE_PROJECTS = HOME / ".claude/projects"
CLAUDE_HISTORY = HOME / ".claude/history.jsonl"
VAULT = Path(os.environ.get("NOTES_VAULT", HOME / "notes"))
PROFILE = VAULT / "_meta/profile.md"


def profile():
    """Read simple `key: value` lines from the YAML front matter of _meta/profile.md."""
    out = {}
    if not PROFILE.exists():
        return out
    text = PROFILE.read_text()
    if text.startswith("---"):
        text = text.split("---", 2)[1]
    for line in text.splitlines():
        if ":" in line and not line.startswith((" ", "-", "#")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.split("#", 1)[0].strip().strip('"').strip("'")
    return out


def github_login():
    login = profile().get("github_login")
    if login:
        return login
    import subprocess
    r = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True)
    return r.stdout.strip()
CHECKPOINT = VAULT / "_meta/worklog-checkpoint.json"

# Sessions in these folders are scratch work or notes work, not project work.
SKIP_DIRS = ("/private/var/folders/", "/var/folders/", "/tmp/", str(VAULT))

TEXT_LIMIT = 4000
TOOL_INPUT_LIMIT = 300
TOOL_ERROR_LIMIT = 400


def parse_time(value):
    if value is None:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def to_ms(dt):
    return int(dt.timestamp() * 1000) if dt else None


def iso(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def clip(text, limit):
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + f" ...[{len(text) - limit} more chars]"


def skipped(cwd):
    return any(cwd.startswith(d) for d in SKIP_DIRS)


# ---------- OpenCode ----------

def opencode_conn():
    return sqlite3.connect(f"file:{OPENCODE_DB}?mode=ro", uri=True)


def opencode_list(since_ms, until_ms):
    if not OPENCODE_DB.exists():
        return []
    conn = opencode_conn()
    rows = conn.execute(
        """
        select s.id, s.directory, s.title, s.time_created, s.time_updated,
          (select count(*) from message m where m.session_id = s.id
             and json_extract(m.data, '$.role') = 'user'
             and m.time_created > ? and m.time_created <= ?) as user_msgs,
          (select json_extract(p.data, '$.text') from part p join message m on m.id = p.message_id
             where p.session_id = s.id and json_extract(m.data, '$.role') = 'user'
             and json_extract(p.data, '$.type') = 'text'
             and coalesce(json_extract(p.data, '$.synthetic'), 0) = 0
             order by m.time_created, p.id limit 1) as first_user
        from session s
        where s.parent_id is null and s.time_updated > ? and s.time_created <= ?
        order by s.time_updated
        """,
        (since_ms, until_ms, since_ms, until_ms),
    ).fetchall()
    return [
        {
            "tool": "opencode",
            "id": r[0],
            "cwd": r[1],
            "title": title_from(r[6]) if r[2].startswith("New session") and r[6] else r[2],
            "started": iso(r[3]),
            "updated": iso(r[4]),
            "user_messages": r[5],
            "resume": f"opencode -s {r[0]}",
        }
        for r in rows
    ]


def opencode_dump(session_id, since_ms):
    conn = opencode_conn()
    meta = conn.execute("select directory, title from session where id = ?", (session_id,)).fetchone()
    if not meta:
        sys.exit(f"opencode session not found: {session_id}")
    lines = [f"# {meta[1]}", f"tool: opencode", f"cwd: {meta[0]}", f"resume: opencode -s {session_id}", ""]
    rows = conn.execute(
        """
        select m.time_created, json_extract(m.data, '$.role'), p.data
        from part p join message m on m.id = p.message_id
        where p.session_id = ? and m.time_created > ?
        order by m.time_created, p.id
        """,
        (session_id, since_ms),
    ).fetchall()
    last_role = None
    for created, role, data in rows:
        part = json.loads(data)
        kind = part.get("type")
        if kind == "text":
            if part.get("synthetic"):
                continue
            if role != last_role or role == "user":
                lines.append(f"\n## {role.upper()} {iso(created)}")
                last_role = role
            lines.append(user_text(part.get("text", "")) if role == "user" else clip(part.get("text", ""), TEXT_LIMIT))
        elif kind == "tool":
            lines.append(format_tool(part.get("tool"), part.get("state", {}).get("input"),
                                     part.get("state", {}).get("status") == "error",
                                     part.get("state", {}).get("error"),
                                     part.get("state", {}).get("output") if part.get("tool") == "task" else None))
            last_role = "tool"
    return "\n".join(lines)


# ---------- Pi ----------

def pi_files():
    if not PI_SESSIONS.exists():
        return []
    return sorted(PI_SESSIONS.glob("*/*.jsonl"))


def pi_read(path):
    entries = []
    with open(path) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def pi_list(since_ms, until_ms):
    out = []
    for path in pi_files():
        if path.stat().st_mtime * 1000 <= since_ms:
            continue
        entries = pi_read(path)
        if not entries or entries[0].get("type") != "session":
            continue
        head = entries[0]
        times = [to_ms(parse_time(e["timestamp"])) for e in entries if e.get("timestamp")]
        started, updated = min(times), max(times)
        if updated <= since_ms or started > until_ms:
            continue
        user_msgs = [
            e for e in entries
            if e.get("type") == "message" and e["message"].get("role") == "user"
            and since_ms < to_ms(parse_time(e["timestamp"])) <= until_ms
        ]
        first_user = next((e for e in entries if e.get("type") == "message" and e["message"].get("role") == "user"), None)
        title = pi_text(first_user["message"]) if first_user else ""
        out.append({
            "tool": "pi",
            "id": head["id"],
            "cwd": head.get("cwd", ""),
            "title": title_from(title),
            "started": iso(started),
            "updated": iso(updated),
            "user_messages": len(user_msgs),
            "resume": f"pi --session {head['id'][:8]}",
            "path": str(path),
        })
    return out


def pi_text(message):
    content = message.get("content")
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if c.get("type") == "text")


def pi_find(session_id):
    for path in pi_files():
        if session_id in path.name:
            return path
    sys.exit(f"pi session not found: {session_id}")


def pi_dump(session_id, since_ms):
    path = pi_find(session_id)
    entries = pi_read(path)
    head = entries[0]
    lines = [f"tool: pi", f"cwd: {head.get('cwd')}", f"resume: pi --session {head['id'][:8]}", ""]
    errors = {}
    for e in entries:
        m = e.get("message", {})
        if e.get("type") == "message" and m.get("role") == "toolResult" and m.get("isError"):
            errors[m.get("toolCallId")] = pi_text(m)
    last_role = None
    for e in entries:
        if e.get("type") != "message" or to_ms(parse_time(e["timestamp"])) <= since_ms:
            continue
        m = e["message"]
        role = m.get("role")
        if role == "toolResult":
            continue
        content = m.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        for c in content or []:
            if c.get("type") == "text" and c.get("text", "").strip():
                if role != last_role or role == "user":
                    lines.append(f"\n## {role.upper()} {e['timestamp']}")
                    last_role = role
                lines.append(user_text(c["text"]) if role == "user" else clip(c["text"], TEXT_LIMIT))
            elif c.get("type") == "toolCall":
                err = errors.get(c.get("id"))
                lines.append(format_tool(c.get("name"), c.get("arguments"), err is not None, err, None))
                last_role = "tool"
    return "\n".join(lines)


# ---------- Claude Code transcripts ----------

def claude_files():
    if not CLAUDE_PROJECTS.exists():
        return []
    return sorted(CLAUDE_PROJECTS.glob("*/*.jsonl"))


def claude_user_text(content):
    """Return the user's typed text, or None for tool results and system injections."""
    if isinstance(content, str):
        text = content
    else:
        text = "\n".join(c.get("text", "") for c in content or [] if c.get("type") == "text")
    text = text.strip()
    if not text or text.startswith("<") or text.startswith("Caveat:"):
        return None
    return text


def claude_list(since_ms, until_ms):
    out = []
    for path in claude_files():
        if path.stat().st_mtime * 1000 <= since_ms:
            continue
        entries = [e for e in pi_read(path) if e.get("type") in ("user", "assistant") and not e.get("isSidechain")]
        if not entries:
            continue
        times = [to_ms(parse_time(e["timestamp"])) for e in entries if e.get("timestamp")]
        started, updated = min(times), max(times)
        if updated <= since_ms or started > until_ms:
            continue
        prompts = [
            (e, claude_user_text(e["message"].get("content"))) for e in entries
            if e["type"] == "user" and not e.get("isMeta")
        ]
        prompts = [(e, t) for e, t in prompts if t]
        in_window = [e for e, _ in prompts if since_ms < to_ms(parse_time(e["timestamp"])) <= until_ms]
        sid = path.stem
        out.append({
            "tool": "claude",
            "id": sid,
            "cwd": entries[0].get("cwd", ""),
            "title": title_from(prompts[0][1]) if prompts else "",
            "started": iso(started),
            "updated": iso(updated),
            "user_messages": len(in_window),
            "resume": f"claude --resume {sid}",
        })
    return out


def claude_dump(session_id, since_ms):
    path = next((p for p in claude_files() if p.stem.startswith(session_id)), None)
    if not path:
        sys.exit(f"claude session not found: {session_id}")
    entries = [e for e in pi_read(path) if e.get("type") in ("user", "assistant") and not e.get("isSidechain")]
    cwd = entries[0].get("cwd", "") if entries else ""
    lines = ["tool: claude", f"cwd: {cwd}", f"resume: claude --resume {path.stem}", ""]
    errors = {}
    for e in entries:
        content = e["message"].get("content")
        if e["type"] == "user" and isinstance(content, list):
            for c in content:
                if c.get("type") == "tool_result" and c.get("is_error"):
                    body = c.get("content")
                    errors[c.get("tool_use_id")] = body if isinstance(body, str) else json.dumps(body)
    last_role = None
    for e in entries:
        if not e.get("timestamp") or to_ms(parse_time(e["timestamp"])) <= since_ms:
            continue
        role = e["type"]
        content = e["message"].get("content")
        if role == "user":
            if e.get("isMeta"):
                continue
            text = claude_user_text(content)
            if text:
                lines.append(f"\n## USER {e['timestamp']}")
                lines.append(user_text(text))
                last_role = "user"
            continue
        for c in content if isinstance(content, list) else []:
            if c.get("type") == "text" and c.get("text", "").strip():
                if last_role != "assistant":
                    lines.append(f"\n## ASSISTANT {e['timestamp']}")
                    last_role = "assistant"
                lines.append(clip(c["text"], TEXT_LIMIT))
            elif c.get("type") == "tool_use":
                err = errors.get(c.get("id"))
                lines.append(format_tool(c.get("name"), c.get("input"), err is not None, err, None))
                last_role = "tool"
    return "\n".join(lines)


# ---------- Claude Code prompt history ----------

def claude_history():
    if not CLAUDE_HISTORY.exists():
        return {}
    sessions = {}
    with open(CLAUDE_HISTORY) as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = e.get("sessionId")
            if sid:
                sessions.setdefault(sid, []).append(e)
    return sessions


def history_text(e):
    """Expand pasted text placeholders, which the history file stores apart from the prompt."""
    text = e.get("display", "")
    for paste in (e.get("pastedContents") or {}).values():
        body = paste.get("content") if isinstance(paste, dict) else None
        if body:
            text += f"\n[pasted]\n{clip(body, 1500)}"
    return text


def claude_history_list(since_ms, until_ms, transcript_ids):
    out = []
    for sid, entries in claude_history().items():
        if sid in transcript_ids:
            continue
        times = [e["timestamp"] for e in entries]
        started, updated = min(times), max(times)
        if updated <= since_ms or started > until_ms:
            continue
        typed = [e for e in entries if not e.get("display", "").startswith("/")]
        in_window = [e for e in typed if since_ms < e["timestamp"] <= until_ms]
        out.append({
            "tool": "claude-history",
            "id": sid,
            "cwd": entries[0].get("project", ""),
            "title": title_from(typed[0]["display"]) if typed else "",
            "started": iso(started),
            "updated": iso(updated),
            "user_messages": len(in_window),
            "resume": f"claude session {sid[:8]} (prompts only, transcript expired)",
        })
    return out


def claude_history_dump(session_id, since_ms):
    match = [(sid, es) for sid, es in claude_history().items() if sid.startswith(session_id)]
    if not match:
        sys.exit(f"claude-history session not found: {session_id}")
    sid, entries = match[0]
    lines = [
        "tool: claude-history",
        f"cwd: {entries[0].get('project', '')}",
        f"resume: claude session {sid[:8]} (prompts only, transcript expired)",
        "",
        "This file holds only the user's prompts. The agent's replies and tool calls are gone.",
        "Infer what happened from what the user asked, pasted, and corrected.",
    ]
    for e in sorted(entries, key=lambda e: e["timestamp"]):
        if e["timestamp"] <= since_ms:
            continue
        lines.append(f"\n## USER {iso(e['timestamp'])}")
        lines.append(clip(history_text(e), TEXT_LIMIT))
    return "\n".join(lines)


# ---------- shared ----------

def title_from(text):
    text = (text or "").strip()
    if text.startswith("# ") and len(text) > 1500:
        return f"[skill: {text.splitlines()[0][2:]}]"
    return clip(text.replace("\n", " "), 100)


def user_text(text):
    """Shorten skill and command prompts, which arrive as long user messages that start with a heading."""
    text = text.strip()
    if text.startswith("# ") and len(text) > 1500:
        first = text.splitlines()[0]
        return f"[skill prompt: {first[2:]}]\n...{text[-600:]}"
    return clip(text, TEXT_LIMIT)


def format_tool(name, args, is_error, error, task_output):
    args = args or {}
    if isinstance(args, dict):
        for key in ("command", "filePath", "path", "pattern", "url", "description", "prompt"):
            if key in args:
                summary = f"{key}={args[key]}"
                break
        else:
            summary = json.dumps(args)
    else:
        summary = str(args)
    line = f"- tool {name}: {clip(summary.replace(chr(10), ' '), TOOL_INPUT_LIMIT)}"
    if is_error:
        line += f"\n  ERROR: {clip(str(error), TOOL_ERROR_LIMIT)}"
    if task_output:
        line += f"\n  SUBAGENT RESULT: {clip(task_output, TEXT_LIMIT)}"
    return line


# ---------- stats ----------

def user_times(since_ms, until_ms):
    """Yield (tool, cwd, ms) for every user prompt in the window, across all sources."""
    if OPENCODE_DB.exists():
        rows = opencode_conn().execute(
            """
            select s.directory, m.time_created from message m join session s on s.id = m.session_id
            where s.parent_id is null and json_extract(m.data, '$.role') = 'user'
              and m.time_created > ? and m.time_created <= ?
            """,
            (since_ms, until_ms),
        ).fetchall()
        for cwd, ms in rows:
            yield "opencode", cwd, ms
    for path in pi_files():
        if path.stat().st_mtime * 1000 <= since_ms:
            continue
        entries = pi_read(path)
        cwd = entries[0].get("cwd", "") if entries else ""
        for e in entries:
            if e.get("type") == "message" and e["message"].get("role") == "user":
                ms = to_ms(parse_time(e["timestamp"]))
                if since_ms < ms <= until_ms:
                    yield "pi", cwd, ms
    transcript_ids = set()
    for path in claude_files():
        transcript_ids.add(path.stem)
        if path.stat().st_mtime * 1000 <= since_ms:
            continue
        for e in pi_read(path):
            if e.get("type") == "user" and not e.get("isMeta") and not e.get("isSidechain") \
                    and claude_user_text(e["message"].get("content")):
                ms = to_ms(parse_time(e["timestamp"]))
                if since_ms < ms <= until_ms:
                    yield "claude", e.get("cwd", ""), ms
    for sid, entries in claude_history().items():
        if sid in transcript_ids:
            continue
        for e in entries:
            if not e.get("display", "").startswith("/") and since_ms < e["timestamp"] <= until_ms:
                yield "claude-history", e.get("project", ""), e["timestamp"]


def tool_counts(since_ms, until_ms):
    """Count tool calls and tool errors in full transcripts."""
    calls, errors, by_tool = 0, 0, {}
    if OPENCODE_DB.exists():
        rows = opencode_conn().execute(
            """
            select json_extract(data, '$.tool'), json_extract(data, '$.state.status'), count(*)
            from part where json_extract(data, '$.type') = 'tool' and time_created > ? and time_created <= ?
            group by 1, 2
            """,
            (since_ms, until_ms),
        ).fetchall()
        for tool, status, n in rows:
            calls += n
            by_tool[tool] = by_tool.get(tool, 0) + n
            if status == "error":
                errors += n
    for path in pi_files():
        if path.stat().st_mtime * 1000 <= since_ms:
            continue
        for e in pi_read(path):
            if e.get("type") != "message" or not (since_ms < to_ms(parse_time(e["timestamp"])) <= until_ms):
                continue
            m = e["message"]
            if m.get("role") == "assistant" and isinstance(m.get("content"), list):
                for c in m["content"]:
                    if c.get("type") == "toolCall":
                        calls += 1
                        by_tool[c.get("name")] = by_tool.get(c.get("name"), 0) + 1
            elif m.get("role") == "toolResult" and m.get("isError"):
                errors += 1
    return {"calls": calls, "errors": errors, "top_tools": dict(sorted(by_tool.items(), key=lambda kv: -kv[1])[:10])}


def gh_json(args):
    """Run gh and parse JSON. Wait and retry when GitHub's search rate limit hits."""
    import subprocess
    import time
    for attempt in range(4):
        result = subprocess.run(["gh", *args], capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout or "[]")
        if "rate limit" not in result.stderr:
            break
        time.sleep(30 * (attempt + 1))
    return {"error": result.stderr.strip()}


def gh_search(kind, start, end):
    """Search PRs in 2-week chunks, because GitHub search caps results per query."""
    import time
    from datetime import timedelta
    out, cursor = [], start
    while cursor < end:
        stop = min(cursor + timedelta(days=14), end)
        chunk = gh_json([
            "search", "prs", kind, f"--created={cursor.date()}..{(stop - timedelta(seconds=1)).date()}",
            "--json", "number,repository,author,state,createdAt,closedAt,commentsCount", "--limit", "1000",
        ])
        if isinstance(chunk, dict):
            return chunk
        out.extend(chunk)
        cursor = stop
        time.sleep(2)
    seen = {(p["repository"]["nameWithOwner"], p["number"]): p for p in out}
    return list(seen.values())


def median(values):
    values = sorted(values)
    return values[len(values) // 2] if values else None


def work_time(local):
    """Split activity into buckets by prompts, distinct active hours, and distinct days.

    An active hour is a clock hour with at least one prompt. It estimates time worked.
    """
    def bucket(d):
        if d.weekday() >= 5:
            return "weekend"
        if d.hour < 9:
            return "weekday_early"
        if d.hour >= 17:
            return "weekday_evening"
        return "weekday_core"

    names = ["weekday_core", "weekday_early", "weekday_evening", "weekend"]
    out = {n: {"prompts": 0, "hours": set(), "days": set()} for n in names}
    for d in local:
        b = out[bucket(d)]
        b["prompts"] += 1
        b["hours"].add((d.date(), d.hour))
        b["days"].add(d.date())
    total_prompts = len(local) or 1
    total_hours = len({(d.date(), d.hour) for d in local}) or 1
    result = {}
    for n in names:
        b = out[n]
        result[n] = {
            "prompts": b["prompts"],
            "prompt_share": round(b["prompts"] / total_prompts, 2),
            "hours": len(b["hours"]),
            "hour_share": round(len(b["hours"]) / total_hours, 2),
            "days": len(b["days"]),
        }
    after = ["weekday_early", "weekday_evening", "weekend"]
    result["after_hours"] = {
        "prompts": sum(result[n]["prompts"] for n in after),
        "hours": sum(result[n]["hours"] for n in after),
        "hour_share": round(sum(result[n]["hours"] for n in after) / total_hours, 2),
    }
    weekends = {d.date() - __import__("datetime").timedelta(days=d.weekday() - 5) for d in local if d.weekday() >= 5}
    result["weekend"]["weekends_worked"] = len(weekends)
    return result


def stats(since, until):
    s_ms, u_ms = to_ms(since), to_ms(until)
    prompts = [(t, c, ms) for t, c, ms in user_times(s_ms, u_ms) if not skipped(c)]
    local = [datetime.fromtimestamp(ms / 1000).astimezone() for _, _, ms in prompts]
    def by(keyf):
        counts = {}
        for p in prompts:
            counts[keyf(p)] = counts.get(keyf(p), 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))

    hours = sorted({(d.date(), d.hour) for d in local})
    days = sorted({d.date() for d in local})

    authored = gh_search("--author=@me", since, until)
    reviewed = gh_search("--reviewed-by=@me", since, until)
    gh = {}
    if isinstance(authored, list):
        merged = [p for p in authored if p["state"] == "merged"]
        merge_hours = [
            (parse_time(p["closedAt"]) - parse_time(p["createdAt"])).total_seconds() / 3600
            for p in merged if p.get("closedAt")
        ]
        repos = {}
        for p in authored:
            repos[p["repository"]["name"]] = repos.get(p["repository"]["name"], 0) + 1
        gh["authored"] = {
            "total": len(authored),
            "merged": len(merged),
            "by_repo": dict(sorted(repos.items(), key=lambda kv: -kv[1])),
            "median_hours_to_merge": round(median(merge_hours), 1) if merge_hours else None,
        }
    else:
        gh["authored"] = authored
    if isinstance(reviewed, list):
        me = github_login()
        others = [p for p in reviewed if p["author"]["login"] != me]
        bots = [p for p in others if p["author"]["login"].endswith("[bot]")]
        others = [p for p in others if not p["author"]["login"].endswith("[bot]")]
        authors = {}
        for p in others:
            authors[p["author"]["login"]] = authors.get(p["author"]["login"], 0) + 1
        gh["reviewed_for_others"] = {
            "total": len(others),
            "people": len(authors),
            "by_author": dict(sorted(authors.items(), key=lambda kv: -kv[1])),
        }
        gh["reviewed_bot_prs"] = len(bots)
        if isinstance(authored, list) and (len(authored) + len(others)):
            gh["review_share"] = round(len(others) / (len(authored) + len(others)), 2)
    else:
        gh["reviewed_for_others"] = reviewed

    return {
        "since": since.isoformat(),
        "until": until.isoformat(),
        "prompts": {
            "total": len(prompts),
            "by_source": by(lambda p: p[0]),
            "by_repo": by(lambda p: p[1].replace(str(HOME), "~")),
        },
        "active": {
            "days": len(days),
            "hours": len(hours),
            "by_hour_of_day": {h: sum(1 for d in local if d.hour == h) for h in range(24) if any(d.hour == h for d in local)},
            "by_weekday": {w: sum(1 for d in local if d.strftime("%a") == w) for w in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
            "after_hours_share": round(sum(1 for d in local if d.hour < 9 or d.hour >= 17 or d.weekday() >= 5) / len(local), 2) if local else None,
            "after_hours_rule": "before 9am, from 5pm, or weekend",
            "work_time": work_time(local),
        },
        "tools": tool_counts(s_ms, u_ms),
        "github": gh,
    }


def read_checkpoint():
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text()).get("last_run")
    return None


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--since", help="ISO time. Defaults to the checkpoint.")
    p_list.add_argument("--until", help="ISO time. Defaults to now.")
    p_list.add_argument("--all", action="store_true", help="Include skipped folders and sessions with no new user messages.")

    p_dump = sub.add_parser("dump")
    p_dump.add_argument("tool", choices=["opencode", "pi", "claude", "claude-history"])
    p_dump.add_argument("id")
    p_dump.add_argument("--since", help="Only messages after this ISO time.")
    p_dump.add_argument("--out", help="Write to DIR/<id>.md and print the path.")

    p_mem = sub.add_parser("memory")
    p_mem.add_argument("--since", help="Only files changed after this ISO time.")
    p_mem.add_argument("--until", help="Only files changed before this ISO time.")

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--since", required=True)
    p_stats.add_argument("--until", required=True)
    p_stats.add_argument("--out", help="Write JSON to this file and print the path.")

    p_cp = sub.add_parser("checkpoint")
    p_cp.add_argument("--set", help="ISO time to save. Use 'now' for the current time.")

    args = parser.parse_args()

    if args.cmd == "checkpoint":
        if args.set:
            value = datetime.now().astimezone().isoformat(timespec="seconds") if args.set == "now" else parse_time(args.set).isoformat()
            CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
            CHECKPOINT.write_text(json.dumps({"last_run": value}, indent=2) + "\n")
        print(read_checkpoint() or "none")
        return

    if args.cmd == "stats":
        result = json.dumps(stats(parse_time(args.since), parse_time(args.until)), indent=2, default=str)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(result + "\n")
            print(args.out)
        else:
            print(result)
        return

    if args.cmd == "memory":
        since_ms = to_ms(parse_time(args.since)) if args.since else 0
        until_ms = to_ms(parse_time(args.until)) if args.until else None
        files = [p for p in sorted(CLAUDE_PROJECTS.glob("*/memory/*.md"))
                 if p.stat().st_mtime * 1000 > since_ms and (until_ms is None or p.stat().st_mtime * 1000 <= until_ms)]
        print("\n".join(str(p) for p in files))
        return

    if args.cmd == "list":
        since = parse_time(args.since or read_checkpoint() or "1970-01-01T00:00:00Z")
        until = parse_time(args.until) if args.until else datetime.now().astimezone()
        s_ms, u_ms = to_ms(since), to_ms(until)
        transcripts = claude_list(s_ms, u_ms)
        all_claude_ids = {p.stem for p in claude_files()}
        sessions = (opencode_list(s_ms, u_ms) + pi_list(s_ms, u_ms) + transcripts
                    + claude_history_list(s_ms, u_ms, all_claude_ids))
        if not args.all:
            sessions = [s for s in sessions if not skipped(s["cwd"]) and s["user_messages"] > 0]
        sessions.sort(key=lambda s: s["updated"])
        print(json.dumps({"since": since.isoformat(), "until": until.isoformat(), "count": len(sessions), "sessions": sessions}, indent=2))
        return

    if args.cmd == "dump":
        since_ms = to_ms(parse_time(args.since)) if args.since else 0
        dumpers = {"opencode": opencode_dump, "pi": pi_dump, "claude": claude_dump, "claude-history": claude_history_dump}
        text = dumpers[args.tool](args.id, since_ms)
        if args.out:
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            path = out / f"{args.tool}-{args.id}.md"
            path.write_text(text)
            print(f"{path} ({len(text)} chars)")
        else:
            print(text)


if __name__ == "__main__":
    main()
