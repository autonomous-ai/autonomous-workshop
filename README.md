# Autonomous Workshop

Build autonomous AI inventors without rebuilding the machinery around them.

An inventor owns its **Taste** and its creative workflow. The shared
**Workshop** handles durable work, 3D-making skills, inspection, exact artifact
packing, and safe connections to outside services.

The customer experience stays this simple:

```text
WISH  ------------------------- WAIT ---------------------->  RECEIVE
                         the Workshop works
```

`Wait` is not an engine stage; it is simply the person's experience while the
Workshop works. `Receive` is the handoff, and the **Box** is the physical thing
that arrives. The machinery below is for inventor developers and operators,
not customer-facing status theater.

## The blueprint: Alice

A new inventor changes the Alice layer. It reuses everything underneath.

```text
                         ALICE
              +---------------------------+
              | TASTE.md                  |  what Alice loves and rejects
WISH -------->| workflow + prompts        |  how Alice invents
              | niche-specific inspection |  Alice's higher bar
              +-------------+-------------+
                            |
                            v
     +------------------------------------------------------+
     |                    WORKSHOP                          |
     |                                                      |
     |  MAKE --------> INSPECT --------> PACK --------> SEND |
     |    |               |                |             |   |
     | Workbench       evidence         exact bytes     Door  |
     | + 3D skills     tied to bytes                    Stamp |
     |                                                      |
     |  CLOCKWORK: state · workflow · leases · budgets      |
     |             retries · effect fencing                 |
     +------------------------------------------------------+
                            |
                            v
                         RECEIVE
                        (the Box)
```

Alice decides **what should exist** and **what good feels like**. Workshop
guarantees **how the work runs, how exact bytes are inspected, and how an
outside effect is proven**. Workshop never imports Alice.

Today Alice, Bob, and Eve retain some mature inventor-local machinery while
using Workshop at real boundaries. The exact adoption—not an aspirational
claim—is recorded in [the adoption map](workshop/docs/ADOPTION.md).

## The Workshop language

The vocabulary is intentionally small.

| Word | Exact meaning |
|---|---|
| **Wish** | The request, preserved as the inventor received it |
| **Taste** | The inventor's human-owned creative constitution in `TASTE.md` |
| **Make** | Turn a Wish into manufacturable artifact bytes with `Workbench.make()` |
| **Inspect** | Check beauty, safety, printability, and readiness against those exact bytes |
| **Pack** | Seal exact artifact bytes into one reproducible `PackedArtifact` |
| **Send** | Move a Pack through a qualified outside Door with a durable outbox |
| **Door** | A typed boundary to a model, CAD tool, printer, shop, or delivery service |
| **Stamp** | Durable evidence of what actually crossed a Door |
| **Clockwork** | State, workflow, leases, budgets, retries, and effect fencing |
| **Box** | The physical outcome received by the customer |

A shop is one optional Door. An inventor can fulfill one Wish directly without
ever putting the result on a storefront.

## Build an inventor

New generated inventors require Python 3.11 or newer.

```bash
git clone https://github.com/<your-user>/autonomous-workshop.git
cd autonomous-workshop
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e workshop

workshop new deduction-games \
  --name Ada \
  --niche "two-player printable deduction games" \
  --template board-game \
  --root inventors
```

The scaffold creates one self-contained folder:

```text
inventors/deduction-games/
  TASTE.md                 recognizable preferences and explicit rejects
  README.md                thesis, operation, limits, and commands
  inventor.json            identity and genuinely used Workshop features
  src/deduction_games/     inventor-owned workflow and code
  tests/                   offline checks and failure-path tests
```

Edit `TASTE.md` and `src/deduction_games/workflow.py` first. Keep prompts,
model choices, niche judgment, and stronger niche inspections with the
inventor. Reuse Workshop rather than copying another inventor's runtime.

Then prove the starter without credentials:

```bash
cd inventors/deduction-games
python -m pip install -e ../../workshop -e .
deduction_games doctor
deduction_games make first-product
deduction_games status
python -m unittest discover -s tests -p 'test_*.py' -v
cd ../..
```

`doctor` and `status` are read-only. The offline `make` is deterministic and
records exact Taste, Inspection, and artifact identities. It proves wiring,
not production CAD, physical safety, print quality, or live fulfillment.

Before opening a pull request:

```bash
python -m unittest discover -s workshop/tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/deduction-games --run
python workshop/tools/verify_skill_locks.py
python workshop/tools/verify_snapshot_locks.py
python workshop/tools/scan_secrets.py
git diff --check
```

Read [the complete build guide](workshop/docs/BUILD_AN_INVENTOR.md) and
[CONTRIBUTING.md](CONTRIBUTING.md) before sending the PR.

## Two main folders

```text
inventors/
  alice/                   one autonomous inventor
  <new-inventor>/          Taste, workflow, code, docs, and tests

workshop/
  src/inventor_workshop/   shared Python package
  skills/                  versioned CAD and product-making skills
  schemas/                 inventor and Stamp contracts
  docs/                    architecture, build, adoption, and migration guides
  tests/                   credential-free shared contract tests
```

The repository also carries pinned upstream inventors as reference snapshots.
Their provenance and current integration status are documented in
[inventors/README.md](inventors/README.md).

## Public contract

- Distribution: `inventor-workshop`
- Python package: `inventor_workshop`
- CLI: `workshop`
- Inventor manifest: schema v3 with reviewed `workshop_features`
- Runtime directory for a clean inventor: `.workshop/`
- Durable state: `.workshop/clockwork.sqlite3`

Former `inventor_foundation` and `inventor_core` imports remain direct
compatibility shims to the same implementation. New code must not emit their
old names or create a second state authority. See
[the migration guide](workshop/docs/MIGRATION.md).

## Rules that every inventor inherits

1. **Taste belongs to the inventor.** Agents may propose a change; they do not
   silently rewrite `TASTE.md`.
2. **Unknown is not pass.** Missing, stale, malformed, timed-out, or unsupported
   evidence holds the work.
3. **Inspection follows the bytes.** Every result names the exact product
   artifact and its report must be present in a sealed evidence manifest.
   Evidence may be retained separately so the customer's Pack stays
   product-only, but both identities remain bound in Clockwork.
4. **External outcomes outrank self-scores.** Real use, prints, returns, and
   independent review beat generator confidence.
5. **Remote effects need Stamps.** A local flag or HTTP success alone proves
   neither ownership nor the requested outside state.
6. **No viable product is a valid outcome.** Never lower an inspection floor to
   preserve sunk work.

## Read next

- [Build an inventor](workshop/docs/BUILD_AN_INVENTOR.md)
- [Workshop architecture](workshop/docs/ARCHITECTURE.md)
- [Current adoption](workshop/docs/ADOPTION.md)
- [Migration from Core and Foundation](workshop/docs/MIGRATION.md)
- [Lessons from the inventor ecosystem](workshop/docs/ECOSYSTEM.md)

Never commit credentials, runtime databases, private keys, generated backups,
or third-party source without documented provenance and permission.
