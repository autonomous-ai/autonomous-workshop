---
title: Interlocking joinery for prints
tags: [joinery, mortise, tenon, dovetail, lap, finger-joint, scarf, spline, key, puzzle, burr, interlock, glue, split]
aliases: [woodworking joints, wood joints, carpentry joints, mortise and tenon, mortice and tenon, through tenon, blind tenon, stub tenon, wedged tenon, fox wedge, pinned tenon, pegged tenon, drawbore, draw bore, draw pin, bridle joint, open mortise, slot mortise, half lap, halving joint, lap joint, cross lap, egg crate, finger joint, box joint, comb joint, sliding dovetail, tapered sliding dovetail, through dovetail, half-blind dovetail, lapped dovetail, bowtie, bow tie key, butterfly key, butterfly joint, dutchman, scarf joint, splice joint, tongue and groove, splined miter, spline joint, keyed miter, miter key, jigsaw joint, puzzle joint, puzzle-piece connector, japanese joinery, kigumi, tsugite, shiguchi, kanawa tsugi, komisen, sampo zashi, three-way corner joint, kawai tsugite, burr puzzle, six-piece burr, interlocking puzzle, snap dovetail, twist-lock tenon, keyhole tenon, glue-free joint]
sources:
  - https://www.popularwoodworking.com/techniques/tenons-rule-so-here-are-the-rules-on-tenons/ (tenon 1/3 of the mortised stock, length ≥ 5 × thickness, half the rail width, split when wider than 6 × thickness)
  - https://en.wikipedia.org/wiki/Mortise_and_tenon (through, stub, wedged half-dovetail mortise, pegged, tusk and loose tenons; haunch 1/3 of the length, 1/6 of the width)
  - https://dcstructural.com/wp-content/uploads/2020/09/TFEC-Timber-Design-Guide-20-Draw-Boring-of-Pegged-Joints.pdf (offset 1/8 in softwood, 3/32 in hardwood for a 1 in peg, proportional; end distance ≥ 4 peg diameters in tension; prestress relaxes)
  - https://www.finewoodworking.com/2011/03/29/how-to-make-a-drawbored-mortise-and-tenon-joint (tenon hole offset toward the shoulder; tapered peg pulls the joint tight)
  - https://en.wikipedia.org/wiki/Dovetail_joint (through, half-blind, sliding; 1:6 softwood, 1:8 hardwood, 1:7 compromise)
  - https://www.westsystem.com/app/uploads/2022/12/875-Scarffer-Instruction.pdf (8:1 scarf at 7.5°, eight times the bonding area of a butt joint)
  - https://en.wikipedia.org/wiki/Scarf_joint (tapers 1:8 to 1:10; aircraft repairs no shallower than 1:8; hooked and keyed scarfs)
  - https://www.popularwoodworking.com/techniques/tongue-groove-joinery/ (tongue 1/3 of the thickness; a long tongue breaks at the shoulder; 1/8 in registers)
  - https://en.wikipedia.org/wiki/Butterfly_joint (two dovetails joined at the narrow part; reinforces cracks)
  - https://projects.mcah.columbia.edu/jaanus/node/3413 (kanawa tsugi: oblique, housed, rabbeted, T-shaped, half-blind tenoned scarf; komisen draw pin or two shachi keys)
  - https://www.tomiki.cz/en/2022/04/07/kanawa-tsugi-%e9%87%91%e8%bc%aa%e7%b6%99-japonsky-tradicni-spoj/ (halves laid together then slid lengthwise; wedge-shaped peg closes it; tenons stop lateral movement)
  - https://www.bigsandwoodworking.com/kanawa-tsugi-joinery-models-part-2/ (a deliberate gap at the stub-tenon end so the shoulders close)
  - https://thecarpentryway.blog/2010/11/ming-inspiration-3/ (three-way corner: a long tenon through one rail, a short one trapped by the other; weak unless the stock is large)
  - https://hillbillydaiku.com/2014/06/03/hillbilly-tansu-corner-joint/ (three-way corner with wedged tenons; frames first, connecting rails last)
  - https://www.machines4u.com.au/mag/5-japanese-woodworking-techniques-youll-love/ (sampo-zashi: three or more members into one post, dovetail with mortise and tenon, pegged)
  - https://woodgears.ca/puzzles/3way_joint.html (kawai tsugite: 120° symmetry about the cube diagonal; no slack meant chiselling; the ends broke off first)
  - https://en.wikipedia.org/wiki/Burr_puzzle (sticks at least 3 × their width, notches in half-width cubes, key piece, level)
  - https://formlabs.com/blog/how-to-3d-print-interlocking-joints/ (joint types for printing; comb joints' thin edges break; puzzle joints suit FDM)
  - https://index.ieomsociety.org/index.cfm/item/54883 (CA raised the flexural strength of printed PLA screw joints and lowered it for flat dovetails)
related: [fdm-joining-split-prints, joints, adhesives-and-solvent-welding, layer-anisotropy, fdm-print-orientation-for-strength, fit-derivation, snap-fit-design, dowel-pins-and-press-fits, linear-guides-and-slides, creep-and-stress-relaxation, wall-thickness-and-hollowing, bayonet-and-twist-locks, rod-ends-and-clevises, push-pins-and-clip-fasteners]
updated: 2026-10-01
---

# Interlocking joinery for prints

The default connector for a glued split is a plug
([[fdm-joining-split-prints#connectors]]): it locates, and the glue holds. A
woodworking or puzzle joint earns its extra geometry when the joint must carry
bending, tension or racking by its shape, needs more glue area than the cut
face, aligns a long seam, holds without glue, or comes apart again. Wood's
rules come from the grain; a print's come from the layers.

## Three questions for every interlock

1. **Which directions stay free, and what closes them?** Every interlock
   leaves at least one way in. Name it, and name its closer: glue, a pin, a
   wedge, a snap, gravity, or the next part (proved held). Sweep one half
   along the 26 axis, edge and corner directions
   ([[fdm-joining-split-prints#connectors]]); an interlock is free only round
   its way in.
2. **Where is the neck, and do strands cross it?** The neck is the narrowest
   section that carries the locking force: a tenon's root, a dovetail's waist,
   a jigsaw knob's stem. On a layer boundary it may hold as little as a third
   of its in-plane strength ([[layer-anisotropy#how-much-weaker-across-the-layers]]).
   Put the locking force in the layer plane: lay the part with the neck flat.
3. **What does the glue touch?** Perimeter walls are accurate and bond well,
   and a top skin is flat. A bed face is flat but has elephant's foot
   ([[fdm-first-layer-and-warping#elephants-foot]]), and a shallow slope is a
   staircase of layers. Put glue faces on walls and flat skins.

## Fit, clearance and the joint's own forces

- **Derive every mate** with `cadfits` ([[fit-derivation]]): glued locating
  faces `snug`, dry or removable joints `slip`, slides over about 40 mm and
  many-piece puzzles `free`. Offset the whole profile, so a dovetail flank gets
  its clearance normal to the flank, not only across the width. Lead-ins and
  glue relief: [[fdm-joining-split-prints#clearance-and-glue]].
- **Plastic does not swell shut.** Wood tightens as fibres crush and swell; a
  print creeps instead ([[creep-and-stress-relaxation]]), so a joint that must
  stay tight is glued, pinned or wedged.
- **A flare splits its housing.** A face at angle α to the pull turns a pull
  `F` into a sideways push of `F / (2 tan α)` on each wall (friction lowers it).
  A 1:6 wood dovetail (α ≈ 9.5°) pushes each wall with 3 F; a 30° flank with
  0.87 F. A printed wall takes that push only along its strands: steepen α,
  thicken the wall, or orient it so the push runs along the layers.

## Choosing a joint

| joint | beats a plug when | free direction (closed by) | print each half |
|---|---|---|---|
| **mortise and tenon** | a bar end into a face carries bending or racking | out along the tenon (glue, pin, wedge) | tenon part flat; mortise opening up |
| **pinned / drawbored tenon** | glue-free or removable, in tension | along the tenon (the cross pin) | pin flat or steel |
| **bridle** | two thin bars at a corner or T; big cheeks | along the slot (glue, pin) | both flat |
| **half-lap, cross-lap** | crossing or splicing bars flush | normal to the lap (glue, screw) | both flat, notch up |
| **finger / box** | box corners from flat panels; squareness | along the fingers (glue) | panels flat |
| **sliding dovetail** | a shelf or rail held against lift, no glue | along the slide, both ways (stop, snap) | socket flat; rail part on its side |
| **tapered sliding dovetail** | a long slide binds before it seats | out of the wide end | as sliding |
| **through / half-blind dovetail** | a corner pulled along one axis | out along the tail board's face normal (glue) | both flat, tails in XY |
| **bowtie** | locking a seam across plates from the top | up out of its pocket (glue, cover) | key flat |
| **scarf** | lengthening a bar past the bed | along the slope (glue) | slope cut in plan |
| **kanawa tsugi** | glue-free lengthening in tension, bending, twist | none once keyed | halves flat; key flat |
| **tongue and groove** | edge-joining panels: alignment and glue area | along the tongue (glue) | both flat |
| **splined / keyed miter** | mitred frames that slip as they are clamped | along the spline (glue) | spline flat across the miter |
| **jigsaw** | splitting a flat panel for the bed | normal to the panel, both ways (glue, cover) | both flat |
| **three-way corner** | a leg and two rails meeting, hidden | the last piece's path (pin, wedge) | each bar flat |
| **burr** | a glue-free node of crossing bars; puzzles | the key piece's path | sticks flat |
| **snap-dovetail** | a removable cover on a slide | none until the latch is lifted | latch beam in XY |
| **twist-lock tenon** | a tenon that locks by a quarter turn | the reverse turn (detent) | lugs in XY |

## Mortise and tenon

- **Proportions (wood).** Tenon one third of the mortised stock, so each
  mortise cheek is a third too. Length at least 5 × its thickness, width about
  half the rail; wider than 6 × its thickness, split it in two. A haunch is a
  third of the length by a sixth of the width.
- **In a print the cheeks decide.** Each cheek at least
  `cadprint.shell_wall(NOZZLE)`, the tenon at least four lines thick; the
  one-third rule is then a ceiling for thin stock only. Cheek glue area
  `2 W L` against the butt's `W T`: a tenon 5 T long gives ten times the butt.
- **Print** the tenon's part flat, strands along the tenon; a standing tenon
  snaps at its root layer. A mortise open upward is a pocket; a horizontal
  one has a bridged or teardrop roof ([[fdm-bridging-and-sacrificial-layers#how-far-a-bridge-can-go]]).
  A stub (blind) tenon stops short of the mortise floor by the glue gap.
- **Wedged through tenon.** The mortise flares on the exit face, and wedges
  driven into kerfs spread the tenon into the flare: permanent. Kerf the
  tenon square to the bed so its halves spread sideways, bending in the layer
  plane, and keep their strain inside [[snap-fit-design#cantilever]]. A tapered key across a
  tenon is the cotter of [[rod-ends-and-clevises]].
- **Pinned and drawbored.** The tenon's peg hole is offset toward the
  shoulder, so a tapered peg pulls the shoulder tight. Timber framers
  offset about 1/8 D in softwood and 3/32 D in hardwood (D the peg diameter);
  in tension the hole sits at least 4 D from the tenon's end. The prestress
  relaxes, and then the peg carries the whole applied load. A PLA peg is
  brittle in the bending a drawbore forces: use PETG or a steel pin with a
  tapered nose, start below 0.1 D, and test.

## Laps, bridles and fingers

- **Half-lap**: each bar notched to half its thickness, glue on the overlap.
  Print both notch up (flip one in the layout); the lap faces are then flat
  skins. A **cross-lap** blocks both in-plane directions: slot width
  `slot_for(T, fit)`, each slot half the depth.
- **Bridle**: an open slot in one member's end round a tenon on the other; a
  pin through its two big cheeks makes it a clevis ([[rod-ends-and-clevises]]).
- **Finger (box) joint** of finger width `w` on panels of thickness `t`:
  side-face glue area over butt area ≈ `t / w`. Fingers wider than the panel is
  thick add almost no glue area; the joint's value is then squareness and
  registration. Fingers print as wall profile and need at least four lines;
  thin combs break.

## Dovetails

- **Free directions.** Sliding: both ways along the slide; stop one end, and
  close the other with a snap or glue. Through and half-blind: only outward
  along the tail board's face normal, so glue or the next corner holds it.
- **Angle.** Wood uses 1:6 to 1:8 (9.5° to 7.1°), 1:7 as a compromise. In
  print, choose α from the splitting push above. The 60° flank of
  [[joints#prismatic-joints]] is α = 30°.
- **Print.** Tails in a flat board flare in XY, with strands across the
  waist. A sliding-dovetail rail grown upward from a flat base has its waist
  on a layer line, and lift peels it. Print that part on its side, or make
  the rail a separate double-dovetail key, printed flat, glued in both
  halves. Slide axis horizontal, a 30° flank overhangs 30° from vertical and
  prints ([[overhangs-and-print-orientation#bridge-ledge-overhang]]).
- **Long slides bind** when pushed off their axis
  ([[linear-guides-and-slides#the-binding-ratio]]). A **tapered sliding
  dovetail** runs at `free` clearance until the last part of its travel and
  reaches `snug` only at home: taper per side `(c_free − c_snug) / L_taper`.
- **Snap-dovetail.** A cantilever latch on the slide's tail drops into a notch
  at home. The dovetail carries every load; the latch only resists sliding
  back ([[snap-fit-design#cantilever]]).
- **Glue.** In one PLA bending test CA weakened a flat dovetail and
  strengthened a screw joint: glue a dovetail only thin, in a snug fit.

## Scarfs and the kanawa tsugi

- **Slope** `s:1`, length over thickness. Glue area ≈ `s` times the butt (an
  8:1 scarf has eight times the bonding area). With `θ = atan(1/s)` and bar
  stress σ, the glue sees `σ sin²θ` normal and `σ sinθ cosθ` shear. Wood uses
  1:8 to 1:10, aircraft no shallower than 1:8.
- **Cut it in plan.** With the slope seen from above, both scarf faces are
  perimeter walls: accurate, smooth, bonded along strands. Cut in elevation,
  each 0.2 mm layer step at 1:8 is 1.6 mm long and the feather edge is a
  single layer.
- **Nib the feather edge** at `cadprint.min_wall(NOZZLE)`; a knife edge does
  not print ([[wall-thickness-and-hollowing#knife-edges-are-walls-too]]). A
  plain scarf slides along its slope until glued; hooks, nibs or keys lock it.
- **Kanawa tsugi**: an oblique, housed, rabbeted scarf of two identical
  halves, a T-shaped stub tenon on each end entering a housing on the other.
  Lay the halves together and slide them lengthwise until the tenons engage;
  a wedge-shaped draw pin (komisen) or two keys (shachi) through the central
  gap then pushes them apart along the beam and closes the shoulders. The
  tenons stop lateral movement; a gap at each tenon end lets the shoulders
  seat first. Print one model twice, flat, scarf faces as walls; print the key
  flat, slot `slot_for(KEY_T, SEAT)`, its taper drawing the joint. Reprint the
  key if it loosens.

## Panels: tongues, splines, keys and jigsaws

- **Tongue and groove.** Tongue about a third of the stock thickness and as
  long; a longer tongue breaks at its shoulder, and deep groove walls crack.
  Registration alone needs only a short tongue. In print the tongue is at least
  1.5–2 line widths, lies in XY, and the groove is deeper by the glue gap.
- **Splined miter.** A thin spline in slots across the miter faces keeps it
  from sliding as it is clamped; print it flat, strands across the miter line.
  A **keyed miter** glues keys into kerfs cut across the corner after glue-up.
- **Bowtie.** Two dovetails joined at the waist, set across a seam. Print the
  key flat so strands cross the waist; give the pocket a floor of at least
  `cadprint.min_wall(NOZZLE)`; glue or a part above closes the way up.
- **Jigsaw.** A knob on a neck, in the panel's plane. It blocks every in-plane
  direction and leaves both normals free. The neck carries the tension,
  `F = σ_allow · w_neck · t`, so size it from the load; the head is wider than
  the neck by twice the undercut. Both halves print flat, their edges are
  walls. Close the normal with glue, a cover plate or a bowtie.

## Locking nodes: three-way corners, burrs and twist-locks

- **Three-way corner** (a leg and two rails). In one form the leg's long tenon
  runs through one rail and its short tenon is trapped by the other rail's
  tenon. Three members compete for one space, so it is weak unless the stock
  is large. A tansu corner wedges its tenons: frames first, connecting rails
  last, no glue. The sampo-zashi brings three or more members into one post
  with dovetails and tenons, pegged. The kawai tsugite uses the cube's 120°
  symmetry about its diagonal to join straight or at a right angle; built with
  no slack it needed chiselling, and its thin ends broke first.
- **Printing any node.** Write the assembly order: each member needs a clear
  path when it goes in, and the last one is pinned, wedged or keyed. Strands
  cross every neck. Tenons meeting in one post must keep
  `cadprint.shell_wall(NOZZLE)` between them; check each pair.
- **Burr.** Sticks at least three times their width, notched in half-width
  cubes; a traditional burr's unnotched key slides out first, and its level is
  the moves to free the first piece. Print sticks on a face, notches up:
  `slip` per face for a puzzle, `snug` for a node that must stay.
- **Twist-lock tenon.** Lugs on a round tenon pass a keyhole mortise; a
  quarter turn puts them under an undercut, and a detent bump stops the
  reverse turn. It is a bayonet ([[bayonet-and-twist-locks]]); lugs in XY.

## Failure classes

| symptom | rule that prevents it |
|---|---|
| tenon or tail snaps flush at its root | the neck's part prints flat; strands cross the neck |
| socket wall splits along a layer under pull | `F / (2 tan α)` inside the wall's in-plane strength |
| halves will not meet with glue in | `cadfits` clearance plus a relief path |
| an "interlocked" part slides out one way | name the free direction and its closer; 26-direction sweep |
| scarf glue line fails | cut the scarf in plan, nib the edge |
| a puzzle or node cannot be assembled | written order; a clear insertion sweep per member |
| drawbore peg breaks | PETG or steel peg; offset under 0.1 D |
| joint loosens over months | glue, pin or wedge; never rely on press alone |

## Checks

```python
import math, cadfits, cadprint
TENON_T = cadfits.peg_for(MORTISE_W, SEAT)
assert (STOCK_T - MORTISE_W) / 2 >= cadprint.shell_wall(NOZZLE), "mortise cheeks too thin"
assert TENON_W <= 6 * TENON_T, "split a wide tenon in two"
assert DRAWBORE_OFFSET <= 0.125 * PEG_D, "drawbore offset breaks the peg"
assert PEG_END_DIST >= 4 * PEG_D or not TENSION, "peg tears out of the tenon end"
push = F_PULL / (2 * math.tan(math.radians(FLARE_DEG)))
assert push <= WALL_CAPACITY_IN_PLANE, f"flare splits the socket with {push:.0f} N"
assert SCARF_SLOPE >= 8 and SCARF_NIB >= cadprint.min_wall(NOZZLE), "scarf too steep or feathered"
assert NECK_IN_LAYER_PLANE, "locking force crosses the layers"
assert all(CLOSED_BY.get(d) for d in FREE_DIRECTIONS), "a free direction has no closer"
```
