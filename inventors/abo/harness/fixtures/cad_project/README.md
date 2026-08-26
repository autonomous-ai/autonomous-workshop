# STEP-first board-game gate fixture

This fixture is deliberately small but exercises the full project layout: one
combined assembly, two print-orientation entries, a numeric board-game brief,
a component bill, a local algebraic fit audit, and a motion manifest with both
clear and expected-blocked directions.

Printer declaration: `--bed 246x246x251`.

```bash
.venv/bin/python skills/cad/scripts/verify_project \
  board-game/tests/fixtures/cad_project --fresh --exports --strict-fit
```

No shipped STL is repaired; all derived artifacts must come from the checked
source entries.
