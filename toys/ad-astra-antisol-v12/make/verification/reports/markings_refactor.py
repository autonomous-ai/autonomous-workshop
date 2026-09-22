"""Did threading a side through the marking lookup change anything it must not?

`parts/markings.MARKINGS` was read in five places in `parts/world.py` -- the
raw union, the region builder twice, the body assembly and the absent-key
check -- and every one of them now calls `markings_for(planet, side)` instead.
One place owns the longitude reflection and every consumer is unchanged in
shape.

The claim that buys is that the other six worlds get back exactly what they got
before, on BOTH sides, and that the two corrected worlds' SOL pieces do too.
That is sixteen cases, fourteen of which must be the untouched table.  It is
checked here rather than asserted, on the structure itself: same length, same
keys, same filaments, same subtractions, same region specs vertex for vertex.

Uranus's entry is empty, from the run before this one.  An empty marking list
has to survive the refactor unchanged and must not have become a special case,
so it is checked like any other world rather than skipped.

    "$WORKSHOP_PYTHON" measure/markings_refactor.py > measure/markings-refactor.md

Exit 0 when every case that must be unchanged is unchanged, 1 otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402
from parts.markings import (                                  # noqa: E402
    MAP_MIRRORED_WORLDS,
    MARKINGS,
    markings_for,
)


def spec_count(entries) -> int:
    return sum(len(specs) for _k, _c, specs, _s in entries)


def vertex_count(entries) -> int:
    total = 0
    for _key, _colour, specs, _sub in entries:
        for spec in specs:
            if spec[0] == "outline":
                total += sum(len(ring) for ring in spec[1])
            elif spec[0] == "blob":
                total += len(spec[1])
    return total


def main() -> int:
    print("# `MARKINGS[planet]` against `markings_for(planet, side)`")
    print()
    print("Every marking lookup in `parts/world.py` now goes through")
    print("`markings_for(planet, side)`. This is the check that the change is a")
    print("refactor everywhere it is supposed to be one: for the six worlds not")
    print("named in `MAP_MIRRORED_WORLDS`, on both sides, and for the Sol piece")
    print("of the two that are, the function must return exactly what indexing")
    print("`MARKINGS` returned before.")
    print()
    print("`identical object` is the strongest form of that answer and the one")
    print("the function actually gives: in those fourteen cases it returns the")
    print("table's own list rather than a copy of it, so there is nothing that")
    print("could drift.")
    print()
    print("| planet | side | must be unchanged | equal | identical object | markings | region specs | ring vertices |")
    print("|---|---|---|---|---|---:|---:|---:|")
    failures = []
    for planet in sorted(P.PLANETS, key=lambda name: P.PLANETS[name]["rank"]):
        baseline = MARKINGS[planet]
        for side in P.SIDES:
            got = markings_for(planet, side)
            must = not (side == "anti" and planet in MAP_MIRRORED_WORLDS)
            equal = got == baseline
            same = got is baseline
            print("| %s | %s | %s | %s | %s | %d | %d | %d |"
                  % (planet, side, "yes" if must else "no -- mirrored",
                     ("yes" if equal else "**no**") if must
                     else ("**no -- it did not mirror**" if equal
                           else "no, as required"),
                     "yes" if same else ("no" if must else "n/a"),
                     len(got), spec_count(got), vertex_count(got)))
            if must and not (equal and same):
                failures.append(
                    "%s %s must be unchanged and is not (equal=%s, identical=%s)"
                    % (planet, side, equal, same))
            if not must and equal:
                failures.append(
                    "%s %s is supposed to be mirrored and came back unchanged"
                    % (planet, side))

    print()
    print("## The shape of what comes back")
    print()
    print("A mirrored entry has to be the same structure with different")
    print("longitudes in it -- same number of markings in the same order, the")
    print("same keys, the same filaments, the same subtractions, and every ring")
    print("the same length. A transform that dropped a marking or reordered the")
    print("split would pass a longitude check and fail the piece.")
    print()
    print("| planet | markings in order | filaments | subtractions | ring lengths |")
    print("|---|---|---|---|---|")
    for planet in MAP_MIRRORED_WORLDS:
        for side in ("sol", "anti"):
            entries = markings_for(planet, side)
            keys = [key for key, _c, _s, _sub in entries]
            colours = [colour for _k, colour, _s, _sub in entries]
            subs = [tuple(sub) for _k, _c, _s, sub in entries]
            lengths = []
            for _key, _colour, specs, _sub in entries:
                for spec in specs:
                    if spec[0] == "outline":
                        lengths.extend(len(ring) for ring in spec[1])
            print("| %s %s | %s | %s | %s | %s |"
                  % (planet, side, ", ".join(keys), ", ".join(colours),
                     "; ".join(str(item) for item in subs),
                     ", ".join(str(item) for item in lengths)))
        for field, reader in (("keys", lambda e: [k for k, _c, _s, _u in e]),
                              ("filaments", lambda e: [c for _k, c, _s, _u in e]),
                              ("subtractions", lambda e: [tuple(u) for _k, _c, _s, u in e]),
                              ("ring lengths", lambda e: [
                                  len(ring)
                                  for _k, _c, specs, _u in e
                                  for spec in specs if spec[0] == "outline"
                                  for ring in spec[1]])):
            if reader(markings_for(planet, "sol")) != reader(markings_for(planet, "anti")):
                failures.append("%s: the mirror changed the %s" % (planet, field))

    print()
    print("## Uranus's empty entry")
    print()
    empty_ok = (markings_for("uranus", "sol") == []
                and markings_for("uranus", "anti") == []
                and markings_for("uranus", "sol") is MARKINGS["uranus"])
    print("`MARKINGS[\"uranus\"]` is `%r`, the one world in the set with a bare"
          % (MARKINGS["uranus"],))
    print("globe. `markings_for` returns that same empty list on both sides, by")
    print("the same route every other unmirrored case takes -- there is no")
    print("`if not entries` anywhere in the function, and no branch that names")
    print("Uranus. %s" % ("Checked here." if empty_ok else "**IT DOES NOT.**"))
    if not empty_ok:
        failures.append("Uranus's empty entry did not survive the refactor")

    print()
    print("## Verdict")
    print()
    if failures:
        for item in failures:
            print("- **%s**" % item)
    else:
        print("All sixteen cases behave as they must. Fourteen return the")
        print("untouched table itself; the two mirrored ones return the same")
        print("structure with reflected longitudes in it. The refactor moved no")
        print("marking on any world it was not asked to move.")
    print()
    print("Measured by `measure/markings_refactor.py`.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
