# Autonomous Workshop architecture

Autonomous Workshop turns one person's Wish into one evidence-backed physical
product design. It is a thin workflow harness over a pluggable coding-agent
runtime, not a Python agent framework. Codex is the default Manager. The Claude
Code adapter, CLI selection, and native projection are implemented and covered
by deterministic tests; a real private Claude Wish has not yet completed the
live acceptance bar. Grok Build remains a future adapter to the same boundary.

## Product scope

The first version makes open-ended playthings for grown-ups (14+). Users state
what they want in their own words; they do not choose a product class before
the Workshop can begin. A universal toy blueprint supplies the shared contract
and baseline Playtest checks: `agent-playtest`, `mechanical-check`, and
`printability-check`. The host derives that exact tuple from
`ToyBlueprint.required_playtest_checks()`. These checks are Manager-authored
digital assessments unless host-replayed evidence or a physical receipt
explicitly proves more; they never establish a successful print or physical
fit by themselves. The Wish, selected Inventor, and evolving artifact determine
any additional specialist method or evidence.

Every result must be materially shaped by its Wish, feel designed rather than
decorated, and be represented no more strongly than its evidence permits.

## Lifecycle

```text
Wish -> Match -> Invent -> Make -> Playtest -> Release -> Deliver
                            ^          |
                            +----------+
                              feedback
```

- **Wish** preserves the person's exact words and explicit constraints.
- **Match** selects and binds one Inventor for that Wish.
- **Invent** explores and records one bounded product concept with research
  provenance where needed.
- **Make** creates the actual product tree, CAD project, assemblies, and
  deterministic CAD verification.
- **Playtest** inspects and simulates that exact Made revision. Evidence-linked
  failures return to Make within a bounded round budget.
- **Release** creates `MANUAL.md` and the complete schema-v3, `page-ready`
  product page: evidence-bound facts and claims, hero and cinematic sections,
  use case, story blocks, what arrives, limitations, and visual direction.
- **Deliver** is currently a truthful wait boundary. The host does not perform
  or claim manufacture, hands-on QA, packing, carrier handoff, or delivery.
  Those future effects require separate authorization and reconciled physical
  receipts bound to the exact approved bytes.

Release replaces the old instruction-only name because the output is broader
than a manual. The selected Manager owns the complete page copy and visual
direction while the host keeps authenticated Factory transport and publication
outside the agent.

Customer Reviews happen after delivery and may inform a later Wish or revision.
They do not mutate a completed run.

## One Manager session per Wish

`workshop wish` first creates and populates one persistent toy project under
`toys/`, then starts one coding-agent session with that directory as its working
directory before Match. The same session handles discovery, research, concept
work, CAD, inspection, repair, Playtest judgment, manual writing, and
product-page facts. `workshop resume` continues the exact recorded session id.

That root session plays the Workshop Manager role. The Wish checkpoint records
one selected runtime: Codex by default or Claude Code when requested at Wish
creation. It may dynamically delegate bounded matching, specialist creation,
or independent inspection through that runtime's native subagents. Those
children are part of the Manager's native agent tree; they are not separately
launched OS-level Manager processes, Python workers, or lifecycle sessions. The
root Manager receives each host stage packet, synthesizes child work, and
submits the one proposal the host verifies.

Stage names are host checkpoints, not Python workers or model roles. During
Match, the Manager may ask native children for bounded candidate-fit analysis,
then makes one evidence-based selection. The host materializes every eligible
Inventor through the selected runtime's project-scoped agent convention; the
Manager owns native spawning, routing, waiting, and synthesis.

“Inventor” is the Workshop's friendly domain name for a standard native
subagent role. Codex receives official project-scoped custom agents under
`.codex/agents/`; Claude Code receives namespaced agents in the explicit
host-generated plugin under `.claude/agents/`.

The Claude adapter starts `claude -p` with empty filesystem setting sources,
private `0700` home/configuration/internal-temp directories, one exact plugin,
and strict empty MCP configuration. It sends the exact current
`/goal <condition>` over standard input for each new attempt. An interrupted
attempt resumes the restored Goal with fixed continuation prose; a private
stage/checkpoint-bound sidecar prevents accidental replacement. Workshop
selects `ANTHROPIC_API_KEY` rather than the normal keychain/OAuth login path,
and init must attest that API-key source.
OS-, MDM-, and server-managed Claude settings, instructions, plugins, hooks,
and administrator policy remain part of the host trusted computing base;
Workshop does not defend against a malicious host administrator.

That directory is the sole run roster. The reusable source bundle behind each
generated custom agent contains:

- `TASTE.md` defines creative judgment, preferences, and rejection boundaries;
- schema-v8 `inventor.json` defines stable source metadata and exact skill-tree
  hashes;
- the required `<id>-inventor` portable skill tree contains `SKILL.md` for the
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

For each host-authorized Match, Invent, Make, Playtest, or Release attempt, the
root Manager session creates one native Goal using the selected runtime's goal
control. Only one Goal is active at a time. It names one objective, the exact
inputs to inspect, proof artifacts and checks, and a verifiable stopping
condition: the current stage finalizer succeeds and writes the bound proposal.

While pursuing the Goal, the Manager works as observe -> act -> evaluate ->
improve: it inspects the current artifact, makes focused changes with native
tools and subagents, runs deterministic checks and independent native review,
inspects the actual output, and repeats. This is agent behavior inside the Goal,
not a separate loop primitive or Python program. The Manager completes the
native Goal only after the finalizer succeeds, then returns to the host instead
of starting the next stage. That native return does not complete durable host
state: the host validates the exact checkpoint-bound proposal and acknowledges
any adapter Goal sidecar before mutating a gate.

Wish is sealed by the host before Match, and Deliver is a host effect boundary,
so neither is an agent Goal. A failed native Playtest Goal still completes after
it finalizes truthful evidence. The host applies the round budget, invalidates
downstream evidence, and checkpoints the return to Make. The Manager interprets
the feedback and repairs the product inside the next Make Goal.

## Trust boundary

### The selected native Manager owns

- root-session Workshop management, native subagent delegation, and synthesis;
- one active native Goal per cognitive stage attempt and the
  observe -> act -> evaluate -> improve work inside it;
- understanding the Wish and Match reasoning;
- native search and source provenance;
- concept exploration and design decisions;
- use of CAD, product-to-CAD, STEP-parts, rendering, and other materialized
  skills;
- creation and repair of product files;
- AI Playtest perspectives and evidence-linked feedback;
- `MANUAL.md`, evidence-bound claims, and complete page-ready Release content;
- a compact proposal for the next host transition.

### The Python host owns

- Wish/run identity, private roots, immutable inputs, and durable checkpoints;
- validation, hashing, and resource limits for every materialized Inventor
  bundle and declared skill tree;
- legal transition order, one exclusive host mutation lock per run, round
  budgets, and invalidation;
- selected-Manager session start/resume, policy binding, and an allowlisted
  environment;
- public contracts, exact-byte manifests, deterministic CAD/evidence gates,
  and artifact sealing;
- authorization, credential isolation, idempotency, external adapters,
  reconciliation, and receipts.

Python never performs creative candidate generation, semantic judging, prompt
chaining, specialist simulation, repair reasoning, or a score/reward/feedback
loop. The Manager does not advance its own gate or perform credential-bearing
effects.

## Workspace protocol

The host materializes the product-run constitution, workflow skill, Make domain
skills, Wish, immutable `MANAGER.json`, and exactly one selected-runtime
projection into the persistent toy project. Codex uses `.codex/agents/` and
`.agents/skills/`; Claude Code uses the explicit `.claude/` plugin with
`.claude/agents/` and `.claude/skills/`. Each projection binds the same exact
Inventor identity, Taste, and skill source bytes. The workflow skill is the
Manager's playbook, not a separate Manager agent. Before each native turn the
host writes read-only `STAGE.json` with:

```text
schema_version, kind, product_id, stage, checkpoint_sha256,
subject_sha256, next_transition, round, max_rounds, inputs
```

The packet binds exact upstream contracts and canonical output paths for only
the current stage. The Manager authors substantive files and then invokes the
run-local, standard-library finalizer at the path recorded by `MANAGER.json`:

```text
Codex:       .agents/skills/autonomous-workshop/scripts/stage_proposal.py
Claude Code: .claude/skills/autonomous-workshop/scripts/stage_proposal.py
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
| Host Factory receipt | reconciled remote draft/publication state for exact hashes | manufacture, shipment, or delivery |
| Future Deliver receipts | the exact production, QA, packing, or carrier event observed | a later event or customer experience |
| Customer Review | what one verified recipient reported | universal preference or an earlier Playtest fact |

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. A model's confidence is never independent evidence.

## Release and Factory

The local Release package is rooted at `artifacts/release/package` and contains
at least:

- substantive UTF-8 `MANUAL.md`;
- canonical schema-v3 `product.json` with `kind=workshop.release-package`,
  `status=page-ready`, exact Made/Playtest identities, `title`, `summary`,
  `hero`, `cinematic`, `use_case`, one or more `story_blocks`,
  `what_arrives`, `limitations`, and claims copied from exact Playtest evidence.
  Every page section carries `headline`, `body`, `visual_direction`, and valid
  `evidence_refs`.

Local Release data may describe the product but cannot contain credentials,
remote receipts, images, audio, video, or unsupported claims of manufacture,
physical performance, human response, publication, or delivery. The host
validates and seals the package before importing it. Factory receives the
exact sealed page, `MANUAL.md`, and model bytes; it does not creatively enrich
them. After private import, the host projects the exact compatible use-case and
story-block text into Factory's bounded rich-content fields, persists a
separate hash-bound effect intent, and requires authenticated exact readback
before publication. Copy outside Factory's documented limits is rejected, not
silently truncated. Page sections without a semantically exact Factory field
remain authoritative in the sealed project archive.

The CLI default is private. `--publish` records explicit prospective authority
for the host to promote the exact verified Factory page after private import
and authenticated readback. Factory credentials are stored outside the run in
the private Workshop home, loaded only between native turns, and never copied
into the run workspace or selected Manager process. A public page is not a
Deliver receipt.

## Shared implementation

```text
toys/<toy-id>/              persistent toy project and coding-agent CWD
  .workshop-product-run-root exact project/instruction boundary
  AGENTS.md                 Manager-neutral product-run constitution
  MANAGER.json              selected runtime and projection map
  Codex projection:
    .codex/agents/          sole run roster of Inventor agents
    .agents/skills/         workflow, Make, and Inventor skills
  Claude Code projection:
    CLAUDE.md               native pointer to AGENTS.md
    .claude/                explicit plugin with agents and skills
  artifacts/                product work and evidence

inventors/<id>/
  TASTE.md                 canonical creative point of view
  inventor.json            schema-v8 source metadata and skill-tree hashes
  skills/<id>-inventor/    required primary portable skill tree
    SKILL.md               specialist workflow and tool routing
  skills/<id>-<specialty>/ optional additional portable skill tree
    scripts/               optional deterministic specialist tools
    references/            optional specialist reference material
    assets/                optional immutable templates and references

.agents/
  product-run/             canonical Manager-neutral source bundle
    AGENTS.md              product-run constitution
    .agents/skills/autonomous-workshop/
                           portable workflow and proposal-finalizer source

src/
  cli/                     parsing, presentation, and exit codes only
  workshop/
    product/               universal blueprint and baseline checks
    wish/                  exact customer-intent contract
    match/                 Inventor roster and assignment contract/gate
    invent/                concept contract/gate
    make/                  Made/CAD contracts and deterministic gates
      skills/              canonical reusable Make domain skills
    playtest/              evidence, feedback, and Playtested contract/gate
    release/               local package and Release contract/gate
    deliver/               truthful wait boundary; future physical effects
    workflow/              lifecycle/checkpoint protocol and trusted run host
    artifacts/             immutable artifact identity
    runtime/               native session and trusted state/effect boundaries
    integrations/          host-only external adapters
    contributors/          Taste and Inventor source-manifest tooling

tests/<component>/         tests mirror component ownership

$WORKSHOP_HOME/state/<toy-id>/
                           trusted checkpoints and effects, outside agent CWD
```

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
| Claude Code | Adapter, CLI, and projection implemented; live private-Wish acceptance pending |
| Grok Build | Planned adapter |

The adapter seam is session start/resume, native specialist delegation, and the
toy-project protocol—not one runtime's prompt syntax, command flags, or custom
agent format. Every future adapter must preserve the root Manager role, exact
Inventor binding, stage objective and proof condition, `STAGE.json`, exact-byte
gates, authorization, and effect isolation.
