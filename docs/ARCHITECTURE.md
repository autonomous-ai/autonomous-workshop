# Toy Workshop architecture

Autonomous Workshop is a Santa-style workshop for **playthings for grown-ups
(14+)**. People make a Wish, wait, and receive a box. Inside the Workshop,
inventors work like elves: each brings a distinct Taste while sharing the same
reliable machinery.

The first version is intentionally narrow. It makes joy, surprise, and play—not
plain utility.

## What the Workshop makes

Every product belongs to one of four lanes:

- **Tabletop games** (`table-game`) — games, sets, dice play, and compact social
  experiences.
- **Desk toys** (`desk-toy`) — mechanisms, fidgets, tiny machines, and playful
  versions of useful objects.
- **Tiny models and characters** (`model-character`) — original vehicles,
  creatures, companions, and little worlds.
- **Puzzles and playful keepsakes** (`puzzle-keepsake`) — secret boxes,
  personalized discoveries, and objects with play hidden inside.

A useful Wish still enters the Workshop, but Make gives it a soul. A cable
holder might become a creature that swallows cables; it must not remain a plain
bracket with decoration added afterward.

## The five jobs

The complete Workshop vocabulary is:

```text
Wish -> Make <-> Playtest -> Docs -> Deliver
             feedback
```

- **Wish** preserves what the person asked for and the relevant constraints.
- **Make** invents the plaything, writes any rules, and creates its exact
  printable product files.
- **Playtest** tests that exact Make from every relevant angle. A failed check
  returns actionable feedback to Make, producing a new immutable round.
- **Docs** creates a truthful private product page, instructions, and beautiful
  images for the approved Make.
- **Deliver** produces, checks, packs, and hands the exact approved product to
  USPS, UPS, or FedEx.

`Taste` guides the jobs; it is not a sixth job. Research, rules writing,
rendering, slicing, simulation, repair, printing, and carrier integration are
tasks inside the five jobs, not extra lifecycle concepts.

## Alice on the shared Workshop

Alice is the concrete example. Her folder stays thin at the Workshop boundary;
the machinery beneath her is shared by every inventor.

```text
+-------------------------- ALICE --------------------------+
|  TASTE.md: recognizable judgment                         |
|  optional Make hook: game invention                      |
|  optional Playtest hook: tabletop expertise              |
+----------------------------+------------------------------+
                             | configures typed hooks
                             v
+-------------------- SHARED WORKSHOP ----------------------+
|                                                            |
|  [Wish] -> [Make] -> [Playtest] --pass--> [Docs]          |
|              ^            |                    |            |
|              +--feedback--+                    v            |
|                                             [Deliver]       |
|                                                            |
|  CAD | AI players | evidence | runtime | rendering         |
|  product pages | production | USPS / UPS / FedEx           |
+----------------------------+-------------------------------+
                             |
                             v
                    PERSON RECEIVES THE BOX
```

Dependency remains one-way: Alice imports Workshop; Workshop never imports
Alice. Alice can become more specialized without forking artifact identity,
the improvement loop, Docs, delivery, or durable runtime.

Inventor identities are backstage. Customers Wish through the Workshop and
receive the Workshop's box; they do not need to select or understand an elf.

## Three customization levels

The same boundary supports three levels of authorship:

| Level | Inventor supplies | Workshop supplies |
|---|---|---|
| **Taste only** | `TASTE.md` | Make, Playtest, the improvement loop, Docs, Deliver, and runtime |
| **Custom Make** | `TASTE.md` and `MakeContext -> Made` | Playtest, the improvement loop, Docs, Deliver, and runtime |
| **Custom Playtest** | `TASTE.md`, custom Make, and `PlaytestContext -> Playtested` | the improvement loop, Docs, Deliver, and runtime |

A custom Playtest requires a custom Make. This keeps the maximum level honest:
an inventor that changes how evidence is interpreted must also own the product
contract being tested. Docs and Deliver remain shared so every inventor gets
the same truth and exact-artifact guarantees.

The shared defaults are capabilities configured for the Workshop as a whole,
not magic built into a profile. If a model, CAD worker, physical test, image
renderer, printer, or carrier connection is unavailable, the job returns a
typed `WaitingFor` result. Missing capability is never converted into success.

## Job contracts

The jobs exchange small, exact records:

```text
Wish + Taste + ToyBlueprint
              |
              v
         MakeContext  ->  Made
                            | exact product manifest
                            v
      PlaytestContext  ->  Playtested
                            | evidence + Feedback
                            v
          DocsContext  ->  ProductDocs
                            | exact page manifest
                            v
       DeliverContext  ->  Delivered
                            | production + carrier receipts
                            v
                       WorkshopRun
```

`Made` binds product metadata to an immutable artifact tree. `Playtested` binds
every result and evidence file to that artifact hash. `ProductDocs` binds the
page and media to both its own manifest and the product hash. `Delivered` binds
production and carrier receipts to the exact product and Docs hashes.

Changing product bytes after Make, evidence after Playtest, or page bytes after
Docs invalidates the next boundary. No later job is allowed to bless stale
work.

## The Playtest improvement loop

Playtest is broader than checking rules. It asks whether the whole plaything is
good enough to continue:

- Does the idea feel playful and aligned with Taste rather than merely useful?
- Are rules executable, terminating, understandable, and resistant to obvious
  exploits?
- Do AI-player traces reveal balance, pacing, dominant strategies, dead states,
  or discontinuities?
- Do CAD bodies, fits, motion, assembly, and part interfaces work?
- Do every expected part and exact slicer profile pass printable-geometry and
  manufacturing checks?
- Does the exact physical prototype work under measured use?
- Can independent people use it without inventor coaching, and what do they
  actually do or say?

A failed result includes structured `Feedback`: the area, observed finding,
evidence references, severity, and a concrete change for the next Make. The
Workshop creates a new round and retains the old one; it never edits history to
make a later version look like the version originally tested.

The loop is bounded. Reaching the round limit stops truthfully instead of
lowering the bar.

The allowance is selected per Wish, not baked into an elf:

```python
workshop.run(wish, playtest_rounds=2)   # a small service tier
workshop.run(wish, playtest_rounds=10)  # a deeper service tier
```

A trusted checkout or quote maps payment to the allowance; text inside a Wish
cannot authorize spend. `playtest_rounds` is the maximum number of
Make–Playtest improvement rounds. A Playtest implementation may also run many
seeded AI games, reviewers, or physical trials inside one round. More budget
buys more opportunities to find and repair problems—it never lowers the same
acceptance policy.

## Evidence classes and honest claims

Different evidence proves different things. The class travels with its source,
hash, evaluator, exact version, configuration, and observation time.

| Evidence class | May support | Does not prove |
|---|---|---|
| **AI simulation** | executable rules, termination, traces, measured balance or pacing proxies | that people understand it or find it fun |
| **Independent model review** | a reproducible prediction about clarity, novelty, or Taste alignment | human preference or physical behavior |
| **CAD/kernel measurement** | topology, dimensions, clearances, interference, or motion computed from exact geometry | that a real print assembled or survived use |
| **Slicer analysis** | that exact meshes sliced under a pinned printer, material, and profile; predicted time/material/supports | successful printing or acceptable surface quality |
| **Physical prototype** | recorded measurements and tests of one exact printed revision with printer/material/calibration provenance | broad durability, safety, or customer delight beyond that test |
| **Human playtest** | observed behavior and feedback from identified independent participants under a stated protocol | universal fun or demand beyond the observed sample |
| **Production/carrier receipt** | the exact job, QA, packing, handoff, or delivery event the authenticated provider observed | an event later than the receipt's actual status |

Examples of truthful boundaries:

- “128 seeded simulations terminated” is an AI-simulation claim; “players had
  fun” is not.
- “Sliced with profile X” is slicer evidence; “prints perfectly” requires a
  physical print and test.
- A label is not carrier handoff. “Delivered” requires the corresponding
  carrier observation.

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. An inventor's own confidence is not independent evidence.

## Docs is part of the proof chain

Docs begins only after Playtest passes for the exact Make. The shared default
creates a private page with five fixed image roles—hero, play, detail, parts,
and box—and a claim-to-evidence map.

Images must depict the product actually approved. Concept art can guide Make,
but it cannot masquerade as a render or photograph of printable geometry. Copy
must preserve evidence qualifiers: simulation remains simulation; a prototype
remains a prototype; limited human observations remain limited.

## Deliver is an exact-product boundary

Deliver does not mean “a label was created.” It requires evidence for printing,
QA, packing, and carrier handoff, bound to the approved product and Docs hashes.
The supported first-version carriers are USPS, UPS, and FedEx.

External effects use durable intent, stable idempotency, scoped credentials,
and authenticated receipts. A timeout or ambiguous response is held for
reconciliation. It is not blindly retried and it never becomes a fabricated
receipt.

## Shared implementation

```text
inventors/<id>/
  TASTE.md              human-owned creative constitution
  inventor.json         identity, lane capability, entry point, and checks
  README.md             niche, operation, evidence, and known limits
  profile.py or src/    thin Workshop connection and optional hooks
  tests/                inventor-specific checks

src/inventor_workshop/
  toys.py               four lanes and their shared task blueprint
  workshop.py           five-job orchestration and improvement loop
  jobs.py               typed inputs, results, feedback, and waiting
  make.py               Wish and shared making boundary
  gameplay.py           reproducible AI-player games and leagues
  playtest.py           exact artifact-bound evidence
  docs.py               truthful product-page contract
  deliver.py            production and carrier contract
  artifacts.py          immutable product and evidence identity
  runtime.py            state, leases, budgets, and durable effects
  taste.py              exact human-owned creative constitution

skills/                 versioned shared making knowledge
schemas/                portable persisted contracts
tests/                  shared Workshop invariant tests
```

Provider adapters may vary, but provider database models never become local
state authority. Credentials remain outside Taste, prompts, artifacts, events,
and source.

## Extension rule

Put a behavior in Workshop when multiple inventors need the same invariant and
it can remain independent of Taste. Keep it in the inventor when it expresses
recognizable judgment, niche-specific generation, or stricter niche Playtest
logic.

Older persisted runs and imports remain readable through compatibility aliases.
Those aliases are migration details, not alternate jobs or concepts for new
inventors.
