#!/usr/bin/env python3
"""The gcode parsers behind the print kit.

    python3 tests/test_slice.py

These turn slicer output into the filament and time a person buys and waits
for. A parser that silently drops the hours component understates a 21-hour
part as 10 minutes and nothing downstream can tell.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import slice_parts  # noqa: E402


def ok(name, got, want):
    good = got == want
    print(f"  {'PASS' if good else 'FAIL'}  {name}: {got!r}"
          + ("" if good else f"  <- want {want!r}"))
    return good


def main() -> int:
    r = []
    print("seconds() - PrusaSlicer omits any unit that is zero")
    for s, want in (("9m 49s", 589), ("21h 10m", 76200), ("1h 9m 49s", 4189),
                    ("40m", 2400), ("12s", 12), ("1d 2h", 93600), ("", 0)):
        r.append(ok(s or "(empty)", slice_parts.seconds(s), want))

    print("\nhhmm() - what a person reads")
    for sec, want in ((589, "9m"), (76200, "21h10m"), (4189, "1h09m"), (0, "0m")):
        r.append(ok(str(sec), slice_parts.hhmm(sec), want))

    print("\nregexes against real gcode comments")
    sample = ("; filament used [g] = 1.06\n"
              "; total filament used [g] = 255.40\n"
              "; estimated printing time (normal mode) = 21h 10m 3s\n")
    g = slice_parts.GRAMS.search(sample)
    t = slice_parts.TIME.search(sample)
    # `filament used` appears before `total filament used`; matching the wrong
    # one reports a single object's weight as the whole plate's.
    r.append(ok("grams takes the TOTAL line", g and g.group(1), "255.40"))
    r.append(ok("time is read", t and t.group(1), "21h 10m 3s"))

    # publish.py appended the measured facts and THEN truncated the whole
    # string, so with a description already at the cap - it always is - the
    # facts were added and immediately sliced off. coach-party 2026-08-20 went
    # out with "scatters each round's a" as its last words and no numbers.
    import publish
    FACTS = "7 printed designs, 40 pieces, 1111.9g PETG, 96h42m of printing"
    LONG = "word " * 200
    out = publish.fit_desc(LONG, FACTS)
    r.append(ok("facts survive a description already over the cap",
                FACTS in out, True))
    r.append(ok("and the result still fits", len(out) <= 500, True))
    r.append(ok("the prose is cut on a word boundary",
                out.split(" (")[0].endswith("\u2026"), True))
    r.append(ok("a short description is neither padded nor cut",
                publish.fit_desc("A small village game.", FACTS),
                f"A small village game. ({FACTS})"))
    r.append(ok("no slice report means no parenthetical",
                publish.fit_desc("A small village game.", ""),
                "A small village game."))
    r.append(ok("a long description with no facts is still capped",
                len(publish.fit_desc(LONG, "")) <= 500, True))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
