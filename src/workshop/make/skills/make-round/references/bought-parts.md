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
    "routes": [{"wire": "wire", "from": "s-half", "to": "pcba",
                "points": [[2.4, 16.6, 13.6], [2.4, 29.0, 13.6]]}]}
   ```

   - `facing` is the side the part works through: a receptacle's mouth, an
     LED's light, a lever switch's lever. It is required for those forms,
     and for a `box` whose catalogue entry states both a `body` and a
     `plunger` size (a push switch): that box is drawn as its `body` with
     the plunger as a nose of the plunger's cross-section centred on the
     `facing` side, as long as the `body with plunger out` height above the
     body's (else the plunger's own length). Point `facing` at what the
     plunger drives, such as a button cap's socket.
   - `hinge` is the end of a lever switch's lever that is hinged.
   - `pose` is for a seat that is not square to the world axes, such as a
     switch square to a 30 degree deck or an LED in a sloped wall. Without
     it the body is drawn square to the world, and in a tilted envelope it
     clashes with its own pocket. Give the rotation that turns the world
     axes into the part's own, right-handed about the centre of the
     envelope's world bounding box:
     `"sw": {"facing": "+z", "pose": {"axis": [1, 0, 0], "angle_deg": 30}}`.
     `axis` is a nonzero `[x, y, z]`; `angle_deg` is nonzero and at most
     180 either way. Use the same rotation that tilted the envelope in
     `measure/power.json`'s `cad.source`. The envelope is then read in the
     part's frame, `facing` and `hinge` name the part's own axes, and the
     body list records the body's `seat` and `bounds` in that frame beside
     its `pose`. Route ends are still world points. A seat square to the
     world takes no `pose`; a wire never does.
   - `routes` are optional wire polylines in the assembly frame; each end
     lies within 1 mm of the body it joins.
   - The board (`bought_pcba`) is never placed here. It is drawn exactly at
     the contract's `pcba.bounds_mm`, because the board is no catalogue part
     and only the contract may state its outline. A placements file with a
     `pcba` key is refused.
3. Run `"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/bought_model.py
   <project> --build`. It writes `bought/<name>.step`, `bought/__init__.py`
   and `measure/bought-bodies.json`. Fix every refusal it prints; never edit
   what it writes. The bodies that list names with their current bytes are
   no components: final verification asks them for no mount row,
   `check_mount` leaves them out of the model it measures each mount
   against, and `bought/__init__.py` is no Shared Helper. Any other STEP
   outside `ref/`, including an unlisted one in `bought/`, is still refused.
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
  the contract lists a `pcba`, at its `bounds_mm`;
- every body STEP is the one the list records;
- the assembly-package's `bought_` occurrences are exactly those bodies, in
  magenta;
- the pictures and text are the ones `electrical.json` names;
- the README carries `assembly.md`.

## On a fix run

A toy sealed before catalogue models existed gets its Bought Parts through a
`workshop fix` round whose contract the owner amended (a `pcba` with its
`bounds_mm`, if the toy has a factory-assembled board), and whose Wish
reseals the current catalogue. Every printed Component
carries forward unchanged. The round's work is steps 2 to 6, followed by an
assembly round and `--full`.
