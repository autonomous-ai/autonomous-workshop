# How Rolife manuals structure assembly

Gathered 2026-10-23 for ADR 0092 (kit Assembly Tree and Manual), by reading
the page tiles of six 2026 Rolife manuals: TGB18, TGE05 (book nooks), TGB19,
DH201, DH102, DG186 (houses). Tiles are `sources/manuals-2026/tiles*/<KIT>/
<KIT>-NN.png`, about two manual pages each; `sources/` is kept out of git (see
`README.md`). Every claim cites a tile.

## Steps form a tree

- Rolife names each sub-assembly with a letter tag (blue or black squares a,
  b, c…), and later steps take those tags as inputs; the finished toy is the
  root (TGB18 a…o, TGE05 a…t, TGB19 a1…h2).
- Furniture with items on it decomposes exactly as furniture, each item, then
  "mount the items": DH201 builds "Big table B" (-12/-13) and each coffee item
  (-03/-04, -27, -31, -32), joins them in "Part A–I" (-33/-34), then places
  each Part in the shell in "Framework" (-36/-37).
- Pages only present steps: one step spans several pages (TGE05 step 5,
  pp. 13–21) and one page holds several steps (TGE05 p. 24 holds 7 and 8).

## What does not fit a plain tree, and how ADR 0092 places it

| Case | Evidence | Placed as |
|---|---|---|
| Lamps in different subtrees, spliced after the subtrees merge | TGB18 P17/P18/P25/P39/P42 spliced with P43 (-15, -18); TGE05 P1/P2/P3 with P67 (-19) | A wiring Assembly Step at or above the smallest Sub-assembly holding every lamp |
| A lead must pass a gap before something closes | TGB18 "Rotate f to check if the wiring passes through the gap" (-09); TGE05 "!" (-11); DG186 (-28) | The enclosing step declares where the lead comes out |
| Light test connected, then taken apart and bagged | TGE05 (-02), TGB19 (-02), DG186 (-03) | A Check Step outside the tree |
| Fold, cut to a 1:1 gauge, peel, bend, roll | TGE05 step 1 (-02); DH201 cut P15 (-05) | A one-input Assembly Step |
| Repeated identical sub-assemblies | TGB18 S2 ×2 (-04); DH201 chair ×5 (-07) | An Assembly Step made N times |
| Tools, jigs, tape | TGE05 D8 "TOOL" (-13); tape S/M/L (TGB18 -02) | Material list only |
| Bags | TGB18 bag 3-1 used in S1, S6, S11, S12; DH201 one bag badge per section | One bag per Component (DH201 style) |

## Ordering keeps hands able to reach

Ranked by how consistently the six kits do it:

1. Furniture and props are finished and dressed outside the room, then
   placed whole (all six: DH201 -33/-34, DG186 -25…-28, TGE05 -08…-10).
2. Walls and ceilings are dressed flat or loose, then joined (five of six:
   TGB18 -07/-08, TGE05 -15/-16).
3. Interior out, floor first, front and roof last (TGE05 -07…-23, TGB19).
4. Wiring is laid before anything closes over it (TGE05 -11, TGB19 -25,
   DG186 -28, DH201 -38).
5. Reach aids: tweezers (TGE05 -08, DH102 -50), jigs, rotate icons.
6. Awkward reach happens only through a face still open (TGE05 -16, DG186
   -32); nothing small is glued deep inside a closed room.

Multi-joint placements are one panel per arrow along one direction, one panel
engaging a whole row of tabs (DG186 octagon walls one by one, -19/-20).
Several loose pieces converging at once appear only on small boxes (TGB18
battery box -04), which a printed kit prints as one piece.

## What paper lands on

| Paper lands on | TGB18 | TGE05 | TGB19 | DH201 | DH102 | DG186 |
|---|---|---|---|---|---|---|
| One loose part, before joining | 10 | 24 | 13 | 25 | 35 | 17 |
| One face of a part already joined | 14 | ~21 | – | 16 | – | 9 |
| Several joined parts (wrap, roof sheet, edge strip) | 4 | ~5 | 9 | 6 | 23 (with one-face cases) | 6 |
| A bought part (jar, bottle, wire, bead) | 0 | 13 | 3 | ~30 | ~25 | 7 |

Counts are approximate (repeated ids, unclear tiles). Spanning examples: roof
sheets over joined trusses (DG186 -31, TGB18 M12 -10), wraps round joined
boxes (TGE05 M9 -05, DH201 N10 -10), edge strips round corners (DG186 M7–M9
-26). No piece deliberately crosses a small seam. Some paper is folded into
an object of its own and lands on nothing (DH201 kettle M3/M5/M6, boxes; DG186
K3–K18).

## Tools and spares in the box

- Book nooks show tools only inside steps, with no tools or warnings page:
  screwdriver (TGB18 P46 -19, TGE05 P4 -02), foam tape and dots, wire jig
  (TGE05 D8 -13), tweezers (TGE05 P35 -08). Batteries are "Self-prepare".
- House kits open with a page of included tools (sandpaper, tweezers,
  screwdriver, double-sided tape, glue) and self-prepared ones (scissors,
  knife, pliers, batteries), plus warnings (DH201 -02, DH102 -02). DH201 -03
  contradicts its own glue icon ("Glue needs self-preparation").
- DH201/DH102 define "+" as "has spare ones" (-02), but no "+" part was found
  in the tiles; counts read `ID*n`. Spares are implicit: shared bags of beads
  and cups (DH201 -14, -27), more dots than used (TGB18 -02), wire as a coil
  cut to 1:1 gauges (DH201 -08/-09). House kits print an after-sales email
  (DH201 -52); book nooks print only QR codes.
