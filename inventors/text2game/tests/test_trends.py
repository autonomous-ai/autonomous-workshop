#!/usr/bin/env python3
"""Trend sourcing: does the panel read the whole world, or one corner of it?

    python3 tests/test_trends.py

The bug these guard is not a crash - it is a shortlist where every idea came
from Hacker News while the code reported nothing wrong. So the cases below are
mostly about the AUDIT being loud, plus the parsers that feed it.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import discover  # noqa: E402
import trends    # noqa: E402

WIKI_JSON = b'''{"items":[{"articles":[
 {"article":"Main_Page","views":9000000},
 {"article":"Special:Search","views":800000},
 {"article":"Wikipedia:Featured_pictures","views":700000},
 {"article":"The_Odyssey_(2026_film)","views":134753},
 {"article":"Spider-Man:_Brand_New_Day","views":187879},
 {"article":"Portal:Current_events","views":50000},
 {"article":"ZZ_Top","views":125167}]}]}'''

RSS = b"""<rss><channel>
<item><title>maxx crosby</title><ht:approx_traffic>1000+</ht:approx_traffic>
<ht:news_item_title>Cousins: &apos;My elbow got hit&apos;</ht:news_item_title></item>
<item><title>the odyssey</title><ht:approx_traffic>2000+</ht:approx_traffic>
<ht:news_item_title>Nolan&apos;s epic opens</ht:news_item_title></item>
</channel></rss>"""


def cand(seed, **kw):
    d = {"SEED": seed}
    d.update(kw)
    return d


def main() -> int:
    r = []

    # ---- seed_source ----------------------------------------------------
    for raw, want in (
            ('trends/2026-08-19-wiki-top.md — "The Odyssey"', "2026-08-19-wiki-top.md"),
            ('raw/2026-08-20-hn-morning.md — "a joke domain"', "2026-08-20-hn-morning.md"),
            ("no file cited at all", ""),
            ("", "")):
        got = discover.seed_source({"SEED": raw})
        print(f"  {'PASS' if got == want else 'FAIL'}  seed_source({raw[:34]!r}) -> {got!r}")
        r.append(got == want)

    # ---- audit_seeds ----------------------------------------------------
    cases = [
        ("all one tech digest (the real 2026-08-20 round)",
         {"a": cand('raw/2026-08-20-hn-morning.md — "x"'),
          "b": cand('raw/2026-08-20-hn-morning.md — "y"')}, True),
        ("two digests, one non-tech",
         {"a": cand('raw/2026-08-20-hn-morning.md — "x"'),
          "b": cand('trends/2026-08-19-wiki-top.md — "The Odyssey"')}, False),
        ("two tech digests is still all-tech",
         {"a": cand('raw/2026-08-20-hn-morning.md — "x"'),
          "b": cand('raw/2026-08-20-lobsters.md — "y"')}, True),
        ("a candidate that cited nothing",
         {"a": cand('trends/2026-08-19-wiki-top.md — "x"'),
          "b": cand("")}, True),
        ("two non-tech digests is fine",
         {"a": cand('trends/2026-08-19-wiki-top.md — "x"'),
          "b": cand('trends/2026-08-19-google-trends.md — "y"')}, False),
        # A lane can cite one file twice and hide inside a varied shortlist -
        # the prompt promises this is measured, so it has to be.
        ("one lane doubled up, shortlist still looks varied",
         {"a": dict(cand('trends/2026-08-19-wiki-top.md — "1"'), lane="coop"),
          "b": dict(cand('trends/2026-08-19-wiki-top.md — "2"'), lane="coop"),
          "c": dict(cand('raw/2026-08-20-hn-morning.md — "3"'), lane="family"),
          "d": dict(cand('trends/2026-08-19-google-trends.md — "4"'), lane="family")},
         True),
        ("different lanes citing the same file is NOT a lane repeat",
         {"a": dict(cand('trends/2026-08-19-wiki-top.md — "1"'), lane="coop"),
          "b": dict(cand('trends/2026-08-19-google-trends.md — "2"'), lane="family")},
         False),
        ("no candidates at all is not an alarm",
         {}, False),
    ]
    for name, cands, want_bad in cases:
        note, bad = discover.audit_seeds(cands)
        print(f"  {'PASS' if bad == want_bad else 'FAIL'}  audit: {name} -> bad={bad}")
        if bad != want_bad:
            print(f"        note={note!r}")
        r.append(bad == want_bad)

    # ---- wiki_top: the boilerplate pages must never become trends -------
    trends.get = lambda url: WIKI_JSON        # noqa: E731 - deliberate stub
    trends.summary = lambda t: "one line"     # noqa: E731 - no network in tests
    rows = trends.wiki_top("2026/08/19")
    titles = [t for _, t, _ in rows]
    ok = ("Main Page" not in titles and "Special:Search" not in titles
          and "Portal:Current events" not in titles and len(rows) == 3)
    print(f"  {'PASS' if ok else 'FAIL'}  wiki_top drops boilerplate -> {titles}")
    r.append(ok)
    ok = titles[0] == "The Odyssey (2026 film)"
    print(f"  {'PASS' if ok else 'FAIL'}  wiki_top keeps API order, underscores -> spaces")
    r.append(ok)

    # ---- google_trends: entities must be decoded ------------------------
    trends.get = lambda url: RSS              # noqa: E731
    got = trends.google_trends()
    ok = len(got) == 2 and got[0][0] == "1000+" and "'My elbow got hit'" in got[0][2]
    print(f"  {'PASS' if ok else 'FAIL'}  google_trends decodes &apos; -> {got[0][2]!r}")
    r.append(ok)

    # ---- the prompt must carry both inputs and the IP rule --------------
    p = discover.propose_prompt("stack", HERE / "out" / "_discover",
                                [Path("trends/x-wiki-top.md")])
    for probe in ("INPUT A", "INPUT B", "TWO SOURCES, NOT ONE",
                  "USE THE ATTENTION, NEVER THE PROPERTY", "x-wiki-top.md"):
        ok = probe in p
        print(f"  {'PASS' if ok else 'FAIL'}  propose prompt carries {probe!r}")
        r.append(ok)

    # A prompt with no local digests must still name the corpus, not go blank.
    p0 = discover.propose_prompt("aim", HERE / "out" / "_discover", [])
    ok = "INPUT B" in p0 and "INPUT A" not in p0
    print(f"  {'PASS' if ok else 'FAIL'}  no local digests -> MCP block only")
    r.append(ok)

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
