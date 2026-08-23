#!/usr/bin/env python3
"""Local BoardGameGeek name index for the DISCOVER prior-art gate.

Source: BGG's own CSV dump (boardgamegeek.com/data_dumps/bg_ranks, downloaded
while logged in — no API key needed), 180k games as of 2026-08-20.

What this dump CAN answer, deterministically and without spending a judge turn:
  - is a candidate's NAME already a published game
  - is the proposer's NEAREST claim a real game, and how big is it

What it CANNOT answer: whether a game with the same CORE LOOP exists. The dump
carries name, year, rank, rating and the eight subdomain ranks — no mechanics,
no categories, no descriptions. That question stays with the judges' WebSearch
until the XML API key lands (registration pending, see README).

Not in git: the dump is BGG's data, and /browse and the XML API both refuse
unauthenticated clients (403 / 401 as of 2026-08-20). Re-download it logged in.
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

CSV_PATH = Path(__file__).with_name("bgg_ranks.csv")

# "the rounds" and "rounds" must collide; "of" and "game" must not carry weight.
STOP = {"the", "a", "an", "of", "and", "or", "game", "games", "boardgame"}

SUBDOMAINS = ("abstracts", "cgs", "childrensgames", "familygames",
              "partygames", "strategygames", "thematic", "wargames")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


def tokens(s: str) -> set:
    return {t for t in norm(s).split() if len(t) > 2 and t not in STOP}


def load(path: Path = CSV_PATH):
    """(rows, by_name, postings, by_id). Rows are tuples, not dicts: 180k dicts of 16
    columns is a few hundred MB on a box that has already been OOM-killed."""
    rows, by_name, postings, by_id = [], {}, {}, {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            i = len(rows)
            by_id[r["id"]] = i
            subs = ",".join(s for s in SUBDOMAINS if r.get(s + "_rank"))
            rows.append((r["id"], r["name"], r["yearpublished"], r["rank"],
                         r["average"], r["usersrated"], r["is_expansion"], subs))
            by_name.setdefault(norm(r["name"]), []).append(i)
            for t in tokens(r["name"]):
                postings.setdefault(t, []).append(i)
    return rows, by_name, postings, by_id


def as_dict(row: tuple) -> dict:
    keys = ("id", "name", "year", "rank", "average", "usersrated",
            "is_expansion", "subdomains")
    return dict(zip(keys, row))


def search(query: str, index, limit: int = 5, min_overlap: float = 0.6) -> list:
    """Exact normalised-name matches first, then token-overlap near misses.

    Substring matching was tried and thrown out: 180k names include "M", "Ra"
    and "IT", so every query matched a dozen one-letter games."""
    rows, by_name, postings, _ = index
    out, seen = [], set()
    for i in by_name.get(norm(query), []):
        seen.add(i)
        out.append(dict(as_dict(rows[i]), match="exact"))
    q = tokens(query)
    if q:
        counts = {}
        for t in q:
            for i in postings.get(t, ()):
                counts[i] = counts.get(i, 0) + 1
        near = []
        for i, c in counts.items():
            if i in seen:
                continue
            other = tokens(rows[i][1])
            j = c / len(q | other)
            if j >= min_overlap:
                near.append((j, int(rows[i][5] or 0), i))
        near.sort(reverse=True)
        for j, _, i in near:
            out.append(dict(as_dict(rows[i]), match=f"near {j:.2f}"))
    out.sort(key=lambda d: (d["match"] != "exact", -int(d["usersrated"] or 0)))
    return out[:limit]


def scan(names: dict, index) -> dict:
    """{slug: {"NAME": ..., "NEAREST": ...}} -> per-slug findings for the judges."""
    report = {}
    for slug, d in names.items():
        entry = {}
        title = (d.get("NAME") or "").strip()
        if title:
            entry["title_hits"] = search(title, index)
        nearest = (d.get("NEAREST") or "").strip()
        if nearest:
            entry.update(resolve_nearest(nearest, index))
        report[slug] = entry
    return report


def resolve_nearest(nearest: str, index) -> dict:
    """Resolve a proposer's NEAREST line to a dump row.

    The line is written URL-first ("<url> — <name> is the benchmark for..."),
    so name-matching it matches the URL. Prefer the BGG id in the URL, which is
    exact; fall back to the URL's slug, which beats the trailing prose.
    """
    rows, _, _, by_id = index
    m = re.search(r"boardgamegeek\.com/boardgame/(\d+)", nearest)
    if m:
        i = by_id.get(m.group(1))
        if i is not None:
            return {"nearest_claim": f"BGG id {m.group(1)}",
                    "nearest_hits": [dict(as_dict(rows[i]), match="by id")]}
        return {"nearest_claim": f"BGG id {m.group(1)}", "nearest_hits": [],
                "nearest_note": "id is not in the dump (expansion, or newer than it)"}
    if "boardgamegeek.com" in nearest:
        return {"nearest_claim": nearest.split()[0],
                "nearest_hits": [],
                "nearest_note": "a BGG page that is not a single game entry"}
    m = re.search(r"https?://\S+", nearest)
    if m:
        seg = [x for x in m.group(0).split("?")[0].split("#")[0].split("/") if x]
        claim = re.sub(r"[-_]+", " ", seg[-1]) if len(seg) > 2 else ""
    else:
        claim = nearest
    claim = re.split(r"\s+[-\u2014(]", claim)[0].strip()
    if not claim or len(claim) > 80:
        return {}
    return {"nearest_claim": claim, "nearest_hits": search(claim, index, limit=3)}


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] not in ("title", "resolve"):
        print(__doc__.strip())
        print("\nusage: bgg_index.py title|resolve \"<name>\"")
        return 2
    if not CSV_PATH.is_file():
        print(f"missing {CSV_PATH} — download it logged in from "
              f"https://boardgamegeek.com/data_dumps/bg_ranks")
        return 1
    index = load()
    for h in search(" ".join(sys.argv[2:]), index):
        print(f"{h['match']:>10}  {h['id']:>7}  {h['name']} ({h['year']}) "
              f"rank={h['rank']} rated={h['usersrated']} {h['subdomains']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
