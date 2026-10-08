# Vault

This is {{name}}'s private Obsidian vault, made with Memorium. Agents write most of the notes here, so follow these rules. `_meta/profile.md` says who {{name}} is: role, team, efforts, people, values, and which sources are on. Read it before you write anything.

## Start here

`Home.md` is the one-screen overview. `Open Questions.md` holds facts agents could not confirm, which {{name}} answers inline with `A: ...`.

## Folders

These are the sensible defaults. {{name}} can rename, drop, or add folders. When they do, update this table so the skills follow.

| Folder | What goes there |
| --- | --- |
| `Work Log/` | One note per ISO week, named `YYYY-Www (Mon D).md` with that week's Monday (for example `2026-W41 (Oct 5).md`). The H1 is a readable title, such as `# Week of Oct 5, 2026: ...`. Each topic gets a heading, with bullets for what was done, PR links, and session IDs. |
| `Achievements/` | One note per year, named `YYYY.md`, with Major, Notable, and Mentoring and influence sections. Add an entry only after {{name}} approves it. |
| `Projects/` | One note per effort, a project that spans many weeks. Each has an `effort` property, a `role` (leading, helping, or supporting), and a timeline that links to week notes. |
| `Meetings/` | One folder per recurring meeting, with one note per meeting named `YYYY-MM-DD.md`. Keep raw transcripts out. |
| `Topics/` | Private briefs about a subject, each with `Current State.md` and `Log.md`, kept current by the `topic` skill. `Topics/README.md` lists them. |
| `Docs/` | One note per doc {{name}} authored, such as a design doc or ADR: summary, decision, why, impact, links. Never the full body. |
| `Kudos/` | `Kudos.md` (praise, newest first) and `images/` (the screenshots, as proof). |
| `About Me/` | `How I Work.md` (patterns with evidence), `Strengths.md`, `Struggles.md` (each with a status), and `By the Numbers.md` (stats per week and highlights). |
| `Notes/` | Anything loose. |
| `_meta/` | `profile.md`, `people.md`, `Fixes.md`, `Worklog Changelog.md`, `findings/` (raw findings per session), and `stats/` (raw stats per run). Don't link to these from regular notes. |

If a note doesn't clearly fit, put it in `Notes/`. Ask before you create a new top-level folder.

## Quick captures

- **Kudos.** When {{name}} shares praise ("add to kudos") as a screenshot or text, save the image to `Kudos/images/YYYY-MM-DD-<name>.png`. Copy a pasted image from its temp path right away, before the OS deletes it. Then add an entry to the top of `Kudos/Kudos.md`: date, who said it, where, the exact words, the embedded image, and links to the effort and the week note. Never paraphrase the quote.
- **1:1 notes.** When {{name}} says "1:1 notes: ...", file it at `Meetings/1-1 <Name>/YYYY-MM-DD.md` with sections for Feedback, Goals, Decisions, and Follow-ups. Keep their words.

## Writing rules

- `Home.md` is about {{name}}. Describe what they built, led, and helped with. Credit teammates by name in effort notes, week notes, and achievements, not on Home.
- Link generously with `[[Note Name]]`, even when the target doesn't exist yet.
- Name notes in Title Case with plain words. Use dates in names only for week, meeting, and achievement notes.
- Start each note with YAML properties (`created`, `tags`, and links such as `efforts`).
- Follow {{name}}'s communication style in `_meta/profile.md`.

## Tools

- Prefer the Obsidian CLI (`obsidian help`) for search, backlinks, tags, and properties. The Obsidian app must be running.
- Plain file edits are fine when the app is closed.

## Git

- This vault is a private repo. Commit small and often, with short messages such as `worklog: 2026-W41`. Push after every few commits.
- Read a file in full before you rewrite it. Never read and write the same file in one shell command.
- Never commit secrets, tokens, or customer data.

## Memorium

The skills live in a clone of the Memorium kit and are linked into the agent skills folder. Personal details live only in this vault, never in the kit. When {{name}} improves a kit skill, the change goes in the kit clone, written generically. A skill that only fits {{name}} stays in their own skills folder.
