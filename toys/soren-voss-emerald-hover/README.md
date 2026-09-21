# Emerald Hover (Hummingbird)

**Archive status:** Incomplete Make draft: 15 component STEP exports; no assembled STEP, final verification, or verified Factory publication.

Hand-cranked hummingbird design with eccentric cams, a pushrod and articulated wings. This archive preserves the generated component geometry and editable source at the interrupted Make stage. Assembly motion, printability and physical operation remain unverified. The additional Python files in drafts/ are unintegrated source drafts.

## Design files

- [Editable assembly entry](cad/hummingbird.step.py)
- `cad/part_*.step.py`: individual component generators.
- `cad/part_*.step`: existing generated component geometry.
- `cad/parts/`, `cad/features/`, `cad/assemblies/`: shared model source.

## Reuse and provenance

The source uses build123d and Workshop's cadgen/CAD helpers. Use a compatible
Workshop CAD toolchain when rebuilding the explicit `*.step.py` entries.
STEP exports can be opened independently in a STEP-compatible CAD viewer.

This is a generated design archive committed at the owner's request. It does
not represent a completed Factory publication or a new validation run. Digital
reports do not establish a successful physical print, fit, durability or safety.
Only design source, existing STEP geometry, renders and selected engineering
records are included. Local path prefixes in text are replaced with stable
placeholders; `PROVENANCE.json` records original and archived hashes.
`MANIFEST.json` hashes every archived file except itself.
