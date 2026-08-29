# Saigon Skyline Chess CAD project

This STEP-first build contains a 208 mm one-piece relief board and twelve unique architectural chess-piece variants: six building silhouettes in a round `river` plinth language and six in a square `grid` plinth language. Standard chess uses sixteen physical pieces per side, so pawns and major/minor pieces are printed in the orthodox quantities listed below.

The combined `saigon_chess.step.py` entry is a labelled, deliberately uncoloured play configuration and declares `PRINTABLE = False`. Omitting per-occurrence display colours keeps the STEP presentation section deterministic across fresh isolated exports; the round and square plinths carry side identity without colour. Every `part_*.step.py` entry is a bed-oriented printable part. The product uses independent chess components with no purchased parts, electrical loads, joints, fasteners, constrained insertion path, or retention mechanism.

The product root packages the final review assembly as `assembled.step`, a 33-shell `assembled.stl`, and self-contained `assembled.step.json` metadata whose hashes bind those exact two files. `snap/` contains regenerated whole-set silhouettes; `snap/pieces/queen/` and `snap/pieces/grid_queen/` show the repaired supported sky deck with the round and square side languages, while `snap/pieces/grid_rook/` supplies a second square-plinth reference.

Print inventory:

- `part_board`: 1
- each side's pawn: 8
- each side's rook, knight, and bishop: 2 each
- each side's queen and king: 1 each

Recommended digital slicing assumptions: PLA; 0.4 mm nozzle; 0.20 mm layer; at least two perimeters; upright stance exactly as exported. The project declares a `--bed 220x220x220`. The board is close to the bed envelope and should be centred by the slicer. These are CAD assumptions only; no physical print, fit, durability, or human play result is claimed.

Rebuild from the run workspace with `XDG_CACHE_HOME` pointed inside the workspace:

```text
python .agents/skills/cad/scripts/verify_project artifacts/make/r0001/product/cad --assembly saigon_chess.step.py --exports --strict-fit --bed 220x220x220 --nozzle 0.4
```
