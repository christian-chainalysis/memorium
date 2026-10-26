---
name: papercut
description: Silently log a paper cut, one small piece of friction, the moment it happens, so the weekly worklog can group and fix the root cause. Use when you hit a dead end, stale or missing docs, a skill that does the wrong thing, a setup snag, a flaky check, or when the user corrects you. Also use when the user types /papercut or says "papercut: ...".
---

# Papercut

Log friction the moment it happens. Do not fix it now, and do not tell the user unless they asked. One line in a file, then go back to the task.

The weekly `worklog` run reads the week's cuts, groups them, counts them, and looks for the cause one level up. Ten cuts that look different can share one fix. A fix made the moment a cut happens only patches that one cut.

## Log a cut

Run the script next to this file:

```sh
python3 <this skill>/scripts/papercut.py log <category> "<what happened>" [--skill <name>] [--fix-hint "<where a fix might go>"]
```

- **What happened:** one or two plain sentences. Name the file, command, doc, or skill, and what was wrong with it. Write it so someone with no context can find it again.
- **--skill:** the skill you were following, if any.
- **--fix-hint:** optional. Where a fix might live, such as a repo's AGENTS.md, a skill, global agent rules, or the app code. A guess is fine. The weekly pass decides.
- The script records the time, folder, repo, branch, and harness itself.

## Categories

| Category | When |
| --- | --- |
| `correction` | The user corrected you or had to repeat an instruction. Log every one. These are the strongest signal. |
| `stale-docs` | A doc, AGENTS.md, README, or skill said something no longer true. |
| `missing-docs` | You had to work out something a doc should have said. |
| `skill-gap` | A skill did the wrong thing, skipped a step, or had no step for this case. |
| `dead-end` | A command or approach failed and you had to back out. |
| `setup` | Env vars, ports, worktrees, installs, or auth got in the way. |
| `flaky` | A test, CI job, or service failed for reasons outside the change. |
| `slow` | Something worked but took far longer than it should. |
| `agent-mistake` | You made an error that you or the user caught. |
| `other` | Anything else worth counting. |

## Rules

1. Log every hit, even the same cut twice in one session. Repeats are the count. The weekly pass dedupes.
2. Log your own mistakes and the user's corrections. They are easy to skip and they matter most.
3. Never put a secret, token, customer data, or private personal news in a cut. The script refuses text that looks like a key.
4. Do not stop to fix a cut unless it blocks the user's task. If it blocks, work around it, log it, and say so in one line.
5. When the user says "papercut: <text>", log it with their words and category `correction` or the best fit, then reply "logged".

## Read the week

- `papercut.py summary` shows counts by category, skill, repo, and harness for this week.
- `papercut.py list --week 2026-W44` prints every cut for one week.

The files live in the vault at `_meta/papercuts/<YYYY-Www>.jsonl`, one JSON object per line.
