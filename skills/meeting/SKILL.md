---
name: meeting
description: Turn a meeting transcript into a meeting note and findings in your Obsidian vault at ~/notes. Use when the user types /meeting or gives a meeting transcript to save.
disable-model-invocation: true
---

# Meeting

Turn one or more meeting transcripts into notes in `~/notes`. Follow the rules in `~/notes/AGENTS.md`, and read `~/notes/_meta/profile.md` for who the user is and where their transcripts land. Sessions show how the user builds. Meetings show how they lead, so record their role with care.

## 1. Find the transcripts

The user gives a path, a folder, or pasted text. With no input, look in the transcript folders listed in `profile.md` for files newer than the latest note in the matching `~/notes/Meetings/<Meeting>/` folder.

For each transcript:

1. Work out the meeting name and date from the file name or the text.
2. Skip it if `~/notes/Meetings/<Meeting>/YYYY-MM-DD.md` already exists, unless the user asks to redo it.
3. Look for an attendance report next to the transcript (for example a Google Meet CSV with the same date). If one exists, use it for `attendees`. Otherwise use the invite list and the speakers, and say so in the note.
4. Clean it into a temp folder with `python3 scripts/clean.py <file> > <tmpdir>/<YYYY-MM-DD>.md`. Exports from note-taking tools often carry inline images that make a file 10 times bigger than its text.

## 2. Write the note

For one meeting, write it yourself. For three or more, give each subagent two or three meetings.

Write `~/notes/Meetings/<Meeting>/YYYY-MM-DD.md`. If the folder has earlier notes, match the newest one. Otherwise use this shape:

- Frontmatter: `created`, `tags: [meeting]`, `meeting`, `date`, `attendees`, `attendance_source` (`report` or `invite`), and `efforts` as links.
- **Summary:** 3 to 5 bullets in your own words. Never copy a tool's auto summary.
- **Decisions:** aligned or needs discussion, one line each.
- **<User's first name>'s role:** what they drove, proposed, taught, or pushed back on, with short quotes. This is the most important section.
- **Others:** notable contributions, written as `Name (handle)` from `~/notes/_meta/people.md`.
- **Action items**, **Numbers**, and **Themes**.

Keep the raw transcript out of the vault. Leave out anything the user marks private.

Write raw findings to `~/notes/_meta/findings/<meeting-slug>/YYYY-MM-DD.md`: how the meeting moved the story, patterns in how the user leads, achievement candidates, people, and open threads.

## 3. Update the notes that span meetings

Show the user a short plan first: new achievement evidence, new or changed How I Work patterns, and open threads. Wait for an OK, then:

- Update the meeting's effort note in `Projects/`, if it has one: a timeline line, the Story, Open threads, and the unique attendee count.
- Add approved patterns to `About Me/How I Work.md`, and approved evidence to `Achievements/<year>.md`.
- Add new people to `_meta/people.md`, and facts you couldn't confirm to `Open Questions.md`.

Skip any of these notes the user removed from their vault.

## 4. Commit

Commit each note on its own, such as `meeting: design review 2026-10-13`, then push.
