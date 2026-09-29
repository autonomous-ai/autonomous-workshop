- Resync the vendored `cad`, `design-reference`,
  `electromechanical-integration`, `image-to-cad` and `step-parts` skills to
  `autonomous-ai/autonomous-product-to-cad` `bd1dcdc`, and materialize four
  more upstream skills into every product run: `wiki` (a searchable design
  knowledge base, read-only in a run) replaces the retired `mechanisms`,
  `product-design` designs a prose Wish whose design is still open, and
  `step-to-source` and `stl-to-step` rebuild a supplied STEP or STL as source.
  Upstream's `toy-archive` is not adopted, because Factory publication is a host
  effect. `cad` gains `stdpart` standard elements, which adds the
  `bd-warehouse` and `py-gearworks` dependencies. It also gains the
  `cadcache.py` build cache, the `CARRIES` declaration and the PLA Matte stock;
  a bare `"PLA"` material now raises, so name `PLA Lite` or `PLA Matte`.
- **`verify_project --image-derived` requires a camera on every reference**,
  as `--likeness-ref LABEL=PATH@AZ,EL[,TOL]`, so the likeness gate can catch a
  model built the wrong way round. `make_round` accepts the same suffix on
  `--ref`, reads it from the build spec's camera column, passes it to
  `render_views --camera` and forwards it on `--full`. A `--ref` that copies a
  sealed Wish image lends that image its camera.
- The run input caps rise from 4 MiB and 512 files to 6 MiB and 768 files, so
  the larger installed tool tree keeps its headroom for Wish references and a
  correction's imported tree. The occurrence-name colour vocabulary gains the
  PLA Matte colours.
- **Materialized instruction bytes changed**: five skill fingerprints move
  (`step-parts` does not), four trees are added, one is dropped, and the
  product-run `make.md` and `make-playtest.md` change. A run parked before this
  change must be restarted rather than resumed. `workshop resume
  --refresh-tools` brings a parked run the resynced trees but none of the new
  ones. An all-planar part now writes different STEP bytes, so a `workshop fix`
  of an older archive re-measures such parts instead of carrying them forward.
