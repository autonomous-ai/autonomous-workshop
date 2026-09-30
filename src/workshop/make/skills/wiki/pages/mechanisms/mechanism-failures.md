---
title: Mechanism failure catalogue
tags: [failure, checklist, mechanism, review, defect]
aliases: [common mistakes, pitfalls, lessons learned, pre-flight checklist]
sources:
  - "experience: mechanism faults caught in this repository after validate, interfere, check_fit and the mesh gates had passed"
  - skills/cad/references/motion-manifests.md
related: [mechanism-verification, mechanism-design]
updated: 2026-09-23
---

# Mechanism failure catalogue

Mechanism faults that passed `validate`, `interfere` (at the pose they were
built in), `check_fit` and the mesh gates, what they looked like, and the rule
that prevents each. Read before calling a mechanism finished; add a row when
a new class of fault is found.

## Faults and the rules that prevent them

| # | fault | symptom | rule |
|---|---|---|---|
| 1 | legs built at one pose for every phase | feet overlap over a turn; the gait is a pace, not a trot | build each moving part in its neutral pose and place it from its own phase by the kinematics ([[linkages#walking-linkages]]) |
| 2 | captured shaft in a closed bore | features on both sides wider than the bore: cannot be installed | check the insertion path of every captured part before adding features on both sides; open fork + keeper ([[joints#rules-that-are-easy-to-break]]) |
| 3 | bore through the pinion root | teeth on a sub-millimetre skin | assert body under the teeth ([[gears#body-under-the-teeth]]) |
| 4 | one rod per axle | each axle passes dead centre twice a turn and can reverse | quarter two rods 90° apart, or drive the crank directly ([[linkages#dead-centres]]) |
| 5 | double-D keys | phased parts fit 180° out | single flat for any phased part ([[joints#keyed-joints]]) |
| 6 | parts joined on bare glued faces | no location; part count balloons | key or peg every joint that is not meant to move |
| 7 | no motion manifest | nothing has tested the cycle | generate one from the kinematics ([[mechanism-verification]]) |
| 8 | cycle swept without the frame | a lever grinds into a post through most of its swing, gate green | always name `obstacle_parts` |
| 9 | coarse sampling of a mesh | a tooth passes clean through a tooth between samples | fine tooth-pitch sweep with `maxStepMm` ([[mechanism-verification#5-sampling]]) |
| 10 | group compound as mover | boolean returns 0 mm³ on a real overlap | movers are leaf parts |
| 11 | linkage posed by hand | link × staple clashes | solve the rest pose from the linkage, then repair by re-solving ([[linkages#solving-closure-numerically]]) |
| 12 | rest pose at a travel end | `driven` pass reports a working follower as undriven | park mid-stroke |
| 13 | removable part used as a retainer without proof | a shaft "held" by a gate that could itself fall out | `retention` chain to a fixed root |
| 14 | hand-authored standard gear | a catalog gear that fitted was never searched | search `$step-parts` by form, not only by name |
| 15 | self-locking stage in a back-driven train | pull-back or hand-reversed toy jams | check worm lead angle ([[gears#worm-and-crossed-helical-pairs]]) |
| 16 | open U hook for a band | unprintable overhang with the hook vertical | blade with a barbed notch ([[energy-drive#sources]]) |
| 17 | shaft axially located at both supports | binds or preloads once printed | fixed at one support, floating at the other ([[shafts-and-bearings#axial-location-fixed-and-floating]]) |
| 18 | long printed span under a gear | mesh separates under load; backlash vanishes or doubles | deflection assert, or a metal rod ([[shafts-and-bearings#stiffness-deflection-decides-before-strength-does]]) |

## Before calling a mechanism finished

- [ ] archetype named, rejected alternatives recorded
- [ ] every shaft: supports, axial stop, torque path named ([[shafts-and-bearings]])
- [ ] every kinematic number in one parameter block, mates from `cadfits`
- [ ] feasibility asserts in the parameter module, passing
- [ ] geometry placed from the kinematics at a mid-stroke rest pose
- [ ] manifest generated: coupled cycle with `driven` outputs and named
      obstacles, fine sweep of the fastest contact, both directions per joint,
      assembly order, retention to a fixed root
- [ ] open items (forces, friction, compliance, gait) written down
