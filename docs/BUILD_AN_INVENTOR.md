# Build an inventor

An inventor is a durable creative identity in the Autonomous Workshop
for one kind of plaything. The inventor supplies recognizable Taste and, only
when needed, a custom Make or Playtest override. Workshop supplies the complete
product journey:

```text
creation:       Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
                                       feedback
after delivery: customer Reviews -> future Makes
```

Every assignment follows these six creation jobs. Taste shapes the shared
workers; Reviews is post-delivery feedback for future work, not another hook to
implement.

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
little worlds. They demonstrate the five categories with Taste-only defaults;
the scaffold also supports the two optional override levels. They are not a
closed roster. Anyone may add an inventor, and many inventors may serve the
same category with different niches and Taste.

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

The Manager is not one of the six jobs. Once assigned, the Wish follows:

```text
creation:       Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
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
| `taste-only` | `TASTE.md` | Workshop Invent, Make, and Playtest |
| `custom-make` | `TASTE.md` plus `MakeContext -> Made` | Workshop Invent and Playtest |
| `custom-playtest` | `TASTE.md`, custom Make, and `PlaytestContext -> Playtested` | Workshop Invent and the feedback loop |

Workshop owns Invent, Instructions, Deliver, artifact identity, evidence
binding, runtime, and truthful waiting at every level. Custom Playtest is
available only with custom Make.

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
| Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver |
|                 artifacts + feedback + evidence + runtime     |
+-----------------------------------------------------+
                           |
                           v
                 Reviews -> future Makes
```

A new inventor follows this dependency shape and chooses the smallest level its
category needs; it does not copy Alice's state machine or private history.
Alice's earlier Blindcap work is Workshop provenance, while Leo is the bundled
`invented-games` example using shared Invent, Make/CAD, and Playtest by default.
Custom workers remain optional when an inventor has genuinely
category-specific logic.

## 3. Create your inventor

Already have a `TASTE.md`? That is enough creative code. Its header names the
Inventor and tells the Manager when to choose it:

```bash
uv run workshop create inventor ada \
  --taste ./TASTE.md \
  --lane moving-machines

uv run workshop wish --root . \
  "I wish my bicycle became a hand-cranked climbing creature"
```

The creator copies `TASTE.md` byte for byte, validates it, adds the thin runtime
connection, runs its smoke tests, and atomically joins it to the Manager's
catalog. The source file is never modified. `workshop wish` records the exact
Manager assignment so status and continuation stay available. The generated
`run.py` remains a developer check; installing the package bundles the same
exact identity.

The only other required choice is one [plaything category](#1-choose-one-plaything-category).
`taste-only` is the default, so Workshop supplies Invent, Make/CAD, Playtest,
Instructions, and Deliver. There is no custom Python file to finish.

Starting without a Taste is also supported. The creator writes a useful first
draft for you:

```bash
uv run workshop create inventor ada \
  --description "Choose Ada for hand-cranked creatures; not static models or games." \
  --lane moving-machines
```

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
  run.py                  works directly from the checkout
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
exact file, and Workshop binds that same hash to Invent, Make, and Playtest. If a
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
shared Invent, Make, Playtest, Instructions, and Deliver implementations. A
profile must not embed shared credentials or quietly fall back to a developer's
personal account.

Before running, `Workshop.preview(wish)` can show the exact Wish-, Taste-, and
category-bound brief without starting work.

The application dispatches the Manager's typed assignment to the selected
profile once. A profile should not rediscover the roster, reroute the Wish,
poll for more work, or create its own scheduler. Reassignment is an explicit
new Manager decision with a new assignment identity.

## 6. Customize Make only when necessary

Custom Make has one stable boundary after shared Invent has selected and scored
the industrial-design concept:

```python
from inventor_workshop import Made, MakeContext


def make(context: MakeContext) -> Made:
    # Use context.wish, context.taste, context.blueprint, context.invented,
    # context.feedback, context.round, and the fresh context.workspace.
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

Custom Playtest receives the exact `Made` revision. It owns the testing method;
the Workshop still owns the release bar. Capability-specific results carry the
public typed proof record in `evidence["release_proof"]`:

```python
from inventor_workshop import (
    CapabilityReleaseProof,
    PlaytestContext,
    Playtested,
    ReleaseProofSource,
)


def playtest(context: PlaytestContext) -> Playtested:
    motion = run_motion_check(context.made, context.workspace)
    proof = CapabilityReleaseProof(
        capability="motion-test",
        artifact_sha256=context.made.artifact_sha256,
        proof_class="kinematic-motion-proof",
        sources=(
            ReleaseProofSource(
                "step-model", "product", motion.step_ref, motion.step_sha256
            ),
            ReleaseProofSource(
                "motion-receipt",
                "playtest",
                motion.receipt_ref,
                motion.receipt_sha256,
            ),
        ),
        measurements=motion.measurements,
    )
    # Embed proof.to_dict(), then write the full result evidence mapping unchanged.
    return seal_results(context, release_proof=proof.to_dict())
```

`ReleaseProofSource` identifies exact product or Playtest bytes by role, path,
and hash. `CapabilityReleaseProof` rejects a proof class for the wrong
capability and carries the capability's measured release semantics. The motion
adapter above, for example, must report the required sweep, tolerance, load,
orientation, wear, misuse, collision, stall, and failure measurements; naming
those fields without their sealed sources is not enough.

Every cited Playtest receipt uses this engine-neutral envelope (shown for the
motion receipt above):

```json
{
  "schema_version": 1,
  "kind": "workshop.capability-release-receipt",
  "artifact_sha256": "<exact Made artifact hash>",
  "capability": "motion-test",
  "proof_class": "kinematic-motion-proof",
  "role": "motion-receipt",
  "source_sha256": {"product:<STEP path>": "<STEP hash>"},
  "measurements": {"<exactly the same fields as the typed proof>": "..."},
  "payload": {"<replayable adapter-specific observations>": "..."}
}
```

The receipt file itself is then cited by path and hash in
`ReleaseProofSource`. Classic, science, and world proofs use the same envelope
for each of their Playtest receipt roles. Custom print proofs additionally cite
at least three `slicer-profile` sources and one `gcode-output` source per sealed
part; each profile and G-code path and hash must also appear in the print
measurements. Arbitrary digest strings are not output evidence.

The adapter must preserve all shared guarantees while adding niche-specific
checks:

- every result names the exact product artifact hash;
- every evidence reference exists with the declared hash in a sealed evidence
  manifest;
- the result's evidence mapping exactly matches its sealed evidence document;
- every capability promised by the `ToyBlueprint` returns its matching result
  and, where required, a valid `CapabilityReleaseProof`;
- evaluators, exact versions, configuration, and observation times are named;
- failed results include `Feedback` with an observed finding and a concrete
  requested change;
- missing capability returns `WaitingFor`, not pass;
- an inventor's model does not grade its own output as independent evidence.

The Workshop revalidates this common contract before Instructions and again
when Instructions resumes. A custom adapter can supply better evidence; it
cannot replace the gate with a passed label, model score, or weaker schema.

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
paper that belongs in the box and a structured, evidence-bound content brief:
a rulebook for a game, or instructions for another toy. Both stay bound to the
same approved product. Local product renders can remain useful Make/Playtest
evidence, but they are not uploaded as Factory marketing images.

Creating files locally is only the first half of Instructions. The same shared
job creates a model-only Factory draft and requires authenticated owner
readback for the exact approved model, sealed facts, guide, and terminal
`By <Inventor>.` attribution before Deliver can begin. Factory page enrichment
is a separate downstream responsibility. The draft records
`enrichment_status=pending` and `page_ready=false`; it does not claim images,
copy, or video were generated.
Instructions does not make the page public and does not require an active
listing. The customer CLI performs the separate, owner-controlled transition
after exact draft verification: `workshop wish` makes it public by default and
`--draft` opts out. Publication remains outside the six-job pipeline and never
counts as Deliver proof.

If a run waits here, resume the exact sealed work instead of starting over:

```python
resumed = workshop.resume_instructions(wish)
```

Workshop verifies the original Wish, Taste, blueprint, round allowance, Make,
Playtest evidence, event chain, and Instructions manifest, then calls only the
shared model-handoff writer. Make, Playtest, and the sealed content brief are
not repeated.

Do not add a media provider to Instructions. Factory renders the approved model
and owns all customer-facing page images and video. Local renders may remain
Make or Playtest evidence, but the model-only handoff excludes them.

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
public transition is not an inventor hook or a seventh Workshop job.

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
six jobs—not a seventh job.

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
- Instructions facts and in-box paper remain bound to the approved product;
- creator code cannot add marketing images, video, `use_case`, `story_blocks`,
  or publication attachments to the Factory handoff;
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
inventors should learn and expose only the six jobs.
