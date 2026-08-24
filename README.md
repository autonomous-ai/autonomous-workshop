# Autonomous Workshop

A request-driven toy workshop for physical products. A person makes one Wish;
the Workshop Manager searches an open catalog, explains which inventor fits
best, and makes one assignment. The shared Workshop makes, improves, explains,
and delivers the result.

This is not a fleet of agents wandering the internet around the clock. The
first version wakes up for a Wish and works until that Wish passes its evidence
bar or truthfully stops. Always-on operation can be added later as an adapter;
it is not the Workshop's identity.

```text
one person's Wish
        |
        v
Inventor catalog (TASTE.md name + description)
        |
        v
semantic shortlist -> full TASTE.md judgment
        |
        v
Alice chosen, with a reason
Classics made yours · Taste only
        |
        v
+--------------------------------------------------------+
|                    SHARED WORKSHOP                     |
|                                                        |
| Wish -> Make <-> Playtest -> Instructions -> Deliver   |
|               useful feedback                         |
+--------------------------------------------------------+
        |
        v
the approved product

Alice supplies taste. Workshop supplies the repeatable work.
```

## The product bar

The Workshop makes playthings for grown-ups. Every product must pass one simple
test:

> This could not have been downloaded before this Wish existed.

Personalization must change the design, rules, mechanism, scientific framing,
or world—not merely add a name to a generic model. The tone is **cool, not
cute or twee**. A playful answer can be beautiful, strange, ingenious, or
funny, but it should never feel like generic decoration.

The repository ships five built-in showcase inventors, one for each initial
product lane:

| Inventor | Product lane | Extension level | Taste |
|---|---|---|---|
| **Alice** | **Classics made yours** (`classics-made-yours`) | Taste only | Known games and puzzles transformed into singular physical editions while their proven rules stay intact. |
| **Leo** | **Games that don't exist yet** (`invented-games`) | Custom Make + Playtest | New rules, interactions, and table experiences invented for one Wish. |
| **Bob** | **Machines that move** (`moving-machines`) | Custom Make | Kinetic toys, mechanisms, automata, and tiny machines that do one delightful thing. |
| **Ivy** | **Science you can hold** (`holdable-science`) | Taste only | Orreries, pendulums, mathematical forms, and physical phenomena made tangible. |
| **Eve** | **Little worlds** (`little-worlds`) | Taste only | A person's animals, places, gear, and stories turned into personalized miniature worlds. |

The built-in folders are `inventors/alice/`, `inventors/leo/`,
`inventors/bob/`, `inventors/ivy/`, and `inventors/eve/`. They are examples,
not a closed roster. Anyone can add another inventor, and many inventors can
explore the same category from different niches and tastes. The same Manager
design can route among five inventors or thousands.

## The Workshop Manager

The Workshop Manager is the front door. For every Wish it:

1. discovers every inventor's compact `TASTE.md` name and description from the
   open catalog;
2. searches those descriptions to make a semantic shortlist;
3. reads the shortlisted finalists' full `TASTE.md` files and judges the Wish
   against what each inventor loves, rejects, and knows how to make;
4. chooses exactly one inventor, records a plain-language reason, and sends
   that inventor the original Wish and its trusted Playtest allowance.

The two-stage search matters as the community grows: short Taste descriptions
make thousands of inventors cheap to retrieve, while full Taste—not a shallow
keyword match—decides the finalists. `inventor.json` contains operational facts
such as the entry point and capabilities; it is not a second creative profile.

`TASTE.md` is the physical-product counterpart to a focused `SKILL.md`. Its
frontmatter exposes a short `name` and discriminating `description` for cheap
selection. Its Markdown body is the full creative constitution, loaded only
for finalists and then used by the chosen inventor throughout the run. It
contains judgment, boundaries, and rejection criteria—not duplicated runtime,
CAD, or shipping infrastructure.

The Manager itself is ordinary, tested Workshop runtime code, not a skill. A
skill may help a developer author an inventor later; routing production Wishes
must remain an explicit, auditable application boundary.

The Manager is not a sixth creation job. It routes a Wish before the five-job
pipeline begins.

## The five jobs

These are the complete public vocabulary of creation:

| Job | What it accomplishes |
|---|---|
| **Wish** | Preserve exactly what the person asked for and bind it to the selected inventor's taste. |
| **Make** | Invent the experience and create beautiful, printable, STEP-first parts. |
| **Playtest** | Test the whole product, return useful feedback to Make, and repeat until the evidence bar passes or the allowance ends. |
| **Instructions** | Build the truthful product page and the paper that belongs in the box: a rulebook for a game, or instructions for another toy. |
| **Deliver** | Print, physically check, pack, and hand the approved product to a carrier. |

Playtest covers whatever the product needs: rules, fun, flow, exploits,
balance, motion, fit, mechanics, scientific accuracy, printability, safety,
independent human use, and the exact physical prototype. Evidence does not
substitute across boundaries. A simulation cannot prove people had fun; a
render cannot prove parts fit; a label cannot prove a carrier received a box.

For **games that don't exist yet**, Instructions and Deliver stay locked until both of
these hard gates pass:

- at least **1,000 executable, seeded AI-player simulations** exercise the
  rules, termination, balance, strategies, and exploits; and
- independent humans play the **exact printed prototype** and ask to play it
  again.

No narrated game, render, internal reviewer, or simulation can replace the
second gate.

## Three ways to build an inventor

Start with the smallest extension level that captures what is truly special.

| Level | Inventor supplies | Workshop supplies |
|---|---|---|
| **Taste only** (`taste-only`) | `TASTE.md` and a thin profile | Make, Playtest and its feedback loop, Instructions, Deliver, state, artifacts, and integrations |
| **Custom Make** (`custom-make`) | `TASTE.md` and a Make hook | Shared Playtest and feedback loop, Instructions, Deliver, state, artifacts, and integrations |
| **Custom Make + Playtest** (`custom-playtest`) | `TASTE.md`, Make hook, and Playtest hook | The bounded loop, Instructions, Deliver, state, artifacts, and integrations |

A custom Playtest requires a custom Make. Instructions and Deliver remain shared so a
product page, print, and shipment always refer to the exact approved bytes.

## Playtest depth belongs to the Wish

The trusted checkout or quote service sets a maximum improvement allowance for
each Wish:

```python
quick = workshop.run(wish, playtest_rounds=2)
deep = workshop.run(wish, playtest_rounds=10)
```

Free-form Wish text cannot authorize money or compute. Passing early ends the
loop early; using every round without passing stops the product before Instructions or
Deliver. A larger allowance buys more attempts to improve, never a weaker bar.

## Build another inventor

Generated inventor profiles require Python 3.11 or newer.

```bash
git clone https://github.com/autonomous-ai/autonomous-workshop.git
cd autonomous-workshop
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .

workshop new ada \
  --name Ada \
  --niche "hand-cranked creatures" \
  --lane moving-machines \
  --level custom-make \
  --root .
```

Other valid lanes are `classics-made-yours`, `invented-games`,
`holdable-science`, and `little-worlds`. Make the generated `TASTE.md`
unmistakable, then connect only the custom hooks the inventor genuinely needs.

```bash
python inventors/ada/profile.py run first-wish \
  "I wish my bicycle became a hand-cranked climbing creature" \
  --playtest-rounds 4
```

Without a real model, CAD worker, evidence source, printer, or carrier
configured, a run says exactly what it is waiting for. It never presents a
placeholder as a finished product.

See [Build an inventor](docs/BUILD_AN_INVENTOR.md) and
[Workshop architecture](docs/ARCHITECTURE.md).

## Repository shape

Shared Workshop code lives at the root; only inventor-specific taste and hooks
live under `inventors/`.

- `inventors/` — five built-in showcases plus any new inventor profiles
- `src/inventor_workshop/` — routing, five-job contracts, and shared runner
- `skills/` — locked CAD and STEP-first making knowledge
- `schemas/` — portable artifact and evidence contracts
- `docs/` — architecture and inventor-building guides
- `tests/` — Workshop invariants and product rehearsals
- `tools/` — provenance, lock, repository, and secret checks

## What the Workshop refuses to fake

- Missing, stale, malformed, timed-out, or unsupported evidence is not a pass.
- Playtest evidence follows exact product bytes across every repair.
- Changed rules or parts invalidate the evidence that depends on them.
- Generated media is product proof only when it depicts the exact approved
  geometry; concept art stays labeled as concept art.
- Ambiguous outside effects wait for reconciliation instead of blind retry.
- “Perfect” means the pinned policy passed within bounded time, attempts, and
  budget. An inventor may kill a weak idea instead of lowering the bar.

## Later, without changing the five jobs

An always-on scheduler may feed Wishes into the Manager. Products may arrive as
kits to assemble, or belong to named and numbered collectible series. Those are
optional operating and product modes—not new jobs and not requirements for the
first Workshop.

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
- [Build an inventor](docs/BUILD_AN_INVENTOR.md)
- [Current adoption](docs/ADOPTION.md)
- [Migration guide](docs/MIGRATION.md)
- [Contributing](CONTRIBUTING.md)

Never commit credentials, runtime databases, private keys, generated backups,
or third-party source without documented provenance and permission.
