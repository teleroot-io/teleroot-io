#!/usr/bin/env python3
"""Generate static SVG cards (stats + top languages) for the profile README.

Only the Python standard library is used, so the GitHub Action needs no
dependencies beyond the preinstalled interpreter.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER = os.environ.get("GITHUB_USER", "teleroot-io")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"

BG = "#0D1117"
FG = "#C9D1D9"
DIM = "#8B949E"
GREEN = "#00FF41"
FONT = "'JetBrains Mono','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
BAR_COLORS = ["#00FF41", "#2BE65B", "#5CD97A", "#8CCC99", "#A9B8AD"]


def api(path, accept="application/vnd.github+json"):
    headers = {
        "Accept": accept,
        "User-Agent": f"{USER}-profile-cards",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(API + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def total_count(query, accept="application/vnd.github+json"):
    try:
        return api(f"/search/{query}", accept).get("total_count", 0)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"warn: search/{query}: {exc}", file=sys.stderr)
        return None


def human(number):
    if number is None:
        return "n/a"
    if number >= 1000:
        return f"{number / 1000:.1f}k".replace(".0k", "k")
    return str(number)


def chrome(width, height, title):
    """Terminal window chrome shared by both cards."""
    return f"""  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0H0V24" fill="none" stroke="{GREEN}" stroke-opacity="0.045" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{width}" height="{height}" rx="14" fill="{BG}"/>
  <rect width="{width}" height="{height}" rx="14" fill="url(#grid)"/>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="13.5" fill="none" stroke="{GREEN}" stroke-opacity="0.32"/>
  <circle cx="26" cy="25" r="5" fill="#FF5F57" fill-opacity="0.8"/>
  <circle cx="44" cy="25" r="5" fill="#FEBC2E" fill-opacity="0.8"/>
  <circle cx="62" cy="25" r="5" fill="#28C840" fill-opacity="0.8"/>
  <text x="82" y="29" font-family="{FONT}" font-size="11" fill="{DIM}">{title}</text>
  <text x="{width - 24}" y="29" font-family="{FONT}" font-size="11" fill="{DIM}" text-anchor="end">archer@github</text>
  <line x1="0" y1="46" x2="{width}" y2="46" stroke="{GREEN}" stroke-opacity="0.14"/>"""


def build_stats(stats, updated):
    width, height = 880, 300
    cells = len(stats)
    margin = 28
    cell_w = (width - margin * 2) / cells
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GitHub stats for {USER}">',
        chrome(width, height, "./stats --all"),
        f'  <text x="{margin}" y="84" font-family="{FONT}" font-size="18" fill="{GREEN}">'
        f'&gt;_ ./stats --all</text>',
        f'  <text x="{width - margin}" y="84" font-family="{FONT}" font-size="11" '
        f'fill="{DIM}" text-anchor="end">PUBLIC DATA</text>',
    ]
    for i, (label, value) in enumerate(stats):
        cx = margin + cell_w * i + cell_w / 2
        if i:
            x = margin + cell_w * i
            parts.append(
                f'  <line x1="{x:.1f}" y1="112" x2="{x:.1f}" y2="212" '
                f'stroke="{GREEN}" stroke-opacity="0.12"/>'
            )
        parts.append(
            f'  <text x="{cx:.1f}" y="170" font-family="{FONT}" font-size="34" font-weight="700" '
            f'fill="{GREEN}" text-anchor="middle">{value}</text>'
        )
        parts.append(
            f'  <text x="{cx:.1f}" y="196" font-family="{FONT}" font-size="10" fill="{DIM}" '
            f'letter-spacing="1.6" text-anchor="middle">{label}</text>'
        )
    parts.append(
        f'  <line x1="{margin}" y1="228" x2="{width - margin}" y2="228" '
        f'stroke="{GREEN}" stroke-opacity="0.12"/>'
    )
    parts.append(
        f'  <text x="{margin}" y="258" font-family="{FONT}" font-size="11" fill="{DIM}">'
        f'updated {updated}</text>'
    )
    parts.append(
        f'  <text x="{margin}" y="278" font-family="{FONT}" font-size="11" fill="{GREEN}">'
        f'<tspan fill="{DIM}">$</tspan> ./refresh --cron daily  <tspan fill="{DIM}">'
        f'# github actions</tspan></text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def build_langs(langs, updated):
    rows = len(langs)
    width = 880
    top = 112
    row_h = 34
    height = top + rows * row_h + 62 if rows else 220
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Top languages for {USER}">',
        chrome(width, height, "./stack --languages"),
        f'  <text x="28" y="84" font-family="{FONT}" font-size="18" fill="{GREEN}">'
        f'&gt;_ ls ./stack --languages</text>',
        f'  <text x="{width - 28}" y="84" font-family="{FONT}" font-size="11" '
        f'fill="{DIM}" text-anchor="end">BY CODE SIZE</text>',
    ]
    if not langs:
        parts.append(
            f'  <text x="28" y="140" font-family="{FONT}" font-size="13" fill="{DIM}">'
            f'no public language data yet</text>'
        )
    bar_x, bar_max = 170, 560
    for i, (name, pct) in enumerate(langs):
        y = top + i * row_h
        w = max(6.0, bar_max * pct / 100)
        color = BAR_COLORS[i % len(BAR_COLORS)]
        parts.append(
            f'  <text x="28" y="{y + 15}" font-family="{FONT}" font-size="13" '
            f'fill="{FG}">{name}</text>'
        )
        parts.append(
            f'  <rect x="{bar_x}" y="{y + 3}" width="{bar_max}" height="12" rx="6" '
            f'fill="{GREEN}" fill-opacity="0.10"/>'
        )
        parts.append(
            f'  <rect x="{bar_x}" y="{y + 3}" width="{w:.1f}" height="12" rx="6" fill="{color}"/>'
        )
        parts.append(
            f'  <text x="{width - 28}" y="{y + 14}" font-family="{FONT}" font-size="12" '
            f'fill="{DIM}" text-anchor="end">{pct:.1f}%</text>'
        )
    parts.append(
        f'  <text x="28" y="{height - 22}" font-family="{FONT}" font-size="11" fill="{DIM}">'
        f'updated {updated}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    user = api(f"/users/{USER}")
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r.get("fork")]

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    commits = total_count(f"commits?q=author:{USER}&per_page=1",
                          "application/vnd.github.cloak-preview+json")
    pulls = total_count(f"issues?q=author:{USER}+type:pr&per_page=1")
    issues = total_count(f"issues?q=author:{USER}+type:issue&per_page=1")

    stats = [
        ("REPOSITORIES", human(len(repos))),
        ("STARS", human(stars)),
        ("FOLLOWERS", human(user.get("followers", 0))),
        ("COMMITS", human(commits)),
        ("PULL REQUESTS", human(pulls)),
        ("ISSUES", human(issues)),
    ]

    bytes_by_lang = {}
    for repo in repos:
        for name, size in api(f"/repos/{USER}/{repo['name']}/languages").items():
            bytes_by_lang[name] = bytes_by_lang.get(name, 0) + size
    grand_total = sum(bytes_by_lang.values()) or 1
    langs = [
        (name, size * 100 / grand_total)
        for name, size in sorted(bytes_by_lang.items(), key=lambda kv: kv[1], reverse=True)[:5]
    ]

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stats.svg").write_text(build_stats(stats, updated), encoding="utf-8")
    (OUT_DIR / "langs.svg").write_text(build_langs(langs, updated), encoding="utf-8")
    print(f"wrote {OUT_DIR / 'stats.svg'}")
    print(f"wrote {OUT_DIR / 'langs.svg'}")
    print(f"stats: {stats}")
    print(f"langs: {[(n, round(p, 1)) for n, p in langs]}")


if __name__ == "__main__":
    main()
