# Rivetback H-6 V2

![Rivetback H-6 V2](cad/snap/iso_v2.png)

**Archive status:** Local generated revision; historical digital verification report available.

Hard-surface refinement of the original armed hexapod. The saved V2 final report records PASS. The original CAD README includes inherited V1 descriptions; the V2 geometry and specification are the revision assets.

## Design files

- [Editable assembly entry](cad/rivetback.step.py)
- `cad/part_*.step.py`: individual component generators.
- `cad/part_*.step`: existing generated component geometry.
- `cad/parts/`, `cad/features/`, `cad/assemblies/`: shared model source.
- [Original CAD documentation](cad/README.md)

## Existing verification records

- [validate_v2_final.json](cad/measure/validate_v2_final.json)
- [verification_v2_final.md](cad/measure/verification_v2_final.md)

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
