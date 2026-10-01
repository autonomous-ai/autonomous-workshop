---
title: Posable figure joints
tags: [figure, articulation, joint, friction, ratchet, toy, pose, doll]
aliases: [action figure articulation, points of articulation, poa, articulated figure, posable figure, poseable figure, action figure joints, doll joints, bjd, ball jointed doll, ball-jointed doll, swivel joint, cut joint, peg joint, mushroom joint, mushroom peg, ball hinge, ball-hinge, swivel hinge, swivel-hinge, hinged peg, double-jointed elbow, double-jointed knee, double hinge, double joint, butterfly joint, butterfly shoulder, pectoral joint, drop-down hip, drop hip, h-joint, h-hip, disc hip, ab crunch, rocker ankle, ankle tilt, ratchet joint, click joint, clicky joint, dumbbell joint, polycap, poly-cap, bicep swivel, thigh cut, kit figure, strung figure, elastic stringing, super articulation]
sources:
  - http://www.oafe.net/articulation/terms.php (peg joint turns 360°; pin joint about 90°; a cut at 90° to the limb only spins)
  - https://poeghostal.com/action-figure-glossary (mushroom peg, hinged joint, dumbbell joint, H-joint hips flush with the pelvis)
  - https://toylandeu.com/blogs/articles/action-figure-articulation (double-jointed elbows and knees past 160°; ratchets on larger figures; ankle rockers; ball joints loosen first, hinges stay tight longer)
  - https://www.cartoonkingdom.ca/blogs/collectors-corner/articulation-daze-three-modern-action-figure-terms-you-need-to-know (butterfly joints let figures cross their arms and hold weapons)
  - https://patents.google.com/patent/US8308524B2/en (pectoral shoulder sections on a vertical pin in the chest; collar friction pad held by screw tension)
  - https://patents.google.com/patent/US6817921 (double-jointed elbow and knee from two intermediate members; a kneecap stop against over-swing)
  - https://patents.google.com/patent/US9919230B2/en (hip discs on a central friction plate; post about half the disc diameter; ribbed faces)
  - https://patents.google.com/patent/US5087219 (hex shaft in a hex socket turns under excessive force so the arm does not break)
  - https://tfwiki.net/wiki/Ratchet_(mechanism) (a ratchet carries more than a friction joint of its size; plastic ratchets with the pawl moulded in; one axis)
  - https://tformers.com/articulation-breakdown-week-epilogue-ratcheting-joints/31213/news.html (metal ratchet springs fatigue and corrode; plastic teeth erode)
  - https://tformers.com/articulation-breakdown-week-day-2-swivels/31193/news.html (mushroom pegs; too much tension shears a peg)
  - https://goniometer.io/range-of-motion (AAOS normal joint ranges)
  - https://makeronline.com/en/model/Dummy%2013%20-%20version%201.0!/237622.html?trackModuleType=13 (kit figure designer: ABS/ASA/PETG for joints, not PLA; compliant swivels; 0.15 mm elephant-foot compensation)
  - https://gunplahangar.com/learn/guides/fixing-loose-joints (creep and polycap wear loosen joints; coatings add fractions of a millimetre; cement swells 0.05–0.2 mm)
  - https://yukibjd.com/blogs/bjd-guide/giving-your-bjd-a-new-lease-on-life-a-super-detailed-restringing-tutorial (two elastic loops; too tight kicks back, too slack flops)
  - https://www.flashforge.com/blogs/news/how-to-3d-print-action-figures (joint axes in the X-Y plane against delamination; metal pins in high-wear joints)
  - https://reality.tf.fau.de/projects/jointfit/jointfit-lowres.pdf (Calì et al. 2012: friction bands in print-in-place ball joints; twist feels stiffer than bend)
related: [ball-and-socket-joints, joints, hinges-and-pin-joints, latches-detents-and-ratchets, print-in-place-mechanisms, flexi-chain-joints, snap-fit-design, creep-and-stress-relaxation, arm-and-gripper-sizing, stability-and-tipping, toy-safety-constraints, carved-figures-on-split-prints, flexure-materials-and-snap-strain]
updated: 2026-10-01
---

# Posable figure joints

A posable figure is a chain of friction or click joints that must hold
every pose against the weight outboard of it. This page says which joint
goes where, how much holding torque each one needs, when friction stops
being enough and a ratchet takes over, and how printed figures get friction
that lasts. The ball itself is sized in [[ball-and-socket-joints]], hinges in
[[hinges-and-pin-joints]], and limbs carved onto split prints in
[[carved-figures-on-split-prints]].

## Joint by body location

Ranges are the AAOS normal values for a person: the targets a figure is
judged against.

| location | usual build | anatomical range | note |
|---|---|---|---|
| neck | ball; ball-hinge to tilt the head; double ball to look up | flex 45°, ext 45°, side 45°, turn 60° | a ball or hinged peg also makes the head removable |
| shoulder | ball, or swivel-hinge; butterfly (pectoral) hinge inboard | flex 180°, abduct 180°, ext 60° | butterflies let arms cross the chest and hold a weapon |
| upper arm, thigh | swivel cut | shoulder turn 90° out / 70° in; hip turn 45° each way | a cut square to the limb only turns it; a 45° cut also bends it |
| elbow | hinge; double hinge for a deep bend | flex 150° | one pin gives about 90°, a double hinge past 160° |
| wrist | ball, or swivel-hinge on a peg | flex 80°, ext 70°, deviation 20° / 30° | hands on pegs swap |
| waist, abdomen | waist swivel; ab crunch hinge or midriff ball | — | the crunch carries the whole upper body |
| hip | ball; drop-down hip; H or disc hip | flex 120°, ext 30°, abduct 45° | stance joint: carries the figure |
| knee | hinge; double hinge | flex 135° | stance joint; add a kneecap stop |
| ankle | hinge plus a rocker (side tilt), or ball | up 20°, down 50°, in 35°, out 15° | rockers keep the foot flat in a wide stance |

## The joint forms

| form | build | freedoms | holds by |
|---|---|---|---|
| **swivel, cut, peg** | peg across the limb's section in a hole | 1 turn, 360° | friction on the peg |
| **mushroom peg** | peg with a flared head snapped through a hole | 1 turn | head retains; friction holds |
| **hinge (pin)** | knuckle on a pin in a clevis ([[hinges-and-pin-joints]]) | 1 bend | pin or knuckle-face friction |
| **ball** | ball on a neck in a socket ([[ball-and-socket-joints]]) | 3 turns | socket preload |
| **ball-hinge** | a hinge whose post ends in a ball | bend plus turn and tilt | both |
| **swivel-hinge, hinged peg** | a hinge on a post that swivels in a hole | bend plus turn | both |
| **double hinge** | two parallel pins joined by a short link (two intermediate members) | 1 bend, twice the range | both pins; a kneecap stop limits it |
| **butterfly, pectoral** | shoulder block on a vertical pin inside the chest | arm forward and back | hinge friction |
| **drop-down hip** | hip ball on a lever hinged in the pelvis that swings down | abduction past the crotch sculpt | lever hinge friction |
| **H or disc hip** | leg discs flush with the pelvis either side of a central friction plate | ball-like range, flush faces | face friction; post about half the disc diameter; ribbed faces |
| **ab crunch** | hinge, or a ball, in the midriff | torso bend | friction or ratchet |
| **rocker ankle** | ankle hinge on a fore-aft axis | side tilt | friction |
| **ratchet, click** | toothed disc and a sprung pawl ([[#ratchet-joints-for-heavy-limbs]]) | 1 axis, in steps | teeth |
| **dumbbell** | ball, peg, ball | ball-like, less range | friction at both ends |

## Holding torque from limb weight

Sum every part outboard of the joint, the hand and its accessory included,
at its horizontal distance from the joint in the worst pose. This is the
static sum used for an arm ([[arm-and-gripper-sizing#static-joint-torque-at-full-reach]]):

```text
M_g = g · Σ_j m_j · x_j                 limb segments, hand, accessory
stance joints (ankle, knee, hip) carry everything above them: M_g = g · m_above · x_cg
T_hold ≥ SF · M_g                       the pose holds
T_slip · SF_break ≤ T_break             the joint gives before its peg, pin or neck breaks
```

- **Worked, 1:12 figure (about 150 mm).** Arm 5 g with its centre 25 mm out,
  a 6 g accessory in the hand at 60 mm: `M_g` = 9.81 × (0.005 × 25 +
  0.006 × 60) = 4.8 N·mm. With `SF` = 2 that needs 9.5 N·mm. On a 4 mm-radius
  ball with μ = 0.3 and `k` = 2/π, it takes `ΣN` ≈ 12 N
  ([[ball-and-socket-joints#holding-torque-friction-on-the-ball]]). The
  accessory is three quarters of it.
- **Stance joints carry the most.** The whole figure, 80 g, with its centre
  20 mm past one ankle in a lunge: `M_g` = 15.7 N·mm, so 31 N·mm at `SF` = 2,
  over three times the shoulder.
- **Scale is against friction.** Scale a figure by `s` and the gravity
  moment grows as `s⁴` (mass `s³`, lever `s`). A friction joint scaled with
  it at the same contact pressure grows only as `s³`. The margin falls as
  `1/s`: a joint that holds at 1:12 sags at 1:6. Larger figures use ratchets
  because a ratchet of a given size carries more than a friction joint, and
  ball joints are the first to loosen.
- **Give before breaking.** One patent seats an arm on a hex shaft in a hex
  socket that turns under excessive force, so the arm does not break. Any
  joint's slip torque must stay below the break torque of its weakest peg or
  neck ([[ball-and-socket-joints#the-neck-is-the-fuse]]). A child's toy also
  meets the abuse tests ([[toy-safety-constraints#use-and-abuse-tests-what-breaks-off-means]]).
- **Twist feels stiffer than bend.** The hand twists a limb at its thickness
  and bends it at its length. The same joint torque therefore resists twist
  more, which Calì et al. found welcome.

## Ratchet joints for heavy limbs

A posing ratchet is a two-way detent: teeth on a disc and a sprung pawl,
with both flanks sloped so a hand moves it either way
([[latches-detents-and-ratchets#detent-holding-force]]).

```text
T_click = F_p · r_t · tan(β + φ)      F_p pawl force, r_t tooth radius, β flank from the travel direction, φ = atan μ
hold    T_click ≥ SF · M_g
raise   hand torque ≥ T_click + M_g;   lower: ≥ T_click − M_g
steps   n = 2π · r_t / pitch;  pitch = 2 · h_t / tan β  (h_t tooth depth);  resolution 360° / n
pawl    F_p = E b t³ h_t / (4 L³),   ε = 1.5 t h_t / L²     cantilever deflected by the tooth depth
```

- **Flanks.** Use 90° symmetric teeth (`β` = 45° each side) for two-way
  posing. A steeper flank on the side gravity loads holds a heavy limb while
  raising stays light. Keep `β + φ` well below 90° on both flanks, or the
  joint locks. A one-way locking ratchet is for a part that must not come
  back without a release ([[latches-detents-and-ratchets#ratchet-and-pawl-geometry]]).
- **Print the disc lying flat** (axis along Z), so the nozzle draws the tooth
  profile in X-Y. Teeth on an axial face come out as stairs of layers: give
  them at least three layers of height, or avoid them.
- **Tooth depth at least one line width** (0.4–0.45 mm). The nozzle rounds
  tips and roots, and a shallower tooth prints as a wave. Worked: `r_t` = 5, `h_t` = 0.5,
  90° teeth → pitch 1.0, 31 teeth, 11.6° steps.
- **The pawl's strain is its life.** A PLA flexure that clicks thousands of
  times must stay near 0.15 % strain
  ([[flexure-materials-and-snap-strain#snap-fit-strain]]), so
  `L ≥ sqrt(1.5 t h_t / ε)`. With `t` = 0.8 and `h_t` = 0.5 that is 20 mm at
  0.15 %, or 7.7 mm at 1 % for occasional use in PETG. Moulded toys often use a
  metal spring instead. Toy ratchets still wear: metal springs
  fatigue and corrode, and plastic teeth erode.
- **One axis per ratchet.** Add a swivel for a second freedom.

## Friction joints that hold in printed PLA and PETG

- **Friction comes from a designed deflection, not from a fit.** Make the
  preload interference several times the print error, delivered by a soft
  spring ([[ball-and-socket-joints#holding-torque-friction-on-the-ball]]).
  One kit figure's designer swapped tight-tolerance swivels for a compliant
  member that holds tension, to cure joints that came out too loose or too
  tight.
- **Pegs.** A solid peg in `cadfits.slot_for(D, "snug")` locates it but
  barely grips: that is 0.10 mm of clearance per side. For grip, use a split
  peg whose halves spring against the hole (each half a cantilever,
  [[snap-fit-design#cantilever]]), a mushroom head that snaps through and
  retains, or a TPU sleeve. Too much tension shears pegs. Fillet the root and
  print the peg lying down.
- **Discs beat balls on torque per newton.** Face friction is
  `T = μ · F_ax · r_m` per face. A disc as large as the sculpt hides (the
  disc hip on a friction plate) holds more than a small ball pressed equally
  hard. A screw through the stack sets `F_ax` and can be retightened.
- **Material.** Frame joints in PETG, ABS or ASA. One kit designer rules PLA
  out because it is stiff (hard to snap together), brittle (breaks doing it)
  and creeps (joints loosen) ([[creep-and-stress-relaxation#design-rules]]).
  PLA is fine for armour and shells.
- **Orientation.** Lay hinge pins and pegs in the X-Y plane, so bending runs
  along the layers and does not delaminate them
  ([[layer-anisotropy#orient-so-layers-do-not-carry-the-tension]]).
- **First layer.** Every joint face on the bed needs elephant's-foot
  compensation (0.15 mm in one kit's profile) or a bottom chamfer.
- **Tightening after printing is a repair, not a design.** A clear coat or CA
  builds a peg up by fractions of a millimetre, and solvent cement swells
  styrene 0.05–0.2 mm. Design the adjustment in: a screw, a sleeve, a
  replaceable liner.

## How printed figures are built

| approach | joints | friction from | notes |
|---|---|---|---|
| **print-in-place, flexi** | crossed loops or pin-in-C ([[flexi-chain-joints]]) | none: free by design | flops and holds no pose |
| **print-in-place, posable** | balls printed in their sockets ([[print-in-place-mechanisms#captive-shapes]]) | bands proud of the ball, printed lodged in socket grooves, that drag once moved | Calì: a 0.3 mm gap worked and 0.2 mm fused (SLS, PolyJet); FDM needs a coupon |
| **kit (snap-assembled)** | balls snapped into split casings, compliant swivels, pinned hinges | finger and flexure preload | frames in PETG/ABS/ASA; any filament for armour; metal pins or screws in high-wear joints |
| **strung (BJD style)** | ball and cup on every part, elastic cord through all of them | cord tension presses every joint at once | arm loop through the chest; leg loop through the torso, hooked at the neck; too tight kicks back, too slack flops |

**Route a cord through each joint's turning centre.** A cord that passes
off-centre gets longer when the joint bends. Its tension then makes a
restoring moment, and the limb kicks back. A cord through the centre keeps
its length in every pose and only presses the faces together. Cord paths are
designed in [[cable-and-tendon-drives#tendon-driven-joints-and-fingers]].

## Failure classes

| symptom | cause | rule |
|---|---|---|
| limb droops in a pose | `T_hold` under the outboard moment; the accessory left out | sum the accessory; larger radius, a disc, or a ratchet |
| scaled-up figure sags where the small one held | gravity `s⁴` against friction `s³` | re-size every joint at the new scale; ratchets for stance joints |
| figure topples | centre of mass outside the feet; the ankle cannot tilt | rocker ankle ([[stability-and-tipping]]) |
| peg shears or neck snaps posing a stiff joint | slip torque over the break torque | slip budget; peg lying flat; root fillet |
| double hinge folds in a random order | two equal hinges | give one pin more friction so it moves second |
| loose after a week on the shelf | creep or relaxation in PLA | PETG/ABS/ASA; a retightenable preload |
| ratchet skips or stops clicking | pawl fatigue, eroded teeth | pawl strain limit; teeth in the harder part |
| strung limb kicks back | cord off the joint centre, or over-tensioned | route through the centre; tension |

## Checks

```python
import math
G = 9.81                                          # m in kg, x in mm -> N·mm
m_g = G * sum(m * x for m, x in OUTBOARD[joint])
assert T_HOLD[joint] >= SF * m_g, f"{joint} droops: holds {T_HOLD[joint]:.1f}, needs {SF * m_g:.1f} N·mm"
assert T_SLIP[joint] * SF_BREAK <= T_BREAK[joint], f"{joint} breaks before it slips"
assert RANGE_DEG[joint] >= TARGET_DEG[joint], f"{joint} range short of its posing target"
t_click = F_PAWL * R_TEETH * math.tan(math.radians(FLANK_DEG) + math.atan(MU))
assert t_click >= SF * m_g or not RATCHET[joint], f"{joint} click joint will not hold the limb"
assert math.degrees(math.atan(MU)) + FLANK_DEG < 80, "flank too steep: the click joint locks"
assert 1.5 * PAWL_T * TOOTH_H / PAWL_L**2 <= EPS_REPEATED[MATERIAL], "pawl strain too high for repeated clicks"
assert TOOTH_H >= LINE_W, "tooth shallower than one extrusion line"
assert GRIP_DELTA >= 3 * PRINT_ERR, "friction joint interference within print error"
```
