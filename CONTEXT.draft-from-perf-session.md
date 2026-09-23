# Autonomous Workshop

The Workshop turns a single written Wish into a sealed, published toy: a native
agent session does the designing and making, while a deterministic host owns
lifecycle order, budgets, gates and every external effect.

## Language

### Runs

**Wish**:
The exact written request for a toy, frozen at the start of a run and never
edited afterwards.
_Avoid_: Prompt, brief, spec

**Run**:
One execution of the lifecycle against a Wish, from creation to a sealed
archive or a truthful failure.

**Correction Run**:
A run created by `workshop fix` that clones a published toy and applies one
correction brief to it. Distinct from a fresh run because it has a Revision to
carry parts forward from.
_Avoid_: Fix flow, fix run, re-run

**Revision**:
The source archive a Correction Run is cloned from, and the baseline its
carried-forward parts are compared against.

**Frozen**:
Fixed at run creation and thereafter immutable for that run — the Wish, the
effort, the Make options, and the run's own copies of the skills and tools.

### Lifecycle

**Lifecycle**:
The fixed order of Stages a Run passes through. A Run chooses one at creation
and cannot change it afterwards.

**Stage**:
One durable step of a Lifecycle, with its own outcome and its own Gate. A Stage
is a checkpoint in one continuous session, not a separate session or persona.

**Spark**:
The shortest Lifecycle: Wish, then Make, then Release. It has no Invent Stage,
so a Correction Run of a Spark toy returns to Make.

**Forge**:
The Lifecycle that adds Invent before Make.

**Quest**:
The longest Lifecycle: Forge plus Playtest between Make and Release. Only Quest
requires passing Playtest evidence.

**Invent**:
The Stage that decides what the toy is, before anything is built.

**Make**:
The Stage that builds the toy and proves it correct. It contains every Make
Round and the Blind Review.
_Avoid_: Make round (that is one pass inside this Stage), build phase

**Playtest**:
The Stage that judges whether the built toy is worth playing with.

**Release**:
The Stage that seals the toy and publishes it.

**Inventor**:
The declared specialist whose taste governs creative judgment for a Run. One
Run has one Inventor.

**Passed Through**:
A Stage that a Run's Lifecycle omits. It produces no turn, artifact, Gate or
evidence, and a Run says so plainly rather than implying the work happened.

### Making

**Make Round**:
One pass of building a component or the assembled object, gating it, rendering
its visual packet, and recording feedback on what that packet shows. One Make
Stage contains many Make Rounds.
_Avoid_: Make phase, make_round (that is the tool that runs one)

**Component Round**:
A Make Round scoped to a single printable part in isolation, before any
assembled object exists.

**Review Loop**:
Everything in Make after first geometry exists: Component Rounds, assembled
Make Rounds, and the Blind Review with its repair cycles. The part of a run
whose cost scales with how wrong the geometry is rather than with how big the
Wish is.
_Avoid_: Fix flow, repair loop, iteration loop

**Gate**:
A deterministic check with a pass, fail or unverified verdict that the agent
cannot argue with or waive.

**Print Gate**:
A Gate that judges a part against the fixed 0.4 mm nozzle standard — wall
thickness and overhang — so a printability defect surfaces in the round that
caused it.

**Blind Review**:
An independent critic's reading of the rendered images and animation alone,
recorded before the Wish and concept are revealed to it. Any geometry change
afterwards invalidates it.
_Avoid_: Signature review, critique, QA

**Carry Forward**:
Reusing a part from the Revision unchanged, rather than rebuilding and
re-gating it, when its freshly built bytes match. A Correction Run's default.

### Sealing

**Sealing**:
Hashing the finished product tree into an immutable archive. The host
re-derives the geometry from source outside the sandbox, with caches disabled,
as the last word on what the archive contains.

**Toy Archive**:
The sealed, hashed output of a run: the deliverable, and the input to the next
Correction Run.
