---
title: Automaton craft practice
tags: [automaton, cam, follower, crank, pulley, craft, kinetic-sculpture, toy]
aliases: [automata making, snail cam, drop cam, lobe cam, cam follower guide, kinetic toy, cabaret mechanical theatre, rob ives]
sources:
  - http://dennissvoronos.com/assets/docs/automata1.188190813.pdf
  - https://www.robives.com/mechanism/cam/
  - https://www.robives.com/blog/designing-cams-and-followers/
  - https://makezine.com/article/maker-news/designing-automata-kit-ca/
related: [automata-patterns, cams-intermittent, linkages, energy-drive, toy-safety-constraints, cable-and-tendon-drives]
updated: 2026-09-23
---

# Automaton craft practice

Makers of automata (Robert Addams, *How to Design and Make Automata*; Rob
Ives's paper mechanisms; Cabaret Mechanical Theatre's *Cabaret Mechanical
Movement*) have a practical vocabulary of cams, followers and drives that
complements the engineering formulas in [[cams-intermittent]] and the layouts
in [[automata-patterns]]. This page is that vocabulary, with what each choice
does to the motion.

## Cam shapes and the motion they give

| cam | motion of the follower | watch out |
|---|---|---|
| **round, off-centre (eccentric)** or **oval** | smooth, regular up and down, sine-like | an oval gives two rises per turn |
| **lobe** (a raised part on a round base) | lift by the lobe's height above the base circle, then a pause — the **dwell** — while the follower rides the round part | a dwell can also be shaped on top of the lobe |
| **multi-lobe** | several short rises per turn; more lobes, faster motion | |
| **snail (drop)** | steady rise, then a sudden drop | **works in one direction only**: turned backwards, the follower jams against the step |
| **double snail** | the snail motion twice per turn, so twice as fast | same one-way rule |
| **offset cam** (contacting a drive plate to one side of the shaft) | up-and-down plus circular motion; two opposed offset cams give side-to-side | if the contact is directly under the shaft it only lifts |
| **skew cam** (a plate set at an angle on the shaft) | rocks a forked lever side to side, which twists a vertical rod | |

The lift is the highest point of the profile measured from the shaft centre,
minus the base radius. Design the cam from the motion you want: how many
movements per turn, how long each dwell.

Because a snail cam only runs one way, a snail-cam automaton needs a
ratchet on its crank or a clear direction arrow
([[cams-intermittent#ratchet-and-pawl]]).

## Followers and guides

- The follower is a rigid rod with a smooth end, constrained by a guide so
  it can only move along its axis. A badly designed follower and guide jam.
- **Make the guide block fairly thick and put it close to the cam**, so the
  rod cannot wobble sideways. This is the craft form of the guide-length rule
  in [[cams-intermittent#keeping-the-follower-on-the-cam]].
- A turning cam pushes the follower sideways. Rob Ives's cure is a separate
  follower that drags over the cam, joined to the push rod, so the rod itself
  only sees vertical motion.
- Moving the follower below the cam allows a longer push rod that twists less.
  Pivoting a lever follower at its middle rather than its end, and using a
  bell crank or a dog-leg, brings the follower closer to the cam to save
  space.

## Cranks versus cams

A crank drives its output both ways — up and back down — so it does not rely
on gravity to return the follower, which is a common failure with cams. A
crank and slider can also give side-to-side motion, whose amplitude is set by
the crank throw and the guide position. Choose a cam for timing (dwells,
drops); choose a crank for positive motion both ways ([[linkages]]).

## Drives: gears and pulleys

- Gears reverse direction at every mesh, and stepping down gives more force
  at lower speed. Stepping up makes the handle hard to turn, so check the
  ratio against the hand ([[energy-drive#ratio-budget]]).
- Belt-and-pulley ("friction") drives are simple and work over distance, but
  **slip**, which upsets the timing of a multi-motion automaton. Use gears or
  a toothed belt where timing matters. Grooved pulley rims keep the belt on.

String loops, pull cords and capstan friction: [[cable-and-tendon-drives]].

## Free movement

Wherever two parts move against each other there must be clearance, or the
mechanism jams. The stresses are low, but the engineering still has to be
sound. Harder materials are less forgiving than soft ones: a card gear may
run where a wooden one with the same profile sticks. For printed parts this
is the running-fit rule of [[joints#two-fit-classes-per-project]].

## The design check

Addams's checklist for an automaton idea: visually exciting? funny? intriguing?
will it hold attention? too complex? humour too obscure? enjoyable to make?
The engineering version, in order: make the mechanism move before adding the
figure; confirm every cam's direction; confirm nothing relies on gravity that
might tip; then fit the figure ([[automata-patterns#reading-a-mechanism-off-a-picture]]).
