#!/usr/bin/env python3
"""What a LOT of people are paying attention to — not what Hacker News is.

    ./trends.py                 -> out/_discover/trends/<date>-*.md

DISCOVER used to read two digests out of second-brain: `hn-morning` and
`x-scrape`. Measured 2026-08-20, that skews the whole day's output toward tech
in four independent ways, and only the first is about taste:

1. The hn digest is ~4 KB and arrives WHOLE. The x-scrape is ~85 KB and
   `memory_get` truncates it — "81,646 chars left" — so the proposer reads all
   of the tech source and a tenth of the diverse one. The x-scrape is actually
   broad (Netflix, WSJ on food, sneakers, bison, the Beatles film); the pipeline
   just never got to most of it.
2. HN items carry vote counts. The prompt asks for "recurring themes with mass
   attention", and HN is the only source that shows a NUMBER, so it reads as
   evidence while a post from Reuters does not.
3. The citation example in the prompt was itself a tech story.
4. Both SEED lines that survived the last panel cite `hn-morning`.

So this file adds sources where mass attention is measured and NOT tech-shaped.
Both are keyless and one call each:

- Wikipedia top pageviews. The single best "what did the world look up
  yesterday" signal there is. Run 2026-08-20 it returned `Spider-Man: Brand New
  Day` (187,879) and `The Odyssey (2026 film)` (134,753) in the top ten — the
  exact two things the owner named as missing.
- Google Trends daily RSS. Sports, celebrities, and local news that Wikipedia
  under-weights (Son Heung-min, Paul Mescal filming the Beatles movie).

Titles alone do not seed a game — `Hayden Panettiere` is a name, not a tension —
so every Wikipedia row is enriched with its one-line summary.
"""
import concurrent.futures as cf
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Wikimedia asks for a contact in the UA and Cloudflare in front of Google
# Trends rejects the default python UA outright.
UA = "text2game/1.0 (tamnguyenfe@gmail.com) curl/8.7.1"
TIMEOUT = 25

# Pages that are always at the top and never a trend.
SKIP_EXACT = {"Main_Page", "Special:Search", "Wikipedia:Featured_pictures",
              "Special:Random", "Portal:Current_events"}
SKIP_PREFIX = ("Special:", "Wikipedia:", "Portal:", "Help:", "Category:",
               "File:", "Template:")


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def summary(title: str) -> str:
    """One line of what a page IS. A bare title cannot seed anything."""
    try:
        d = json.loads(get("https://en.wikipedia.org/api/rest_v1/page/summary/"
                           + urllib.parse.quote(title, safe="")))
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return ""
    text = (d.get("extract") or "").strip()
    return re.sub(r"\s+", " ", text)[:240]


def wiki_top(day: str, limit: int = 30) -> list:
    """[(views, title, one-line summary)] for the most-read pages of `day`."""
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
           f"en.wikipedia/all-access/{day}")
    arts = json.loads(get(url))["items"][0]["articles"]
    keep = [a for a in arts
            if a["article"] not in SKIP_EXACT
            and not a["article"].startswith(SKIP_PREFIX)][:limit]
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        sums = list(ex.map(lambda a: summary(a["article"]), keep))
    return [(a["views"], a["article"].replace("_", " "), s)
            for a, s in zip(keep, sums)]


def google_trends(geo: str = "US") -> list:
    """[(traffic, term, top news headline)] from the daily trending RSS."""
    x = get(f"https://trends.google.com/trending/rss?geo={geo}").decode(
        "utf-8", "replace")
    out = []
    for it in re.findall(r"<item>(.*?)</item>", x, re.S):
        def f(tag):
            m = re.search(rf"<{tag}>(.*?)</{tag}>", it, re.S)
            return re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1)).strip() if m else ""
        out.append((f("ht:approx_traffic"), html.unescape(f("title")),
                    html.unescape(f("ht:news_item_title"))))
    return out


def write(dst: Path, day: str) -> list:
    dst.mkdir(parents=True, exist_ok=True)
    written = []

    try:
        rows = wiki_top(day.replace("-", "/"))
        body = "\n".join(f"- **{t}** — {v:,} views. {s or '(no summary)'}"
                         for v, t, s in rows)
        p = dst / f"{day}-wiki-top.md"
        p.write_text(
            f"# Most-read Wikipedia pages — {day}\n\n"
            "What people actually looked up yesterday, ranked by real view "
            "counts. Films, deaths, sport, TV, scandals. A high number here "
            "means mass attention in the plainest sense there is.\n\n"
            + body + "\n", encoding="utf-8")
        written.append(p)
        print(f"  wiki-top: {len(rows)} pages -> {p.name}", flush=True)
    except Exception as e:                       # a dead source is not fatal
        print(f"  wiki-top FAILED: {e}", flush=True)

    try:
        rows = google_trends()
        body = "\n".join(f"- **{t}** — {tr or '?'} searches. {n}"
                         for tr, t, n in rows)
        p = dst / f"{day}-google-trends.md"
        p.write_text(
            f"# Google Trends, daily — {day} (US)\n\n"
            "Sport, celebrity and local news, which the Wikipedia list "
            "under-weights.\n\n" + body + "\n", encoding="utf-8")
        written.append(p)
        print(f"  google-trends: {len(rows)} terms -> {p.name}", flush=True)
    except Exception as e:
        print(f"  google-trends FAILED: {e}", flush=True)

    return written


def gamevault_briefing() -> list:
    """The newest board-game MARKET snapshot, if the vault has written one.

    The two digests above measure what the world at large looked up - broad
    on purpose, and blind to the hobby itself. vault_refresh.py --trends
    (gamevault repo) writes the other half when the orchestrator runs it at
    idle: BGG hotness, crowdfunding hits, viral print-and-play, researched by
    a headless claude with WebSearch and written in its own words. Newest
    file only; a stale month is still signal, and the generation stamp is in
    the file for the proposer to weigh.
    """
    root = Path(os.environ.get("GAMEVAULT", "/root/gamevault")) / "briefings"
    got = sorted(root.glob("trends-*.md"))
    return [str(got[-1])] if got else []


def fetch(out_dir: Path) -> list:
    """Digest paths for today. Yesterday's date: today's pageviews are partial."""
    day = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    return write(out_dir / "trends", day) + gamevault_briefing()


if __name__ == "__main__":
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out" / "_discover"
    got = fetch(d)
    print(f"\n{len(got)} digest(s) in {d / 'trends'}")
    sys.exit(0 if got else 1)
