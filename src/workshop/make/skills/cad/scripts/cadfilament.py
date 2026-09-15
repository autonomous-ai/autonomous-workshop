#!/usr/bin/env python
"""Filament colours — the stock this repository prints, by name.

A printed part can only be the colour of a spool somebody can load. Author a
colour as a free hex and the model shows a filament that does not exist: the
render looks decided, the STEP carries the decision into every downstream
reader, and nothing in the toolchain disagrees, because no gate here knows what
Bambu sells.

Pick from a palette instead, and the unbuyable colour becomes unrepresentable:

    from cadfilament import filament

    body.color = filament("sunflower yellow")                    # PLA Lite
    shell.color = filament("misty blue", material="PETG Basic")  # PETG Basic
    lens.color = filament("cyan", 0.42)                          # with alpha

An unknown name raises with the whole list rather than resolving to something
close, for the same reason `cadfits` derives the second half of a mate instead
of asserting it: a near-miss that still builds is the failure worth preventing.

Two stocks, two tables
----------------------
**Bambu Lab PLA Lite** (13 colours) is the default, read from
https://3dfilamentprofiles.com/filaments/bambu-lab/pla/lite on 2026-09-10.

**Bambu Lab PETG Basic** (13 colours) is the tougher, less brittle stock — a
part that flexes, takes an impact, or sits in a warm car. Its hex values come
from Bambu's own *Filament Hex Code Table — PETG Basic*, read 2026-09-15.

Hex values are as published; the trailing number is Bambu's colour code.

Seven names — black, white, gray, red, orange, yellow, green — are in both
tables, and five of them are a **different** hex in each (black and orange
happen to be the same colour in both stocks), so a name alone no longer
identifies a spool. `material` is what separates them, and it defaults to PLA
Lite, which is what every colour authored before PETG was stocked already meant.
Ask for a PETG-only colour without saying so and the error names the stock that
has it instead of guessing.

A PETG part printed in place also wants
`cadfits.print_in_place_gap(..., material="PETG")`: PETG strings and oozes more
than PLA, and its printed-together joints need the extra gap to come out free.

Colour that is deliberately not printed filament — a purchased component, a
reference surface, a see-through datum — is in neither table and belongs in
`cadgen.srgb("#rrggbb")`.

Retire or extend a table here and every project that reads it follows.

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

__all__ = ["DEFAULT_MATERIAL", "FILAMENTS", "MATERIALS", "filament", "filament_hex"]

# stock -> {colour name -> sRGB hex as published}. The comment on a colour is
# Bambu's colour code where the catalogue lists one. Keys are already in the
# form `_normalise` produces.
MATERIALS: dict[str, dict[str, str]] = {
    # Bambu Lab PLA Lite — the default stock.
    "pla lite": {
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
    },
    # Bambu Lab PETG Basic — tougher and less brittle than PLA.
    "petg basic": {
        "black": "#000000",             # 30105
        "dark beige": "#DBC8B6",        # 30403
        "dark brown": "#4F2C1D",        # 30800
        "gray": "#7F7E83",              # 30107
        "green": "#009639",             # 30502
        "misty blue": "#688197",        # 30108
        "navy blue": "#0086D6",         # 30604
        "orange": "#FF671F",            # 30302
        "pine green": "#034638",        # 30503
        "red": "#D6001C",               # 30201
        "reflex blue": "#001489",       # 30603
        "white": "#FFFFFF",             # 30106
        "yellow": "#FCE300",            # 30402
    },
}

#: The stock a colour comes from when the caller does not say.
DEFAULT_MATERIAL = "pla lite"

# Family shorthands. Exactly one PLA stock and one PETG stock are loaded here,
# so the family alone is unambiguous; stocking a second of either retires its
# shorthand rather than picking a winner behind the caller's back.
_MATERIAL_ALIASES: dict[str, str] = {"pla": "pla lite", "petg": "petg basic"}

_MATERIAL_LABELS: dict[str, str] = {
    "pla lite": "Bambu Lab PLA Lite",
    "petg basic": "Bambu Lab PETG Basic",
}

#: The default stock's table, under the name it carried when it was the only one.
FILAMENTS: dict[str, str] = MATERIALS[DEFAULT_MATERIAL]


def _normalise(name: str) -> str:
    return " ".join(name.replace("_", " ").replace("-", " ").lower().split())


def _resolve_material(material: str) -> str:
    """Return the table key for a stock name, or raise with the stocked list."""
    key = _normalise(material)
    key = _MATERIAL_ALIASES.get(key, key)
    if key not in MATERIALS:
        available = ", ".join(_MATERIAL_LABELS[stock] for stock in sorted(MATERIALS))
        raise ValueError(
            f"{material!r} is not a stock this repository prints; "
            f"choose one of: {available}"
        )
    return key


def filament_hex(name: str, *, material: str = DEFAULT_MATERIAL) -> str:
    """Return the sRGB hex of a palette colour, by name and stock.

    Matching ignores case, underscores, hyphens and repeated spaces, so
    ``"Dark Gray"``, ``"dark_gray"`` and ``"DARK-GRAY"`` are one colour, and
    ``"PETG Basic"``, ``"petg_basic"`` and ``"PETG"`` are one stock. ``material``
    defaults to PLA Lite. A name that is not in the requested stock raises with
    the full list of what can actually be printed in it, and says so explicitly
    when the other stock is the one that carries that colour.
    """
    stock = _resolve_material(material)
    palette = MATERIALS[stock]
    colour = _normalise(name)
    if colour in palette:
        return palette[colour]

    label = _MATERIAL_LABELS[stock]
    available = ", ".join(sorted(palette))
    elsewhere = [
        other
        for other in sorted(MATERIALS)
        if other != stock and colour in MATERIALS[other]
    ]
    if elsewhere:
        other = elsewhere[0]
        raise ValueError(
            f"{name!r} is not a {label} colour; it is a {_MATERIAL_LABELS[other]} "
            f"colour — pass material={other!r}. {label} has: {available}"
        )
    raise ValueError(f"{name!r} is not a {label} colour; choose one of: {available}")


def filament(name: str, alpha: float = 1.0, *, material: str = DEFAULT_MATERIAL):
    """Build a build123d ``Color`` from a palette colour name.

    The conversion is `cadgen.color.srgb`, so the channels come out linear and
    the part displays as the hex the catalogue publishes. Never hand a palette
    hex to ``Color()`` directly: those channels are linear RGB and a hex read
    into them renders washed out.
    """
    from cadgen.color import srgb

    return srgb(filament_hex(name, material=material), alpha)


def _self_check() -> int:
    """Round-trip every colour through the renderer's own conversion."""
    from cadgen.color import linear_to_srgb

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'}  {label}{f'  — {detail}' if detail else ''}")
        if not ok:
            failures.append(label)

    for stock, palette in MATERIALS.items():
        for name, published in palette.items():
            red, green, blue, alpha = tuple(filament(name, material=stock))
            shown = "#%02X%02X%02X" % tuple(
                round(linear_to_srgb(channel) * 255) for channel in (red, green, blue)
            )
            check(
                f"{stock}: {name} displays as {published}",
                shown == published and alpha == 1.0,
                shown,
            )

    check(
        "name matching ignores case and separators",
        filament_hex("Dark Gray") == filament_hex("dark_gray") == filament_hex("DARK-GRAY"),
    )
    check("alpha reaches the Color", tuple(filament("cyan", 0.42))[3] == 0.42)
    check("the default stock is PLA Lite", filament_hex("red") == FILAMENTS["red"])
    check(
        "stock names match case, separators and family shorthand",
        filament_hex("black", material="PETG Basic")
        == filament_hex("black", material="petg_basic")
        == filament_hex("black", material="PETG"),
    )

    shared = sorted(set(MATERIALS["pla lite"]) & set(MATERIALS["petg basic"]))
    check(
        "a name in both stocks reads the stock it was asked for",
        all(
            filament_hex(name, material=stock) == MATERIALS[stock][name]
            for name in shared
            for stock in MATERIALS
        ),
        f"in both: {', '.join(shared)}",
    )
    differing = [
        name
        for name in shared
        if MATERIALS["pla lite"][name] != MATERIALS["petg basic"][name]
    ]
    check(
        "most of those are a different spool in each stock",
        differing == ["gray", "green", "red", "white", "yellow"],
        f"differ: {', '.join(differing)}",
    )

    try:
        filament("hot pink")
    except ValueError as exc:
        check("an unknown colour raises with the list", "sunflower yellow" in str(exc))
    else:
        check("an unknown colour raises with the list", False, "no error raised")

    try:
        filament("misty blue")
    except ValueError as exc:
        check(
            "a colour from the other stock names that stock",
            "petg basic" in str(exc),
            str(exc),
        )
    else:
        check("a colour from the other stock names that stock", False, "no error raised")

    try:
        filament("black", material="nylon")
    except ValueError as exc:
        check("an unstocked material raises with the list", "PETG Basic" in str(exc))
    else:
        check("an unstocked material raises with the list", False, "no error raised")

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
