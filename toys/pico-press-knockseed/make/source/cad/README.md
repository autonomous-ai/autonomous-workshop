# Knockseed

One-piece fingertip seed tumbler. Flick the equator; it spins on the rounded
belly and knocks to rest on the same ventral face.

Print stance: ventral knock face on the bed at Z=0.

`--bed 220x220x220`

## Files

- `knockseed.step.py` — combined printable entry
- `knockseed_lib.py` — parameters and solid
- `knockseed.step` / `knockseed.stl` — generated artifacts

## Rebuild

```text
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen artifacts/make/r0001/product/cad/knockseed.step.py --write
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/export artifacts/make/r0001/product/cad/knockseed.step --stl
```
