# Toy Workshop architecture

Autonomous Workshop is a Santa-style workshop for **playthings for grown-ups
(14+)**. People make a Wish, wait, and receive a box. Inside the Workshop,
inventors each bring a distinct Taste while sharing the same
reliable machinery.

The first version is intentionally narrow. It makes joy, surprise, and play—not
plain utility. It is also request-driven: one Wish starts one assignment. An
inventor does not need to poll a queue or run continuously.

## What the Workshop makes

Every product belongs to one of five categories:

- **Classics made yours** (`classics-made-yours`) — known games and puzzles
  remade as exceptional, personal physical editions. The rules are already
  known; the product is judged as an object and a custom edition, not as a new
  game design.
- **Games that don't exist yet** (`invented-games`) — new rules, mysteries,
  strategy, competition, and tactile problems to solve. AI players exercise
  the complete rules, strategies, endings, and exploits before Instructions;
  customer response arrives later as Reviews after delivery.
- **Machines that move** (`moving-machines`) — mechanisms, kinetic desk toys,
  tiny machines, and objects with a satisfying motion.
- **Science you can hold** (`holdable-science`) — tangible phenomena, geometry,
  nature, space, waves, forces, and experiments made graspable through play.
- **Little worlds** (`little-worlds`) — personalized miniature places,
  characters, stories, memories, and relationships shaped around one person.

Every category faces the same bar:

1. **It could not have been bought before the Wish.** The person's words,
   context, or relationships must materially change the rules, geometry, or
   experience. Adding a nameplate to a generic model does not qualify.
2. **Cool beats cute or twee.** The result should feel clever, striking,
   surprising, or deeply satisfying. Cuteness may support the idea; it cannot
   be the whole idea.
3. **Personalization and design intelligence beat generic prints.** Make must
   interpret the Wish and solve a design problem, not retrieve a familiar STL
   and decorate it.

Kits and numbered series may become later ways to extend a successful product.
They are not Workshop jobs and are not V1 promises.

## The six jobs

The complete Workshop vocabulary is:

```text
creation:       Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
                                       feedback
after delivery: customer Reviews -> a future revision of this toy
                                  -> future Wishes and Makes
```

- **Wish** preserves what the person asked for and the relevant constraints.
- **Invent** explores the plaything's industrial design and improves the chosen
  concept to its fixed reward goal.
- **Make** turns that concept into mechanical and 3D design, including any
  rules and exact printable product files.
- **Playtest** has AI agents simulate using or playing that exact Make from
  every relevant angle. A failed check returns actionable feedback to Make,
  producing a new immutable round. Playtest never means a human
  print-and-play session.
- **Instructions** creates the paper that belongs in the box and a factual,
  evidence-bound content brief. It preserves the terminal `By <Inventor>.`
  attribution, sends a model-only private draft to Factory, and authenticates
  that handoff. Factory owns later marketing images and page copy; the handoff
  remains explicitly pending and not page-ready until a separate content
  pipeline confirms enrichment. Instructions does not make the page public or
  require an active listing.
- **Deliver** produces, checks, packs, and hands the exact approved product to
  USPS, UPS, or FedEx.

`Taste` guides the jobs; it is not a job of its own. Research, rules writing,
rendering, slicing, simulation, repair, printing, and carrier integration are
tasks inside the six jobs, not extra lifecycle concepts. After Deliver,
customer **Reviews** may improve a future revision of the same toy and inform
future Wishes and Makes. Reviews is a public, post-delivery feedback stream,
not a seventh inventor job, custom inventor hook, or release gate for the order
already shipped.

The owner-facing transition from private draft to public page is deliberately
outside those six jobs. An owner reviews the finished draft and decides when
to make it public; that decision does not delay Instructions or Deliver and
does not introduce a seventh job.

## The Workshop Manager

Customers do not have to know which inventor to choose. The Workshop Manager
discovers an open catalog that may contain thousands of inventors and assigns
one Wish to the best fit once.

```text
                            one Wish
                               |
                               v
             TASTE.md names + short descriptions
                               |
                               v
                    +----------------------+
                    |   WORKSHOP MANAGER   |
                    | semantic shortlist   |
                    | full finalist Tastes |
                    | chooses + explains   |
                    +----------+-----------+
                               |
                         one assignment
                               |
                               v
                         chosen inventor
                               |
                               v
             creation: Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
                                                feedback
             later:    customer Reviews -> future Makes
```

This checkout begins with five showcase inventors:

| Inventor | Taste lane |
|---|---|
| Alice | classics made yours (`classics-made-yours`) |
| Leo | games that do not exist yet (`invented-games`) |
| Bob | machines that move (`moving-machines`) |
| Ivy | science you can hold (`holdable-science`) |
| Eve | little worlds (`little-worlds`) |

The catalog is open: other people may add many inventors in the same category
or introduce narrower niches. Like a skill, each `TASTE.md` exposes only its
name and a short, discriminating description during discovery. A semantic
retriever compares those descriptions with the complete Wish and records a
bounded shortlist. Only then does the Manager load each finalist's complete
`TASTE.md` body. `inventor.json` is operational: it tells Workshop how to run
the inventor, not when to choose it.

Routing is semantic, not a keyword switch. A judge assesses every shortlisted
Taste under one rubric, records acceptance, score, explanation, and hard
tensions, then applies a deterministic ordering. If that bounded comparison is
not enough, the Manager returns a truthful need; the caller may widen retrieval
and submit a new, separately recorded shortlist. The Manager never invents
certainty or silently changes the candidate set. The assignment binds the
untouched Wish, catalog snapshot, retrieval and judge provenance, finalist
Taste hashes, complete ranking, selected entry point, and trusted
Playtest-round allowance. Relevant catalog or Taste changes make that
assignment stale.

If retrieval or full-Taste judgment is unavailable, the Manager waits
truthfully. If no finalist genuinely fits, it waits for clarification, a wider
shortlist, or a new inventor instead of forcing the Wish into the least-wrong
category.

The Manager is typed Workshop engine code, not a skill, a sixth Workshop job,
or a creative supervisor once work begins. Making it a skill would leave the
host to select the selector and would hide routing behind prompt behavior. Its
assignment enters the same six-job contract as every other Wish. A future
continuous service may repeatedly call this one-Wish interface, but scheduling,
polling, and 24/7 operation stay outside an inventor profile and outside the V1
Workshop promise.

## Alice on the shared Workshop

Alice is the concrete example. Her folder stays thin at the Workshop boundary;
the machinery beneath her is shared by every inventor.

```text
+-------------------------- ALICE --------------------------+
|  TASTE.md: recognizable judgment                         |
|  category: classics-made-yours                           |
|  no custom Make or Playtest code                         |
+----------------------------+------------------------------+
                             | configures typed hooks
                             v
+-------------------- SHARED WORKSHOP ----------------------+
|                                                            |
|  [Wish] -> [Invent] -> [Make] -> [Playtest] -> [Instructions] |
|                          ^            |              |       |
|                          +--feedback--+              v       |
|                                                   [Deliver]  |
|                                                            |
|  CAD | AI players | evidence | runtime | rendering         |
|  product pages | production | USPS / UPS / FedEx           |
+----------------------------+-------------------------------+
                             |
                             v
                    PERSON RECEIVES THE BOX
                             |
                             v
                    REVIEWS -> FUTURE MAKES
```

Dependency remains one-way: Alice imports Workshop; Workshop never imports
Alice. She demonstrates the Taste-only level: shared Workshop owns Invent,
Make, Playtest, their improvement loops, Instructions, Deliver, and runtime.

Alice is the bundled `classics-made-yours` example. Her earlier Blindcap work
remains provenance that taught Workshop how to make and Playtest games; Leo is
the bundled `invented-games` example. Neither profile owns a category: future
inventors may enter either lane with a different Taste.

Inventor identities are backstage. Customers Wish through the Manager and
receive the Workshop's box; they do not need to select or understand an inventor.

## Three customization levels

The same boundary supports three levels of authorship:

| Level | Inventor supplies | Workshop supplies |
|---|---|---|
| **Taste only** | `TASTE.md` | Invent, Make, Playtest, their loops, Instructions, Deliver, and runtime |
| **Custom Make** | `TASTE.md` and `MakeContext -> Made` | Invent, Playtest, the feedback loop, Instructions, Deliver, and runtime |
| **Custom Playtest** | `TASTE.md`, custom Make, and `PlaytestContext -> Playtested` | Invent, the feedback loop, Instructions, Deliver, and runtime |

A custom Playtest requires a custom Make. This keeps the maximum level honest:
an inventor that changes how evidence is interpreted must also own the product
contract being tested. Instructions and Deliver remain shared so every inventor gets
the same truth and exact-artifact guarantees.

The shared defaults are capabilities configured for the Workshop as a whole,
not magic built into a profile. If a model, CAD worker, AI simulator, image
renderer, printer, or carrier connection is unavailable, its owning job
returns a typed `WaitingFor` result. Missing capability is never converted
into success.

## Job contracts

The jobs exchange small, exact records:

```text
Wish + Taste + ToyBlueprint
              |
              v
       InventContext  ->  Invented
                            | scored industrial-design concept
                            v
         MakeContext  ->  Made
                            | exact product manifest
                            v
      PlaytestContext  ->  Playtested
                            | evidence + Feedback
                            v
          InstructionsContext  ->  ProductInstructions
                            | exact facts/paper manifest + authenticated private draft
                            v
       DeliverContext  ->  Delivered
                            | production + carrier receipts
                            v
                       WorkshopRun
```

`Invented` binds the scored industrial-design concept to the exact Wish and
Taste. `Made` binds the resulting mechanical and 3D design to an immutable
artifact tree. `Playtested` binds
every result and evidence file to that artifact hash. `ProductInstructions` binds
the factual Factory handoff and in-box paper to both its own manifest and the
product hash. Factory alone creates customer-facing page copy, images, and video.
`Delivered` binds production and carrier receipts to the exact product and
Instructions hashes.

After delivery, customer Reviews may be collected with the delivered product
identity and offered as input to a future Make. They do not mutate the
completed run, re-grade its Playtest, or add another inventor hook.

Changing product bytes after Make, evidence after Playtest, or page bytes after
Instructions invalidates the next boundary. No later job is allowed to bless stale
work.

## The Playtest improvement loop

Playtest is AI-agent simulation and feedback, broader than checking rules. It
asks whether the digital plaything is good enough to continue:

- Does the idea feel playful and aligned with Taste rather than merely useful?
- Are rules executable, terminating, understandable, and resistant to obvious
  exploits?
- Do AI-player traces reveal balance, pacing, dominant strategies, dead states,
  or discontinuities?
- Do AI agents and deterministic tools find problems in CAD bodies, fits,
  motion, assembly, and part interfaces?
- Do every expected part and exact slicer profile pass digital geometry and
  manufacturing checks?

A failed result includes structured `Feedback`: the area, observed finding,
evidence references, severity, and a concrete change for the next Make. The
Workshop creates a new round and retains the old one; it never edits history to
make a later version look like the version originally tested.

The loop is bounded. Reaching the round limit stops truthfully instead of
lowering the bar.

Category policy stays explicit. A classic is simulated as an exact custom
edition: rules fidelity, object legibility, setup, handling proxies,
printability, and the Wish-specific design. For an invented game, executable AI
players must complete at least 1,000 seeded games and probe rules, endings,
balance, strategies, and exploits. Customer desire for another play is not a
Playtest claim; it arrives later through Reviews and can improve a future
revision of the same toy as well as future Wishes and Makes.

The allowance is selected per Wish, not baked into an inventor:

```python
workshop.run(wish, playtest_rounds=2)   # a small service tier
workshop.run(wish, playtest_rounds=10)  # a deeper service tier
```

A trusted checkout or quote maps payment to the allowance; text inside a Wish
cannot authorize spend. `playtest_rounds` is the maximum number of
Make–Playtest improvement rounds. A Playtest implementation may also run many
seeded AI games, model reviewers, or digital trials inside one round. More budget
buys more opportunities to find and repair problems—it never lowers the same
acceptance policy.

## Evidence boundaries and honest claims

Different boundary records prove different things. Each travels with its
source, hash, evaluator, exact version, configuration, and observation time.

| Boundary evidence | May support | Does not prove |
|---|---|---|
| **AI simulation** | executable rules, termination, traces, measured balance or pacing proxies | that people understand it or find it fun |
| **Independent model review** | a reproducible prediction about clarity, novelty, or Taste alignment | human preference or physical behavior |
| **CAD/kernel measurement** | topology, dimensions, clearances, interference, or motion computed from exact geometry | that a real print assembled or survived use |
| **Slicer analysis** | that exact meshes sliced under a pinned printer, material, and profile; predicted time/material/supports | successful printing or acceptable surface quality |
| **Deliver receipt** | the exact print, QA, packing, handoff, or delivery event an authenticated provider observed | any later event or customer experience |
| **Customer Review** | what a verified customer reported after delivery | that the earlier Playtest predicted it, or that every customer agrees |

The first four rows belong to Playtest. Deliver owns the exact physical print,
hands-on QA, packing, and carrier receipts. Reviews begins only after delivery
and feeds future Makes; it never changes the completed Playtest result.

Examples of truthful boundaries:

- “128 seeded simulations terminated” is an AI-simulation claim; “players had
  fun” is not.
- “Sliced with profile X” is slicer evidence; “prints perfectly” requires a
  print and QA receipt from Deliver.
- A label is not carrier handoff. “Delivered” requires the corresponding
  carrier observation.

Unknown, missing, stale, malformed, mismatched, or timed-out evidence cannot
pass. An inventor's own confidence is not independent evidence.

## Instructions is part of the proof chain

Instructions begins only after Playtest passes for the exact Make. The shared
default creates the in-box instructions plus a structured content brief and
claim-to-evidence map. It derives a model-only handoff from the exact Make and
imports it into Factory as a private draft. Local CAD previews, inspection
renders, `use_case`, and `story_blocks` are never sent as marketing content.
Project-marker handoffs must expose a Playtested root `assembled.stl` or
`<slug>.stl`, so Factory cannot mistake a nested component for the complete
toy. Generator handoffs may instead provide a top-level `gen_step`.
Authenticated owner readback proves the exact approved model history and
sealed fact identities. It also records `enrichment_status=pending` and
`page_ready=false`; model import alone does not prove that final images, copy,
or video exist.

Factory receives both the full canonical facts file and a bounded factual
story prompt made from the Wish, title, summary, description, components,
design facts/specifications, rules/instructions, optional structured story and
art direction, limitations, and exact inventor credit. The prompt is input to Factory enrichment, not
creator-authored page output.

Instructions stops there and advances to Deliver. It neither makes the page
public nor requires an active listing. An owner may review the draft and make
it public later through a separate, explicit action outside the six-job
pipeline.

This is a fail-closed boundary across every shared Shop entry point, including
the low-level compatibility APIs: a caller cannot attach an import thumbnail,
upload page media, patch `use_case` or `story_blocks`, or add creator
attachments while publishing. Those calls fail before HTTP. Authenticated
readback may observe copy, images, attachments, and video that Factory generated
after the model handoff; Workshop accepts that server-owned enrichment without
requiring it to equal the original factual brief.

Before any site effect, Workshop seals both the approved Make/Playtest
checkpoint and the complete Instructions tree. If credentials disappear or a
site response is ambiguous, `workshop.resume_instructions(wish)` reuses those
exact bytes and retries only the idempotent model-handoff writer. It never
reruns Make, Playtest, or the sealed content brief. Factory enrichment is a
separate handoff, not a silently retried Workshop side effect.

Images must depict the product actually approved. Concept art can guide Make,
but it cannot masquerade as a render or photograph of printable geometry. Copy
must preserve evidence qualifiers: simulation remains simulation; a digital
prototype remains a digital prototype; Reviews from earlier deliveries must
not be presented as proof that the current toy passed Playtest.

## Deliver is an exact-product boundary

Deliver does not mean “a label was created.” It requires evidence for printing,
QA, packing, and carrier handoff, bound to the approved product and Instructions hashes.
The supported first-version carriers are USPS, UPS, and FedEx.

External effects use durable intent, stable idempotency, scoped credentials,
and authenticated receipts. A timeout or ambiguous response is held for
reconciliation. It is not blindly retried and it never becomes a fabricated
receipt.

## Reviews improve the next Make

Reviews begins after the customer receives the box. It records customer
feedback against the delivered toy and may inform a new Wish or future Make.
It does not delay the original delivery, mutate that run's evidence, or become
a sixth Workshop job. Inventors customize Taste, Make, and optionally
Playtest—not Reviews.

## Shared implementation

```text
inventors/<id>/
  TASTE.md              selection header + human-owned creative constitution
  inventor.json         operational id, status, entry point, and checks
  README.md             niche, operation, evidence, and known limits
  profile.py or src/    thin Workshop connection and optional hooks
  tests/                inventor-specific checks

src/inventor_workshop/
  manager.py            one-Wish, Taste-bound inventor assignment
  toys.py               five categories and their shared task blueprint
  workshop.py           six-job orchestration and improvement loop
  jobs.py               typed inputs, results, feedback, and waiting
  make.py               Wish and shared making boundary
  gameplay.py           reproducible AI-player games and leagues
  playtest.py           exact artifact-bound evidence
  instructions.py       truthful product-page and box-paper contract
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

A scheduler belongs in a future application adapter only when an operator
actually needs continuous intake. It may create repeated one-shot assignments;
it must not become a seventh job, hide inside `TASTE.md`, or make every inventor
carry queue and daemon infrastructure.
