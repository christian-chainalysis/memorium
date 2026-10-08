---
name: worklog
description: Turn agent sessions and GitHub PRs into weekly work log notes and saved findings in your Obsidian vault at ~/notes. Use when the user types /worklog or asks to log, update, catch up, or backfill the work log.
disable-model-invocation: true
---

# Worklog

Read every agent session in a window and pull out two things: what the user got done, and what the sessions show about the user. Show a plan, let the user edit it, then write weekly notes and save the raw findings. Follow the rules in `~/notes/AGENTS.md`. Read `~/notes/_meta/profile.md` first: it names the user, their role, the harnesses they use, their efforts, and which optional sources are on.

Reading sessions costs the most, so each session gets read once and every finding gets saved. A later audit reads `_meta/findings/`, never the sessions again.

Weekly notes tell the story of pieces. **Efforts** tell the story of long projects, such as building a design system or launching a product. An effort is a project that spans many weeks and many PRs. Every work finding names its effort, so effort notes in `Projects/` grow a timeline across the year. New efforts show up when the same theme keeps coming back.

The script `scripts/sessions.py` (next to this file) reads every source. Run it with `python3`.

| Source | What it holds |
| --- | --- |
| `opencode`, `pi`, `claude` | Full transcripts: prompts, replies, tool calls, and errors. Only the harnesses listed in `profile.md` matter. To add another harness, see the header of `sessions.py`. |
| `claude-history` | Claude Code prompts only. The transcripts expired, so infer the work from what the user asked, pasted, and corrected. |
| GitHub PRs | The most complete record. Some weeks have PRs but no sessions. |
| Confluence (optional) | On when `profile.md` sets `confluence_site`. Pages the user created or edited in the window, with their edit counts. `scripts/confluence.py list --since <start> --until <end>`, then `dump <id> --out <tmpdir>/confluence` for each page they created or edited substantially. |
| Jira (optional) | Off unless the user asks. Issues they created, were assigned, or resolved in the window, through `/rest/api/3/search/jql` with JQL like `assignee = currentUser() AND resolved >= <start>`, using the same Keychain token. |
| Meeting notes | `~/notes/Meetings/*/`, one note per meeting. Read the notes dated in the window, and link them from the week note. |
| Claude Code memory | Notes Claude Code saved about the user's repos, decisions, and feedback, if they use Claude Code. Run `sessions.py memory --since <start>` for the paths. |

## 1. Pick the window

Run `sessions.py checkpoint`. It prints the last run time, or `none`.

- **Regular run:** by default the user runs this on Mondays (see `profile.md` for their cadence). The window is the previous full ISO week: Monday 00:00 through Sunday 23:59, local time. Never include today, even if the user worked this morning. If the checkpoint is older than that Monday, start at the checkpoint, so no week is skipped. Set the checkpoint to the Monday that starts this week.
- **Backfill:** when the user asks to backfill or catch up, or the checkpoint says `none`, ask which month to process. Work one calendar month per run, oldest first. Each run writes only that month's weeks. A backfill run saves the checkpoint only when its window reaches the present.

Save the window end before listing, so the checkpoint matches the window exactly.

`scripts/gather.sh <start> <end> <stats label> <tmpdir>` runs steps 1 to 5 and step 2 of Dump below, then writes subagent batches to `<tmpdir>/batch-N.txt`. Use it. The steps it runs:

1. `sessions.py list --since <start> --until <end>`
2. PRs the user wrote that were created, merged, or updated in the window. Run `gh search prs --author=@me` three times, with `--created=`, `--merged-at=`, and `--updated=` set to `<start date>..<end date>`. Use `--json number,title,url,state,repository,author,createdAt,closedAt --limit 200`, then merge and dedupe by repo and number. Searching by created date alone misses PRs opened before the window.
3. PRs the user reviewed, using the same three searches with `--reviewed-by=@me`.
4. `sessions.py memory --since <start>`
5. `scripts/confluence.py list --since <start date> --until <end date>` for Confluence pages, when on.
6. `sessions.py stats --since <start> --until <end> --out ~/notes/_meta/stats/<label>.json`, where the label is `YYYY-Www` for one week or `YYYY-MM` for a month.
7. **Seed lists**, so parallel subagents use the same names:
   - Efforts: the `effort` values in the frontmatter of `~/notes/Projects/*.md`.
   - Topics: short kebab-case slugs drawn from the PR titles, such as `checkout-redesign`. Add slugs used in earlier findings for the same work.
   - People: `~/notes/_meta/people.md`, which maps GitHub handles to names.
   - Known fixes: the friction fixes already shipped, listed in `~/notes/_meta/Worklog Changelog.md` and `~/notes/_meta/Fixes.md`.

Tell the user the counts for each source before you go on.

## 2. Dump the sessions

For each session, run `sessions.py dump <tool> <id> --since <start> --out <tmpdir>/dumps`.

## 3. Extract with one subagent per session

List the batch files with `ls <tmpdir>/batch-*.txt` and start exactly one subagent per file. Start them in parallel. When you split a window across subagents by month, cut on ISO week edges, so no two subagents write the same week. Give each dump over about 90 KB its own subagent. Pack smaller dumps into a single subagent, up to about 110 KB in total. Send PRs and memory files from weeks with no sessions to one more subagent. Give each subagent the file paths, the PR lists, the seed lists, and the brief in [EXTRACT.md](EXTRACT.md).

Each subagent writes its findings to `~/notes/_meta/findings/<YYYY-MM>/<tool>-<id>.md` and returns a short summary. These files are the single source of truth for the audit.

## 4. Build and show the plan

For a large window, have one subagent read every findings file, write the week notes directly, and draft the rest of the plan to `<tmpdir>/plan.md`. In each topic, list only the sessions that fed that topic. Before you show it, check that every PR's author and state comes from `gh`, and that facts agree across findings.

Merge work findings that share a topic. Group them by ISO week, using each work item's `date`. Show:

- each week note to create or update, with its topic headings and bullets
- **Efforts:** each effort that moved this window, in one line each. Flag a new effort when one theme shows up in three or more sessions or PRs across two or more weeks.
- achievement candidates, each marked with its size and effort (see EXTRACT.md)
- **How you work:** the three to five strongest patterns from the "about you" findings, each with evidence and a session count
- **Fix candidates:** open friction only, ranked by how often it came back and how cheap the fix is. Before you list one, check that it still happens: read the current repo docs, skill, or config it points at. On a backfill, friction from months ago is history, not a to-do. Show a fix candidate from an old window only if it also showed up in the last month, or you checked that it is still true today.
- **Fixed since:** one line per old friction that a known fix now covers, with the count of sessions it cost. This shows the payoff of each fix.
- **By the numbers:** six to ten stats from the stats file, compared with the running averages in `~/notes/About Me/By the Numbers.md`
- **Noticed:** the best cross-session patterns
- sessions dropped as `none`, one line each
- **Workflow changes:** problems with the findings themselves that should change this skill or EXTRACT.md
- **Open questions:** facts you could not confirm. Add them to `~/notes/Open Questions.md` under the right heading. Read that file first. Fold any answers the user wrote there (lines starting `A:`) into the notes, then delete those questions.

Wait for the user. They may drop, merge, reword, resize, or approve. When the user corrects a finding, fix it in the findings file too.

## 5. Write

For each week, write `~/notes/Work Log/YYYY-Www (Mon D).md`, where `Mon D` is that week's Monday, such as `2026-W41 (Oct 5).md`. Link it as `[[2026-W41 (Oct 5)]]`. If the user picked a different naming scheme at setup, `AGENTS.md` says so. Follow it. If the file exists, add to matching topic headings and append new ones. Never delete existing entries.

```markdown
---
created: 2026-10-06
tags: [worklog]
week: 2026-W41
title: "Week of Oct 5, 2026: checkout redesign ships, flaky tests"
efforts: ["[[Checkout]]"]
---
# Week of Oct 5, 2026: checkout redesign ships, flaky tests

## Checkout redesign
- Shipped the one-page checkout behind a flag, so users finish in one step. ([web PR #412](https://github.com/acme/web/pull/412))
- **Effort:** [[Checkout]]
- **Sessions:** `opencode -s ses_abc`, `pi --session 01a0ec95`
```

When Confluence is on, for each page the user created in the window, or edited 3 or more times, write or update a doc note in `~/notes/Docs/<clean title>.md` (kind, space, confluence URL, authored date, versions by them, efforts, Decision or Summary, Why, Status and impact, Links). Add it under a `## Docs` heading in the week note and in the effort note. Summarize, never paste the body.

Then update the notes that span weeks:

- **Efforts:** in each `~/notes/Projects/<Effort>.md` that moved, add one timeline line per week, with a link to the week note and the key PRs. Create the note when the user approves a new effort.
- **Achievements:** add each approved achievement to `~/notes/Achievements/<year>.md` under Major, Notable, or Mentoring and influence. Add to an existing entry for the same effort instead of starting a new one.
- **About me:** add each approved finding to the matching note in `~/notes/About Me/`. Patterns go in `How I Work.md`, one-line strengths in `Strengths.md`, and struggles in `Struggles.md`, each with a status (ongoing, improving, or resolved). Add new evidence to an existing entry instead of repeating it. Keep a count of sessions and weeks for each pattern.
- **Numbers:** append one row per week to the table in `~/notes/About Me/By the Numbers.md`, including the `work_time` buckets from the stats file (active hours for weekday core, early, evening, weekend, and the after-hours total). Refresh the When I work year-to-date table. Add any standout stat to its Highlights list.
- **People:** add new handle and name pairs to `~/notes/_meta/people.md`.
- **Home:** if a big win, a headline number, or an effort changed, update `~/notes/Home.md`. Keep it one screen long.
- **Fixes:** in `~/notes/_meta/Fixes.md`, add each fix the user ships for a friction, with its date and link. Raise the "sessions affected" count on fixes that showed up again in this run's older sessions.
- **Workflow changes:** for each change made to this skill, EXTRACT.md, `sessions.py`, or another skill because of this run, add a dated entry to `~/notes/_meta/Worklog Changelog.md`. Each entry says what changed, why, and which run found it.

## Optional notes

The vault ships with sensible defaults: About Me, Achievements, Projects, Kudos, Docs, Open Questions, and Home. If the user removed one at setup, skip its step. `AGENTS.md` lists what the user keeps.

## Meetings

Meeting transcripts go through the separate `meeting` skill. This skill only reads meeting notes already in `~/notes/Meetings/` for the window, and links them from the week note.

## 6. Save and commit

Commit early and often in `~/notes`. Make a small commit after each step that writes files: findings, each week note, each effort or About Me update. Use short messages such as `findings: 2025-12` or `worklog: 2025-W50`. Push after each few commits. Small commits mean no work is lost if a run stops.

1. Save the checkpoint with `sessions.py checkpoint --set <end>`, unless this is a backfill run that ends before the present.
2. Commit anything left, then push.
3. Delete the temp folder.

The run is done when every listed session and PR appears in the plan as a finding or as dropped, every findings file is saved, every note above is updated, and the push succeeded.
