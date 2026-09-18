# Reference images supplied with the Wish

- `ref-01-ref-1-roof-dome.png` — the dome, drum and centred telescope. Already
  built correctly except for the yoke's x position, which revision C repairs.
  Nothing in it was redesigned.
- `ref-02-ref-2-sun-face.png` — the Sun counter. **Frozen.** Shown so the counter
  that must not be touched can be confirmed. `part_sun_counter.step` hashes
  `262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b`, asserted
  on every run by `measure/check_fit.py`.
- `ref-03-ref-3-moon-face.png` — the Moon counter. **Frozen**, same.
- `ref-04-ref-4-yoke-offset.png` — **THIS IS THE DEFECT, NOT THE TARGET.** It is
  a render of the previous, wrong geometry, looking straight down into the slit:
  one arm hugging one slit wall outside the tube, the tube beside it, and empty
  slit on the other side. The corrected view of the same thing is
  `snap/roof/slit-plan-close_el90.png`, where the two arms straddle the tube
  symmetrically with 6.000 mm clear to each wall. Do not use this file as a
  likeness reference for anything.
