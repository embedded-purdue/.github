"""Refresh the organization profile using GitHub's public repository metadata."""

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def repositories():
    result = []
    page = 1
    while True:
        request = Request(
            f"https://api.github.com/orgs/embedded-purdue/repos?type=public&per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "embedded-purdue-profile",
            },
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def render_stats(repos):
    languages = Counter(repo["language"] for repo in repos if repo.get("language"))
    lines = [
        "| Metric | Total |",
        "| :--- | ---: |",
        f"| Public repositories | {len(repos):,} |",
        f"| Stars across repositories | {sum(repo['stargazers_count'] for repo in repos):,} |",
        f"| Forks across repositories | {sum(repo['forks_count'] for repo in repos):,} |",
        f"| Primary languages | {len(languages):,} |",
    ]
    if languages:
        lines += ["", "**Most-used languages**", "", "| Language | Repositories |", "| :--- | ---: |"]
        for language, count in sorted(languages.items(), key=lambda item: (-item[1], item[0]))[:8]:
            lines.append(f"| {language.replace('|', '&#124;')} | {count:,} |")
    lines += ["", f"Updated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}."]
    return "\n".join(lines)


def main():
    path = Path(__file__).resolve().parents[1] / "profile" / "README.md"
    original = path.read_text()
    start, end = "<!-- STATS:START -->", "<!-- STATS:END -->"
    if original.count(start) != 1 or original.count(end) != 1:
        raise ValueError("Expected exactly one stats marker pair")
    before, rest = original.split(start)
    _, after = rest.split(end)
    stats = render_stats(repositories())
    path.write_text(f"{before}{start}\n{stats}\n{end}{after}")


if __name__ == "__main__":
    main()
