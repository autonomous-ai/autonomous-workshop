# ADR 0096: The approved Contract Proof is the build, and Workshop certifies it

- Status: Proposed on 2026-11-02 from the owner's direction of the same day.
  Implemented on main and not yet run live: `proof_diff` (#189), the
  design-a-toy Proof prompts (#190), schema 11 and `seal_proof` (#191), the
  host `--seed-source` path with approval-locked rounds and the seed
  deviation check (#192), build-a-toy and DETECT (#193), and the assembly
  review carried from `CRITIC.json` (`make_round --carry-assembly-review`,
  signature review schema 10). Still migrating: the
  Approved Proof copy in the published archive. The plan is
  [docs/plans/0096-seeded-build-plan.md](../plans/0096-seeded-build-plan.md).
  The owner decided every open question on 2026-11-02 (see "Owner
  decisions" at the end).
- Date: 2026-11-02
- Amends: ADR 0072 (the sealed contract as the whole objective; for new
  contracts the approved Proof is the shape's source of truth), ADR 0093
  decision 1 (the Proof sees no image and closes every guess in the
  contract; "a Proof is never a Reference Image, and nothing compares it
  with the model"; the deferred "Proof's CAD source as Make's starting
  skeleton"), ADR 0094 decisions 3 and 4 (the kept Proof reader, the
  fresh contract-only read, and what DETECT compares), and for **seeded runs only** ADR 0075 (where the second
  reader lives), ADR 0076/0077/0080/0081 (Component Workers, the Component
  Reviewer and Shape Rounds) and the assembly blind review of ADRs
  0022/0023/0060.
- Relates to: ADR 0061 (Spark keeps Make's own verification), ADR 0063
  (print gates on the source), ADR 0065/0069 (a correction run starts from
  a source and carries unchanged parts by hash), ADR 0072 (every
  requirement carried), ADR 0082 (Interfaces), ADR 0085 (in-run
  amendments), ADR 0092 (kits), ADR 0095 (powered toys).

## Context

Since ADR 0094 the Contract Proof runs make_round's own print gates on a
project laid out as Make lays one out. Two builds have now been compared
with their Proofs (`toys-spec/_workflow/CONCEPT-DRIFT-standalone.html`,
2026-11-01, measured with OCP on the STEP files):

- **K4 turtle keycap set.** 9 of 9 Components of build v02 match the kept
  Proof to 0.01 mm³ in volume and 0.01 mm in size. The whole set's
  silhouette at ref-01's camera overlaps 99.97%. The only extra material
  is a hidden 9.4 mm³ pocket in the base.
- **NCH cabinet pilot.** 13 of 13 Parts match the Proof in size, volume
  within 0-0.8%.
- **The build adds nothing visible but colour.** What Make adds is
  evidence: motion, the final CAD gate, receipts and the STEP package.
- **Make spent 33.6 cost units on K4 v01** re-typing a model that already
  existed, mostly in component rounds and reviews.
- **The only drift Make caused came from an in-run Manager ruling.** On
  K4 v01 a ruling on a Blocked Report changed the Grumpy and Wink faces
  (ADR 0081's #97 rule then bound the reviewer to it). Fix v02 spent 18
  units, partly to bring the faces back to the Proof.
- **Drift from the concept enters in design, not in Make**
  (CONCEPT-DRIFT Part 2): printability choices taken one detail at a
  time, shapes the Inventor wrote for the mechanism or engraving, and
  references drawn from the contract. No step after Stage 1 compares
  anything with the Concept Image.

`toys-spec/_workflow/PROOF-COST-standalone.html` (2026-10-31) prices the
design side: a whole design costs 16-25 units, 45-65% of one build. A
first Proof build or a fresh read costs 0.7-1.7 units, an amendment to the
kept Proof 0.1-0.5. The coordinator, not the Proof, is 55-60% of design
cost.

On the beaver coaster's arms the owner ran the review this ADR proposes,
live: an independent critic compared the Proof with the references and
the concept, round after round, until it agreed, and only then did the
owner see it at Stage 4.

So the run's most expensive work reproduces geometry the owner has already
approved, and its in-run judgement is the one place that has moved a
build away from it.

## Decision

### 1. The Proof becomes the official build, reviewed in design

- **The kept Proof sees everything from round 1** (owner, 2026-11-02).
  - It receives the contract, the Reference Images, the Guide Images,
    the chosen Concept Image and its three views, and the Concept
    Checklist.
  - From round 2 it also receives each Stage 3a compare.
  - It models the shape to the images.
  - Nothing it takes from an image has to become contract text (see
    decision 1c).
  - There is no contract-only round.
- **A Proof Critic replaces the Component Reviewer and the blind review.**
  A fresh subagent that never wrote Proof code compares the Proof with
  each reference at its Reference Camera, with the concept at the concept's
  cameras, and with every requirement row. Rounds go on until it agrees.
  It judges as the Component Reviewer does: differences, Reference
  Conflicts (ADR 0084) and camera mismatch (ADR 0083).
- **One critic for the whole toy** (owner, 2026-11-02). One critic thread
  is kept for the whole design and reused, as ADR 0077 reuses a reviewer,
  so its cache survives. It judges every Component and the assembly from
  the compares.
- **A close look only when needed.** When the critic cannot settle a
  Component from the whole-toy compares, it asks for one (a small part,
  a hidden face, a detail below the compare's resolution). The
  coordinator then renders that Component alone at its Reference Camera
  and its Guide Image cameras, and the same critic thread judges it.
  It is not a second critic. `CRITIC.json` records each close look and
  why it was needed.
- **The critic holds a Concept Checklist** (owner, 2026-11-02;
  CONCEPT-DRIFT solution 1).
  - After the three views in Stage 1, a fresh subagent that sees only
    the concept and its three views writes `CONCEPT-CHECKLIST.md`:
    8-12 defining traits, each with one line and, where possible, a
    ratio measured on the image.
  - The owner marks each trait required or changeable.
  - The critic judges every trait on the Proof at the concept's cameras:
    kept, lost, or changed by a named owner decision.
  - A required trait that is lost is a difference, like any other.
  - Stage 4 opens with concept | Proof | 50% overlay and the
    checklist's count ("10 of 12 kept; the blush and the two-tone shell
    left out, by your choice").
- **A cap, then the owner.** After five rounds that changed the Proof's
  geometry, the critic's open differences go to Stage 4 as lines under
  their compares, for the owner to decide. Nothing is accepted silently,
  the same rule as ADR 0076's Component Acceptance, with the owner as the
  decider instead of the reviewer.
- **The critic writes a record.** `proof/CRITIC.json`: per round, per
  Component and for the assembly, the verdict, each difference, and the
  hashes of the Proof sources and compare images it judged. Its last round
  carries one verdict per requirement id, which is what ADR 0072 needs.
- **No fresh contract-only read** (owner, 2026-11-02). ADR 0094's
  fresh read existed to find contract silences that the kept Proof had
  filled from memory. Under decision 1c the contract no longer has to
  describe the shape, so a silence about shape is no longer a gap. The
  places a fresh read used to protect are now protected by the shape
  diff of decision 2b, which compares against the approved shape itself
  rather than against a second model's reading of words.
- **The owner's approval is the acceptance record.** Stage 4 shows the
  owner each reference beside the Proof, the concept beside the Proof, and
  the critic's open lines. On approval, Stage 5 writes
  `proof/APPROVAL.json`. It records:
  - the contract's sha256;
  - the Proof tree's manifest: the sha256 of every source file;
  - each Component's B-rep identity and carry key as make_round computes
    them;
  - each Component's approved STEP (print stance) and its Display-Pose
    STEP, each with its sha256, its volume per Part and its bounding
    box, the measures decision 2b compares against;
  - the assembly identity;
  - the `CRITIC.json` and `CONCEPT-CHECKLIST.md` hashes;
  - the make_round tool hash the gates ran under, and the nozzle;
  - `approved_by: owner` with the date.

  The Proof's code, its STEP files and `APPROVAL.json` together are the
  **Approved Proof**.

### 1c. The Approved Proof owns the shape; the contract owns what is measured or decided

- **The shape's source of truth.** For a contract designed under this
  ADR, the Approved Proof defines what the toy looks like: every surface,
  proportion, curve and visible detail.
- **What the contract keeps.** Only what a gate measures or the owner
  decides:
  - function and motion;
  - critical dimensions: anything a gate, fit, Interface, motion sweep,
    envelope, bed size or a stated owner number holds;
  - Interfaces and their text;
  - print choices: the nozzle, Print Sheets, and details made larger,
    put on paper or left out;
  - colours and filaments;
  - Bought Parts and the `electrical` section;
  - the Assembly Tree and count;
  - the requirement rows for all of these.
- **Prose and form rows become optional.** They may describe the shape
  for people, but they are no longer the authority, and no one checks
  them against the Proof.
- **Who wins.** The two cannot disagree silently, because the Proof is
  gated against the contract.
  - Where a contract-owned value and the Proof differ, the contract wins,
    and the Proof is rebuilt.
  - Where the contract is silent about shape, the Proof decides.
- **What `GUESSES.md` becomes.** It lists only choices inside the
  contract's fields: a fit, a colour, a critical dimension, an Interface
  pose, a bought part. Such a guess still closes in the contract. A
  shape choice is judged by the critic, not closed in words.
- **New contract schema.** Design Contract schema 11 is schema 10 with
  `shape: "approved-proof"`.
  - Geometry-scoped form rows and prose sections are optional.
  - The host refuses a schema 11 contract without `--seed-source`.
  - Schemas 1-10 keep the contract as the whole objective.

### 1b. The Proof is written by Make's authoring rules

The owner asked whether the Proof uses the same `autonomous-product-to-cad`
toolchain as Make. Partly.

- **What it shares today.**
  - It may read the vendored `cad` skill and the print-details library.
  - It lays its project out as Make does.
  - It gates through make_round's own code (`--print-gates-only`,
    ADR 0094).
- **What it is not required to do.** Everything Make's Manager and
  Component Worker must do when they write source. So today a Proof
  that passes the same gates can still be code Make would never have
  written: hand-modelled rivets, a fit chosen without the wiki, a
  hand-written involute, a joint value inside one Component's file.
  K4's heads, engraved with 123-253 small flat faces, are an example.
  A seed must be the source Make would have produced. So from this ADR
  on, the Proof follows **exactly** the authoring rules below, which
  are cited by section rather than copied. One home per rule (ADR 0094
  decision 6): the Proof prompt points at them and does not paraphrase
  them.

| Rule | Make's home | What the Proof must do |
|---|---|---|
| Component list and shared files | `references/make.md` § Pipeline step 1, first three paragraphs | one `part_<id>.step.py` per Component at a natural seam; overhang repair order before any print split; shared values only in `params.py` and `features/` |
| print-details layout | `make.md` § Pipeline step 1, `print_details.py --install <cad-project>` (and `--install-print` for a `print` section, `kit_tree.py --install` for a tree) | install the library into `<OUT>/features/print_details.py` byte for byte; never edit it |
| Decorative detail | `component-worker.toml`, the "Build decorative detail…" bullet (`pd = print_details.Details(nozzle=…)`, Detail Refusals) and the Print Piece bullet | every rivet, boss, dome, band, rim, rib, panel, window, slit and teardrop bore through `Details()`, never by hand; every hosted Print Piece through `pd.print_*` |
| Blunt tips | `component-worker.toml`, the "End every point, chisel, keel…" bullet | `pd.blunt_tip` / `pd.rib_end` to one print minimum; never a thinner chamfer |
| Joints, fits, clearances, gears | `make.md` § Pipeline step 1, the Interfaces paragraph; `wiki/SKILL.md` § The loop | run the wiki's `search` and `show` before every joint, fit, clearance or gear; write `# wiki: <slug>` beside each value and that page's `assert` naming it |
| Standard parts | same paragraph | every gear, bearing and fastener from `cad/scripts/stdpart` (`bd_warehouse`, `py_gearworks`); never a hand-written involute |
| Shared Helpers | same paragraph and the next one (`samples/<name>.step.py`, `make_round --shared-helpers`) | Shared Helpers hold only Interface values, joint sections and standard profiles; one sample per helper; `--shared-helpers` passes and freezes them before any Component is gated |
| Component file shape | `component-worker.toml`, the Shared Helper, `assembly_pose` and `<id>#<n>` instance bullets, and the kit bullet (`gen_step`, `bought_parts`, `print_parts`, labels, colours) | the same functions and signatures a worker writes |
| Reading references (from round 1) | product-run `AGENTS.md`, the reference-images bullet ("measure them with the `image-to-cad` skill"); `image-to-cad/SKILL.md` Steps 1-4b and 6 | measure each reference with `image-to-cad` (triage, `measure_image.py`, the cross-check gate, scale anchor, three views, per-component description, the build123d operation map) rather than reading it by eye. A number that falls in a contract-owned field (decision 1c) becomes a contract amendment the same round; a shape number stays in the Proof. Not its Step 5 (the contract already chose the design) or Step 8 (no likeness gate, ADR 0076) |

- **Where the Proof still differs from a worker,** on purpose:
  - **A gate failure forced by a contract-owned value is a finding.**
    It goes to `FINDINGS.md` and is fixed by amending the contract (a
    fit, a wall a requirement sizes, a stated dimension). A failure on
    the Proof's own shape choice is repaired by the Proof under Make's
    repair rules (the overhang order in make.md § Pipeline step 1), and
    the critic judges the result.
  - **A Detail Refusal is a finding too.** It is never silently left
    out after two refusals. Stage 3c puts it to the owner.
  - **One agent writes the shared files and every Component.** It needs
    no worker nonce, because it is not a run.
- **The approval binds the toolchain.** `APPROVAL.json` also records
  `src/workshop/make/skills/LOCK.json`'s sha256 and the installed
  `features/print_details.py` sha256.
- **A resync between design and build can change the toolchain.** When
  the run materializes a different library, `make_round` reinstalls it
  and rebuilds. A Component whose shape fingerprint then changes is a
  seed deviation, never a silent pass.

### 2. A seeded run certifies and packages

- **`--seed-source DIR`** on `workshop wish` and `workshop fix`, only with
  `--contract`, only on Spark. The host refuses it unless `DIR` holds an
  `APPROVAL.json` whose contract hash is the sealed contract's and whose
  manifest matches every file in `DIR`. It seals the Proof tree with the
  Wish as an immutable input, as `fix` seals its source archive (ADR 0065),
  and freezes `seed` into `MAKE-OPTIONS.json` (a new schema). No resume
  can add or drop it.
- **The run starts from the Proof's project.** Its `params.py`,
  `features/` and every `part_<id>.step.py` become Make's project. The
  Shared Helpers are frozen as ADR 0082 freezes them, after their samples
  pass.
- **An approved Component carries its approval.** Each component round
  builds and gates the Component as today. When its B-rep identity and
  carry key equal the ones in `APPROVAL.json`, the round carries the
  design approval as its review (`review.carried_from: "seed-approval"`),
  the way ADR 0081 carries a review forward. No Component Worker is
  spawned, no Component Reviewer is asked, no Shape Round is counted.
- **The assembly carries it too.** When every Component carries and the
  assembly identity equals the approved one, the assembly review is the
  critic's assembly verdict and its per-requirement verdicts. The blind
  review does not run.
- **What the run still does, unchanged:** host-verified bytes and hashes;
  the print gates at the frozen nozzle in each component round and in
  `verify_project --print-gates` for a print-ready claim; every Coupled
  Interface check and separable Keep-out Envelope (ADR 0082); the motion
  check (`--check-motion`); `--powered` and the host's power-report check
  (ADR 0095); Bought Parts; mesh, interference and insertion (ADR 0088);
  `make_round --full`; STEP export; Print Sheets; the kit Manual; README;
  receipts; DETECT; publication. A gate never trusts the design's own run
  of it: every gate runs again in the run on the sealed bytes.
- **Fix rounds stay for real defects.** If a gate, Interface, motion or
  power check fails in the run, the Manager may change the Component.
  The changed Component is a **seed deviation**, and the shape diff
  (decision 2b) decides what happens next:
  - **Within tolerance.** The change cannot be seen. The Component
    keeps the approval, its round records the diff, and no reviewer is
    asked.
  - **Over tolerance.** The change is visible. The Component goes
    through today's path: one Component Worker and one Component
    Reviewer (ADRs 0077/0080/0081), with Shape Rounds counted. The
    worker reads the approved part source and STEP as its shape.
  - **Either way,** the receipt and `workshop status --json` list every
    deviation with the gate that forced it and its diff, and
    `build-a-toy` shows each visible one to the owner before
    publication.
- **No in-run rulings on the approved shape.** A seeded run raises no
  Blocked Report about shape and makes no Manager ruling on one. A
  Contract Contradiction stops the run with a need. `build-a-toy` answers
  it in design: the kept Proof, the critic, the owner if visible, a new
  `APPROVAL.json`, then `workshop fix --seed-source`. ADR 0085's in-run
  amendment stays available for an invisible fix.
- **The receipt says where acceptance came from.** `seed: {approval_sha256,
  proof_manifest_sha256, critic_sha256, deviations: [...]}`, and the
  run report prints "approved in design by the owner on <date>; N
  Components certified unchanged; M deviations".

### 2b. The shape diff replaces the contract-only read

One deterministic tool, `proof_diff`, compares a built STEP with the
Approved Proof's STEP, Part by Part. It reads only bytes and computes:
- volume per Part;
- the bounding box in the print stance and in the Display Pose;
- the two-way Boolean difference: the material only in A and the
  material only in B, summed, so that a change which adds and removes
  the same amount still counts.

A Part passes when all three hold (owner, 2026-11-02):
- its volume differs by at most 1%;
- each bounding-box side differs by at most 0.1 mm;
- its two-way difference is at most 1% of its volume.

When the Boolean fails, as it did on K4's faceted heads, the tool
reports `boolean: failed` and the Part is judged on volume and bounding
box alone, which the receipt says. It runs everywhere the contract-only
read used to protect the shape:

| Where | Compared against | Over tolerance means |
|---|---|---|
| Seeded build: every Component whose identity differs from the approved one, and the final assembly | the Approved Proof sealed with the run | a visible seed deviation (decision 2) |
| `workshop fix` of a seeded toy | the Approved Proof in the toy's archive; or a new one, when the fix was approved in design | a fix changed the shape without a new approval: refused at Make acceptance |
| DETECT (`build-a-toy`) | the Approved Proof the build was seeded from | a `shape:<geometry>` finding |
| Contract amendment (design-side or a `build-a-toy` root amendment) | the previous Approved Proof | a visible change: the critic judges it and the owner approves it, giving a new `APPROVAL.json`. Within tolerance it needs no owner, matching "only visible changes wait for the owner" |
| An ADR 0085 in-run amendment | the Approved Proof | the change is visible, so ADR 0085 refuses it, as it already refuses a change a reference shows |

- **Validation on K4 (2026-11-02, `src/workshop/make/proof_diff.py`).**

  | Pair | Grumpy head | Wink head | Keycap base |
  |---|---|---|---|
  | v02 (fix) vs v01 (drifted faces) | two-way 0.77%, surface 0.600 mm: **passes** | dV 0.14%, surface 0.319 mm: **passes** | identical |
  | Proof vs v02 | 0.00%, surface 0.001 mm | Boolean failed (faceted Proof), surface 0.001 mm | dV 1.30%, surface 1.000 mm: **fails** (the hidden 9.4 mm³ stem pocket) |

  - **The three accepted criteria miss the visible face drift.** They
    pass the v01 faces, which took an 18-unit fix to undo, and they fail
    an invisible hidden pocket.
  - **Volume measures cannot see visibility.** An engraving moves very
    little material.
  - **A surface measure does see it.** `proof_diff` therefore also
    reports each Part's surface deviation: the largest distance from
    either surface to the other. It separates the cases cleanly: 0.001
    mm for the same shape modelled differently (faceted vs arcs), 0.3-0.6
    mm for the redrawn faces.
  - **It is reported, not yet a pass criterion.** It fails a Part only
    with `--surface-limit`, until the owner decides whether a 0.1 mm
    surface limit becomes the fourth criterion. The tool also treats a
    Boolean that returns an operand unchanged (K4's faceted wink: only-A
    = all of A) as failed, by checking `A - B = only_A - only_B`.
- **Where the host runs it.** The host runs `proof_diff` itself before
  Make acceptance, on the sealed approved STEP and the made STEP. This
  is a byte comparison with a fixed tolerance, not an engineering
  judgement, so ADR 0061's rule that Spark does not rerun the verifier
  still holds.
- **What DETECT keeps.** DETECT keeps `print:`, `count:`, motion, power
  and the requirement rows the contract still owns.
- **What DETECT drops.** For schema 11 it drops `extents:` and form
  rows. `envelope` stays when the owner stated it.

### 3. Where independence and trust now live

AGENTS.md says model prose and self-scores are proposals, and only
host-verified bytes, deterministic checks and reconciled receipts advance a
gate. ADR 0075 required a second reader besides the Manager for any
Component acceptance. Under this ADR:

| What | Who | What the host can verify |
|---|---|---|
| The geometry is what was approved | host | sha256 of every seed file against `APPROVAL.json`; B-rep identity of every built Component against the approved identity |
| It prints, moves, is powered, fits | host-run deterministic gates | the same gates as today, rerun in the run on the sealed bytes |
| It looks like the references and the concept | the Proof Critic (fresh, never wrote Proof code), then the owner | only that `CRITIC.json` and `APPROVAL.json` bind the exact Proof hash the run built; not the judgement itself |
| The build, a fix or an amendment keeps the approved shape | `proof_diff` | the host runs the diff itself on sealed bytes, with the fixed tolerance |
| A changed Component still looks right | the Component Reviewer, as today | as today (ADR 0081 and its #77 extension) |

- **The second reader is stronger, not weaker.** Before, the second
  reader was one low-effort model per Component. Now it is a fresh critic
  plus the owner, the only reader whose acceptance is not a proposal.
- **What gets weaker.** The host cannot prove that a critic ran, that it
  was fresh, or that the owner approved. `APPROVAL.json` is operator
  input, like the contract and the reference images already are: the
  operator who runs `workshop wish --seed-source` vouches for it. The host
  verifies only that the approval binds the exact bytes it builds. Today's
  in-run reviewer evidence on Claude Code (ADR 0081 #77: the guard saw the
  reviewer start and read every image) has no equivalent in design. The
  receipt must therefore say "approved in design", never "reviewed in
  run".
- **A model reading is replaced by a deterministic one.** The
  contract-only read was a model's reading of words. It is replaced by a
  byte comparison the host runs itself. For the places it protected,
  that is a stronger guarantee under AGENTS.md's rule.
- **The cost: the contract no longer proves anything about shape.** No
  independent reader checks that the words alone could rebuild the toy.
  See Consequences.
- **Model judgement is still only a proposal.** The critic's agreement
  only lets the design reach Stage 4. Two things advance the build: the
  owner's approval and the gates the host reruns.

### 4. Compatibility and lifecycles

- **Unseeded runs, frozen runs, schemas 1-10:** unchanged.
  - Every run without `seed` keeps workers, reviewers, the blind review
    and all current rules, with the contract as the whole objective.
  - DETECT keeps its contract extents for them.
  - Frozen runs keep the tool bytes they materialized.
  - An existing schema 1-10 contract may still be designed the old way.
    Its Proof then keeps ADR 0094's contract-only rounds and fresh read,
    because its contract is still the shape's authority.
- **Spark:** the only lifecycle that accepts a seed. ADR 0061 holds: the
  host does not rerun the verifier. It checks the seed binding and reads
  Make's sealed records, as ADR 0095 reads the power report.
- **Forge:** refused. Invent would create a concept that the sealed Proof
  already fixes.
- **Quest:** refused for now. Playtest could later follow a seeded Make
  unchanged; that needs its own decision.
- **Runtimes:** the seeded path needs no reviewer evidence from the
  runtime, so Codex and Claude Code behave the same. This also ends the
  Codex/Claude split of ADR 0081 #77 for seeded runs.
- **`workshop fix` of a seeded toy:**
  - The toy's archive carries its Approved Proof: code, STEP and
    `APPROVAL.json`.
  - Unchanged Components carry by STEP hash (ADR 0069).
  - A changed Component either stays within tolerance of the Approved
    Proof or carries a new approval passed with `--seed-source`.
  - A fix of a schema 11 toy without its Approved Proof is refused,
    because the contract alone no longer defines its shape.

## Considered options

- **Seed Make but keep workers, reviewers and the blind review**
  (CONCEPT-DRIFT option 3). Saves an estimated 10-20 units per build and
  keeps in-run review evidence. Rejected as the default: the reviewers
  would re-judge geometry the owner approved, and a reviewer or ruling
  is the one in-run step that has moved a build away from it (K4 v01).
- **Keep a contract-only first round and a fresh contract-only read**
  (the first draft's recommendation). Rejected by the owner on
  2026-11-02.
  - What they protected: that fix runs, DETECT and amendments, reading
    only the contract, would reproduce the approved shape.
  - Why they are not needed: under decision 1c those consumers compare
    against the Approved Proof with a deterministic diff instead.
  - The saving: about 1.1-1.7 units for the fresh read, plus one Proof
    round built blind and then rebuilt.
- **Seal the concept as a Make reference** (CONCEPT-DRIFT option 7).
  Rejected there and here: the contract wins, so a sealed concept only
  produces Reference Conflicts.
- **Have the host rerun a model critic in the run.** Rejected. It would
  be a Python-owned model judge, which AGENTS.md forbids, and the same
  re-review this ADR removes.
- **Ship the Proof without rerunning gates in the run.** Rejected. Gate
  code and catalogues can change between design and build, and the host
  needs its own run of every gate.

## Consequences

- **Cost moves from Make to design.** Make keeps only certification and
  packaging. Estimate, not yet measured: a seeded K4-sized build costs
  about 6-12 units instead of 33.6. Design gains about 1-2.5 units of
  critic rounds and image-aware Proof rounds, and saves the fresh read and
  the blind first round (about 1.5-2.5 units). Net about 16-27 units saved
  per toy, plus the drift fix rounds avoided (K4 v02 was 18 units).
- **Design cost leaves Workshop's token accounting.** design-a-toy runs
  outside the host, so `--max-tokens` and the run's TOKENS no longer cover
  modelling. `APPROVAL.json` carries the design's measured cost for
  information only.
- **The Proof's code quality now ships.** Decision 1b requires Make's
  own authoring rules, plus true arcs rather than faceted engraving (K4's
  heads had 123-253 faces against Make's 45-51). A worker that must repair
  a seed deviation then edits code written to its own rules. A Proof
  round costs a little more: wiki lookups, `image-to-cad` measurement and
  the helper sample freeze. Estimate +0.1-0.3 units per first build,
  unmeasured.
- **Trade-off: rebuilding without the Proof's code is harder.** For a
  schema 11 toy the words no longer describe the shape.
  - **Losing the Proof means losing the shape.** If its code or STEP is
    lost, or a future kernel cannot build it, nothing regenerates the
    shape from the contract. Another tool or vendor cannot build the
    toy from the contract alone, and a person reading the contract
    learns its function, sizes and choices, not its form.
  - **What the archive must keep.** The toy archive, the receipt and
    every fix carry the Approved Proof as a required artifact. The STEP
    files stay readable without the code, so the shape survives a dead
    toolchain even if editing it does not.
  - **Rebuilding from images and STEP is no longer checked.** The
    contract-only read used to prove this was possible. Nothing proves
    it now.
- **The diff is necessary, not sufficient.** A visible change that
  moves little material can stay under 1%: the K4 v01 face change is the
  case to measure. The two-way difference catches a change that adds and
  removes the same amount, and every deviation is listed on the receipt
  and shown to the owner when visible. The pilot measures `proof_diff`
  on K4 v01's faces against its Proof before the tolerance is trusted.
- **Older Proofs cannot seed.** A Proof written before decision 1b
  (K4's, the cabinet's) does not follow these rules. It is rebuilt under
  the new prompt first; `seal_proof.py` refuses a project with no
  `# wiki:` citations where it has joints, or with no installed
  `features/print_details.py`.
- **design-a-toy becomes heavier and more important.** Its coordinator
  context is already the largest design cost. The critic and the compares
  must stay in subagents.
- **Kits and powered toys:** the Proof already writes `print_parts()`
  (ADR 0092). The Manual, Print Sheets and the power report stay Make
  work.

## Owner decisions (2026-11-02)

The owner accepted every recommendation, and decided the last question
(item 8):

1. **Critic cap.** Five rounds that change the Proof's geometry. Open
   differences then go to the owner at Stage 4.
2. **One critic for the whole toy,** plus a close look at one Component
   only when the critic needs one (decision 1).
3. **A Concept Checklist** is added and held by the critic (decision 1).
4. **A visible seed deviation** goes through the in-run Component Worker
   and Component Reviewer, is listed on the receipt, and is shown to the
   owner by `build-a-toy` before publication.
5. **Diff tolerance:** 1% of volume per Part, 0.1 mm per bounding-box
   side, and the two-way difference at most 1% of volume. It applies
   everywhere `proof_diff` runs (decision 2b).
6. **Every Proof follows Make's authoring rules** (decision 1b), not
   only a Proof meant to seed a build.
7. **Pilot:** the beaver coasters.

8. **No contract-only first round and no contract-only fresh read.**
   - The kept Proof sees the references, the concept and the checklist
     from round 1.
   - The deterministic shape diff against the Approved Proof replaces
     them wherever they protected: the seeded build, fix runs, DETECT,
     amendments and seed deviations (decision 2b).
   - The Approved Proof is the shape's source of truth, and the contract
     keeps what gates measure or the owner decides (decision 1c).
