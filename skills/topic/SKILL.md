---
name: topic
description: Keep a private, living brief about a topic built from live sources (a repo, an issue tracker, or any read-only command) plus meeting transcripts or docs, and chat about it. Use when the user types /topic, asks to update a topic, or wants to discuss one of their topics.
disable-model-invocation: true
---

# Topic

A topic is a private knowledge base for one subject. It combines three sources:

- **Live sources**, read fresh each time and never copied into the vault. A live source can be a repo, an issue tracker board, or anything else with a read-only command.
- **Meeting notes** in `~/notes/Meetings/<Topic>/`.
- **A brief**, `~/notes/Topics/<Topic>/Current State.md`, which joins the two, plus `Log.md` with dated checkpoints.

Newer sources win. When a meeting and a live source disagree, the live source wins on what exists, and the newest meeting wins on intent. Say so in the brief.

## Live sources

The brief's frontmatter lists its live sources under `live:`. Each entry says where to get the data and when it was last checked:

```yaml
live:
  - name: app repo
    kind: repo
    path: ~/code/app
    scope: [docs/adr, packages/core]
    checked: 86265a0
  - name: team board
    kind: command
    read: <read-only CLI command that prints the current state>
    checked: 2026-10-08
    snapshot: "165 items: 83 to do, 9 in progress, 73 done"
```

- **`repo`:** a git checkout. `checked` is the commit last read.
- **`command`:** any read-only CLI, such as an issue tracker, `gh`, or a docs tool. `read` is the exact command. `checked` is the date, and `snapshot` holds a short summary to compare against next time.
- **Read only.** Never run a command that creates, edits, moves, or deletes anything in a live source. Never write to, branch, or push a topic's repo.
- **No secrets.** Commands authenticate through their own login or env vars. Never put a token in the brief or the command.
- Older briefs use `repo:`, `repo_path:`, `repo_scope:`, and `repo_checked_at:`. Treat those as one `repo` source.

Topics are listed in `~/notes/Topics/README.md`, one row each: topic, live sources, and transcript folder. Add a row when the user starts a new topic. A topic can have no live source.

## Always: read the live sources first

For each `repo` source:

1. `git -C <path> fetch origin`.
2. If the checkout is on the default branch with a clean tree, run `git pull --ff-only`. Otherwise leave the checkout alone, and read `origin/<default>` with `git show` and `git log origin/<default>`.
3. Note the new HEAD.

For each `command` source, run `read` and any narrower read-only queries you need. Compare the result with `snapshot`.

If a source fails, for example when the login expired, say so and go on with the rest.

## Chat: `/topic <name>`

1. Read the live sources.
2. Read `Current State.md` and the last few `Log.md` entries.
3. Tell the user in 2 to 4 lines what changed since each source's `checked`. For a repo, skim `git log <checked>..HEAD -- <scope>` and the changed docs. For a command, compare with `snapshot`. Don't update the brief unless they ask.
4. Answer questions from the brief, the meeting notes, and the live sources. Cite the source for each claim: an ADR number, a file, an issue key, or a meeting note. When the brief doesn't cover something, read the source and say what you found.
5. If the brief has a **My model** section, check the user's statements against it and the sources. When the user shows a new understanding or gets corrected, offer to add a row to My model with the old belief, the correction, and the date.

## Update: `/topic <name> update`

1. Read the live sources.
2. **New transcripts:** check the drop folder, plus any path the user gives. Turn each new one into a meeting note with the `meeting` skill steps: clean the images, then write the note with Summary, Decisions, Architecture and plan, Who thinks what, the user's role, Open questions, and Action items. Skip notes that already exist.
3. **Live source changes since `checked`:** for a repo, new or changed ADRs (status changes count most), the decision log rows, plans, and big commits. For a command, new and closed items, status and owner changes, and anything that answers an open question. Use subagents for large reads.
4. Show the user a short plan of what changes in the brief: new decisions, closed questions, overrides, and new open questions. Wait for an OK.
5. Rewrite `Current State.md` in place. Keep it current, not a history. Update each source's `checked` (and `snapshot`), plus `updated` and `sources`.
6. Add a dated entry to the top of `Log.md` covering what changed, what got overridden, and the sources.
7. Update the matching effort note in `Projects/` only if the user's own role changed.
8. Commit small: one for the meeting notes, one for the brief and log. Push.

## New topic: `/topic new <name>`

Ask for the live sources (a repo with its path and the paths that matter, a read-only command, or none), the drop folder, and the user's angle (leading, helping, or learning). Run each command once to check it works before you save it. Create `Topics/<Name>/Current State.md` and `Log.md`, and `Meetings/<Name>/`. Add a row to `Topics/README.md`. Then run an update.

A good brief has: the topic in one paragraph, what's decided, what's open, how it works, who's involved, the user's role, open questions, and sources. When the user is learning the topic, add a **My model** section that records what they believed, what's true, and when that changed.
