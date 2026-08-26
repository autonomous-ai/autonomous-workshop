# Multi-part project structure

Read this when a model outgrows one file: a multi-part assembly, a part with
more than ~120 lines of geometry, anything with separately printable pieces, or
anything the user will come back and tweak.

**Once `gen` has part entries, this layout is not advisory.** A project with
`part_*.step.py` files beside its assembly entry owes the whole format below —
the right tier, one parameter block, one module per part, assembly-is-positioning
— and `scripts/check_layout` fails it when it does not.

Making it mandatory rather than recommended is a response to how it actually
fails. Reaching Tier 2 is easy; *outgrowing* Tier 2 is invisible. A 700-line
library builds, writes its STEP, and passes `validate`, `interfere`,
`check_motion`, `check_fit` and `check_mesh` exactly like a healthy one — none of
those gates has an opinion about where code lives. Only a line count catches it,
so the line count is a gate.

## How many printed parts?

Decide this before the layout, because it decides the layout. **Default to one
part.** Most objects are a single sculpted body; a unified body looks better,
prints better, and has nothing to misfit.

Split into a separate printed part only when at least one of these is true:

1. It must open or be removed in use — a lid, a cover, a cap, a drawer.
2. It moves relative to the rest — hinge, linkage, bearing, rotating joint —
   and is not print-in-place.
3. No single orientation can print it — two functional faces that must both be
   smooth and face opposite ways, or an unsupportable internal void.
4. It exceeds the print bed in every orientation.
5. It must be a different material or colour, and the user said so.
6. It is a purchased component, not printed at all. A bearing, magnet, screw,
   PCB, or motor is not a printed part — it is a pocket in one. Model the
   pocket, sized from the real component, and search `$step-parts` for it first.

When none applies, or when you are genuinely unsure: one part. A visible parting
line on a reference photo is not a reason to split — mass-produced objects carry
seams from mould tooling and factory assembly that a printed part does not need.
`$image-to-cad`'s `references/decomposition.md` defers to this rule and expands
the reasoning for reconstructions.

A part count is not a file count. One printed part with a dozen features still
earns the layout below; three parts do not have to mean three directories.

This is the sentence that gets skipped. "Default to one part" answers *what
gets printed*; it does not answer *how many files*. A one-piece display model —
an aircraft, a figurine, a vehicle — is still 300 lines and 50 named solids, and
it gets the directory. Decide the two questions separately, in that order, and
run `scripts/check_layout` rather than deciding the second one by feel.

## One file, or a directory?

| Single `<name>.step.py` | Project directory |
|---|---|
| Cube with a hole, plate, hook, bracket, single knob | Enclosure with base + lid |
| Under ~120 lines | Multi-part assembly |
| One physical body | 3+ named parts, or 5+ distinct features |
| One-shot | The user will iterate on it |

When in doubt, prefer the directory. The edit affordances pay for themselves on
the first follow-up turn.

`scripts/check_layout` decides this mechanically. Point it at a project
directory or the worktree; it reads source only (no build123d import), so it is
safe to run before the model builds:

```bash
python "$CAD_SKILL_ROOT/scripts/check_layout" <project-dir>
python "$CAD_SKILL_ROOT/scripts/check_layout" --json
```

It fails a project three ways:

| rule | what it caught |
|---|---|
| `unsplit-entry` | an entry generator over the thresholds with no `part_*.step.py` beside it |
| `missing-assembly-entry` | part entries with no combined assembly entry — both halves are required, see SKILL.md step 6 |
| `oversized-library` | a project **that has part entries** whose importable modules have passed the Tier 3 threshold below |

The third only fires once part entries exist, which is the point at which the
layout stops being a suggestion. It walks the project's own subpackages too, so
moving 700 lines into a single `parts/everything.py` does not satisfy it — Tier 3
is only worth the churn if the modules that come out of it are readable.

## Three tiers

**Tier 1 — one entry generator.** `<name>.step.py` with `gen_step()`. Nothing
else.

**Tier 2 — library plus entries.** The working default for a reconstructed
object:

```
<project-dir>/
├── <name>_spec.md                     design intent (image-to-cad output)
├── <name>_lib.py                      ALL parameters + part builders
├── <name>.step.py                     assembly entry — placement + labels only
├── part_body.step.py                  one printable part, in print orientation
├── part_lid.step.py
├── part_base.step.py
└── README.md                          what each file is, sizes, rebuild commands
```

**Tier 3 — project package.** When the library file itself passes ~400 lines or
the parts stop being readable side by side, split it. The first half of that
sentence is what `check_layout` measures — **400 code lines**, comments and
docstrings excluded — and it is a floor, not the whole test: a 300-line library
whose parts have stopped being readable side by side is still due the package.

```
<project>/
├── <name>_spec.md      design intent
├── params.py           ALL dimensions + manufacturing constants
├── validation.py       assert checks on the parameters, run before geometry
├── parts/              one module per physical part
│   ├── __init__.py
│   ├── body.py
│   └── lid.py
├── features/           reusable feature functions (vents, cutouts, bosses)
│   └── __init__.py
├── assemblies/         named placement of parts — no geometry
│   ├── __init__.py
│   └── product.py
├── <name>.step.py      assembly entry
└── part_<x>.step.py    one print-orientation entry per printable part
```

There is no project manifest and no directory-level build. Every tier is built
the same way: `scripts/gen` on an explicit entry target.

## Filenames

- **Entry generators are `<name>.step.py`.** That suffix is what the build
  tools scan for. Every entry defines `gen_step()`.
- **Everything importable is a plain `<name>.py`.** A `.step.py` file cannot be
  imported by name — `import foo` does not find `foo.step.py`. Shared
  parameters, builders, and feature functions therefore live in `.py` modules;
  see `step-generation.md`.
- **One entry per part**, named `part_<role>.step.py`, returning that part
  alone. The assembled entry is for viewing; the `part_*` entries are what get
  opened, edited, and — when they are printable parts — sliced.
  - A **printable part** returns in its print orientation, bed datum at Z=0.
  - A **logical part** — a group of a one-piece model, split for review and
    editing rather than for the bed — returns in assembly coordinates, carries
    no mating features, and says so in its docstring. A display model that
    stays one printed piece still gets these entries.
- **A STEP output keeps its generator's basename and directory.** `--write`
  puts `<name>.step` next to `<name>.step.py`.

## Companion files

A reconstruction directory carries more than its generators:

| path | what it holds | written by |
|---|---|---|
| `<name>_spec.md` | the build spec — sections, dimension ledger, provenance of every number | `$image-to-cad`, from `templates/build_spec.md` |
| `README.md` | file map, assembled size, print table, rebuild commands | you, once the model validates |
| `ref/` | the source images, copied into the project | you, when reconstructing from references |
| `measure/` | probe scripts, image crops, and the measurement ledger they produced | you, during the measuring pass |
| `__cadgen__/`, `__pycache__/` | build cache and bytecode — gitignored, regenerated on demand | the tooling |

Exported artifacts (`.step`, `.stl`, `.3mf`, `.glb`) sit beside the generator
that produced them, sharing its basename.

**There is no project manifest.** No `cad_project.json`, no metadata file, and
nothing to keep in sync with the source. The set of entries is simply whichever
`.step.py` files sit in the directory, and every build takes explicit
targets. What a manifest would carry
lives in prose instead — the spec owns design intent and the dimension ledger,
the README owns the file map and the rebuild commands. Both are read by the
next agent, so keep them current the way you would keep a manifest current.

**The JSON in a project is output, never input.** A measurement ledger under
`measure/` and the descriptors inside `__cadgen__/` are both records of
something that already ran. No build step
reads them back, so do not hand-edit one to change a model — change the
parameter and regenerate.

The other naming rules live with the thing they name: parameter names in
`parameters.md`, part/occurrence/feature labels in `build123d-modeling.md`, and
the entry-versus-helper file rule in `step-generation.md`. All of them agree on
snake_case names that state intent.

## Import resolution

`scripts/gen` seeds `sys.path` with the entry script's own directory (see
`cadgen/_internal/generation_runner.py`), and nothing else from the repository.
So a sibling `<name>_lib.py` and a `parts/` subpackage sitting next to the entry
both import normally, while anything outside the project directory does not.
Two consequences:

- Import sibling modules at module top level, never inside `gen_step()`. The
  seeded path is restored once the module finishes executing, so an import
  attempted at call time fails with a bare `No module named ...`.
- Keep the entries at the project root, alongside the modules they import.

## Rules of the format

- **All dimensions live in one place** — `<name>_lib.py`'s parameter block, or
  `params.py`. Geometry code never hardcodes a number. Bad:
  `Box(220, 180, 213)`. Good: `Box(BODY_W, BODY_D, BODY_H)`.
- **One module per physical part.** A part builds in its own local frame and
  knows nothing about its siblings.
- **Every mating interface derives from one base value**, with the clearance
  applied in exactly one place. Never size the two halves independently.
- **Assembly is positioning, never geometry.** Compose with
  `cadgen.assembly.AssemblyHelper`: `asm.add(Location(AT) * build_part(), "name",
  color=...)`, then `asm.compound()`. Boolean-union only what is manufactured as
  a single part; keep separately printable pieces as named children so the next
  turn can address them by name.
- **Each feature is its own function**, named by intent. `add_rear_vent_slots`,
  `apply_corner_fillets`, `mirror_to_right_side` — not `thing1`, `fix_hole`,
  `helper2`. Names are the editing API: the next edit request is a search for
  one of them.
- **Parameter checks run before geometry.** Assert shared dimensions, clearance
  application, connector naming, and other algebraic invariants before building
  so bad numbers fail loudly. Do not rebuild all shapes in a local audit merely
  to repeat solid/body/volume checks already owned by `check_fit`, `validate`,
  and `check_mesh`.
- **Say when an STL is repaired.** `scripts/repair_mesh` writes a mesh the
  generator does not produce, so a project shipping one has to name it in the
  README beside the `check_mesh` result. Nothing else compares the two.
- **Record the provenance** of each dimension — `[observed]`, `[inferred]`,
  `[assumed]` — in a comment next to it, and cross-reference the spec section.

## Editing rules

1. **Dimension change** ("2 mm thicker wall") → edit the parameter block only.
   Do not touch geometry.
2. **New feature** ("vent slots on the back") → new feature function, a call
   site in that part's pipeline, new parameters. Three edits, each obvious.
3. **Remove a feature** → comment out the call site; keep the function. The
   user often wants it back next turn.
4. **New physical part** → new module in `parts/` (or a new builder in the lib),
   register it in the assembly, add a `part_<role>.step.py` print entry.
5. **Tighter or looser fit** → adjust the clearance parameter, nothing else.
6. **Different printer or material** → adjust the validation constants.
7. **Moving up a tier** → a pure move. Prove it the way `parameters.md` asks a
   `cadfits` migration to be proved: fingerprint every entry's volume, solid
   count and bbox straight from source before the split, again after, and diff.
   A tier migration touches every import in the project and is exactly the kind
   of edit that silently drops a feature — the diff is what turns "I only moved
   code" from a claim into a check. Measured on a 10-part project: 440 code
   lines of library became `params.py` + `validation.py` + `features/` +
   `parts/` + `assemblies/`, and the fingerprint was byte-identical.

After an entry-only edit, run `scripts/gen` on that affected entry, then the
checks tied to the changed feature. After a shared `*_lib.py` edit, delete the
project's `__cadgen__` cache first: the local Tier 2 source-closure invalidation
is known to serve stale packages even with `--force`. During iteration, rebuild
the combined entry only when that is sufficient for the current visual or
measurement question. Before final handoff, pass every affected combined/part
entry to one multi-target `scripts/gen ... --write` call and run the full gate.
See "Shared-library cache defect" in `step-generation.md`.

## Avoid

- Mixing dimensions into geometry. If you are typing a number inside a part
  builder, it belongs in the parameter block first.
- Flattening a project back into one file because a single edit felt easier to
  write that way.
- Assembling inside a part module. Parts do not know about each other; two
  coordinated parts are an assembly.
- Boolean-unioning parts that are printed or removed separately.
- Renaming between turns without a reason. The user is tracking the names the
  project already established.
