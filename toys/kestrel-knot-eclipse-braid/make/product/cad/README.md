# Eclipse Braid CAD project

One-piece, print-in-place desk toy comprising a connected frame/rail body and
one separate captive crescent runner. There is no post-print assembly and no
hidden support-removal operation. Visible slender support posts pass through
the runner's lower opening; that opening is wider than each post but narrower
than the rail, so the runner remains captive.

CAD brief:

- Model: Eclipse Braid, a two-solid print-in-place moving object.
- Units: millimetres.
- Coordinate convention: XY desk plane, origin at frame centre, +Z upward.
- Verified overall envelope: 116 × 84 × 25.986 mm.
- Route: one periodic 3D spline with two projected crossings at X = ±17 mm.
- Crossings: alternate elevated strands, low rail Z 10.4 mm, high rail Z 23.8 mm.
- Runner: squared crescent/C collar, 12 mm outer span, 6.8 mm inner window,
  2.6 mm walls, and 3.6 mm axial length.
- Capture: 2.4 mm runner opening over 1.5 mm support posts and a 4.4 mm rail.
- Materials/process: assumed PLA or PETG, 0.4 mm nozzle, 0.20 mm layers.
- Print stance: frame flat on XY bed; no supports; bridge spans are visible.
- Printer bed: `--bed 220x220x220`.
- Printed target: `eclipse_braid.step.py` (`PRINTABLE = True`).
- Primary output: STEP; secondary output: STL exported from that final STEP.
- Validation: layout, fit, spec algebra, route traversal, STEP refs/validate,
  assembly interference, mesh integrity, wall thickness, and direct renders.

The two bodies are intentionally disconnected in the export because the
runner must move. `check_mesh` is therefore evaluated as an assembly mesh. CAD
checks are digital evidence only: no successful physical print, friction,
durability, or human response is claimed.
