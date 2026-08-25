# Workshop 0.5 adoption

Autonomous Workshop 0.5 is the shared Toy Workshop for playthings for grown-ups
(14+). Its product journey is exactly:

```text
creation:       Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver
                                       feedback
after delivery: customer Reviews -> future revision + future Wishes
```

The creation workflow has exactly six jobs. Reviews is shown only as
post-delivery feedback for future work.

This page records what the five bundled showcase profiles can do **now**. A
valid profile or passing offline test is not a claim that its model, AI
Playtest, printer, product-page, production-QA, carrier, or post-delivery
Reviews capability is live.

V1 intake is request-driven. The Workshop Manager handles one Wish, retrieves
a shortlist from an open Taste catalog, compares the finalists' exact Tastes,
explains the best fit, and creates one content-bound assignment. No profile is
required to run 24/7, poll a queue, or schedule itself.

The installed distribution is `autonomous-workshop`, Python users import
`workshop`, and the `workshop` command is implemented in the sibling `src/cli/`
package. Shared implementation and tests are grouped by architecture component;
see [ARCHITECTURE.md](ARCHITECTURE.md#shared-implementation).

## Current profiles

| Profile | Category | Customization level | Truthful 0.5 status |
|---|---|---|---|
| Alice | classics made yours (`classics-made-yours`) | Taste only | Alice brings Taste; shared Invent, Make, and Playtest do the work. Her Blindcap laboratory is provenance that taught Workshop, not her active profile or a second invented-game inventor. |
| Leo | games that don't exist yet (`invented-games`) | Taste only by default | Shared Invent, Make/CAD, and AI Playtest build and test Leo's games, including the pinned simulation policy. Paired custom Make and Playtest workers remain optional. |
| Bob | machines that move (`moving-machines`) | Taste only by default | Shared Invent, Make/CAD, and AI Playtest build and test Bob's moving machines. A custom Make worker is optional for specialized mechanisms; his preserved board-game laboratory is not that worker. |
| Ivy | science you can hold (`holdable-science`) | Taste only | Shared Invent, Make, and Playtest do the work, including the lane's scientific-evidence checks. |
| Eve | little worlds (`little-worlds`) | Taste only | Shared Invent, Make, and Playtest do the work. This profile does not restore the old Eve implementation. |

All five categories share the same bar: the result could not have been
bought before the Wish; cool, clever, or striking beats merely cute or
twee; and personalization plus design intelligence must do more than decorate a
generic print. Kits and numbered series are later product variants, not current
profiles, jobs, or V1 promises.

Invented games have one additional AI Playtest requirement: executable players
must complete at least 1,000 seeded games and probe rules, endings, balance,
strategies, and exploits. Whether customers want another play is learned after
delivery through Reviews and can improve a future revision of that toy and
future Wishes.

## Current routing boundary

The current checkout discovers immediate local inventor folders that contain
both `inventor.json` and `TASTE.md`; a deployed catalog may contain thousands.
The Manager indexes every Taste's short name and description, records a
semantic shortlist, then loads and judges only the finalists' exact Taste
bodies. It deterministically selects the highest accepted fit and binds the
assignment to:

- the untouched Wish;
- the catalog snapshot and retrieval receipt;
- every finalist's exact Taste hash and complete ranking;
- the chosen inventor;
- the inventor's declared entry point; and
- the trusted per-Wish Playtest allowance.

Without semantic retrieval or judgment, the Manager returns a truthful
`WaitingFor` need. If every finalist rejects the Wish, it returns another
`WaitingFor` need rather than forcing an assignment. The caller may clarify the
Wish or submit a wider, separately recorded shortlist. Changing relevant
catalog metadata, a finalist Taste, or the selected manifest after routing
invalidates the handoff.

This boundary dispatches once. It is not a background scheduler and does not
add another Workshop job. A future continuous-intake adapter may repeatedly
invoke the same one-Wish contract without adding queue or daemon machinery to
the inventors themselves.

All five profiles use shared Invent, Make/CAD, and Playtest by default. The
inventor supplies Taste; Workshop owns those common workers, their reward and
feedback loops, Instructions, Deliver, artifact identity, and runtime. Bob's
profile accepts an explicit custom Make override, and Leo's accepts paired
custom Make and Playtest overrides, but a customer Wish does not depend on
either inventor building common infrastructure.
Mature legacy code remains useful migration material and is never invoked
silently through a bundled profile.

“Taste only” means the profile is wired to shared capabilities—not that model,
Factory, printer, or carrier credentials are present in every checkout.

## What is shared today

All five profiles use the same 0.5 contracts for:

- bounded Wishes that preserve the person's words;
- one-Wish, exact-Taste routing and content-bound assignment;
- exact, human-owned Taste bytes and SHA-256 identity;
- one of the five Workshop product categories;
- the `InventContext -> Invented` industrial-design seam;
- the `MakeContext -> Made` and `PlaytestContext -> Playtested` seams;
- actionable Playtest feedback and bounded immutable rounds;
- typed `Need` and `WaitingFor` results instead of fabricated success;
- content-addressed product, evidence, and Instructions identities;
- the shared Instructions and Deliver boundaries;
- durable state, leases, and a recorded per-Wish Playtest allowance.

Locked making skills have one owner under `src/workshop/make/skills/`.
Persisted schemas live under the component that defines each contract and are
distributed as package data; the CLI's schema registry is a view of those
component-owned resources, not a second source of truth.

The platform operator still has to configure the shared tools. A complete path
needs, as applicable, authenticated model and CAD workers, executable AI
players, independent model reviewers, and a pinned slicer profile for Playtest,
plus private model-only site-draft integration for Instructions. Factory owns
the downstream customer-facing page renderer, copy, images, and video.
Deliver then needs a printer profile, exact production, hands-on QA, packing,
and USPS/UPS/FedEx integration. Reviews begins only after customers receive
those deliveries.

Missing tools remain a `waiting` result. Simulation does not become human-fun
evidence; slicer output does not become a physical print; concept art does not
become a product photograph; a generated label does not become carrier handoff.

Reviews is post-delivery feedback that can inform a future revision of the same
toy and future Wishes. It is not a seventh job, a custom inventor hook, or a gate
that holds the original order, and it cannot mutate shipped bytes.

## Per-Wish Playtest allowance

The Workshop default can be overridden by a trusted service boundary for one
Wish:

```python
result = workshop.run(wish, playtest_rounds=6)
```

`playtest_rounds` must be an integer from 1 through 100. Workshop records it
with the Wish and exposes it to custom Make and Playtest contexts. It is the
maximum number of Make–Playtest improvement rounds, not the number of AI games
inside a round.

The checkout, quote, or product tier may select the allowance. Free-form Wish
text cannot authorize spend or raise it. A larger allowance buys more chances
to find and repair problems; it **never changes required evidence, weakens a
gate, lowers a threshold, or permits Instructions and Deliver after failure**. When the
allowance is exhausted, the run stops truthfully.

## Preserved laboratories are provenance

Alice's invented-game laboratory already has stronger local leases, evidence,
release, physical-production, and effect-reconciliation machinery. Bob's
preserved board-game laboratory has useful queue, research, budget, simulation,
reward, draft, and readback behavior. Both also exercise older shared artifact
and outside-effect boundaries.

Those facts are evidence for Workshop's extracted workflow, not proof of 0.5
adoption and not active category ownership. Alice's bundled classics profile
does not invoke Blindcap. Bob's and Leo's canonical profiles use the same shared
Make/CAD and Playtest path as the other inventors. Their optional custom hooks
must preserve exact Taste, product, evidence, tool-version, budget, and
external-effect identities. Until golden fixtures show parity, each legacy
laboratory remains separate and every stronger invariant stays in place.

Some native files, commands, database columns, and event payloads retain older
terminology. They remain only because renaming persisted operational state can
break replay or create a second authority. They are not additional 0.5 jobs.

Earlier team prototypes may inform shared Workshop implementation, but they do
not belong to the inventor collection. This checkout starts with five bundled
examples; the catalog is intentionally open to additional inventors, including
multiple Tastes in the same product category.

## What offline checks prove

The repository checks prove contracts and fail-closed behavior without paid
providers. They cover profile discovery and entry points, exact Taste and
artifact binding, truthful waits, per-Wish allowances, feedback loops,
tamper rejection, schema and skill locks, credential exclusion, and ambiguous
outside-effect handling.

Manager checks additionally prove that a thousand-inventor catalog remains
discoverable without loading a thousand full Taste bodies, the exact finalists
are considered, non-routable or stale candidates fail closed, ties resolve
deterministically, all-rejected shortlists wait, and one assignment cannot
silently become a standing schedule. These checks do not prove the semantic
judge's real-world taste or the quality of its chosen inventor.

They do **not** prove that a real product was invented, enjoyed, printed,
published, packed, handed to a carrier, or delivered.

Run the shared checks from the repository root:

```bash
python3 tools/scan_secrets.py
python3 tools/verify_skill_locks.py
python3 tools/verify_snapshot_locks.py
workshop inventors --root inventors --check-entrypoints
PYTHONPATH=src python3 -m unittest discover -s tests -t . -p 'test_*.py'
git diff --check
```

Then run each profile's declared checks. No offline check should require a
model credential, catalog credential, printer, carrier, or paid service.

## Next adoption slices

1. Connect real semantic retrieval and judgment to the one-Wish Manager and
   rehearse explained routing across a large catalog, including ambiguous,
   close-margin, stale, and all-rejected shortlists.
2. Prove the shared Invent, Make/CAD, and Playtest workers preserve Alice's known rules
   while producing a genuinely personal edition.
3. Prove the shared workers invent, create, and execute Leo's games, including
   seeded AI-player simulation and the 1,000-game gate.
4. Prove the shared workers invent, create, and test Bob's moving machines without
   routing those Wishes into the preserved board-game laboratory.
5. Add an inventor-specific Make or Playtest override only when a category
   truly needs behavior the shared workers cannot express.
6. Rehearse one exact Wish per category through truthful waiting, then through each
   real capability as it becomes available.
7. Enable Instructions after exact AI Playtest evidence, then let Deliver own
   exact printing, physical QA, packing, and carrier evidence.
8. Collect Reviews only after delivery and feed them into a future revision of
   the same toy and future Wishes without rewriting the completed run.

The target architecture is not a claim about current completeness. Adoption is
complete only when the selected profile crosses every typed boundary with the
same or stronger evidence than the code it replaces.
