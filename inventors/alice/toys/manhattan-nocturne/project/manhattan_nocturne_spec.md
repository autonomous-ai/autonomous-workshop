# Manhattan Nocturne Chess — product build specification

Status: **HELD — digital prototype in Make. Deliver requires physical evidence.**

## Product intent

- User and job: an adult chess player wants an original NYC architectural set
  striking enough to leave out and conventional enough to play without coaching.
- Interaction and environment: indoor tabletop play, repeated pickup/capture,
  one-piece board setup, storage between games.
- Age/safety boundary: collectible for ages 14+; not a children's toy. Small
  pieces and pointed silhouettes are choking/poke risks for young children.
- Out of scope: novel rules, structural certification, food contact, outdoor
  exposure, exact landmark reproduction, and untested durability claims.

## Visual intent

- Three adjectives: nocturnal, architectural, heirloom.
- Scale anchor: 28.5 mm chess square; assembled envelope 244 × 244 × 83.35 mm
  in the initial position, including board and tallest placed piece.
- Primary forms: an immediate checker field made from 32 isolated sloped light
  pads over one continuous dark base, six unmistakable rank silhouettes, and
  Stone and Steel armies with different façade rhythm.
- Secondary forms: Manhattan setbacks, masonry bands, vertical fins, parapets,
  water towers, seven sloped file/rank street dashes in each outer border, and
  one true diagonal Broadway cue contained within the south border.
- Detail forms: printable grooves and windows, never required for rank recognition.
- Seams: none across the playing surface; every light pad overlaps and fuses
  into the same base, so the board remains one printed solid.
- Material/color breaks: the continuous base is midnight through Z8.20; only
  the 32 isolated light pads above that exact plane receive a warm brass/gold
  contrast. Stone and Steel remain visually distinct in neutral grayscale;
  board parity is judged with the required production finish while one-material
  raw views remain available as engineering evidence.
- Forbidden shortcuts: see `../art-direction/ART-DIRECTION.md`.
- Frozen canonical target: `../art-direction/directions-v1.png`; mood only. Its
  SHA-256 is sealed during the first Make receipt.

## CAD brief

- Model: multipart 8×8 chess set and starting-position assembly.
- Task: new STEP-first product plus STL outputs.
- Units: millimetres.
- Coordinates: board centered at world XY origin; +Z is up. Every printable
  part has its bed datum at Z=0.
- Overall board: 244 × 244 × 9.0 mm, one piece on a 256 mm bed.
- Functional features: 64 readable squares from native sloped-face shading,
  25.0 mm light-square top landings, 32 stable pieces, tactile side coding,
  rank-specific silhouettes, and support-conscious details.
- Standard mechanical components: none. No fasteners, bearings, magnets, or
  purchased components are used, so no STEP-parts catalog form is triggered.
- Validation: exact inventory, bounding boxes, positive-volume solids, strict
  meshes, assembly interference, rank/side recognition, base clearance,
  stability proxy, bed packing, and pinned-slicer results.

## Manufacturing envelope

- Process: assumed FDM in PLA for exploration.
- Machine: Bambu Lab P2S exploration envelope, 256 × 256 × 256 mm; exact
  machine serial and physical calibration are not yet bound.
- Nozzle/layer: assumed 0.4 mm nozzle and 0.20 mm layer for exploration only.
- Measured extrusion width: unknown; held for calibration.
- Supports: target support-free unique pieces and the one-piece board. Slicer output
  decides; no claim is made from geometry alone.
- Finish: required midnight base plus warm brass/gold light-square family. Use
  either one BOARD-only material change after the completed Z8.20 layer, or
  mask every surface at/below Z8.20 and apply the contrasting top finish only
  to exposed pad slopes and tops. Execution remains unverified until Deliver.
- Texture: none added. The real 0.80 mm bevel supplies light response, while
  each flat 25.0 mm landing stays stable under a D22.5 piece base.
- Post-processing: finish cannot rescue failed geometry, fit, or print quality.
- Target mass/time/cost: to be recorded from the pinned slicer, not guessed.

## Part inventory

| Stable ID | Qty | Purpose | Material | Canonical source | Expected solids | Print orientation |
|---|---:|---|---|---|---:|---|
| BOARD | 1 | Seamless 8×8 board | PLA | `part_board.step.py` | 1 | flat, top up |
| STONE-P | 8 | Stone pawns | PLA | `part_stone_pawn.step.py` | 1 | upright |
| STONE-R | 2 | Stone rooks | PLA | `part_stone_rook.step.py` | 1 | upright |
| STONE-N | 2 | Stone knights | PLA | `part_stone_knight.step.py` | 1 | upright |
| STONE-B | 2 | Stone bishops | PLA | `part_stone_bishop.step.py` | 1 | upright |
| STONE-Q | 1 | Stone queen | PLA | `part_stone_queen.step.py` | 1 | upright |
| STONE-K | 1 | Stone king | PLA | `part_stone_king.step.py` | 1 | upright |
| STEEL-P | 8 | Steel pawns | PLA | `part_steel_pawn.step.py` | 1 | upright |
| STEEL-R | 2 | Steel rooks | PLA | `part_steel_rook.step.py` | 1 | upright |
| STEEL-N | 2 | Steel knights | PLA | `part_steel_knight.step.py` | 1 | upright |
| STEEL-B | 2 | Steel bishops | PLA | `part_steel_bishop.step.py` | 1 | upright |
| STEEL-Q | 1 | Steel queen | PLA | `part_steel_queen.step.py` | 1 | upright |
| STEEL-K | 1 | Steel king | PLA | `part_steel_king.step.py` | 1 | upright |

## Controlled parameters

| Parameter | Nominal/range/unit | Provenance | Confidence | Owner | Dependents |
|---|---|---|---|---|---|
| `square_pitch` | 28.5 mm | assumed | high | `params.py` | board, placements, base limit |
| `outer_border` | 8.0 mm | derived | high | `params.py` | 244 mm board envelope |
| `board_total_height` | 9.00 mm | assumed | high | `params.py` | preserved board envelope |
| `square_relief` | 0.80 mm | assumed | high | `params.py` | four 0.20 mm layers, grid readability |
| `board_thickness` | 8.20 mm | derived | high | `params.py` | continuous one-piece dark base |
| `light_pad_lower_size` | 27.40 mm | exploration | medium | `params.py` | embedded footprint and visible slope |
| `light_pad_top_size` | 25.00 mm | derived | high | `params.py` | 1.25 mm landing around D22.5 base |
| `light_pad_embed` | 0.20 mm | exploration | medium | `params.py` | avoids coplanar/point-only pad contact |
| `border_street_groove` | 2.00→1.20 × 0.80 mm | exploration | medium | `params.py` | sloped file/rank dashes and Broadway cue |
| `finish_boundary_z` | 8.20 mm | derived | high | `params.py` + `validation/finish-plan.json` | exact midnight/brass material plane |
| `board_base_finish` | midnight | assumed | medium | `validation/finish-plan.json` | continuous base at/below Z8.20 |
| `light_pad_finish` | warm brass/gold | assumed | medium | `validation/finish-plan.json` | only 32 isolated pads above Z8.20 |
| `max_base_diameter` | 22.5 mm | derived | high | `params.py` | adjacent clearance |
| `min_wall` | 1.2 mm | exploration | low | `params.py` | façade/crown details |
| `min_free_feature` | 2.2 mm | exploration | low | `params.py` | king finial, fins |

All piece dimensions and their provenance are defined once in `params.py`.
Every mate derives both sides from one nominal dimension and applies clearance
only to the receiving feature.

## Finish contract

`validation/finish-plan.json` is the deterministic manufacturing contract and
`validation/check_finish.py` is its gate. The checker seals all 27 canonical
STEP/STL artifacts, proves one connected base below Z8.20, proves exactly 32
isolated light-pad solids above Z8.20, verifies a1 remains dark, and rejects any
finish plan that targets piece artifacts or adds landing texture.

The finish is a real manufacturing operation, not a render material. Deliver
must select exactly one documented method: a BOARD-only filament/material
change after completing Z8.20, or a mask at that plane followed by warm
brass/gold finish on the exposed pad slopes and tops. Actual color, adhesion,
registration, wear, and piece stability remain unverified until physical
Deliver evidence exists.

## Fits and contacts

There are no printed mates, connectors, fasteners, or moving joints in this
revision. This follows the one-part default for the board and removes fit claims
that would otherwise require physical calibration.

| Pair | Surfaces | Class | Coupon | Load | Evidence |
|---|---|---|---|---|---|
| piece/board | flat base/square | planar contact | n/a | gravity/pickup | flatness + placement/interference |

## Motion and interference

- Every chess piece moves by vertical lift before legal chess translation; AI
  Players test collision-free lift proxies in crowded positions.
- No connector or retention claim is made.
- Compliance, friction, fatigue, impact, warp, tactile feel, and tip resistance
  remain physical Deliver claims.

## Assembly

1. Place the board with a light square at each player's right hand.
2. Confirm the complete 8×8 grid.
3. Place each side's back rank rook, knight, bishop, queen, king, bishop, knight,
   rook; the queen starts on her own color.
4. Place eight pawns on the rank in front.

## AI Playtest gates

Every immutable round seals the exact CAD artifact hash and emits all four
required Workshop results: `agent-playtest`, `classic-rules-test`,
`mechanical-test`, and `print-test`, each as `evidence_class=ai-simulation`.
Deterministic CAD and slicer receipts are nested as hashed source records.

| Gate | Acceptance | Substrate | Initial status |
|---|---|---|---|
| Manifest | exact 1 board + 32 pieces; current hashes | deterministic | held |
| B-rep | every canonical output valid, closed, positive volume | deterministic | held |
| Mesh | every STL watertight; zero non-manifold edges | deterministic | held |
| Dimensions | 244 mm board; parts within 256 mm bed; no out-of-tolerance target | deterministic | held |
| Interference | zero forbidden overlaps in starting assembly | deterministic | held |
| Bed packing | exact quantities assigned to board and army plates within 256 mm | deterministic | held |
| Slicer | all unique outputs slice; errors 0; support grams recorded | slicer | held |
| Finish plan | Z8.20 boundary; 32 brass/gold pads only; geometry seal unchanged | deterministic | held |
| Recognition | aggregate rank ≥95%; no rank <90%; king/queen 100% | AI Players | held |
| Side identity | 100% side recognition in neutral material | AI Players | held |
| Chess fidelity | 64 squares, exact inventory/setup, unchanged rules | AI Players | held |
| Form/beauty | ≥6 canonical views; blockers 0 | independent review | held |
| Safety | hazards 0 within 14+ collectible scope | independent review | held |

## Deliver gates

Physical printing, selected coupon clearance, bed flatness, real tip behavior,
surface quality, hand comfort, durability, packing completeness, and shipping
remain held until bound to exact produced artifacts and operator receipts.

## Bounds and unresolved claims

- Maximum five AI Playtest repair rounds for this Make.
- Maximum two CAD repair passes per failed deterministic gate before reporting
  the remaining failure honestly.
- No untested connector or board-locking claim.
- No physical-print claim, human-fun claim, or durability claim in this Make.
