# Limbward: completed selected-inventor handoff

Chess — coronagraph theme: rival optical masks cross a focal-plane board to leave the opposing star no safe line of sight.

This is the completed construction dependency for the Manager, authored by selected inventor Mara Masque for subject 4e24e678156d0546d69502195bf393dc26e673b47d0c4266bfb51294ff89783c. All dimensions below are deliberate design decisions within the exact Wish. No reference images were attached. All 97 physical items are monolithic individual solids: one camera-board, 32 starting pieces, and 64 promotion replacements. “No assemblies” means no constructed or captive subassemblies within an item; the free chess pieces remain separate and movable. No hardware, light, circuitry, hinges, storage lid or extra game system.

## Geometry authority

Coordinates: millimetres. Camera body overall bounds including integrated lens and grip are x=-98..98, y=-98..98, z=0..26. Front points toward negative y. Main body is x=-98..98, y=-80..98, z=0..22, with 4 mm vertical corner radii or 4 mm corner chamfers. This broad, shallow chunky camera has a solid flat underside. Board lies x=-80..80, y=-70..90, playing surface z=22; the 160 by160 surface is eight20 mm cells in both directions. Rim rises to z=26 around the board and retains at least4 mm material next to all edges. Keep camera's right grip visibly separate in relief within x=84..98, y=-66..78: a14 mm broad raised pad to z26, with three2 mm wide vertical recessed grip channels,2 mm deep and separated by3 mm. It is integral with the body and does not enter the board.

Broad integral lens bulge occupies x=-34..34, y=-98..-76, z=0..24. Use an octagonal rounded-rectangle cross section in the x/z front plane,68 mm wide,24 mm high, with4 mm corner chamfers, extruded22 mm in y. Its rear4 mm overlaps the body, producing one solid. Its underside is flat; the4 mm upper/lower bevels are45 degrees. Add a shallow original optical rim/front recess within this mass if needed for camera recognition, preserving at least2 mm walls and support-free lower surfaces. This is an inert solid stylized lens, not a working optical cylinder. Do not allow camera dimensions to expand when adding its form. The body, prominent lens, distinct grip and exposed top board must all be visible in the held render.

Alternating board cells: retain coplanar central landing pads; on the32 dark cells engrave a square perimeter groove2 mm wide and0.6 mm deep, inset1 mm from the cell edges. The groove centerline square spans17 mm; the inner clear landing area remains14 mm across and a16 mm foot bridges its shallow groove. Smooth cells have no groove. All64 cells have20 mm nominal pitch. Use a1 mm wide,0.5 mm deep continuous grid only if required by visual review; this is recessed marking, never a structural wall. Light h1 is smooth; a1 is the dark engraved cell. Painting is optional; square parity stays readable unpainted. Recesses do not remove a whole cell or create raised obstacles. Discreet coordinate markings are optional original markings, not required geometry.

Each piece has a16 mm diameter,4 mm high flat foot. White feet are circular and smooth. Black feet have exactly three vertical scallops made by radius3 mm cutters centred radius9 mm from the foot axis, at angles0,120,240 degrees. They bite2 mm into the perimeter, leaving a central radius6 mm load path. All upper forms must fit inside the foot's16 mm circumscribed disk and connect to the base with positive overlap. Black scallops stay visible/tactile even in monochrome. No tapered needle tips or unsupported horizontal projections. Side colour can additionally be warm ivory versus deep blue-gray; side identity never relies on paint.

Six upper forms (total heights include foot):

| Role | Total height | Original solid form above foot | Meaning and orientation |
|---|---:|---|---|
| K |22 | Radius6 mm vertical pedestal z4..16, topped by radius6 mm upper hemisphere z16..22 | Exposed stellar dome; no cross or crown. |
| Q |28 | Radius6 mm cylinder z4..28 with axial radius3 mm top-open blind well from z18..28;3 mm ring wall | Annular all-direction occulting mask. |
| R |34 | Two perpendicular vertical plates, each12 mm long and3 mm thick, from z4..34, fused as a full-height plus | Tall cross-vane mask aligned to ranks/files for the showcase; orientation is not game state. |
| B |26 | Two perpendicular12 by3 mm vertical plates rotated45 degrees about z, from z4..26; clip upper6 mm into a double-slope peaked diagonal vane crest if visual review needs stronger distinction | Lower diagonal vanes; lower height and peaked crest distinguish this from the tall flat-topped rook even if rotated. Make the peaked crest baseline, with2 mm flat truncated peak at z26 and slopes45 degrees down to z21. |
| N |24 | Nested off-axis solid stair:12 by10 mm z4..12,8 by10 mm z12..20 shifted+2 mm in x,4 by10 mm z20..24 shifted+4 mm in x; each tier is contained in the tier below | Off-axis baffle; clearly stepped asymmetry, no horse head. |
| P |12 |12 by10 mm solid wedge z4..12, with low roof z6 at y=-5 and high roof z12 at y=5;2 mm minimum low-edge vertical material | Advancing knife-edge wedge with diagonal capture corners; no sharp physical blade. |

Upper forms are buildable by additive boxes, cylinders, prisms or lofts; union them with the foot. No joints. A queen blind well is subtractive. For the bishop peaked crest, an upper clipping prism must leave a central2 mm flat top and never add an unsupported cap. Print all items upright on their flat bottoms,0.4 mm nozzle; structural material minimum2 mm and downward overhangs at most45 degrees from vertical. Recessed surface markings are nonstructural. Deterministic thickness and overhang checks must confirm geometry; this design does not claim a successful print.

## Inventory and layout

13 distinct geometries: camera_board and white/black K,Q,R,B,N,P. Physical inventory is board1; for each side K1,Q9,R10,B10,N10,P8, totalling48 pieces per side. The32 starting pieces consume K1,Q1,R2,B2,N2,P8 per side. Each side's32 offboard replacement pieces are Q8,R8,B8,N8. Those spares do not alter the32-piece initial position. They guarantee every pawn may independently promote to any of four roles without needing an already captured piece.

Use one combined inventory source with97 uniquely named occurrences. Default on-board state is the normal32-piece starting position and64 offboard spares. Store/show spares in two offboard4 by8 arrays at x=-156,-136,-116,-96 for White and x=116,136,156,176 for Black, y=118,138,158,178,198,218,238,258; each item's base is at z=0. These are presentation positions only, not storage trays or a claim that spare pieces fit inside the camera. Avoid overlap with the196 mm camera; board ends at y98, so spare feet begin y110. Inventory spread exceeds camera envelope by design; the196 mm limit describes the toy camera, not the loose-piece layout.

Board square centres: x=-70+20*file_index; y=-60+20*(rank-1). Thus a1=(-70,-60),h1=(70,-60),a8=(-70,80),h8=(70,80). All on-board bases are z22. Initial White back rank a1..h1 is R,N,B,Q,K,B,N,R; pawns rank2. Black back rank a8..h8 is R,N,B,Q,K,B,N,R; pawns rank7. Light cell h1 establishes orientation; White begins.

## Signature evidence

Two separate exact geometric state STEPs at the SAME elevated view from h1, looking toward board centre. Before: White K a1, White R h1, Black K a8; all93 other pieces remain offboard. After: same kings, White R h8. The rook translates(0,140,0) mm with no rotation or resizing. The full34 mm tall cross-vane moves from foreground to far edge and remains completely visible above the26 mm rim. Use a camera sufficiently high (50–60 degree elevation) that the rear rook isn't hidden; perspective position toward(+x,-y). Keep lens/grip and board framing identical. The only on-board change is Rh1-h8+. This is legal: unobstructed h-file, own king safe, rook on h8 attacks a8 across the empty eighth rank. Black has legal escapes; do not label checkmate. It is an illustrative legal turn, not the starting setup or a compulsory puzzle.

If a motion manifest is required, declare a freely handled unconstrained rook rigid-body translation over140 mm along positive y; it is not a slider joint. No retained mechanical parts, swept captive pathways, snaps or flexures exist. Render sparse states from helper-generated data without replacing the97-occurrence deliverable. A separate full-starting-position hero may show only board and32 starting pieces; the complete97 inventory must remain in delivered occurrences/production files.

## Frozen equivalence ledger

One source game only: standard two-player chess. Primary rules provenance: FIDE Laws effective1 January2023, Articles1–5 and9 for the requested game semantics. No Chess960 or other variant. Every optical piece maps one-to-one to its chess role, side and square; physical orientation, colour, light, camera direction and literal visibility never enter legality. The optical system is a metaphor, not a simulation.

- Public complete information, no random component. Same board, players, setup, White-first alternating turn order and legal choices. Captures remove the opposing piece; the king is never captured. Own occupied squares block entry; sliders cannot cross occupied cells. Knights jump with the ordinary2+1 displacement. Each move must leave own king unattacked.
- King moves one adjacent square; queen moves any unobstructed rank/file/diagonal distance; rook ranks/files; bishop diagonals; knight2+1; pawns forward one to empty squares or initial two if both empty, and capture one forward diagonal. Pawn orientation is fixed by side, not rotated sculpture.
- Castling uses ordinary untouched king and original rook rights, clear intervening squares, and unattacked king start/transit/destination. King travels two files toward the rook; rook occupies the crossed square. A returning king/rook does not regain rights. The rook being attacked is not itself a prohibition.
- En passant is available only immediately after the adjacent opposing pawn's initial two-square advance, on its passed square, subject to own-king safety. Remove the passed pawn from its actual square.
- Promotion is mandatory on reaching the far rank and immediately substitutes any same-side Q/R/B/N; prior captures do not limit choice. Offboard replacement stock is not a reserve drop mechanic.
- Check is an attacked king; checkmate is checked with no legal reply and ends in a win immediately. Stalemate means no legal move without check and draws. Dead position draws when neither player can possibly mate by any legal continuation; do not reduce this to a coarse material heuristic.
- A resignation normally loses, but draws if the opponent cannot possibly checkmate by any legal continuation. Agreement draws only after each side has made at least one move.
- Threefold repetition and50-move draws require a correct claim; claim may refer to the current qualifying state or an indicated legal move that will produce it. Repetition includes same player to move, piece types/sides/squares and identical legal possibilities, including castling rights and a legally available en-passant capture.50 moves means50 by each player without any pawn move or capture.
- Fivefold repetition and75 moves by each side without pawn move/capture end automatically; checkmate on the final move takes precedence over the75-move rule. No custom score, tie-break or themed override: win1/loss0/draw½ each when scores are recorded.
- Ordinary one-hand/touch-move and release semantics apply; announce adjustment before adjusting. No added clock is part of the97 pieces; timed competition, if chosen independently, follows the same ordinary applicable clock/arbiter rules. The reskin adds no time control.

Semantic map: board is a sampled focal plane; occupancy interrupts lanes; capture extinguishes an opposing optical element; king is exposed star; queen annular mask; rook cross-vane; bishop diagonal vanes; knight off-axis baffle; pawn knife-edge. Castling shelters the star alongside a vane; en passant intercepts a passing edge; promotion replaces an edge with a selected full mask. Check threatens occultation and mate makes the threat unavoidable without physically taking the star. Draws retain exact source meanings instead of inventing astronomical outcomes.

Zero-difference design audit: setup, component functions, information, choices, transitions, results and all named exceptional rules are unchanged. This is an authored rule-equivalence audit, not human playtesting. Manager should verify exact signature legality computationally and preserve geometry inventory evidence.

## Research and rights

Accessed2026-09-12. The research array in spark-source.json carries source URLs and bounded claims. FIDE documents exact rules but its prose and diagrams are not reproduced. US Copyright Office explicitly excludes game ideas and methods of play from copyright, while recognizing expressive text/art protection; WIPO likewise separates methods/ideas from expression. The public-domain mechanics basis applies to the exact rules, including current draw procedures; no claim is made that the FIDE publication is public-domain text. Original prose and geometry are authored here. UN and Chess.com independently establish international recognition and a large active player base. NASA explains glare suppression by coronagraph masks; chess movement is expressly metaphorical.

Bounded novelty search covered Limbward chess, coronagraph chess/optical-mask chess, and Wish-named collisions. The word Limbward already exists as an astronomical direction; this is not an exclusive word claim. Closest documented objects are Jim Podpolucha's2012 telescope-themed set, Kankunapa's NASA-inspired planet/vehicle pieces, and Purling/Cheba's Cosmos painted set. Limbward's camera focal-plane board and movement-family solid masks differ in construction and meaning. Use only “an unusual original combination,” never a universal novelty assertion. No commercial asset or instrument CAD was copied.

## Build dependency and remaining evaluation

Design decisions are resolved. Construct isolated board plus12 side/role components; inspect all isolated views and print gates before combined inventory. Then construct97 occurrences, exact signature states, standard setup hero, and independent final visual review. Styling refinements within these exact Wish dimensions and role identities may improve camera recognition; record substantive refinements in research.design_changes.

Residual tests, not external needs: verify camera recognition of the shallow lens silhouette; distinguish bishop/rook by height and crest even in monochrome; verify16 mm feet on20 mm pitch; inspect all pieces above rim; verify support-free/2 mm material constraints; confirm97 inventory and unrestricted promotion stock; verify exact before/after legality and140 mm displacement. No unresolved engineering choice is delegated to the operator.

## Evaluated construction refinements
Lens recess opening radii26x8, rear radii22x4 over2 mm depth. Pawn footprint10x8, roof8..12; bishop plateau3 and side crest21.5; knight depth8. These supersede detail dimensions above to improve edge thickness and footing. All Wish dimensions and role semantics stay intact.

## Independent review 1 repair
The front oval was mistaken for a handle. Revised to a shallow concentric optical surround around a solid circular centre and small circular well. The right grip now projects forward beside the lens, with an integrated shutter boss. All remain one solid within the prescribed envelope; no optical operation is claimed.
