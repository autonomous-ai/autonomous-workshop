# Exact display states

These STEP exports use the same production geometry as the assembled set. `before.step` contains White Kf6, Qh1 and Black Kf8; `after.step` changes only the queen to h8. `crowded.step` is the legal opening position after 1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.d3 d6, with spare queens beside the board.

The corresponding source helpers are `cad/before.py`, `cad/after.py`, and `cad/crowded.py`. Generate them with the CAD `gen` tool and move their auxiliary STEP exports into this directory before integrated verification; the CAD source directory reserves sibling STEP files for `*.step.py` entries. These views illustrate positions and digital geometry. They do not establish physical sliding, printing or full-game usability.
