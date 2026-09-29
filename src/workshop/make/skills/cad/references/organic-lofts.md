# Organic bodies: lofts, junctions, and the checks that catch what renders hide

Read this before modelling any animal, figure, vehicle body, hull, or other
freeform mass — anything whose cross-section changes continuously along a
curved spine. Extrudes, revolves and sketches are covered in
`build123d-modeling.md`.

The modelling knowledge lives in the wiki:

- `wiki show loft-organic-bodies` — the station table as the model (12–16
  stations; one every ~25° of a tight spiral), consecutive segments that must
  OVERLAP rather than meet (a loft's end cap is a plane normal to the spine
  tangent), the cap that shows, section families beyond the ellipse, and
  colour regions cut from one fused body.
- `wiki show frames-and-rotations` — the station frame built from a lateral
  reference, never from Z, and which `Ellipse` argument is the half-height.
- `wiki show loft-pitfalls` — sections matched by index, PCHIP not smoothstep,
  ruled lofts, and diagnosing a loft that fails.

## The one-body assertion is mandatory

`inspect validate` and `inspect interfere` both pass a body whose tail is a
separate solid resting against it, and `check_fit` flags `multi-body-part`
only as an advisory note on `part_*.step.py` entries. Put the assertion where
the geometry is built:

```python
assert len(subject.solids()) == 1, (
    f"{len(subject.solids())} disconnected bodies — a segment junction "
    "does not overlap")
```

## Cost of the loop

A dense loft is the slow part of an organic model, and every `gen` rebuild pays
it. Two habits keep the edit loop short:

- Build and check the pieces in a plain Python session (`build_body()`,
  `build_tail()`) before running `scripts/gen`, which additionally writes the
  GLB package.
- Remember to delete `__cadgen__` after editing the `_lib.py`; `--force` does
  not repair a stale package. See "Shared-library cache defect" in
  `step-generation.md`.
