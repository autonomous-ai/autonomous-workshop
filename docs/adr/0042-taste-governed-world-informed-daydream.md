# ADR 0042: Make Daydream Taste-governed and world-informed

- Status: Accepted
- Date: 2026-09-03
- Owners: Daydream, Inventor roster, Invent, Workflow, and Runtime
- Relates to: ADR 0012 (native runtime), ADR 0016 (effort routes), and the
  Design Vault contract

## Context

Daydream currently gives a named Inventor its exact `TASTE.md`, a lexical
catalog of prior work, a compact notebook, and a random situation/twist. The
native turn searches for prior art and writes one idea; a separate Judge turn
predicts whether the named route can build it.

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
  Judge advice and downstream outcomes cannot improve a later Dream;
- the Design Vault begins at Invent and writes shared learning only after a
  sealed Playtest, leaving Daydream and the Spark/Forge fast paths outside the
  learning loop; and
- the single Judge decision conflates Taste, novelty, opportunity, proof mode,
  desirability, and route feasibility.

Making Python generate candidate ideas, select trends, rank semantic quality,
or implement a feedback/reward loop would solve these gaps at the wrong
boundary. ADR 0012 assigns cognition and tool use to the native Manager while
the host owns exact inputs, contracts, identity, budgets, and gates.

## Decision

Daydream is the pre-Wish creative research boundary. It seals one **creative
product thesis**, not an engineering solution and not a `NativeInvented`
contract.

The thesis owns:

- the current opportunity or durable human tension;
- the exact Inventor Taste promises and rejections that govern the idea;
- the physical action, response, payoff, and anti-generic signature;
- a source-backed novelty thesis and bounded search scope;
- an observable proof mode and falsifiable kill criteria;
- a route-capability floor; and
- exact provenance for the world, portfolio, Vault, memory, Manager, and
  Inventor inputs used by the Dream.

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
Design Vault knowledge, Judge predictions, build outcomes, Factory activity,
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

### Knowledge and memory planes

Daydream keeps four boundaries distinct:

1. **Inventor memory** records prior theses, rejection reasons, Judge advice,
   and evidence-backed reflections relevant to that Inventor.
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

### Judge

The independent Judge remains a separate short native Goal. Its current task
expands from one generic still-render bet to a conjunctive falsification record:

- exact Taste fidelity;
- source-backed opportunity grounding;
- mechanism/play novelty rather than theme novelty;
- an observable anti-generic signature under the declared proof mode;
- fit with the named route;
- desirability worth spending a build on; and
- a calibrated prediction of the downstream Make result.

The host accepts `build` only when every required dimension passes and all
identity hashes match. It validates booleans, enums, bounds, and exact bytes;
it does not interpret creative prose. Judge confidence remains a prediction,
never independent evidence. Later outcome processing compares the prediction
with actual downstream gates instead of treating confidence as truth.

### Outcome and lineage

Every Dream keeps a stable lineage through `daydream_id`, idea hash, Wish id,
product id, canonical concept and Made hashes, Release hash, Factory design id
and slug, Inventor id, Taste hash, Manager/runtime profile, and every context
snapshot used. Host-owned lifecycle and effect code append only facts it
actually observes.

Judge rejection, novelty rejection, Make admission, Make gate results,
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
- Historical schema-v1 ideas and verdicts remain readable with their exact
  hashes. New Daydreams use versioned contracts and do not reinterpret old
  records.
- Fresh world sources and outcome feedback increase prompt-injection and data-
  poisoning exposure, requiring bounded untrusted inputs, provenance, and
  evidence-class separation.
- The Design Vault can compound learning across product runs without becoming
  the Inventor's aesthetic authority.

## Compatibility and migration

Existing sealed Daydreams, notebooks, saved `--idea` builds, and product runs
remain valid. New fields use new schema versions; parsers dispatch by version
instead of changing the canonical representation of historical objects.

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
- Daydream workspace tests prove only the selected validated Inventor's exact
  declared skills are materialized and no credentials are copied.
- Judge tests require every independent dimension and reject a `build` that
  contradicts any one of them.
- Novelty tests retain the deterministic lexical floor and add structural
  fingerprints without claiming exhaustive global novelty.
- Notebook tests prove rejection advice and downstream factual outcomes reach
  a later Dream without mutating Taste.
- Source-checkout and installed-wheel acceptance tests discover the same prior
  work and Inventor assets.
- A focused end-to-end loop runs repeated Daydream and Judge Goals, observes
  the exact second Dream context after the first outcome, and demonstrates
  repair rather than repetition.
- A production comparison across materially different Inventor Tastes and all
  three routes must show stronger blind preference and downstream admission
  without reducing portfolio diversity; no unit test alone establishes
  creative leadership.
