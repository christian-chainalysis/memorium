#!/usr/bin/env python3
"""Read your Confluence pages for the worklog skill. Optional.

Settings come from ~/notes/_meta/profile.md: confluence_site (https://<you>.atlassian.net) and
confluence_email. The token comes from the macOS Keychain (service atlassian-api-token) and
is never printed. Save long tokens with: security add-generic-password -U -a "$USER" -s atlassian-api-token -w "$(pbpaste)"

Commands:
  confluence.py list [--since YYYY-MM-DD] [--until YYYY-MM-DD]
      JSON list of pages he created or edited in the window, with his edit counts.
  confluence.py dump <page-id> --out DIR
      Write the page as plain text with a metadata header to DIR/<id>.md.
"""

import argparse
import base64
import html
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

import os
VAULT = Path(os.environ.get("NOTES_VAULT", Path.home() / "notes"))


def _profile():
    out = {}
    p = VAULT / "_meta/profile.md"
    if p.exists():
        text = p.read_text()
        if text.startswith("---"):
            text = text.split("---", 2)[1]
        for line in text.splitlines():
            if ":" in line and not line.startswith((" ", "-", "#")):
                k, v = line.split(":", 1)
                out[k.strip()] = v.split("#", 1)[0].strip().strip('"').strip("'")
    return out


_P = _profile()
SITE = _P.get("confluence_site", "").rstrip("/")
EMAIL = _P.get("confluence_email", "")
if not SITE or not EMAIL:
    sys.exit("Set confluence_site and confluence_email in ~/notes/_meta/profile.md to use Confluence.")


def token():
    out = subprocess.run(
        ["security", "find-generic-password", "-s", "atlassian-api-token", "-w"],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit("No atlassian-api-token in the Keychain.")
    return out.stdout.strip()


def get(path, params=None):
    url = SITE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    auth = base64.b64encode(f"{EMAIL}:{token()}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": "Basic " + auth, "Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def me():
    return get("/wiki/rest/api/user/current")["accountId"]


def my_versions(page_id, account):
    versions, start = [], 0
    while True:
        data = get(f"/wiki/rest/api/content/{page_id}/version", {"start": start, "limit": 200})
        versions += data.get("results", [])
        if data.get("size", 0) < 200:
            break
        start += 200
    mine = [v for v in versions if v.get("by", {}).get("accountId") == account]
    return len(versions), mine


def list_pages(since, until):
    account = me()
    cql = "contributor=currentUser() and type in (page,blogpost)"
    if since:
        cql += f' and lastmodified >= "{since}"'
    if until:
        cql += f' and lastmodified < "{until}"'
    cql += " order by lastmodified desc"
    results, start = [], 0
    while True:
        data = get("/wiki/rest/api/search", {"cql": cql, "limit": 50, "start": start,
                                             "expand": "content.space,content.history,content.version"})
        results += data.get("results", [])
        if start + 50 >= data.get("totalSize", 0):
            break
        start += 50
    pages = []
    for r in results:
        c = r["content"]
        total, mine = my_versions(c["id"], account)
        window = [v for v in mine if (not since or v["when"][:10] >= since) and (not until or v["when"][:10] < until)]
        created_by_me = c.get("history", {}).get("createdBy", {}).get("accountId") == account
        pages.append({
            "id": c["id"],
            "title": html.unescape(c["title"]),
            "space": c.get("space", {}).get("key"),
            "url": SITE + "/wiki" + c["_links"]["webui"],
            "created": c.get("history", {}).get("createdDate", "")[:10],
            "created_by_me": created_by_me,
            "last_modified": r.get("lastModified", "")[:10],
            "versions_total": total,
            "versions_mine": len(mine),
            "versions_mine_in_window": len(window),
            "my_edit_dates": sorted({v["when"][:10] for v in window}),
        })
    return pages


class Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "table"}

    def __init__(self):
        super().__init__()
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag in {"h1", "h2", "h3", "h4"}:
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in self.BLOCK:
            self.out.append("\n")
        elif tag in {"td", "th"}:
            self.out.append(" | ")

    def handle_data(self, data):
        self.out.append(data)

    def text(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.out)).strip()


def dump(page_id, out_dir):
    account = me()
    c = get(f"/wiki/rest/api/content/{page_id}", {"expand": "body.storage,space,history,version"})
    total, mine = my_versions(page_id, account)
    parser = Text()
    parser.feed(c["body"]["storage"]["value"])
    header = [
        f"# {html.unescape(c['title'])}",
        f"id: {c['id']}",
        f"space: {c['space']['key']}",
        f"url: {SITE}/wiki{c['_links']['webui']}",
        f"created: {c['history']['createdDate'][:10]} by {c['history']['createdBy'].get('displayName')}",
        f"versions: {total} total, {len(mine)} by you",
        f"my_edit_dates: {', '.join(sorted({v['when'][:10] for v in mine}))}",
        "",
    ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{page_id}.md"
    path.write_text("\n".join(header) + parser.text() + "\n")
    print(f"{path} ({path.stat().st_size} bytes)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list")
    p.add_argument("--since")
    p.add_argument("--until")
    d = sub.add_parser("dump")
    d.add_argument("id")
    d.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.cmd == "list":
        print(json.dumps(list_pages(args.since, args.until), indent=2))
    else:
        dump(args.id, args.out)


if __name__ == "__main__":
    main()
