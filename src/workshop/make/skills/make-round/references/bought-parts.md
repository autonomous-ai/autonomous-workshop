# A powered toy's Bought Parts in its model

ADR 0095, amendment of 2026-11-01. Read this once when the sealed contract
states a circuit (a schema 10 `electrical` section, no `assembly_tree`). It
applies only when the Wish's catalogue snapshot (`WISH.json`
`context.kit_catalogue.bought_parts`) records a `model` for one of the
circuit's parts; `bought_model.py <project> --applies` exits 0 when it does.

The sealed `assembled.step` then carries every Bought Part as a magenta,
not-printed body named `bought_<part>` (`bought_<part>_<n>` for a part whose
count is above 1, `bought_pcba` for the factory-assembled board). These are
never print parts: they are no `part_*` entry, no print gate reads them, and
they get no `parts/` production STEP.

## Steps

1. Write `measure/power.json` first. Its `cad.source` envelopes are the
   mounts `check_mount` judged; each body is seated inside its part's
   envelope, so an envelope smaller than the catalogue part refuses here.
2. Write `measure/bought-placements.json`:

   ```json
   {"kind": "bought-placements", "schema_version": 1,
    "parts": {"usb-c": {"facing": "-y"},
              "s-half": {"facing": "+z", "hinge": "+x"}},
    "pcba": {"envelope": "ref/validation/pcba-envelope.step"},
    "routes": [{"wire": "wire", "from": "s-half", "to": "pcba",
                "points": [[2.4, 16.6, 13.6], [2.4, 29.0, 13.6]]}]}
   ```

   - `facing` is the side the part works through: a receptacle's mouth, an
     LED's light, a lever switch's lever. It is required for those forms.
   - `hinge` is the end of a lever switch's lever that is hinged.
   - `pcba` names the board's envelope, a validation STEP in the assembly
     frame like the power report's. It is required when the contract lists a
     `pcba`, and refused otherwise.
   - `routes` are optional wire polylines in the assembly frame; each end
     lies within 1 mm of the body it joins.
3. Run `"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/bought_model.py
   <project> --build`. It writes `bought/<name>.step`, `bought/__init__.py`
   and `measure/bought-bodies.json`. Fix every refusal it prints; never edit
   what it writes.
4. In the assembly entry, add the group to the compound:

   ```python
   from bought import bought_group
   ...
   asm.children.append(bought_group())
   return asm.build()
   ```

   Then run an assembly round. The bought bodies are magenta in every
   render; that colour is reserved for them. The round's interference check
   sees them too: a clash with a printed part means an envelope, a facing or
   a route is wrong, and you fix that input, not the printed part.
5. Final verification runs `bought_model.py --final`. It refuses a body list
   that is not the plan of the current inputs, then writes
   `measure/electrical/`: `exploded.png`, `cutaway.png`, `wiring.png`,
   `assembly.md` and `electrical.json`.
6. Copy `measure/electrical/assembly.md` into the product `README.md`
   verbatim, as its Electrical assembly section. Write nothing else in the
   README about who assembles, fits or solders the circuit, or about a PCBA:
   that text follows the contract's `assembled_by`, `joins` and `pcba`
   fields, and your own prose may contradict it.

## What the host checks

Before Make is accepted, without rebuilding any geometry, the host checks
that:

- final verification passed `bought_model.py`;
- there is one body per carried part instance, and the board exactly when
  the contract lists a `pcba`;
- every body STEP is the one the list records;
- the assembly-package's `bought_` occurrences are exactly those bodies, in
  magenta;
- the pictures and text are the ones `electrical.json` names;
- the README carries `assembly.md`.

## On a fix run

A toy sealed before catalogue models existed gets its Bought Parts through a
`workshop fix` round whose contract the owner amended, if the circuit needs
it, and whose Wish seals the current catalogue. Every printed Component
carries forward unchanged. The round's work is steps 2 to 6, followed by an
assembly round and `--full`.
