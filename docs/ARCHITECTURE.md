# Autonomous Workshop architecture

Autonomous Workshop turns one person's Wish into one evidence-backed physical
product design. It is a thin workflow harness over a pluggable coding-agent
runtime, not a Python agent framework. Codex is implemented first; Claude Code
and Grok Build are future adapters to the same boundary.

## Product scope

The first version makes open-ended playthings for grown-ups (14+). Users state
what they want in their own words; they do not choose a product class before
the Workshop can begin. A universal toy blueprint supplies the shared contract
and baseline Playtest checks: `agent-playtest`, `mechanical-check`, and
`printability-check`. The host derives that exact tuple from
`ToyBlueprint.required_playtest_checks()`. These checks are Codex-authored
digital assessments unless host-replayed evidence or a physical receipt
explicitly proves more; they never establish a successful print or physical
fit by themselves. The Wish, selected Inventor, and evolving artifact determine
any additional specialist method or evidence.

Every result must be materially shaped by its Wish, feel designed rather than
decorated, and be represented no more strongly than its evidence permits.

## Lifecycle

```text
Wish -> Match -> Invent -> Make <-> Playtest -> Release -> Deliver
```

- **Wish** preserves the person's exact words and explicit constraints.
- **Match** selects and binds one Inventor for that Wish.
- **Invent** researches, explores, selects, and seals one bounded product
  concept, including the physical facts and provenance Make needs.
- **Make** consumes that exact sealed Invent result and creates the actual
  product tree, CAD project, assemblies, and deterministic CAD verification.
- **Playtest** inspects and simulates that exact Made revision. Evidence-linked
  failures return to Make within a bounded round budget.
- **Release** creates and seals a self-contained printable `MANUAL.pdf` plus
  bounded evidence-linked product facts. The manual is the canonical customer
  artifact; website publication is optional.
- **Deliver** is currently a truthful wait boundary. The host does not perform
  or claim manufacture, hands-on QA, packing, carrier handoff, or delivery.
  Those future effects require separate authorization and reconciled physical
  receipts bound to the exact approved bytes.

Release is the final digital product-design stage because the in-box experience
is part of the product. Codex owns manual structure, copy, visuals, rendering,
and revision while the host validates exact PDF and product bytes. The host
keeps authenticated Factory transport and every physical effect outside the
agent.

Customer Reviews happen after delivery and may inform a later Wish or revision.
They do not mutate a completed run.

## One Manager session per Wish

`workshop wish` first creates and populates one private persistent project at
`$WORKSHOP_HOME/runs/<wish-id>/workspace`, then starts one coding-agent session
with that directory as its working directory before Match. The same session
handles discovery, research, concept
work, CAD, inspection, repair, Playtest judgment, manual design, and bounded
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

That root session plays the Workshop Manager role. In the current adapter it is
Codex, and it may dynamically delegate bounded matching, specialist creation,
or independent inspection through standard Codex-native subagents. Those
children are part of the Manager's native agent tree; they are not separately
launched OS-level Codex processes, Python workers, or lifecycle sessions. The
root Manager receives each host stage packet, synthesizes child work, and
submits the one proposal the host verifies.

Stage names are host checkpoints, not Python workers or model roles. During
Match, the Manager may ask native children for bounded candidate-fit analysis,
then makes one evidence-based selection. The host materializes every eligible
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

For each host-authorized Match, Invent, Make, Playtest, or Release
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

Wish is sealed by the host before Match, and Deliver is a host effect boundary,
so neither is an agent Goal. A failed Playtest Goal still completes after it
finalizes truthful evidence. The host applies the round budget, invalidates
downstream evidence, and checkpoints the return to Make. Codex interprets the
feedback and repairs the product inside the next Make Goal.

## Trust boundary

### Native Codex owns

- root-session Workshop management, native subagent delegation, and synthesis;
- one active native Goal per cognitive stage attempt and the
  observe -> act -> evaluate -> improve work inside it;
- understanding the Wish and Match reasoning;
- native search and source provenance;
- concept exploration and design decisions;
- use of CAD, image-to-CAD, design-reference, STEP-parts, rendering, and other
  materialized skills;
- creation and repair of product files;
- AI Playtest perspectives and evidence-linked feedback;
- the printable `MANUAL.pdf`, evidence-bound claims, and bounded Release facts;
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

If a Playtest verdict is `improve` or `block`, the proposal returns to Make and
preserves feedback evidence. A changed Make revision invalidates old Playtest,
Release, and Deliver evidence.

## Evidence boundaries

| Evidence | May support | Does not prove |
|---|---|---|
| Native research with cited sources | factual design assumptions | that a source is current if it was not checked |
| AI simulation | executable rules, termination, measured strategy or pacing proxies | human enjoyment or comprehension |
| Independent model inspection | a recorded prediction about clarity, novelty, or Taste fit | human preference or physical behavior |
| CAD/kernel verification | topology, dimensions, required files, and exact computed geometry properties | successful physical printing or durability |
| Slicer analysis | predicted printability under an exact machine/material/profile | a successful print or surface quality |
| Structurally validated manual PDF | exact sealed customer guidance, printable pages, and extractable text | beauty, comprehension, safety certification, or a physical print |
| Host Factory receipt | reconciled optional remote draft/publication state for exact hashes | local Release success, manufacture, shipment, or delivery |
| Future Deliver receipts | the exact production, QA, packing, or carrier event observed | a later event or customer experience |
| Customer Review | what one verified recipient reported | universal preference or an earlier Playtest fact |

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. A model's confidence is never independent evidence.

## Manual-first Release and optional Factory publication

The local Release package is rooted at `artifacts/release/package` and contains
at least:

- self-contained `MANUAL.pdf`, bound to the package manifest and suitable for
  printing into the physical box;
- canonical `product.json` with exact Made/Playtest identities, concise product
  facts, what arrives, limitations, and claims copied from exact Playtest
  evidence;
- optional editable manual source or accessible text companions that do not
  contradict the PDF.

The current contract pair is NativeRelease schema v2 with `MANUAL.pdf` and
product schema v4/`manual-ready`. Legacy NativeRelease schema v1 remains
readable only with `MANUAL.md` and product schema v3/`page-ready`; the host
validates it under those original rules rather than upgrading it implicitly.

Local Release data cannot contain credentials, remote receipts, external PDF
dependencies, active content, or unsupported claims of manufacture, physical
performance, human response, publication, or delivery. Embedded fonts,
vectors, and product-derived images are valid manual content. Codex renders and
visually inspects every page; the trusted host separately parses, bounds,
rehashes, and seals the exact PDF and package. Parser success is not an
aesthetic or physical-verification score.

Local Release advances to Deliver without contacting Factory. If requested and
configured, the host may separately transport the exact sealed model,
`MANUAL.pdf`, and supported product facts, persist a hash-bound effect intent,
and require authenticated readback. Remote field limits can fail that optional
effect but cannot invalidate the local Release.

The Factory import declares the canonical `toys` category. An omitted category
would be assigned to Factory's first active category, so Workshop never relies
on that mutable ordering. Draft and public evidence are accepted only when
authenticated readback preserves the declared category slug.

The CLI default creates no publication. `--publish` records explicit
prospective authority for the host to import and promote the exact released
bytes when the adapter and credentials are available. Factory credentials are
stored outside the run in the private Workshop home, loaded only between native
turns, and never copied into the run workspace or Codex process. Missing
credentials leave publication `not-created`; a public page is never a Deliver
receipt.

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
    product/               universal blueprint and baseline checks
    wish/                  exact customer-intent contract
    match/                 Inventor roster and assignment contract/gate
    invent/                researched concept contract/gate
    make/                  Made/CAD contracts and deterministic gates
      skills/              canonical reusable Make domain skills
    playtest/              evidence, feedback, and Playtested contract/gate
    release/               local package and Release contract/gate
      skills/manual-design/ canonical printable-manual design skill
    deliver/               truthful wait boundary; future physical effects
    workflow/              lifecycle/checkpoint protocol and trusted run host
    artifacts/             immutable artifact identity
    runtime/               native session and trusted state/effect boundaries
    integrations/          host-only external adapters
    contributors/          Taste and Inventor source-manifest tooling

tests/<component>/         tests mirror component ownership

$WORKSHOP_HOME/state/<wish-id>/
                           trusted checkpoints and effects, outside agent CWD

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
