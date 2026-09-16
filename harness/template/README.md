# Workshop project

| file | what it is |
|---|---|
| `model.step.py` | the combined entry; `gen_step()` returns the object |
| `model.step` | the generated STEP, the only deliverable; rewritten by every `gen --write` |
| `snap/` | review renders (`render_review`, `render_product`) |
| `measure/` | gate reports and manifests written by the CAD tools |

Rebuild:

```bash
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/gen" model.step.py --write
```

Verify (quick, every round; final, once the shape has settled):

```bash
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/verify_project" . --quick
"$WORKSHOP_PYTHON" "$CAD_SKILL_ROOT/scripts/verify_project" . --print-gates --nozzle 0.4
```
