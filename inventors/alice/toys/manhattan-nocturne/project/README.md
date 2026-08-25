# Manhattan Nocturne CAD project

STEP-first source for Alice's one-piece-board NYC architectural chess set.
The twelve canonical piece entries differ geometrically, not just by color:
Stone uses horizontal masonry bands and one base groove; Steel uses vertical
structural fins and two tactile channels between three broad base rails.

## Source map

- `params.py` — every controlled dimension and its provenance.
- `manhattan_nocturne_lib.py` — board and six role builders plus tactile side coding.
- `manhattan_nocturne.step.py` — board and 32 labeled occurrences in the standard starting position.
- `assembled.stl` — Factory's canonical whole-product mesh, with all 33 occurrences already placed.
- `assembled.step.json` — Factory's occurrence-order map for coloring that combined mesh.
- `part_board.step.py` — one seamless 244 mm board, printable at Z=0.
- `part_<side>_<role>.step.py` — twelve unique printable piece variants at Z=0.
- `manhattan_nocturne_spec.md` — intent, manufacturing boundary, and evidence gates.
- `validation/finish-plan.json` — required midnight/brass material boundary.
- `validation/check_finish.py` — read-only proof that only the 32 light pads continue above Z8.20.
- `validation/check_factory_handoff.py` — proves Factory receives one board and 32 ordered, placed pieces.

The combined assembly has 33 labeled occurrences: one board and 32 pieces.
The board is 244 × 244 × 9.0 mm. Piece heights are 44.0–74.35 mm and all bases
are at most 22.5 mm across for a 28.5 mm square pitch.

`assembled.stl` deliberately lives at the project root. Factory ranks that exact
name above loose part meshes when it creates the viewer GLB and product imagery.
The sibling sidecar preserves the `.add()` order from the combined source, so
the board and every placed piece receive the intended renderer part index.
There is intentionally no `_panda_artifact.json`: that verified-family schema
requires each part path to be unique, while this chess assembly has repeated
occurrences of twelve canonical piece meshes. Factory's supported sidecar path
is the truthful 33-occurrence contract for this product.

## Rebuild

Run from the repository root with the project Python environment:

```text
.venv-cad/bin/python skills/cad/scripts/check_layout inventors/alice/toys/manhattan-nocturne/project
.venv-cad/bin/python inventors/alice/toys/manhattan-nocturne/project/measure/check_fit.py
.venv-cad/bin/python skills/cad/scripts/check_fit inventors/alice/toys/manhattan-nocturne/project --bed 256 256 --strict

.venv-cad/bin/python skills/cad/scripts/gen \
  inventors/alice/toys/manhattan-nocturne/project/manhattan_nocturne.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_board.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_pawn.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_rook.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_knight.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_bishop.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_queen.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_stone_king.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_pawn.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_rook.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_knight.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_bishop.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_queen.step.py \
  inventors/alice/toys/manhattan-nocturne/project/part_steel_king.step.py \
  --write

.venv-cad/bin/python skills/cad/scripts/export \
  inventors/alice/toys/manhattan-nocturne/project/manhattan_nocturne.step.py \
  --stl assembled.stl
```

Generation proves only that the parametric B-reps were created. Printability,
surface quality, tactile feel, durability, and real stability remain held until
the pinned slicer and physical Deliver evidence exist.

The checked-in final digital gate also runs `check_mesh` and
`check_thickness --nozzle 0.4` on all thirteen fine-mesh STL exports. See
`validation/slicer-receipt.json` and `validation/thickness-reports/`. These are
digital manufacturing checks, not proof of a successful physical print.

The required board finish is likewise a digital manufacturing contract, not a
photograph or physical receipt. It can be executed as one BOARD-only material
change after the completed Z8.20 layer or as a masked top finish; Deliver must
verify the chosen process, color, adhesion, registration, and wear.
