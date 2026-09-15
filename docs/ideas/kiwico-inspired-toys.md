# Ten KiwiCo-inspired toys we can develop with Make

Research date: 2026-09-10. Repository baseline: `61da5eaf`.

Status: shortlist preserved for review. Cratercade is the first CLI prototype,
started on 2026-09-10; see [the run notes](cratercade-run-notes.md).
Names below are working names. These are original adaptation proposals, not
KiwiCo products or claims of affiliation.

## The brief and the recommendation

Create an exciting toy inspired by KiwiCo's popular build-and-play
kits. The structure and mechanisms should be primarily 3D printed. No
electronics, motors, batteries, sensors, or apps. Ordinary extras such as
rubber bands, string, cardboard, paper, marbles, felt, and wooden dowels are
acceptable when they improve the toy.

My first choice is **Cratercade**, a rebuildable mechanical pinball arcade.
It has an immediately understandable invitation, skill-based replay, a visible
mechanical jackpot, and a strong fit with printed parts plus rubber bands.
**Dragon Marble Foundry** is the strongest kinetic showpiece; **Orbit Ink** is
the most attractive choice for relatively contained mechanical development.

The ranking weighs visual excitement, repeat play, how well printing serves
the design, and engineering uncertainty. It is my assessment, not KiwiCo's
sales ranking. All ten are plausible Make prototype projects; none has been
built or physically validated as part of this research.

## What the popularity evidence actually says

KiwiCo's [US Best Sellers](https://www.kiwico.com/us/store/cp/best-sellers)
currently includes Pinball Machine, Marble Roller Coaster, Chain Reaction
Workshop, Pendulum Art Machine, Flex & Fly Plane Launcher, and Chomping
Mechanical Dinosaur Costume. Pinball and Marble Roller Coaster carry
“Most loved” labels there.

[Now Trending](https://www.kiwico.com/now-trending) additionally features
Domino Machine, Programmable Music Box, and Spinning Sand Garden. The
[mechanical kits collection](https://www.kiwico.com/us/store/cp/mechanical-kits)
also marks Domino Machine “Most loved.” The Mechanical Lock Box appears in
[Eureka Classics](https://www.kiwico.com/us/store/dp/eureka-classics-five-pack-project-kits/3049),
which KiwiCo describes as a bundle of popular Eureka crates; I did not verify
an individual current bestseller badge for it.

These merchandising signals are useful inspiration, but do not establish
unit sales or a top-ten ordering. Supporting references such as Wooden
Automaton and Geometric Drawing Machine supply mechanism ideas without an
individual bestseller claim. Some product pages return sparse shells;
readable official regional and education pages are linked where useful.

## Quick comparison

Complexity describes prototype engineering effort, not a measured success rate.

| Rank | Working idea | The memorable moment | Simple extras | Complexity |
|---|---|---|---|---|
| 1 | Cratercade | A skill shot tips a lunar bucket and plants a flag | Marbles, rubber bands, felt feet | Medium–high |
| 2 | Dragon Marble Foundry | Crank marbles up a dragon's spine and watch them loop back down its tail | Marbles; optional dowel axle | Medium–high |
| 3 | Domino Dispatch | Push a little vehicle that leaves a standing domino trail | Rubber traction bands | Medium–high |
| 4 | Chain Reaction Harbor | One marble unloads a bucket, moves a bridge, and finishes a delivery | Marbles, string, card scenery | Medium–high |
| 5 | Orbit Ink | Changing a gear and pen position creates a new intricate drawing | Pen, paper, rubber feet | Medium |
| 6 | Clockwork Treasure Vault | A custom mechanical code opens a visibly geared treasure door | Paper clue cards; optional bands | Medium |
| 7 | Beat Foundry | Move pegs to compose a rhythm, then crank it into sound | Optional card drum skin, felt pads | Medium–high |
| 8 | Dragon Grip | A squeeze makes a creature pick up and sort treasure | String, rubber band, felt jaw pads | Lower–medium |
| 9 | Dune Loom | A hand crank weaves repeating patterns into a sand tray | Craft sand | Medium |
| 10 | Skyport Glider Lab | Tune the launcher and glider to land on a tiny flight deck | Rubber band, paper/card gliders | Medium–high |

## 1. Cratercade — rebuildable lunar pinball

**KiwiCo inspiration:** [Pinball Machine](https://www.kiwico.com/us/store/dp/pinball-project-kit/1648)
and its [Eureka design notes](https://www.kiwico.com/eureka/pinball).

**Play:** Launch a marble with a rubber-band plunger, operate two independent
thumb flippers, and aim through movable crater bumpers. A successful shot
reaches a raised sample bucket; its weight tips the bucket and raises a
landing flag. Rearrange the bumpers and target entrance to make different
missions. Reset the jackpot by hand and play again.

**What Make produces:** A sectional inclined playfield, rails, flippers,
pivots, plunger housing, interchangeable obstacle mounts, bucket-and-flag
linkage, legs, and assembly instructions. Print the structural play surface;
use paper only for optional mission cards. KiwiCo's design notes specifically
report rolling and warping problems with paper/wood playfields.

**Why this version earns its own identity:** Winning changes a real scene:
the sample is delivered and the flag rises. The mission layout is physically
rebuildable, rather than a space graphic pasted onto a fixed board.

**First proof:** One flipper, a short playfield, and the bucket target. Check
the full motion and band routes digitally; print-test ball travel across
seams, flipper control, required shot energy, and reliable jackpot reset.
Those functions are required before a complete arcade can count as successful.

## 2. Dragon Marble Foundry — a hand-cranked marble creature

**KiwiCo inspiration:** [Marble Roller Coaster](https://www.kiwico.com/au/store/dp/marble-roller-coaster/5885)
and [Wooden Automaton](https://education.kiwico.com/store/dp/wooden-automaton-project-kit/5431).
The coaster uses a powered lift; the automaton demonstrates a hand-cranked
marble stair-climber.

**Play:** Turn a side crank to walk marbles up exposed steps along a dragon's
spine. Each marble emerges through its open mouth, descends a curling tail
track, and returns to the pickup. Two exchangeable tail sections offer a
gentle route and a rolling slalom. The complete return loop keeps working
while the user keeps cranking; it is not self-powered.

**What Make produces:** Camshaft, guided stair followers, crank, retained
axles, pickup, return rails, segmented dragon body, and tail modules. Ordinary
marbles provide smoother, more consistent rolling than assumed-perfect
printed spheres.

**Why this version earns its own identity:** The dragon's anatomy performs
the transport. Open inspection areas make the climbing mechanism legible,
while the head and tail give the complete machine a strong silhouette.

**First proof:** Two adjacent lifting steps, their cam timing, and the
handoff to a short rail. Physical tests must establish feed reliability,
rolling resistance, and crank torque. Start with an open gravity path, not an
unproven high-speed inversion loop.

## 3. Domino Dispatch — a push-powered trail builder

**KiwiCo inspiration:** [Domino Machine](https://www.kiwico.com/us/store/dp/domino-machine-project-kit/3827),
featured in Now Trending. KiwiCo's version contains a motor and battery pack.

**Play:** Load a magazine of printed dominoes and push a compact trail-making
vehicle. A ground wheel drives a mechanical dispenser, placing one domino
per interval. Steer broad curves, join trails, then start the toppling chain.
Swap between two spacing settings to experiment with propagation.

**What Make produces:** An original vehicle body, wheels, cam or escapement,
removable magazine, loading guide, tile-placement shoe, and uniform dominoes.
Rubber bands around the wheels provide replaceable traction. The mechanism
is powered directly by pushing, with no wound motor substitute hidden inside.

**Why this version earns its own identity:** Its visible wheel-to-dispenser
link lets players control the layout directly. Design its form and dispensing
mechanism independently, rather than reproducing KiwiCo's robot casing.

**First proof:** A bench magazine that releases exactly one tile, then a
wheel-driven carriage that leaves it upright. CAD can check the timing and
escape paths; a real print must establish anti-jamming clearances, tile
stability, traction, and curve performance. This is among the riskier ten.

## 4. Chain Reaction Harbor — a rebuildable cargo adventure

**KiwiCo inspiration:** [Chain Reaction Workshop](https://www.kiwico.com/de/store/dp/chain-reaction-workshop/5674)
and the [Chain Reaction Bundle](https://www.kiwico.com/us/store/dp/lots-of-bots-robotics-engineering-bundle-pack/5710).

**Play:** Arrange three dock modules, load their stored gravitational energy
by hand, and release one marble. It tips a cargo bucket, releases a
counterweighted drawbridge, and lets the cargo reach a ship that raises its
arrival flag. Change module spacing and bridge timing to solve delivery
challenges. Reset openly by hand between runs.

**What Make produces:** Stable dock bases, rails, bucket pivot, low-force
latches, bridge, cord pulleys, a ship receiver, and common connector sockets.
Use string for tension transmission and card for optional scenery or ramp
extensions. Main structures, joints, and the core route stay printed.

**Why this version earns its own identity:** The chain completes a visible
job with a beginning and an ending. Modules can rearrange without turning
the first build into an unlimited catalog of mechanisms.

**First proof:** Each trigger must release the next module with an adequate
energy margin, followed by the complete three-module chain. Clearance
animation alone cannot prove force, timing, tipping, or reliable reset.

## 5. Orbit Ink — a mechanical pattern composer

**KiwiCo inspiration:** The popular [Pendulum Art Machine](https://www.kiwico.com/uk/store/dp/pendulum-art-machine/4668)
and the [Geometric Drawing Machine](https://www.kiwico.com/tinker/drawingmachine)
as a supporting mechanism reference.

**Play:** Fit a gear cartridge, choose an eccentric pen position, and turn a
crank to draw rosettes and looping curves. Swap one ratio or offset to change
the pattern, then layer a second color. Include a few repeatable pattern
recipes and blank cards for discoveries.

**What Make produces:** A compact paper bed, crank, interchangeable gears,
pen carrier, adjustment scales, and a restrained pen-pressure mechanism.
Only a normal pen, paper, and optional anti-slip feet are bought or crafted.
This proposal uses positive gear drive instead of a large suspended pendulum
frame; that is an intentional adaptation suited to compact printed machinery.

**Why this version earns its own identity:** Gear settings become a physical
composition language. The user can predict, reproduce, and combine patterns,
and keep the drawing afterward.

**First proof:** Calculate and plot the actual linkage's pen trajectory,
then print a single gear pair and carrier. Test backlash, pen drag, paper
flatness, and closure of a complete pattern. A plotted ideal path is only
the reference against which the physical drawing is checked.

## 6. Clockwork Treasure Vault — a reprogrammable puzzle box

**KiwiCo inspiration:** [Mechanical Lock Box](https://www.kiwico.com/us/store/dp/mechanical-lock-box-project-kit/3101)
and [its design notes](https://www.kiwico.com/eureka/lockbox).

**Play:** Set three oversized code rings so their gates align, release a
locking bar, and turn a wheel to retract the door bolts. Hide a clue or small
treasure, then rearrange the code inserts for the next person. A removable
inspection panel lets the owner see the logic and reset the puzzle.

**What Make produces:** Ring gates, locking bar, gears, bolts, door, box,
code inserts, and a deliberate owner-reset path. Paper supplies clue cards;
any return elastic is replaceable. The large mechanism favors generous
clearances over tiny lock pins.

**Why this version earns its own identity:** The owner authors the challenge.
Its visible mechanical logic supports both puzzle play and experimentation.
This is a toy vault, with no security claim for valuables.

**First proof:** A three-ring gate cartridge that blocks at wrong settings
and opens at the right setting, including near-aligned cases. Then check
bolt travel, retention, and an accessible reset. Printed wear and accidental
unlocking still need physical trials.

## 7. Beat Foundry — peg-programmed percussion

**KiwiCo inspiration:** [Programmable Music Box](https://www.kiwico.com/store/dp/programmable-music-box-project-kit/3136),
featured in Now Trending, and [its development notes](https://www.kiwico.com/eureka/musicbox).

**Play:** Put pegs into three tracks around a twelve-step drum and turn the
crank. The pegs lift and release hammers over different resonant surfaces.
Move pegs to change the beat; crank faster or slower; open and close a
resonator to explore timbre. The raised hammers make the rhythm visible too.

**What Make produces:** Peg drum, chunky removable pegs, axle, crank, hammer
arms, two printed resonant bodies, and an optional card-skin drum mount.
Felt can soften impacts. Printing owns the sequencer, structure, and much
of the sound-producing geometry.

**Why this version earns its own identity:** It is a tactile rhythm composer
with visible programming. The goal is distinct percussive voices, not an
unsupported promise of accurately tuned PLA melody bars.

**First proof:** A single peg and hammer must release cleanly, followed by
two physically distinguishable sound samples. Test crank effort, missed or
double strikes, sound quality, and wear. KiwiCo's own notes describe how
pluck strength and hammer material forced changes to its music box.

## 8. Dragon Grip — a creature puppet that collects treasure

**KiwiCo inspiration:** [Chomping Mechanical Dinosaur Costume](https://www.kiwico.com/us/store/dp/chomping-mechanical-dinosaur-costume-project-kit/2282)
and [Mechanical Claw](https://education.kiwico.com/us/dp/mechanical-claw-classroom-pack-activity-pack/4150).
The dinosaur costume appears in Best Sellers; the claw is a supporting
mechanism reference.

**Play:** Squeeze a handle to close a dragon's broad jaws around printed
treasure shapes. Release to open them. Rescue eggs from a crater, sort gems
into matching nests, or use the creature as a talking puppet. Interchangeable
jaw pads change which objects are easiest to collect.

**What Make produces:** Sculpted head, jaw, retained hinge, handle lever,
cord guides, treasure shapes, and nest targets. String transmits the pull,
a low-force rubber band returns the jaw, and felt pads improve grip.
Optional card wings are decorative; it is a handheld puppet, not a heavy
printed costume worn on the head.

**Why this version earns its own identity:** Expression and dexterity use the
same mechanism. The creature does something useful in a repeatable game.

**First proof:** Handle travel, jaw opening, tendon routing, and positive
travel stops. Physical tests determine comfortable squeeze force, pad
friction, and dependable release. Use rounded teeth and keep fingers clear
of the jaw's closing space.

## 9. Dune Loom — a hand-cranked sand-pattern machine

**KiwiCo inspiration:** [Spinning Sand Garden](https://www.kiwico.com/eureka/sandgarden),
featured in Now Trending.

**Play:** Turn a crank to rotate a shallow sand tray while a linked rake
sweeps across it. Choose a gear ratio and rake offset to weave different
rosettes and spirals. Smooth the sand with a supplied blade, change the
settings, and begin a new pattern.

**What Make produces:** Tray, base, crank, gears, guided rake arm, adjustable
mounts, smoothing blade, and a cover. Ordinary craft sand is the medium.
Use direct mechanical drive and a visible rake; no magnetic ball-control
system, motor, or electronics is required. Keep sand out of the drive.

**Why this version earns its own identity:** The user feels and sees the
relationship between the two motions, and can design repeatable patterns.
Its mechanism is part of the play, rather than an inaccessible automatic base.

**First proof:** A small tray, one ratio, and a controlled rake depth.
Check the trajectory and clearances digitally, then test actual drag, grain
behavior, pattern clarity, and sand ingress. KiwiCo's development notes
also document gear jamming and containment problems.

## 10. Skyport Glider Lab — tune, launch, and land

**KiwiCo inspiration:** [Flex & Fly Plane Launcher](https://www.kiwico.com/li/store/dp/flex-fly-plane-launcher/5907),
included in the US Best Sellers collection.

**Play:** Fold a lightweight glider, adjust launch angle and one of a few
bounded pullback settings, then try to land on a target flight deck. Change
wing tabs and balance, record a flight, and tune the next attempt. Add
cardboard gates for optional accuracy challenges.

**What Make produces:** A substantial sectional runway, guided launch
carriage, rubber-band housing, angle stand, travel stop, wing-setting gauges,
and landing-target frame. Paper/card makes the aircraft; rubber provides
launch energy. The reusable launcher and adjustment system are the main
product. Do not turn the glider into a heavy printed projectile.

**Why this version earns its own identity:** Repeatable mechanical settings
turn launching into an experiment and a landing game, with a clear reason
to adjust and retry.

**First proof:** Controlled release with no carriage escape or band
entanglement, followed by low-energy flights with the actual craft glider.
CAD cannot establish aerodynamics, launch range, or landing accuracy.
This earns the last position because flight tuning adds uncertainty beyond
the printed mechanism.

## Make boundaries applied to all ten

Make supports parametric solids, assemblies, organic lofts, gears, source
audits, interference checks, and sampled motion/retention evidence. Current
delivery is STEP plus CAD source and supporting artifacts. Its print gates
measure thickness, overhang, and tessellated-solid properties from source;
passing them does not establish physical operation.

Design parts to fit a conventional desktop printer, splitting large
playfields and frames into mechanically aligned sections. Favor rigid bodies,
retained axles, replaceable bands, and accessible adjustments. Use purchased
marbles for rolling experiments and paper/card where flexibility or low mass
is essential. Avoid depending on microscopic clearances, fragile printed
springs, all-printed musical tuning, printed hydraulic seals, or arbitrary
robot locomotion. A motorized reference does not authorize an electric version.

The early proofs above are development steps, not substitutes for the complete
promised toy. In particular, a rendered marble path is not a working marble
run; moving jaws are not a tested gripper; an animation is not force evidence.
The desired final handoff includes complete source/STEP, assembly and reset
instructions, an explicit extras list, evidence, and honest open physical tests.

Grounding: [Make CAD skill](../../src/workshop/make/skills/cad/SKILL.md),
[motion limits](../../src/workshop/make/skills/cad/references/motion-manifests.md),
[product verification](../PRODUCT_VERIFICATION.md), and the archived
[Cybercab](../../toys/ferro-line-cybercab-elastic-drive/make/source/cad/README.md)
and [Rainspell Dial](../../toys/sonora-reed-rainspell-dial-three-field-sound-garden/README.md).
The stale “2–12 boxes or cylinders” sentence in Make's README is not the
current native geometry boundary. Daydream's deliberately simpler generation
policy is also not a universal cap on a directly supplied Wish.

## When we choose one: actual-user CLI run and observation

User direction recorded: run the selected toy through the normal CLI as an
actual user would. Observe Workshop and Make, diagnose real issues, and improve
the implementation where evidence supports a bug or workflow improvement.
The shortlist itself launched nothing. The subsequent continuation of the
original build request started Cratercade; the other nine remain ideas.

The initial requested configuration was **Spark / Codex / Astra / ultra /
100,000,000 total product tokens**. The user subsequently changed the existing
Cratercade run to **medium effort and a 1,000,000,000 total token cap** through
normal CLI resumes. Spark, Astra, the exact native session and prior usage
remain preserved. This allowance is for Cratercade, not ten builds; see the
[run notes](cratercade-run-notes.md) for the current checkpoint.

The original launch used this CLI form:

```sh
.venv/bin/python -m cli wish "<selected complete toy brief>" \
  --workflow spark --agent codex --model astra --effort ultra \
  --max-tokens 100000000 --strict
```

Before running, select the repository's supported local Codex executable through
`WORKSHOP_CODEX_BIN` when necessary and check the actual CLI environment. On this
workstation, `docs/RUNNING_AUTONOMOUSLY.md` records an isolated supported binary.
At the first launch, the convenience `run_wish_codex.py` wrapper rejected
`ultra` even though the underlying CLI accepted it. The run used the main CLI
with ultra preserved. Local commit `9aab2a39` subsequently fixed the wrapper
through shared runtime validation and regression tests; see the run notes.

Observe the saved run ID, frozen model/effort/budget, stage progress, exact
Make outputs, visual reviews, failures, token accounting, and publication
handoff. Resume the same run/session when appropriate. Do not replace the
native product workflow with CAD authored in this repository-builder chat.
Recheck liveness before treating a quiet run as stopped.

For a reproducible bug, preserve the failing evidence, make a focused source
fix, add the relevant contract/failure-path regression test, and rerun the
necessary checks. Read the applicable runtime ADRs before such changes.
Respect frozen run tools and session identity; never lower a gate, rewrite
sealed evidence, or alter the toy promise just to get a pass. Log proposed
quality improvements separately from established defects.

Spark currently publishes Make's existing files without a second host CAD
rebuild or a new manual turn. That policy must remain explicit while observing
the run. Digital publication is the handoff to Operations, not proof of a
physical print or hands-on playtest.
