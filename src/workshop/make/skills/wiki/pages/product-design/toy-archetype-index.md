---
title: Toy archetype index
tags: [toy, archetype, index, play, chooser]
aliases: [toy chooser, kind of toy, toy type, toy category, which toy pages, printable toy, desk toy, fidget toy kinds]
sources:
  - https://www.cpsc.gov/s3fs-public/Small-Parts-16-C-F-R-Part-1501-English.pdf (age decides which rules apply)
  - "experience: toy requests that reached CAD with only the archetype named, and lost a review round to a play, feel or safety question the archetype's page already answered"
related: [mechanism-design, product-aesthetics, toy-safety-constraints, character-proportions-and-appeal, play-value-and-tactile-feel, key-rings-and-charm-hardware, spinning-toys-and-flywheels, marble-runs-and-ball-tracks, construction-toy-interfaces, balance-toys-and-tensegrity, launchers-and-projectile-toys, mechanical-puzzles]
updated: 2026-10-10
---

# Toy archetype index

Start here when a request names a toy. "A dragon fidget", "a keychain for
the team", "a marble run for the desk" each name a category, and each category
has a play pattern, a construction family, a handful of numbers that decide
whether it works, and safety rules that depend on the child. This page routes
the category to the pages holding those numbers. The mechanism side has its
own chooser ([[mechanism-design#archetype-chooser]]); the look has
[[product-aesthetics]].

## Questions every toy answers before a concept

Write these into the spec's requirements before choosing a form. Each one has
changed a design after CAD when it was left open.

1. **Who plays, and how old.** The age decides the small-parts, magnet, cord,
   edge and battery rules ([[toy-safety-constraints#who-the-toy-is-for-decides-everything]]).
   A display piece for adults is a stated age too.
2. **What the hands do.** Pick one primary play pattern — hold, click, spin,
   slide, pose, build, solve, launch, watch it move, collect
   ([[play-value-and-tactile-feel]]). A toy that does three things weakly
   loses to one that does one well.
3. **What it does a second time.** The reveal, the second state, the
   challenge or the open-ended play that brings the hand back.
4. **How it is carried or kept.** Pocket, key ring, bag charm, shelf, desk,
   bath. That sets the size band and the attachment
   ([[key-rings-and-charm-hardware]]).
5. **What is bought.** Bearings, steel balls, magnets, springs, rings, cells,
   tags: each is a catalog search and a seat, never a printed stand-in.
6. **What breaks first** when it is dropped from a table, yanked by a ring or
   sat on: the thin limb, the loop across layers, the cocked flexure.

## Chooser: toy kind → pages

| Toy kind | Play pattern | Construction family | Decisive numbers live in |
|---|---|---|---|
| keychain, charm, NFC token | carry, show, tap | flat plate or two glued halves, colour bodies | [[key-rings-and-charm-hardware]], [[nfc-tags-in-prints]], [[pixel-art-plans]], [[fdm-joining-split-prints]] |
| collectible figure, mascot | collect, display | organic body, often split for print | [[character-proportions-and-appeal]], [[product-aesthetics#making-a-figure-splendid]], [[carved-figures-on-split-prints]], [[stability-and-tipping]] |
| flexi animal, articulated print-in-place | wiggle, fidget | one body cut into chained segments | [[flexi-chain-joints]], [[print-in-place-mechanisms]] |
| posable figure | pose, play pretend | segments on friction or ratchet joints | [[posable-figure-joints]], [[ball-and-socket-joints]] |
| fidget (click, slide, flip) | repeat a satisfying motion | detents, flexures, sliders | [[play-value-and-tactile-feel]], [[latches-detents-and-ratchets]], [[flexure-materials-and-snap-strain]], [[printed-fatigue]] |
| spinner, top, yo-yo, gyroscope | spin, compare spin time | revolved body, bought bearing, rim mass | [[spinning-toys-and-flywheels]], [[mass-properties-and-measurement]] |
| automaton, crank toy | turn a handle, watch | shaft box with cams or cranks | [[automata-patterns]], [[automaton-craft-practice]], [[cams-intermittent]], [[linkages]] |
| walker, vehicle, wind-up | let it go, chase it | chassis, linkage or wheels, stored energy or motor | [[wheeled-vehicles]], [[energy-drive]], [[linkages]], [[small-dc-motors]] |
| marble run, ball track | drop, watch, rebuild | channels, helices, a lift | [[marble-runs-and-ball-tracks]] |
| launcher, catapult, popper | aim, fire, retrieve | arm or piston, trigger, stored energy | [[launchers-and-projectile-toys]] |
| balance toy, tensegrity, rocker | nudge, wonder | centre of mass placed against a pivot or curve | [[balance-toys-and-tensegrity]], [[counterweights-and-gravity-balance]] |
| puzzle (box, maze, burr, sliding, twisty) | solve | sliding or interlocking pieces with set clearances | [[mechanical-puzzles]], [[interlocking-joinery-for-prints]] |
| construction-set accessory | build with an existing system | stud, tube, pin, axle or track interface | [[construction-toy-interfaces]], [[push-pins-and-clip-fasteners]] |
| two-state or reveal toy | turn, flip, discover | volvelle, indexer, hidden face | [[volvelle-two-state-display]], [[push-to-turn-indexer]] |
| extending grabber, lazy tongs | reach, snap | scissor or telescoping linkage | [[scissor-and-pantograph-linkages]], [[telescoping-tubes-and-locks]] |
| light-up or sound toy | press, see, hear | enclosure, cells, switch, load | [[lighting-design]], [[sound-modules]], [[toy-battery-compartments]] |
| bath, teether, food-adjacent | mouth, water | sealed or single-piece body | [[food-and-toy-safety]], [[toy-safety-constraints]] |

A request that spans two rows (a light-up figure, a fidget keychain) reads
both rows; the play pattern of the row the user named first is the primary
one.

## Constraints that cross every row

- **Small parts and bought parts.** Every steel ball, magnet, ring and cell
  is a small part unless captured; a part a child can free is judged as
  free ([[toy-safety-constraints#small-parts-the-choke-test]]).
- **Thin features break first.** A limb, tail, horn or ring loop sized for
  the look and not for the drop is the commonest field failure; size it from
  [[fdm-minimum-feature-sizes]] and [[layer-anisotropy]], not from the
  render.
- **Stored energy decays in plastic.** A flexure or band left loaded creeps
  ([[creep-and-stress-relaxation]]); a toy that stores energy releases it
  when put away.
- **A toy that moves gets motion checks**, with both the allowed and the
  blocked direction where it claims to hold or retain
  ([[mechanism-verification]]).
- **Beauty is still a requirement.** The play pattern does not excuse a
  plain form; the direction and review rounds of [[product-aesthetics]] apply
  to every row.

## Toy-specific review items

Add these to the design review rounds, after the aesthetic checklist:

1. The primary play pattern can be named from the render alone.
2. The part the hand touches most is the best-finished surface, off
   supports and seams.
3. The weakest feature has a stated drop or pull case and a section sized
   for it.
4. Every bought part is captured, or the age rules allow it free.
5. The attachment (ring, clip, base, track) is drawn with the real bought
   part beside it, not a placeholder.
