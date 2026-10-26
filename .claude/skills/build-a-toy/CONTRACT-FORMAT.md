# The Design Contract file

A Design Contract is one Markdown file, `CONTRACT.md`, kept in the same
directory as its reference images. It has two parts:

1. **Prose.** The full spec that `design-a-toy` Stage 1 wrote, reconciled with
   the reference images the person approved. The Make agent reads it for
   intent. From schema 8 (ADR 0093) the prose is split into one `###`
   section per Component or Part, and each Component's Worker receives the
   sections its geometry names (`prose_sections`, below).
2. **One fenced `design-contract` block.** The checkable enumeration of that
   same spec. This skill checks conformance against the block.

This is the exact format `workshop wish --contract` and `workshop fix
--contract` seal: the whole file becomes the Wish objective, byte for byte
(ADR 0072). Keep the whole file under **40,000 characters**. A correction
brief is itself a Wish objective, which is limited to 50,000 characters, and
does not need to repeat the contract, since `fix --contract` seals it
separately from the brief.

The block must cover the prose. If the prose decides something checkable, such
as a dimension, a count, a wall thickness or a visible feature, and the block
does not carry it, the contract is incomplete. Complete it and get it
re-approved before any run starts. A block that leaves something out
recreates the defect this skill exists to remove.

## Print minimums in the prose

The prose states no print minimum of its own. Every minimum is the
print-details library's `limits()` at the contract's nozzle, the numbers Make
builds detail with and the Component Reviewer judges by: at a 0.4 mm nozzle a
rivet, boss or dome is at least 2.0 mm across, a raised band, rim or rib
0.9 mm, a wall or land 0.8 mm, a groove or gap 0.5 mm. `design-a-toy` Stage
3c lists them all. The print section carries two rules, word for word:

- "Every point, chisel, keel and V underside ends in a flat land at least
  0.8 mm across (one print minimum at a 0.4 mm nozzle)." The 0.8 mm is the
  nozzle's print minimum, never a geometry's `wall_min_mm`.
- "A drawn detail under the print minimums is enlarged to the minimum; when
  the enlarged detail does not fit its spot, it is left out, and this
  contract names it."

Every detail left out is named in a `requirements[]` row of its Component
("The brow band is a plain raised band and carries no rivets"): the
Component Reviewer reads that Component's rows and Interface text, not the
prose, even under schema 8, where the Component Worker reads its prose
sections too. Never write that a detail is "never left out", and never state a
smaller minimum, such as "every rivet at least 1.0 mm across".

## The block

````markdown
```design-contract
{
  "schema_version": 4,
  "title": "Antisol",
  "inventor": "ad-astra",
  "envelope_mm": [200, 200, 60],
  "references": [
    {"file": "ref-01-antisol.png", "shows": "assembly", "camera": [-60, 30]},
    {"file": "ref-02-world-disc.png", "shows": "geometry:world-disc", "camera": [-90, 75]}
  ],
  "geometries": [
    {"id": "world-disc", "name": "Planet disc", "count": 16,
     "extents_mm": [30, 30, 6], "wall_min_mm": 1.2}
  ],
  "requirements": [
    {"id": "R01", "scope": "assembly",
     "text": "The sun den is the focal point at 35 degrees azimuth, 22 elevation."},
    {"id": "R02", "scope": "geometry:world-disc",
     "text": "Each disc carries one raised equatorial band."}
  ],
  "interfaces": [
    {"id": "disc-peg", "kind": "static", "components": ["world-disc", "base"],
     "text": "Each disc's flat underside carries a 4 mm peg, 6 mm long, at its centre; the base has a 4.2 x 6 socket under each disc."},
    {"id": "disc-swing", "kind": "separable", "components": ["world-disc", "base"],
     "text": "Each disc swings inside a 34 mm radius drum above the base; the base keeps that drum clear.",
     "envelope": {"inside": "world-disc", "outside": "base", "shapes": [
       {"pose": "rest", "cylinder": {"base_mm": [0, 0, 20], "axis": [0, 0, 1],
                                     "radius_mm": 34, "height_mm": 8}}]}},
    {"id": "sun-drive", "kind": "coupled", "components": ["sun-gear", "world-disc"],
     "text": "The sun gear's rim teeth mesh with a toothed rim on each disc's edge.",
     "yielding": "world-disc",
     "poses": {"steps": 10, "movers": [
       {"component": "sun-gear", "rotation": {"axis_point": [0, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 36}},
       {"component": "world-disc", "driven": true, "rotation": {"axis_point": [40, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -72}}]}},
    {"id": "disc-pair-mesh", "kind": "coupled", "components": ["world-disc#1", "world-disc#2"],
     "text": "The first two discs' rim teeth mesh with each other.",
     "yielding": "world-disc#2",
     "poses": {"steps": 8, "movers": [
       {"component": "world-disc#1", "rotation": {"axis_point": [40, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 30}},
       {"component": "world-disc#2", "driven": true, "rotation": {"axis_point": [72, 0, 0],
        "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": -30}}]}}
  ]
}
```
````

(The example abridges `geometries[]`; every id an Interface names must be a
Unique Geometry. `world-disc#1` and `world-disc#2` are two of its 16
instances.)

## Field rules

- **JSON, not YAML.** The host must parse it deterministically with the
  standard library.
- `title`: the toy's name, without a revision suffix. The loop adds
  suffixes such as `v01`.
- `inventor`: an id from `inventors/`, passed to `--inventor`.
- `envelope_mm` and `extents_mm`: three positive numbers in millimetres, in any
  order. They are compared sorted, because Make chooses the axes. The
  tolerance is fixed at ±0.05 mm and is not a field: it describes the
  measuring instrument, not the design.
- `references[].file`: named `ref-NN-<slug>.png`, `.jpg` or `.webp`,
  numbered from `01` without gaps, each at most 800x800 pixels and 12 MiB,
  with one subject fully inside the frame. These are `design-a-toy`'s rules.
  `shows` is `assembly` or `geometry:<id>`. Pass every one of these files to
  `--ref` under these names and in this order: `wish --contract` and
  `fix --contract` refuse missing images and images that would seal under any
  other name, because Make finds an image's label by its name.
- `references[].camera` (ADR 0083): the reference's **Reference Camera**,
  `[AZ, EL]` in degrees, in the Display Pose (assembly) frame, assembly
  reference included. AZ is in -180..180 and EL in -90..90, in
  `render_review`'s convention: AZ 0 looks from +X, -90 from the front (-Y),
  90 from the back, 180 from the left; EL 0 is level and 90 looks straight
  down. design-a-toy estimates it by eye, rounded to 15 degrees. Make renders
  each Component placed by its `assembly_pose(shape, None)` from this camera
  beside its reference, so a wrong camera shows the wrong side of the model.
  Required from schema 3 and refused before it.
- `guides[]` (schema 5, ADR 0089): the contract's **Guide Images**, pictures
  that explain the design, such as a colour-coded transformation step sheet
  or a part seen from more sides. Each is `{"file": "guide-NN-<slug>.png",
  "shows": "<what it explains, at most 500 characters>", "steps": ["<each
  step it draws, in order>", ...], "geometries": ["<geometry id>", ...]}`,
  numbered from `01` without gaps, at
  most 2048 pixels a side and 12 MiB, any number of panels. `steps` is optional,
  1 to 24 distinct lines of at most 300 characters; for a transformation
  sheet, write the Transformation section's moves in the order the sheet
  draws them. `geometries` is optional: a non-empty list of distinct
  `geometries[]` ids whose Component Workers read the guide (issue #125).
  Without it every Component Worker reads it; give a sheet that shows one
  part `geometries: ["<that id>"]`. Pass every file to `--guide` under these
  names and in this order, after the `--ref` images. A Guide Image is never
  compared with the model: the Workshop Manager reads every one, each
  Component Worker reads those for its Component, the Component Reviewer
  never sees one, and the contract wins wherever it disagrees. With
  `--check-motion true` the run must account for every step of every guide.
  Required at schema 8 (ADR 0093 decision 5), where every Unique Geometry is
  named in at least one guide's `geometries`: each Component's image is a
  three-view sheet whose first view is its Reference Image and whose other
  two are its Guide Images. A guide without `geometries` counts for no
  geometry. `wish --contract` refuses a schema 8 contract with a geometry no
  guide names.
- `print` (schema 6, ADR 0091): the toy's **Print Sheets**, everything the
  maker prints on A4 and ships for the buyer to cut out with scissors, fold
  and apply. It is `{"stocks": {...}, "art": [...], "pieces": [...]}`:
  - `stocks`: each stock the pieces are cut from, `paper`, `sticker`, `card`
    or `film`, as `{"name": "<what the print shop sells>", "caliper_mm":
    <thickness>}`, 0.03 to 1.0 mm. Defaults: `paper` matte couche 120 gsm
    0.10, `sticker` paper decal 0.15, `card` Ivory 300 gsm 0.45, `film` laser
    OHP film 100 µm 0.10. Declare only stocks some piece uses.
  - `art[]`: `{"file": "print-NN-<slug>.png", "shows": "<at most 500
    characters>"}`, numbered from `01` without gaps; stock art adds `"source":
    "<http(s) link>", "licence": "CC0-1.0"` (CC0 only). Every art file is
    used by at least one piece; one file may serve several. Pass every file
    to `--print-art` under these names and in this order, after the `--guide`
    images. Print art is never compared with the model as a likeness target.
  - `pieces[]`: `{"id", "art", "stock", "way", "on", "where", ...}`. `id` is
    lowercase kebab case and unique; `on` is the Unique Geometry it lands on,
    or one instance `<id>#<n>`. In schema 7 (ADR 0092) a piece is a Part:
    `id` is `M01-<mnemonic>` or `N01-<mnemonic>` and `on` names a printed
    Part, a Bought Part or a step's Sub-assembly in `assembly_tree`. `where` says which face, block, sphere or
    slot (at most 300 characters); optional `count` (1 to 99) is how many
    copies are printed. `way` and its sizes, all in mm, the contract's
    sizes being the truth the model must match within ±0.5 mm:

    | `way` | Stock | Sizes |
    |---|---|---|
    | `flat` (into a recess about 0.4 mm deep) | `paper` or `film` | `size_mm: [w, h]`, optional `outline` `rect`/`oval` |
    | `sticker` (into a recess) | `sticker` | `size_mm`, optional `outline` |
    | `wrap` round a block | `paper` | `block_mm: [height, width, depth]`, `around`: `cover` (front, spine, back) or `band` (all four sides) |
    | `sphere`, one strip of joined gores | `paper` | `diameter_mm` ≥ 25, `gores` 8 to 24 |
    | `fold`, accordion pages | `paper` | `page_mm: [w, h]`, `pages` 2 to 32 |
    | `stand`, a card in a slot | `card` | `size_mm`, optional `outline`, `slot_mm` (≤ the card's width) |

    Scissors rules: every cut edge is at least 5 mm (a `wrap`'s height, a
    `fold`'s page, a flat or standing piece's sides); small shelf books are
    one spine strip, never one piece each.
- `assembly_tree` (schema 7, ADR 0092): the toy as a Rolife-style kit, the
  **Assembly Tree** its Manual is written from. Its leaves are the Parts the
  buyer handles, every inner node is an Assembly Step, and the last step is
  the finished toy. It is `{"panel_mm": <mm>, "parts": [...], "steps":
  [...], "components": [...], "checks": [...], "materials": [...]}`. Make writes the kit's
  Manual from it (ADR 0092 decision 9), using only this section's words:
  - Every id is a code plus a kebab-case mnemonic, and no code or mnemonic
    repeats anywhere in the tree or the Print Pieces.
  - `panel_mm` (optional, default 2.0, from 0.8 to 10): the toy's one
    standard panel thickness, five 0.4 mm lines by default (owner decision
    Q34, 2026-10-26).
  - `parts[]`: a printed Part is `{"id": "A03-hat", "name": "<at most 80
    characters>", "filament": "<filament id>", "form": "panel" | "solid"}`
    (owner decision Q33, 2026-10-26). Furniture, boxes, the shell and frames
    are built from flat **Panels** joined by tab and slot, each `panel`;
    small round or 3D props (an inkwell, a ring pull, a crystal ball, a hat)
    are `solid`, printed whole. A panel is `panel_mm` thick; one of another
    thickness adds `"thickness_mm"` and a `"thickness_reason"` (at most 300
    characters), which `contract_lint.py` lists for a verdict. A solid takes
    neither. A panel is one filament colour: relief (a door's arch moulding,
    a frame) prints on its face, and texture and colour go on Print Pieces
    (Q37). The tab-slot clearance is no contract field: it is the printer's
    `TAB_SLOT_CLEARANCE` in `print-details` (Q35, an estimate). Its letter groups Parts by
    colour: any letter except M and N (Print Pieces), P (Bought Parts) and S
    (steps), one letter per filament and one filament per letter. A Bought Part is
    `{"id": "P02-steel-pin", "bought": "<Bought Part id>"}`. Both ids come
    from the owner's catalogues, `src/workshop/wish/catalogues/filaments.json`
    and `bought-parts.json`. A colour or Bought Part outside them is refused:
    the owner approves one by adding it to the catalogue. No filament may be
    the reserved magenta `#ff00ff`: it marks Bought Parts, which every STEP
    and render shows in it as bought, not printed (ADR 0092 decision 5,
    owner decision Q29). Tools and
    consumables (tweezers, foam tape and dots, glue, a screwdriver) are never
    Parts; they go in `materials`.
  - `steps[]`, in Manual order with rising numbers, each `{"id":
    "S07-teacher-desk-items", "output": "<the Sub-assembly's name, at most 80
    characters>", "count": <how many times it is made per toy>, "joint":
    "<kind>", "inputs": [...], "text": "<one short English instruction, at
    most 200 characters>"}`, optionally `"error_prone": true` (the Manual
    adds a correct/incorrect picture) and `"leads"`. The Sub-assembly takes
    the step's id. Each input is `{"id": "<Part, Print Piece or earlier
    step>", "direction": [x, y, z], "count": n}`; `count` (default 1) is how
    many one making of the step takes, and a step's `count` equals its parent
    step's count times that. The finished toy is made once. `joint` is one
    of:

    | `joint` | What the step does | Inputs |
    |---|---|---|
    | `peg-socket`, `tab-slot`, `pin-hinge`, `foam-tape` | joins its inputs | two or more |
    | `glue` | joins them, as a last resort, with `glue_reason` | two or more |
    | `paper` | applies Print Pieces to their host | two or more |
    | `fold`, `cut`, `bend`, `roll` | reshapes one input | exactly one |
    | `leads` | joins the LED leads of `lamps` | one or more |

    In a joining or `paper` step the first input is what the others go into
    and takes no `direction`; every later input has its one straight
    insertion `direction`, in the assembly frame. A reshaping or `leads` step
    takes none. A `leads` step lists `lamps`, Bought Parts whose catalogue
    category is `lamp`, each already in its Sub-assembly: it sits at or above
    the smallest Sub-assembly holding every lamp it joins. A step that
    encloses a lead declares it in `leads`: `{"lamp": "<lamp Part>",
    "route_mm": [[x, y, z], ...], "exit": "<where it comes out>"}`, two or
    more points in the assembly frame.
  - Every Part and every Print Piece is the input of exactly one step, and
    every step but the last feeds exactly one later step. A Print Piece is
    applied in the first `paper` step above it that joins, once its host is
    in that Sub-assembly, and its `count` equals how many times the tree
    applies it.
  - `components[]`: `{"geometry": "<Unique Geometry id>", "parts": [<its
    printed and Bought Parts>]}`, exactly one per Unique Geometry. Every
    printed and Bought Part belongs to exactly one Component, and a
    Component's Parts are exactly the printed and Bought Parts of one
    subtree, made as many times per toy as the geometry's `count`. A Print
    Piece belongs to the Component whose subtree applies it; one applied
    above every Component belongs to the join. Make's `paper` gate checks a
    piece where its host is (ADR 0092 decision 8): a piece on a printed Part,
    or on a Sub-assembly inside one Component, in that Component's round;
    one on a Sub-assembly across Components in assembly rounds, carried by
    exactly one of their parts; one on a Bought Part has no printed feature.
    Steps above the Components join Components and stay recorded as
    Interfaces. In Make each printed Part is one solid labelled with its id
    in its filament's colour, and each Bought Part one labelled body in
    `#ff00ff` (`make-round/SKILL.md`, "The kit's Assembly Tree"). Final
    verification lists every Bought Part body with its catalogue id in
    `measure/not-printed.json`, which ships beside the STEP files. A body
    that does not match the tree is a labelling slip the run repairs; a
    tree that does not hold together stops the run (ADR 0092 decision 10,
    Q28).
  - `checks`: the Check Steps the Manual shows first, outside the tree:
    `{"id": "light-test", "text": "<one short English instruction>",
    "parts": [<lamp and power Bought Parts>]}`, each naming at least one lamp
    and one power source; the id is a kebab-case mnemonic no other id uses.
    A tree with a lamp tests every lamp in one; otherwise `checks` is left
    out.
  - `materials`: the tools and consumables the Manual lists, catalogue ids
    whose category is `tool` or `consumable`. The Manual adds a screwdriver
    by itself when a Bought Part is a screw or a power source.

  A box closes with each panel entering alone: the last panel slides in
  along grooves, so no step needs two inputs to move together (Q36).

  An abridged cabinet, one Component of five Parts with a spine strip and a
  pin hinge, placed in the case (a real flat-pack cabinet is about six panel
  Parts plus its props):

  ```json
  "assembly_tree": {
    "parts": [
      {"id": "B01-cabinet-carcass", "name": "Cabinet carcass", "filament": "dark-oak", "form": "panel"},
      {"id": "B02-cabinet-door", "name": "Cabinet door", "filament": "dark-oak", "form": "panel"},
      {"id": "D01-inkwell", "name": "Inkwell", "filament": "dark-blue", "form": "solid"},
      {"id": "P01-hinge-pin", "bought": "steel-pin-1.5x29.5"},
      {"id": "P02-jar", "bought": "clear-jar-6x7"}
    ],
    "steps": [
      {"id": "S01-cabinet-shelf", "output": "Cabinet with jar and inkwell", "count": 1,
       "joint": "peg-socket", "text": "Press the jar and the inkwell onto the upper shelf.",
       "inputs": [{"id": "B01-cabinet-carcass"}, {"id": "P02-jar", "direction": [0, 1, 0]},
                  {"id": "D01-inkwell", "direction": [0, 1, 0]}]},
      {"id": "S02-cabinet-spines", "output": "Cabinet with book spines", "count": 1,
       "joint": "paper", "text": "Lay the spine strip in the lower shelf's recess.",
       "inputs": [{"id": "S01-cabinet-shelf"}, {"id": "M01-spine-strip", "direction": [0, 1, 0]}]},
      {"id": "S03-hang-door", "output": "Cabinet", "count": 1, "joint": "pin-hinge",
       "error_prone": true, "text": "Set the door between the lugs and push the pin down.",
       "inputs": [{"id": "S02-cabinet-spines"}, {"id": "B02-cabinet-door", "direction": [1, 0, 0]},
                  {"id": "P01-hinge-pin", "direction": [0, 0, -1]}]}
    ],
    "components": [
      {"geometry": "cabinet", "parts": ["B01-cabinet-carcass", "B02-cabinet-door",
                                        "D01-inkwell", "P01-hinge-pin", "P02-jar"]}
    ],
    "materials": ["tweezers"]
  }
  ```

  (Abridged: the case's Parts and Component, the step placing the cabinet in
  it, and `print.pieces` with `M01-spine-strip` on `B01-cabinet-carcass` are
  left out. `tests/wish/test_assembly_tree.py` holds a whole example.)
- `geometries[]`: one entry per **Unique Geometry**. `id` is lowercase kebab
  case. `count` is how many Components the toy has with this shape.
  `wall_min_mm` is the minimum wall.
- `geometries[].prose_sections` (schema 8, ADR 0093, required there and
  refused before it): a non-empty list of distinct heading texts, each
  exactly the text after `### ` of one level-3 heading in the prose, outside
  every fenced block. Each named heading must appear exactly once as a `###`
  heading and have text. One section may be named by several geometries
  ("Spine housing and heart core"). A section runs from the line after its
  heading to the next heading of level 1 to 3; `####` subheadings stay in
  it, and the design-contract block belongs to no section. `wish --contract`
  seals the named sections inside the contract as `prose`
  (`[{"heading", "text"}]`, in prose order), and each component round
  writes its Component's sections into its `summary.json` `contract`, for
  the Component Worker only. Rows win wherever a section and a row differ;
  the Component Reviewer never reads prose, so every visible claim the
  reviewer must judge still needs its row. An owner amendment on resume may
  change a section's text, never which sections exist or which geometry
  names them; an in-run Contract Amendment never changes prose.
- `schema_version`: `4` is schema 3 plus a `text` on every Interface (ADR
  0084). `5` is schema 4 plus a
  non-empty `guides[]` (ADR 0089).
  `6` is schema 5 plus the `print` section (ADR 0091), with `guides[]`
  optional. `7` is schema 6
  plus `assembly_tree` (ADR 0092), with `print` and `guides[]` optional and
  the Print Pieces' ids and hosts in the Part form above. Make's tree gates
  (ADR 0092 decision 8) check a schema 7 kit, and final verification writes
  its Manual (decision 9). `8` (ADR 0093) is schema 7 with `assembly_tree`
  optional, so it serves every new contract, kit or not: a kit carries its
  `assembly_tree` and gets the tree gates and Manual exactly as schema 7
  does, and a toy that is not a kit omits it and gets neither; `print` is
  optional as in schema 7, with Part ids and hosts only when the tree is
  there. Schema 8 adds two requirements: every geometry names its
  `prose_sections`, and `guides[]` is required with every geometry named in
  some guide's `geometries`. Use `8` for every new contract; 1 to 7 stay
  valid, with exactly their earlier rules, for contracts and runs sealed
  before it. Schema 3 is schema 2 plus a `camera` on every
  reference; from schema 3 every Component file defines
  `assembly_pose(shape, pose)`, even one in no Interface. A schema 3
  contract has no Interface text, a schema 2 contract no cameras and a
  schema 1 contract no `interfaces`; they stay valid only for runs sealed
  before them.
- `interfaces[]` (ADR 0082): one entry per place two or more Components meet;
  `[]` when none do. `id` is lowercase kebab case and unique. `kind` is
  `static`, `separable` or `coupled`. `components` lists two or more
  different Components. Each is a Unique Geometry id or, when that
  geometry's `count` is above 1, one instance of it written `<id>#<n>` with
  `n` from 1 to `count` (issue #80): `wing#1` and `wing#2` for two wings that
  meet each other, or `wing#1` alone where only the left wing meets
  `heart-core`. One Interface never names a geometry and an instance of it
  together. Every other field that names a Component (`inside`, `outside`,
  `yielding`, a mover's `component`) uses the same references as
  `components`. `text` (schema 4, required and non-empty, no length limit)
  states in words what the Interface imposes on each Component it joins:
  every joint feature it puts on each side (a peg, a socket, a plug, a seat
  face), with its size and place. Make writes it into each joined
  Component's review packet and round summary, so the Component Reviewer
  and the Component Worker read it from the sealed contract. No gate
  measures or scores it; Interface checks stay numeric.
  - A `separable` Interface has an `envelope`: `inside` and `outside`, two of
    its Components, and `shapes`, each a lowercase `pose` name with exactly
    one `box` (`min_mm`, `max_mm`, min below max) or `cylinder` (`base_mm`, a
    non-zero `axis`, positive `radius_mm` and `height_mm`), in assembly
    coordinates. One shape is a static envelope; several are one per pose,
    each pose named once.
  - A `coupled` Interface has `yielding`, one of its Components, and exactly
    one of `poses` (`steps`, a positive integer, and `movers`, each naming
    one of its `component`s once with a `rotation` and/or `translation` in
    `check_motion`'s form and an optional `driven`) or `poses_from`, the id
    of a `coupled_motion_collision` condition in the CAD project's
    `measure/motion.json` whose movers name Components by id.
  - A `static` Interface has nothing more. No Kind takes another Kind's
    fields.
- `requirements[]`: the visual requirements, meaning what a person would
  judge by looking. `id` is `R` followed by two digits (`R01`), or three
  from `R100`, unique. There is no limit on how many rows a contract or a
  Unique Geometry has (ADR 0093 decision 6): a kit writes one row per Part
  for what can be seen. `scope` is
  `assembly` or `geometry:<id>`. That is the requirement's Requirement Scope.
  Write the text as one observable claim. A number already carried by a
  geometry field is not repeated here.
  An `assembly` row states only what renders of the assembled toy in its
  Display Pose show, because the blind signature review needs visible
  evidence for it. Materials, print order, pauses, inserted parts and
  physical behaviour go in the prose, or in a geometry row a gate measures.
  A row or Interface `text` that puts several Components on one face, plane
  or level agrees with each one's `extents_mm` and every Interface range
  that places it, and a Component thinner or thicker than its neighbours
  states its thickness in its own row.

## Validation before any run

A contract is ready only when all of these hold. Report every failure at once.

- The block parses, and every field above is present and well formed.
- Every `id` is unique, and every `geometry:<id>` it cites exists.
- Every reference has a `camera` in range, and the person approved the
  cameras with the images.
- Every Interface has its Kind, two or more existing Components and its
  `text`, a separable one its envelope and a coupled one its yielding
  Component and poses. An instance `<id>#<n>` names a geometry whose `count` is above 1,
  with `n` in 1..`count`.
- Every Unique Geometry has at least one reference whose `shows` names it.
- Every reference file exists beside `CONTRACT.md` and meets the image rules.
- Every Guide Image file exists beside `CONTRACT.md`, the person approved it
  with the references, and its `steps` follow the Transformation section.
- Every assembly row states only what the assembled renders show, and
  every shared face agrees with the extents and Interface ranges of the
  Components it names.
- The prose carries the blunt-edge and detail rules above, states no
  minimum below the library's, and every detail left out has its row.
- For schema 7, every tree rule above holds, every printed Part is a
  `panel` or a `solid`, every panel off `panel_mm` states its reason, and
  `python3 .claude/skills/design-a-toy/scripts/contract_lint.py CONTRACT.md`
  reports no error. It runs the host's own parser and warns for each
  catalogue entry the owner has not confirmed.
- For schema 8, every geometry names its `prose_sections`, each one exactly
  one `###` heading with text, and every geometry is named in some guide's
  `geometries`.
- No row count is limited: ADR 0093 removed ADR 0072's guards of 16
  assembly-scoped rows and 4 per Unique Geometry.
- The whole file is at most 40,000 characters. Nothing in the host checks
  this number; it leaves room under the 50,000-character Wish objective
  limit, which `wish --contract` enforces on the whole file.
