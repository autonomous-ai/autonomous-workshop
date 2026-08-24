# Build an inventor

An inventor is a durable creative identity in the Autonomous Workshop
for one kind of plaything. The inventor supplies recognizable Taste and, only
when needed, custom Make or Playtest craft. Workshop supplies the product
journey:

```text
creation:       Wish -> Make <-> Playtest -> Instructions -> Deliver
                             feedback
after delivery: customer Reviews -> future Makes
```

The inventor participates only in the five creation jobs. Reviews is
post-delivery feedback for future work, not another hook to implement.

This guide is for the first Workshop, which makes playthings for grown-ups
(14+). It is not a generic framework for organizers, replacement parts, or
other plain utility products. An inventor is request-driven: it receives one
Wish assignment, does that work, and returns. Running a daemon, watching a
queue, or staying alive 24/7 is not part of the inventor contract.

## 1. Choose one plaything category

Every inventor starts in exactly one category:

| Category ID | Focus |
|---|---|
| `classics-made-yours` | known games and puzzles remade as exceptional custom physical editions |
| `invented-games` | new rules, mysteries, strategy, and tactile games exercised by complete AI-agent simulations |
| `moving-machines` | mechanisms, kinetic toys, and tiny machines with satisfying motion |
| `holdable-science` | tangible phenomena, geometry, nature, space, waves, and forces |
| `little-worlds` | personalized miniature places, characters, stories, and memories |

Then apply the category bar before writing code:

- **The product could not have been bought before the Wish.** The Wish must
  materially change its rules, geometry, interaction, or meaning. A generic
  model with a name added is still generic.
- **Cool beats cute or twee.** Aim for clever, striking, surprising, or deeply
  satisfying. Cute may be an ingredient, never the entire idea.
- **Personalization and design intelligence beat generic prints.** The inventor
  must interpret the person and solve a real design problem.

For `classics-made-yours`, do not pretend to invent known rules. Judge the
custom edition as an object: fidelity, personalization, beauty, legibility,
handling proxies, setup, digital printability, and the way the Wish changes the
edition.

For `invented-games`, AI players must execute at least 1,000 complete seeded
games and probe endings, balance, strategies, illegal actions, and exploits.
Whether customers want another play is learned after delivery through Reviews
and can shape a future revision of the same toy as well as future Wishes and
Makes; it is not a Playtest gate for the original order.

Kits and numbered series are possible later variants of a successful design.
They are not jobs and are not promises of the V1 Workshop.

This checkout starts with five showcase inventors: Alice for classics, Leo for
invented games, Bob for moving machines, Ivy for holdable science, and Eve for
little worlds. They demonstrate the five categories and three extension
levels; they are not a closed roster. Anyone may add an inventor, and many
inventors may serve the same category with different niches and Taste.

### How the Workshop Manager chooses

The Workshop Manager is the Workshop's front door. For one untouched Wish, it
discovers the compact `name` and `description` header in every `TASTE.md`. A
semantic retriever records a bounded shortlist; the Manager then loads the
complete, exact Taste body only for those finalists and asks a semantic judge
to assess each one. It creates one assignment bound to the Wish, catalog
snapshot, retrieval receipt, finalist Taste hashes and ranking, selected entry
point, and trusted Playtest-round allowance.

This is not category routing by keyword. “A moving solar system for my desk,”
for example, may have real tensions between motion and science inventors. The
retriever must preserve those plausible alternatives, and the judge must read
their Tastes in full and explain the choice. A tie is resolved deterministically.
If every finalist rejects the Wish, the Manager waits for clarification, wider
retrieval, or a genuinely new Taste instead of forcing a bad match.

The Manager is not a sixth job. Once assigned, the Wish still follows only:

```text
creation:       Wish -> Make <-> Playtest -> Instructions -> Deliver
                             feedback
after delivery: customer Reviews -> future Makes
```

A future always-on intake service can call the same one-Wish Manager repeatedly.
That optional scheduler belongs outside inventor folders; it does not change
the profile contract or the Workshop vocabulary.

The Manager is Workshop runtime code, not a skill. `TASTE.md` borrows a skill's
progressive-disclosure design; the routing service remains explicit and tested
so application code, not an implicit host prompt, owns the assignment.

## 2. Choose the smallest customization level

Start with the least code that can express the inventor:

| Level | Files or hooks you author | Shared behavior |
|---|---|---|
| `taste-only` | `TASTE.md` | Workshop Make and Playtest |
| `custom-make` | `TASTE.md` plus `MakeContext -> Made` | Workshop Playtest |
| `custom-playtest` | `TASTE.md`, custom Make, and `PlaytestContext -> Playtested` | Workshop still owns the feedback loop |

Workshop owns Instructions, Deliver, artifact identity, evidence binding, runtime, and
truthful waiting at every level. Custom Playtest is available only with custom
Make.

Do not add a hook merely to rename phases or wrap a shared call. Add one when
the inventor has real niche logic that Taste and shared tools cannot express.

Alice, the `classics-made-yours` inventor, illustrates the boundary:

```text
+----------------------- ALICE -----------------------+
| TASTE.md                                             |
| classics-made-yours; no custom job hooks            |
+--------------------------+--------------------------+
                           |
                           v
+-------------------- SHARED WORKSHOP ----------------+
| Wish -> Make <-> Playtest -> Instructions -> Deliver        |
|        artifacts + feedback + evidence + runtime    |
+-----------------------------------------------------+
                           |
                           v
                 Reviews -> future Makes
```

A new inventor follows this dependency shape and chooses the smallest level its
category needs; it does not copy Alice's state machine or private history.
Alice's earlier Blindcap work is Workshop provenance, while Leo is the bundled
`invented-games` example with custom Make and Playtest.

## 3. Create your inventor

The canonical creator writes the thin folder, validates its schema-v5 identity,
runs its smoke checks, and only then lets it join the Manager's catalog:

```bash
workshop create inventor ada \
  --description "Choose Ada for Wish-shaped hand-cranked creatures; not static models, tabletop rules, or science explainers." \
  --lane moving-machines
```

`--name` defaults to the inventor ID in title case, and `--level` defaults to
`taste-only`. Choose `custom-make` or `custom-playtest` only when the inventor
really owns that typed creative seam. `--json` returns a versioned receipt with
the exact Taste, manifest, and catalog hashes for an agent or another tool.

The routing description is not a slogan. Say what should choose this inventor
and name the nearest work it must reject. After creation, edit the full
`TASTE.md` body until the inventor has an unmistakable point of view.

The generated repository boundary is:

```text
inventors/your-id/
  TASTE.md
  README.md
  inventor.json
  pyproject.toml
  toys/
    your-toy/             one complete creation and its evidence
  src/your_id/
    __main__.py           thin Workshop connection
    inventor.py           optional custom hooks only
  tests/
```

Only `TASTE.md` is creative code at the taste-only level. The generated module
selects a category, creates typed Wishes, and constructs `Workshop`; it does not
reimplement the loop.

The README must answer:

1. Which category and audience does this inventor serve?
2. What makes its output recognizable without a logo?
3. How does it turn useful Wishes into play?
4. Which customization level does it use, and why?
5. Which shared capabilities are required for a real run?
6. Which evidence classes can pass Playtest?
7. What is missing, synthetic, experimental, or blocked today?

Use a schema-v5 `inventor.json`. It contains only operational facts. Creative
identity and routing prose belong in `TASTE.md`, so they cannot disagree across
two files. Capabilities should state the category and real custom behavior, not
list every shared internal module:

```json
{
  "schema_version": 5,
  "id": "your-id",
  "status": "experimental",
  "entrypoint": ["python3", "-m", "your_id"],
  "capabilities": ["wish", "make", "playtest", "instructions", "deliver", "moving-machines", "taste-only"],
  "checks": [["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]],
  "source": {"kind": "local"}
}
```

Older manifest schemas remain readable during migration, but new inventors do
not declare an `autonomy` mode. Every profile receives one assignment and may
truthfully wait for people or tools when the work requires them.

## 4. Write Taste before code

`TASTE.md` is the human-owned creative constitution. For physical products it
uses the same progressive-disclosure shape as a focused `SKILL.md`: a small
selection header followed by the full instructions. It tells the Manager which
craft this inventor is right for, which work it should refuse, and what good
output looks like. It should make two inventors given the same Wish choose
recognizably different products.

Start every Taste with bounded YAML frontmatter:

```yaml
---
name: Ada
description: Choose Ada for Wish-shaped hand-cranked creatures and expressive mechanisms; not static models, known games, or scientific teaching objects.
---
```

The catalog indexes only that name and description. Write the description like
a selection boundary: say what should choose this inventor and the closest
work it should not absorb. The Manager loads the Markdown body only when the
inventor reaches the finalist shortlist.

Define:

- a short routing description: **best for**, **not for**, and hard boundaries;
- the chosen Workshop category and the kinds of ambiguous Wishes it should win;
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
pass an AI Playtest check, replace a Deliver receipt, or stand in for customer
Reviews after shipping.

Keep routing guidance inside the same Taste rather than adding a second prompt
or manager-only description. The Manager compares each finalist's complete,
exact file, and Workshop binds that same hash to Make and Playtest. If a
finalist Taste changes after routing, the assignment is stale and must be made
again; it may not silently change who the Wish was assigned to midway through
a run.

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
shared Make, Playtest, Instructions, and Deliver implementations. A profile must not
embed shared credentials or quietly fall back to a developer's personal
account.

Before running, `Workshop.preview(wish)` can show the exact Wish-, Taste-, and
category-bound Make brief without starting work.

The application dispatches the Manager's typed assignment to the selected
profile once. A profile should not rediscover the roster, reroute the Wish,
poll for more work, or create its own scheduler. Reassignment is an explicit
new Manager decision with a new assignment identity.

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
exhausted, it stops before Instructions and Deliver; it does not receive a cheaper
quality bar.

## 8. Use the right evidence class

Playtest is performed by AI agents over the whole digital toy or game, and a
result may claim only what its evidence observed:

- **AI simulation:** seeded traces, legal actions, termination, balance and
  pacing proxies. It cannot claim human fun.
- **Independent model review:** a reproducible prediction about clarity,
  novelty, or Taste alignment. It is not human feedback.
- **CAD/kernel measurement:** exact topology, dimensions, fit, interference,
  motion, or assembly calculations. It is not a physical test.
- **Slicer analysis:** exact meshes under a pinned printer, material, and
  profile. It predicts manufacturing; it does not prove a print succeeded.

Deliver separately records the exact artifact, printer, material, calibration,
physical measurements, hands-on QA, packing, and shipment receipts. After the
customer receives that order, Reviews records what verified customers say
about living with it. Bind each Review to the delivered toy, report the sample,
and do not generalize beyond it. Reviews may improve a future revision of the
same toy and inform future Wishes and Makes; it is not Playtest evidence, an
inventor hook, or a release gate for the original order.

For invented games, AI players must execute the rules rather than let one model
narrate an imagined session. Rotate seats and policies, retain seeded traces,
and check termination, dead states, illegal actions, dominant strategies,
pacing, and exploits. Run at least 1,000 complete seeded games. These are
useful predictions, not claims about customer fun; actual customer response is
collected later as Reviews and may guide a future revision of the same toy as
well as future Wishes and Makes.

For classics made yours, verify the known rules and evaluate the exact custom
edition as an object. Do not market familiar gameplay as a new invention.

For every category, Playtest covers delight intent, mechanics, printable
geometry, slicing, rules, and other checks that AI agents or deterministic
tools can perform. Printing and hands-on QA begin only in Deliver. Human
customer feedback begins only after delivery as Reviews.

## 9. Let shared Instructions tell only the truth

Instructions starts only after the exact Make passes Playtest. It produces the
truthful product page and the paper that belongs in the box: a rulebook for a
game, or instructions for another toy. Both stay bound to the same approved
product. The shared contract requires distinct hero, play, detail, parts, and
box images plus a claim-to-evidence map.

Creating files locally is only the first half of Instructions. The same shared
job creates and enriches the page in Factory as a private draft and requires
authenticated owner readback for the exact approved product, sealed page,
guide, media, and terminal `By <Inventor>.` byline before Deliver can begin.
Instructions does not make the page public and does not require an active
listing. An owner reviews the draft and may make it public later through a
separate action outside the five-job pipeline.

If a run waits here, resume the exact sealed work instead of starting over:

```python
resumed = workshop.resume_instructions(wish)
```

Workshop verifies the original Wish, Taste, blueprint, round allowance, Make,
Playtest evidence, event chain, and Instructions manifest, then calls only the
shared site writer. Make, Playtest, copy, and media are not repeated.

The media provider must render or photograph the approved artifact. Concept art
may appear only when clearly labeled as concept art; it cannot stand in for a
product render, printed prototype, or packed box.

Copy must retain evidence qualifiers. Good copy can be magical without
inventing facts:

- say “128 seeded AI games terminated,” not “players love it”;
- say “sliced under the named profile,” not “guaranteed to print”;
- do not borrow customer Reviews from an earlier delivery as proof for this
  toy's Playtest;
- never claim a local page is a remote draft; only authenticated owner readback
  of the private Factory draft can complete Instructions.

An inventor does not implement its own Factory draft path. Improve shared
Instructions when every inventor needs the change. The later owner-controlled
public transition is not an inventor hook or a sixth Workshop job.

## 10. Let shared Deliver ship the exact approval

Deliver binds four kinds of evidence to the approved product and Instructions:

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

## After Deliver, Reviews improve future Makes

Reviews records what customers report after they receive the exact shipped
toy. That feedback may inspire a new Wish or enter a future Make as product
learning. It never rewrites the completed run, delays the original order, or
becomes a custom inventor hook. Reviews is post-delivery feedback around the
five jobs—not a sixth job.

## 11. Test failure before success

At minimum, an inventor's tests should prove:

- its complete Taste gives the Manager clear positive and negative routing
  guidance;
- the root `TASTE.md` is loaded and its exact bytes are bound;
- its profile selects one valid category and the intended customization level;
- changing Taste after assignment makes the assignment stale;
- changing Taste or product bytes during a run fails closed;
- Made files stay inside the fresh round workspace;
- a failed Playtest returns actionable feedback to the next Make round;
- stale, missing, malformed, mismatched, or synthetic evidence cannot become a
  real pass;
- AI simulation cannot be presented as human-fun evidence;
- slicer output cannot be presented as a successful physical print;
- production and hands-on QA cannot be presented as Playtest;
- customer Reviews cannot rewrite the Playtest evidence for a shipped toy;
- Instructions claims and images remain bound to the approved product;
- Instructions completes only with authenticated readback of the exact private
  draft, without requiring public visibility or an active listing;
- changed Instructions bytes cannot enter Deliver;
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
