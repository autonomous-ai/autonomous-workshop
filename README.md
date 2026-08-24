# Autonomous Workshop

Build autonomous AI inventors without rebuilding everything around them.

An inventor owns its **Taste** and the way it turns a **Wish** into something
real. Autonomous Workshop supplies the reliable making machinery: durable
state, reusable skills, exact artifacts, inspection evidence, and safe
connections to outside services.

The experience for the person making the Wish stays simple:

```text
WISH  ------------------------ WAIT ------------------------>  RECEIVE
                                |
                         the Workshop works
```

`Wait` and `Receive` are ordinary customer language, not engine stages.

## How Alice is built

Alice is one inventor. A new inventor replaces Alice's layer while reusing the
Workshop underneath it.

```text
                             ALICE
                 +---------------------------+
                 | TASTE.md                  |
WISH ----------->| prompts + creative choices|
                 | niche-specific inspection |
                 +-------------+-------------+
                               |
                               v
                 +---------------------------+
                 |         WORKSHOP          |
                 |                           |
                 |      MAKE <-> INSPECT     |
                 |        ^         |        |
                 |        + feedback+        |
                 |                           |
                 | skills · artifacts        |
                 | runtime · integrations    |
                 +-------------+-------------+
                               |
                               v
                            RECEIVE
```

Alice decides what should exist and what good feels like. The Workshop makes
the work repeatable, inspectable, recoverable, and safe to hand off. The
Workshop never imports Alice.

## Four words

| Word | Meaning |
|---|---|
| **Wish** | What someone wants, preserved as the inventor received it |
| **Taste** | The inventor's creative judgment, written in `TASTE.md` |
| **Make** | Create or revise the product |
| **Inspect** | Test the exact result and return useful feedback to Make |

That is the complete public Workshop vocabulary. Packaging bytes, recording
state, calling providers, and retaining receipts are implementation details;
they are not extra stages an inventor author has to learn.

## Repository shape

The repository *is* the Workshop, so its shared code lives at the root.
Inventor-owned code lives under `inventors/`.

```text
autonomous-workshop/
  inventors/
    alice/                   one autonomous inventor
    bob/
    <new-inventor>/          Taste, workflow, code, docs, and tests

  src/inventor_workshop/     shared Python package
  skills/                    reusable making skills
  schemas/                   portable data contracts
  docs/                      architecture and build guides
  tests/                     shared contract tests
  tools/                     repository checks
  pyproject.toml
```

The pinned upstream inventors are reference snapshots. Their provenance and
integration status are recorded in [inventors/README.md](inventors/README.md).

## Build an inventor

Generated inventors require Python 3.11 or newer.

```bash
git clone https://github.com/<your-user>/autonomous-workshop.git
cd autonomous-workshop
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

The scaffold creates a self-contained inventor:

```text
inventors/deduction-games/
  TASTE.md                 recognizable preferences and explicit rejects
  README.md                thesis, operation, limits, and commands
  inventor.json            identity and entry point
  src/deduction_games/     inventor-owned workflow and code
  tests/                   offline and failure-path checks
```

Edit `TASTE.md` and `src/deduction_games/workflow.py` first. Keep prompts,
model choices, niche judgment, and stronger niche inspections with the
inventor. Reuse Workshop for everything common.

Then prove the starter without credentials:

```bash
cd inventors/deduction-games
python -m pip install -e ../.. -e .
deduction_games doctor
deduction_games make first-product
deduction_games status
python -m unittest discover -s tests -p 'test_*.py' -v
cd ../..
```

The offline `make` is deterministic and records exact Taste, Inspection, and
artifact identities. It proves the wiring; it does not claim production CAD,
physical safety, print quality, or live fulfillment.

## What the Workshop guarantees

- Taste belongs to the inventor. Agents may propose changes; they do not
  silently rewrite `TASTE.md`.
- Unknown is not pass. Missing, stale, malformed, timed-out, or unsupported
  evidence sends the result back to Make or holds it for review.
- Inspection follows the bytes. Evidence identifies the exact artifact that
  was inspected.
- External outcomes outrank self-scores. Real prints, use, returns, and
  independent review beat generator confidence.
- Outside effects are recorded before they happen, use stable idempotency, and
  keep ambiguous outcomes for reconciliation.
- No viable product is a valid outcome. An inventor never lowers its bar just
  to preserve sunk work.

Internally, those guarantees are implemented with three plain subsystems:

```text
Artifact   immutable product identity and exact transferable bytes
Runtime    state, leases, budgets, retries, and durable outside effects
Adapter    a provider boundary that returns a verifiable receipt
```

These are implementation names, not additional steps in the invention loop.
Older `Pack`, `Send`, `Door`, `Stamp`, and `Clockwork` APIs remain readable
during migration, but new inventor code should not build its mental model
around them.

## Verify the repository

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
workshop check inventors --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
git diff --check
```

Public package names remain stable:

- distribution: `inventor-workshop`
- Python package: `inventor_workshop`
- CLI: `workshop`
- per-inventor runtime directory: `.workshop/`

Former `inventor_foundation` and `inventor_core` imports are compatibility
shims to the same implementation. They do not own separate state or behavior.

## Read next

- [Build an inventor](docs/BUILD_AN_INVENTOR.md)
- [Workshop architecture](docs/ARCHITECTURE.md)
- [Current adoption](docs/ADOPTION.md)
- [Migration guide](docs/MIGRATION.md)
- [Lessons from the inventor ecosystem](docs/ECOSYSTEM.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups,
or third-party source without documented provenance and permission.
