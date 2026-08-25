# Contributing

This repository is a shared blueprint for autonomous inventors. The normal
contribution is one new folder under `inventors/` with a distinctive Taste and
a thin connection to the shared Workshop. Invent, Make, Playtest,
Instructions, and Deliver are already supplied; custom Make or Playtest code
is an explicit exception for genuinely niche behavior.

Start with [Build an inventor](docs/BUILD_AN_INVENTOR.md). For a new
inventor, the expected path is scaffold, customize, prove it offline, and open a
pull request.

## Set up a contribution

Generated inventors require Python 3.11 or newer.

```bash
git clone https://github.com/<your-user>/autonomous-workshop.git
cd autonomous-workshop
git switch -c inventor/ada-deduction-games
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
```

Use `fix/`, `docs/`, or `workshop/` as the branch prefix when that describes
the change better. Keep a pull request focused on one inventor or one coherent
Workshop contract.

## Add an inventor

Create a clean Taste-only package rather than copying Alice, Bob, or an
imported snapshot:

```bash
workshop create inventor deduction-games \
  --name Ada \
  --description "Choose Ada for Wish-shaped two-player deduction games; not known classics, kinetic machines, or decorative miniatures." \
  --lane invented-games \
  --level taste-only \
  --root .
```

Choose one of the five lanes documented in
[Build an inventor](docs/BUILD_AN_INVENTOR.md). Start with `taste-only`; use
`custom-make` or `custom-playtest` only when the contribution really replaces
that typed shared seam.

The pull request must include:

- `inventors/<inventor-id>/inventor.json` whose capabilities describe the
  Taste lane and actual custom behavior—not shared Workshop stages;
- one canonical, non-empty root `TASTE.md`;
- a README explaining the thesis, workflow, commands, evidence bar, external
  dependencies, current limitations, and live-readiness status;
- complete code and tests for each custom override the inventor actually
  claims; Taste-only profiles do not need their own workers, prompts,
  generators, evaluators, CAD stack, or integration composition;
- deterministic tests and an offline smoke path that need no credentials,
  network, paid provider, CAD service, or printer;
- no runtime databases, transcripts, credentials, generated backups, or private
  keys.

Add the inventor to the table in `inventors/README.md`. A local inventor should
not use `source.kind=upstream-snapshot`; that kind is reserved for reviewed,
byte-locked imports with an `UPSTREAM.md` provenance record and snapshot lock.

## Keep the ownership boundary clear

The Inventor contribution answers:

- Who is this for?
- What does this inventor value and reject?
- What makes this Taste recognizable and which Wishes should it reject?
- Does this niche truly require a custom Make or Playtest override?
- If so, what extra behavior and evidence does that override provide?

Workshop-owned code answers:

- How do shared Invent, Make/CAD, Playtest, Instructions, and Deliver run?
- How do their reward goals, feedback loops, and truthful waits work?
- How does the runtime persist identity, state, leases, retries, budgets, and effects?
- How are making skills and CAD/print evidence invoked and versioned?
- How are artifacts and evidence bound to exact bytes?
- How are outside effects recorded, executed, and reconciled by receipt?
- How are shared adapters tested without exposing credentials?

Put reusable infrastructure in its owning component under `src/workshop/`, not
in the new inventor. Put Taste and only genuinely niche override behavior in
the inventor. If an adapter is generally useful, propose it under
`src/workshop/integrations/` and keep provider-specific transport out of
inventor domain logic.

## Public names

The creation vocabulary has six jobs:

- **Wish** for preserved intent;
- **Invent** for industrial design and concept selection;
- **Make** for mechanical, CAD, and 3D design;
- **Playtest** for exact-artifact checks and feedback;
- **Instructions** for the product manual and authenticated private Factory handoff;
- **Deliver** for printing, physical QA, packing, and carrier handoff.

**Taste** is the inventor's creative constitution and guides every job; it is
not another job. Customer Reviews arrive after Deliver and may guide future
work; they are not an Inventor hook.

The distribution is `autonomous-workshop`. Use `workshop` for Python imports
and for the CLI command. The command implementation lives in the sibling
`src/cli/` package; library code under `src/workshop/` must not import it.
Artifact, runtime, adapter, and receipt are literal internal implementation
names, not more lifecycle stages. Migration rules for historical API, manifest,
and durable-data names live in [MIGRATION.md](docs/MIGRATION.md).

Use these naming roles consistently:

| Role | Form | Example |
|---|---|---|
| inventor ID and folder | kebab-case | `deduction-games` |
| Python package | snake_case | `deduction_games` |
| environment prefix | uppercase snake case | `DEDUCTION_GAMES_RUNTIME` |
| display name | human-readable text | `Ada` |

## Taste contract

The root `TASTE.md` is the canonical creative constitution. It must state a
specific audience, recognizable qualities, explicit rejects, signature product
moment, and the external evidence that can motivate a human-approved revision.

Tests must prove the workflow reads the canonical taste input before generation.
An autonomous process may propose a change but must not edit or activate taste
on its own. Avoid a second operational taste file elsewhere in the inventor;
supporting research may live under `knowledge/`, but it must not silently
supersede the root contract.

## Tests and offline evidence

From the new inventor folder, install both editable packages and run its
documented commands:

```bash
python -m pip install -e ../.. -e .
deduction_games profile
deduction_games preview first-product "I wish for a tiny deduction duel"
deduction_games run first-product "I wish for a tiny deduction duel"
python -m unittest discover -s tests -p 'test_*.py' -v
```

The generated smoke path proves discovery, exact Taste binding, shared-engine
wiring, and truthful waiting without claiming that a product was made. Add
tests for every custom capability claimed, including artifact identity,
Playtest failures, bounded repair, and outside-effect ambiguity where those
capabilities apply. A mock outcome must be visibly identified as a mock and
cannot establish live readiness.

Run the repository checks from the root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -t . -p 'test_*.py' -v
workshop skills list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/deduction-games --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
git diff --check
```

Also run every test command documented by an existing inventor that your change
touches. `workshop check inventors/deduction-games --run` executes
the check commands declared by that inventor’s manifest without shell
interpolation.

## Change Workshop safely

Read [Native coding-agent runtime](docs/NATIVE_AGENT_RUNTIME.md) before changing
the CLI, runtime, workflow, or any lifecycle stage. One native Codex session
starts immediately after Wish persistence and before Match, then owns the
cognitive work through Deliver. Python owns deterministic contracts, tools,
gates, checkpoints, and authorized effects. Do not extend the transitional
per-stage model calls or add Python planning, browsing, candidate, judge, or
repair loops.

A Workshop pull request needs contract tests in the matching component folder
under `tests/` and must preserve the dependency direction: inventors import
Workshop; Workshop never imports an inventor. For example, Make changes belong
in `src/workshop/make/` with tests in `tests/make/`; Playtest changes use
`src/workshop/playtest/` and `tests/playtest/`.

The shared component folders are `product`, `wish`, `match`, `invent`, `make`,
`playtest`, `instructions`, `deliver`, `reviews`, `workflow`, `artifacts`,
`runtime`, `integrations`, and `contributors`. Keep Make's locked knowledge in
one place at `src/workshop/make/skills/`. Put a persisted schema under the
component that owns its contract, not in a second repository-root schema tree.
Cross-component composition belongs at the Workshop bootstrap boundary rather
than inside an inventor or the CLI.

Changes to the runtime, budgets, artifact identity, Make or Playtest
floors, or outside effects need tests for success, malformed input,
unknown outcomes, retry/recovery, and compatibility with already persisted
data. An inventor may strengthen a gate but must not create a bypass around a
shared floor.

Keep the Python runtime usable without credentials or paid providers. Shared
CAD dependencies and provider SDKs belong behind explicit Workshop provider
boundaries, with deterministic fakes for CI; they do not become an Inventor's
private stack merely because a provider is unavailable.

## Security, provenance, and generated files

- Never commit `.env` files, bearer tokens, API keys, cookies, private keys,
  runtime databases, transcripts, or source backups.
- Use injected credentials and distinct least-privilege inventor identities;
  never borrow a human or shared bearer for an unattended outside effect.
- Record the source URL, exact commit, import date, exclusions, patches, and
  license status for imported code or skills.
- Do not modify an upstream snapshot silently. Update its `UPSTREAM.md` and
  snapshot lock only as part of an intentional, reviewed import.
- Keep large generated CAD/media binaries in the repository only when policy
  explicitly permits them; otherwise retain a content hash and artifact-store
  reference.

## Pull request expectations

Use the pull request template. Lead with the inventor or Workshop outcome,
then state what is implemented today, what remains a target, and the exact
offline commands that passed. Include no live-effect evidence unless it is
authenticated, receipt-bound, safe to disclose, and required for the change.

Reviewers will check that:

1. capability claims match executable code and tests;
2. the root taste contract influences the workflow;
3. shared Invent, Make, Playtest, Instructions, Deliver, artifact, runtime, and integration infrastructure was reused
   rather than copied;
4. failure and ambiguity stop safely;
5. current adoption is not described as completed target architecture;
6. provenance, secrets, and durable compatibility are preserved.
