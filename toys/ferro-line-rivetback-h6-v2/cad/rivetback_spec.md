# RIVETBACK H-6 CAD brief

## V2 hard-surface refinement

- Preserve the published V1 assembly envelope, six keyed leg stations, snap-fit
  clearances, part count, and documented print orientations.
- Add printable visual hierarchy through layered carapace panels, open-top
  trenches, large polygonal rivets, faceted joint housings, raised armor crests,
  split-toe feet, stepped energy conduits, a banded cannon, toothed muzzle, and
  recessed sensor visor. `[assumed]`
- Cosmetic additions overlap their host solids by 0.2 mm or more. `[assumed]`
- New minimum intentional detail is 1.2 mm. `[assumed]`
- Split-toe tip walls are 1.4 mm per side for a 0.4 mm nozzle. `[assumed]`
- No loose greebles are introduced.

- Model: original multi-part static mecha hexapod display kit.
- Task type: new parametric assembly with 16 unique printable component generators and 50 placed occurrences; the joint-lock-pin generator is an optional standalone spare outside the canonical assembly.
- Inputs: prose-only `WISH.json`; no drawing, photograph, prototype, or likeness reference exists. All detailed geometry is invented.
- Units: millimetres. Assembly frame: X left/right, +Y forward, +Z up; ground is Z=0.
- Target envelope: approximately 210 X × 190 Y × 96 Z; body approximately 88 × 112 × 40.
- Required form: low yellow three-plate armored island over a charcoal chassis; six black segmented legs; separate yellow leg armor; separate cyan passive conduit crescents; blunt pointed-looking feet; one forward cannon and faceted sensor triplet.
- Manufacturing: supportless FDM intent at `NOZZLE_MM` 0.4 mm nozzle; every printable component is independently bed-oriented; structural walls/features at least 1.2 mm, with socket regions at least 2.0 mm. `[assumed]`
- Positioning/mating: six fixed radial leg poses; keyed rectangular tenons and asymmetric mortises use one-source `cadfits.slot_for` derivations; the canonical static assembly relies on these keyed joints and uses no lock-pin occurrences; assembly placement is parameterized and labeled.
- Truth boundary: no articulation, walking, firing, lighting, physical print, snap force, durability, or printer-specific fit is claimed.
- Outputs: `rivetback.step.py` combined entry, one role-named part generator per unique printable component, sibling STEP files, root delivery copies, production occurrence STEP files, measurements, and canonical renders.
- Validation: layout, generation, per-component make rounds, combined make round, bounding facts, source fit audit, topology, assembly interference, 0.4 mm thickness/overhang/mesh gates, independent signature review, and final integrated verifier. `[assumed]`

## Dimension and provenance ledger

Every number below is `[assumed]`, derived from the Wish and the selected-Inventor handoff rather than observed from a real machine.

- Chassis: 78 × 92 × 18, bottom at assembly Z=35.
- Carapace widths: `PLATE_WIDTH_MM` 88 mm; three clipped plates with open black shadow gaps. `[assumed]`
- Leg roots: six parameterized stations around the chassis; all legs use repeated geometry and fixed transforms.
- Fit families: small armor peg 4.0 with `SMALL_PEG_CLEARANCE_MM` 0.20 mm/side clearance; structural keyed tenon 8 × 6 with `TENON_CLEARANCE_MM` 0.25 mm/side clearance; hip key 8.0 with `HIP_CLEARANCE_MM` 0.25 mm/side clearance; optional spare lock pin 5.0 with `PIN_CLEARANCE_MM` 0.20 mm/side clearance. `[assumed]`
- Colors are authored directly as sRGB channel triples required by the Make contract: yellow `#D9A514`, charcoal `#191B1C`, cyan `#25C7D9`.

## Part and interface plan

The 16 unique roles are chassis core, fore/center/aft carapace, hub pedestal, cannon body, muzzle collar, sensor insert, hip yoke, upper beam, upper armor, lower beam, lower armor, passive conduit, foot, and optional joint lock pin. The canonical assembly contains 50 labeled occurrences and omits lock pins after deterministic interference review showed the keyed joints were the cleaner static solution. Repeated occurrences are copies positioned by the assembly source; no component generator returns a plate of disconnected loose pieces.

Sockets are open or steep-roofed in each chosen print stance. The cyan crescent is a flat extruded ring segment and carries no load. Feet end in a broad sole and rounded wedge profile rather than a needle point. The combined model is view-only and all `part_*.step.py` entries are printable.
