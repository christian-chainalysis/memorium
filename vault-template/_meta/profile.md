---
# Who you are. The skills read this file. Keep it current.
name: {{name}}
role: {{role}}                     # for example: senior software engineer, product designer
team: {{team}}
company: {{company}}
started: {{started}}               # YYYY-MM, when you started this job
github_login: {{github_login}}     # from `gh api user -q .login`

# Agent harnesses you use. The worklog reads these.
# Built in: opencode, pi, claude-code. Add others here, and add a reader (see sessions.py).
harnesses: [{{harnesses}}]

# Weekly run day. Each run covers the previous Monday through Sunday.
worklog_day: Monday

# Optional sources. Leave blank to turn off.
confluence_site:                   # https://<you>.atlassian.net
confluence_email:
jira: off
---
# Profile

This file tells the worklog, meeting, and topic skills about you. Write it in plain words. The more context here, the better the findings.

## Role and work

{{role_summary}}

## Efforts

Long-running projects. Each also gets a note in `Projects/`. Mark your role: leading, helping, or supporting.

{{efforts}}

## Credit notes

Work you shared with others, or work that started before you joined. Extraction follows these so you never get credit you didn't earn.

-

## People

The people you work with most, and how. Handles for everyone go in `people.md`.

-

## Values and style

How you like to work and communicate. Extraction reads requests in this light. For example, "I value short answers" means asking for shorter replies is a value, not confusion.

-

## Transcript folders

Where meeting transcripts land, by meeting. The meeting skill checks these.

-

## Private

Anything agents should never write down, even in this private vault.

-
