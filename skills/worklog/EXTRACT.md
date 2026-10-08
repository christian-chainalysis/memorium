# Extraction brief

Give this brief to each extraction subagent, with the file paths, PR lists, and seed lists.

---

You read one or more agent session transcripts from one person. Before you read them, read `~/notes/_meta/profile.md`. It says who they are, their role, their efforts, the people they work with, and anything they want you to know about how to read them. In this brief, "the user" means that person.

Read each transcript in full. You have two jobs.

1. Record **what the user got done**.
2. Notice **how the user works**: what they are good at, where they struggle, what they care about, and how they work with others.

Use their words for the work, not the agent's process. Quote them when a quote shows something real. Record only what the transcript supports. When you infer, say so.

## Check before you write

- **PR authors and state:** for any PR not in the PR lists, run `gh pr view <n> -R <owner>/<repo> --json author,state,mergedAt,title`. Never guess who wrote a PR or whether it merged. Mark PRs you looked up with `(looked up)`.
- **Credit:** follow the credit notes in `profile.md`. When work was shared, name everyone who built it. Never give the user credit for work that started before them or that someone else did.
- **Names:** use the seed lists. Reuse a seed topic slug or effort name when the work matches. Write people as `Name (github-handle)`, taking the pair from `people.md` or the PR author. When you can't find a handle, write the name alone.
- **Links between sessions:** do not guess that one session caused work in another. The orchestrator links sessions.
- **Secrets:** never copy a token, key, or password. Note only that one was pasted, and whether the session shows it was rotated.

## Write one file per session

Pick the session's `date` as the day with the most user activity. Write to `~/notes/_meta/findings/<YYYY-MM of date>/<tool>-<id>.md`. Leave out any section that has nothing.

```markdown
---
session: <resume command>
source: <tool>
cwd: <cwd>
date: <YYYY-MM-DD with most activity>
start: <first user message, ISO time>
end: <last message, ISO time>
---

## Work
- topic: <kebab-case slug, from the seed list when it fits>
  effort: <effort name from the seed list, a proposed new one, or none>
  project: <repo or product>
  date: <YYYY-MM-DD the outcome happened>
  summary: <1 to 3 sentences. What changed and why it matters. Include numbers and outcomes.>
  prs: <repo#number (author, state), ...> or none
  reviews: <review results on this work, such as "review: 3 must-fix">, or none
  size: none | notable | major

## About you
- kind: strength | struggle | worry | win | value | growth | habit
  note: <one or two sentences>
  evidence: <short quote or event>

## People
- who: <Name (github-handle)>
  what: <mentoring, unblocking, review, collaboration>
  evidence: <short quote or event>

## Friction
- what: <where the user or the agent got stuck, looped, or undid work>
  cause: <bad docs, missing tool, unclear repo convention, agent mistake, flaky CI, other>
  fix: agents-md | skill | doc-pr | tooling | none
  fix_detail: <the specific file, repo, or skill that would remove it>
  status: open | fixed (<link or date>) | unknown

## Corrections
- <up to 5 things the user told the agent to do or stop doing, in their words>

## Repeats
- <a task they do that looks like it recurs, and could become a skill>

## Learnings
- <a fact, gotcha, or technique worth a note, unless the repo docs already cover it>

## Numbers
- <up to 10 counts, durations, or ratios that matter most: tests fixed, files touched, minutes stuck, retries, people helped, scores>

## Noticed
- <anything interesting that fits no section above: a pattern, an oddity, a hunch>
```

If a session holds nothing worth logging, write only the frontmatter and `none: <one line why>`.

## Sizing work

Size the task in this session, not the effort it belongs to. The effort carries the big story.

- **major:** the task alone changes how the company works, such as a new system other teams now depend on. Rare. Most weeks have none.
- **notable:** a shipped feature users see, a hard bug, a migration, an incident fix, or work that unblocked another team.
- **none:** routine fixes, small UI tweaks, chores, reviews, and docs. Docs and chore PRs are none unless they change how a team works. Most work is none.

## Efforts

An effort is a project that spans many weeks. The seed list and `profile.md` name the current efforts, with the user's role in each: leading, helping, or supporting. Tag supporting work and say "supporting" in the summary. Follow any backstory or alias notes in `profile.md`, such as a product's old names.

Tie every work item to an effort when one fits. If the work clearly belongs to a long project that no seed effort names, propose a name and add `(new)`.

## About you, people, and friction

- **About you** covers the person, not the code. Look for how they work: what they check by hand, how they review, what they explain well, what they ask for help with, what makes them impatient, what they are proud of, and the choices they defend. Read their requests in the light of the values in `profile.md`. For example, a person who values short answers is stating a value when they ask for less, not showing confusion.
- **People** covers anyone the user helps, teaches, reviews for, or unblocks.
- **Friction** matters most when it would happen again. Record the concrete fix target, such as "the repo's AGENTS.md lacks the local setup step" or "a skill for dependency triage". Always record friction, even when it is already fixed, because the history shows how the setup improved. Check the known fixes list first. If the friction matches a known fix, set `status: fixed` and link it. Otherwise use `open` for recent sessions and `unknown` for sessions older than a month.
- **Numbers** are always worth keeping. The audit adds them up across the year.
- **Noticed** is for curiosity. The sections above are only a starting list. If something seems interesting and has no home, write it here.

## Return

Reply with the paths you wrote and one line for each session.
