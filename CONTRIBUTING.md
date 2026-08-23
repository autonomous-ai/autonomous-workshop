# Contributing

This repository is a shared blueprint for autonomous inventors. The normal
contribution is one new folder under `inventors/` whose developer-defined taste
and workflow reuse Workshop instead of rebuilding infrastructure.

Start with [Build an inventor](workshop/docs/BUILD_AN_INVENTOR.md). For a new
inventor, the expected path is scaffold, customize, prove it offline, and open a
pull request.

## Set up a contribution

Generated inventors require Python 3.11 or newer.

```bash
git clone https://github.com/<your-user>/inventors.git
cd inventors
git switch -c inventor/ada-deduction-games
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e workshop
```

Use `fix/`, `docs/`, or `workshop/` as the branch prefix when that describes
the change better. Keep a pull request focused on one inventor or one coherent
Workshop contract.

## Add an inventor

Create a clean package rather than copying Alice, Bob, Eve, or an imported
snapshot:

```bash
workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

Choose `board-game`, `physical-product`, or `custom` for `--template`.

The pull request must include:

- `inventors/<inventor-id>/inventor.json` with truthful, implemented
  capabilities;
- one canonical, non-empty root `TASTE.md`;
- a README explaining the thesis, workflow, commands, evidence bar, external
  dependencies, current limitations, and live-readiness status;
- complete inventor-owned code, prompts, roles, generators, evaluators, and
  Door composition needed for the claimed behavior;
- deterministic tests and an offline smoke path that need no credentials,
  network, paid provider, CAD service, or printer;
- no runtime databases, transcripts, credentials, generated backups, or private
  keys.

Add the inventor to the table in `inventors/README.md`. A local inventor should
not use `source.kind=upstream-snapshot`; that kind is reserved for reviewed,
byte-locked imports with an `UPSTREAM.md` provenance record and snapshot lock.

## Keep the ownership boundary clear

Inventor-owned code answers:

- Who is this for?
- What does this inventor value and reject?
- Which roles, prompts, mechanisms, and experiments generate candidates?
- Which stronger niche-specific evaluators define good?
- Which verified outcomes alter future choices?

Workshop-owned code answers:

- How does Clockwork persist identity, state, leases, retries, budgets, and effects?
- How are making skills and CAD/print evidence invoked and versioned?
- How are artifacts and evidence bound to exact bytes?
- How are exact bytes Packed, Sent, and reconciled by Stamp?
- How are shared Doors tested without exposing credentials?

Put reusable infrastructure in `workshop/`, not in the new inventor. Put
taste, creative policy, and niche-specific workflow in the inventor, not in
Workshop. If a Door is generally useful, propose it as a shared Workshop
integration and keep provider-specific transport out of inventor domain logic.

## Public names

The developer-facing vocabulary is:

- `workshop` for the CLI;
- `inventor_workshop` for the Python package;
- `workshop_features` for the schema-v3 manifest’s shared-capability declaration;
- **Wish** for preserved intent;
- **Taste** for the inventor’s creative constitution;
- **Make** for generation/CAD/print work;
- **Inspect** for exact-artifact validation and evidence;
- **Pack** for reproducible transport bytes;
- **Send** for a durable outside effect;
- **Door** for a qualified external-service boundary;
- **Stamp** for evidence returned through a Door;
- **Clockwork** for state, workflow, leases, budgets, and retries.

Migration rules for historical package, manifest, and durable-data names live in
[MIGRATION.md](workshop/docs/MIGRATION.md). New contributions use the public
vocabulary above throughout code, manifests, tests, and prose.

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
python -m pip install -e ../../workshop -e .
deduction_games doctor
deduction_games make first-product
deduction_games status
python -m unittest discover -s tests -p 'test_*.py' -v
```

The generated offline Make proves the complete Taste → Make → Inspect path with
deterministic workshop fakes, binds its artifact identity, and records local
state. It is necessary but not sufficient for production readiness. Add tests
for each claimed capability, including Taste binding, deterministic agent fakes,
Make/Inspect failures, artifact identity, bounded repair, and Sender
ambiguity where those capabilities apply. A mock outcome must be visibly
identified as a mock and cannot establish live readiness.

Run the repository checks from the root:

```bash
python -m unittest discover -s workshop/tests -p 'test_*.py' -v
workshop skills list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/deduction-games --run
python workshop/tools/verify_skill_locks.py
python workshop/tools/verify_snapshot_locks.py
python workshop/tools/scan_secrets.py
git diff --check
```

Also run every test command documented by an existing inventor that your change
touches. `workshop check inventors/deduction-games --run` executes
the check commands declared by that inventor’s manifest without shell
interpolation.

## Change Workshop safely

A Workshop pull request needs contract tests in `workshop/tests/` and must
preserve the dependency direction: inventors import Workshop; Workshop
never imports an inventor.

Changes to Clockwork, budgets, artifact identity, Make or Inspect
floors, or Send effects need tests for success, malformed input,
unknown outcomes, retry/recovery, and compatibility with already persisted
data. An inventor may strengthen a gate but must not create a bypass around a
shared floor.

Keep the Python runtime usable without credentials or paid providers. Heavy CAD
dependencies and provider SDKs belong behind optional Make or Door
boundaries, with deterministic fakes for CI.

## Security, provenance, and generated files

- Never commit `.env` files, bearer tokens, API keys, cookies, private keys,
  runtime databases, transcripts, or source backups.
- Use injected credentials and distinct least-privilege inventor identities;
  never borrow a human or shared bearer for an unattended Sender effect.
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
3. shared Make, Inspect, Pack, Send, Clockwork, and Door infrastructure was reused
   rather than copied;
4. failure and ambiguity stop safely;
5. current adoption is not described as completed target architecture;
6. provenance, secrets, and durable compatibility are preserved.
