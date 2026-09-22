# Failure catalogue

Mechanism faults found in the upstream `autonomous-product-to-cad`
repository, what they looked like, and the rule that prevents each. Every one
of them passed `validate`, `interfere` (at the pose it was built in),
`check_fit` and the mesh gates.

| # | fault | where | symptom | rule |
|---|---|---|---|---|
| 1 | legs built at one pose for every phase | trotter-src | feet overlapped up to 750 mm³ over a turn; gait was a pace, not a trot | build each moving part in its neutral pose and place it from its own phase by the kinematics (`linkages.md`) |
| 2 | captured shaft in a closed bore | trotter-src winder neck | hook on one side, pinion on the other, both wider than the bore: cannot be installed | check the insertion path of every captured part before adding features on both sides; open fork + keeper (`joints.md`) |
| 3 | bore through the pinion root | trotter-src m1 z8 pinion, 6.2 socket | teeth on a 0.4 mm skin | assert body under the teeth (`gears.md`) |
| 4 | one rod per axle | trotter-src | each axle passed dead centre twice a turn and could reverse | quarter two rods 90° apart, or drive the crank directly (`linkages.md`) |
| 5 | double-D keys | trotter-src | phased parts fit 180° out | single flat for any phased part (`joints.md`) |
| 6 | parts joined on bare glued faces | trotter-src legs | no location, 56 parts | key or peg every joint that is not meant to move |
| 7 | no motion manifest | trotter-src | nothing had tested the cycle | generate one from the kinematics (`verification.md`) |
| 8 | cycle swept without the frame | 4 of 6 machines (see motion-manifests) | a lever ground 0.4 mm into a post through most of its swing, gate green | always name `obstacle_parts` |
| 9 | coarse sampling of a mesh | general | a tooth passes clean through a tooth between samples | fine tooth-pitch sweep with `maxStepMm` (`verification.md`) |
| 10 | group compound as mover | trotter | boolean returned 0 mm³ on a real 123.6 mm³ overlap | movers are leaf parts |
| 11 | linkage posed by hand | manta_ray (before re-solve) | 8 link × staple clashes | solve the rest pose from the linkage, then repair by re-solving (`automata-patterns.md`) |
| 12 | rest pose at a travel end | general | `driven` pass reports a working follower as undriven | park mid-stroke |
| 13 | removable part used as a retainer without proof | camshaft fixture in `check_motion` self-check | shaft "held" by a gate that could itself fall out | `retention` chain to a fixed root |
| 14 | hand-authored standard gear | cat automaton | a catalog gear 2 % off was never searched | search `$step-parts` by form, not only by name |
| 15 | self-locking stage in a back-driven train | general | pull-back or hand-reversed toy jams | check worm lead angle (`gears.md`, `energy-drive.md`) |
| 16 | open U hook for a band | trotter-src | unprintable overhang with the head vertical | blade with a barbed notch (`energy-drive.md`) |

## Before calling a mechanism finished

- [ ] archetype named, rejected alternatives recorded
- [ ] every kinematic number in one parameter block, mates from `cadfits`
- [ ] feasibility asserts in the parameter module, passing
- [ ] geometry placed from the kinematics at a mid-stroke rest pose
- [ ] manifest generated: coupled cycle with `driven` outputs and named
      obstacles, fine sweep of the fastest contact, both directions per joint,
      assembly order, retention to a fixed root
- [ ] open items (forces, friction, compliance, gait) written down
