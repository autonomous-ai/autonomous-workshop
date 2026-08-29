# Saigon Skyline Chess — CAD brief

- Model: one orthodox chess set with an 8 × 8 relief board and 32 separately printable architectural pieces.
- Task type: new static multi-part product; no purchased parts, fasteners, powered loads, or fit-critical mates.
- Units: millimetres.
- Coordinate convention: every print part has its footprint centred on XY, bed at Z=0, and +Z upward. The play assembly centres the board at the origin.
- Board: 208 × 208 × 4.0 maximum, including a 4 mm perimeter; playable grid 200 × 200 with 25 mm squares. Alternating squares are encoded by 0.4 mm relief islands inset 0.4 mm per edge, so the state is legible without colour and diagonal islands do not create non-manifold point contacts.
- Piece family: bases fit inside an 18 × 18 mm envelope. River side has circular stepped plinths; Grid side has square stepped plinths. Building silhouettes are shared so both sides preserve the same orthodox rank hierarchy.
- Piece mapping and target height: pawn / Saigon Central Post Office 28 mm; rook / Bến Thành Market 34 mm; knight / Independence Palace 38 mm; bishop / Notre-Dame Cathedral Basilica of Saigon 43 mm; queen / Bitexco Financial Tower 49 mm; king / Landmark 81 55 mm.
- Construction: monolithic overlapping build123d primitives intended for support-free slicing at the default upright print stance. The 4.8 mm diameter × 3.2 mm Bitexco sky-deck disc is carried by an integral 2.4 × 2.6 mm pier that overlaps both the tower and upper plinth; separating the deck from the taper avoids a knife-edge boolean junction. Fine façade ornament, text, clock numerals, and exact architectural scale are deliberately omitted.
- Manufacturing assumption: FDM PLA, 0.4 mm nozzle, 0.20 mm layers, two or more perimeters; default bed 220 × 220 × 220 mm. This is a digital print-readiness assumption, not evidence of a physical print.
- Assembly: the combined entry is a labelled, uncoloured review configuration with pieces placed in the orthodox initial position; both Independence Palace canopies face inward toward the opposing army. Omitting display colours makes isolated fresh STEP export deterministic while the two plinth geometries preserve side identity. It is not a single print target and has no mechanical mating operation.
- Paths: `saigon_chess.step.py` produces the combined STEP; `part_*.step.py` entries produce each unique printable variant; exports sit beside their generators.
- Validation targets: layout gate; all 13 unique print entries on the declared bed; project-specific dimensions and inventory; combined STEP refs, topology validation, and interference; mesh and 0.4 mm nozzle thickness checks for every exported print target.
- Assumptions: architecture is stylised from public landmark silhouettes, not a measured reconstruction; pigment can enhance presentation but all meaningful side/square distinctions remain geometric.
