# Autonomous Workshop architecture

Autonomous Workshop turns one person's Wish into one evidence-backed physical
product design. It is a thin workflow harness over a pluggable coding-agent
runtime, not a Python agent framework. Codex is implemented first; Claude Code
and Grok Build are future adapters to the same boundary.

## Product scope

The first version makes open-ended playthings for grown-ups (14+). Users state
what they want in their own words; they do not choose a product class before
the Workshop can begin. A universal toy blueprint supplies the shared product
contract. Spark and Forge omit Playtest truthfully; Quest activates the bounded
Playtest evidence loop. The Wish, selected Inventor,
and evolving artifact determine any additional specialist method or evidence.

Every result must be materially shaped by its Wish, feel designed rather than
decorated, and be represented no more strongly than its evidence permits.

## Lifecycle

```text
Spark: Wish -> Make -> Release
Forge: Wish -> Invent <-> Make -> Release
Quest: Wish -> Invent <-> Make <-> Playtest -> Release

Release -- handoff to Operations --> Printing -> Deliver -> Review
```

- **Wish** preserves the person's exact words and explicit constraints.
- The first active creative stage selects and binds one Inventor. Optional
  stages pass through without turns, artifacts, gates, or fabricated evidence.
- **Invent** researches, explores, selects, and seals one bounded product
  concept, including the physical facts and provenance Make needs.
- **Make** consumes that exact sealed Invent result and creates the actual
  product tree, CAD project, assemblies, and deterministic CAD verification.
  In Spark, selection and compact invention are sealed inside this same turn.
  A capable Forge or Quest Make may return to Invent only with exact preserved
  evidence that the sealed concept prevents any conforming build.
- **Playtest** independently evaluates the sealed Made revision only in Quest,
  preserving exact evidence and returning directly to Make for implementation
  defects or Invent for concept defects.
- **Release** creates and seals a self-contained printable `MANUAL.pdf`,
  revalidates the exact Made revision as full-tier print-ready CAD, and
  publishes both through Factory with authenticated public hash readback.
  The manual is the canonical customer artifact.
- **Printing**, **Deliver**, and **Review** show the rest of the product story
  after Release. They belong to the Operations team and are not executable
  Workshop stages.

Release is the final digital product-design stage because the in-box experience
is part of the product. Codex owns manual structure, copy, visuals, rendering,
and revision while the host validates exact PDF, product, and CAD bytes. The
host alone performs authenticated Factory transport. Every physical effect
remains outside both the agent and the executable Workshop lifecycle.

Customer Reviews happen after delivery and may inform a later Wish or revision.
They do not mutate a completed run.

## One Manager session per Wish

`workshop wish` first creates and populates one private persistent project at
`$WORKSHOP_HOME/runs/<wish-id>/workspace`, freezes the selected effort, then
starts one coding-agent session with that directory as its working directory
for the first enabled creative stage. The same session
handles discovery, research, concept
work, CAD, inspection, repair, manual design, and bounded
product facts. `workshop resume` continues the exact recorded session id.

Within either command, a timed-out native turn or explicitly recognized
provider disconnect automatically continues only after Workshop has both
durably bound that exact session id and proven the old launcher's dedicated
POSIX process session is empty. The host keeps the same mutation lock, stage
packet, lifecycle gate, and bounded turn/round budgets while applying capped,
deterministically jittered backoff and resuming the same session for another
turn. Other failures stop normally. The workflow consumes the launcher's typed
category rather than reclassifying public exception prose or model-authored
text; the Codex adapter recognizes transport only from an anchored,
adapter-recognized diagnostic on the private launcher channel. Product-run
tools must remain attached to the launcher's process session rather than
daemonizing or detaching. It never starts a replacement session when identity
is ambiguous.

If the installed Codex CLI is atomically upgraded during a long turn, the host
may resume the intact private checkpoint only across a strictly newer supported
version in the same major line and only when all non-runtime session bindings
remain exact. The new turn runs under the recomputed current sandbox policy.
Same-version policy changes, downgrades, and major-version changes remain
fail-closed conditions.

That root session plays the Workshop Manager role. In the current adapter it is
Codex, and it may dynamically delegate bounded selection, specialist creation,
or independent inspection through standard Codex-native subagents. Those
children are part of the Manager's native agent tree; they are not separately
launched OS-level Codex processes, Python workers, or lifecycle sessions. The
root Manager receives each host stage packet, synthesizes child work, and
submits the one proposal the host verifies.

Stage names are host checkpoints, not Python workers or model roles. During the
first enabled creative stage, the Manager may ask native children for bounded
candidate-fit analysis, then makes one evidence-based selection. The host materializes every eligible
Inventor through Codex's documented project-scoped custom-agent convention;
Codex owns native spawning, routing, waiting, and synthesis.

“Inventor” is the Workshop's friendly domain name for a standard native
subagent role. For Codex, every eligible bundle is materialized as an official
project-scoped custom agent under `.codex/agents/`.

That directory is the sole run roster. The reusable source bundle behind each
generated custom agent contains:

- `TASTE.md` defines creative judgment, preferences, and rejection boundaries;
- schema-v8 `inventor.json` defines stable source metadata and exact skill-tree
  hashes;
- the required `<id>-inventor` Codex skill tree contains `SKILL.md` for the
  specialist's primary workflow and tool routing;
- additional Inventor-prefixed skill trees are optional;
- their optional scripts, references, assets, CAD generators, evaluators, and
  other tested deterministic tools provide specialist craft.

The selected native Inventor subagent reasons and invokes those declared
resources. Custom code never becomes a prompt loop, agent scheduler, lifecycle
engine, semantic gate, or credential-bearing effect path. Child output remains
a proposal: the root Manager reviews it, and the host still verifies exact
bytes and advances the gate.

The durable toy project is the Manager's working record. Trusted host state is
kept outside that writable directory. Session memory never overrides exact
files, manifests, gate receipts, or effect receipts.

## One native Goal per active stage attempt

For each host-authorized Invent, Make, Playtest, or Release
attempt, the root Codex session creates one native Goal. Only one Goal is
active at a time. It names one objective, the exact inputs to inspect, proof
artifacts and checks, and a verifiable stopping condition: the current stage
finalizer succeeds and writes the bound proposal.

While pursuing the Goal, Codex works as observe -> act -> evaluate -> improve:
it inspects the current artifact, makes focused changes with native tools and
subagents, runs deterministic checks and independent native review, inspects
the actual output, and repeats. This is agent behavior inside the Goal, not a
separate loop primitive or Python program. The Goal completes only after the
finalizer succeeds; Codex then returns to the host instead of starting the next
stage.

Wish is sealed by the host before the first enabled stage, so it is not an agent Goal. Host gate
rejections remain bound to the exact proposal and return to the same stage for
repair; unchanged rejected bytes cannot be resubmitted as success.
Malformed Make and Playtest candidates are also recoverable without becoming
evidence: the host quarantines the exact proposal in private state, binds a
fixed failure class and feedback message into the next stage subject, and caps
each checkpoint at 32 such rejections. State conflicts and host-state tampering
still fail closed. This includes a Make tree that changes between the run-local
finalizer inventory and the host's independent readback; the stale proposal is
rejected rather than weakening exact-tree verification.

A normally completed native turn that has not written `agent-outcome.json` is
unfinished work, not a failed gate. When the exact native session checkpoint is
already bound, the host resumes the same Goal and immutable stage subject under
the command's existing 32-turn budget with a fixed reminder that the required
finalizer has not written a proposal. No proposal, attempt, or evidence is
fabricated. An unbound session or exhausted budget still fails closed.

## Trust boundary

### Native Codex owns

- root-session Workshop management, native subagent delegation, and synthesis;
- one active native Goal per cognitive stage attempt and the
  observe -> act -> evaluate -> improve work inside it;
- understanding the Wish and selecting an Inventor inside the first active stage;
- native search and source provenance;
- concept exploration and design decisions;
- use of CAD, image-to-CAD, design-reference, STEP-parts,
  electromechanical-integration, rendering, and other materialized skills;
- creation and repair of product files;
- the printable `MANUAL.pdf`, truthful omission record, and bounded Release facts;
- a compact proposal for the next host transition.

### The Python host owns

- Wish/run identity, private roots, immutable inputs, and durable checkpoints;
- validation, hashing, and resource limits for every materialized Inventor
  bundle and declared skill tree;
- legal transition order, one exclusive host mutation lock per run, round
  budgets, and invalidation;
- Codex session start/resume and environment scrubbing;
- public contracts, exact-byte manifests, deterministic CAD/evidence gates,
  and artifact sealing;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python never performs creative candidate generation, semantic judging, prompt
chaining, specialist simulation, repair reasoning, or a score/reward/feedback
loop. Codex does not advance its own gate or perform credential-bearing
effects.

## Workspace protocol

The host materializes the product-run constitution, workflow skill, Make domain
skills, Wish, generated `.codex/agents/` roster, and its hash-bound Inventor
skill trees into the persistent toy project. The workflow skill is the
Manager's playbook, not a separate Manager agent. Before each native turn the
host writes read-only `STAGE.json` with:

```text
schema_version, kind, product_id, stage, checkpoint_sha256,
subject_sha256, next_transition, round, max_rounds, inputs
```

The packet binds exact upstream contracts and canonical output paths for only
the current stage. Codex authors substantive files and then invokes the
run-local deterministic finalizer:

```text
.agents/skills/autonomous-workshop/scripts/stage_proposal.py
```

The finalizer validates authored input, hashes exact bytes, writes the
canonical stage contract, and atomically writes `agent-outcome.json`. It does
not call a model or pass a gate. The host verifies the proposal binding, rereads
the whole artifact tree, reruns trusted checks, seals accepted bytes, and alone
advances the durable checkpoint.

For new direct-Release runs, a changed Make revision invalidates Release and
must pass the full CAD gate again. Frozen pre-ADR-0015 runs retain their
materialized Playtest routing and evidence contracts; the host does not
reinterpret those historical checkpoints.

All backward transitions are explicit failed host gates and use the same
bounded lifecycle revision counter. Make-to-Invent is available only when its
contract marker was frozen into a new Forge or Quest workspace. The request
binds the exact Wish, assignment, Invented contract, authored source, and a
rehashable evidence tree. It invalidates Invent and everything downstream.
This keeps normal implementation repair inside Make, avoids an unnecessary
Make Goal when Playtest already identified a concept defect, and prevents an
old run from silently gaining a new lifecycle edge.

## Evidence boundaries

| Evidence | May support | Does not prove |
|---|---|---|
| Native research with cited sources | factual design assumptions | that a source is current if it was not checked |
| AI simulation | executable rules, termination, measured strategy or pacing proxies | human enjoyment or comprehension |
| Independent model inspection | a recorded prediction about clarity, novelty, or Taste fit | human preference or physical behavior |
| CAD/kernel verification | topology, dimensions, required files, and exact computed geometry properties | successful physical printing or durability |
| Slicer analysis | predicted printability under an exact machine/material/profile | a successful print or surface quality |
| Structurally validated manual PDF | exact sealed customer guidance, printable pages, and extractable text | beauty, comprehension, safety certification, or a physical print |
| Host Factory receipt | authenticated public publication of the exact ready-to-print CAD and manual hashes required by Release | manufacture, printing, shipment, delivery, or customer response |
| Future Operations receipts | the exact production, QA, packing, or carrier event observed | a later event or customer experience |
| Customer Review | what one verified recipient reported | universal preference or an earlier Playtest fact |

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. A model's confidence is never independent evidence.

## Manual-first terminal Release and required Factory publication

The Release package is rooted at `artifacts/release/package` and contains
at least:

- self-contained `MANUAL.pdf`, bound to the package manifest and suitable for
  printing into the physical box;
- canonical schema-v5 `product.json` with the exact Made identity, concise
  product facts, what arrives, limitations, and `playtest_status: not-run`;
- canonical `PLAYTEST-NOT-RUN.json`, with no Playtest claims;
- optional editable manual source or accessible text companions that do not
  contradict the PDF.

The current contract pair is NativeRelease schema v3 with `MANUAL.pdf` and
product schema v5/`manual-ready`. NativeRelease schema v2/product schema v4
remains valid for frozen Playtest runs. Legacy NativeRelease schema v1 remains
readable only with `MANUAL.md` and product schema v3/`page-ready`; the host
validates it under those original rules but cannot report it as a successful
current Release without an explicit migration through today's gates.

Release-authored data cannot contain credentials, remote receipts, external PDF
dependencies, active content, or unsupported claims of manufacture, physical
performance, human response, publication, or delivery. Embedded fonts,
vectors, and product-derived images are valid manual content. Codex renders and
visually inspects every page; the trusted host separately parses, bounds,
rehashes, and seals the exact PDF and package. Parser success is not an
aesthetic or physical-verification score.

After accepting those local bytes, the host reruns the full-tier CAD gate over
the exact sealed Made revision. It then transports the exact production model,
`MANUAL.pdf`, and supported product facts, persists a hash-bound effect intent,
and requires authenticated public readback. Release completes only when that
readback proves the same CAD and manual hashes. Missing credentials and typed
transient or ambiguous results leave Release waiting for reconciliation;
permanent contract or server rejections fail closed.

The Factory import declares the canonical `toys` category. An omitted category
would be assigned to Factory's first active category, so Workshop never relies
on that mutable ordering. Draft and public evidence are accepted only when
authenticated readback preserves the declared category slug.

Starting `workshop wish` authorizes this one required publication for the exact
run bytes; there is no separate publish mode. One host-owned Workshop Factory
service account publishes every Inventor's Release. Its credentials are stored
outside the run in the private Workshop home, loaded only between native turns,
and never copied into the run workspace or coding-agent process. Inventor
provenance stays in the sealed Release facts rather than being inferred from
the publisher username. Missing credentials leave Release incomplete. A public
page is the terminal digital handoff, never a printing or delivery receipt.

## Shared implementation

```text
$WORKSHOP_HOME/runs/<wish-id>/workspace/
                            private persistent project and coding-agent CWD
  .workshop-product-run-root exact Codex project/instruction boundary
  AGENTS.md                 product-run constitution
  .codex/agents/            sole run roster of project-scoped Inventor agents
  .agents/skills/           materialized workflow, stage, and Inventor skills
  artifacts/                product work and evidence

inventors/<id>/
  TASTE.md                 immutable creative point of view
  inventor.json            schema-v8 source metadata and skill-tree hashes
  skills/<id>-inventor/    required primary Codex skill tree
    SKILL.md               specialist workflow and tool routing
  skills/<id>-<specialty>/ optional additional Codex skill tree
    scripts/               optional deterministic specialist tools
    references/            optional specialist reference material
    assets/                optional immutable templates and references

.agents/
  product-run/             complete run-only toy-project template
    AGENTS.md              product-run constitution
    .agents/skills/autonomous-workshop/
                           run workflow and proposal finalizer

src/
  cli/                     parsing, presentation, and exit codes only
  workshop/
    product/               universal blueprint and compatibility check ids
    wish/                  exact customer-intent contract
    match/                 Inventor roster and assignment contract/gate
    invent/                researched concept contract/gate
    make/                  Made/CAD contracts and deterministic gates
      skills/              canonical reusable Make domain skills
    playtest/              frozen-run/future evidence contracts and gates
    release/               terminal package and Release contract/gate
      skills/manual-design/ canonical printable-manual design skill
    workflow/              lifecycle/checkpoint protocol and trusted run host
    artifacts/             immutable artifact identity
    runtime/               native session and trusted state/effect boundaries
    integrations/          host-only external adapters
    contributors/          Taste and Inventor source-manifest tooling

tests/<component>/         tests mirror component ownership

$WORKSHOP_HOME/state/<wish-id>/
                           trusted checkpoints, token totals, and effects,
                           outside agent CWD

toys/<inventor>-<slug>/    optional sanitized public examples only
```

Release owns the canonical
[`manual-design` skill](../src/workshop/release/skills/manual-design/); the host
packages its exact bytes into each product-run project.

The installed distribution is `autonomous-workshop`; application imports begin
with `workshop`. The `workshop` command lives in the sibling `src/cli/` package.
Keeping both under `src/` prevents repository tools, fixtures, and tests from
being imported accidentally.

Dependencies follow the product flow. Stage components own narrow contracts
and deterministic gates. `workflow` alone owns sequencing, and
`workflow/native_run.py` is the trusted composition root for one whole native
run. `runtime` owns session/state boundaries. `integrations` owns
credential-bearing adapters. The CLI calls Workflow's public host service and
contains no lifecycle, session, gate, effect, or product reasoning.

## Engine portability

Manager runtime support is intentionally pluggable:

| Manager runtime | Status |
|---|---|
| Codex | Implemented |
| Claude Code | Planned adapter |
| Grok Build | Planned adapter |

The adapter seam is session start/resume, native specialist delegation, and the
toy-project protocol—not the content of Codex prompts or one vendor's custom
agent format. Every future adapter must preserve the root Manager role, exact
Inventor binding, stage objective and proof condition, `STAGE.json`, exact-byte
gates, authorization, and effect isolation.
