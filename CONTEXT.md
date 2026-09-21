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
numeric checks and the Manager's own inspection of the rendered result.

**CAD Project**:
The self-contained directory holding a toy's geometry source, exports,
measurements, renders, and verification report. It is the exact unit the host
rebuilds and seals.

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
