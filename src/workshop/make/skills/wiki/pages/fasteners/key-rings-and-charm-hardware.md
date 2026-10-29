---
title: Key rings, keychains and charm hardware
tags: [keychain, key-ring, split-ring, jump-ring, charm, clasp, ball-chain, lanyard, loop, hanging-hole]
aliases: [split ring, keyring, key ring, keychain hole, keyring hole, keychain loop, jump ring, lobster clasp, lobster claw, swivel clasp, trigger snap, swivel snap hook, ball chain, bead chain, beaded chain, lanyard, phone strap, phone charm, bag charm, charm loop, screw eye, eye pin, head pin, bail, pendant, hanging hole, ring ligament, pocket token]
sources:
  - https://www.mcmaster.com/products/split-key-rings/ (zinc-plated split rings, OD x ID / thickness / wire, in - 3/4 x 5/8 / 1/8 / 1/16; 1 x 13/16 / 1/8 / 5/64; 1 1/2 x 1 1/4 / 3/16 / 3/32; half-round and full-round wire)
  - https://tornadoparts.com/products/1-2-heavy-duty-split-key-rings-usa-10-pack (1/2 in ring - OD 0.670, ID 0.526, A 0.072, B 0.105, wire 0.064 in)
  - https://keyring.com/content/USA-Made-Split-Keyrings-Size-Comparison.pdf (nominal 1/2 in ring is 0.670 in OD; nominal 1 in is 1.100 in OD)
  - https://core-electronics.com.au/split-key-ring-attachment-20mm-pack-of-50.html (20 mm ring - ID 17.2, ring thickness 2.6 mm, carbon spring steel)
  - https://en.wikipedia.org/wiki/American_wire_gauge (16, 18, 20 AWG = 1.291, 1.024, 0.812 mm)
  - https://www.firemountaingems.com/learn/categories/ask-the-experts/C794-ask-the-experts.html (jump ring OD = ID + 2 x wire)
  - https://www.firemountaingems.com/resources/ask-the-experts/aa6m (22-16 gauge half-hard for durability; 18-16 gauge for a large pendant)
  - https://thebeadchest.com/blogs/jump-rings/jump-ring-types (closed jump rings are stronger and less likely to come undone than open ones)
  - https://stonesandfindings.com/product/fkc1s-6x11mm-rounded-lobster-claw-clasps-sterling-silver-925/ (6 x 11 mm lobster clasp - gate opening 1.69 mm, claw ID 3.57 x 3.68, end loop ID 1.21 x 2.18)
  - https://artbeads.com/jewelry-supplies/30mm-round-antique-brass-swivel-lobster-clasp (30 mm swivel lobster - trigger opening 5.5 mm, eye hole 5 mm, 6 mm wide)
  - https://www.mcmaster.com/products/trigger-snaps/ (swivel-eye snap hooks 1 7/8-2 5/16 in usable length, 3/8 in opening, 3/8-3/4 in eye, capacity not rated)
  - https://www.mcmaster.com/products/ball-chain (trade sizes 3, 6, 10 = 3/32, 1/8, 3/16 in beads; 20, 30, 40 lbf in nickel-plated steel)
  - https://en.wikipedia.org/wiki/Ball_chain (size 3 is 2.4 mm; connectors snap on and off without tools; relatively low strength)
  - https://qidi3d.com/blogs/guides/add-hole-to-3d-model-keychain (holes - 4 mm standard ring, 5 mm heavy ring, 3.5 mm ball chain, 9-10 mm doubled paracord, 8 mm or a slot for a flat lanyard clip; strands x thickness + 1 mm; 2 mm of material, 3 mm on a real keyring; model 0.2 mm over; lay flat)
  - https://www.namestl.com/personalized-3d-printed-keychains-slicer-settings (5 mm hole, 3 mm to the edge, at least 5 mm thick, 4-6 walls, PETG for daily carry)
  - https://jlc3dp.com/blog/3d-printed-keychains-tips (3-4 mm hole, at least 3 mm thick, 30-60 mm long, at least 3 walls at the loop)
  - https://www.cnckitchen.com/blog/comparing-pla-petg-amp-asa-feat-prusament (hooks flat / upright - PLA 73 / 40 kg, PETG 55 / 25 kg; flat PETG stretched without snapping)
  - https://resinplay.sg/products/screw-eye-pins-for-resin-jewellery-set-of-3-colours-750-pcs (screw eyes 4 x 8 mm with a 2 mm eye, 5 x 10 mm with a 3 mm eye; pilot hole first)
  - https://www.beadsandbeading.com/blog/securing-eye-pins-in-polymer-clay-charms/17354/ (eye pins pull out of a body they do not bond to; a head pin through a through-hole cannot; 20-21 gauge half-hard)
  - https://www.stickermule.com/support/faq/keychains (custom keychains 0.75 x 0.75 to 4 x 4 in; acrylic about 2.83 mm)
  - https://createpins.com/blog/custom-keychain-thickness-guide/ (typical thickness - metal 1.8-2.0, acrylic 3.0, PVC 4.0 mm; 3.5 mm and up may feel bulky)
related: [nfc-tags-in-prints, straps-buckles-and-textile-attachment, layer-anisotropy, fdm-hole-accuracy, fdm-minimum-feature-sizes, fdm-first-layer-and-warping, toy-safety-constraints, stability-and-tipping, mass-properties-and-measurement, rod-ends-and-clevises, friction-wear-and-lubricants, laid-rope-tubes]
updated: 2026-10-10
---

# Key rings, keychains and charm hardware

A printed token hangs from steel many times stronger than itself, so the
print fails first: a ligament snaps across layers, the ring binds or files
through an edge, or the charm hangs crooked. Each rule is an assert to pass
before any gate runs. NFC tags near the ring: [[nfc-tags-in-prints]].

## Which hardware each object takes

| object | hardware | why |
|---|---|---|
| pocket keychain token, key cover | steel split ring, 20-25 mm | two spring coils; opens only when pried |
| heavy or large token | split ring 28-38 mm, 2.0-2.4 mm wire | stiffer coil, takes a thicker boss |
| bag charm, zipper pull | swivel lobster or snap hook, then a split ring or closed jump ring | clips off; the swivel stops the strap twisting |
| pendant, small charm | jump ring, 18-16 AWG, closed where it can be | one thin wire through a small hole |
| phone-strap charm | cord loop (girth hitch) or a jump ring onto the strap | hole sized from the doubled cord |
| badge, tag, giveaway | ball chain #3 | cheap, swivels by itself, low strength |
| figure with no room for a hole | screw eye in a modelled pilot bore, or a head pin through a bore | metal makes the loop; the print holds the metal |

Never hang a token on an open jump ring alone: its ends only butt, and a
token riding round levers them apart at the gap. Never print the ring: it is
a thin curved beam crossing layers ([[straps-buckles-and-textile-attachment#d-rings-and-loops-printed-or-bought]]).

## Split rings: what the size names mean

A split ring is about two turns of spring wire, usually **half-round** (flat
face inward, so the coils lie flat on each other), sometimes full-round. The
hole sees the **coil section**: radial width `A = (OD - ID) / 2` by the
two-turn stack `B`, sold as "ring thickness" or "B" (a vendor's "A" column
equals `(OD - ID) / 2`).

| ring | OD | ID | A | B | wire | min hole `hypot(A,B) + 1` |
|---|---|---|---|---|---|---|
| 20 mm carbon spring steel | 20.0 | 17.2 | 1.40 | 2.60 | - | 4.0 |
| 1/2 in heavy duty | 17.0 | 13.4 | 1.83 | 2.67 | 1.63 | 4.2 |
| 3/4 in zinc (McMaster) | 19.1 | 15.9 | 1.59 | 3.18 | 1.59 | 4.6 |
| 1 in x 13/16 zinc (McMaster) | 25.4 | 20.6 | 2.38 | 3.18 | 1.98 | 5.0 |
| 1 1/2 in zinc (McMaster) | 38.1 | 31.8 | 3.18 | 4.76 | 2.38 | 6.7 |

The nominal size is not the OD (one maker's "1 in" is 27.9 mm OD, another's
25.4) and `B` at one OD varies by a fifth between makers: size the hole from
the ring you ship, measured. The guides' 4 mm hole for a standard ring and
5 mm for a heavy one agree with the last column.

## Jump rings, clasps, ball chain, cords and screw eyes

- **Jump rings** are sold by gauge and ID, `OD = ID + 2 * wire`; 20, 18 and
  16 AWG are 0.81, 1.02 and 1.29 mm. Suppliers advise 22-16 gauge half-hard,
  18-16 for a large pendant. A closed (soldered) ring is stronger and stays
  shut; an open one is for parts that must come off.
- **A jewellery lobster clasp never clips the print**: a 6 x 11 mm one opens
  1.69 mm and is 3.6 mm inside, so it takes a jump ring. A 30 mm keychain
  swivel lobster opens 5.5 mm with a 5 mm swivel eye; snap hooks of 48-59 mm
  usable length open 9.5-12.7 mm, have 9.5-19 mm eyes and **no rated load**.
- **Ball chain** #3, #6, #10 has 2.4, 3.2, 4.8 mm beads (3/32, 1/8, 3/16 in)
  and breaks at about 89, 133, 178 N (20, 30, 40 lbf) in plated steel. The
  hole passes one bead (3.5 mm for #3): the chain is threaded before the
  connector closes. The connector snaps off without tools: a breakaway.
- **Cords**: hole `>= strands x cord diameter + 1 mm`; doubled 4 mm paracord
  takes 9-10 mm, a flat lanyard clip 8 mm or a slot
  ([[straps-buckles-and-textile-attachment#webbing-sizes-and-the-slot-that-takes-them]]).
- **Screw eyes** for charms are about 4 x 8 mm (2 mm eye) and 5 x 10 mm
  (3 mm eye), set in a pilot hole. **Eye pins** pull out of anything they do
  not bond to; a head pin through a through-hole cannot.

## The hole a ring passes through

- **Both coils of a split ring sit in the hole** and the token swings round
  them, so the hole clears the section's diagonal:
  `HOLE_D >= hypot(A, B) + 1.0`. The 1.0 mm covers the swing, the printed
  undersize (guides model 0.2 mm over;
  [[fdm-hole-accuracy#why-a-vertical-hole-comes-out-small]]) and the bed lip;
  add twice any paint or coat, measured. One strand (jump ring, cord):
  `HOLE_D >= max(2.0, wire + 1.0)`, Ø2 mm being FDM's smallest hole.
- **The ring must also go round the ligament.** The ligament's section,
  width `w` (hole edge to outer edge) by thickness `t`, fits inside the ring
  with room to turn: `RING_ID >= hypot(w, t) + 0.5`. Any split ring clears
  it; a jump ring may not. A 2 x 3 mm ligament needs ID >= 4.1 mm: a 6 mm
  OD ring on 1 mm wire binds, a 7 mm one swings.
- A clasp clips straight onto a printed bar only when the bar's thinner side
  passes the gate with 0.5 mm spare and the bar fits the claw, both
  measured; otherwise put a ring between. Keep the hole's axis along Z: it
  prints round, where a horizontal hole facets under an overhanging roof.

## The ligament and the loop boss

- **Width**: at least 2 mm of solid plastic round the hole, 3 mm on a real
  keyring (the guides), in whole perimeters: `w >= 2 * walls * line_w` lets
  the hole's and the outline's loops both fit, so the ligament is continuous
  strands, not gap fill (3 walls of 0.45 mm need 2.7 mm). Edge distance in
  the pull direction at least `w`, so shear-out never governs.
- **Thickness**: guides ask 3 mm (JLC) to 5 mm (namestl). Keep the token at
  least 3 mm and the boss round the hole at least 4 mm; a thinner token gets
  a raised boss or a wider ligament, since capacity goes with `w * t`: keep
  `w * t >= 12 mm^2` a side (3 mm x 4 mm).
- **Capacity** is the lug tearing check
  ([[rod-ends-and-clevises#knuckle-joint-proportions-and-failure-checks]]),
  `P = 2 w t sigma / (SCF * S)`. Worked: `w = 3`, `t = 4`, PLA X-Y 52 MPa,
  SCF 3, S 2 gives 208 N printed flat, three times the 67 N toy tension test
  ([[toy-safety-constraints#use-and-abuse-tests-what-breaks-off-means]]).
- Make the boss a round end concentric with the hole and fillet its root
  (r >= 1 mm): PLA and PETG are brittle at a notch ([[filament-properties]],
  [[ribs-and-stiffening#fillets-and-stress-concentration]]).

## Lay the loop flat, never across layers

A pull on a loop is tension in its two ligaments: printed flat it runs along
strands; on a loop standing up from an upright figure it pulls layer welds
apart. A hook test broke PLA at 73 kg flat and 40 kg upright, PETG at 55 and
25 kg. At the design value Z = 0.3 X-Y
([[layer-anisotropy#how-much-weaker-across-the-layers]]) the boss above
falls to 62 N, under the 67 N test. For a figure printed upright:

1. make the loop a flat tab, or print the figure lying down;
2. run a cord or head pin through a straight bore with a stopper below, so
   the print bears in compression ([[laid-rope-tubes#hanging-a-figure-on-the-strand]]);
3. set a screw eye in a pilot bore modelled along Z at its thread's root
   diameter, with CA ([[adhesives-and-solvent-welding#what-bonds-what]]);
   pull-out along Z still loads layers, so add perimeters round the bore.

## Round the hole edges so the ring does not saw

Hardened steel wears PLA and PETG
([[friction-wear-and-lubricants#ordinary-filaments-wear-fast-against-steel]]).
The ring swings at every step and bears on the hole's **edges**, not its
bore, so a square edge is a line contact the ring files through. Chamfer the
bed-side edge at least the base chamfer (about 0.3 mm), or the
elephant's-foot lip narrows the hole and leaves a burr
([[fdm-first-layer-and-warping#elephants-foot]]); the break's shape is
[[rounded-bodies-on-the-print-bed#breaking-the-bed-edge]]. Round or chamfer the top
edge >= 0.5 mm (Ø1 mm is the smallest printable fillet;
[[fdm-minimum-feature-sizes#features-pins-and-gaps]]); a countersunk or
radiused entry spreads the contact. Round the boss's outer edge too: the
ring's end slides over it when the token is threaded on.

## Loads on a carried keychain

It is dropped (toys are tested 4 times from 0.92 m), yanked by a key caught
in a pocket, sat on and flexed. No standard sets a keychain pull: design the
loop to the 67 N toy test with the factors above, so the bought hardware is
the weakest link (a ball chain lets go near 89 N). **Delamination fails
first**, then a notch at the boss root. Flat PETG hooks stretched without
snapping through, which is why guides pick PETG for daily carry; PLA also
softens in a parked car ([[heat-resistance-of-printed-parts]]).

## Hanging upright: hole over the centre of mass

A body hung from a pin rests with its centre of mass (CoM) straight below the
pin, so the hole's centre goes on the CoM line along the intended vertical.
An offset `e`, with the CoM `h` below the hole, tilts it `atan(e / h)`: 3 mm
off a CoM 18 mm below is 9.5°. Keep `h` large (hole near the top): a hole
just above the CoM rights the charm weakly and friction leaves it crooked.

```python
import math
from build123d import Vector
com = token.center()                    # volume centroid, density 1
hole = Vector(HOLE_X, HOLE_Y, 0)        # token drawn with "up" along +Y
e, h = hole.X - com.X, hole.Y - com.Y
assert h > 0, "hole below the CoM: it hangs upside down"
assert abs(math.degrees(math.atan2(e, h))) <= TILT_MAX_DEG
```

A sealed tag, magnet or ballast moves the CoM: weight by density
([[mass-properties-and-measurement#density-weighted-centre-of-mass-for-mixed-materials]]).
On a cord a figure leans both ways, so check its front-back offset too.

## Spinning on a cord, a chain or a clip

**A round hole on a cord, ball chain or strap loop is a point suspension**:
turning about the vertical costs only cord twist, so the charm spins and
shows its back. To hold a face forward the hanger must resist that turn: a
slot matched to a flat strap's width, or two holes a bar apart (both strands
pull it back square). On a split ring the wire through the hole fixes the
face across the ring's tangent: the token swings but does not spin. A swivel
clasp lets a bag charm turn without winding up its strap.

## Pocket comfort and size

Commercial keychains run 19-102 mm (0.75-4 in) across; metal ones are
1.8-2.0 mm thick, acrylic about 3 mm, PVC 4 mm, and 3.5 mm and up starts to
feel bulky. A printed token is 3-5 mm thick, so keep it within about 75 mm
long (a design choice) and light. Round every outline corner and face edge
([[form-and-finish-heuristics#edges-fillet-or-chamfer]]); no thin points,
horns or re-entrant hooks that catch pocket fabric or snap to a sharp tip.
A token that fits the 31.7 mm cylinder is a small part ([[toy-safety-constraints#small-parts-the-choke-test]]).

## Checks

```python
import math
A = (RING_OD - RING_ID) / 2                        # coil radial width
assert HOLE_D >= max(2.0, math.hypot(A, RING_B) + 1.0)  # both coils swing
assert LIG_W >= max(3.0, 2 * WALLS * LINE_W)       # keyring ligament, whole perimeters
assert EDGE_ABOVE >= LIG_W                         # shear-out never governs
assert TOKEN_T >= 3.0 and BOSS_T >= 4.0 and LIG_W * BOSS_T >= 12.0
assert RING_ID >= math.hypot(LIG_W, BOSS_T) + 0.5  # ring turns round the ligament
P = 2 * LIG_W * BOSS_T * UTS_XY * (1.0 if LOOP_FLAT else 0.3) / (3 * 2)
assert P >= 67.0, f"loop holds {P:.0f} N; toy tension test is 67 N"
assert HOLE_CHAMFER_BED >= 0.3 and HOLE_EDGE_R >= 0.5
```
