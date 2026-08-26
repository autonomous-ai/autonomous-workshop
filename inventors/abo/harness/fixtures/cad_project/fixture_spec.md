# Board-game gate fixture CAD brief

- Model: two-part sliding gate fixture.
- Task type: regression assembly with two separately printable parts.
- Units: millimetres.
- Coordinate convention: centered XY footprint, print datum at Z=0, +Z up.
- Receiver: 60 × 30 × 10 mm overall, with a 4 mm floor, two 4 mm side rails,
  a 22 mm channel, and one closed end stop.
- Slider: 20 × 20 × 4 mm, assembled on the receiver floor with 1 mm lateral
  clearance per side.
- Positioning: slider begins centered in the channel at Z=4.
- Motion: withdrawal toward -X must remain clear; travel toward +X must be
  blocked by the end stop.
- Parts catalog: no purchased or standard mechanical components are present.
- Paths: combined `fixture.step.py`; printable `part_receiver.step.py` and
  `part_slider.step.py`; STEP, STL, and GLB outputs remain derived artifacts.
- Validation targets: two labeled assembly children, positive closed solids,
  no rest-pose interference, P2S bed fit, 1 mm side clearance, allowed and
  blocked motion conditions.
- Assumptions: all dimensions exist only to exercise the pipeline and are not
  a product design.
