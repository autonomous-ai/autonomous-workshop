# Host CAD gate rejection repair

- Host rejection: `da54b1efa6a8501e5b6f64d8a48937c77e19c04807c777d3d028bc32c146fad6`
- Rejected generator SHA-256: `dc9e7abd24dcda7382484897c3f0569a4cfdf6d830ccd25e534bef139dee258e`
- Repaired generator SHA-256: `fa2713572ea0ddc856891506515f36dce26bc3cb801227b8ae1be217958ab4dc`

The rejected combined entry declared `PRINTABLE = True` while producing nine disconnected solids. It is now a review/storage-layout entry with `PRINTABLE = False`. The three single-family entries remain printable one-body parts, and the product print plan requires three copies of each family STL.

The exact isolated verification used a cold cache, fresh generation, exports, strict fit, and a 220 x 220 x 220 mm bed:

```text
XDG_CACHE_HOME=$PWD/.cache CADGEN_WARM=0 $WORKSHOP_PYTHON .agents/skills/cad/scripts/verify_project _verification/make-r0001-7fbab280/project --fresh --exports --strict-fit --bed 220x220x220
```

Result: PASS (exit 0). Strict fit evaluated exactly `part_comet.step.py`, `part_crescent.step.py`, and `part_star.step.py`; each generated one connected 31.5 x 31.5 x 5.6 mm body. The report is `verification-pipeline.md`.

This is deterministic digital evidence only. It does not claim a physical print, durability result, or human play response.
