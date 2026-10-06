# Autonomous Workshop

Autonomous Workshop turns one person's Wish into one evidence-backed physical
toy. This glossary fixes the vocabulary that the host, the native agent, and
the sealed artifacts all have to agree on.

## Language

### The toy

**Toy**:
The single physical plaything one run produces, from its CAD source to its
printed manual. It is the only thing in this domain called a product; the word
"product" survives only inside the identifier below.
_Avoid_: Product, model, plaything, item

**Wish**:
One person's request for a toy, preserved in their exact words with their
explicit constraints. It is stated in open language rather than chosen from a
catalogue of product classes.
_Avoid_: Prompt, brief, order, spec

**Product id**:
The opaque identity of one toy, minted once when its Wish is sealed and used
for every run directory, checkpoint, and sealed artifact thereafter.
_Avoid_: Wish id, wish-id, run id

**Toy Blueprint**:
The small baseline contract every toy satisfies regardless of what its Wish
asked for. It binds shared checks, never creative scope.

**Design Contract**:
The person's approved enumeration of one toy's decided form — its unique
geometries, their dimensions, their joints and print stances, its visual
requirements, and its references — sealed inside the Wish. No two of its
statements may be impossible to satisfy together. Unlike the Toy Blueprint it belongs to one toy; unlike
the Wish's prose it is exact enough to check.
_Avoid_: Spec, design spec, concept

**Trend**:
One topic people are talking about now, backed by dated evidence, that a toy
is invented to be inspired by. A toy takes inspiration from a Trend; it never
carries the Trend's protected names, characters, logos or trade dress.
_Avoid_: Topic, fad, meme, theme

**Trend Hook**:
One countable or pointable feature of a toy that makes it read as inspired by
its Trend rather than a generic toy with the Trend's name on it. A
trend-inspired toy without one is rejected, whatever it looks like.
_Avoid_: Theme Hook, trend fit, reference

**Signature Motion**:
The one movement a toy's play centres on, made by parts in contact or sharing
space over time — a crank that flaps wings, a pull that walks legs. A toy whose
only motion is decorative has none.
_Avoid_: Gimmick, action feature, animation

**Contract Mode**:
A run that was given a Design Contract at creation and is judged against it,
rather than against requirements the Manager compiled. Frozen for the run.
_Avoid_: Strict mode, image-derived mode

**Correction Run**:
A fresh run that imports an already-sealed toy as data and rebuilds it against
a correction brief. The original run is never mutated.
_Avoid_: Fix run, revision run, v2

**Unreleased**:
The state of a toy that was sealed locally with no Factory listing. It is a
complete toy with a publication record that says so, not an incomplete one.

### People and judgment

**Inventor**:
A declared specialist with its own creative point of view, materialized for a
run as a native subagent the Manager can delegate to. One Inventor is selected
per run and bound for its whole life.
_Avoid_: Persona, designer, custom agent, role

**Taste**:
An Inventor's immutable creative constitution: its preferences, its judgment,
and the work it refuses to make. It governs creative decisions and never
waives a gate.
_Avoid_: Style guide, preferences, prompt

**Manager**:
The single root native coding-agent session that owns one run's cognitive
work. It receives each stage packet, delegates to Inventors, and submits the
one proposal the host verifies.
_Avoid_: Orchestrator, root agent, driver

**Roster**:
The set of Inventors eligible for a given run, materialized as the run's only
source of selectable specialists.

### Lifecycle

**Route**:
The lifecycle a run freezes at creation, fixing which stages are enabled.
Passed-over stages produce no turn, artifact, gate, or evidence.
_Avoid_: Mode, track, tier, effort level

**Spark**:
The shortest route: Wish, Make, Release.

**Forge**:
The middle route: Wish, Invent, Make, Release.

**Quest**:
The full route: Wish, Invent, Make, Playtest, Release.

**Stage**:
One durable lifecycle checkpoint in a route. A stage is a host-owned
transition boundary, not a separate model session, persona, or worker.
_Avoid_: Phase, step, task

**Invent**:
The stage that researches, explores, and seals one bounded toy concept,
including the physical facts Make will need.

**Make**:
The stage that turns a sealed concept into the actual CAD source, components,
assemblies, renders, and deterministic verification.

**Playtest**:
The stage that independently evaluates a sealed toy against its concept. It is
active only in Quest, and its absence elsewhere is recorded rather than
implied.

**Release**:
The terminal digital stage, which seals the customer-facing package and hands
it to the host for publication.

**Goal**:
The one native objective a Manager pursues during a single active stage
attempt, ending only when that stage's finalizer succeeds. Exactly one is
active at a time.

**Round**:
One bounded attempt inside a stage. Rounds are spent on repair within a stage.
_Avoid_: Iteration, retry, loop

**Revision**:
One backward trip to an earlier stage, recorded as a failed gate and charged
against the run's shared revision history. It invalidates every artifact
downstream of the stage it returns to.
_Avoid_: Rollback, rework, restart

**Gate**:
A deterministic host check that decides whether a stage may advance. Only
exact bytes, deterministic checks, and reconciled receipts pass one; model
prose and self-scores never do.

**Checkpoint**:
The durable host-owned record of where a run truthfully is. It lives outside
the agent's working directory and is the only thing a resume trusts.

**Stage Packet**:
The read-only description of the current stage the host hands the Manager
before each turn, binding exact upstream contracts and output paths.
_Avoid_: Context, payload, prompt

**Proposal**:
The Manager's compact claim that a stage is complete. It is an input to
verification, never an outcome.
_Avoid_: Result, output, submission

**Finalizer**:
The deterministic run-local tool that validates authored work, hashes exact
bytes, and writes a proposal. It neither reasons nor advances a gate.

**Seal**:
To fix an artifact tree to exact content-addressed bytes so that later stages
and gates can bind to it. Sealed bytes are immutable for the rest of the run.

**Frozen**:
Fixed at run creation and immune to later changes in Workshop itself. A frozen
run keeps the exact route, model, allowances, and tool bytes it started with.

### Making the toy

**Component**:
One distinct physical part of a toy, authored in its own source file and
proven on its own before it may join an assembly.
_Avoid_: Part, piece, module

**Make Round**:
One build-and-repair cycle over a component or an assembly, driven by both
numeric checks and an inspection of the rendered result: the Manager's own
for an assembly, its Component Reviewer's for a Component.

**Carry Forward**:
The permission for a Correction Run to keep a Component's existing evidence
instead of earning it again, granted only when that Component's geometry is
unchanged. Identity is established on the shape itself rather than on the
exported file: a check is a pure function of the shape it reads, and two
exports of one shape need not agree byte for byte. It carries evidence only.
It lowers no threshold and skips nothing about the assembly.
_Avoid_: Quick fix, quick mode, carry policy, `quick_fix`, `--quick`

**CAD Project**:
The self-contained directory holding a toy's geometry source, exports,
measurements, renders, and verification report. It is the exact unit the host
rebuilds and seals.

**Evidence Scene**:
An assembly built only to answer a question about a toy, never part of the toy
and never printed: two pieces set side by side so a mirrored cue reads as one
cue inverted, a rank ladder, two worlds that share a filament set adjacent. It
is exported and rendered like any other geometry, so it costs what the toy
costs.
_Avoid_: Test scene, scratch assembly, render scene

**Hero**:
The single canonical render of the finished toy, chosen from the archived
render family and used as its public image.
_Avoid_: Thumbnail, cover, preview

**Signature Experience**:
The promised interaction, reveal, or anti-generic detail that makes a toy
specific to its Wish. It must be visually inspectable before any prose may
claim it.

**Blind Review**:
An independent critique of a toy's renders performed before the critic is told
the Wish or the concept, so that what the object actually shows is recorded
separately from what it was meant to show.
_Avoid_: QA, review pass, critique

**Component Review**:
A reader other than the Workshop Manager judging whether one Component looks
like its reference, from the reference beside the model in the Display Pose,
at the reference's Reference Camera. Its recorded agreement, with passing
build and print checks, is what passes a Component; its disagreement lists
the differences to repair. A third answer, camera mismatch, says only that
the side of the model facing the camera is not the side the reference shows:
it is not a Shape Round, gives the Component Worker nothing to repair, and
stops the run until that one Reference Camera is amended (ADR 0083). A
Reference Conflict it lists is not a difference (ADR 0084).
_Avoid_: Likeness check, self-review, sign-off

**Reference Camera**:
The azimuth and elevation, in the Display Pose frame, from which a reference
image shows its subject. A schema 3 Design Contract records one for every
reference, estimated by eye in design-a-toy and approved with the images.
A camera mismatch is answered by amending that one camera; the contract's
requirements and image bytes stay sealed.
_Avoid_: View, declared camera, viewpoint

**Shape Round**:
The first round of a Component after a disagreeing Component Review. A
Component gets five. Build or print repairs, unchanged reruns, and changes
forced by a Shared Helper, an Interface or an assembly round are not Shape
Rounds (ADR 0081).
_Avoid_: Attempt, iteration

**Component Worker**:
The agent that authors one Component's own source, repairs it until it builds
and passes its print gates, then applies its Component Reviewer's text as
Shape Rounds. It sees only that Component's inputs, including its sealed
reference image, but never the Component's rendered rounds, and never edits a
Shared Helper. Only a Component Worker runs a Component's rounds. Its context
lives until the assembly passes, so an unlock returns to the worker that
already knows the Component.
_Avoid_: Builder, sub-Manager, part agent

**Component Reviewer**:
The reader who performs every Component Review of one Component, kept as one
thread and asked again for each later review. The Workshop Manager, not the
Component Worker, asks it. It is the only agent that views that Component's
rendered rounds.
_Avoid_: Critic, judge

**Component Acceptance**:
A Component Review that disagreed after the Component used all its Shape
Rounds, recorded instead of repaired again and reported to the person when
the run ends. It is never the person's decision.
_Avoid_: Waiver, override, Stalled Out

**Reference Conflict**:
A place where a Component's reference image shows something its Design
Contract forbids. The Design Contract wins: it is not a difference, costs no
Shape Round, and is reported to the person when the run ends so the image can
be corrected.
_Avoid_: Contract mismatch, disagreement

**Shared Helper**:
A project file two or more Components import because they must agree on what
it holds: an Interface's values, a joint section or a standard profile. Each
value cites the design wiki page it came from and carries that page's assert;
a gear or other standard element comes from the toolchain's libraries. A
Component's own geometry, print stance and dimensions never live in one. The
Workshop Manager writes it, tests it on built samples, and freezes it before
any Component Worker starts.
_Avoid_: Shared file, common code, utils

**Print Detail**:
A decorative surface feature (a rivet, boss, low dome, band, rim, pipe rib,
inset panel, lancet window or grille slit) that a Component Worker adds from
the Workshop's print-details library instead of modelling it by hand. Each
refuses a size below the design wiki's print limits for the run's nozzle and
prints without support in the Component's print stance. The Workshop Manager
copies the library unchanged into the CAD project, where it is frozen with
the Shared Helpers but holds no design value.
_Avoid_: Greebles, trim, hand-modelled detail

**Blunt Free Edge**:
The flat land, at least one print minimum across (0.8 mm at a 0.4 mm nozzle),
in which every point, chisel, keel and V underside of a Component ends. The
printer sizes it, not the geometry's minimum wall, which is a strength floor
for load-bearing sections. The
print gate fails every straight knife edge as a thin wall, so every Design
Contract states the rule, the Component Reviewer never asks for a sharper
edge, and the print-details library cuts the land (issue #82).
_Avoid_: Sharp tip, knife edge, feather edge

**Repeated Print Defect**:
A failing component round whose failing feature, as the print gate names it,
also failed in the same Component's previous round. Runs are compared by
their repeated print defects, which show blind repair; the print-gate failure
rate is context only, since a failing round costs about what a local gate run
does (issue #82).
_Avoid_: Failure rate, retry

**Detail Refusal**:
A Print Detail's refusal, at build and before any print gate, of a size or
spot it cannot print. It is not a print defect: repeats of it are counted
apart from Repeated Print Defects. A build reports every Detail Refusal at
once, each with the value that would pass at that spot, and fails; a
Component Worker leaves out a detail refused at the same spot in two rounds
and names it in its report (issue #86).
_Avoid_: Print failure, build error

**Contract Contradiction**:
Two Design Contract statements that cannot both hold. A print rule the
contract states (the print stance, "no part needs support") counts as a
statement, so geometry that cannot print in its stated stance is a Contract
Contradiction. Neither the Component Worker nor the Workshop Manager chooses
between the statements: the Manager turns it into a `need` quoting both
(ADR 0080, issue #88), or, when the smallest fix is invisible, proposes a
Contract Amendment a Contract Reviewer must confirm (ADR 0085).
_Avoid_: Conflict (a Reference Conflict is an image against the contract), impossible spec

**Blocked Report**:
A Component Worker's recorded report, made with `make_round
--report-blocked`, that its contract rows contradict or that it cannot
proceed without a Workshop Manager decision. It names the Component, the
worker's latest round and the rows, verbatim. It stays open until the
Manager answers it with a Decision, a `need` or an applied Contract
Amendment that names it (ADR 0085); a Decision that waits on
another Component keeps it open until that Component's next passing round,
when the Manager wakes the worker again. While one is open the host refuses
an assembly round, the Make proposal and Make acceptance, and on Claude Code
the root's turn end unless it ends on a recorded need. The run report lists
every Blocked Report, how it was cleared and how long it stayed open (issue
#88). A Decision that waits on nothing is a ruling that binds the Component
Reviewer too: every later review packet of that Component carries it
(issue #97).
_Avoid_: Blocked message, stuck worker

**Ruling Dispute**:
A Component Reviewer's statement that a Workshop Manager ruling in its
review packet is wrong. It names the Blocked Report and says why. It is not
a difference: the ruling stands, it costs no Shape Round and never reaches
the Component Worker, and a review whose only findings are Ruling Disputes
agrees (issue #97).
_Avoid_: Disagreement with the ruling, re-asking a ruled-out repair

**Contract Amendment**:
A change to the text of Design Contract rows made inside a run to remove a
Contract Contradiction whose smallest fix no sealed reference image shows.
The Workshop Manager proposes it; it applies only when a Contract Reviewer
confirms that the rows cannot both hold, that it is the smallest change, and
that it is invisible in every reference. The host replays every amendment
against the sealed contract by hash before it accepts Make; `WISH.json` and
the images keep their bytes, Components whose rows changed unlock, the run
report lists each one, and `build-a-toy` folds it into the toy's contract for
the next attempt (ADR 0085, issue #90). A Reference Camera amendment (ADR
0083) is the host's own and is not one.
_Avoid_: Contract edit, override, waiver

**Smaller Retry**:
The one further Contract Amendment allowed after a refusal whose Contract
Reviewer confirmed the contradiction and found the change invisible but
named a smaller change: the same rows, each change's new text the refused
change's old text with only deletions applied, reviewed by another fresh
Contract Reviewer. Its refusal stops the run with the need (issue #96).
_Avoid_: Second attempt, re-proposal

**Owner Contract Amendment**:
The owner's answer to a Contract Contradiction need on resume: `workshop
resume <wish-id> --amend-contract CONTRACT.md` with the amended contract
file. The host records only the requirement text, Interface text and prose
that file changes against the contract the run reads now, and refuses
anything else; the run keeps its sealed name line, `WISH.json` and images.
Rounds read its rows after every applied Contract Amendment, Components
whose own rows changed unlock, and the run's in-run Contract Amendments
close. It needs no Contract Reviewer: the source is the owner. A run
materialized before it is refused and relaunched (issue #100).
_Avoid_: Contract override, re-seal, owner patch

**Contract Reviewer**:
The fresh reader, never the Workshop Manager and never a Component's
reviewer, who confirms or refuses one Contract Amendment after viewing every
sealed reference image. Each amendment gets its own (ADR 0085).
_Avoid_: Contract judge, second Manager

**Visible Change**:
A Design Contract amendment that a reference image would show, so the image
must be redrawn. Only a Visible Change waits for the owner: the unattended
`build-a-toy` loop batches a pass's Visible Changes on one review page and
applies every other amendment (a clearance, a print stance, hidden geometry, a
value no image shows) without asking, recording it in the toy's ledger (issue
#89). Inside a run, only a change that is not a Visible Change may be a
Contract Amendment (ADR 0085).
_Avoid_: Cosmetic change, user-facing change

**Unmeasurable Mesh**:
A print gate's verdict on a valid B-rep whose tessellation stays open even
after one finer retry. Inside and outside are undefined, so nothing was
measured: it is not a print failure, and it never passes a round. An invalid
B-rep with an open mesh fails instead, with its bad faces named.
_Avoid_: Open-mesh failure, non-watertight

**Interface**:
One place where two or more Components meet, recorded in the Design Contract
with its Interface Kind and the Components it joins. Interfaces are how a
toy's Components are built in isolation and still fit. An Interface names a
Component by its Unique Geometry id, or one instance of a Unique Geometry
whose count is above 1 as `<id>#<n>`: a mirror pair of wings that mesh is an
Interface between `wing#1` and `wing#2`.
_Avoid_: Joint (a joint is one kind of Interface), connection, mating

**Interface Kind**:
How an Interface is proven: static (parts that sit together, proven by the
Shared Helper samples), separable (proven by a Keep-out Envelope in each
side's own rounds) or coupled (proven by a Coupled Interface check).

**Keep-out Envelope**:
A simple solid in assembly coordinates, one per declared pose or a single
static one, that one Component of a separable Interface stays inside and the
other stays outside. Each side is checked in its own Component rounds, so
either can be repaired without touching the other. It is sufficient, not
necessary: anything that needs contact or shares space over time is coupled.
_Avoid_: Clearance box, bounding box

**Coupled Interface**:
An Interface whose Components must move together or pass through the same
space at different times: gears, cams, linkages. It is checked on its locked
Components alone by the coupled motion check over its pose table. On failure
the Design Contract's yielding Component is unlocked and repairs, and that
repair is not a Shape Round.
_Avoid_: Mechanism check, mesh check

**Unique Geometry**:
One distinct shape in a Design Contract, shared by every Component built to it.
A chess set has six, not thirty-two. It is the unit a Design Contract names
before any Component exists.
_Avoid_: Piece type, part shape

**Focal Component**:
The one component of a toy's design allowed to dominate the composition,
chosen and paid for in the design before any image exists. It is a part of
the object, not a picture of it.
_Avoid_: Hero, signature piece, centrepiece

**Display Pose**:
The one arrangement of a toy's moving parts that its design fixes for
presentation. The assembly reference image, the built toy and its comparison
images all use it, so a jointed toy has one form to compare rather than many.
_Avoid_: Default pose, rest pose, render pose

**Requirement Scope**:
Whether a visual requirement in a Design Contract is judged on the assembled
toy or on one Unique Geometry, and so on every Component built to it. It
decides which renders may serve as that requirement's evidence.

**Conformance**:
Agreement between a sealed toy and its Design Contract, requirement by
requirement. A toy can pass every Gate and still lack conformance.
_Avoid_: Match, contract match, compliance

**Print Gate**:
The deterministic geometry check that a toy is actually printable — fit, mesh
validity, overhang support, and wall thickness — measured at the exact nozzle
the print will use.

### Release and effects

**Manual**:
The self-contained printable PDF that ships in the box. It is the canonical
customer artifact, not a summary of one.
_Avoid_: Docs, readme, instructions, guide

**Publish**:
The host-owned effect that transfers a sealed toy's exact bytes to Factory and
confirms them by authenticated readback. It is the effect half of Release, and
never a creative turn.

**Factory**:
The external service that hosts published toys. It is the only authenticated
external effect in the lifecycle, and the host alone ever talks to it.

**Pack**:
A reproducible immutable serialization of a sealed artifact tree, used to move
exact bytes without trusting the filesystem they came from.

**Operations**:
Everything after Release — printing, delivery, and customer review. It is part
of the toy's story but not an executable Workshop stage.

### Design Vault

**Design Vault**:
The typed-link graph of design knowledge that links mechanisms to their known
risks, risks to anti-patterns, and anti-patterns to the fixes that worked.
Every finished toy adds its own page.
_Avoid_: Knowledge base, wiki, memory

**GameVault**:
The external service that hosts the Design Vault and serves it over an
authenticated API. It names the deployment, not the concept.

**Vault Node**:
One entry in the Design Vault — a mechanism, anti-pattern, rule pattern,
constraint, component, combo, or toy — joined to others by typed links.

**Vault Lead**:
A recorded risk the host hands a stage because the toy's concept uses a
mechanism that carries it. A lead must be answered, and answering it never
waives a gate.
_Avoid_: Warning, hint, suggestion

**Make Lesson**:
An evidence row banked on the Design Vault by a finished Make attempt,
recording how a toy failed or passed so later runs can read it before
designing.

### Daydreaming

**Daydream**:
One Inventor inventing and judging a brand-new toy idea with no Wish behind
it. It happens before and outside a run.
_Avoid_: Brainstorm, ideation

**Idea**:
One judged candidate produced by a daydream, which may later be built as if it
were a Wish.

**Seed**:
The starting constraint drawn for a daydream, which pushes an Inventor away
from its own defaults.

**Novelty Report**:
The record of how an Idea differs from the toys already made, used to reject
repeats before any run begins.

**Taste Fit**:
The recorded judgment of how well an Idea matches the Inventor's own Taste.
