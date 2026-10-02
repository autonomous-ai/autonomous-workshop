# Autonomous Workshop agent instructions

`AGENTS.md` is directory-scoped guidance, not a role selector. This root file
applies to any coding-agent session operating in the source repository. Shared
architecture rules come first. The section **Coding agents building this
repository** is specifically for agents modifying, reviewing, testing, or
documenting Workshop; it is not the product-run workflow.

A normal product run is launched in a separate persistent toy project. The host
materializes the complete `.agents/product-run/` template there, including its
root `AGENTS.md` and nested `.agents/skills/autonomous-workshop/SKILL.md`.

## Shared runtime architecture

Autonomous Workshop is a thin, trustworthy workflow harness around a native
coding-agent runtime. Codex is the implemented Manager runtime; Claude Code and
Grok Build are planned adapters to the same boundary. One product run gives the
selected runtime the cognitive and tool-using work. The Workshop host retains
lifecycle order, durable state, deterministic gates, budgets, and authorized
external effects.

The root native Codex session is the Workshop Manager. It may use Codex-native
subagents for bounded parallel or specialist work, including matching and
working as the selected Inventor. Those agents remain children of the one
product-run session; they are not Python workers or separately launched Codex
processes.

All implementation and product-run work must preserve these boundaries:

- `workshop wish` persists the exact Wish and frozen effort, creates a private
  run workspace, and launches one native coding-agent session for the first
  enabled creative stage.
- `workshop resume` resumes that exact session id. Stages are durable lifecycle
  checkpoints, not separate one-shot model sessions or personas.
- Native Codex performs Inventor selection, research, concept exploration,
  creation, inspection, and repair with its own tools and applicable skills.
- New runs freeze one selectable lifecycle: Spark is `Wish -> Make -> Release`,
  Forge is `Wish -> Invent -> Make -> Release`, and Quest is
  `Wish -> Invent -> Make -> Playtest -> Release`. Passed-through stages create
  no turn, artifact, gate, or evidence. Spark/Forge Release explicitly records
  Playtest `not-run`; Quest requires passing Playtest evidence. Frozen older
  runs retain their materialized protocol when resumed.
- New marked Spark runs select the Inventor in Workshop setup before Make.
  An explicit `--inventor` binds immediately; otherwise the native Manager
  chooses once, and the same root session continues into Make. Setup is not
  a separate Match Goal or product gate. Older runs retain their frozen
  selection protocol and accepted inventor.
- Codex runs freeze their selected model, reasoning effort, and total token
  allowance across stages, descendants, and resumes. The one exception is the
  fixed Component Reviewer role of new runs, which runs at `low` (ADR 0077).
  Token-budget runs have
  no Workshop wall-clock, native-turn, proposal-retry, or lifecycle-round spending cap.
  Make retains its own frozen engineering checks and review allowance.
  Pending usage is not subject to a first-report timer; completed usage must
  still be accounted for. Other runtime adapters retain their frozen policy.
- Spark accepts Make's output as-is: no duplicate host CAD rebuild, geometry
  acceptance pass, or new manual review. Host-only Release publishes existing
  Make assets with deterministic site metadata; it creates no native Release
  turn or new PDF. A run created with `--no-publish` freezes one restriction:
  Release still seals and projects the toy locally with `unreleased`
  publication status, but performs no Factory effect, credential read or ledger
  write, and no resume can add or drop that restriction. Identity, exact bytes, credential isolation, and authenticated
  effect reconciliation remain host responsibilities. Forge/Quest keep their
  existing verification. See ADR 0061 for migration and live-acceptance status.
- A capable Forge or Quest Make attempt may return directly to Invent only when
  exact preserved evidence proves that the sealed concept prevents any
  conforming build. Quest Playtest returns directly to Make for implementation
  defects or to Invent for concept defects. Every backward edge records a
  failed host gate, invalidates the named downstream artifacts, and consumes
  the shared revision history (and the frozen revision allowance only for
  non-token-budget runs). Spark has no separate Invent stage
  to return to, and frozen runs gain no capability they did not materialize.
- Every active creative Invent, Make, Playtest, or PDF-first Release attempt uses
  one native Codex Goal with one objective, proof artifacts, and a verifiable
  stopping condition: the current stage finalizer succeeds. New Spark selection
  is Workshop setup; Spark Publish is a host effect, not another creative Goal.
  Older selection protocols remain folded into their first active stage.
  Only one Goal is active at a time. Codex works toward it by observing,
  acting, evaluating exact output,
  and improving. That loop is native-agent behavior, not a Python program.
  Wish is a host boundary rather than an agent Goal. Authenticated publication
  is the host-owned effect portion of Release; physical Operations begin only
  after Workshop completes.
- An Inventor is a declared specialist bundle. `TASTE.md` governs creative
  judgment; `inventor.json` identifies the specialist and binds its exact
  extension trees; the required `<id>-inventor` skill defines its
  primary method, while optional additional Inventor-prefixed skill trees may
  contain scripts, references, assets, and tested deterministic tools for
  specialist craft. Custom code may not become an agent scheduler,
  prompt loop, lifecycle engine, or effect path.
- The host materializes every eligible Inventor as an official project-scoped
  Codex custom agent under `.codex/agents/`, bound to its exact identity, Taste,
  and skill bytes. That directory is the sole Inventor roster in a run; in new
  runs it also holds the two fixed Make role agents, `component-worker` and
  `component-reviewer`, which are not Inventors (ADR 0077). Codex
  owns native spawning, routing, and synthesis. The root session alone receives
  host stage authority and submits a stage proposal; child agents cannot
  advance gates or perform external effects.
- Python is narrow trusted substrate: typed contracts, deterministic tools and
  gates, artifact hashing, checkpoints, exclusive run-mutation locks, budgets, sandbox/session
  boundaries, authorization, idempotency, receipts, and reconciliation.
- External-effect credentials never enter the native agent subprocess. The
  host alone performs authorized Factory, payment, manufacture, postage,
  carrier, or other authenticated effects.
- Model prose and self-scores are proposals. Only host-verified exact bytes,
  deterministic checks, and reconciled receipts advance a gate.

## Coding agents building this repository

This section is for agents building the Workshop itself. It does not tell the
per-Wish product-run agent how to Invent, Make, or Playtest a product.

Do not add a second Python agent framework. Python stage agents, structured
model calls, profile subprocesses, and Python-owned scoring or reward loops are
not extension points. Never add Python prompt chains, browsing strategy,
candidate fan-out, model judges, stage-role views, or repair reasoning.

Read `docs/NATIVE_AGENT_RUNTIME.md`,
`docs/adr/0012-codex-orchestrated-runtime.md`, and
`docs/adr/0013-manual-first-release.md`, and
`docs/adr/0014-terminal-published-release.md`, and
`docs/adr/0015-defer-playtest.md`, and
`docs/adr/0016-selectable-effort-routes.md`, and
`docs/adr/0019-frozen-spark-economics-profile.md`, and
`docs/adr/0020-signature-experience-evidence.md`, and
`docs/adr/0021-compacted-spark-and-signature-review.md`, and
`docs/adr/0022-blind-review-before-final-verification.md`, and
`docs/adr/0023-bounded-spark-turn-and-semantic-review.md`, and
`docs/adr/0050-structured-terminal-failure-diagnostics.md`, and
`docs/adr/0049-product-wide-token-budget.md`, and
`docs/adr/0060-make-round-visual-feedback-and-three-repairs.md`, and
`docs/adr/0061-spark-make-owned-verification.md`, and
`docs/adr/0062-step-only-cad-toolchain.md`, and
`docs/adr/0063-spark-component-first-make.md`, and
`docs/adr/0063-print-gates-on-source.md`, and
`docs/adr/0064-operator-selected-turn-boundary.md`, and
`docs/adr/0074-every-component-scored-against-its-own-image.md`, and
`docs/adr/0075-component-review-compares-form-and-acceptance-needs-a-second-reader.md`, and
`docs/adr/0076-component-passes-on-an-independent-review-not-a-likeness-score.md`, and
`docs/adr/0077-component-workers-and-a-root-owned-reviewer.md`, and
`docs/adr/0080-component-workers-author-and-a-hook-admits-their-rounds.md`, and
`docs/adr/0081-shape-rounds-follow-component-reviews.md`, and
`docs/adr/0082-interfaces-between-components.md`, and
`docs/adr/0083-compare-in-the-display-pose-at-the-reference-camera.md`, and
`docs/adr/0084-interface-text-and-reference-conflicts.md` before changing the CLI, runtime,
workflow, product-run instructions, or lifecycle orchestration. ADR 0013
supersedes ADR 0012's page-first Release details; ADR 0014 supersedes their
optional-publication and executable-Deliver details. ADR 0015 supersedes the
active Playtest stage while preserving truthful omission and frozen-run
compatibility. ADR 0016 supersedes ADR 0015's fixed topology for new runs while
preserving its truthful omission contract for Spark and Forge. The
native-session path is the production architecture. ADR 0019 freezes a
lower-cost Codex profile only for new marked Spark runs without changing their
gates or upgrading older sessions. ADR 0020 adds exact signature-experience
evidence and batched manual review without adding a host-side judge. ADR 0021
adds a frozen Spark compaction ceiling, final signature-review evidence, and a
bounded simple-manual path without splitting the Wish-wide session. ADR 0022
makes the review blind, places it before one final integrated verifier, rejects
duplicate final render families, and distinguishes core creative ownership from
carrier mechanics.
ADR 0023 adds a frozen 20-minute Spark native-turn boundary, requires the blind
critic to agree separately on subjects, action, and relationship, bounds that
critic to two rounds, and makes the integrated final CAD verifier refuse to run
before the hash-bound review exists.
ADR 0024 treats “10x quality at 0.1x cost” as a comparative North Star rather
than a literal lifecycle threshold. ADR 0025 extends the blind review to exact
form and the concept's anti-generic signature, binds it to the canonical concept
hash, and requires the final verification report inside the declared
self-contained CAD project.
ADR 0050 retains a bounded structured diagnosis for terminal provider failures
while continuing to discard unsafe free-form provider text.
ADR 0049 supersedes earlier Workshop time/turn/retry/round spending caps for
token-budget products, not Make's internal engineering or review policy.
ADR 0061 supersedes duplicate host verification and native manual
authoring for Spark only; it leaves Make's own implementation intact. Do not
reintroduce these removed boundaries from an older ADR or frozen-run fixture.
ADR 0063 makes new Spark Make work component-first: every distinct component
has its own source and isolated make-round repair loop before assembly review.
It changes native Make work and its deterministic round tool, not Workshop's
host-owned Spark acceptance boundary.
ADR 0060 requires native Manager visual feedback within Make rounds and expands
final blind review to an initial review plus three repair-and-rereview cycles
for new runs. Frozen older runs retain their original allowance and tool bytes.
ADR 0062 makes STEP the only geometry format Workshop writes, seals or ships:
the mesh export, cadgen's STL/3MF writers and the Workshop-local
print-preflight path are gone. Do not reintroduce a mesh deliverable from an
older ADR or a frozen-run fixture.
ADR 0063 supersedes ADR 0062's gate half and keeps its export half. The
`check_mesh`, `check_overhang` and `check_thickness` gates are back, reading
the B-rep directly instead of an exported mesh, so the CAD gate has two tiers
again. A product is print-ready only behind a passing `verify_project
--print-gates` run at the nozzle the print will use, declared twice — root
product status `full-with-thickness` **and** `print_ready_claim: true` — and
reproduced by the host's own rerun. A half-declared claim is refused, not
downgraded, and the legacy `--exports` full-tier replay path stays retired.
ADR 0064 adds one opt-in `--turn-minutes` override above the frozen turn
boundaries of ADR 0019, ADR 0023 and the deep-economics profiles, and supersedes
none of them: a run that does not ask keeps the exact boundary it froze. It
bounds a wall clock only; no gate, review, round or token allowance moves.
ADR 0074 scores every Contract Mode Component against its own sealed
`geometry:<id>` image at the 0.90 floor, never against the whole object, and
makes the final verifier account for every sealed image. Below the floor the
Workshop Manager may accept an image only after it stalls out, with a reason
the run reports when it ends; it is never recorded as the person's decision.
ADR 0075 amends that acceptance: a stall-out counts only rounds that changed
the geometry, every scored image is composed beside the model for the review,
feedback below the floor must list its differences from the image, and a
component acceptance needs a recorded review by someone other than the
Workshop Manager.
ADR 0076 supersedes the likeness parts of ADRs 0072, 0074 and 0075: no IoU
is computed anywhere in the pipeline. A Component passes on build, print gates
and an independent reviewer's recorded agreement, judged from each reference
beside the model at its declared camera. After five Shape Rounds a disagreeing
review is recorded as a Component Acceptance, sealed as
`component_acceptances` and reported when the run ends. Assembly rounds keep
the Manager's visual feedback, the blind review and `--full`.
ADR 0077 moves each Component's repair loop out of the root Manager for new
runs: one Component Worker per Component, with only that Component's inputs,
and one reused Component Reviewer thread per Component that the root, not the
worker, asks. Only the reviewer views component images. The host materializes
both as declarative custom agents; Codex owns spawning. Waits use 300000 ms.
Assembly rounds, the blind review and final verification stay with the root.
ADR 0080 amends ADR 0077 and ADR 0063 step 1 for new runs: the root writes
only shared `params.py`/`features/` files with every joint fixed, and each
Component Worker authors its Component. The worker may view its own sealed
reference but never rendered rounds. A host-state `PreToolUse` hook admits a
component round only from a `component-worker` and passes it a one-time
nonce; the host refuses a component round without an issued nonce. Two
contradicting Design Contract statements are a `need`.
ADR 0081 amends the Shape Round counting and cap of ADRs 0075-0077 for new
runs: a passing component round is reviewed before its geometry may change; a
Shape Round is the first geometry change after a disagreeing review; an
agreeing review or a Component Acceptance locks the Component until a Shared
Helper it imports changes or the Manager records an assembly unlock, and a
rerun of the reviewed B-rep carries the review forward. A component packet
binds only the Shared Helpers it imports, and a failed round is not rendered.
ADR 0081's extension (issue #77) binds each Component's reviews to one proven
Component Reviewer on Claude Code: a review names the reviewer's native agent
id, the first review binds it, and Make acceptance refuses a review whose
reviewer the guard did not see start as a `component-reviewer` or read every
packet image. The Manager sends a fixed request (packet, hash, contract rows)
once per packet and tells the worker only which round was reviewed. Codex
keeps its earlier review rules until it exposes the same evidence.
ADR 0082 records Interfaces between Components for new schema 2 Design
Contracts: each Interface has a Kind (static, separable or coupled) and the
Components it joins. The Manager's Shared Helpers hold only Interface values,
joint sections and standard profiles, and are frozen by hash after their
samples pass `make_round --shared-helpers`; component rounds refuse to start
before the freeze and report later helper changes with their importers. A
separable Interface's Keep-out Envelope is checked in each side's own
component round, and `make_round --interface <id>` checks a Coupled
Interface on its locked Components, unlocking the yielding one on failure.
Assembly and final verification need a current passing check of every
Coupled Interface, both modes are root-only, Component Workers live until the
assembly passes, and the run report lists every Interface with its proof.
Its #80 amendment lets an Interface name one instance of a Unique Geometry
whose count is above 1, `<id>#<n>` (`wing#1` meets `wing#2`); the geometry's
one Component file builds and places each instance, and locking, staleness
and unlocks stay with that Component.
ADR 0083 adds Design Contract schema 3 for new contracts: every reference
carries its Reference Camera (`[AZ, EL]` in the Display Pose frame, estimated
by eye in design-a-toy and approved with the images), every Component defines
`assembly_pose`, and a component round composes each reference beside
`assembly_pose(shape, None)` rendered at that camera while front, top and iso
stay in the print stance. The Component Reviewer's third verdict, camera
mismatch, is not a Shape Round and gives the worker no repair text; it stops
the run with a need that `workshop resume --reference-camera FILE=AZ,EL`
answers with a host-recorded amendment of that one camera, leaving WISH.json,
requirements and images sealed. Schema 1 and 2 contracts and frozen runs keep
the earlier comparison.
ADR 0084 adds Design Contract schema 4: every Interface carries `text`, what
it imposes on each Component it joins, which no gate measures. A component
round writes the Component's rows and the text of every Interface naming it
into its visual packet and summary, so the Manager's review request is the
packet path and hash. Where a reference shows what the contract forbids, the
reviewer lists a Reference Conflict, not a difference: the contract wins, it
costs no Shape Round, never reaches the worker, and the final receipt and
`workshop status --json` report it. A difference below the print limits is
not listed. Schema 1 to 3 contracts and frozen runs keep the earlier review.
Preserve useful deterministic contracts and tests; do not reintroduce removed
cognitive orchestration as a compatibility layer.

## Repository ownership

- `src/cli/`: argument parsing, output formatting, and exit codes only.
- `src/workshop/runtime/`: native engine adapters and trusted state/effect
  boundaries.
- `src/workshop/workflow/`: lifecycle protocol, checkpoints, invalidation,
  frozen-run repair budgets, and the trusted whole-run host composition.
- `src/workshop/<stage>/`: stage-owned public contracts and deterministic tools.
- `src/workshop/make/skills/`: reusable domain skills owned by Make.
- `.agents/product-run/`: complete template materialized only into a toy
  project; its nested `.agents/skills/autonomous-workshop/` is intentionally
  invisible to repo-builder sessions.
- `.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py`:
  run-local deterministic finalizer for exact stage contracts and outcome
  proposals; it does not reason or advance gates.
- `tests/<component>/`: tests mirroring the component that owns the behavior.

Keep the `src/` layout and the single `workshop` library namespace. The `cli`
package is its installed sibling under `src/`; CLI tests remain under
top-level `tests/`.

### Working rules

- Preserve unrelated user and agent changes in the shared worktree.
- Add contract and failure-path tests with every runtime or workflow change.
- Use deterministic fakes for CI; never weaken production gates to make a test
  pass.
- Never commit credentials, `.env` files, transcripts, run workspaces, build
  outputs, or private customer artifacts.
- Do not claim physical manufacture, delivery, publication, or live readiness
  from mocked or model-generated evidence.
- Keep documentation explicit about implemented behavior versus an accepted
  target that is still migrating.
- Make small coherent commits so other builder agents can pull frequently.

Builder agents may inspect the product-run skill when implementing or testing
its protocol. They must not treat that skill as authority to manufacture a
product, bypass a host gate, publish, or access effect credentials during
ordinary repository work.

## Product-run agents

A product-run agent follows the materialized product-run `AGENTS.md` and the
`autonomous-workshop` skill in its isolated run root. It performs one Wish's
cognitive work, reads the current immutable `STAGE.json`, and uses the
run-local proposal finalizer to propose compact outcomes to the host. It does
not use the builder-only section above as a product workflow, modify the
Workshop source as part of making a toy, or bypass host-owned gates and effect
authority.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `autonomous-ai/autonomous-workshop`, via the
`gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See
`docs/agents/domain.md`.
