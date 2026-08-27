# Orbit Gobbler CAD project

Tier 3 STEP-first build123d project for the all-printed C-Mouth Lunar Cam.

`orbit_gobbler.step.py` is the combined inspection assembly and is not a print target. Each `part_*.step.py` entry is one printable part in its bed orientation. Repeated braces, frame keys, the shared small snap clip, and the shared small washer are printed twice from the same entry. The two small-clip occurrences retain the central axle and crank grip; their grooves and the clip's geometry are exactly identical. Both adjacent washers serve 8 mm shafts with the Invent-specified 8.4 mm bore, 16 mm OD, and 2 mm thickness. One verified print target therefore serves each repeated pair without omitting any physical piece.

The project vendors the exact `cadfits.py` utility used to derive every mating clearance. Product-local audit hooks import only product-local modules, so the same fit and specification checks run after the CAD directory is copied into an isolated verifier with no run-level `.agents` parent.

The combined STEP intentionally omits per-occurrence presentation colors. Open CASCADE may reorder equivalent color-style records across fresh processes, changing exact STEP bytes while leaving geometry unchanged; unstyled labeled occurrences keep the host-reverified assembly deterministic. Color is not required for the product's operation or comprehension.

Assembly sequence: seat the rear frame into the base, insert the two frame keys, slide the braces into their stopped seats, insert the central axle, slide the lunar slider into the front carrier channel, press the follower axle's snap collar through the roller and D-shaped slider opening, quarter-turn the moon onto the unequal round lugs, seat the carrier and eye guard, then add the front washer and horseshoe snap clip to the central-axle groove. Insert the pinion's D sleeve rearward through the frame bore, seat the rear crank, then add its washer and snap clip. Install the forward-projecting grip, washer, and snap clip, then seat the single fixed C-mouth bezel. Turn slowly through two crank turns after assembly.

The motion manifest checks declared rigid-body clear paths and the follower axle's blocked capture direction. Snap-collar and snap-clip compliance, quarter-turn lug compliance, friction retention, insertion force, and real repeated-cycle behavior remain physically unverified.

Build and gate:

```text
--bed 200x200x220
XDG_CACHE_HOME=<workspace>/.cache CADGEN_WARM=1 python <cad-skill>/scripts/verify_project <this-dir> --fresh --exports --strict-fit --motion-manifest measure/motion.json --bed 200x200x220 --nozzle 0.4
```

The root `assembled.stl` is an assembly-preview mesh with multiple shells; individual `part_*.stl` files are the slicer targets.
