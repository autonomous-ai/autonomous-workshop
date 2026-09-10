#!/usr/bin/env python
"""Filament colours — the stock this repository prints, by name.

A printed part can only be the colour of a spool somebody can load. Author a
colour as a free hex and the model shows a filament that does not exist: the
render looks decided, the STEP carries the decision into every downstream
reader, and nothing in the toolchain disagrees, because no gate here knows what
Bambu sells.

Pick from the palette instead, and the unbuyable colour becomes unrepresentable:

    from cadfilament import filament

    body.color = filament("sunflower yellow")
    lens.color = filament("cyan", 0.42)      # with alpha

An unknown name raises with the whole list rather than resolving to something
close, for the same reason `cadfits` derives the second half of a mate instead
of asserting it: a near-miss that still builds is the failure worth preventing.

The palette is **Bambu Lab PLA Lite**, read from
https://3dfilamentprofiles.com/filaments/bambu-lab/pla/lite on 2026-09-10. Hex
values are as published there; the trailing number is Bambu's colour code where
the catalogue lists one. Retire or extend the table here and every project that
reads it follows.

Colour that is deliberately not printed filament — a purchased component, a
reference surface, a see-through datum — is not in this table and belongs in
`cadgen.srgb("#rrggbb")`.

Importing it
------------
Every CLI launcher in `skills/cad/scripts/` puts its own directory on
`sys.path` before loading a generator, so a generator, a `*_lib.py`, or a
`measure/*.py` run through `scripts/gen` / `inspect` / `check_*` can
`import cadfilament` with no path setup. `verify_project` also supplies its
materialized scripts directory when launching local audits. A script run
directly by the interpreter adds the scripts directory itself, exactly as it
does for `cadfits`.

Deliberately NOT inside the vendored `cadgen` package, for the reason
`cadfits` gives: `cadgen` is installed into `.venv` as a *copy* while the
launchers prefer the vendored `scripts/packages/cadgen/src`, so a table living
there is read from two different files depending on how the process started,
and a pinned-version bump overwrites it. This one has a single home.

Self-check:

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadfilament.py"
"""

from __future__ import annotations

__all__ = ["FILAMENTS", "filament", "filament_hex"]

# Bambu Lab PLA Lite. name -> sRGB hex as published; comment is Bambu's colour
# code where the catalogue lists one.
FILAMENTS: dict[str, str] = {
    "beige": "#F7E6DE",             # 16700
    "black": "#000000",             # 16100
    "blue": "#004EA8",              # 16601
    "cocoa brown": "#8E3C06",
    "cyan": "#00FFFF",              # 16600
    "dark gray": "#6F6E6D",         # 16102
    "gray": "#9FA19F",              # 16101
    "green": "#00BB31",             # 16501
    "orange": "#FF671F",            # 16301
    "red": "#FF0000",               # 16200
    "sunflower yellow": "#FFB549",  # 16401
    "white": "#FFFEF7",             # 16103
    "yellow": "#FFD834",            # 16400
}


def _normalise(name: str) -> str:
    return " ".join(name.replace("_", " ").replace("-", " ").lower().split())


def filament_hex(name: str) -> str:
    """Return the sRGB hex of a palette colour, by name.

    Matching ignores case, underscores, hyphens and repeated spaces, so
    ``"Dark Gray"``, ``"dark_gray"`` and ``"DARK-GRAY"`` are one colour. An
    unknown name raises with the full list of what can actually be printed.
    """
    try:
        return FILAMENTS[_normalise(name)]
    except KeyError:
        available = ", ".join(sorted(FILAMENTS))
        raise ValueError(
            f"{name!r} is not a Bambu Lab PLA Lite colour; choose one of: {available}"
        ) from None


def filament(name: str, alpha: float = 1.0):
    """Build a build123d ``Color`` from a palette colour name.

    The conversion is `cadgen.color.srgb`, so the channels come out linear and
    the part displays as the hex the catalogue publishes. Never hand a palette
    hex to ``Color()`` directly: those channels are linear RGB and a hex read
    into them renders washed out.
    """
    from cadgen.color import srgb

    return srgb(filament_hex(name), alpha)


def _self_check() -> int:
    """Round-trip every colour through the renderer's own conversion."""
    from cadgen.color import linear_to_srgb

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'}  {label}{f'  — {detail}' if detail else ''}")
        if not ok:
            failures.append(label)

    for name, published in FILAMENTS.items():
        red, green, blue, alpha = tuple(filament(name))
        shown = "#%02X%02X%02X" % tuple(
            round(linear_to_srgb(channel) * 255) for channel in (red, green, blue)
        )
        check(f"{name} displays as {published}", shown == published and alpha == 1.0, shown)

    check(
        "name matching ignores case and separators",
        filament_hex("Dark Gray") == filament_hex("dark_gray") == filament_hex("DARK-GRAY"),
    )
    check("alpha reaches the Color", tuple(filament("cyan", 0.42))[3] == 0.42)

    try:
        filament("hot pink")
    except ValueError as exc:
        check("an unknown colour raises with the list", "sunflower yellow" in str(exc))
    else:
        check("an unknown colour raises with the list", False, "no error raised")

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
