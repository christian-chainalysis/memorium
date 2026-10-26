# Changelog

Changes to the Memorium kit, newest first.

## Unreleased

- `papercut`: new skill. Agents log friction the moment it happens, one JSON line per cut in `_meta/papercuts/<YYYY-Www>.jsonl`, repeats included. Ten categories, from `correction` to `flaky`. The script refuses text that looks like a secret.
- `worklog`: reads the week's paper cuts as the main friction source. The plan groups cuts by cause, names the layer and place for each fix, and counts friction the sessions show that no cut logged. Each week gets a `_meta/papercuts/<YYYY-Www>.md` summary.
- `worklog`: skills listed in `skills_private` in `profile.md` are never offered for publishing.
- `tools/leak-guard`: new pre-push hook for public repos. Blocks a private term list, ignoring case and accents, in added lines, paths, commit messages, and authors. Also scans full history and the working tree.

- `worklog`: Skill changes no longer drafts a message to paste. Set `skills_publish_auto: true` in `profile.md` to run `skills_publish` after each run without asking.
- `meeting` and `worklog`: when a person has no handle in `people.md`, follow its "Finding someone's handle" steps before writing the name alone. If the section is empty, ask the user once and save the answer. The vault template has the empty section.
- `worklog`: a Skill changes step. When a run's fixes change your agent skills, it lists them as plain bullets you can paste to the people who use them. Set `skills_source` in `profile.md` to read changes from git, and `skills_publish` to name your own command for sharing them.
- `topic`: topics can name any live source, not only a repo. A brief lists sources under `live:`, each a `repo` or a read-only `command` (such as an issue tracker CLI), with a `checked` marker and a `snapshot`. Chat and update read every source and report what changed. Old `repo:` fields still work.

## 0.1.0

- First release: `worklog`, `meeting`, and `topic` skills, the vault template, and the bootstrap prompt.
- Session readers for OpenCode, Pi, and Claude Code (transcripts and prompt history).
- Stats: prompts, active hours split into weekday core, early, evening, and weekend, PRs, time to merge, and reviews per person.
- Optional Confluence source.
