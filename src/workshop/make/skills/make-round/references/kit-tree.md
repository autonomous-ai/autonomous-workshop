# The kit's Assembly Tree (ADR 0092)

Read this once when the sealed Design Contract has an `assembly_tree`
(schema 7, or a schema 8 kit).

A schema 7 Design Contract, and a schema 8 kit (ADR 0093), splits the toy
into kit Parts and joins them in an Assembly Tree, in Manual order. Before any worker starts, the Workshop
Manager installs the tree beside the Print Sheets:

```bash
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/kit_tree.py --install <cad-project> --wish WISH.json
```

It writes `tree/kit.json`: the tree, the geometries, the Print Pieces and
the catalogue entries the Wish sealed (`kit_catalogue`). Never edit it; a
round of a schema 7 run fails its `tree` line until it is the sealed one.

**How a Part is a STEP body.** A Component's `gen_step()` returns one
labelled solid per printed Part of the Component, its label the Part id
(`A03-hat`), coloured with its filament's catalogue hex
(`cadgen.srgb(<hex>)`; `tree/kit.json` `catalogue.filaments`). A Component
that holds Bought Parts also defines `bought_parts()`, returning one labelled
body per Bought Part (`P02-steel-pin`) at its catalogue size, in the same
frame as `gen_step()`, coloured the reserved not-printed magenta `#ff00ff`
(`cadgen.srgb("#ff00ff")`), which no filament takes; it is never printed.
When one Component instance
holds a Part more than once, the copies are `<id>#1`, `<id>#2`, ... in Manual
order: copy k of a step takes the next `count` copies of each of its inputs.
Instance n of a geometry whose count is above 1 is the n-th copy of its
subtree. `assembly_pose(shape, None)` moves the shape as a whole and keeps
its labels. Unlabelled nodes are looked through; a solid reached without a
Part label is an extra body.

**Each Part prints alone** (owner decision 2026-10-28). A kit Component's
file also defines `print_parts()`, returning `{Part id: shape}`: every
printed Part of the Component, once per Part id (copies are the same Part,
so no `#n`), each alone in the stance it prints in, bottom at Z 0 (centred
in X and Y is fine). Bought Parts and Print Pieces are not in it. The
Contract Proof writes the same `print_parts()` and gates it with this
skill's own code (`make_round --print-gates-only`). `check_mesh`, `check_overhang`
and `check_thickness` measure each of those Parts on its own, in component
rounds, assembly rounds and final verification, never `gen_step()`'s
assembled Component: assembled, a flat top board is an inner ceiling over
air. The `parts` line and `print.<role>.parts` give each Part's verdict;
the Component passes only when every Part does, and each failure names its
Part (`cabinet/B04-top-board`). A missing `print_parts()`, a printed Part
left out, or a Bought Part, Print Piece, copy, unknown Part or another
Component's Part named in it fails the round's `parts` line with the
repair, like a print gate, and nothing is gated in its place. A Part whose
stance changed is gated again even when the assembled Component did not
move. The tree, Interface, envelope, motion, paper and review checks still
read the assembled Component.

**What the gates check.** `kit_tree.py` reconciles every body, Print Piece
and cited Bought Part with exactly one leaf; checks each printed Part is in
its filament's colour and never `#ff00ff`, and each Bought Part in
`#ff00ff`; sweeps each input of each joining step alone from wholly outside
the rest of its Sub-assembly to its seat, against only what is already
assembled, along its declared direction (a `check_motion`
`assembly_sequence` of `linear_motion_collision` conditions, overlap above
0.001 mm3 fails, contact at the seat allowed, sampled no coarser than the
thinnest wall); refuses an input that only goes in together with another
(a simultaneous move) and a mating face pair at an angle to the direction (a
non-parallel joint); and sweeps a sphere of each Wired Part's lead diameter
plus 0.4 mm along every declared lead route. A Wired Part is a lamp or, from
ADR 0095, any Bought Part whose catalogue entry has a `lead diameter` (a
lever switch, a resistor, a wire).

**Where each check runs.** A step whose Parts all belong to one Component is
checked in that Component's round (its `tree` line); a step across
Components in every assembly round and in final verification, which also
reconciles every Component and writes `measure/tree-report.json` for the
host, and `measure/not-printed.json`: every Bought Part body of the toy
(`<id>#n` across the toy) with its catalogue id, which the host checks, the
receipt lists and Release ships beside the STEP files. The `paper` gate
follows the same split: a Print Piece on a printed
Part, or on a Sub-assembly inside one Component, is that Component's to
carry; one on a Bought Part has no printed feature; one on a Sub-assembly
across Components must be carried by exactly one of their parts, which
assembly rounds and final verification check.

**A labelling slip is repaired; a contract tree defect stops the run**
(decision 10 as the owner amended it on 2026-10-23, Q28).

- A **labelling slip** means the tree holds together but the built bodies
  do not match it: a body with a wrong or unknown Part label, a missing,
  extra or duplicated body, a Part built in another Component, or a wrong
  colour. The `tree` line fails with `labelling slip: ...` lines. Repair it
  in the next round like any failing gate: the Component Worker in its
  component round, the Manager in the next assembly round. It records
  nothing and stops nothing.
- A **contract tree defect** means the sealed tree itself does not hold
  together: a Print Piece or Bought Part it cannot account for, a leaf in
  two steps, a Part in no step or no Component, or a leads step below its
  lamps' smallest common Sub-assembly. It prints `TREE DEFECT` with a need,
  records `measure/tree-defects.json`, and from then on `make_round`
  refuses every round of that tree. A worker reports it to the Manager and
  changes nothing; the Manager stops the run with the need it names
  (`stage_proposal.py need --stage make --status waiting`). Nothing in the
  run repairs the tree: the owner corrects the contract, and the
  build-a-toy loop logs the defect in the toy's `TREE-ISSUES.md`.

Insertion and lead-route failures are repairs like a print gate's.

**The Manual** (ADR 0092 decision 9). Final verification, after the tree
gates and the Print Sheets pass, runs

```bash
"$WORKSHOP_PYTHON" .agents/skills/make-round/scripts/kit_manual.py <cad-project>
```

which writes `manual/manual.pdf` and its report `manual/manual.json`. It is
deterministic: the same tree and build give the same bytes. It builds every
Component as the final tree gate does and draws, from one fixed camera:
a front page of tools, warnings, every Bought Part under "Bought, not
printed" (Q29) and "check all Parts first"; the Check Steps; one section
per Component (bag, printed / paper / "bought, not printed" material
list, 1:1 gauges, one exploded picture per step with arrows along each
insertion direction, a correct/incorrect pair for an `error_prone` step);
one join section per step across Components; the completion picture and
the after-sales contact from `make-round/company.json`. Every sentence is
the contract's own (`text`, names, lead `exit`s) or a fixed label: nobody
writes or edits the Manual. It fails only when the tree cannot be written
(a step with no instruction, an unknown Part id, a leaf in no or two
material lists, which a sealed contract never gives) or a Component fails
to build. The host accepts Make only with a passing Manual for the sealed
tree, and Release ships the PDF in `make/manual/`. A leads step's `method`
(ADR 0095) titles it: `twist`, `solder` or `connector`. A soldered step adds
a soldering iron and solder to the self-prepared tools and the company's
`warnings.soldering` to the front page (no warning, no Manual); loose cells
print one `Batteries: N x <name>` line.
