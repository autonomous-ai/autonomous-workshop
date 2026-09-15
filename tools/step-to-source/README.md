# step-to-source

Recover editable CadQuery or build123d source from a STEP file, and measure how
far the recovery is from the original.

This directory is the source of truth. Install it as a Claude Code skill with:

```bash
cp -R tools/step-to-source ~/.claude/skills/
```

`SKILL.md` carries the workflow and the measured results;
`references/recovery-limits.md` covers what a B-rep can and cannot give back.

## Scripts

| Script | Needs | Does |
|---|---|---|
| `scripts/step_probe.py` | OCP only | Reports exact B-rep facts: face kinds, bores, chamfers, fillets, arc slots, extrusion axis |
| `scripts/step_emit.py` | OCP only | Emits source by slab decomposition, or refuses when that cannot reproduce the solid |
| `scripts/step_verify.py` | OCP only | Compares a rebuilt STEP to the original by symmetric difference |

Running the emitted source needs `build123d` or `cadquery<2.8`; probing and
verifying do not.

## Deliberately not in `src/workshop/make/skills/`

That tree is hash-locked by `LOCK.json` and its membership is asserted exactly
by `tests/make/test_skill_registry.py`. It holds skills vendored from
`autonomous-product-to-cad`, and adding a Workshop-local tool there would both
fail those tests and collide with the next upstream resync.
