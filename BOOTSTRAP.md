# Memorium bootstrap

Paste this whole file into a new agent session (OpenCode, Pi, Claude Code, or another harness), started in your home folder. The agent sets up your vault, then walks you through a test week.

---

You are setting up Memorium for me. Memorium is a kit of agent skills plus an Obsidian vault template. It turns my agent sessions, GitHub PRs, and meetings into a private, linked record of my work: what I shipped, how I work, what slows me down, and what's worth saving.

The kit is at `~/dev/memorium` (or wherever I cloned it, so ask if it isn't there). Read `README.md` in the kit first. Then do these steps in order. Ask before anything that installs, deletes, or pushes. Keep each question short. Offer a recommended answer where you can.

## 1. Interview me

Ask, one group at a time:

1. **Me:** name, role, team, company, and when I started this job.
2. **My harnesses:** which agent tools I use for coding, all of them. Built-in readers cover OpenCode, Pi, and Claude Code. For each harness, check where it stores sessions on disk, such as `~/.local/share/opencode/`, `~/.pi/agent/sessions/`, `~/.claude/projects/`, `~/.codex/`, and Cursor's app data. Report what you found, with session counts and date ranges.
3. **My efforts:** the 3 to 6 long-running projects I work on, and my role in each: leading, helping, or supporting.
4. **My people:** who I work with most, mentor, or review for.
5. **My style:** how I like to work and communicate, and anything I value that should shape how my sessions are read.
6. **Credit:** any work I shared, or that started before me, that I shouldn't get sole credit for.
7. **Optional sources:** do I use Confluence or Jira? Where do my meeting transcripts land?
8. **My existing skills:** list the skills in my skills folders (such as `~/.config/agents/skills`, `~/.claude/skills`, or OpenCode's), and ask which ones I use. They become one of my efforts, so I can see what improves them.
9. **The vault shape:** show me the default folders from `vault-template/AGENTS.md`. Ask which I want, which I'd rename, and what I'd add. The defaults are a starting point, not rules.

## 2. Install

1. **Obsidian:** if missing, `brew install --cask obsidian`. Ask me to open Obsidian, then turn on **Settings > General > Advanced > Command line interface**. Check `obsidian version` works.
2. **Tools:** check `gh` (logged in), `jq`, `python3`, and `git`. Offer to install anything missing.
3. **Claude Code transcripts:** if I use Claude Code, offer to set `"cleanupPeriodDays": 3650` in `~/.claude/settings.json`, because it deletes transcripts after 30 days by default.

## 3. Create the vault

1. Copy `vault-template/` to `~/notes` (or a path I choose). If I chose another path, tell me to set `export NOTES_VAULT=<path>` in my shell profile.
2. Fill the `{{placeholders}}` in `AGENTS.md`, `Home.md`, and `_meta/profile.md` from the interview. Write my efforts into `profile.md` and create a note in `Projects/` for each, with `effort:` and `role:` properties.
3. Apply my folder choices. Update the table in `AGENTS.md` to match, and remove the matching steps from my copy of the notes if I dropped something.
4. Install the two Obsidian plugins the template expects:
   - **Obsidian Git:** `gh release download -R Vinzent03/obsidian-git -p main.js -p manifest.json -p styles.css` into `.obsidian/plugins/obsidian-git/`.
   - **Homepage:** `gh release download -R mirnovov/obsidian-homepage -p main.js -p manifest.json -p styles.css` into `.obsidian/plugins/homepage/`.
   
   Then ask me to turn off Restricted mode in Obsidian, open the vault folder, and enable both.
5. `git init`, commit, and offer to create a **private** GitHub repo with `gh repo create <me>/notes --private --source=. --push`.

## 4. Link the skills

Symlink each folder in the kit's `skills/` into every skills folder my harnesses read. Don't copy, so kit updates reach me with a `git pull`. For example:

```
ln -s ~/dev/memorium/skills/worklog ~/.config/agents/skills/worklog
```

If a harness I use has no built-in session reader, offer to write one in `skills/worklog/scripts/sessions.py`, following the notes in its header. Write it generically, so it can go back into the kit.

## 5. First run

1. Tell me the skills load in new sessions only.
2. Have me start a new session in the vault and run `/worklog` for last week only.
3. Review the plan with me. Ask what it got wrong or missed. Fix my `profile.md` from what I say.
4. Offer a backfill, one month at a time, oldest first. Check how far back my sessions go first, because some harnesses delete old transcripts. GitHub PRs go back to my first commit.

## 6. Finish

Tell me in a few lines:

- what's set up
- my weekly routine (`/worklog` on my run day, `/meeting` after meetings worth keeping, `/topic` for subjects I'm learning)
- that personal details live only in my vault, and the kit stays generic
