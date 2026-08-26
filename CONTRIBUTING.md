# Contributing

Autonomous Workshop is one native Codex workflow with a small trusted Python
host. Contributions should make that shared system or one declared Inventor
specialist better without creating another agent framework.

Read [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md) and
[Workshop architecture](docs/ARCHITECTURE.md) before changing the CLI, runtime,
workflow, lifecycle contracts, or product-run instructions. Read
[Build an Inventor](docs/BUILD_AN_INVENTOR.md) before adding a specialist.

## Set up the repository

Workshop requires Python 3.11 or newer. A signed-in Codex CLI is needed for a
real Wish, but repository tests are deterministic and need no model account,
Factory credential, network service, CAD service, or printer.

```bash
git clone https://github.com/<your-user>/autonomous-workshop.git
cd autonomous-workshop
git switch -c inventor/ada-deduction-games
uv sync
```

Keep a pull request focused on one Inventor or one coherent Workshop contract.
Use `fix/`, `docs/`, or `workshop/` as the branch prefix when appropriate.

## Add an Inventor

Create a new specialist from its own Taste instead of copying another
Inventor's implementation:

```bash
uv run workshop create inventor ada-deduction-games \
  --name Ada \
  --description "Choose Ada for Wish-shaped two-player deduction games; not known classics, kinetic machines, or decorative miniatures." \
  --lane invented-games \
  --root .
```

The committed bundle is intentionally small:

```text
inventors/ada-deduction-games/
├── TASTE.md
├── inventor.json
└── skills/
    └── ada-deduction-games-inventor/
        ├── SKILL.md
        ├── scripts/       # optional deterministic specialist tools
        ├── references/    # optional specialist knowledge
        └── assets/        # optional bounded source assets
```

`TASTE.md` is the creative constitution. It must state a specific audience,
recognizable qualities, explicit rejects, a signature product moment, and the
external evidence that could motivate a human-approved revision.

`inventor.json` identifies the specialist, declares its eligible lane, and
binds every inventor-owned Codex skill tree by exact content hash. Capability
claims must describe real specialist behavior, not shared Workshop stages.

The skill tells a selected native Codex subagent how to apply that Taste during
bounded Match, Invent, Make, Playtest, or Release work. Optional scripts are
tools for specialist craft. They may not launch agents, sequence stages, submit
host gates, access effect credentials, or duplicate shared Make and Playtest
machinery.

Start with instructions alone. Add scripts, dependencies, or large assets only
when they provide a genuine niche capability and have deterministic tests,
clear licensing, and a measurable evidence bar.

## Keep ownership clear

An Inventor owns:

- who the specialist is for and which Wishes it should reject;
- its distinctive judgment in `TASTE.md`;
- its concise Codex specialist skill;
- genuinely niche deterministic tools and their tests.

Workshop owns:

- Wish identity and the Match -> Invent -> Make <-> Playtest -> Release ->
  Deliver lifecycle;
- the root Codex session, checkpoint protocol, invalidation, and round budgets;
- shared CAD, artifact, evidence, schema, and publication contracts;
- credentials, authenticated effects, idempotency, receipts, and recovery.

Put reusable implementation in its owning component under `src/workshop/`,
not in an Inventor. Shared text-to-3D and CAD capabilities belong under
`src/workshop/make/skills/`. Provider transport belongs under
`src/workshop/integrations/`. The CLI only parses user commands and invokes the
host; it does not perform product reasoning.

The checked-in product-run constitution and workflow skill live under
`.agents/`. They are Runtime-owned source assets and are packaged byte-for-byte
for isolated product runs. Root `AGENTS.md` remains guidance for coding agents
building this repository.

## Public vocabulary

Use these lifecycle names consistently:

- **Wish** preserves the customer's exact intent.
- **Match** selects and binds one eligible Inventor.
- **Invent** researches and selects an industrial-design concept.
- **Make** creates the mechanical, CAD, and printable product artifacts.
- **Playtest** checks the exact Make and returns bounded repair feedback.
- **Release** creates the manual, product facts, page content, and authorized
  private Factory handoff.
- **Deliver** waits for separately authorized production, physical QA, packing,
  and carrier receipts.

Taste guides the specialist; it is not another lifecycle stage. Reviews arrive
after Deliver and may inform future work.

The distribution, Python namespace, and command are respectively
`autonomous-workshop`, `workshop`, and `workshop`. The command implementation
lives in the sibling `src/cli/` package; library code under `src/workshop/`
must not import it.

## Verification

Validate an Inventor statically. Validation reads and hashes declared files but
does not execute contributor code:

```bash
uv run workshop inventors --root inventors
uv run workshop check inventors/ada-deduction-games
```

Run repository gates from the root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py' -v
PYTHONPATH=src python -m cli skills list
PYTHONPATH=src python -m cli schemas list
python .agents/skills/autonomous-workshop/scripts/stage_proposal.py --help
python tools/verify_skill_locks.py
python tools/scan_secrets.py
python tests/packaging/installed_wheel_cli_acceptance.py
git diff --check
```

Add contract and failure-path tests in the top-level `tests/<component>/`
directory for every code change. Runtime, artifact identity, Make, Playtest,
and outside-effect changes need success, malformed-input, retry/recovery, and
ambiguous-outcome coverage. Never weaken a production gate to make a fake pass.

## Security and provenance

- Never commit `.env` files, bearer tokens, API keys, cookies, private keys,
  runtime databases, transcripts, generated backups, or customer artifacts.
- Use injected, least-privilege credentials. Native agents never receive
  Factory or other external-effect secrets.
- Record source URL, exact revision, import date, local changes, and license for
  imported code or skills in the owning component's provenance ledger.
- Update the owning deterministic lock whenever reviewed skill bytes change.
- Do not copy unlicensed source. A clean implementation may use observed public
  contracts and general engineering ideas, with that boundary documented.
- Keep generated CAD and media out of Git unless repository policy explicitly
  requires a bounded fixture.

## Pull requests

Use the pull request template. Lead with the user, Inventor, or operator
outcome; identify the owning component and highest-risk invariant; describe
implemented behavior rather than aspirations; and list the exact offline
commands that passed.

Authenticated publication or physical-delivery claims require real,
receipt-bound evidence that is safe to disclose. Mocks prove code paths only.
