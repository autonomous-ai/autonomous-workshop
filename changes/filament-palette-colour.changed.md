- Resync the vendored `cad` and `image-to-cad` skills to
  `autonomous-ai/autonomous-product-to-cad` `facbc58`, refreshing `LOCK.json`
  and the provenance ledger. `design-reference`,
  `electromechanical-integration`, and `step-parts` are byte-identical to the
  previous snapshot, and `cadgen` remains pinned at 0.4.19.
- **A printed part now takes its colour from stock filament, not from a free
  hex.** The new `cad/scripts/cadfilament.py` holds the Bambu Lab PLA Lite
  palette — 13 names with the hex the catalogue publishes — and
  `filament("sunflower yellow")` converts through `cadgen.color.srgb`, so the
  channels reach the renderer linear. It imports with no path setup wherever
  `cadfits` does, and an unknown name raises with the whole list rather than
  resolving to the nearest colour. `cadgen.srgb("#rrggbb")` stays for the
  colours that are deliberately not filament: a purchased component, a
  reference surface, a see-through datum.
- The four reference files that taught hex authoring now teach the palette:
  **Colour** in `cad/references/build123d-modeling.md` is three rules and
  carries the table, `cad/references/parameters.md` gains a `cadfilament`
  section beside `cadfits`, `cad/references/organic-lofts.md` rounds sampled
  region colours to stock instead of passing raw `Color()` channels, and
  `image-to-cad/references/build123d-operations.md` asks a build spec to name a
  filament per leaf and to record a substitution when the reference colour
  falls between two of them.
- No gate reads the palette — it is a table a generator imports, not a check.
  Geometry is unchanged, the sealed STEP still carries linear RGB, and the
  colours Release publishes are read back exactly as before.
- **Materialized instruction bytes changed**: the `cad` and `image-to-cad`
  fingerprints are new. Frozen runs keep their materialized skills; a parked
  run picks the palette up through `workshop resume --refresh-tools`, which
  rebinds the instruction manifest and records the change in the owner ledger.
