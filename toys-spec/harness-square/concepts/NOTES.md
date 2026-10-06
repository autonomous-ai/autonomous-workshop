# Harness Square: exploration concepts

Concept images only, for picking a direction; no contracts yet. `CONCEPTS.html`
is the selection page (published as a private artifact).

- `foldable/`: eight pocketable folding shells (F1 compact, F2 folio, F3 swivel,
  F4 sleeve, F5 legs, F6 cover-270, F7 tent, F8 slide-tilt), two variants each
  (`_a`, `_b`). Each image shows the device closed (left) and open (right).
  F3's images drew an ordinary flip hinge, not the corner swivel that was asked for.
- `retro/`: six retro-computer shells (R1 minimac, R2 terminal, R3 pet,
  R4 tubetv, R5 luggable, R6 pocketterm); `_a` is cream, `_b` is charcoal.
  Keyboard keys are moulded, non-moving relief that doubles as a speaker grille,
  because the device has no buttons. The R1 and R4 images draw a 4:3 screen; the build
  uses the 3.5" square screen.

All images are AI generations (OpenRouter `openai/gpt-5.4-image-2`), downscaled
to 800 px JPEG. The retro direction took inspiration from a pinned photo of a
retro-PC-style Bluetooth speaker,
https://www.pinterest.com/pin/128282289382610442/ (another company's product).
That photo was looked at only. It was never passed to the generator and is not
used as a reference.

## Desk concepts (`desk/`, `DESK_CONCEPTS.html`)

The owner later set new constraints: desk-only (portable deferred), fixed shell
(no swappable module), and a screen that is flat or tilted 30 degrees or less, for touch use
with the Habitat firmware (swipe for panes, top-left corner plus swipe for tabs,
tap the octopus to speak). There are eight concepts with two variants each:
D1 tidepool, D2 fieldinstrument, D3 lectern, D4 slate, D5 turntable, D6 aquarium,
D7 draftingtable, D8 tentacles. The D3 and D7 renders are steeper than 30 degrees and must
come down to 25 degrees if picked. The screen shows the firmware's lilac ASCII octopus.

Pinterest pins and boards consulted for inspiration (looked at only; never passed
to the generator) are listed at the end of `DESK_CONCEPTS.html`.

## Creature-neutral home concepts (`home/`)

The companion is not fixed to the octopus. The firmware roster has ten creatures
(cat, frog, rabbit, penguin, cow, ghost, plant, jellyfish, robot, bat), so the
shell should be a neutral home. There are six concepts with two variants each,
and each screen shows a different creature: H1 littlehouse (cat), H2 stage (robot),
H3 planter (frog), H4 petbed (rabbit), H5 terrarium (ghost), H6 zenstone
(penguin). The H4 and H6 renders show a raised rim around the screen, which must be
lowered on the front and sides for edge swipes. The H6 penguin resembles Linux's
Tux and must be redrawn. D1, D6 and D8 are tied to the sea and the octopus.

## Retro desk concepts (RT1–RT7), 2026-10-02

Retro computer forms with the screen near flat (≤ 30°), fixed shell, desk only, creature-neutral. Images in `retro-desk/`, page `RETRO_DESK_CONCEPTS.html` (artifact https://claude.ai/artifact/Rh8jjehWanFWMcvM8jaPD4).

- All images are AI-generated with `openai/gpt-5.4-image-2` from text prompts only. No web image was used as input. Pinterest search pages need a login and returned no pins, so inspiration came from named historical devices (1950s radar console, Atari VCS, cocktail arcade table, Commodore 64, Tandy Model 100, Tektronix-style bench instrument, early Macintosh).
- Regenerated once: breadbin (first pair was too steep, `_c`/`_d` kept), reclined mac (still about 45° after the retry, flagged), turntable (Tux-like penguin). Turntable was then dropped as a repeat of D5.
- Flags: RT3 cocktail draws a raised rim around the screen; RT5 Model 100 and RT6 lab instrument draw the screen steeper than 25°; RT6 corner bumpers and RT2 rear ribs must sit below the glass; RT4 rainbow badge and RT7 silhouette recall Apple/Commodore trade dress.

## Synthwave variants (SW1–SW5), 2026-10-05

Added to `RETRO_DESK_CONCEPTS.html` (same artifact). Images in `synthwave/`, all AI-generated from text prompts only (`openai/gpt-5.4-image-2`).

- A grass/moss round (G1–G3, SW2 Grid Lawn) was made and then removed at the owner's request ("tôi nói đùa thôi"). SW1 Sunset, SW2 Outrun Breadbin and SW3 Palm Cab were regenerated without grass (`_c`/`_d`).
- SW1 Sunset is recommended: a translucent striped half-sun behind the back edge, a light guide for the WS2812, with a cyan grid engraved on the sides.
- Flags: SW2 is drawn at about 30° and SW4 Neon Radar at about 35°; the SW3 palm fronds are too thin to print as drawn.

## 2060 futuristic concepts (FX1–FX8), 2026-10-05

Images in `future/`, page `FUTURE_CONCEPTS.html` (artifact https://claude.ai/artifact/FNm2n8khhL6ru4UB5H3tfR). AI-generated from text prompts only, one round.

- FX1 Lattice (recommended, gyroid lattice base only additive manufacturing can make), FX2 Hover, FX3 Glass Block, FX4 Exo (transparent shell showing the real board), FX5 Facet, FX6 Liquid Metal, FX7 Soft Skin, FX8 Halo.
- Flags:
  - FX2 base is too thin for the 22.3 mm board.
  - FX3 and FX4 need clear cast or resin parts.
  - FX3b, FX6a and FX7 draw a rim above the glass.
  - FX5b is about 30°.
  - FX8 ring feet sit next to the top-left tab tap.
  - FX1 lattice struts must be ≥0.8 mm.

## Sci-fi film concepts (SF1–SF8), 2026-10-05

Added to `FUTURE_CONCEPTS.html`. Images in `scifi/`, AI-generated from text prompts only, one round. Prompts describe genre moods only ("used future", clean white future, glowing digital world, black monolith, starship bridge, neon noir, desert brutalism, hologram) and ask for no copy of any specific film prop.

- Recommended: SF1 Used Future, SF3 Light Grid (edge light pipes fed by the WS2812), SF2 White Drone (the sensor eye can be the real CSI camera).
- Flags:
  - The SF1 rear-left corner guard rises above the glass, next to the tab tap.
  - SF2 is drawn at about 30–35°.
  - SF6 draws a metal rim above the glass.
  - The SF8 floating hologram is not real technology; it would become an edge-lit etched acrylic fin.
  - SF3 recalls Tron.

## VHS round, screen 20–30° (VH1–VH8)

The owner picked the synthwave VHS Deck (SW5) as the best look and set a new tilt requirement: the screen sits at 20–30°. Prompts are in the scratchpad `prompts13.py` (keys `vh/...`) and ask for an exact 25° wedge. Images are in `vhs/`; the page is the VHS section of `RETRO_DESK_CONCEPTS.html`. Angles below are estimated from the three-quarter renders.

| Code | Name | Images | Angle | Flags |
|---|---|---|---|---|
| VH1 | VHS Deck 25° (SW5 reworked) | deck_d, deck_c (deck_a about 35°, deck_b has a bezel lip) | 25–28° | none |
| VH2 | Cassette | cassette_a, cassette_b | about 33° | a is too steep; b has a raised frame |
| VH3 | Rental Sleeve | sleeve_a, sleeve_b | 20–28° | mostly graphic decal |
| VH4 | Tape Stack | stack_a, stack_b | 20–22° | top must be one plate |
| VH5 | Tracking Glitch | tracking_b, tracking_a | about 15° | below 20°, back layers must rise |
| VH6 | Camcorder | camcorder_a, camcorder_b | 20–30° | lens can be the real CSI camera |
| VH7 | VCR 12:00 | vfd_a, vfd_b | 28–35° | clock needs an extra 4-digit LED module; b too steep |
| VH8 | Rewinder | rewinder_a, rewinder_b | 25° (a) | b about 40° with a bezel lip; hinge is decorative |

## VHS cassette on a tilted stand (VC1–VC8)

The owner asked for a separate part instead of one solid wedge: a rectangle with the shape of a real VHS cassette (187 × 103 × 25 mm), mounted on a stand tilted 20–30°. Prompts are in the scratchpad `prompts14.py` (keys `vc/...`). The first pass (`_a`/`_b`) drew the cassette standing at 50–75°, so it was discarded and not committed. The second pass (`_c`/`_d`) asks for the back edge to sit 45 mm above the front edge. Images are in `vhs-stand/`. Angles are estimated from the renders.

| Code | Name | Stand | Angle | Flags |
|---|---|---|---|---|
| VC1 | Deck Dock | mini VCR deck | about 20° | at the low limit |
| VC2 | Glow Reel | black wedge, screen left, glowing reel right | 20–25° | screen drawn landscape, the real one is square |
| VC3 | Sunset Acrylic | gradient acrylic wedge | about 25° | gradient acrylic is bought in, not printed |
| VC4 | Neon Grid | two chrome posts over a grid-engraved slab | about 25° | posts must carry the touch load and the FPC |
| VC5 | Wire Easel | bent chrome wire | about 25° | PCB must fit inside the 25 mm cassette |
| VC6 | Rental Cradle | black tray with chrome rails | 25–35° | rental_c is too steep |
| VC7 | Blank Tape | folded aluminium bracket | 25–35° | blank_d is too steep; PCB in the cassette |
| VC8 | Clear Shell | black wedge | about 25° | drawn as an audio cassette, not VHS |

Common: most renders draw the screen smaller than the cassette or landscape. The real 84 mm square glass fills most of the cassette's 103 mm height.

## Detachable handheld with a desk dock (VC4, FX2 Hover)

New owner requirement (2026-10-05): the device lifts off its stand and is used in the hand like a phone; on the desk it sits at 20–30°. The owner picked VC4 Neon Grid and FX2 Hover to rework. VC4's face loses the cassette interior (no reel windows) and takes the SW5 deck styling instead. Prompts are in the scratchpad `prompts15.py` (keys `vx/...`), which uses our own earlier renders (grid_c, vhsdeck_a, hover_a) as edit references. Images are in `handheld-dock/`; the page is `HANDHELD_DOCK_CONCEPTS.html`.

| Concept | Shots | Flags |
|---|---|---|
| VC4 Neon Grid Dock | dock, lift (pogo contacts), hand | 187 mm wide so two-handed; about 28 mm thick for the 22.3 mm PCB; penguin looks Tux-like; chrome strip must be flush with the glass |
| FX2 Hover Dock | dock (25° wedge base, rerun), lift (pogo + USB-C), hand | renders show a 10 mm tile, the real one is about 28 mm; less room for a battery |

Hardware impact: a battery and charger are now needed. The device charges through pogo pins on the dock and keeps its bottom USB-C, and magnets locate it on the dock.

### Revision: compact VC4, no charging

Owner (2026-10-05): shrink the VHS device to the device's own size (VHS aesthetic only, not real cassette size). Charging is not required. The device must sit fixed on the desk at 20–30°, lift off easily for two-handed use, and drop back just as easily. It runs on its USB-C cable, which now leaves from the back edge. `handheld-dock/` was replaced (the pogo-contact images were removed). Prompts are in the scratchpad `prompts16.py` plus inline reruns (keys `vy/`, `vz/`, `vw/`, `vv/`).

- VC4 took four passes. Pass `vy` was still cassette-wide. Pass `vz` was too tight, with the screen filling the face. Pass `vw` got the proportions right (about 120 × 106 × 28 mm, ribbed side bands, stripe band under the glass), but the device stood up at 35–60°. Pass `vv` changed the stand to a 25° grid-engraved wedge with a chrome front bar and two rear pins, which fixed the docked angle (dock_d about 30°, dock_a about 35°). The "seat" renders still draw the device upright above the empty wedge.
- Hover (`vy`): a 110 mm tile on a 25° ceramic wedge with a magnet. Docked angle about 25°. Renders draw the tile about 10 mm thick against the real 28 mm.
- The creature was switched from penguin to cat in VC4 because the penguin read as Tux.

### FX2 Hover: magnetic hold at 30° (hand calculation)

The owner's question: can magnets alone hold a 200 g device on a 30° slope, with no ledge underneath? The reference is the current device's 5-pin magnetic pogo connectors (photo from the owner; force rating unknown).

Gravity at 30°, W = 200 g × 9.81 = 1.96 N:
- along the slope: W sin 30° = 0.98 N (about 100 gf);
- into the slope: W cos 30° = 1.70 N.

A magnet pulls perpendicular to the slope, so it holds against sliding only through friction: μ (1.70 + F_mag) ≥ load along the slope.

| Case | Load along slope | μ | F_mag needed |
|---|---|---|---|
| resting | 0.98 N | 0.3 (plastic on glazed ceramic) | ≥ 1.6 N |
| resting | 0.98 N | 0.8 (silicone pad) | 0 (friction alone holds) |
| swiping, 1 N finger, μ_finger 0.5 | 1.48 N | 0.3 | ≥ 2.2 N |
| swiping | 1.48 N | 0.8 | 0 |

Rocking is the larger risk. A 2 N tap at the top-left corner of a 110 mm tile sits about 78 mm from the centre. The tile pivots on the puck's edge, and the magnet plus weight resist at the puck radius r. The condition is (F_mag + 1.7) · r ≥ 2 · (78 − r):
- r = 15 mm (30 mm puck): F_mag ≥ 6.7 N;
- r = 35 mm (70 mm puck or pad ring): F_mag ≥ 0.8 N.

Typical small magnetic pogo pairs hold a few newtons in pull and only about 20–30% of that in shear, so on their own they are marginal. Fix, keeping the floating look: a hidden boss on the puck that drops into a recess in the tile back takes the sliding load mechanically; contact spread over about 70 mm (a ring or three pads) with a silicone face; magnets only seat the tile and resist peel. The base needs weight or rubber feet so it does not slide on the desk when tapped.

### FX2 with a boss and pad ring; current dock in the VC4 theme

- FX2 Hover (`vh2/`, scratchpad `prompts17.py`): the base gets a 70 mm ring of three silicone pads and a central 12 mm boss with a magnet; the tile back gets a matching recess (see the magnetic hold note above). The docked images show the tile at 20–25°, and hover_dock_a deliberately shows the ring. The lift images draw the base nearly square and less sloped than the 25° wedge.
- CUR, Current Dock × VC4 (`cv/`): uses the owner's photo of the current device and dock as an edit reference (logo ignored). It keeps the mechanics: two 5-pin magnetic pogo connectors on the device's bottom edge, a front ledge with contacts, and a sloped back support. It is restyled with the VC4 cues. Flags: the front ledge must stay below the glass surface so it does not block swipes off the bottom edge; some docked renders show the device resting loosely on the ledge.
- `handheld-dock/` drops the old hover_dock and hover_seat images and adds the vh2 and cv images.

## Minimal-dock concepts (M1–M6), 2026-10-06

The owner asked for a more compact, minimal dock that keeps the synthwave/arcade/future look and the 3.95" screen. Images in `minimal/`, page `MINIMAL_CONCEPTS.html`. All AI-generated from text prompts only (`openai/gpt-5.4-image-2`), no web imagery.

M1 Sunset Fin, M2 Arcade Puck, M3 Pixel Step, M4 Hover Rail, M5 Holo Prism, M6 Mini Grid (VC4 shell on a cut-down CUR dock). Flags: M2a and M5a are drawn steeper than 22 degrees; M3a puts the steps off to one side instead of under the device; M4 rails must print thicker than drawn; M5 needs clear material.

## Minimal stable docks (N1–N6), 2026-10-06

The owner rejected M1–M6: too small to hold the device steadily; they meant minimal in form, not compact. New set in `minimal2/` (same page): a footprint at least the device's size, a low centre of gravity, a front lip, and one accent at most. N1 Slab, N2 Fold, N3 Plinth, N4 Disc, N5 Console, N6 Frame. Text prompts only, `openai/gpt-5.4-image-2`.
