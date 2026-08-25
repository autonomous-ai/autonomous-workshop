# Autonomous Workshop

You wish for a toy that doesn't exist. A few days later, it arrives at your
door. Not from a shelf. From your imagination. Welcome to Autonomous Workshop,
where human and AI Inventors come together to make toys the world has never
seen.

[![A peek inside the Autonomous Workshop: how a Wish becomes a toy, from Match and Invent through Make, Playtest, Instructions, Deliver, and Reviews](docs/images/workshop-floorplan.svg)](docs/images/workshop-floorplan.svg)

## Meet some of the inventors

Here are five, one for each kind of toy. Many more are coming, and you can
[build your own](#build-your-own-inventor).

### Alice — reinvent the classics

Chess, go, dominoes, puzzles — games everyone already knows, made into a set
that is yours. Alice never touches the rules. She changes what the pieces are,
so the set is about you. It is judged as an object, not as a game.

![2030 San Francisco Chess Set](docs/images/alice-sf-chess.jpg)
*2030 San Francisco Chess Set*

### Leo — invent games that don't exist yet

Brand new games, invented for one wish: new rules, new pieces, a new reason to
sit at a table. Leo is the only inventor allowed to invent rules. Before
Instructions, his AI players must finish the required seeded games and expose
broken rules, loops, exploits, and weak strategies. Whether customers want to
play again is learned later from Reviews, after they receive the game.

https://github.com/user-attachments/assets/36ffa63e-6e36-4422-8db7-bb1545b3bdb7

*[Blindcap: Duel](https://www.autonomous.ai/factory/product/blindcap-duel)
— a two-player hidden-information strategy game of mushrooms, probes, and crowns*

### Bob — invent machines that move

Things that do one delightful thing when you wind them up, let them go, or drop
something in. No motors, no batteries, no electronics — the movement has to come
out of the shape itself. That makes this the hardest kind to get right and the
best to watch when it works.

https://github.com/user-attachments/assets/ba57de75-37e2-45e8-a71f-2a339b0de49a

*[Trotter](https://www.autonomous.ai/factory/product/spot-quadruped-robot-wind-up-walker)
— a palm-size, rubber-band-powered quadruped*

### Ivy — invent science toys you can hold

The planets, a swinging pendulum, a shape that looks impossible — real science,
small enough to pick up. Ivy says where her numbers came from and what she left
out, because here being wrong is worse than being boring.

![A solar system with its orbits engraved](docs/images/ivy-solar-system.jpg)
*A solar system with its orbits engraved — $59.99*

### Eve — invent little worlds

Your dog, your bike, your desk, your homelab — turned into a small world you can
put on a shelf. Anyone can buy a generic model of anything. Eve's only counts if
it could not have existed before your wish.

![A 1:16 Formula 1 car](docs/images/eve-f1-car.jpg)
*A 1:16 Formula 1 car*

Several inventors can make the same kind of toy in their own way, and picking
one works the same whether there are five of them or a thousand.

## Build your own inventor

Choose how much the Inventor owns, set the Playtest allowance, then create and
run it.

### 1. Choose an extension level

Start with the least you need.

| Inventor brings | Workshop supplies |
|---|---|
| **`TASTE.md`** | Make, Playtest and its feedback loop, Instructions, Deliver, storage, files, and connections |
| **`TASTE.md` + Custom Make** | Playtest and its feedback loop, Instructions, Deliver, storage, files, and connections |
| **`TASTE.md` + Custom Make + Custom Playtest** | The improvement loop around Make and Playtest, Instructions, Deliver, storage, files, and connections |

The CLI calls these levels `taste-only`, `custom-make`, and `custom-playtest`.

Custom Playtest requires Custom Make. Instructions and Deliver are always
shared. Instructions creates the in-box guide and factual content brief,
preserves the terminal `By <Inventor>.` attribution, puts a model-only handoff
in Factory as a private draft, and records authenticated draft readback before
Deliver can begin. It uploads no local marketing images and writes no final
page copy. The receipt remains `enrichment_status=pending` and
`page_ready=false` until a separate Factory content pipeline proves otherwise.
It does not make the page public or require an active listing. An owner reviews
the finished draft and may make it public later, outside the five-job pipeline.

#### Custom Make

A custom Make is one function. `workshop create inventor … --level custom-make`
writes it for you, already wired up and waiting:

```python
from inventor_workshop import Made, MakeContext, Need, WaitingFor


def make(context: MakeContext) -> Made:
    # context.wish   — the person's words, unchanged
    # context.taste  — this inventor's TASTE.md
    # context.feedback — what Playtest said last round, empty on round 1
    # context.workspace — an empty folder to write parts into
    raise WaitingFor(Need("make", "inventor-make", "not connected yet",
                          "Return a Made record bound to exact artifact bytes."))
```

Replace the wait: design the thing, write the files into `context.workspace`,
and return a `Made`. Until you do, a run stops and says what it is waiting for
instead of inventing a result.

#### Custom Playtest

A custom Playtest is the same shape. `--level custom-playtest` writes this one
too:

```python
from inventor_workshop import Playtested, PlaytestContext, Need, WaitingFor


def playtest(context: PlaytestContext) -> Playtested:
    # context.made — the exact revision to test, bytes and all
    # everything else is the same as Make
    raise WaitingFor(Need("playtest", "inventor-playtest", "not connected yet",
                          "Return Playtested evidence for the exact Make."))
```

Test the thing and return `Playtested`: the evidence, tied to the exact bytes
you were handed, plus a list of `Feedback` — a code, an area, a severity
(`note`, `improve`, or `block`), what you found, and what to change. Anything
worse than a note sends the toy back to Make with your notes in
`context.feedback`, and round 2 begins. That loop is the whole job: Make and
Playtest talking until the evidence passes or the rounds run out.

### 2. Choose the Playtest allowance

Checkout decides how many times an inventor may improve a toy before it has to
pass or stop:

```python
quick = workshop.run(wish, playtest_rounds=2)
deep = workshop.run(wish, playtest_rounds=10)
```

The words of a wish can never buy money or compute — only checkout can. Passing
early ends it early. Running out of rounds stops the toy before it is written up
or shipped. More rounds buy more tries, never an easier bar.

### 3. Create and run it

You need Python 3.9 or newer. Creating one checks the layout and runs its own
smoke tests before the inventor can receive a wish.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

workshop create inventor ada \
  --name Ada \
  --description "Choose Ada for Wish-shaped hand-cranked creatures; not static models, tabletop rules, or science explainers." \
  --lane moving-machines \
  --level custom-make \
  --root .
```

The other kinds are `classics-made-yours`, `invented-games`,
`holdable-science`, and `little-worlds`. Write a `TASTE.md` nobody could mistake
for another inventor's, then add only the custom parts it really needs.

```bash
python -m pip install -e inventors/ada
ada run --playtest-rounds 4 first-wish \
  "I wish my bicycle became a hand-cranked climbing creature"
```

With no model, CAD worker, printer, or carrier connected, a run says exactly
what it is waiting for. It never passes off a placeholder as a finished toy.

See [Build an inventor](docs/BUILD_AN_INVENTOR.md) and
[Workshop architecture](docs/ARCHITECTURE.md).

## What is in here

Shared code lives at the root. Only an inventor's taste and its own hooks live
under `inventors/`.

- `inventors/` — the first five, any you add, and each inventor's
  `toys/<toy-name>/` creations
- `src/inventor_workshop/` — picking an inventor, the five jobs, the shared runner
- `skills/` — locked CAD and STEP knowledge for making parts
- `schemas/` — the shapes files and proof have to take
- `docs/` — how it is built and how to add an inventor
- `tests/` — the rules the Workshop must never break
- `tools/` — checks for locks, provenance, and secrets

## Check it works

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
- [Build an inventor](docs/BUILD_AN_INVENTOR.md)
- [Playtest evidence](docs/PLAYTEST_EVIDENCE.md)
- [Publish the sealed showcase toys](docs/PUBLISH_SHOWCASES.md)
- [Current adoption](docs/ADOPTION.md)
- [Migration guide](docs/MIGRATION.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups, or
someone else's source without written permission and a record of where it came
from.
