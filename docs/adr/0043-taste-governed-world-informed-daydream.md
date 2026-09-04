# ADR 0043: Make Daydream Taste-governed and world-informed

- Status: Accepted
- Date: 2026-09-03
- Owners: Daydream, Inventor roster, Invent, Workflow, and Runtime
- Relates to: ADR 0012 (native runtime), ADR 0016 (effort routes), and the
  Design Vault contract

## Context

Daydream currently gives a named Inventor its exact `TASTE.md`, a lexical
catalog of prior work, a compact notebook, and a random situation/twist. The
native turn searches for prior art and writes one idea; an early implementation
also used a separate Judge turn to predict whether the named route could build
it.

That is a useful fail-closed MVP, but it is not yet the creative research
system needed for autonomous Inventors:

- it does not deliberately observe current news, trends, changing behavior,
  or demand before choosing an opportunity;
- it materializes Taste but not the selected Inventor's declared native skill
  trees, so specialist method is absent from the Dream;
- one global simplicity and still-render style overrides materially different
  Tastes, including tabletop, acoustic, shadow, kinetic, modular, and
  transformation specialists;
- its notebook remembers only title, one-line summary, status, and hash, so
  downstream outcomes cannot improve a later Dream;
- the Design Vault begins at Invent and writes shared learning only after a
  sealed Playtest, leaving Daydream and the Spark/Forge fast paths outside the
  learning loop; and
- a predictive Judge has no calibrated pre-build ground truth and can become a
  false wall between a creative thesis and the stages that can test it.

Making Python generate candidate ideas, select trends, rank semantic quality,
or implement a feedback/reward loop would solve these gaps at the wrong
boundary. ADR 0012 assigns cognition and tool use to the native Manager while
the host owns exact inputs, contracts, identity, budgets, and gates.

## Decision

Daydream is the mandatory first creative step of every
`workshop start <inventor>` cycle and the pre-Wish creative research boundary.
Supplying `--idea` reuses a Daydream that already completed; it does not skip
the step. The direct `workshop wish` command remains the separate entry point
for a person's already-authored Wish. Daydream seals one **creative product
thesis**, not an engineering solution and not a `NativeInvented` contract.

The thesis owns:

- the current opportunity or durable human tension;
- the exact Inventor Taste promises and rejections that govern the idea;
- the physical action, response, payoff, and anti-generic signature;
- a source-backed novelty thesis and bounded search scope;
- an observable proof mode and falsifiable kill criteria;
- a route-capability floor; and
- exact provenance for the world, portfolio, Vault, memory, Manager, and
  Inventor inputs used by the Dream.

Kill criteria must be discriminating but jointly satisfiable. The native
pre-mortem requires at least one plausible result that
passes them all; an exhaustive set that rejects every possible outcome makes a
thesis impossible rather than falsifiable.

It may carry mechanism hypotheses and Vault leads, but those are explicitly
advisory. Forge and Quest Invent remain authoritative for exact mechanisms,
dimensions, components, materials, construction, tolerances, compatibility,
and research-backed physical facts. Spark Make retains ADR 0016's compound
responsibility to seal the compact `NativeInvented` contract before building.

An accepted Dream becomes the immutable Wish intent. Invent or Make may refine
how to realize it but may not replace its opportunity, Taste promise, action,
payoff, or anti-generic signature. If later evidence proves that no conforming
product can be built, the run records that outcome and a later autonomous loop
creates a new Daydream identity; it does not silently rewrite the old Dream.

### Taste authority

`TASTE.md` remains the human-owned creative constitution. Current signals,
Design Vault knowledge, build outcomes, Factory activity,
and customer evidence may affect what the Inventor notices and what it learns,
but none may rewrite Taste.

Every new thesis cites specific exact Taste text in two directions: positive
promises it makes and rejection boundaries it avoids. The host validates the
bounded structure and exact Taste hash. Semantic Taste judgment remains native
work. A generic global product style may not override an Inventor's hard rule
or specialist method.

### World observation

Every new Dream performs a current-world scan before candidate selection.
Native search is the default zero-configuration source because it already
belongs to the Manager boundary. The resulting thesis records bounded source
references, observation times, and the explicit translation:

```text
current signal -> durable human tension -> Taste-specific physical opportunity
```

Hotness is not a quality score. A headline, character, color, name, or theme
applied to a known object is not a creative translation. The Dream must remain
distinctive when transient theme words are removed. An evergreen opportunity
is valid when the scan finds no current signal worth following, but the scan
and its scope are still recorded truthfully.

World evidence earns the durable tension, not a pre-existing demand for the
exact novel mechanism. The Inventor may make an original physical leap from a
supported tension through its Taste, but may not search backward to rationalize
a seed or ignore evidence that contradicts the proposed setting or payoff.
Schema-v3 makes the epistemic seam explicit with `evidence_boundary`: unsupported
demand, benefit, motivation, and repeat-use claims cannot hide inside the human
tension and must remain visible as creative hypotheses.

Future host connectors may materialize a content-addressed world snapshot with
source, publication and fetch time, region, language, expiry, and trust class.
The host may fetch, normalize, bound, deduplicate, and hash those records. It
must not semantically choose the opportunity. External content remains
untrusted data and credentials never enter the native session.

### Inventor method

The Daydream workspace materializes the selected, validated Inventor bundle as
an official project-scoped custom agent with every exact declared skill tree.
The root Manager owns the one Daydream Goal and finalizer. It may delegate the
bounded creative work to that exact Inventor and then synthesize and finalize
the one thesis. A child cannot write host state or advance a gate.

The universal Daydream constitution defines only process, evidence, and
cross-product safety bounds. It does not prescribe a friendly animal, a
particular motion family, a universal moving-part distance, a single still-
render proof, or one/two parts across every Inventor and route. Inventor Taste,
method, proof mode, and the selected route determine those choices.

Inside its one Goal the native Manager observes, diverges across meaningfully
different interaction families, strips theme from promising candidates,
falsifies them against Taste, prior art, the portfolio, Vault leads, proof
requirements, and route capability, then commits exactly one thesis. These are
native work instructions, not host stages or a Python prompt chain.

Before commitment it privately pre-mortems the selected candidate against nine
independent dimensions: Taste, opportunity, novelty, anti-generic signature,
proof, route, worth, Invent handoff, and exact learning closure. This is native
self-repair, not a score: no candidate list or shadow verdict becomes a host
gate. Whether build time was well spent is learned from downstream evidence.

### Knowledge and memory planes

Daydream keeps four boundaries distinct:

1. **Inventor memory** records prior theses, novelty rejection reasons,
   and evidence-backed reflections relevant to that Inventor. Each exact
   memory record has a content hash. A later schema-v3 thesis must disposition
   the newest unresolved rejection as `repaired` or `abandoned` and bind that
   exact hash; the native pre-commit audit must test whether the claimed
   creative response is substantive. Up to four older unresolved memories may be closed
   when relevant; they remain visible but cannot make the bounded contract
   impossible as history grows.
2. **Design Vault** records shared causal craft knowledge: mechanisms, risks,
   constraints, mitigations, and evidence. Daydream reads it as advisory;
   Invent applies its canonical compatibility gate.
3. **Portfolio history** records designs and structural fingerprints across
   Inventors so a new name or theme cannot hide repetition.
4. **World signals** are time-sensitive observations with freshness and
   provenance; they do not become permanent craft truth merely because they
   were popular.

Model hypotheses, model predictions, deterministic observations, physical
measurements, authenticated Factory events, and customer reports remain
distinct evidence classes. A prediction cannot be banked as an observed fact.

### Evaluation boundary

New Daydreams do not run a separate predictive Judge. The experiment was
retired after replay against real downstream outcomes rejected all four failed
builds but also both published products in the comparison set. Confidence and
conjunctive booleans did not become evidence merely because another native
session produced them; the extra turn instead created an uncalibrated admission
wall and doubled the native-session topology.

The useful dimensions survive as the Inventor's pre-commit falsification audit:
exact Taste fidelity, source-backed opportunity, structural novelty,
anti-generic signature, observable proof, route fit, post-reveal return value,
a clean Invent handoff, and substantive closure of exact prior feedback. The
Goal may repair, simplify, change route, or abandon its candidate before seal.
It may not ask pre-Wish Daydream for dimensions, prototype runs, printed
coupons, simulations, or other Invent/Make evidence.

The sealed thesis proceeds to the chosen Workshop route. Exact novelty failures,
Make gates, signature review, print preflight, Release, publication, Factory,
and future customer facts become bounded learning input for later Dreams. This
does not imply that every build-worthy hypothesis succeeds; it makes the
evidence boundary honest.

### Outcome and lineage

Every Dream keeps a stable lineage through `daydream_id`, idea hash, Wish id,
product id, canonical concept and Made hashes, Release hash, Factory design id
and slug, Inventor id, Taste hash, Manager/runtime profile, and every context
snapshot used. Host-owned lifecycle and effect code append only facts it
actually observes.

Historical Judge records, novelty rejection, Make admission, Make gate results,
signature-review results, print preflight, Release, publication, and future
normalized Factory/Operations outcomes may produce bounded reflection input
for later Dreams. This write-back is route-independent: Spark and Forge must
not be excluded because they omit Playtest. Native Daydream interprets the
facts; Python does not turn them into a semantic reward function.

## Alternatives considered

### Add a news prompt to the existing one-size-fits-all Daydream

Rejected. It would produce more topical versions of the same globally
constrained object family without fixing Taste authority, memory, lineage, or
evaluation.

### Let Daydream seal exact mechanisms and construction

Rejected. That duplicates Invent and makes a short pre-Wish turn authoritative
for engineering facts it has not proved. Mechanism hypotheses are useful;
canonical technical specification remains Invent's responsibility.

### Rank trends, candidates, or creativity in Python

Rejected. It would create the cognitive scheduler, semantic judge, and reward
loop forbidden by ADR 0012, and would pressure every Inventor toward one host-
defined style.

### Use one scalar creativity score

Rejected. Taste fidelity, originality, opportunity, observability,
desirability, and feasibility are conjunctive and differently evidenced. A
single score conceals blocking failures and creates an easy optimization target.

## Consequences

- Daydream becomes more expensive than the MVP's random-seed idea card because
  it performs current observation, specialist work, falsification, and richer
  provenance before spending a build.
- A global visual recipe can no longer guarantee that every idea looks alike;
  each proof mode must be evaluated honestly by its route and specialist.
- Historical schema-v1/v2 ideas and verdicts remain readable with their exact
  hashes. New Daydreams use versioned contracts, create no verdict, and do not
  reinterpret old records.
- Fresh world sources and outcome feedback increase prompt-injection and data-
  poisoning exposure, requiring bounded untrusted inputs, provenance, and
  evidence-class separation.
- The Design Vault can compound learning across product runs without becoming
  the Inventor's aesthetic authority.

## Compatibility and migration

Existing schema-v1 and schema-v2 sealed Daydreams, notebooks, saved `--idea`
builds, and product runs remain valid with their canonical identities unchanged.
New schema-v3 Daydreams bind exact learning traces and carry no predictive
verdict. A valid sealed thesis may become Wish intent directly. Historical
`build` and `dream-again` verdicts remain inspectable but have no authority over
new runs or saved-idea admission. Parsers dispatch by version instead of
changing the canonical representation of historical objects.

The current CLI names remain. A saved new thesis still becomes an ordinary
Wish through `wish_from_daydream`, preserving status/resume and the two-session
boundary. Installed distributions must materialize the same Inventor skills,
prior-work catalog view, finalizer bytes, and context contracts as a source
checkout.

## Verification

- Contract and finalizer parity tests apply the same valid and adversarial
  corpus to host and run-local parsing.
- Every new idea records a current-world scan, exact Taste trace, physical
  opportunity translation, proof mode, anti-generic test, and kill criteria.
- Portable schema validation rejects a source publication time after its scan;
  the host rejects any thesis whose route floor exceeds the selected route.
- Daydream workspace tests prove only the selected validated Inventor's exact
  declared skills are materialized and no credentials are copied.
- Pre-commit prompt tests require every independent falsification dimension;
  compatibility tests prove historical verdicts are readable but non-gating.
- Novelty tests retain the deterministic lexical floor and add structural
  fingerprints without claiming exhaustive global novelty.
- Notebook tests prove rejection advice and downstream factual outcomes reach
  a later Dream without mutating Taste, and that the next thesis closes the
  newest unresolved memory by exact id and record hash.
- Source-checkout and installed-wheel acceptance tests discover the same prior
  work and Inventor assets.
- A focused end-to-end loop runs repeated Daydream Goals, writes an exact
  downstream failure, observes it in the second Dream context, and demonstrates
  repair rather than repetition.
- A production comparison across materially different Inventor Tastes and all
  three routes must show stronger blind preference and downstream admission
  without reducing portfolio diversity; no unit test alone establishes
  creative leadership.
