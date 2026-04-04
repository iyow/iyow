#!/usr/bin/env python3

import re
import json
import urllib.request
from datetime import datetime

USERNAME = "iyow"
TOP_N = 3


def fetch_json(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_activity_status(pushed_at):
    update_date = datetime.strptime(pushed_at[:10], "%Y-%m-%d")
    days = (datetime.now() - update_date).days
    if days <= 30:
        return "🟢 活跃"
    elif days <= 90:
        return "🟡 维护"
    return "🔴 沉寂"


def score_repo(stars, pushed_at):
    pushed_date = datetime.strptime(pushed_at[:10], "%Y-%m-%d")
    days = (datetime.now() - pushed_date).days
    recency_bonus = max(0, 100 - days) / 100
    return stars + recency_bonus * 10


def get_repo_emoji(name):
    emoji_map = {
        "dream-vault": "🎭",
        "agent-forge": "🤖",
        "frontend-learningroad": "📚",
        "blog": "📝",
        "notes": "📓",
        "tool": "🛠️",
        "cli": "⚡",
        "web": "🌐",
        "app": "📱",
        "api": "🔌",
        "config": "⚙️",
        "dotfiles": "📁",
        "vim": "💻",
        "nvim": "💻",
        "zsh": "🐚",
    }
    name_lower = name.lower()
    for key, emoji in emoji_map.items():
        if key in name_lower:
            return emoji
    return "📦"


def format_name(name):
    return name.replace("-", " ").replace("_", " ").title()


def generate_cell(p):
    status = get_activity_status(p["pushed"])
    emoji = get_repo_emoji(p["name"])
    title = format_name(p["name"])
    desc = p["desc"] or ""
    desc_truncated = (
        f"""
{desc[:50]}{"..." if len(desc) > 50 else ""}
"""
        if desc
        else ""
    )
    return f"""<td width="33%" valign="top" align="center">

**{emoji} {title}**

<span>

⭐ {p["stars"]}  ·  {p["language"]}  ·  {status}

</span>
{desc_truncated}
[View →]({p["url"]})

</td>"""


def main():
    with open("README.md", "r") as f:
        content = f.read()

    content = content.replace(
        "<!-- UPDATE_TIME -->", datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&page={page}&sort=updated"
        try:
            data = fetch_json(url)
            if not data:
                break
            repos.extend(data)
            if len(data) < 100:
                break
            page += 1
        except Exception as e:
            print(f"Error fetching repos: {e}")
            break

    print(f"Found {len(repos)} repositories")

    scored = []
    for r in repos:
        if r.get("fork"):
            continue
        if r["name"].lower() == "iyow":
            continue
        scored.append(
            {
                "name": r["name"],
                "desc": r.get("description") or "",
                "stars": r["stargazers_count"],
                "language": r.get("language") or "Code",
                "pushed": r["pushed_at"],
                "url": r["html_url"],
                "score": score_repo(r["stargazers_count"], r["pushed_at"]),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    top3 = scored[:TOP_N]

    print("\nTop 3 projects:")
    for i, p in enumerate(top3, 1):
        print(f"  {i}. {p['name']} (⭐{p['stars']}, score={p['score']:.1f})")

    cells = [generate_cell(p) for p in top3]
    table_rows = "\n".join(cells)
    table = f"""<table>
<tr>
{table_rows}
</tr>
</table>"""

    new_content = re.sub(
        r"### 📦 精选项目\n\n<table>.*?</table>",
        f"### 📦 精选项目\n\n{table}",
        content,
        flags=re.DOTALL,
    )

    with open("README.md", "w") as f:
        f.write(new_content)
    print("\n✓ README.md updated")


if __name__ == "__main__":
    main()
