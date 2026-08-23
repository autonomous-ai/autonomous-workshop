# Project structure

SKILL.md covers the canonical layout and the project rules; this file adds the
decision table and editing discipline.

Load this when the user asks for any non-trivial part — multi-part
assembly, more than ~5 features, anything that wants to be tweaked over
time.

## When to use a project, not a single file

| Single ``.py`` | Project directory |
|---|---|
| Cube, plate, hook, single knob, single bracket | Enclosure with base + lid |
| <120 lines | Multi-part assembly |
| One physical body | 3+ named parts or 5+ features |
| Throwaway / one-shot | The user might come back and tweak it |

When in doubt, prefer the project. The edit affordances pay off after
the first iteration.

(The canonical project layout and the project-format rules — dimensions in
``params.py``, one file per part, features as functions, assemblies position
not deform, ``validation.py`` runs first — live in SKILL.md under "Treat the
design as a project". Don't restate them; the items below are the parts that
file doesn't carry.)

## Entry point

``main.py`` MUST define ``gen_step()`` returning the shape (legacy: a
module-level ``result`` still works). The runner calls ``gen_step()`` and
exports STL + STEP + metadata from what it returns. Don't write files inside
``main.py``; just return the shape (a ``cq.Workplane`` / ``cq.Shape`` /
``cq.Assembly``, or an envelope ``dict``).

## Stable, intent-aligned names

Names are an editing API. The agent searches by intent:

```
# Good — agent edit "make the USB cutout bigger" hits exactly one place
add_left_usb_c_cutout(part, p)
add_right_button_cutout(part, p)
add_top_vent_slots(part, p)

# Bad — opaque, agent has to read code to find the right spot
thing1(part, p)
modify(part, p)
helper2(part, p)
```

Name features by intent: ``add_left_usb_c_cutout``, ``apply_corner_fillets``,
``mirror_to_right_side``. Not ``thing1``, ``fix_hole``, ``helper``.

## Editing rules for the agent

When the user asks for a change:

1. **Dimension change** ("2mm thicker wall", "10mm longer") → edit
   ``params.py`` ONLY. Don't touch geometry.
2. **New feature** ("add USB cutout", "vent slots on top") → add a new
   feature function in ``features/`` or the relevant ``parts/<file>.py``,
   add a call site in the feature pipeline, add dimensions to
   ``params.py``.
3. **Remove feature** → comment out the call in the pipeline; don't
   delete the function (user might want it back next turn).
4. **New part** → new file in ``parts/``, register in the assembly.
5. **Tighter / looser fit** → adjust gap parameters in ``params.py``
   (``lid_gap``, ``shaft_fit``, etc.).
6. **Different material / printer** → edit ``validation.py`` constants
   (``min_wall``, ``min_overhang_angle``, etc.).

After any edit, run ``scripts/cad <project_dir>/`` and inspect the STL.
The loop applies the same way — project mode doesn't change it.

## What the agent should AVOID

- Mixing dimensions and geometry. If you find yourself typing a number
  inside ``parts/*.py``, stop. Add it to ``params.py`` first.
- Single-file refactors of a project. If the user has a project, keep
  it as a project — don't flatten into one giant file because it feels
  simpler to write.
- Inline assembly inside a part file. Parts don't know about each
  other; if you need two parts coordinated, that's an assembly.
- Renames without need. If the agent renames ``make_base`` →
  ``build_base`` between turns, the user has to mentally chase. Stick
  with the names the project established.
