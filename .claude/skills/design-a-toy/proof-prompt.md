You build the toy the owner will approve and Workshop will ship: the
Contract Proof (ADR 0096). Once the owner approves it, its source is the build;
Workshop certifies and packages it and models nothing again.

From round 1 read the Design Contract at `<CONTRACT>` (its prose and its
`design-contract` block), its Reference Images and Guide Images, the chosen
Concept Image and its three views, and `CONCEPT-CHECKLIST.md`. The contract
owns function, critical dimensions, Interfaces, print choices, colours,
Bought Parts and the electrical section (ADR 0096 decision 1c); the images own
the shape. You may read, in every round, the CAD skill
(`src/workshop/make/skills/cad/SKILL.md` and the references it names), the
print-details library (`src/workshop/make/skills/print-details/`), the wiki
(`src/workshop/make/skills/wiki/`), the image-to-cad skill
(`src/workshop/make/skills/image-to-cad/SKILL.md`), the owner's catalogues
(`src/workshop/wish/catalogues/`) and the Make rule homes named below.

Work in `<OUT>`, a CAD project laid out as Make lays one out:

- One combined entry, `<OUT>/proof.step.py`, `PRINTABLE = False`: the whole
  toy in its Display Pose, every Component placed at every instance.
- One `<OUT>/part_<geometry-id>.step.py` per `geometries[]` entry. Its
  `gen_step()` returns the Component in its print stance, bed face down at
  Z 0, and its `assembly_pose(shape, pose, instance=1)` returns the shape
  placed in the Display Pose when `pose` is None (ADR 0083), for each
  instance up to the geometry's `count`.
- For a kit (an `assembly_tree`), each Component's `part_<geometry-id>.step.py`
  is what Make's Component Worker writes (ADR 0092): its `gen_step()`
  returns one body per Part, labelled with the Part id (copies `<id>#1`,
  `<id>#2`), and it also defines `print_parts()`, returning
  `{Part id: shape}`: every printed Part of the Component once (no `#n`),
  each alone in the stance it prints in, bottom at Z 0, and never a Bought
  Part or a Print Piece. Make's print gates measure those Parts, never the
  assembled Component. Each printed Part is coloured with its filament's
  `hex` from `filaments.json`; every Bought Part is magenta `#ff00ff`.

## Write it as Make writes it

Your source seeds the build, so it follows Make's authoring rules exactly.
Read them where they live and copy none of their text here:

- `.agents/product-run/.agents/skills/autonomous-workshop/references/make.md`
  § Pipeline step 1: the component list, the overhang repair order, the
  shared files, the install commands, the Interfaces paragraph and the Shared
  Helper sample paragraph;
- `src/workshop/make/agents/component-worker.toml`: the Shared Helper,
  `assembly_pose`, instance, decorative-detail, Print Piece, kit and
  blunt-tip bullets.

Wherever they say "the Manager" or "the worker", you do both. Run every
command from the repository root with `uv run python`, never
`$WORKSHOP_PYTHON`, and give a file a contract input with `--contract
<CONTRACT>` where a run gives `--wish WISH.json`.

1. **Layout, before any part.** Install the shared files:

   ```
   uv run python src/workshop/make/skills/print-details/scripts/print_details.py --install <OUT>
   ```

   For a contract with a `print` section add `--install-print <OUT>
   --contract <CONTRACT>`; for an Assembly Tree run
   `src/workshop/make/skills/make-round/scripts/kit_tree.py --install <OUT>
   --contract <CONTRACT>`. Never edit an installed file.
2. **Details.** Every decorative detail the contract or the images list goes
   through `Details(nozzle=…)`; every point or rib end through `blunt_tip`
   or `rib_end`. A Detail Refusal goes into `FINDINGS.md` under "Refused
   detail", with the passing value the refusal names. Never model a refused
   detail by hand and never drop one silently.
3. **Joints.** Before each joint, fit, clearance or gear run
   `src/workshop/make/skills/wiki/scripts/wiki search …` and `show …`. Write
   `# wiki: <slug>` beside the value and add the page's `assert`. A fit the
   contract does not give is a guess (fits are a contract field), with the
   page cited.
4. **Standard parts.** Every gear, bearing and fastener comes from
   `src/workshop/make/skills/cad/scripts/stdpart` (`bd_warehouse`,
   `py_gearworks`). Never a hand-written involute. A pin, spring, magnet, cork
   disc or other bought item has no `stdpart`: it is a Bought Part from
   `bought-parts.json`, drawn at the catalogue entry's own sizes in magenta,
   and the printed parts take their fits around it from the wiki. A bought
   item the catalogue lacks is a finding for the owner, never a printed
   copy.
5. **Shared Helpers.** `params.py` and `features/` hold only Interface
   values, joint sections and standard profiles, with one
   `samples/<name>.step.py` per helper. This must pass before the print
   gates:

   ```
   uv run python src/workshop/make/skills/make-round/scripts/make_round <OUT> --shared-helpers --contract <CONTRACT>
   ```
6. **Surfaces.** True arcs and sweeps, not engraving built from many small
   flat faces.

## Model the shape from the images

From round 1, measure each Reference Image, Guide Image and concept view
with the image-to-cad skill's Steps 1-4b and 6: triage, `measure_image.py`,
the cross-check gate, the scale anchor, three views, the per-component
description and the operation map. Never its Step 5 or Step 8. Build the
shape to those measurements and to the checklist's traits. A shape number
stays in the Proof.

1. **Guesses.** Write `<OUT>/GUESSES.md` only for a number that falls in a
   contract field: a fit, a critical dimension, an Interface pose, a colour,
   a bought part. Use a table with columns #, Component or Part, the field
   the contract leaves open, the value you used, and the words you read that
   left it open (quoted, at most 120 characters). The coordinator closes
   these in the contract; this list must reach zero. Where the images and a
   contract field disagree, the contract wins: write it under "Image vs
   contract" in `FINDINGS.md`, so the coordinator can decide whether to
   amend the contract or edit the image.
2. **Build.** Run the CAD skill's `scripts/gen` on every entry with
   `--write`, then `scripts/inspect validate` on each. Fix your modelling
   until every entry builds and validates.
3. **Contradictions.** Write `<OUT>/FINDINGS.md`: every place two
   statements of the contract cannot both hold, each with both quotes and
   the measurement that shows it. Measure what the words relate: a plate
   that must cover a face (a door 19.5 x 25.3 cannot cover a 21.6 x 30.8
   face), a part that must fit inside another, a stated clearance at every
   step of a stated motion (sweep it at 10 degree steps or finer with
   `scripts/inspect interfere` or a distance check), "meets", "flush",
   "clear of", "level with". A contradiction hidden behind another part in
   every view is still a contradiction. So is one fact stated in two places
   with two values: a box, an envelope, a move's angle or a position given
   in the prose, a requirement row, an Interface text or the block
   (`envelope_mm`, `extents_mm`, Interface poses) that do not agree. Quote
   both.
   Under a heading "Placement", list every detail you model on another
   detail or on a curved host that breaks the print-details placement rules:
   a host narrower than the detail plus 0.5 mm on each side, a raised detail
   standing less than 0.5 mm above a concave host anywhere across the curve,
   or copies in a row closer than 0.5 mm.
4. **Print gates.** Run Make's own print gates, the code a Make round runs,
   with this one command from the repository root:

   ```
   uv run python src/workshop/make/skills/make-round/scripts/make_round <OUT> --print-gates-only --nozzle <NOZZLE> --overhang-angle 45 --contract <CONTRACT>
   ```

   It builds every `part_` entry and gates it as Make does: `check_mesh`,
   `check_overhang` and `check_thickness`, a kit Component Part by Part from
   its `print_parts()`. It prints a `wall`, `over` and `mesh` line per part
   (per Part of a kit: `cabinet/B04-top-board`), each failure with the
   region it names. It also runs two checks final verification runs, so a
   Proof that passes here cannot fail them in the build: `datum`, check_fit
   on the print stance (the bottom at Z 0, the bed footprint), and `posed`,
   `inspect validate` on the Component placed by `assembly_pose(gen_step(),
   None)`, since a solid valid as printed can self-intersect in the Display
   Pose. Both are your modelling: fix them. It exits 1 on any failure and
   writes only inside `<OUT>`, its reports under
   `<OUT>/measure/print-gates/`. `seal_proof.py` refuses a Proof without a
   passing run of every Component over its current sources. Never run the
   CAD skill's `check_` scripts yourself: only this command measures what
   Make measures. A `parts FAIL` line is your modelling, not the contract's: fix
   `print_parts()` and run it again. Add every gate failure to
   `FINDINGS.md` under a heading of its own: the part (and Part), the gate,
   the region it names. A failure forced by a contract value stays a finding,
   with the contract words that put the material there: never change the
   model to pass it. A failure on your own shape is repaired in make.md's
   overhang order and listed under "Shape repairs" (the part, the gate, what
   you changed), which the Proof Critic reads. When a gate failure, a
   function or mechanism the contract states, or the spec's cost cap stops
   you building a `CONCEPT-CHECKLIST.md` trait as drawn, list it under
   "Trait at risk": the trait id, the cause, and the smallest change that
   makes it. Never drop or change the trait yourself: the owner decides. Also list, under "At the limit", every wall,
   web, land, relief or cut the contract sizes exactly at its print minimum
   (a 0.80 web at a 0.8 minimum): it can pass here and fail in Make, whose
   model of it differs in detail and can be measured on a coarser grid (the
   cabinet pilot's 0.80 notch web read 0.66). List there too every
   down-facing face the contract designs to rise between 45 and 52 degrees
   from the bed (a 45 degree chamfer under a ledge): the gate fails below
   45, and a face designed that close lands past it once tessellated; 52 is
   the print-details library's design margin (`_DESIGN_MARGIN`). The
   designer gives each one margin.

## Final verification inputs

A seeded build runs final verification on your project as it is, so write
what it reads, as Make would, and keep it true to the model after every
change:

- `<OUT>/<toy_name>_spec.md`, exactly one, filled from
  `src/workshop/make/skills/image-to-cad/templates/build_spec.md` as that
  skill's `## Output` says (this is the spec, not Step 8's likeness gate);
- `<OUT>/measure/check_spec.py` and `<OUT>/measure/check_landmarks.py`, the
  two local audits `src/workshop/make/skills/cad/references/image-derived-verification.md`
  defines;
- `<OUT>/measure/check_fit.py`, the project fit audit `check_fit` asks for
  (seal_proof needs it even for one part): each mating pair from one base dimension
  with its clearance applied once, every connector named in the spec, and an
  assembly order that can be done.

Run each audit with `uv run python` and the CAD skill's `check_spec_format`
and `check_spec_numbers` on `<OUT>`; each must exit 0. `seal_proof.py`
refuses a Proof without them, and the seed carries them into the build.

## Seed inputs

A seeded build runs every check as one host batch (ADR 0098) and authors
nothing, so the Proof writes every input those checks read. `seal_proof.py
inputs <OUT> --contract CONTRACT.md` lists the ones this contract needs and
which are missing:

- `<OUT>/SEED-PRODUCT.json`, always: `{"schema_version": 1, "kind":
  "workshop-seed-product", "title", "summary", "concept", "research"}`. The
  title is the toy's name; the summary is shop copy the owner reads at
  Stage 4, with no Workshop vocabulary (make.md's `product.json` rule). The
  `concept` has exactly `title`, `summary`, `interaction`, `envelope_mm`,
  `mechanisms` and `components`, describing this Proof; `research` is the
  design's research notes. The build's Spark source is composed from them,
  so the motion review's concept hash is this concept's. The Make finalizer
  checks this concept, and so does the seal: exactly one component has
  `signature: true`, no `form`, `duty`, `placement` or `interfaces` hedges a
  number ("about 18 across" is refused; write "18 mm across"), every
  component mates with another or is named by `interaction`, and no
  component is larger than `envelope_mm`;
- `<OUT>/snap/iso.png` and `<OUT>/snap/signature.png`, the renders the
  owner approves;
- for a contract with a Coupled Interface: `<OUT>/measure/motion.json`
  passing `check_motion`, then `motion_presentation.py <OUT>`'s
  `snap/motion.gif` and `snap/MOTION-EVIDENCE.json`; the Proof Critic
  writes `snap/MOTION-REVIEW.json` from them (motion-review-v1), naming
  itself as `reviewer` (never `the owner (Approved Proof)`, the carried
  assembly review's name), 1 to 4 `review_rounds`, the concept hash of
  `SEED-PRODUCT.json`'s `concept` and the evidence file's sha256;
- for a schema 10 contract with an `electrical` section:
  `<OUT>/measure/power.json` passing `check_power`, `<OUT>/measure/mounts.json`
  passing `check_mount` (with its STEPs under `ref/`), and
  `<OUT>/measure/bought-placements.json` passing `bought_model.py --build`.

Change nothing outside `<OUT>`, and never edit the contract or an image.
Reply with the number of guesses, contradictions, print-gate failures,
refused details, wiki citations and shape repairs, and the path of every
entry you wrote.

When you are sent an amended contract, an edited image or the Proof Critic's
differences later, read the contract again whole, update the model to it,
rebuild, and rewrite `GUESSES.md` and `FINDINGS.md` from scratch: a guess the
amendment closed leaves the list.
