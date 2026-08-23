# living-hinge

**Trigger:** load when the user asks for a hinge, fold-open lid, clamshell case,
flap, or any part that needs to fold/pivot without separate fasteners.

## Why this exists (the mechanics)

A living hinge is a thin web that bends in place of a pivot pin. Outer-fiber
strain at full fold is `ε ≈ (h / 2) / R`, where `h` is web thickness and `R` is
the bend radius the web wraps around (R ≈ hinge_length / π for a 180° fold).
Example: a 0.5 mm web folded around R = 1 mm sees ε ≈ 25% — way past yield for
rigid plastics, which is why the web must be thin and the gap relatively wide.
To survive cycling, ε must stay below the material's yield strain: PETG/PP/TPU
tolerate ~3–5% repeatedly, PLA only ~1% and goes brittle fast. The hinge axis
MUST be perpendicular to print layer lines (bend axis parallel to layers) or
the part splits along a layer boundary on the first flex.

## CadQuery template

```python
import cadquery as cq

def make_living_hinge(p):
    """Build two rigid panels joined by a thin flexure web.

    Required params (mm):
      panel_width        - width of each rigid panel (perpendicular to hinge axis)
      panel_length       - length along the hinge axis
      panel_thickness    - thickness of the rigid bits
      hinge_thickness    - web thickness (0.4-0.6 for PETG, 0.8-1.0 for TPU)
      hinge_length       - gap between panels filled by the web
      hinge_count        - for wide hinges, segment into multiple strips (1 = solid web)
      hinge_strip_gap    - gap between strips when segmented (used if hinge_count > 1)
    """
    pw = p.panel_width
    pl = p.panel_length
    pt = p.panel_thickness
    ht = p.hinge_thickness
    hl = p.hinge_length
    n  = getattr(p, "hinge_count", 1)
    sg = getattr(p, "hinge_strip_gap", 2.0)

    # Two rigid panels, centered on Y, separated along X by hinge_length.
    # Panels sit on Z=0 (bottom face) so the web aligns with the bottom layers,
    # which means bending axis runs along Y and is parallel to print layers.
    left = (
        cq.Workplane("XY")
        .box(pw, pl, pt, centered=(False, True, False))
        .translate((-(pw + hl / 2), 0, 0))
    )
    right = (
        cq.Workplane("XY")
        .box(pw, pl, pt, centered=(False, True, False))
        .translate((hl / 2, 0, 0))
    )

    result = left.union(right)

    # Web(s): thin strip(s) bridging the gap on the bottom face.
    if n <= 1:
        web = (
            cq.Workplane("XY")
            .box(hl, pl, ht, centered=(True, True, False))
        )
        result = result.union(web)
    else:
        # Segmented hinge: n strips of equal width with sg gaps between.
        strip_w = (pl - sg * (n - 1)) / n
        if strip_w <= 0:
            raise ValueError("hinge_count too high for panel_length / strip_gap")
        y0 = -pl / 2
        for i in range(n):
            yc = y0 + strip_w / 2 + i * (strip_w + sg)
            strip = (
                cq.Workplane("XY")
                .box(hl, strip_w, ht, centered=(True, False, False))
                .translate((0, yc, 0))
            )
            result = result.union(strip)

    return result
```

## Parameter ranges

| Param | Reasonable range | Notes |
|---|---|---|
| hinge_thickness | 0.4-0.6 mm (PETG), 0.6-1.0 mm (TPU), DON'T (PLA) | one perimeter at 0.4 mm nozzle |
| hinge_length | 1.5-3 mm | gap the web spans; bigger = lower strain, floppier |
| panel_thickness | 2-4 mm | enough to be rigid vs. the web |
| panel_length (along hinge) | 20-80 mm | wider = more torque support, more layer-line risk |
| hinge_count | 1, or 3-8 for long hinges | segmenting distributes stress |
| hinge_strip_gap | 1.5-3 mm | between segmented strips |

## Material guidance

- **PETG**: best practical choice; 0.4-0.5 mm web, 1000+ cycles realistic.
- **TPU 95A**: 0.8-1.0 mm web, near-unlimited cycling, but panels go soft too.
- **PP (polypropylene)**: gold-standard flexure (Tic-Tac lid material), but
  warps badly and barely sticks to most beds.
- **PLA**: do not. Brittle, snaps in 1-3 cycles (typically fails on first fold
  or within a few). Use a printed pin hinge or a snap-fit instead.
- **ABS/ASA**: marginal; works at 0.6 mm web but layer adhesion is the limit.

## Pitfalls

- **Print orientation**: lay the part FLAT with the hinge axis perpendicular to
  the extrusion direction so layers run *along* the hinge, not across it. If
  layers run across the hinge it delaminates on the first flex.
- **Wall count**: the hinge region must be `wall_loops = 1` (single perimeter)
  in the slicer. Extra walls create internal seams that fight bending and
  initiate cracks. Use a slicer modifier to drop walls in the hinge zone only.
- **Geometry shift on fold**: a hinge isn't a sliding pivot — it stretches the
  outer fiber and shortens the inner fiber as it folds. The two panels won't
  sit flush against each other when closed unless you offset one panel by
  roughly `hinge_length` (the web has to go *somewhere*).
- **First-layer squish fuses the web**: if `hinge_thickness < 0.5 mm` and your
  first layer is 0.2 mm at high squish, the web prints as a solid pad fused to
  the bed. Use a brim (not raft) and tune Z-offset before committing.
- **Long unsegmented hinges warp**: anything past ~40 mm of continuous thin web
  curls on cooldown and prints unevenly. Use `hinge_count = 3-8` strips with
  2-3 mm rigid gaps — looks like a piano hinge and spreads stress.
- **Sharp corners at the panel/web junction**: stress concentrates there and
  cracks initiate. Add a small fillet (0.3-0.5 mm) along the web-to-panel edge
  if cycle life matters.
- **Infill bleeding into the web**: if the panel infill pattern intersects the
  hinge volume, the slicer may add infill inside the web. Keep
  `panel_thickness > 2 * hinge_thickness + 1 mm` so the web sits clearly below
  the panel's bottom solid layers.
