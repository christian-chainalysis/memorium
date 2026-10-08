---
name: topic
description: Keep a private, living brief about a topic that has a repo plus meeting transcripts or docs, and chat about it. Use when the user types /topic, asks to update a topic, or wants to discuss one of their topics.
disable-model-invocation: true
---

# Topic

A topic is a private knowledge base for one subject. It combines three sources:

- **The repo**, read live. Never copy it into the vault.
- **Meeting notes** in `~/notes/Meetings/<Topic>/`.
- **A brief**, `~/notes/Topics/<Topic>/Current State.md`, which joins the two, plus `Log.md` with dated checkpoints.

The brief's frontmatter names the repo (`repo:`), the local path, and the last commit it was checked against (`repo_checked_at:`).

Everything stays in the vault. Never write to, branch, or push the topic's repo. Read only.

Newer sources win. When a meeting and the repo disagree, the repo wins on what is built, and the newest meeting wins on intent. Say so in the brief.

## Your topics

| Topic | Repo | Local path | Transcript drop folder |
| --- | --- | --- | --- |
Topics are listed in `~/notes/Topics/README.md`, one row each: topic, repo, local path, paths that matter, and transcript folder. Add a row when the user starts a new topic. A topic can have no repo.

## Always: get the latest repo first

1. `git -C <path> fetch origin`.
2. If the checkout is on the default branch with a clean tree, run `git pull --ff-only`. Otherwise leave the checkout alone, and read `origin/<default>` with `git show` and `git log origin/<default>`.
3. Note the new HEAD.

## Chat: `/topic <name>`

1. Get the latest repo.
2. Read `Current State.md` and the last few `Log.md` entries.
3. If HEAD moved since `repo_checked_at`, skim `git log <checked>..HEAD -- <repo_scope paths>` and the changed docs. Tell the user in 2 to 4 lines what changed. Don't update the brief unless they ask.
4. Answer questions from the brief, the meeting notes, and the repo. Cite the source for each claim: an ADR number, a file, or a meeting note. When the brief doesn't cover something, read the repo and say what you found.
5. If the brief has a **My model** section, check the user's statements against it and the code. When the user shows a new understanding or gets corrected, offer to add a row to My model with the old belief, the correction, and the date.

## Update: `/topic <name> update`

1. Get the latest repo.
2. **New transcripts:** check the drop folder, plus any path the user gives. Turn each new one into a meeting note with the `meeting` skill steps: clean the images, then write the note with Summary, Decisions, Architecture and plan, Who thinks what, the user's role, Open questions, and Action items. Skip notes that already exist.
3. **Repo changes since `repo_checked_at`:** new or changed ADRs (status changes count most), the decision log rows, plans, and big commits. Use subagents for large reads.
4. Show the user a short plan of what changes in the brief: new decisions, closed questions, overrides, and new open questions. Wait for an OK.
5. Rewrite `Current State.md` in place. Keep it current, not a history. Update `repo_checked_at`, `updated`, and `sources`.
6. Add a dated entry to the top of `Log.md` covering what changed, what got overridden, and the sources.
7. Update the matching effort note in `Projects/` only if the user's own role changed.
8. Commit small: one for the meeting notes, one for the brief and log. Push.

## New topic: `/topic new <name>`

Ask for the repo (or none), the local path, the paths that matter, the drop folder, and the user's angle (leading, helping, or learning). Create `Topics/<Name>/Current State.md` and `Log.md`, and `Meetings/<Name>/`. Add a row to `Topics/README.md`. Then run an update.

A good brief has: the topic in one paragraph, what's decided, what's open, how it works, who's involved, the user's role, open questions, and sources. When the user is learning the topic, add a **My model** section that records what they believed, what's true, and when that changed.
