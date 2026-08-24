# Build an inventor

An inventor is an elf in the Autonomous Workshop: a durable creative identity
for one kind of plaything. The inventor supplies recognizable Taste and, only
when needed, custom Make or Playtest craft. Workshop supplies the product
journey:

```text
Wish -> Make <-> Playtest -> Docs -> Deliver
             feedback
```

This guide is for the first Workshop, which makes playthings for grown-ups
(14+). It is not a generic framework for organizers, replacement parts, or
other plain utility products.

## 1. Choose one plaything category

Every inventor starts in exactly one category:

| Category ID | Focus |
|---|---|
| `classics-made-yours` | known games and puzzles remade as exceptional custom physical editions |
| `invented-games` | new rules, mysteries, strategy, and tactile games that must earn another human play |
| `moving-machines` | mechanisms, kinetic toys, and tiny machines with satisfying motion |
| `holdable-science` | tangible phenomena, geometry, nature, space, waves, and forces |
| `little-worlds` | personalized miniature places, characters, stories, and memories |

Then apply the category bar before writing code:

- **The product could not have been downloaded before the Wish.** The Wish must
  materially change its rules, geometry, interaction, or meaning. A generic
  model with a name added is still generic.
- **Cool beats cute or twee.** Aim for clever, striking, surprising, or deeply
  satisfying. Cute may be an ingredient, never the entire idea.
- **Personalization and design intelligence beat generic prints.** The inventor
  must interpret the person and solve a real design problem.

For `classics-made-yours`, do not pretend to invent known rules. Judge the
custom edition as an object: fidelity, personalization, beauty, legibility,
handling, setup, print quality, and the way the Wish changes the edition.

For `invented-games`, simulations are necessary but never sufficient. Release
requires an independent human table that wants another play. Even 1,000 clean
AI simulations cannot pass that gate.

Kits and numbered series are possible later variants of a successful design.
They are not jobs and are not promises of the V1 Workshop.

This repository keeps exactly one canonical elf per category: Alice for
classics, Leo for invented games, Bob for moving machines, Ivy for holdable
science, and Eve for little worlds. A new experiment should not enter
`inventors/` as a sixth elf or duplicate a category; develop it separately and
propose an explicit replacement or category change.

## 2. Choose the smallest customization level

Start with the least code that can express the inventor:

| Level | Files or hooks you author | Shared behavior |
|---|---|---|
| `taste-only` | `TASTE.md` | Workshop Make and Playtest |
| `custom-make` | `TASTE.md` plus `MakeContext -> Made` | Workshop Playtest |
| `custom-playtest` | `TASTE.md`, custom Make, and `PlaytestContext -> Playtested` | Workshop still owns the feedback loop |

Workshop owns Docs, Deliver, artifact identity, evidence binding, runtime, and
truthful waiting at every level. Custom Playtest is available only with custom
Make.

Do not add a hook merely to rename phases or wrap a shared call. Add one when
the inventor has real niche logic that Taste and shared tools cannot express.

Alice, the `classics-made-yours` elf, illustrates the boundary:

```text
+----------------------- ALICE -----------------------+
| TASTE.md                                             |
| classics-made-yours; no custom job hooks            |
+--------------------------+--------------------------+
                           |
                           v
+-------------------- SHARED WORKSHOP ----------------+
| Wish -> Make <-> Playtest -> Docs -> Deliver        |
|        artifacts + feedback + evidence + runtime    |
+-----------------------------------------------------+
```

A new inventor follows this dependency shape and chooses the smallest level its
category needs; it does not copy Alice's state machine or private history.
Alice's earlier Blindcap work is Workshop provenance, while Leo is the single
active `invented-games` elf with custom Make and Playtest.

## 3. Create a thin folder

Use this repository boundary:

```text
inventors/your-id/
  TASTE.md
  README.md
  inventor.json
  profile.py             thin Workshop connection
  inventor.py            optional custom hooks only
  tests/
```

Only `TASTE.md` is creative code at the taste-only level. `profile.py` should
select a category, create typed Wishes, and construct `Workshop`; it should not
reimplement the loop.

The README must answer:

1. Which category and audience does this inventor serve?
2. What makes its output recognizable without a logo?
3. How does it turn useful Wishes into play?
4. Which customization level does it use, and why?
5. Which shared capabilities are required for a real run?
6. Which evidence classes can pass Playtest?
7. What is missing, synthetic, experimental, or blocked today?

Use a schema-v4 `inventor.json`. Its capabilities should state the category and
real custom behavior, not list every shared internal module:

```json
{
  "schema_version": 4,
  "id": "your-id",
  "name": "Your inventor name",
  "niche": "One precise plaything niche",
  "summary": "What this inventor makes differently.",
  "autonomy": "human-checkpointed",
  "status": "experimental",
  "entrypoint": ["python3", "profile.py"],
  "capabilities": ["wish", "moving-machines", "taste-only"],
  "checks": [["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]],
  "source": {"kind": "local"}
}
```

## 4. Write Taste before code

`TASTE.md` is the human-owned creative constitution. It should make two
inventors given the same Wish choose recognizably different products.

Define:

- the exact grown-up audience and play context;
- three recognizable qualities;
- familiar forms, themes, mechanics, and shortcuts to reject;
- the signature interaction or “Christmas morning” moment;
- the balance between beauty, surprise, clarity, printability, and durability;
- how useful Wishes become playful;
- which observed external evidence may justify a proposed Taste revision.

Workshop hashes the exact UTF-8 bytes. An agent may propose a Taste change, but
it may not silently edit or activate one to excuse a weak result.

Taste is direction, not evidence. “This feels fun to me” in `TASTE.md` cannot
pass a human playtest or physical test.

## 5. Connect the profile to Workshop

A taste-only profile is intentionally small:

```python
from pathlib import Path

from inventor_workshop import Wish, Workshop, WorkshopTools


INVENTOR_ROOT = Path(__file__).resolve().parent
CATEGORY = "moving-machines"  # choose one of the five category IDs


def create_wish(product_id: str, objective: str) -> Wish:
    return Wish.create(
        product_id,
        objective,
        constraints={"category": CATEGORY, "audience": "grown-ups-14-plus"},
    )


def build_workshop(shared_tools: WorkshopTools) -> Workshop:
    return Workshop(
        INVENTOR_ROOT,
        CATEGORY,
        tools=shared_tools,
        runtime_root=(INVENTOR_ROOT / ".workshop").resolve(),
    )
```

`WorkshopTools` is configured once by the Workshop operator. It contains the
shared Make, Playtest, Docs, and Deliver implementations. A profile must not
embed shared credentials or quietly fall back to a developer's personal
account.

Before running, `Workshop.preview(wish)` can show the exact Wish-, Taste-, and
category-bound Make brief without starting work.

## 6. Customize Make only when necessary

Custom Make has one stable boundary:

```python
from inventor_workshop import Made, MakeContext


def make(context: MakeContext) -> Made:
    # Use context.wish, context.taste, context.blueprint, context.feedback,
    # context.round, and the fresh context.workspace.
    # Run the inventor's real niche-specific creation here.
    ...
```

Return `Made`, containing:

- a fresh in-workspace product root;
- a content-addressed artifact manifest;
- bounded product metadata with `title`, `summary`, and the selected `category`;
- the actual rules, source, STEP, per-part meshes, assembly information, and
  other files required by that category.

The shared locked CAD and STEP-parts skills are a making recipe, not proof. Pin
the skill and tool versions actually invoked. A renderer output is not a STEP
file, and a mesh that opens is not automatically printable.

If a real model or CAD capability is unavailable, raise `WaitingFor` with a
typed `Need(job="make", ...)`. Do not write a placeholder artifact and call it
production output.

Feedback from a failed Playtest arrives in the next `MakeContext`. Make a new
revision in the new round workspace; never overwrite the revision that
produced the evidence.

Install a custom Make while retaining shared Playtest:

```python
workshop = Workshop(
    INVENTOR_ROOT,
    CATEGORY,
    tools=shared_tools,
    make=make,
    runtime_root=(INVENTOR_ROOT / ".workshop").resolve(),
)
```

## 7. Customize Playtest only for real niche expertise

Custom Playtest receives the exact `Made` revision:

```python
from inventor_workshop import PlaytestContext, Playtested


def playtest(context: PlaytestContext) -> Playtested:
    # Test context.made and seal evidence in context.workspace.
    # Return artifact-bound results and actionable Feedback.
    ...
```

It must preserve all shared guarantees while adding niche-specific checks:

- every result names the exact product artifact hash;
- every evidence reference exists with the declared hash in a sealed evidence
  manifest;
- evaluators, exact versions, configuration, and observation times are named;
- failed results include `Feedback` with an observed finding and a concrete
  requested change;
- missing capability returns `WaitingFor`, not pass;
- an inventor's model does not grade its own output as independent evidence.

Install both custom hooks for the maximum level:

```python
workshop = Workshop(
    INVENTOR_ROOT,
    CATEGORY,
    tools=shared_tools,
    make=make,
    playtest=playtest,
    runtime_root=(INVENTOR_ROOT / ".workshop").resolve(),
)
```

Workshop still owns `Make <-> Playtest`. It sends `improve` and `block`
feedback into a new Make round and stops at the configured round limit.

Choose that allowance per Wish at the trusted service boundary:

```python
result = workshop.run(wish, playtest_rounds=2)
```

The checkout or quote service may offer larger allowances for higher-priced
tiers. Do not read a self-reported dollar amount from `wish.objective` and turn
it into spend authority. If the product still fails when the allowance is
exhausted, it stops before Docs and Deliver; it does not receive a cheaper
quality bar.

## 8. Use the right evidence class

Playtest covers the whole toy or game, but a result may claim only what its
evidence observed:

- **AI simulation:** seeded traces, legal actions, termination, balance and
  pacing proxies. It cannot claim human fun.
- **Independent model review:** a reproducible prediction about clarity,
  novelty, or Taste alignment. It is not human feedback.
- **CAD/kernel measurement:** exact topology, dimensions, fit, interference,
  motion, or assembly calculations. It is not a physical test.
- **Slicer analysis:** exact meshes under a pinned printer, material, and
  profile. It predicts manufacturing; it does not prove a print succeeded.
- **Physical prototype:** exact artifact, printer, material, calibration,
  measurements, and test receipts. It proves only the recorded prototype test.
- **Human playtest:** independent participants, protocol, observed behavior,
  confusion, and feedback. Report the sample; do not generalize beyond it.

For invented games, AI players must execute the rules rather than let one model
narrate an imagined session. Rotate seats and policies, retain seeded traces,
and check termination, dead states, illegal actions, dominant strategies,
pacing, and exploits. These are useful predictions, not release evidence for
fun. The exact game must reach an independent human table, and those people
must want another play; 1,000 simulations do not substitute for that gate.

For classics made yours, verify the known rules and evaluate the exact custom
edition as an object. Do not market familiar gameplay as a new invention.

For every category, the V1 release Playtest also covers delight intent, mechanics,
printable geometry, slicing, an exact physical prototype, and independent human
use. If that evidence does not exist yet, the product waits; simulation or a
self-review cannot fill the gap.

## 9. Let shared Docs tell only the truth

Docs starts only after the exact Make passes Playtest. The shared page contract
requires distinct hero, play, detail, parts, and box images plus a
claim-to-evidence map.

The media provider must render or photograph the approved artifact. Concept art
may appear only when clearly labeled as concept art; it cannot stand in for a
product render, printed prototype, or packed box.

Copy must retain evidence qualifiers. Good copy can be magical without
inventing facts:

- say “128 seeded AI games terminated,” not “players love it”;
- say “sliced under the named profile,” not “guaranteed to print”;
- describe exactly how many independent people played and what was observed;
- keep the page private until its exact product and page hashes are approved
  for Deliver.

An inventor does not implement its own publication path. Improve shared Docs
when every inventor needs the change.

## 10. Let shared Deliver ship the exact approval

Deliver binds four kinds of evidence to the approved product and Docs:

- print receipt;
- QA receipt;
- packing receipt;
- USPS, UPS, or FedEx receipt.

A generated label is not delivery. Carrier status may advance only as far as an
authenticated observation supports. Timeouts and ambiguous effects wait for
reconciliation and are never blindly retried.

Keep printer and carrier credentials in shared provider configuration, scoped
to the minimum authority. They must never enter Taste, prompts, product files,
evidence bundles, runtime event payloads, or source.

## 11. Test failure before success

At minimum, an inventor's tests should prove:

- the root `TASTE.md` is loaded and its exact bytes are bound;
- its profile selects one valid category and the intended customization level;
- changing Taste or product bytes during a run fails closed;
- Made files stay inside the fresh round workspace;
- a failed Playtest returns actionable feedback to the next Make round;
- stale, missing, malformed, mismatched, or synthetic evidence cannot become a
  real pass;
- AI simulation cannot be presented as human-fun evidence;
- slicer output cannot be presented as a successful physical print;
- Docs claims and images remain bound to the approved product;
- changed Docs bytes cannot enter Deliver;
- missing production or carrier capability produces `WaitingFor`;
- a label, timeout, or malformed provider response cannot become delivery;
- credentials and mutable runtime state are absent from artifacts and source.

Fixtures must cross the same typed boundaries as production. Mark fixture,
offline, replay, and synthetic evidence explicitly.

## 12. Run the checks

From the inventor folder:

```bash
python -m pip install -e ../.. -e .
python -m unittest discover -s tests -p 'test_*.py' -v
```

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
workshop skills list
workshop schemas list
workshop inventors --root inventors --check-entrypoints
workshop check inventors/your-id --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
git diff --check
```

## When to improve Workshop

Move code into shared Workshop when at least two inventors need the same
invariant and it remains independent of their Taste. Keep code in the inventor
when it expresses recognizable preferences, niche generation, or stricter
niche Playtest logic.

Shared changes need credential-free contract tests, failure-path tests,
artifact and evidence binding, and backward-compatible persisted-state
handling. Older compatibility aliases may remain for existing runs, but new
inventors should learn and expose only the five jobs.
