# Autonomous Workshop

Santa's workshop for autonomous inventors. A person makes a Wish, waits, and
receives a box containing a playful object with a soul.

```text
PERSON       makes a wish ---------------- waits ----------------> receives a box
                    |
                    v
WORKSHOP          WISH -> MAKE <-> PLAYTEST -> DOCS -> DELIVER
                                ^          |
                                + feedback-+
```

Those five words are the complete creation pipeline. The machinery underneath
them can be sophisticated; the language every elf and developer shares should
stay simple.

## What this Workshop makes

The first Workshop makes **playthings for grown-ups (14+)**:

- tabletop games;
- desk toys;
- tiny models and characters;
- puzzles and keepsakes with play in them.

The rule is simple: a useful Wish gets the playful version. A cable holder
becomes a whale that swallows cables. A phone stand becomes a little creature
that holds the phone. Nothing is merely useful; everything should invite
curiosity, touch, surprise, or play.

## The five jobs

| Job | What the Workshop must accomplish |
|---|---|
| **Wish** | Preserve what the person asked for and bind it to the elf's exact `TASTE.md`. |
| **Make** | Invent the experience, write rules when needed, and create beautiful STEP-first printable parts. |
| **Playtest** | Test the entire product and send useful feedback back to Make until the pinned bar passes. |
| **Docs** | Create a truthful private product page with beautiful exact-product images, copy, rules, and instructions. |
| **Deliver** | Print, QA, pack, and hand the exact approved product to USPS, UPS, or FedEx. |

Playtest is intentionally broad. It covers executable AI-player simulation,
rules, fun and flow predictions, exploits, balance, CAD, fit, motion,
printability, safety, independent human use, and the exact physical prototype.
Different evidence remains different: AI players cannot prove that humans had
fun, a render cannot prove that parts fit, and a shipping label cannot prove a
carrier received the box.

## How Alice is built on the Workshop

Alice is the concrete example; every other elf uses the same dependency
direction.

```text
inventors/alice/
  TASTE.md                       what Alice loves and rejects
  profile.py                     Alice's Workshop connection
  custom Make + Playtest         Alice's tabletop-game craft
          |
          | imports
          v
+--------------------------------------------------------------------+
|                         AUTONOMOUS WORKSHOP                         |
|                                                                    |
|  Wish -> Make <---------------------> Playtest -> Docs -> Deliver   |
|           |        structured feedback       |                      |
|           |                                   |                      |
|           +-- locked CAD skills               +-- exact evidence     |
|           +-- immutable product bytes         +-- bounded repairs    |
|                                                                    |
|  durable state · budgets · leases · receipts · safe integrations   |
+--------------------------------------------------------------------+

Workshop never imports Alice. Alice imports Workshop.
```

Taste makes Alice recognizable. Workshop makes her work repeatable,
content-addressed, evidence-bound, and safe to connect to printers,
product pages, and carriers.

## Three ways to build an elf

Most developers should begin with the smallest level that expresses what is
special about their inventor.

| Level | Inventor authors | Workshop supplies |
|---|---|---|
| **Taste only** | `TASTE.md` | Make, Playtest and its improvement loop, Docs, Deliver, state, artifacts, and integrations |
| **Custom Make** | `TASTE.md` + Make hook | Shared Playtest and improvement loop, Docs, Deliver, state, artifacts, and integrations |
| **Custom Playtest** | `TASTE.md` + Make hook + Playtest hook | The loop, Docs, Deliver, state, artifacts, and integrations |

A custom Playtest requires a custom Make. Docs and Deliver remain shared so
every product page and shipment stays attached to the exact approved bytes.

The playtest allowance is chosen per Wish:

```python
result = workshop.run(wish, playtest_rounds=2)   # small tier
result = workshop.run(wish, playtest_rounds=10)  # deeper tier
```

The trusted checkout or quote service translates payment into that allowance;
free-form Wish text cannot authorize spend. The number is a maximum number of
Make–Playtest improvement rounds, not permission to weaken the bar. A design
that still fails when its allowance is exhausted stops instead of reaching
Docs or Deliver.

## The four elves

The names are internal. Customers make Wishes to the Workshop, not to an elf.

| Elf | Plaything lane | Level | What is uniquely theirs |
|---|---|---|---|
| **Alice** | Tabletop games | Custom Playtest | Hidden-information game invention, executable rules, adversarial simulation, and tabletop evidence |
| **Bob** | Desk toys | Custom Make | Mechanisms, motion, tactile rhythm, and playful versions of useful objects |
| **Eve** | Tiny models and characters | Taste only | Expressive silhouettes, tiny worlds, character, and collectibility |
| **Ivy** | Puzzles and keepsakes | Taste only | Secrets, reveals, personal meaning, and repeatable puzzle moments |

Bob's earlier board-game laboratory is preserved as migration material. His
canonical role is now desk toys, and his reusable budgeting, parallel
exploration, and reward ideas belong in Workshop so every elf can benefit.

## Repository shape

The repository itself is the Workshop. Shared code lives at the root; elf code
lives under `inventors/`.

```text
autonomous-workshop/
  inventors/
    alice/
    bob/
    eve/
    ivy/
    ...                         pinned team experiments remain references

  src/inventor_workshop/        the shared five-job runner and contracts
  skills/                       locked CAD and STEP-first making knowledge
  schemas/                      portable artifact and evidence contracts
  docs/                         architecture and elf-building guides
  tests/                        Workshop invariants and product rehearsals
  tools/                        repository, provenance, lock, and secret checks
```

Internally, the Workshop uses a few literal implementation types:

```text
Artifact   exact immutable product identity
Runtime    state, leases, budgets, retries, and durable outside effects
Adapter    one model, CAD, renderer, printer, shop, or carrier boundary
Receipt    verifiable evidence returned by that boundary
```

They are machinery, not extra jobs. Older `Pack`, `Send`, `Door`, `Stamp`,
`Clockwork`, and `Inspect` spellings remain readable only while existing Alice
and Bob code migrates.

## Build a new elf

Generated elves require Python 3.11 or newer.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

workshop new ada \
  --name Ada \
  --niche "pocket word games" \
  --lane table-game \
  --level taste-only \
  --root .
```

Start by making `inventors/ada/TASTE.md` unmistakably Ada's. The generated
profile uses the same `Workshop` class as Alice, Bob, Eve, and Ivy. With no real
model/CAD worker configured, it reports exactly what it is waiting for; it does
not pass a placeholder off as a printable product.

See [Build an elf](docs/BUILD_AN_INVENTOR.md) and
[Workshop architecture](docs/ARCHITECTURE.md).

## What the Workshop refuses to fake

- Missing, stale, malformed, timed-out, or unsupported evidence is not a pass.
- Playtest evidence follows exact product bytes across every repair.
- A changed rule or part invalidates only the evidence that depends on it, but
  no stale receipt can approve the new revision.
- Generated media is not product proof unless it depicts the exact approved
  geometry; concept art is labeled as concept art.
- External effects are recorded before execution and ambiguous outcomes wait
  for reconciliation instead of blind retry.
- “Perfect” means the pinned acceptance policy passed within bounded time,
  attempts, and budget. The elf may kill a weak idea instead of lowering the bar.

## Verify the Workshop

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root . --check-entrypoints
workshop check inventors --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
git diff --check
```

Read next:

- [Workshop architecture](docs/ARCHITECTURE.md)
- [Build an elf](docs/BUILD_AN_INVENTOR.md)
- [Current adoption](docs/ADOPTION.md)
- [Migration guide](docs/MIGRATION.md)
- [Lessons from the inventor ecosystem](docs/ECOSYSTEM.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups,
or third-party source without documented provenance and permission.
