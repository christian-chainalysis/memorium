#!/usr/bin/env bash
# Gather worklog inputs for one window into a temp folder.
# Usage: gather.sh <start YYYY-MM-DD> <end YYYY-MM-DD, exclusive> <stats label> <outdir>
# Example: gather.sh 2026-02-02 2026-03-02 2026-02 /tmp/bf
set -euo pipefail

START=$1
END=$2
LABEL=$3
OUT=$4
HERE="$(cd "$(dirname "$0")" && pwd)"
VAULT="${NOTES_VAULT:-$HOME/notes}"
S="python3 $HERE/sessions.py"
ME=$(gh api user -q .login)
LAST=$(python3 -c "import datetime as d; print(d.date.fromisoformat('$END') - d.timedelta(days=1))")

rm -rf "$OUT"
mkdir -p "$OUT/dumps"

$S list --since "${START}T00:00:00" --until "${END}T00:00:00" > "$OUT/list.json"

for flag in created merged-at updated; do
  gh search prs --author=@me "--$flag=$START..$LAST" \
    --json number,title,url,state,repository,author,createdAt,closedAt,body --limit 500 > "$OUT/a-$flag.json"
  sleep 2
  gh search prs --reviewed-by=@me "--$flag=$START..$LAST" \
    --json number,title,url,state,repository,author,createdAt --limit 500 > "$OUT/r-$flag.json"
  sleep 2
done

jq -s 'add | unique_by(.repository.name, .number) | [.[] | {repo: .repository.name, number, title, state, createdAt, closedAt, url, body: ((.body // "")[0:800])}] | sort_by(.createdAt)' \
  "$OUT"/a-*.json > "$OUT/prs-authored.json"
jq -s --arg me "$ME" 'add | unique_by(.repository.name, .number) | [.[] | select(.author.login != $me) | {repo: .repository.name, number, title, author: .author.login, createdAt, url}] | sort_by(.createdAt)' \
  "$OUT"/r-*.json > "$OUT/prs-reviewed.json"

jq -r '.sessions[] | "\(.tool) \(.id)"' "$OUT/list.json" | while read -r tool id; do
  $S dump "$tool" "$id" --since "${START}T00:00:00" --out "$OUT/dumps" > /dev/null
done

$S stats --since "${START}T00:00:00" --until "${END}T00:00:00" --out "$VAULT/_meta/stats/$LABEL.json" > /dev/null
CONFLUENCE_SITE=$(grep -E "^confluence_site:" "$VAULT/_meta/profile.md" 2>/dev/null | sed -e "s/^confluence_site:[[:space:]]*//" -e "s/[[:space:]]*#.*$//")
if [ -n "$CONFLUENCE_SITE" ]; then
  python3 "$HERE/confluence.py" list --since "$START" --until "$END" > "$OUT/confluence.json" || echo "[]" > "$OUT/confluence.json"
else
  echo "[]" > "$OUT/confluence.json"
fi
$S memory --since "${START}T00:00:00" --until "${END}T00:00:00" > "$OUT/memory.txt"

# Batch dumps: one batch per dump over 90 KB, others packed to about 70 KB.
python3 - "$OUT" <<'EOF'
import os, sys
out = sys.argv[1]
d = os.path.join(out, "dumps")
files = sorted(((os.path.getsize(os.path.join(d, f)), f) for f in os.listdir(d)), reverse=True)
batches, cur, size = [], [], 0
for s, f in files:
    if s > 90000:
        batches.append([f])
        continue
    if size + s > 70000 and cur:
        batches.append(cur)
        cur, size = [], 0
    cur.append(f)
    size += s
if cur:
    batches.append(cur)
for i, b in enumerate(batches):
    with open(os.path.join(out, f"batch-{i}.txt"), "w") as fh:
        fh.write("\n".join(os.path.join(d, f) for f in b))
EOF

echo "sessions: $(jq .count "$OUT/list.json")"
echo "by tool: $(jq -c '[.sessions[].tool] | group_by(.) | map({(.[0]): length}) | add' "$OUT/list.json")"
echo "authored PRs: $(jq length "$OUT/prs-authored.json")"
echo "reviewed PRs: $(jq length "$OUT/prs-reviewed.json")"
echo "dump bytes: $(cat "$OUT"/dumps/* 2>/dev/null | wc -c)"
echo "confluence pages: $(jq length "$OUT/confluence.json")"
echo "memory files: $(wc -l < "$OUT/memory.txt")"
for b in "$OUT"/batch-*.txt; do echo "$(basename "$b"): $(wc -l < "$b" | tr -d ' ')+1 files"; done
