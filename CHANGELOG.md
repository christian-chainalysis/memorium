# Changelog

Changes to the Memorium kit, newest first.

## Unreleased

- `worklog`: optional Publish skill updates step. When a run's fixes change a skill you share, it syncs the public skills repo, writes changelog bullets, pushes, reinstalls locally, and drafts a message for coworkers. Turn it on with `skills_source` and `published_skills` in `profile.md`.
- `topic`: topics can name any live source, not only a repo. A brief lists sources under `live:`, each a `repo` or a read-only `command` (such as an issue tracker CLI), with a `checked` marker and a `snapshot`. Chat and update read every source and report what changed. Old `repo:` fields still work.

## 0.1.0

- First release: `worklog`, `meeting`, and `topic` skills, the vault template, and the bootstrap prompt.
- Session readers for OpenCode, Pi, and Claude Code (transcripts and prompt history).
- Stats: prompts, active hours split into weekday core, early, evening, and weekend, PRs, time to merge, and reviews per person.
- Optional Confluence source.
