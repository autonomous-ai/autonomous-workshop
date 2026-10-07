# ASCII Tree Key: design-a-toy working notes

Concept S2 ASCII Tree (`toys-spec/key-new/concepts/round6/s2_ascii-tree.jpg`),
chosen by the owner on 2026-10-07 with three changes: the tree centred on the
screen; the top star a gold `*` the same size as the others; four rows of 1, 2,
3 and 4 glyphs offset half a step. Inventor `wyn-seal` (sealed-inlay flat tap
objects), as for the Pixel Tree Key.

## Stage 1 decisions

Reused from the Pixel Tree Key (owner, 2026-10-07): the standard
21.5 x 11.5 x 0.75 mm inlay sealed at a print pause; colour by a multi-colour
print.

Owner (2026-10-07): all six S2 colours (graphite, black screen, cream stripe,
green, gold, red), which needs two AMS units; six-spoke asterisks ("closer to
the original asterisk"), drawn as plain font glyphs, never snowflakes.

Inventor decisions:
- Colour bodies are flush inlays (Taste: colour is geometry, flush), never
  relief.
- Every body is at least 1.0 thick (five layers). The Pixel Tree Key's attempt 2
  stopped on `check_thickness` reading an exact 0.8 slab 1e-16 under its limit;
  1.0 keeps clear of that boundary.
- The 4.0 mm Taste limit holds a 1.0 floor, a 1.0 pocket, a 1.0 stripe and a
  1.0 top layer, and nothing more, so the screen is flush with the frame: S2's
  sunken screen step is left out and named in R06.
- Graphite is two bodies, `base` (bottom layer, shaft, bit) and `frame` (top
  layer): one graphite body above the cream stripe would overhang the stripe in
  its own print check.
- The stripe is a whole bow-sized slab, not a ring: it is also the pocket roof.
- Filaments from `cadfilament.py` stock: PLA Matte nardo gray #757575
  (graphite), desert tan #E8DBB7 (cream), charcoal #000000 (screen), grass green
  #61C680, dark red #BB3D43; PLA Lite sunflower yellow #FFB549 (gold).
- Tree spacing: 6.8 within a row, 6.4 between rows, as the approved image
  draws it (the owner's text grid has equal row and column steps; 6.4 against
  6.8 is the image's reading of it).

## Revision 1 (owner, 2026-10-07): a smaller, terminal-icon bow

Owner at Stage 4: the bow looks too big and does not have a usual terminal
icon's proportions; make it smaller. Everything in Stage 3b to 3c below this
section describes the first set (bow 42.0 x 38.8) and is superseded by the
tables here.

Inventor decisions:
- The tree sets the floor. With 0.9 spokes (0.8 min_wall plus the float margin)
  and 1.6 webs, the smallest printable tree is a 4.0 glyph at 5.8 in a row and
  4.8 between rows: 21.3 x 18.4 (`measure/spec.py`). The screen holds it with
  1.8 margins; the bow is 38.0 x 30.4 (60% of the first bow's area).
- 4:3 was asked of the model; eight edits never drew it below about 1.25, so
  the bow takes the image's 5:4, also a usual terminal-icon proportion.
- The shaft and bit follow the new image, which drew them about 12% smaller
  in proportion to the smaller bow: shaft 6.0, teeth 8.9 / 11.5 / 10.8. The key
  is 70.6 long, 9 mm shorter than today's Key.

Provenance: ref-01 from t02a by p03 (t03c, 1 of 4), then p04 (t04d, 1 of 4).
ref-02 by q02 from t04d (q02d, 1 of 6). ref-04 by e04 from t04d (q04a, 1 of
3). ref-05 by d05 from t04d's bow, cropped and enlarged (q05a, 1 of 3).
ref-03 by n03 from ref-04 (q03a, 1 of 3). ref-06 and ref-07 are unchanged:
their shapes did not change. view-desk by v02 from t04d (w02b).

### ref-01 (assembly, t04d, 0.1743 mm/px from the 38.0 bow)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Bow | 38.0 x 30.4, W/H 1.25 | 38.0 x 30.33, 1.253 | agrees |
| Bow corners | R3.5 | R3.5 | agrees |
| Key end | -40.2 | -40.09 | agrees |
| Shaft | -3.0..3.0 | -3.14..2.79 | agrees |
| Bit right edge by Y range | 8.9 / 5.6 / 11.5 / 7.2 / 10.8 | 8.9 / 5.6 / 11.5 / 7.15 / 10.8 | agrees |
| Bit Y steps | -17.0, -22.5, -23.6, -28.4, -30.6, -35.6 | -17.0, -22.4, -23.5, -28.3, -30.6, -35.9 | agrees |
| Window | X -17.0..17.0, Y 3.3..25.3 | X -16.91..17.08, Y 3.31..25.28 | agrees |
| Dots | X -14.5, -10.6, -6.7, Y 27.9, Ø2.0 | X -14.47, -10.57, -6.65, Y 27.39, Ø2.27 | agrees (Y 0.5) |
| Glyph count and colours | 1 gold, 9 green | 1 gold, 9 green | agrees |
| Rows Y | 21.5, 16.7, 11.9, 7.1 | 21.41, 16.72, 11.88, 7.10 | agrees |
| Row X | ±2.9; -5.8, 0, 5.8; -8.7, -2.9, 2.9, 8.7 | -2.58, 3.25; -5.40, 0.35, 6.09; -8.64, -2.85, 2.96, 8.93 | agrees (0.42 worst) |
| Glyph size | 3.91 x 4.0 | 3.66-3.83 x 4.01-4.18 | agrees |
| Tree centre | (0, 14.3) | (0.15, 14.2) | agrees |

### ref-02 (base, q02d)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Bow height / key end | 30.4 / -40.2 | 29.83 / -40.60 | agrees |
| Pocket | X -11.15..11.15, Y 8.35..20.25 | X -11.20..11.03, Y 8.29..20.72 | agrees |
| Shaft | -3.0..3.0 | -3.24..2.74 | agrees |
| Bit right edge | 8.9 / 5.6 / 11.5 / 7.2 / 10.8 | 8.9-9.0 / 5.6 / 11.5-11.7 / 7.05-7.55 / 10.9 | agrees |

### ref-03 (stripe, q03a), ref-04 (frame, q04a), ref-05 (screen, q05a)

| Image | Check | Contract | Image | Verdict |
|---|---|---|---|---|
| ref-03 | W/H, corners | 1.25, R3.5 | 1.249, R3.75 | agrees |
| ref-04 | W/H | 1.25 | 1.260 | agrees |
| ref-04 | Window | X -17.0..17.0, Y 3.3..25.3 | X -16.82..17.00, Y 3.16..24.95 | agrees |
| ref-04 | Borders side / bottom / title | 2.0 / 3.3 / 5.1 | 2.09 / 3.16 / 5.45 | agrees |
| ref-04 | Dot holes | X -14.5, -10.6, -6.7, Y 27.9, Ø2.0 | X -14.44, -10.46, -6.68, Y 27.46, Ø2.27-2.44 | agrees |
| ref-05 | W/H | 34.0 / 22.0 = 1.545 | 1.595 | agrees (3.2%) |
| ref-05 | 10 hole centres | as R07 | worst 0.22 off | agrees |
| ref-05 | Hole size | 3.91 x 4.0 | 3.51-3.58 x 3.82-3.89 | agrees |

ref-06 (glyph) against the new 3.91 x 4.0 glyph: W/H 0.892 against 0.978,
0.34 at this size; spokes 18% of the height, 0.73 against 0.9: agrees. ref-07
unchanged (Ø2.0). All cameras stay [-90, 90].

### Stage 3c on the revised numbers

| Feature | Size | Minimum | Verdict |
|---|---|---|---|
| Glyph spoke | 0.9 wide | 0.8 (min_wall) | passes |
| Glyph spoke end | flat land 0.9 | 0.8 | passes |
| Screen between two glyph holes | 1.70 least | 1.6 (min_web) | passes |
| Glyph hole to window edge | 1.8 | 1.6 | passes |
| Screen tips between spokes (R0.5 inside corners) | 0.03 mm² under 0.8 | taper budget 2% | passes |
| Dots | Ø2.0 | 2.0 (min_feature) | passes |
| Between dot holes / dot hole to window / to outline | 1.9 / 1.6 / 1.5 | 1.6 / 1.6 / 0.8 | passes |
| Frame border | 2.0 least | 0.8 | passes |
| Bit notch 1 | 1.1 wide, 3.3 deep | 0.5 | passes |
| Pocket wall in plan | 7.85 least | 0.8 | passes |
| Pocket roof bridge | 11.9 | 12 | passes |
| Keep-out: pocket + 2.0 inside the window | holds | Taste | passes |
| Every body | 1.0 thick | 0.8 | passes |

## Stage 3: image provenance

All images AI-edited with OpenRouter `openai/gpt-5.4-image-2`, the base image
passed as an `image_url` part (`measure/edit_image.py`, a wrapper round the
brainstorm-trend `generate_image.py`). Prompts in `prompts/`. No web image was
used.

| File | Made from | Prompt | Rounds |
|---|---|---|---|
| t01a (working) | S2 | p01: top view, centred 1-2-3-4 asterisk tree | 1 |
| ref-01-ascii-tree-key.png | t01a | p02: bigger tree, shorter shaft (t02a) | 1 |
| ref-02-base.png | t02a, 4 steps | g02 plain bow (g02c, 1 of 4 kept; 10 earlier drafts drew the bow 2.7-4.6 taller), i02 pocket (i02a), j02 narrower (j02af, 1 of 8), l02 shorter (l02f, 1 of 6); then a 3.2% vertical resize | cap |
| ref-03-stripe.png | ref-04 (e04c) | n03: fill and recolour cream (n03a, 1 of 3) | cap |
| ref-04-frame.png | t02a | e04: erase screen, shaft, dots (e04a); 4.2% vertical resize | 2 |
| ref-05-screen.png | t02a's bow, cropped and enlarged | d05 (d05b); 6% horizontal resize | 2 |
| ref-06-glyph.png | t02a | c06 | 1 |
| ref-07-dot.png | t02a | c07 | 1 |
| view-desk.png (illustration for the owner, not sealed) | t02a | v02 | 2 |

Criteria: one subject inside the frame; the terminal outline and the tree read
at thumbnail size; contrast holds on #f5f0e6; outline, glyph count and
positions agree with the contract (Stage 3b). Round cap: 6 batches per image.

## Stage 3b: reconciliation

Scripts in `measure/` read images; none draws one. Silhouettes are thresholded
halfway between the background and the subject (a fixed low threshold took the
soft shadow in and read the 6.2 shaft as 7.5). The contract was derived from
t02a at 0.1522 mm/px (bow 276 px = 42.0 mm). Disagreement: off by more than
5% and more than 0.5 mm; positions use 5% of the distance from the datum
(X 0, Y 0 at the bow's bottom edge).

### ref-01 (assembly, t02a)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Aspect W/H | 42.0 / 79.9 = 0.526 | 0.525 | agrees |
| Bow height | 38.8 | 38.96 | agrees |
| Key end | Y -41.1 | -41.09 | agrees |
| Bow corners | R4.0 | R4.25 | agrees |
| Shaft | X -3.1..3.1 | -3.20..3.04 | agrees |
| Bit right edge, Y -17.5..-23.2 | 9.7 | 9.74 | agrees |
| Notch 1, Y -23.2..-24.4 | 6.0 | 6.09 | agrees |
| Tooth 2, Y -24.4..-29.6 | 12.6 | 12.63 | agrees |
| Notch 2, Y -29.6..-31.6 | 8.0 | 8.22 | agrees |
| Tooth 3, Y -31.6..-37.2 | 11.5 | 11.57 | agrees |
| Window | X -18.3..18.3, Y 4.0..33.0 | X -18.2..18.4, Y 4.1..33.0 | agrees |
| Borders side / bottom / title bar | 2.7 / 4.0 / 5.8 | 2.7 / 4.1 / 5.9 | agrees |
| Dots X | -15.5, -11.9, -8.3 | -15.47, -11.87, -8.20 | agrees |
| Dots Y | 35.7 | 35.39 | agrees (0.31) |
| Dot diameter | 2.0 | 2.3 | agrees (0.3) |
| Glyph count | 10 (1 gold, 9 green) | 10 (1 gold, 9 green) | agrees |
| Row Y | 28.1, 21.7, 15.3, 8.9 | 28.06, 21.65, 15.23, 8.84 | agrees |
| Row 4 X | -10.2, -3.4, 3.4, 10.2 | -10.27, -3.45, 3.38, 10.21 | agrees |
| Rows 2, 3 X | -3.4, 3.4; -6.8, 0, 6.8 | -3.39, 3.36; -6.91, 0.0, 6.86 | agrees |
| Tree centre | (0, 18.5) | (0.0, 18.4) | agrees |
| Glyph size | 4.83 x 5.0 | 4.9-5.0 x 5.2-5.3 | agrees |
| Gold glyph size against green | same | 32 x 34 px against 32-33 x 34-35 px | agrees |
| Spoke width | 1.0 | 0.87 | agrees |

The pocket is hidden in ref-01.

### ref-02 (base)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Aspect W/H | 0.526 | 0.526 after resize | agrees |
| Bow height | 38.8 | 40.2 | 1.4 (3.6%): agrees |
| Key end | -41.1 | -39.6 | 1.5 (3.6%): agrees |
| Shaft | -3.1..3.1 | -3.37..3.07 | agrees |
| Pocket X | -11.15..11.15 | -11.38..11.38 | agrees |
| Pocket Y | 12.55..24.45 | 12.38..24.92 | agrees |
| Bit steps | Y -17.5 / -23.2 / -24.4 / -29.6 / -31.6 / -37.2 | -16.5 / -22.0 / -22.9 / -28.5 / -30.1 / -36.2 | about 1.0 high, 2.7-5.7% of the distance from Y 0: the first two steps (1.0 of 17.5, 1.2 of 23.2) fail by a hair; unresolved at the cap, see below |
| Tooth right edges | 9.7, 12.6, 11.5; notches 6.0, 8.0 | 8.5, 11.9, 10.6; 6.4, 9.0 | within 0.5-1.0 |

Unresolved at the cap: every model re-draw of the plain base grew the bow
relative to the shaft, and the best image puts the bit about 1 mm higher than
ref-01 and the contract. The contract keeps ref-01's numbers. Raised at
Stage 4 as "the base picture's bit sits about 1 mm higher; the build follows
the assembly picture".

### ref-03 (stripe)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Aspect W/H | 42.0 / 38.8 = 1.082 | 1.086 | agrees |
| Corners | R4.0 | about R5.5 (soft, low contrast) | 1.5: unresolved at the cap, a softer corner on a plain slab |

### ref-04 (frame)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Aspect W/H | 1.082 | 1.085 after resize | agrees |
| Window X | -18.3..18.3 | -18.38..18.53 | agrees |
| Window Y | 4.0..33.0 | 3.60..32.81 | agrees |
| Borders side / bottom / title | 2.7 / 4.0 / 5.8 | 2.54 / 3.60 / 5.99 | agrees |
| Dot holes X | -15.5, -11.9, -8.3 | -15.98, -12.07, -8.28 | agrees |
| Dot holes Y | 35.7 | 35.48 | agrees |
| Dot hole diameter | 2.0 | 1.64-1.79 x 1.50 | agrees (within 0.5; hole walls shade the rim) |
| Corners | R4.0 | R3.75 | agrees |

### ref-05 (screen)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Aspect W/H | 36.6 / 29.0 = 1.262 | 1.260 after resize | agrees |
| Hole count | 10 | 10 | agrees |
| Hole size | 4.83 x 5.0 | 4.5-4.6 x 5.0 | agrees |
| Row Y | 28.1 ... 8.9 | 28.3, 21.8, 15.4, 8.9 | agrees |
| Pitch in a row / between rows | 6.8 / 6.4 | 6.64 / 6.47 | agrees |
| Row 4 X | ±3.4, ±10.2 | -3.30, 3.28, -9.95, 9.95 | agrees |
| Tree centre | (0, 18.5) | (0.03, 18.6) | agrees |

### ref-06 (glyph) and ref-07 (dot)

| Check | Contract | Image | Verdict |
|---|---|---|---|
| Glyph W/H | 0.966 | 0.892 (0.37 on 4.83) | agrees |
| Glyph spoke width | 1.0 | 0.91 | agrees |
| Glyph area | 13.4 mm² (with R0.5 inside corners) | 11.6 | agrees: the spoke widths agree, and the corner fill is under the print limits |
| Glyph spokes | 6, one vertical | 6, one vertical | agrees |
| Dot W/H | 1.0 | 0.962 (0.08) | agrees |

### Reference cameras

All seven are straight down on the front face with the title bar up:
[-90, 90]. Cue: only the front face shows, with a faint even shadow and no
side face.

### Joint features

The glyph holes show in ref-05 and the dot holes in ref-04, where their
Interfaces put them; the pocket shows open in ref-02. The frame-shaft and
pocket-roof contacts are flat faces that no top view shows. ref-04 shows no
shaft stub (two earlier drafts grew one and were rejected).

## Stage 3c: print

Glyph geometry checked with shapely (`measure/spec.py`).

| Feature | Size | Minimum | Verdict |
|---|---|---|---|
| Glyph spoke | 1.0 wide | 0.8 (min_wall) | passes |
| Glyph spoke end | flat land 1.0 | 0.8 | passes |
| Screen between two glyph holes | 1.97 least | 1.6 (min_web) | passes |
| Glyph hole to window edge | 2.4 | 1.6 | passes |
| Screen wedges between a glyph's spokes | sharp 60-degree tips: 6.6 mm² of plan under 0.8 across, about 3.5% of the screen's surface as tapers and spots | `check_thickness` taper budget 2% | fails; resolved by rounding each glyph's six inside corners R0.5 (enlarged detail): 0.03 mm² left, the image's sharp corners differ by less than the print limits |
| Dot | Ø2.0 | 2.0 (min_feature) | passes |
| Frame between two dot holes | 1.6 | 1.6 (min_web) | passes |
| Dot hole to window / to outline | 1.7 / 2.1 | 1.6 / 0.8 | passes |
| Frame border | 2.7 least | 0.8 | passes |
| Bit notch 1 | 1.2 wide, 3.7 deep | 0.5 (min_cut_width) | passes |
| Every body's thickness | 1.0 least | 0.8 | passes, with the float margin |
| Pocket floor | 1.0 | 0.8 | passes |
| Pocket wall in plan | 9.85 least | 0.8 | passes |
| Pocket roof bridge (stripe) | 11.9 | 12 | passes |
| Keep-out: pocket + 2.0 inside the window, nothing cuts through | holds | Taste | passes |

Stacked or curved details: none (all colour bodies are flush inlays in flat
hosts). Support: every body sits on the bed or on a body printed before it;
every side face is vertical; the only ceiling is the pocket roof, a bridge. No
hidden pegs: every Interface is a flat fused contact. No moving part, so no
swept ceilings.

Left out: the images' sunken screen step (R06). Nothing else.

## Stage 3d

No moving parts. R11's "three dots (cranberry, gold, green from the left)"
holds from the [-90, 90] camera: X -15.5, -11.9, -8.3 run left to right on
screen with +X to the right.
