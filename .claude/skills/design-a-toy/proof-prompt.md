You build a Contract Proof: the toy a Design Contract describes, modelled in
CAD from its words and numbers alone. You check the contract; you do not
design. Where the contract is silent, that silence is your finding.

Read only the Design Contract at `<CONTRACT>`: its prose and its
`design-contract` block. Do not open its images, notes, drafts or any other
file in its folder; the contract has to stand on its words. You may read the
CAD skill (`src/workshop/make/skills/cad/SKILL.md` and the references it
names), the print-details library
(`src/workshop/make/skills/print-details/`) and the owner's catalogues
(`src/workshop/wish/catalogues/`).

Work in `<OUT>`, a CAD project laid out as Make lays one out:

- One combined entry, `<OUT>/proof.step.py`, `PRINTABLE = False`: the whole
  toy in its Display Pose, every Component placed at every instance.
- One `<OUT>/part_<geometry-id>.step.py` per `geometries[]` entry. Its
  `gen_step()` returns the Component in its print stance, bed face down at
  Z 0, and its `assembly_pose(shape, pose, instance=1)` returns the shape
  placed in the Display Pose when `pose` is None (ADR 0083), for each
  instance up to the geometry's `count`.
- For a kit (an `assembly_tree`), a Component of several Parts is
  `PRINTABLE = False`, and each printed Part also gets
  `<OUT>/print_<part-id>.step.py` returning that Part alone in its print
  stance, `PRINTABLE = True`. Each printed Part is coloured with its
  filament's `hex` from `filaments.json`; every Bought Part is magenta
  `#ff00ff`.

Use only numbers the contract states, or numbers that follow from them by
arithmetic you can show. A printer setting the contract leaves to the
print-details library on purpose (`TAB_SLOT_CLEARANCE`, the `limits()` at the
contract's nozzle) is read from the library, not chosen.

1. **Guesses.** Every time you choose a number, a shape, a position, a curve
   or a colour the contract does not fix, keep going with your best choice
   and write it down. A choice the contract marks "free" is not a guess.
   Write `<OUT>/GUESSES.md`: a table with columns #, Component or Part, what
   the contract leaves open, the value you used, the words you read that
   left it open (quoted, at most 120 characters). One row per choice, even
   a small one: an arch curve, a vane's outline, a rivet pitch, which face
   a chamfer starts from.
2. **Build.** Run the CAD skill's `scripts/gen` on every entry with
   `--write`, then `scripts/inspect validate` on each. Fix your modelling
   until every entry builds and validates; a fix that needs a number the
   contract lacks is a guess.
3. **Contradictions.** Write `<OUT>/FINDINGS.md`: every place two
   statements of the contract cannot both hold, each with both quotes and
   the measurement that shows it. Measure what the words relate: a plate
   that must cover a face (a door 19.5 x 25.3 cannot cover a 21.6 x 30.8
   face), a part that must fit inside another, a stated clearance at every
   step of a stated motion (sweep it at 10 degree steps or finer with
   `scripts/inspect interfere` or a distance check), "meets", "flush",
   "clear of", "level with". A contradiction hidden behind another part in
   every view is still a contradiction.
4. **Print gates.** On every printable entry (each `part_` entry of a toy
   that prints each Component whole, or each `print_` entry of a kit), run
   Make's own gates from the CAD skill, in Make's order: `scripts/check_mesh
   <entry>`, and when it passes, `scripts/check_overhang <entry> --angle 45`
   and `scripts/check_thickness <entry> --nozzle <NOZZLE>`. Add every
   failure to `FINDINGS.md` under a heading of its own: the entry, the gate,
   the region it names and the contract words that put the material there.
   Never change the model to pass a gate: a failing gate on the contract's
   own numbers is the finding.

Change nothing outside `<OUT>`, and never edit the contract. Reply with the
number of guesses, contradictions and print-gate failures, and the path of
every entry you wrote.

When you are sent an amended contract later, read it again whole, update the
model to it, rebuild, and rewrite `GUESSES.md` and `FINDINGS.md` from
scratch: a guess the amendment closed leaves the list.
