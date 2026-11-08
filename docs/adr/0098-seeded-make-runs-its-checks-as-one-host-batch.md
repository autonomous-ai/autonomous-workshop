# ADR 0098: A seeded Make runs its checks as one host batch, and the model works only on a failure

- **Status:** Proposed on 2026-11-07. The owner answered all six open
  questions the same day; the answers are folded into the decisions below
  and listed under "Owner decisions". The first implementation merged in
  PR #234; the whole-batch seal, the `parts/` exporter and the Make
  record's batch summary are on branch `seeded-batch-complete`. The
  section "Implementation status" says what is built and what is still a
  target.
- **Amends:**
  - [ADR 0096](0096-the-approved-proof-is-the-build.md), for seeded runs:
    - decision 2, "What the run still does": who runs those checks;
    - the seeded Make order (`make-seeded.md`);
    - decision 1b and amendment item 5: what the Approved Proof must carry.
  - [ADR 0061](0061-spark-make-owned-verification.md), for seeded runs only.
    Make's own verification is run by the host instead of the native
    Manager. It is not a second run of it.
- **Relates to:**
  - [ADR 0049](0049-product-wide-token-budget.md): the token budget is
    unchanged. A Make with no native turn spends no tokens.
  - ADR 0012: one native session per run, and Goals.
  - ADR 0081: carried reviews.
  - ADR 0082: Interfaces.
  - ADR 0095: powered toys.
  - Issue #227: the Proof should run `bought_model`.
- **Evidence:**
  [docs/research/seeded-build-cost-2026-11-07.md](../research/seeded-build-cost-2026-11-07.md).

## Context

ADR 0096 made the owner-approved Contract Proof the build. A seeded run
should only certify it and package it. The first large seeded toy, the
Sunset Slider Night Light (24 Components, powered, moving), shows that it
does much more than that:

- **Attempt 2 cost 13.98 units** in its native root session: 731 model
  calls at an average context of 135K. Attempt 1 cost 8.31 units. That is
  22.3 units of Make for a shape the owner had already approved, against
  56 units for the whole design.
- **Cost is the number of calls times the context re-read on each one.**
  Cached reads are 70% of the money; output is 16%.
- **30% of the calls (221; 4.11 units) only ran a deterministic tool and
  read its result.** Examples: 24 component rounds that each said "locked,
  exact", interface checks, `wait_for` polls on long checks, hash
  comparisons and the finalizer.
- **131 calls (2.26 units) read the source of a host tool** to learn what a
  gate or the finalizer wanted. In the `make-contract-invalid` rejection
  loop, 97 of 135 calls were reads.
- **The seed did not carry the checks' inputs.** The Manager wrote
  generators in the run for:
  - the power manifest, mounts, validation envelopes and Bought Part
    placements;
  - the motion manifest, which design had run 14/14 but not sealed;
  - the production occurrences;
  - the product renders and motion states;
  - `spark-source.json`;
  - the part export.

  Debugging those inputs, not checking the shape, is where most of the
  money went.
- **Every real defect was reported by a deterministic check in its own
  words.** They were:
  - the drive-frame lead hole against the switch wire (`check_mount` and
    assembly interference);
  - the gear-mesh contradiction (`make_round --interface`);
  - two `bought_model` harness defects.

  No model judgement found any of them. The one model repair, a Component
  Worker on the drive frame, cost 0.10 units in 9 calls at 37K context.

So the expensive part of a seeded build is a model driving deterministic
tools on a large context. That job belongs to the host.

## Decision

### 1. The Approved Proof carries every check's input

`seal_proof.py seal` refuses a Proof that lacks an input a seeded batch
would need for its contract. All of these are the toy's own numbers, which
only design knows. ADR 0096 amendment item 5 makes the same argument for
the spec and the three audits.

| Input | Required when | Written and gated in design by |
|---|---|---|
| `measure/motion.json` | the contract has a motion plan, or the run will freeze `check_motion: true` | the Proof, passing `check_motion` (design already runs it; today it is left in `/tmp`) |
| `measure/power.json`, `measure/mounts.json`, `ref/validation/*.step` | schema 10 `electrical` | the Proof, passing `check_power` and `check_mount` (`measure/electrical/` is written by final verification, an output, not an input) |
| `measure/bought-placements.json` | a Bought Part with a `model` or a `pose` | the Proof, passing `bought_model.py` (issue #227) |
| production occurrences in `proof.step.py` (colour-named, as the finalizer reads them) | always | the Proof; checked in the run by the finalizer, which design cannot run (see "Implementation status") |
| `SEED-PRODUCT.json`: `title`, `summary`, `concept` and `research` | always | the Proof; the owner sees the summary at Stage 4 (owner decision 3). The run's `product.json` and Spark source are composed from it |
| `snap/iso.png`, `snap/signature.png` | always | the Proof, the renders the owner approves |
| the motion review (`snap/MOTION-REVIEW.json`, `snap/MOTION-EVIDENCE.json`, `snap/motion.gif`) | a moving toy | the Proof Critic, on the Proof's motion presentation (owner decision 1) |

- **The manifest covers them.** The seed manifest and `APPROVAL.json` list
  these files by sha256, as they list the three audits today. A seed whose
  inputs are missing or stale is refused at seal time, not discovered in
  the run.
- **`seal_proof` runs the whole batch once in design (owner decision 5).**
  It uses `--dry-run`
  against the Proof project, with the same script and tool bytes that
  `APPROVAL.json` binds. A Proof that fails it cannot be sealed. That is
  where the drive-frame lead hole should have been found, at design cost and
  in design's context.

### 2. One deterministic script runs every re-verification

`workshop.make.seeded_batch` is materialized into the run with the other
make-round tools. It is frozen with them, and its sha256 is recorded in
`MAKE-OPTIONS.json`.

- **How it runs.**
  - It runs inside the run's sandbox, as the run user.
  - It uses the run's materialized tools, never the Workshop checkout.
  - It gets no effect credentials.
  - The make_round guard issues its component-round nonces as host state,
    as it issues the Manager's today.
- **What it does, in a fixed order of dependency layers.**
  1. **Project.** It copies the seed into the CAD project. It installs
     `print_details.py` and the Print Sheets, comparing bytes with the seed.
     A changed library rebuilds, and a changed shape is a seed deviation
     (ADR 0096 decision 1b).
  2. **Shared Helpers.** It runs the freeze (`make_round --shared-helpers`).
  3. **Components.** It runs every component round, with its print gates at
     the frozen nozzle, `posed` and `datum`, and the `proof_diff` against
     `seed/approved/`.
  4. **Interfaces.** It checks every Coupled Interface
     (`make_round --interface <id>`) and every separable Keep-out Envelope.
  5. **Bought Parts and power.** It runs `bought_model.py`, `check_power`
     (`--powered`) and `check_mount`.
  6. **Motion.** It runs `check_motion` on the sealed manifest, then the
     motion presentation.
  7. **Assembly.** It runs the assembly round and the product renders
     (`snap/iso.png`, `snap/signature.png`). It carries the assembly review
     (`--carry-assembly-review`) and the motion review.
  8. **Final.** It runs `make_round --full` (`verify_project --print-gates
     --powered` and the rest), and the STEP export and parts.
  9. **Package.** It writes `product.json` from the sealed fields, writes
     the receipts' inputs, and runs the Make finalizer
     (`stage_proposal.py make`).
- **Every failure in a layer is reported at once (owner decision 4).**
  Within a layer, every check runs even when one fails. A layer whose inputs failed does not run.
  The model then sees every independent failure in one report.
- **What it records.** For each step it records in
  `measure/seeded-batch.json`:
  - the argv and the sha256 of the tool;
  - the exit code or signal, and the duration;
  - the paths and sha256 of every report the step wrote.
- **What it never does.**
  - It never edits a source file.
  - It never retries a failed check with other options.
  - It never decides that a failure is acceptable.
- **Deadlines.** It takes the frozen check deadlines, so one check cannot
  spend another's budget. In attempt 2 the motion sweep used up
  `verify_project`'s shared 600 s, and every print gate was recorded
  `unverified`.

This is gate execution in a fixed order, the same commands the Manager
types today. It holds no prompt, reasoning, repair or scoring. It is not an
agent framework, and the host does not loop on it (decision 4).

### 3. A passing batch accepts Make with no native turn

When every step exits 0, the host proceeds as for any Make proposal:

- it checks the finalizer's `made.json` and `agent-outcome.json`;
- it runs `verify_made_seed` with its own `proof_diff`;
- it checks the power report (ADR 0095) and the seed binding;
- it accepts Make.

The Make stage records `executor: "host-batch"`, zero native turns and zero
tokens. Release follows as today. This is the same shape as ADR 0061's
host-only Release: a stage with nothing left to decide creates no native
turn.

### 4. A failing batch invokes the native session with the exact report

- **Which failures go to the model.** When a step fails a check (exit 1,
  with its report written), the host launches the run's native session, or
  resumes it if it exists. The Make Goal is unchanged: the finalizer
  succeeds. `STAGE.json` carries `seeded_batch_failure`, which holds:
  - every failing step's argv, exit code, report path and sha256, and a
    bounded verbatim excerpt of the check's own words;
  - the steps that passed, bound by hash, which the model must not rerun.
  - the rules that still hold: seed deviations, `--record-unlock` with a
    verification quote, Component Workers, and needs for a Contract
    Contradiction.
- **Which failures stop the run instead.** A step that does not fail a
  check is a harness or environment failure, never a model task. That
  covers:
  - a signal, or an exit other than 0 and 1;
  - an import error or traceback in tool code;
  - a timeout.

  The run stops with a need for the operator, with the step's log. Examples
  from this toy: the libexpat import failure that the Manager patched with
  `LD_PRELOAD`, and `bought_model` defects #225 and #228.
- **What the model does.** It repairs only what the report names. It may
  rerun a single check to confirm the repair. Then it proposes Make as
  today.
- **The host gate on that proposal is the batch.** The host reruns the batch
  on the proposed bytes. Steps whose input hashes are unchanged reuse their
  recorded results. A failure is a host gate rejection carrying the new
  report, through the existing `host_make_proposal_rejection` path. The
  model therefore never polls long checks. Only the host loops, and it
  loops on deterministic gates, under the frozen token budget, as it
  already does on rejected proposals.

### 5. Context hygiene for the turns that remain

- **Start small.** A repair turn reads `STAGE.json` and a short
  `seeded-repair.md`. That card maps each batch step to the one reference
  section its repair needs. The turn does not read the 690-line `make.md` or
  the 850-line make-round card up front.
- **The report explains itself.** Every batch step's report must name what
  failed, where, and by how much, in words a repair can act on. A report
  that sends the model into a tool's source is a harness defect, filed as
  one. The vague `make-contract-invalid` is the first case, tracked
  separately. The run boundary already forbids reading the Workshop
  checkout. Reading materialized tool source is allowed but is measured:
  `seeded-batch.json` notes each step whose repair turn read it.
- **Component repairs go to Component Workers.** The root stays a
  dispatcher: it hands a worker the failing Component's report and its
  inputs, as ADR 0077 does, and keeps its own context near the size of the
  report. The drive-frame repair (9 calls, 37K context, 0.10 units) is the
  target shape.
- **No long waits in the model.** Long checks run in the host batch, so no
  `wait_for` poll re-reads the context while a sweep runs (26 polls, 0.47
  units in attempt 2).
- **No compaction should be needed.** A repair turn that grows past about
  60K context is itself a signal: the report was not enough.

### 6. What does not change

- **Host-verified bytes and gates.** Every gate still runs again in the run,
  on the sealed bytes, at the frozen nozzle and tool bytes. The host's own
  checks run as today: `verify_made_seed`, `proof_diff`, the power report
  binding and the seed manifest binding. The batch's records are evidence
  the host reads. They are never a substitute for those checks.
- **Seed deviations.** These work as ADR 0096 and its amendment decide:
  - a change within tolerance relocks on the approval;
  - a change over tolerance goes through one Component Worker and one
    Component Reviewer, with Shape Rounds counted;
  - every deviation is listed on the receipt and in `workshop status
    --json`, and a visible one is shown to the owner before publication.

  A deviation's review is the only model judgement that can remain in a
  seeded run, and it is the same reviewer as today.
- **The model never judges acceptance.**
  - The assembly review is carried from the owner-approved `CRITIC.json`,
    as today.
  - The motion review is carried from design (owner decision 1).
  - The batch decides nothing.
  - Acceptance is the host's, on exact bytes.
- **Frozen-run compatibility.**
  - Only new seeded runs that freeze `seed.batch` (`MAKE-OPTIONS.json`
    schema 4) get the batch.
  - Unseeded runs, runs sealed before this ADR, and resumed runs keep the
    protocol they materialized. That includes the Sunset Slider's current
    attempt.
  - A seed sealed before decision 1 lacks the inputs. It is refused for
    every new launch, `workshop wish` and `workshop fix --seed-source`
    alike, with a message that names the missing inputs and the re-seal
    path (owner decision 2). A run already started from such a seed is
    not a new launch: `workshop resume` never revalidates the seed
    directory and keeps the frozen seeded Make it materialized. That
    includes the Sunset Slider's run `wish-20261107-084342-533c8a5b`.
- **Lifecycles and runtimes.** Spark only, as ADR 0096 decides. The batch
  needs nothing from the runtime, so Codex and Claude Code behave the same.

## Expected cost

| Seeded Make of this toy | Model calls | Units |
|---|---:|---:|
| Measured, attempt 2 (root and subagents, to 15:34) | 785 | 14.81 |
| Measured, attempt 1 | 385 | 8.31 |
| Proposed, batch passes | 0 | 0 |
| Proposed, one real Component defect (the drive-frame case) | about 15-40 | about 0.3-1.2 |
| Proposed, a contract need | 0 in Make; the answer is design work | design's cost |

- **The 0.3-1.2 estimate is built from measured parts.**
  - A fresh root turn on a small context, reading `STAGE.json` and the
    report, then dispatching: 5-15 calls at 30-60K context, about 0.006-0.012
    units a call.
  - The Component Worker's repair: 0.10 units, measured.
  - A Component Review if the repair is over tolerance: 0.1-0.45 units, by
    the review subagents measured in this run (0.13-0.45 a round).
  - Host batch reruns: no tokens.
- **Design cost rises.** The Proof writes and gates the power, mount,
  placement and motion inputs, and the critic judges motion. In this run the
  same work cost 1.27 units (phases 5-6) plus part of phase 7, much of it
  reading. In design, the Proof writes them with the context it already
  has. The estimate is +1-2.5 units per powered, moving toy, and it is not
  measured. A static, unpowered toy adds almost nothing.
- **Net for a toy like this one.** About 12-14 units saved per attempt.
  There is also a further saving: an attempt that a harness defect stops
  now stops without spending model tokens, where attempt 1 spent 8.31 units
  across three such stops.
- **What this does not fix.** The rejection loop (3.49 units, 25% of
  attempt 2) is fixed separately by a precise rejection report. Under this
  ADR it would not arise on the pass path, because the finalizer runs in the
  batch. Wall-clock compute is unchanged: the same sweeps run, in the host
  instead of behind `wait_for`.

## Considered options

- **Keep the Manager, only trim its context.** This means a shorter card,
  no source reading and workers for repairs. It might halve the cost per
  call, but 221 tool-only calls and the input authoring stay. It is
  rejected as the whole answer, and kept as decision 5 for the turns that
  remain.
- **Host batch, but always start a native turn to finalize.** A cold root
  turn costs about 0.5 units just to read the stage and skill (phase 1),
  and it would re-read the batch report to agree with it. Rejected:
  nothing is left to decide on a pass.
- **Let the batch write the missing inputs.** It would derive `motion.json`
  from the spec and placements from the contract. Rejected: those are the
  toy's own numbers. Deriving them is modelling, and modelling belongs to
  the Proof, as ADR 0096 amendment item 5 decided for the spec.
- **A Python repair loop that re-prompts the model per failure.** Forbidden
  by AGENTS.md. The host here only reruns deterministic gates on a
  proposal, a path it already has for rejected proposals.

## Consequences

- **A seeded Make that passes costs compute, not tokens.** The receipt says
  "certified by host batch; 0 native turns".
- **The Approved Proof grows.** Design must run `check_power`,
  `check_mount`, `bought_model` and the motion presentation, and seal their
  inputs. This is the right place for them: a defect found there costs a
  Proof round, not a build.
- **More failures stop for the operator.** A harness defect now stops the
  run before any model spends tokens on it. That is the current practice
  for `build-a-toy` (fix the harness, refresh the tools, resume), with no
  model diagnosis first.
- **The batch is a new trusted tool.** It needs contract tests for:
  - the layer order;
  - reporting every failure within a layer;
  - classifying exits;
  - reusing a step by its input hashes;
  - refusing a seed with missing inputs;
  - frozen runs never getting it.

  Deterministic fakes are needed for CI.

## Owner decisions (2026-11-07)

1. **The motion review is judged by the Proof Critic in design** and
   carries into the run like the assembly review. A seeded batch runs no
   in-run motion critic. The sealed review must name the same concept hash
   the run's carried signature review binds, so design seals the product
   source (concept and research) the run's `spark-source.json` is composed
   from. The run's carried assembly review names its reviewer `the owner
   (Approved Proof)`, and `motion_presentation`'s carried rule needs the
   motion review to name a different one, so the Proof Critic writes it
   under its own name. `seal_proof` refuses a motion review the run could
   not carry: the owner's reviewer name, rounds outside 1 to 4, another
   concept hash or stale evidence.
2. **Seeds sealed before this ADR are refused for new launches** (option
   b). `validate_seed`, which only `workshop wish` and `workshop fix
   --seed-source` call, refuses an approval that does not record every
   check input its contract needs. The message names each missing input,
   says to re-seal through design-a-toy, and gives the re-seal path:
   `seal_proof.py inputs DIR --contract FILE` lists what is missing and
   which design step writes each, and `seal_proof.py seal` then writes an
   approval that records them. Runs already in progress keep their frozen
   rules on `workshop resume`.

   *Why (b) and not today's model-driven path.* A launch that has not
   started has spent nothing. Refusing it costs one re-seal in design,
   where the Proof's context already holds the numbers the inputs need.
   Running it would rebuild those inputs inside the run, the 4-8 units per
   attempt this ADR removes, and keep two seeded Make protocols alive for
   new runs. A run in progress has already spent its tokens and froze its
   protocol, so changing it on resume would break ADR 0096's
   frozen-run rule for no saving.
3. **The Proof writes the `product.json` title and summary**, and the
   owner sees the summary at Stage 4. The batch copies them; it composes
   no shop copy.
4. **A report carries every independent failure in its layer.** Dependent
   layers are skipped and named as skipped.
5. **`seal_proof` runs the whole batch in `--dry-run` before sealing.** The
   compute is spent in design, once per seal.
6. **Subagent tokens are counted.** Checked against the Sunset Slider run
   on 2026-11-07, read-only. The Claude adapter reads each request's usage
   from the stream, and subagent requests arrive on the same stream
   (`--forward-subagent-text`). The budget records them under the root
   invocation's one thread:
   - invocation 1 was recorded at 78.99M tokens. The transcripts give the
     root 76.94M and the subagents 1.01M by then, with the rest in
     compaction requests, which are counted through `modelUsage`;
   - the budget stop at 12:57 recorded 100.02M against 98.76M of root and
     subagent transcript usage at that time.

   "One thread" in the status is the session, not the root alone. One
   anomaly was found and is reported separately: since the operator's
   resume at 14:50 (`--max-tokens 200000000`), `native-budget.json` has
   stayed at 100,022,292 tokens and 3 invocations. Over the same time the
   transcripts show about 4.97M more root tokens and 0.29M more subagent
   tokens, and `native-progress.json` keeps updating. Usage of a resumed
   invocation may not be recorded, which would let a resumed run spend
   past its cap. Its cause is not yet known.

## Implementation status

The batch engine, seal and host merged in PR #234. The rest is on branch
`seeded-batch-complete`. All of it has deterministic-fake tests. No live
seeded build has run with the batch yet.

**Built:**

- **Seal (decisions 1 and 5, owner decisions 2 and 5).**
  - `APPROVAL.json` schema 2 records `check_inputs` {path: sha256} and
    the design batch's `batch` record.
  - `seal_proof.py inputs DIR --contract FILE` lists each required input,
    present or missing, and who writes it.
  - `seal` refuses any of these: a missing input, an invalid
    `SEED-PRODUCT.json`, a motion review the run could not carry, or a
    failing design batch.
  - `validate_seed` refuses schema 1 for new launches and names the
    re-seal path. Resume never calls it.
- **The design batch covers the run's whole batch** (`seeded_batch.design_plan`).
  Each step uses the run's own tool:
  - the project dry run;
  - the shared-helper samples (`--contract`);
  - each Component's print gates. A component round's review and seed
    nonce belong to the run.
  - each Coupled Interface's interference and motion check, run on the
    Proof's Components as they stand. This is
    `make_round --interface ID --contract FILE`: nothing is locked, so
    nothing unlocks and no round state is written. It is refused inside a
    run.
  - `bought_model --build --contract FILE`, `check_power` and
    `check_mount`. Outside a run `bought_model` reads the circuit and
    catalogue snapshot from the contract file with the parser a Wish seals
    it with, so they are the ones the run will seal (issue #241). Inside a
    run `--contract` is refused and only `WISH.json` gives them.
  - `check_motion`;
  - final verification with the run's argv plus `--design --contract
    FILE`. This runs every final gate except the signature review the run
    carries, and passes the contract file to `bought_model --final`.
    `--design` is refused inside a run (a `WISH.json` above the project),
    so the run's gate keeps that requirement, and `--design` and
    `--contract` are each refused without the other.
  - a packaging check, `seeded_package check`. Every printed occurrence of
    a multi-part package must be named for a stocked colour and resolve to
    exactly one Component STEP solid, as `parts` will export it. It writes
    nothing.

  Only the assembly round, the carried reviews, `product`, `parts` and
  the finalizer wait for the run.

  It was tried with the real tools on /tmp copies of the Sunset Slider's
  files:
  - On the Proof, four of its five Coupled Interfaces pass. `crank-slot`
    is refused because its pose table moves Components the Interface does
    not join; the seal would now surface that before a build.
  - On the finished run's CAD project, with its signature review removed,
    `verify_project --design` passes every final gate in 12 minutes, and
    `seeded_package check` resolves all 40 parts.
- **Batch engine** (`workshop.make.seeded_batch`).
  - Layers: seed, project, shared-helpers, components, interfaces, power,
    motion, assembly, final, product, parts and finalize.
  - Every independent failure in a layer is reported, and later layers
    are skipped and named (owner decision 4).
  - Exit 0 is a pass. Exit 1 without a traceback is a check failure.
    Anything else is a harness failure: a signal, another exit code, a
    timeout, a traceback, or a tool that cannot start.
  - A pass is reused only for identical argv, tool bytes and input bytes.
    A failure is never reused.
  - Final verification is judged by its report as well as its exit
    (issue #241). `verify_project` gives every geometry analysis one
    shared allowance, 600 s by default; once it is spent the analyses
    left are recorded UNVERIFIED and the command still exits 0. So the
    final step passes `--geometry-seconds`, the final layer's deadline
    less 300 s for the report (3300 s by default), and an exit 0 whose
    report's Result is not PASS (UNVERIFIED, FAIL or no Result line) is
    a harness failure in both the run's batch and the seal's.
  - The `product` step is bound to final verification's report, so a
    repair that reruns final verification is repackaged.
- **Mechanical steps** (`workshop.make.seeded_package`).
  - `prepare` copies the seed's project and installs the run's
    print-details library.
  - `product` writes `product.json`, the Spark source, the root assembled
    copies and a powered toy's README. It copies the assembly package
    from cadgen's `__cadgen__/models/<entry>.step.py/assembly.json`; the
    Sunset Slider run's Manager copied the same file by hand.
  - `parts` writes `parts/<occurrence>.step` for every printed occurrence
    of a multi-part package, so a passing multi-part build needs no model
    turn:
    - a one-solid Component STEP that passed the print gates is copied
      byte for byte, with instances sharing its bytes;
    - a labelled solid inside a multi-solid Component STEP is exported
      on its own;
    - a Bought Part is skipped;
    - an occurrence no Component holds, or more than one holds, is named
      as a check failure, and nothing is written.

    On a copy of the Sunset Slider product, it wrote all 40 parts, and
    each matches the Manager's file in volume and bounding box.
- **Host** (`workshop.workflow.seeded_batch_host`).
  - New seeded launches freeze `MAKE-OPTIONS` schema 4 with
    `seed.batch.tool_sha256`. Resume can neither add nor drop it.
  - Before a Make turn, the host runs the batch in a credential-free
    minimal environment, the same way as the native gate and release
    renders.
  - On a pass, the finalizer proposes with no native turn. A check
    failure starts the native turn with `STAGE.json`
    `inputs.seeded_batch_failure`. A harness failure stops the run with
    `last-harness-failure.json`.
  - At Make evaluation the host reruns the check layers as the gate,
    unless the passing attempt bound the same proposal bytes.
  - Seed component nonces are issued by the host (`issuer: host-batch`).
- **A powered toy's printed-only primary** (ADR 0095, 2026-11-07
  amendment) needs no extra step. For a powered toy whose sealed catalogue
  records models, the final layer's `verify_project` runs
  `bought_model.py --final`, which writes `measure/electrical/printed.step`
  and its record. A batch-finalized build therefore seals it with no
  native turn. `--design --contract FILE` writes the same file on the
  Proof; before issue #241 `--design` skipped `bought_model` silently,
  because outside a run it found no sealed circuit.
- **A re-seal sets the old `approved/` aside** (issue #241). Its copies
  are STEP files no Component builds, which the batch's project check
  refuses. `seal_proof.py seal` moves `approved/` into a hidden directory
  beside the Proof before the batch, and puts it back if the seal
  refuses, so a failed re-seal leaves the previous `APPROVAL.json` and
  `approved/` whole.
- **The Make record shows who ran the batch.**
  - The Make gate's `evidence.checks.seeded_batch` holds:
    - `executor: host-batch`;
    - `proposed_by`: `host-batch` when the batch finalized Make with no
      native turn, or `native-turn` when a repair turn proposed and the
      host reran the checks;
    - the gate (`batch-finalized` or `batch-gated`);
    - the record path and sha256;
    - the batch tool's sha256.
  - The Make receipt carries the same summary as `seeded_batch`.
  - Every printed receipt (`workshop status`, `wish`, `resume`) shows it
    in one line.
- **Product-run card.** `make-seeded.md` "When the host ran the batch".

**Still a target or a known gap:**

- **Final verification is called directly.** The final layer calls
  `verify_project` with `make_round --full`'s argv rather than
  `make_round --full --record-visual`, because no Manager visual feedback
  exists in a batch.
- **No sandbox.** The batch uses the minimal tool environment. The Claude
  adapter has no bwrap sandbox to reuse, and the batch reads no
  credentials.
- **Proofs sealed before this change need a re-seal.** A schema 1
  approval, such as the Sunset Slider's, lacks the power, mount and
  placement inputs, so its design batch fails at the power layer.
  `seal_proof.py inputs` lists each missing input.
- **The loop is tested in parts, not end to end.**
  `_seeded_batch_before_turn` and the gate are unit-tested with fakes. A
  full `workshop wish --seed-source` through Release has not run with the
  batch. It needs the owner's OK for a pilot toy.
