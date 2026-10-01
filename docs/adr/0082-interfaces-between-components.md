# ADR 0082: Interfaces between Components

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-10-01
- Owners: the Design Contract (`wish/design_contract.py`,
  `.claude/skills/build-a-toy/CONTRACT-FORMAT.md`, `design-a-toy`), the
  `make-round` skill and its `check_envelope` tool, the make_round guard
  (`make/make_round_guard.py`), the final verifier's Contract Mode gate
  (`cad/scripts/verify_project`), the Make finalizer and the host receipt,
  product-run Make instructions (`references/make.md`), the Component Worker
  definition (`src/workshop/make/agents/component-worker.toml`)
- Amends: ADR 0080 (what the root writes before spawning workers, and how
  long a worker lives) and ADR 0081 (a third unlock reason)
- Issue: #78 (spec C of the series begun in #76)

## Context

Components are built in isolation, but they meet: pegs go into sockets, a
pinion drives a sector, wings swing past a housing. In Broken God attempt 11
(`wish-20260930-201412-e8f60ec7`) the Workshop Manager handled every meeting
by writing shared files, and that became the run's biggest cost.

1. About 60% of the root's active time went into shared files (about 64 of
   76 minutes in the first session, about 33 of 80 in the resume).
2. The shared files mixed code two Components had to agree on (joint values,
   peg and socket sections, the gear mesh) with one Component's own geometry:
   a 234-line housing interior used by the housing only, the wing's outline,
   per-part print stances and dimensions.
3. Four bugs in shared code blocked workers: a crashing peg helper, a peg
   section trimmed flat, a wing boss with no backing, and two overhang
   blockers that needed new shared parameters. The housing worker started
   about 37 active minutes after the others.
4. Shared code was edited while workers ran: two rerun broadcasts, and about
   11-16 of the 111 rounds came from shared changes alone.
5. The housing cut its wing clearance from the wing's real outline, so every
   wing repair changed the housing.
6. No transcript consulted the design wiki, and the gear profile was
   hand-written instead of taken from the gear libraries the CAD skill ships.
7. Interactions were checked only on the assembled object, after every
   Component had passed, so a gear-mesh or swept-clearance problem surfaced
   at the very end.

## Decision

1. **Interfaces in the contract.** Design Contract schema 2 adds a required
   `interfaces` list. Each Interface has an `id`, an **Interface Kind**
   (`static`, `separable` or `coupled`) and the two or more Unique Geometry
   ids it joins. A separable Interface carries a **Keep-out Envelope**:
   `inside` and `outside` Components and `shapes`, each a pose name with one
   `box` (`min_mm`, `max_mm`) or `cylinder` (`base_mm`, `axis`, `radius_mm`,
   `height_mm`) in assembly coordinates, one per declared pose or a single
   static one. A coupled Interface names its `yielding` Component and either
   `poses` (`steps` and `movers` in check_motion's form, each naming its
   `component`) or `poses_from`, the id of a `coupled_motion_collision`
   condition in the project's `measure/motion.json`. The validator refuses
   every missing or foreign field at once; schema 1 contracts stay valid and
   may not carry `interfaces`. Contract Mode seals the section with the Wish.
2. **Shared Helper rules.** A Shared Helper holds only what two or more
   Components must agree on: Interface values, joint sections and standard
   profiles. Each value names the wiki page it came from and carries the
   page's assert; gears and standard elements come from `stdpart`
   (`bd_warehouse`, `py_gearworks`). A Component's geometry, print stance and
   dimensions stay in its own file. Component Workers never edit one.
   `--shared-helpers` checks these rules mechanically, before it builds a
   sample, on every Shared Helper a Component or sample imports: each design
   value (a module-level UPPER_CASE name bound to a number or a tuple of
   numbers) cites `# wiki: <slug>` on its line or in the comment lines
   directly above, the page exists in the run's wiki, and the value appears
   in an `assert` of the module; a value derived from cited values needs no
   citation. A function or class named for a standard element (gear, pinion,
   rack, bearing, screw, bolt, nut, washer, thread...) needs `bd_warehouse` or
   `py_gearworks`, and no helper names an involute. A failure builds and
   freezes nothing. The installed print-details library,
   `features/print_details.py`, is a Shared Helper: a project `.py` module
   that Components import, so it is frozen with the others and bound into
   the packets of the Components that import it. It is a standard element
   like a `stdpart` gear, not a design value, so it is exempt from the
   citation rule while its bytes are the library's, and an edited copy is
   refused.
3. **Shared Helper check and freeze.** The Workshop Manager writes samples
   under `samples/<name>.step.py` (a peg in its socket, a pinion on its
   sector) that import the Shared Helpers, and runs `make_round <cad>
   --shared-helpers`. It builds each sample with the project on
   `PYTHONPATH` and runs `check_thickness` and `check_overhang` on it; a
   sample that imports no Shared Helper fails. A pass writes
   `measure/shared-helpers-freeze.json` with the sha256 of every Shared
   Helper (each project `.py` module that is not an entry, a sample or
   evidence) and appends the event, with what changed since the previous
   freeze and the Components importing each changed file, to
   `measure/shared-helper-freezes.jsonl`. A failure freezes nothing. When
   the sealed contract has an Interfaces section, a component round before
   the freeze exits 2 and writes nothing. After it, every component round
   compares the Shared Helpers it imports with the freeze and reports each
   change with every Component that imports it (`helper_freeze`). That is
   detection, not a block: ADR 0081's import-scoped unlock acts on the
   change, and rerunning the check re-freezes.
4. **Keep-out Envelope check.** In a component round, for each separable
   Interface the Component joins, `make-round/scripts/check_envelope` places
   the Component through its entry's `assembly_pose(shape, pose)`. Inside:
   in every declared pose, no material lies outside that pose's shape.
   Outside: at its assembly placement (`pose` None), no material lies inside
   any shape. Both are B-rep Boolean volumes with a residue tolerance. A
   failure fails the round's checks like a print gate, so the round is not
   rendered. Neither side reads the other's geometry.
5. **Interface check.** `make_round <cad> --interface <id>` reads the sealed
   Interface and refuses (exit 2, nothing written) anything but a coupled
   one, and any Interface whose Components are not all locked at their
   current identity (built now). It writes a generated entry that places
   only those Components through `assembly_pose(shape, None)`, labelled by
   Component id, and one `coupled_motion_collision` condition from the pose
   table, with the non-moving Components as its obstacles, then runs
   `check_motion`. The round lives under
   `measure/interface-rounds/<id>/rNNNN`. A failure records an unlock for the
   yielding Component, `{"kind": "interface", "interface", "interface_round",
   "evidence", "reason"}`, with the motion detail, conditions and the log's
   hash as its repair input, through the same policy state and ledger as an
   assembly unlock. Rounds after it are admitted and are never Shape Rounds;
   a different B-rep returns to awaiting review.
6. **Assembly and final verification.** A check is current only while every
   Component it joins has the identity it was checked at. With
   `--require-component-passes`, an assembly round also requires a current
   passing check of every Coupled Interface. The final verifier applies the
   same rule in Contract Mode and writes the Interfaces, each with its Kind,
   Components and proof (`shared-helper-samples`, `keep-out-envelope`, or a
   coupled `pass` with its round), into `component-acceptance.json`. The Make
   finalizer requires that list to name every sealed Interface and copies it
   into `product.json`; the host validates it into the Make receipt, and the
   run report prints one line per Interface.
7. **Roles.** The make_round guard admits `--shared-helpers` and
   `--interface` only from the root, as it does the record calls, and never
   issues a worker nonce for a call that carries either.
8. **Worker lifetime.** The Manager keeps each Component Worker thread until
   the assembly passes and sends every unlock (Shared Helper, Interface or
   assembly) to that thread.

## Consequences

- The Manager's shared code shrinks to what Interfaces need, and is proven
  on samples before any worker builds on it. A broken peg helper fails one
  sample instead of blocking a worker.
- A clearance between two Components is a fixed shape both sides check
  against, so a wing repair no longer changes the housing.
- A gear mesh or swept clearance fails on its two locked Components, before
  assembly, and goes to one named Component with concrete evidence.
- An envelope is sufficient, not necessary. Two Components may enter each
  other's envelope and still work, which is why the contract classifies each
  Interface; the assembly motion check stays the final word for every Kind.
- A Component that joins a separable or coupled Interface must define
  `assembly_pose`. Its placement is the Component's own code, so a wrong
  placement passes its envelope and fails at assembly instead.
- The coupled check proves a necessary geometric condition only, as
  `check_motion` documents: not sustained contact or force transmission.
- The Shared Helper rules are checked by name and syntax, not meaning: a
  citation proves a page exists and an assert names the value, not that the
  assert is the page's own or that a standard element is not hand-built under
  another name.

## Compatibility and migration

Runs created before this change keep their materialized `make_round`, guard,
finalizer and instructions, including on resume. A contract without an
Interfaces section (schema 1, or any older sealed contract) keeps the
protocol without a freeze, envelopes or interface checks. Only new schema 2
contracts get the new rules; `design-a-toy` writes schema 2.

## Verification

Contract tests cover a complete section, a kinematic source in place of a
pose table, an empty section, schema 1 without it, and the refusal of each
missing or foreign field. The `make_round` tests, with fake build, gates,
envelope and motion tools, cover the freeze and its hashes, a failing
sample, a sample importing nothing, the Shared Helper rules (an uncited,
unasserted or unknown-page value, a citation above a value, a derived value,
a hand-written gear or involute, an unimported helper, and the print-details
library exempt only byte for byte), a component round before the freeze, a
contract without the section, a changed helper reported with its importers
only, the re-freeze event, inside and outside envelope failures, a
compliant pair, an inside change that leaves the outside pass current, the
interface check refused while a participant is unlocked, a pass on just its
Components, a failure unlocking only the yielding Component with evidence
and without a Shape Round, a stale result, and assembly refusals for a
missing, failing and stale check. Guard, verifier, finalizer, host and CLI
tests cover the root-only modes and the report chain. `check_envelope` and
`--interface` were also run against real build123d parts and `check_motion`.
A Broken God rerun after specs A-C, measuring root time in shared files,
blocked worker time, rounds caused by shared changes and Interface failures
found before assembly, needs the owner's go-ahead.

## Rejected alternatives

- **Check every meeting on the assembled object only.** That is the status
  quo that surfaced the gear mesh last.
- **Let one side read the other's real outline.** It couples every repair of
  one Component to the other, as the housing and wing showed.
- **Block edits to frozen Shared Helpers.** A necessary change would then
  need an escape hatch; detection with an import-scoped unlock and an
  explicit re-freeze records the change without one.
- **Derive Interfaces from geometry.** Out of scope; the contract names them
  before any geometry exists.
