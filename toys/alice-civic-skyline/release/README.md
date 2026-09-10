# Civic Skyline

A complete standard chess set whose skyline shares one civic ground. Empire State, Chrysler and Flatiron towers rise above the same stepped octagonal plinths as bridge towers, city horses and rooftop water tanks. Around the board, five original relief passages connect researched architectural and cultural references from Chinatown, Williamsburg, the Bronx, Staten Island and Queens.

![The exact CAD assembly and starting position](cad/snap/iso.png)

![Role forms and the civic border from the exact CAD](cad/snap/signature.png)

These are digital CAD illustrations. The package contains model geometry, printable part files and digital engineering evidence. It does not document a physical print, a durability test or a human playtest. Check results and recorded limitations are described in `cad/measure/verification-pipeline.md`; the source-level design specification is `cad/city_spec.md`.

## Print inventory

Print at 100% scale in millimetres. There are **32 chessmen, four board panels and 32 dark square inlays: 68 printed objects**. The assembled board is 384 × 384 mm with 42 mm squares and a 24 mm perimeter frame. Each 192 × 192 mm panel fits individually on the declared 220 × 220 × 220 mm build volume.

| Part family | Light army | Dark army | Other quantity | Nominal size, mm |
|---|---:|---:|---:|---|
| Empire State king | 1 | 1 | — | 86 high; 32 circumscribed base diameter |
| Chrysler queen | 1 | 1 | — | 76 high; 32 circumscribed base diameter |
| Flatiron bishop | 2 | 2 | — | 64 high; 30 circumscribed base diameter |
| City Horse knight | 2 | 2 | — | 58 high; 30 circumscribed base diameter |
| Brooklyn Bridge rook | 2 | 2 | — | 52 high; 30 circumscribed base diameter |
| Rooftop Tank pawn | 8 | 8 | — | 40 high; 26 circumscribed base diameter |
| Board panel `board_0_0`, `board_1_0`, `board_0_1`, `board_1_1` | — | — | 1 of each | 192 × 192 × 6.2 maximum, including relief |
| Dark square tile | — | — | 32 | 41.5 × 41.5 × 2.6; 2 mm chamfered corners |

The octagonal bases are slightly narrower across their flats than their stated circumscribed diameters. Both armies have identical role geometry. Choose strongly contrasting materials, such as warm ivory and dark blue-green, so side identity remains clear across the table. Print all board panels in the light material and all square inlays in the dark material. STL does not carry color; assign material in the slicer. No multimaterial printer is required.

Use the individually named files in `parts/` to print one complete inventory. Their names identify each starting square, for example `ivory_king_e1.stl` or `midnight_rook_a8.stl`. The single family files in `cad/`, such as `part_queen.stl`, are convenient for replacements and additional promotion pieces. Do not print both inventories. The combined `assembled.stl` is an assembly illustration and reference, not a one-piece print job. `print-families.json` maps the eleven geometry families to these 68 named objects; each representative is already included in that inventory.

## Printing and finishing

1. Start with a calibrated 0.4 mm nozzle, 0.2 mm layer height and the filament maker's temperature settings. PLA is a reasonable first trial; these settings are starting guidance rather than a tested printer profile. Use consistent material and settings for the matching armies.
2. Keep the supplied print orientation: chessmen upright on their broad bases, panels flat with relief upward, and tiles flat. Check each slicer preview for continuous walls and missing detail before printing.
3. Start with three perimeter walls, four top and bottom layers and approximately 20% infill. More infill in the lower plinth can improve mass distribution, but requires an actual printed stability check. Do not add weight cavities or metal inserts without revising and checking the model.
4. Print one tile and one panel first to check the nominal clearance on your machine. The 41.5 mm tile has 2 mm chamfered corners and is designed to fit each 42 mm pocket. Pockets have matching chamfers inside each panel and square openings at panel seams. The total straight-edge clearance is 0.5 mm, or 0.25 mm per side when centered. Material shrinkage, elephant's foot and bed flatness can change the result. Tiles should lower freely without force.
5. Use a brim only when needed for adhesion; leave adequate bed margin around the 192 mm panels. Inspect the knight's muzzle, setbacks, roofs and blind recesses in the slicer. Passing geometric overhang checks does not guarantee the same result with every material, cooling setting or printer; no universal support-free claim is made.
6. Remove brims and any supports carefully. Clear burrs from the underside edges; do not round away the flat standing surfaces. Avoid loading the king's cross, the queen's tip or the knight's ears. Grasp each piece around its main body below the crown.
7. Place each finished chessman on a flat table and check for rocking. Check that the board panels lie flat and the inlays finish flush with the light squares. Resolve visible distortion or rough seating before play. CAD checks do not replace this physical inspection.

A completed piece is intended to be solid externally, with internal infill selected in the slicer. The CAD center-of-mass calculation assumes uniform solid material; it is a comparison of geometry, not a measurement of the printed object's mass distribution or resistance to knocks.

## Board assembly

Work on a level, nonslip table. The panels simply lie adjacent; there are no clips, screws, magnets, glue joints or carrying locks. Keep the board on the table during play and separate it before carrying it.

View the board from the light player's side. Arrange the four panel filenames as follows, with their decorated outer edges facing outward:

```text
                    DARK PLAYER
          a–d files               e–h files
      +-------------------+-------------------+
      | board_0_1         | board_1_1         |
      | ranks 5–8         | ranks 5–8         |
      | Bronx at top      | Queens at right   |
      +-------------------+-------------------+
      | board_0_0         | board_1_0         |
      | ranks 1–4         | ranks 1–4         |
      | Williamsburg left| Staten Island     |
      | Chinatown below  | ferry below       |
      +-------------------+-------------------+
                    LIGHT PLAYER
```

Bring the straight inner panel edges together so all eight files and ranks line up. Place one dark inlay in each recessed square, lowering it vertically. There are eight inlays per panel, and all pockets are designed for the same inlay shape. Each pocket has a 2.4 mm backing floor, and the tile top is nominally flush with the 5 mm playing surface. Small gaps at the chamfered inlay corners along panel seams are intentional. Inlays remain loose and can lift out vertically; there is no retention feature. At panel seams, keep the panels together while placing the nearby inlays.

The near-right square for the light player, **h1**, must be light. The near-left square, **a1**, is dark. If the checker pattern breaks at a seam, recheck panel orientation before placing the pieces.

## Identify the six roles

| Chess role | Recognize it by | Architectural interpretation |
|---|---|---|
| King | Tallest tower, a long narrow shaft above broad setbacks, and a stout cross | Empire State Building: the tower's vertical proportions and stepped base lead into a narrow mast adapted into a conventional chess cross |
| Queen | Four stepped semicircular crown tiers, triangular recessed windows and a short peak | Chrysler Building: overlapping arches form the crown's actual silhouette and depth, with triangular windows on both faces |
| Bishop | Long wedge-shaped body with a narrow blunt prow, gridded facades, a projecting cornice and a shallow diagonal mitre mark | Flatiron Building: the symmetric wedge and continuous cornice carry its architectural identity above the shared base |
| Knight | Horse head in side profile, forward muzzle and blunt ears | An original city horse, using the same planar and stepped design language as the architecture |
| Rook | Paired pointed portal recesses and strong corner crenellations | Brooklyn Bridge stone towers adapted into the familiar castle role |
| Pawn | Short cylindrical tank under a conical roof | New York rooftop water tanks, repeated as the city's everyday infrastructure |

The architectural interpretations are original stylizations, not scale replicas. The cross, mitre cue and crenellations prioritize unambiguous chess roles over literal historic detail.

The current printability repair uses rising shoulders beneath the king's base and crossbar, the queen's base and crown, the bishop's base and cornice, the knight's pedestal, the rook's base and crown, and the pawn's tank. It also gives the bishop's recessed bands sloped roofs and the knight diamond-shaped eye recesses. These are assumed design choices; their exact dimensions are recorded in `cad/city_spec.md`. Current exported geometry must be checked before these changes can be described as passing.

## The five cultural passages

Both armies share the same border; neighborhoods are not assigned to opposing sides. The reliefs represent selected, documented aspects of each place rather than an exhaustive portrait.

| Border location from the light side | Relief to find | Reference behind it |
|---|---|---|
| Bottom left | Recessed gallery fronts and a bent street line | Chinatown's adapted association architecture and the sharp bend of Doyers Street |
| Left | Round-headed masonry openings beside a chimney | Williamsburg's waterfront industrial history |
| Top left | Two concentric record decks on a common backing | Bronx hip-hop's creative use of two turntables |
| Bottom right | A long ferry hull, stacked decks and wake strokes | Staten Island's daily harbor connection to Manhattan |
| Right | Train cars above rails and repeated piers | Queens' elevated transit and the 7 line's connection between diverse communities |

The research record in [RESEARCH.md](RESEARCH.md) links the museum, municipal and architectural sources. No institutional logo, transit map, signage, artist likeness or external mesh is reproduced.

## Set up a standard game

Light moves first. Each player has one king, one queen, two rooks, two bishops, two knights and eight pawns. Put the pawns on the second rank from that player's edge. Put the queen on her own color: the light queen on light d1 and the dark queen on dark d8. Kings occupy e1 and e8.

```text
                         DARK
  8     R    N    B    Q    K    B    N    R
  7     P    P    P    P    P    P    P    P
  6     .    .    .    .    .    .    .    .
  5     .    .    .    .    .    .    .    .
  4     .    .    .    .    .    .    .    .
  3     .    .    .    .    .    .    .    .
  2     P    P    P    P    P    P    P    P
  1     R    N    B    Q    K    B    N    R
        a    b    c    d    e    f    g    h
                         LIGHT

R = rook   N = knight   B = bishop
Q = queen  K = king     P = pawn
```

A move takes one piece to a permitted destination. Capture an opposing piece by occupying its square and remove it from the board. You cannot occupy a square containing one of your own pieces. Except for the knight, pieces cannot jump intervening pieces. No move may leave your own king in check.

| Piece | Standard move |
|---|---|
| King | One square in any direction, to a square not attacked by the opponent |
| Queen | Any unobstructed distance along a rank, file or diagonal |
| Rook | Any unobstructed distance along a rank or file |
| Bishop | Any unobstructed distance along a diagonal |
| Knight | Two squares along one axis and one perpendicular, making an L; it may jump |
| Pawn | One empty square forward; on its first move it may move two if both squares are empty. It captures one square diagonally forward and never moves backward. |

**Check and checkmate.** A king attacked by an opposing piece is in check. The player must remove that check with a legal move. If no legal move removes it, the game ends in checkmate; the king is not physically captured. If a player has no legal move and is not in check, the position is stalemate and the game is drawn.

**Castling.** A king and one rook may move together once under the standard conditions: neither that king nor the chosen rook has moved, the squares between them are empty, the king is not in check, and neither the square the king crosses nor the square it reaches is attacked. Move the king two squares toward the rook, then put the rook on the square the king crossed. Kingside: e1–g1 with h1–f1, or e8–g8 with h8–f8. Queenside: e1–c1 with a1–d1, or e8–c8 with a8–d8.

**En passant.** Immediately after an opposing pawn advances two squares from its starting square and finishes beside your pawn, your pawn may capture it as though it had advanced only one square. Move diagonally to the square it passed over and remove that pawn from its actual square. This option expires if not used on the very next move.

**Promotion.** A pawn reaching the farthest rank must become a queen, rook, bishop or knight of its own color, as part of that move. The choice is not limited to previously captured pieces. Print additional chosen roles from the supplied family files if needed. For an informal game when no spare is available, agree on an unmistakable temporary proxy and announce its role; the promoted piece still follows the ordinary rules of that role. An upside-down rook does not automatically become a queen.

Players may also draw by agreement or under the standard repetition, move-count and dead-position rules. For their exact conditions, claims and tournament procedures, consult the [FIDE Laws of Chess](https://rcc.fide.com/fide-laws-of-chess_fulltexthtml/), which govern this unchanged game.

## Storage and care

Remove chessmen and inlays before moving the panels. Store tall pieces with room around their crowns and horses' ears; do not pile heavy board panels on them. Keep small parts away from young children. Wipe gently with a damp cloth and dry; avoid dishwasher heat and prolonged heat exposure that may distort common printing plastics. This package does not include a verified carrying case.

## Editable CAD and digital evidence

`assembled.step` is the primary complete CAD assembly; `assembled.step.json` preserves its associated metadata. `assembled.stl` is the combined reference mesh. `cad/city.step.py` places the named occurrences and colors; `cad/city_lib.py` owns the shared dimensions and geometry. Eleven `cad/part_*.step.py` entries produce six role families, one dark tile and four board panels in print orientation. `parts/` supplies the complete named print inventory. STEP and STL are in millimetres.

The commands below run from the Workshop workspace using its materialized CAD toolchain and configured Python. The assembly has `PRINTABLE = False`; part entries have `PRINTABLE = True`. Rebuild every entry after a shared-library change, then inspect the resulting geometry and repeat the digital gates. Do not edit generated STEP/STL bytes to change the design.

```sh
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen \
  artifacts/make/r0001/product/cad/city.step.py \
  artifacts/make/r0001/product/cad/part_king.step.py \
  artifacts/make/r0001/product/cad/part_queen.step.py \
  artifacts/make/r0001/product/cad/part_bishop.step.py \
  artifacts/make/r0001/product/cad/part_knight.step.py \
  artifacts/make/r0001/product/cad/part_rook.step.py \
  artifacts/make/r0001/product/cad/part_pawn.step.py \
  artifacts/make/r0001/product/cad/part_dark_tile.step.py \
  artifacts/make/r0001/product/cad/part_board_0_0.step.py \
  artifacts/make/r0001/product/cad/part_board_1_0.step.py \
  artifacts/make/r0001/product/cad/part_board_0_1.step.py \
  artifacts/make/r0001/product/cad/part_board_1_1.step.py \
  --write --force

"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/make_round \
  artifacts/make/r0001/product/cad --all-parts --nozzle 0.4 --json

"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/verify_project \
  artifacts/make/r0001/product/cad --exports --strict-fit \
  --bed 220x220x220 --motion-manifest measure/motion.json
```

Every printable must pass the geometric overhang gate in its supplied print pose at the default 45-degree threshold. Short bridge regions accepted by the checker are reported separately; an unsupported overhang failure requires repair. Documenting slicer supports does not replace this gate.

The verification report, overhang results, thickness results, mesh results and tile placement sweeps establish only the digital checks they explicitly record. A uniform-solid stability proxy cannot establish the behavior of a particular infill pattern, material, table or printed surface. A physical print and playtest remain separate evidence.
