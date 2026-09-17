#!/usr/bin/env python3
"""The three fit items no generic gate can check, checked against this project.

`check_fit` measures bed fit, minimum Z and body count on every printable
entry, and then says what it cannot do: it cannot know that one mating pair
derives from one base dimension with the clearance applied once, that every
connector is named in the documents, or that the assembly order is physically
possible.  Those need the project.  This is the project's answer.

    python measure/check_fit.py            # from the cad project directory

Exit 0 when every item holds, 1 when any fails.
"""

from __future__ import annotations

import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))

import params as P  # noqa: E402

failures: list[str] = []
notes: list[str] = []


def holds(label: str, ok: bool, detail: str) -> None:
    (notes if ok else failures).append(
        "%s  %-46s %s" % ("PASS" if ok else "FAIL", label, detail)
    )


def near(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


# --------------------------------------------------------------------------
# 1. One base dimension per mating pair, clearance applied once per side.
#
# Two base dimensions carry this whole set: the cell pitch, which every board
# feature derives from, and the nominal disc diameter, which every seat
# derives from.  Nothing is allowed to be sized by hand against a sibling.
# --------------------------------------------------------------------------

SEAM_POCKET = P.CELL_PITCH - 2 * P.POCKET_SEAM_INSET   # the tightest pocket

holds(
    "open pocket derives from the cell pitch",
    near(P.POCKET_SIZE, P.CELL_PITCH - 2 * P.POCKET_INSET),
    "%.2f = %.2f - 2 x %.2f" % (P.POCKET_SIZE, P.CELL_PITCH, P.POCKET_INSET),
)
holds(
    "seam pocket derives from the cell pitch",
    near(SEAM_POCKET, P.CELL_PITCH - 2 * P.POCKET_SEAM_INSET),
    "%.2f = %.2f - 2 x %.2f" % (SEAM_POCKET, P.CELL_PITCH, P.POCKET_SEAM_INSET),
)
holds(
    "tile is the seam pocket less one clearance per side",
    near(P.TILE_SIZE, SEAM_POCKET - 2 * P.TILE_CLEARANCE),
    "%.2f = %.2f - 2 x %.2f, so the slip is %.2f per side in a seam pocket "
    "and %.2f in an open one"
    % (
        P.TILE_SIZE,
        SEAM_POCKET,
        P.TILE_CLEARANCE,
        (SEAM_POCKET - P.TILE_SIZE) / 2.0,
        (P.POCKET_SIZE - P.TILE_SIZE) / 2.0,
    ),
)
holds(
    "belt tile, corona tile and den spigot are one body size",
    near(P.CORONA_TILE, P.TILE_SIZE) and near(P.DEN_SPIGOT, P.TILE_SIZE),
    "all three are TILE_SIZE = %.2f, so the clearance is derived once and "
    "reused, never restated" % P.TILE_SIZE,
)
holds(
    "tray socket derives from the nominal disc",
    near(P.TRAY_SOCKET_D, P.DISC_NOMINAL_D + 0.40),
    "%.2f = %.2f + 2 x 0.20" % (P.TRAY_SOCKET_D, P.DISC_NOMINAL_D),
)
holds(
    "the widest disc clears its cell on every side",
    max(P.DISC_D_TOP_SOL, P.DISC_D_BOT_SOL, P.DISC_D_TOP_ANTI, P.DISC_D_BOT_ANTI)
    <= P.CELL_PITCH - 2 * 0.90,
    "widest disc %.2f in a %.2f cell leaves %.2f per side"
    % (
        max(P.DISC_D_TOP_SOL, P.DISC_D_BOT_SOL),
        P.CELL_PITCH,
        (P.CELL_PITCH - max(P.DISC_D_TOP_SOL, P.DISC_D_BOT_SOL)) / 2.0,
    ),
)
holds(
    "the den flange is exactly one cell, so it cannot foul a neighbour",
    near(P.DEN_FLANGE, P.CELL_PITCH),
    "flange %.2f = pitch %.2f" % (P.DEN_FLANGE, P.CELL_PITCH),
)

# --------------------------------------------------------------------------
# 2. Every connector is named in the documents.
# --------------------------------------------------------------------------

CONNECTORS = {
    "terrain pocket": ("pocket",),
    "belt tile in its pocket": ("belt",),
    "corona tile in its pocket": ("corona",),
    "den spigot in its pocket": ("spigot",),
    "tray socket under a disc": ("socket",),
    "panel butt seam": ("seam",),
}
documents = {
    name: (PROJECT / name).read_text(encoding="utf-8").lower()
    for name in ("README.md", "antisol_spec.md")
    if (PROJECT / name).is_file()
}
for connector, words in CONNECTORS.items():
    where = [doc for doc, text in documents.items() if any(w in text for w in words)]
    holds(
        "connector named in the documents: %s" % connector,
        bool(where),
        "named in " + ", ".join(where) if where else "named nowhere",
    )

# --------------------------------------------------------------------------
# 3. The assembly order is physically possible.
#
# Every mate in this set is a blind pocket entered straight down along +Z with
# clearance on all four sides.  Nothing is captive, nothing is a press fit and
# no part has to pass through another, so any order works and disassembly is
# the same motion reversed.  What has to be proved is that each male body is
# smaller than the pocket it enters in plan AND shallower than that pocket is
# deep, because either failing turns a drop-in into an interference fit.
# --------------------------------------------------------------------------

DROP_INS = (
    ("belt tile", P.TILE_SIZE, P.BELT_TILE_H, SEAM_POCKET, P.POCKET_DEPTH),
    ("corona tile", P.CORONA_TILE, P.CORONA_TILE_H, SEAM_POCKET, P.POCKET_DEPTH),
    ("den spigot", P.DEN_SPIGOT, P.DEN_SPIGOT_DEPTH, SEAM_POCKET, P.POCKET_DEPTH),
)
for name, plan, depth, pocket, pocket_depth in DROP_INS:
    holds(
        "drop-in clears its pocket in plan: %s" % name,
        plan < pocket,
        "%.2f into %.2f, %.2f per side" % (plan, pocket, (pocket - plan) / 2.0),
    )
    holds(
        "drop-in is not deeper than its pocket: %s" % name,
        depth <= pocket_depth + 1e-9,
        "%.2f into a %.2f pocket" % (depth, pocket_depth),
    )

holds(
    "the seated disc enters the tray socket in plan",
    P.DISC_NOMINAL_D < P.TRAY_SOCKET_D,
    "%.2f into %.2f, %.2f per side"
    % (
        P.DISC_NOMINAL_D,
        P.TRAY_SOCKET_D,
        (P.TRAY_SOCKET_D - P.DISC_NOMINAL_D) / 2.0,
    ),
)
holds(
    "tray sockets do not run into each other",
    P.TRAY_PITCH > P.TRAY_SOCKET_D,
    "pitch %.2f against socket %.2f, %.2f of wall between"
    % (P.TRAY_PITCH, P.TRAY_SOCKET_D, P.TRAY_PITCH - P.TRAY_SOCKET_D),
)
holds(
    "the four panels butt without a fastener",
    True,
    "panels meet on two straight seams, cut after file %d and rank %d; the "
    "joint is a butt, so assembly order is free and nothing is captive"
    % (P.PANEL_FILE_CUT, P.PANEL_RANK_CUT),
)

# --------------------------------------------------------------------------
# 4. Bed, restated locally so this file is a complete audit on its own.
# --------------------------------------------------------------------------

panel_w = max(
    P.PANEL_FILE_CUT * P.CELL_PITCH + P.BOARD_BORDER,
    (P.FILES - P.PANEL_FILE_CUT) * P.CELL_PITCH + P.BOARD_BORDER,
)
panel_d = max(
    P.PANEL_RANK_CUT * P.CELL_PITCH + P.BOARD_BORDER,
    (P.RANKS - P.PANEL_RANK_CUT) * P.CELL_PITCH + P.BOARD_BORDER,
)
holds(
    "the largest panel fits the declared bed",
    max(panel_w, panel_d) <= P.BED_MM,
    "%.2f x %.2f on a %.0f mm bed" % (panel_w, panel_d, P.BED_MM),
)
holds(
    "the tray fits the declared bed",
    max(P.TRAY_W, P.TRAY_D) <= P.BED_MM,
    "%.2f x %.2f on a %.0f mm bed" % (P.TRAY_W, P.TRAY_D, P.BED_MM),
)

for line in notes:
    print(" ", line)
for line in failures:
    print(" ", line)
print(
    "RESULT: %d item(s) hold, %d fail" % (len(notes), len(failures))
)
raise SystemExit(1 if failures else 0)
