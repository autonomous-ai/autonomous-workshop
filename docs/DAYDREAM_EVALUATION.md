# Daydream evaluation

Status: implementation-loop evidence, 2026-09-03

This report records the focused Daydream-only evaluation used while building
the Taste-governed, world-informed creative-thesis path. It is deliberately not
a claim that Workshop is already the world's best product-creation system.
That claim needs blind comparison and downstream build evidence.

## What was exercised

- Real native Codex Daydream and independent Judge sessions, not model fakes.
- Live web-search telemetry required by the host.
- Four materially different Inventor Tastes: acoustic (`sonora-reed`), optical
  (`luma-vale`), abstract rules-play (`abo`), and compact tactile mechanism
  (`pico-press`).
- Spark, Forge, and Quest route judgments.
- Exact prior-memory id/hash binding, `repaired` versus `abandoned` disposition,
  and independent `learning_closure` judgment.
- Only Daydream and Judge. Invent, Make, Playtest, Release, Factory, and the full
  Workshop loop were intentionally not run.

The development loop used a private temporary Workshop home so every later
Dream saw the earlier exact notebook records. Each row below is a separate
sealed thesis and Judge verdict. Constitution hashes changed as repeated runs
exposed system-level defects and the implementation was repaired.

| Inventor / route | Thesis | Judge result | Failed checks |
| --- | --- | --- | --- |
| Sonora / Spark | Doublet Arc | dream-again | proof, route, handoff, learning |
| Sonora / Spark | Countback | dream-again | route, worth, learning |
| Luma / Forge | Narrowcast Window | dream-again | opportunity grounding |
| ABO / Quest | Tallyweave | dream-again | proof |
| ABO / Quest | Common Passage | **build** | none (9/9) |
| Luma / Forge | Light Changes Address | **build** | none (9/9) |
| Sonora / Spark | The Table Takes the Count | dream-again | worth, learning |
| Sonora / Spark | Forksong Yoke | dream-again | route |
| Pico Press / Spark | Keelcode | dream-again | grounding, route, worth |
| Pico Press / Spark | Pedalover | dream-again | proof, handoff |

The accepted theses remained structurally different. `Common Passage` is a
rules-play system in which neutral bars exchange open and blocked cells in a
shared negative-space graph. `Light Changes Address` is a one-slide ambient-
light relay that transfers a complete aperture between direct view and a
receiver. The rejected Spark acoustic and tactile candidates did not collapse
into either family.

## Defects the loop found and repaired

1. A notebook could contain advice without proving that the next thesis used
   it. Schema-v3 added exact content-hashed learning traces and a ninth
   conjunctive Judge check.
2. The first implementation marked a cited memory resolved even when the Judge
   failed `learning_closure`. Now only a later Judge pass on that dimension can
   close the referenced memory.
3. Judge advice asked Daydream for dimensioned coupons, crossing into Invent or
   Make. The Judge can reject route fit, but its advice must change the thesis,
   select a capable route, or abandon the direction.
4. Source-backed tension and speculative product motivation were being mixed.
   Schema-v3 now requires an explicit `evidence_boundary` that states what the
   sources do not establish.
5. One rules-play proof rejected every exhaustive optimal-play outcome. The
   native pre-mortem and Judge now require kill criteria to be jointly
   satisfiable, not merely individually severe.
6. Several acoustic concepts were solved demonstrations with no reason to
   return. Worth-building now asks what decision, discovery, mastery,
   expression, or changing causal response remains after the first reveal.
7. Requiring every unresolved memory would eventually exceed the five-entry
   learning bound. The newest unresolved memory is required; up to four older
   relevant memories may also be closed, while all remain visible as warnings.

The next native attempts reflected these repairs rather than merely changing
their prose. Tallyweave's impossible proof was abandoned for Common Passage's
jointly passable balance, policy-separation, choice-diversity, and reciprocal-
path gates. Narrowcast Window's unsupported private-discovery premise was
reworked into Light Changes Address with a bounded evidence seam and an
exclusive two-output optical proof. Sonora's later Forksong Yoke passed worth
and learning after earlier attempts failed both, but was still correctly
rejected as Forge-scale work submitted to Spark.

## Cost and selectivity observations

The real creative turns took roughly six to ten minutes in this sample. Native
session receipts reported about 1.34M–2.72M cumulative input tokens, of which
roughly 1.24M–2.56M were cached, and about 14k–26k output tokens. These counters
are runtime accounting totals, not unique prompt bytes.

After notebook presentation changed from “cite every unresolved memory” to
“newest required, older relevant,” the comparable Sonora run fell from about
2.72M total / 157k uncached input tokens to about 1.50M total / 106k uncached,
and from roughly ten to seven minutes. A larger controlled sample is needed
before treating that as a stable performance result.

Acceptance rate is intentionally not the target. The Judge rejected:

- attractive but unsupported demand bridges;
- one-shot demonstrations without post-reveal value;
- Spark theses with coupled engineering unknowns that belonged on Forge;
- mutually impossible proof gates; and
- an action/response contradiction about which physical paddle became a foot.

Those are useful rejections, not benchmark misses.

## Deterministic verification

The focused suite covers portable-finalizer/host parity, v1/v2 identity
compatibility, v3 learning hashes, stale and mismatched memory rejection,
Judge-gated closure, live-search telemetry, exact time/Taste/route provenance,
Inventor and Vault materialization, novelty/portfolio memory, Wish admission,
and a scripted two-turn Daydream repair loop.

The production-like runs above add evidence that the native system can use the
contracts in practice. They do not prove physical feasibility, player desire,
sales, or downstream gate success.

## Remaining proof before a leadership claim

1. Freeze this implementation and run a preregistered blind comparison against
   the prior Daydream baseline and credible external product briefs.
2. Use unseen Inventors and time windows; judge Taste fidelity, originality,
   grounding, return value, route fit, and portfolio diversity independently.
3. Send a representative accepted sample through the declared Invent/Make (and
   Quest Playtest) routes and compare Judge predictions with host-observed gate
   outcomes.
4. Track latency, uncached tokens, acceptance-to-build yield, repeated failure
   classes, and cross-Inventor structural diversity over a larger sample.

Until those steps pass, the supported conclusion is narrower: Daydream is a
strong, selective, provenance-bound creative-thesis and learning system whose
focused native loop found and repaired real design defects. “Best in the
world” remains the North Star, not a test assertion.
