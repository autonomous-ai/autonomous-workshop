# print-in-place

**Trigger:** load when the user asks for a print-in-place / print-in-one /
no-assembly mechanism, a captive moving part (slider, drawer, hinge, knuckle,
gear, ball joint, chain link), "moving parts in a single print", or any joint
that must move but **must not fuse**.

## Why this exists (the mechanics)

Print-in-place means two or more parts are printed **together in one job** and
never separated — they must already move when the print comes off the plate. The
only thing keeping them from fusing into one dead solid is an **open gap on every
face between them**. The dominant failure is "everything's stuck together": the
parts came out as one rigid lump. Three causes, in order of how often they bite:

1. **The vertical (Z) gap fused.** The top surface of a gap is an unsupported
   bridge. The first layer printed across it droops onto the layer below and
   welds. A Z gap therefore needs to be **larger than the horizontal (XY) gap** —
   the single most common mistake is using one uniform gap on all faces.
2. **The build-plate gap closed (elephant's foot).** The squished first layer
   prints ~0.2 mm wider than modeled, narrowing or closing any gap that sits on
   the plate.
3. **The XY gap was too tight.** Simultaneously-printed walls ooze and string
   onto each other; a fit that would slide fine when assembled by hand welds when
   printed in contact.

The fix is mechanical, not cosmetic: leave a real gap on **every** mating face,
make Z bigger than XY, chamfer the bottom, keep the cavity support-free, and
**cross-section it to confirm the gap is actually open before declaring done.**

## Use the helper

`cadlib.fits.print_in_place_gap` is the source of truth for the gaps. It returns
the per-face XY gap, the larger Z gap, and the bottom chamfer for elephant's
foot — do not hardcode your own numbers:

```python
from cadlib.fits import print_in_place_gap

g = print_in_place_gap("sliding", layer_height=0.2, material="PLA")
# {"xy": 0.30, "z": 0.50, "bottom_chamfer": 0.5}
```

Then carve the moving part free of its housing **on every face**, applying
`g["xy"]` to the side faces and the larger `g["z"]` to the top and bottom:

```python
# the captive part is housing-minus-(moving-part-grown-by-the-gap)
clearance_solid = (
    moving_part
    .faces().shell(0)          # conceptually: expand by g["xy"] in XY, g["z"] in Z
)
housing = housing.cut(grown_moving_part)   # leaves an open cavity around it
```

Build both halves from one nominal so they can't drift (mirror the
`slot_for`/`peg_for` discipline). Fit classes: `tight` (0.20 XY — pin-in-barrel
hinge, minimal wobble), `sliding` (0.30 — the default captive slider/drawer),
`loose` (0.40 — large faces, tall Z spans, extra margin). Pass `material="PETG"`
to add the ooze bump.

## Rules

- **Gap on EVERY face, including the top.** A gap on the sides but not the top
  (or vice-versa) fuses on the closed face. Walk all six directions of the
  interface.
- **Z gap > XY gap.** Use `g["z"]` for top/bottom faces, `g["xy"]` for sides.
  The direction is firm; the exact amount is a rule of thumb — tune if it still
  fuses (increase) or rattles (decrease).
- **Bottom chamfer at the plate.** Put a `g["bottom_chamfer"]` × 45° chamfer (or
  extra clearance) on any gap edge that touches the build plate, to clear
  elephant's foot.
- **Support-free cavity.** No supports can be placed inside a captive gap, so
  every internal overhang/roof must be **≤45° from vertical** (load the
  `overhang-relief` and `print-orientation` patterns). A flat gap ceiling wider
  than a few mm needs a self-supporting profile (chamfer/teardrop), not a flat
  bridge.
- **Pick the fit by motion, not by looks.** `tight` for a pivot that should not
  wobble, `sliding` for a part that must glide, `loose` for big contact areas.
- **Material for anything that flexes.** A living hinge or printed return spring
  in PLA snaps in ~10–20 cycles. Prefer PETG (more ductile, far better fatigue
  per its own strength) or a flexible filament; flag PLA to the user for any
  compliant element. A flexing web should be **0.4–0.6 mm thick and ≥2 layers**.

## Verification

A print-in-place mechanism is **not done** until you have proven the gap is open.
Renders of the outside cannot show it — the gap is interior. Cross-section every
gap and look:

```bash
python ~/.claude/skills/cadcode/scripts/review <project_dir> --section z
python ~/.claude/skills/cadcode/scripts/review <project_dir> --section y
```

Confirm in the section that the moving part is **visibly separated** from its
housing on every face, the Z gap reads larger than the XY gap, and nothing
touches. If any face is closed, the parts will fuse — fix the gap and regenerate.
Add a `functional` check that the assembled scene contains the expected number of
**distinct solids** so a fused build trips a warning instead of shipping.

## Pitfalls

- **One uniform gap on all faces.** The classic fuse: the top welds because Z
  needs more than XY. Always split XY vs Z.
- **Accidentally unioning the parts.** Building the moving part and the housing
  and forgetting to `cut` the clearance solid between them yields one fused
  body with zero gap. The cross-section catches this.
- **No bottom chamfer.** A gap that meets the build plate closes under
  elephant's foot even when the model has clearance everywhere else.
- **Supports inside the cavity.** Specifying supports for an enclosed mechanism
  is impossible to remove — design the internal overhangs ≤45° so none are
  needed.
- **Gap below the practical floor.** Below ~0.2 mm XY / ~0.3 mm Z on a calibrated
  0.4 mm-nozzle printer, faces tend to weld regardless. Start at `sliding` and
  only go tighter with a reason.
- **PLA for a live hinge or printed spring.** It fatigues and snaps fast — switch
  the compliant element to PETG/TPU and tell the user why.
- **Declaring done from an exterior render.** The gap is interior; only a
  cross-section proves it is open.
