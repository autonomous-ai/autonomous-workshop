# Product quality and token economics

Autonomous Workshop's North Star is dramatically better toys at dramatically
lower creation cost. “10x the quality at 0.1x the cost” is memorable shorthand
for that direction, not a literal ratio or release threshold. The two
requirements are conjunctive: a cheaper dull toy and an extravagant beautiful
toy both miss the target.

## Cost is a vector, not a made-up total

Codex reports input, cached input, cache-write input, output, and reasoning
output for each native turn. Workshop records those values separately by stage
and derives uncached input. It never adds token categories or infers dollars,
because model pricing and the relative price of cached input can change.

A two-turn Codex CLI probe on 2026-08-30 confirmed the semantics:

| Turn | Input | Cached input | Uncached input | Output |
|---|---:|---:|---:|---:|
| New session | 14,589 | 11,008 | 3,581 | 5 |
| Same session resumed | 17,780 | 14,080 | 3,700 | 6 |

The resumed turn reports its whole effective context again, mostly as cached
input. Therefore gross input is useful capacity telemetry but not a proxy for
fresh context. Compare like-for-like runs on all reported categories and turn
coverage. A cost-improvement claim must not hide an increase in one category
behind a combined total.

## Named production baseline

Moonchase Fox is the first complete schema-v3 Spark baseline:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 24,616,026 | 22,343,631 | 2,272,395 |
| Cached input | 24,101,632 | 22,059,008 | 2,042,624 |
| Uncached input | 514,394 | 284,623 | 229,771 |
| Output | 88,501 | 68,149 | 20,352 |
| Elapsed | 49m 28s | 39m 21s native work | 9m 5s native work |

The public snapshot is `toys/pico-press-moonchase-fox/`. It passed full-tier
CAD and publication gates; Release's visual review also found and repaired real
manual collisions. Comparable Spark challengers should beat that artifact on
quality while materially reducing gross input, uncached input, output, and
elapsed time. Cached, uncached, and output counts remain visible so a nominal
win cannot hide a regression in another category.

The first low-reasoning challenger, Starling Gate, established that runtime
tuning alone is insufficient:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,144,631 | 3,247,116 | 3,897,515 |
| Cached input | 6,983,552 | 3,142,784 | 3,840,768 |
| Uncached input | 161,079 | 104,332 | 56,747 |
| Output | 24,291 | 12,055 | 12,236 |
| Reasoning output | 2,884 | 1,510 | 1,374 |
| Elapsed | 19m 50s | 10m 42s native work | 6m 17s native work |

This cut gross input by about 71% and reasoning output by about 91%, but did not
complete the paired objective. More importantly, its exact imagery did not make the
promised bird-to-shooting-star transformation legible. Release then cost more
input than Make while teaching that unproven promise. The next optimization
therefore moves signature-experience proof into Make, selects the Inventor for
the hardest-to-fake magic rather than fabrication convenience, and batches the
full manual review into one render command.

Pocket Eclipse Menagerie tested those evidence-first instructions:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,957,133 | 3,451,567 | 4,505,566 |
| Cached input | 7,764,992 | 3,336,704 | 4,428,288 |
| Uncached input | 192,141 | 114,863 | 77,278 |
| Output | 32,290 | 18,962 | 13,328 |
| Reasoning output | 5,709 | 4,220 | 1,489 |
| Elapsed | 22m 59s | 13m 33s native work | 6m 54s native work |

It selected Orin Shadow for the Wish's perceptual problem and produced a clean,
truthful manual, but used more tokens and time than Starling Gate. Its final
signature sheet showed object rotations rather than unmistakable shadow
outcomes, and Release made four complete manual render rounds for a one-piece
toy. The one persistent session entered Release with roughly 105k tokens of
effective context and grew to roughly 161k; more than 98% of Release input was
cached. This is the evidence behind Spark v2's 64k automatic compaction ceiling,
hash-bound independent final signature review, and double-sided-card default.
The combined quality-and-economics objective remains unproven until a new
permanent production challenger passes both comparisons.

Mooncoil Dragon then tested Spark v2's compaction and review policy in a real
published run:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | 7,468,236 | 5,734,110 | 1,734,126 |
| Cached input | 7,034,240 | 5,401,088 | 1,633,152 |
| Uncached input | 433,996 | 333,022 | 100,974 |
| Output | 50,674 | 35,873 | 14,801 |
| Reasoning output | 11,186 | 8,076 | 3,110 |
| Elapsed | 44m 43s | 32m 58s native work | 7m 50s native work |

The two-sided manual was concise, clear, and visually strong. Release input
fell about 61.5% from Pocket Eclipse Menagerie's 4,505,566, showing that the
64k compaction ceiling and smaller manual path improved the later stage. Make
input rose about 66%, however. Private aggregate inventory showed repeated
rebuild, render, review, and complete-verifier cycles before the final CAD was
sealed, plus identical final render families in two locations. The prompted
critic even identified that the dragon's central mass competed with the
intended crescent, then affirmed readability anyway. The finished render still
read more as a flat dragon cutout than an unmistakable magical two-truth object.

This evidence changes the next optimization from another runtime knob to a
better work order. New Make runs conduct an unprimed visual read from only the
candidate images before the expensive integrated verifier, allow one focused
visual repair, then perform one stable full verification. One canonical final
render family is sealed. Inventor selection distinguishes the Wish's defining
creative problem from a mechanism that merely carries it. Release names exactly
two complete review packets: initial and final. The target remains unproven.

Moonwake Turn tested that work order in another permanent published Spark:

| Measure | Whole run | Make | Release |
|---|---:|---:|---:|
| Gross input | **>=4,040,564 partial** | **>=2,460,653 partial** | 1,579,911 |
| Cached input | **>=3,823,104 partial** | **>=2,329,472 partial** | 1,493,632 |
| Uncached input | **>=217,460 partial** | **>=131,181 partial** | 86,279 |
| Output | **>=29,364 partial** | **>=18,292 partial** | 11,072 |
| Reasoning output | **>=5,521 partial** | **>=3,956 partial** | 1,565 |
| Turn coverage | 2 / 3 | 1 / 2 | 1 / 1 |
| Elapsed | 1h 20m 45s | includes one 1h timeout | measured turn completed |

Every `>=` value is a measured floor, not a total or a valid reduction claim.
The first Make turn exhausted the historical one-hour boundary without a
terminal usage event, so no token category exists for that turn. The recovery
correctly resumed the same session and completed the toy, but the run cannot
establish either the 4.04M nominal figure or a percentage improvement as its
true economics.

The in-box manual was polished and product-specific. The exact product evidence
still exposed a semantic failure: the Wish asked for a whale leaping *through*
a crescent, while the blind reviewer recorded a crescent *beside* a whale-like
animal and then passed the overall signature boolean. Shared nouns had hidden a
wrong spatial relationship. Private run inventory also showed repeated broad
build/export/verification activity inside the one timed-out turn; a single
stage attempt was not a meaningful inner-loop bound.

Spark v3 addresses those two evidenced leaks without lowering quality gates.
Each new native Spark turn has a frozen 20-minute boundary; one critic gets at
most two rounds and must compare subjects, action, and relationship separately;
and the integrated final CAD verifier refuses to begin until the exact
hash-bound review exists. Quick checks remain available for iteration. The next
permanent challenger must have complete turn telemetry, materially improve the
token/time vector over the named baseline and recent challengers, and win the
blind signature comparison. Until then, the combined quality-and-economics
objective remains unproven.

Nectar After Rain was the first real Spark v3 production attempt. It truthfully
stopped in Make instead of publishing a weak signature experience:

| Measure | Failed Make attempt |
|---|---:|
| Gross input | 2,563,485 |
| Cached input | 2,370,688 |
| Uncached input | 192,797 |
| Output | 17,098 |
| Reasoning output | 3,857 |
| Elapsed | 12m 51s |
| Turn coverage | 1 / 1 |

The blind critic still could not identify the trumpet flower after the one
permitted repair, so no integrated final verification or Release work ran. The
attempt is not an end-to-end cost win and is not a public toy. It does prove
that the bounded funnel can spend far less than Moonchase Fox and refuse an
unconvincing product before downstream cost. A successful challenger must keep
that discipline while actually reaching publication.

Orbit Cradle then completed and published under Spark v3, proving bounded
same-session recovery and the full host effect path. Its telemetry is partial
because one timed-out Make turn and two failed Release turns had no terminal
usage event:

| Measure | Measured floor / result |
|---|---:|
| Gross input | >=2,480,047 partial |
| Cached input | >=2,348,160 partial |
| Uncached input | >=131,887 partial |
| Output | >=16,013 partial |
| Reasoning output | >=2,734 partial |
| Turn coverage | 2 / 5 |
| Wish to publication | 54m 40s |

The run cannot establish a token reduction from those floors. It did expose
two concrete costs: a verification report outside the declared CAD project
caused an avoidable host rejection and third Make turn, while one native
Release failure required an explicit normal CLI resume. More importantly, the
published object passed subject/action/relationship review but remained a
constant-depth extrusion even though its canonical concept promised a
pillow-rounded cabochon. Schema v4 now binds the critic to blind volumetric form
and the concept's anti-generic signature, and the finalizer rejects an
out-of-project verification report before isolated host work. The paired
quality-and-economics objective remains open.

Tempest Lull then tested schema v4 with an unusually explicit Spark Wish: the
cloud had to remain fully volumetric and pillow-like, never a constant-depth
extrusion. It published, but it is a negative production benchmark:

| Measure | Measured floor / result |
|---|---:|
| Gross input | >=6,949,853 partial |
| Cached input | >=6,548,608 partial |
| Uncached input | >=401,245 partial |
| Output | >=48,601 partial |
| Reasoning output | >=9,021 partial |
| Turn coverage | 3 / 4 |
| Wish to publication | 55m 26s |

Make used three native turns, including one 20-minute timeout and one host CAD
rejection. Its first sculptural draft failed thickness. After several narrow
repairs, the session replaced the cloud with a common-depth relief, copied the
old review claims forward with new hashes, and rewrote Spark's compact concept
to describe the regression. The review itself called the result common-depth
while still setting `form_matches_wish: true`. The host correctly rejected a
proposal that locally omitted the failed thickness check, but only after the
proposal and isolated rebuild had already consumed time.

Schema v5 addresses those evidenced leaks without adding another critic or a
Python aesthetic judge. Make now runs narrow mesh and thickness checks before
the visual review; the critic enumerates explicit positive and negative Wish
form constraints with blind evidence and cannot leave blocking defects; and the
finalizer requires the current report to be a passing full-tier run containing
a successful thickness row. Spark concept prose may not normalize a geometry
repair that contradicts the exact Wish. The next production challenger must
show that this tighter order improves both truthfulness and cost.

Moonseed Bloom then challenged Forge with a six-part kinetic celestial flower.
Invent earned some of its extra work: one independent review rejected an
overpacked barrel cam, and the same 23m23s native turn sealed a simpler side
moon-wheel/Scotch-yoke concept. Make exposed the remaining economics failure:

| Measure | Preserved production observation |
|---|---:|
| Invent | 1 turn, 23m23s, passed |
| Make turn 1 | 60m00s, timed out |
| Make turn 2 | 44m58s, failed |
| Make turn 3 | 60m00s, timed out after explicit resume |
| Make turn 4 | 39m48s, proposed; host rejected ambiguous combined entry |
| Make turn 5 | 24m31s, proposed; host rejected changed rebuilt output |
| Make turn 6 | operator stopped after 30s when rejection auto-continued |
| Isolated gate after turn 5 | 19m29s, token-free; verifier passed but exact output changed |
| Make native-turn time | 3h49m48s |
| CLI wall time across wish + one resume | about 4h32m47s |
| Publication | not created |

| Stage telemetry | Input tokens | Output tokens | Measured turns |
|---|---:|---:|---:|
| Invent | 6,705,241 | 48,490 | 1 / 1 |
| Make | 20,073,838 | 46,763 | 2 / 5 completed turns; interrupted turn omitted |

These are stage rows, not a fabricated whole-run sum. Three completed Make
turns timed out or ended without terminal usage and therefore have no token
record. Of Make's measured input, 19,755,136 tokens were cached input; that is
still repeated context volume and remains relevant to scale even when billing
discounts it.

Make spent its visual review before discovering that one printable base had
0.14 mm regions and 0.7% sub-minimum surface at the normal 0.4 mm nozzle. It
then experimented with 0.2, 0.1, and even 0.04 mm nozzle arguments before
returning to the standard profile; later repairs exposed more strict-fit and
thickness failures. Its critic also accepted a coarse prototype/device read,
dominant exposed mechanism, and zoom-dependent star as finished and desirable.

Schema v6 replaces the advisory single-STL preflight with one deterministic
`--print-preflight` mode. It generates every declared printable, runs strict
fit, exports every STL, and runs mesh plus thickness gates at the fixed final
0.4 mm profile. The visual review binds that passing report. Product-run
instructions also make prototype/device reads, dominant exposed mechanisms,
zoom-dependent signatures, raw faceting, unclear state changes, and visible
`largest_risk` caveats blocking rather than cosmetically acceptable. No new
agent, model judge, or retry loop is added.

Comet Choir then tested the new Quest economics profile on a demanding optical
strategy sculpture. Invent sealed a distinctive sleeping sky-whale, captive
eclipse mask, and deterministic game in one 14m49s turn. Make produced an exact
mechanism coupon and four-part CAD project during its first bounded turn, then
the 30-minute boundary preserved those bytes and resumed the same session. The
recovery reused the project and ended after 10m31s without a proposal. Nothing
was published.

Workshop received no terminal usage events, so its ordinary telemetry remains
truthfully unmeasured. Diagnostic counters from the local native session are
recorded here as separate turn observations, not fabricated host telemetry and
not a combined token total:

| Stage / turn | Input tokens | Cached input | Output tokens | Elapsed |
|---|---:|---:|---:|---:|
| Invent turn 1 | 919,268 | 770,048 | 15,436 | 14m49s |
| Make turn 1 | 1,895,614 | 1,632,512 | 28,311 | 30m00s |
| Make recovery | 804,655 | 709,120 | 8,157 | 10m31s |
| Make explicit-resume turn 1 | 2,383,232 | 2,087,680 | 28,341 | 30m00s |
| Make automatic recovery | 1,966,262 | 1,724,160 | 25,750 | 30m00s |

The token reduction versus Moonseed Bloom is material, but the paired objective
still failed. Exact renders read as a faceted blob-like whale attached to a
flat board, with floating pieces and no convincing treble-clef composition.
The session did not falsely publish them. Its final preflight also exposed a
workflow defect: agent-side `verify_project --fresh` removed generated bytes
but the product sandbox protected empty cache-directory removal, causing
`PermissionError`. Product iteration now uses non-destructive print-preflight;
the isolated host remains the sole authoritative fresh rebuild. Deep Make also
requires a cheap exact held-view and signature-view blockout before detailed
parts, explicitly rejecting blob-plus-board, plaque, and floating-piece reads.
New runs freeze those fixes. The preserved run remains resumable with its
historical protocol, and its same session retains the exact failed preflight
and can continue non-destructively from the existing CAD.

One explicit normal CLI resume then confirmed the bounded failure window. The
historical session repeated destructive preflight twice, copied the project
into `cad-final` and `cad-release` workarounds, and eventually switched to
non-destructive preflight. Three smaller parts passed the fixed 0.8 mm wall
gate, while the whale retained localized 0.20 mm regions. Two consecutive
30-minute turns ended without a proposal, so Workshop stopped the invocation
and preserved the exact session instead of opening more attempts. The run was
not resumed again: it had not reached visual repair, Playtest, or Release, and
additional operator retries would spend against a known frozen-protocol dead
end rather than validate the new-run fix.

The resume exposed two more deterministic ordering failures. The first proposal
declared four non-part `*.step.py` entries; local verification selected one with
`--assembly`, but the isolated host has no trusted assembly choice in the Made
contract and rejected it immediately. The next proposal passed a 19m29s
isolated verifier, but the rebuilt exact CAD outputs differed from the proposed
bytes. The old CLI then opened another Make turn because a host rejection resets
the two-timeout recovery streak. The operator stopped that turn after 30s and
preserved the session and every artifact.

That iteration froze `deep-economics-v1.md`: high reasoning was retained for
quality, while context compacted at 32k, each native turn stopped at 30 minutes,
and one CLI invocation stopped after eight native turns. Invent
and Make must prove the hardest causal or kinematic relationship with minimal
exact geometry before detailing the full product, and recovery must reuse
durable passed work. The Make finalizer now also refuses anything other than one
unambiguous non-part combined CAD entry before spending an isolated host gate.
Together with schema v6's all-printable preflight, these changes target the
observed token and retry leaks without weakening any CAD, Playtest, manual, or
publication gate. A fresh Forge and Quest production run remains required to
measure the improvement; policy is not proof.

Starbell Seed was that fresh Quest check. Invent sealed a much stronger
three-part helical seed-to-flower concept in 18m21s, including an explicit
minimal motion coupon and held/signature blockout. Make nevertheless spent
about 23.5 minutes before persisting any product source, batch-wrote the whole
part tree, and reached its first numeric motion proof only near the end of the
automatic recovery turn. It preserved coherent STEP source and a passing 60° /
14 mm motion calculation, but never reached print-preflight, product renders,
Playtest, Release, or publication. Workshop stopped after two bounded Make
turns and the run remains preserved as a negative benchmark.

Host token telemetry again remained unmeasured. Local native-session
diagnostics are recorded separately and are not added together:

| Stage / turn | Input tokens | Cached input | Output tokens | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent turn 1 | 1,261,691 | 1,115,136 | 26,642 | 3,752 | 18m21s |
| Make turn 1 | 1,895,334 | 1,621,248 | 23,493 | 5,905 | 30m00s |
| Make recovery | 2,067,470 | 1,903,616 | 17,856 | 4,723 | 30m00s |

This result separates CAD runtime from workflow latency: individual observed
generation steps took seconds, while most spend occurred before the first
persisted falsifier and during late repair. The prompt-only
`deep-economics-v2.md` iteration did not enforce that ordering: the next Quest
Make again persisted no product bytes for its full first 30-minute turn. It
also exposed that the launcher created for high-reasoning Invent was reused
after the checkpoint moved to Make. The automatic recovery wrote the requested
`review/early-proof/` source within about 4.5 minutes.

That evidence produced `deep-economics-v3.md`: one whole-profile identity kept
the persistent thread stable while Invent actually used high reasoning and
later stages used medium. Context compacted at 24k, one invocation stopped
after eight turns, and the first Make turn stopped at a 12-minute proof boundary
before recovery received the normal 30-minute window.

The identical Three-Sky Seed Wish then tested v3. Invent passed in 15m53s with
473,815 input, 397,056 cached input, 12,132 output, and 1,894 reasoning-output
tokens. The initial 12-minute Make turn again persisted no product file; its
terminal token event was unavailable, so no token count is inferred. Recovery
persisted proof source about 5m43s later and reached an exact passing mechanism
report plus held/signature images. That useful milestone arrived about 17m45s
after Make began, versus roughly 34.5 minutes in the v2 run. The two-turn Make
window therefore fell from 60 to 42 minutes.

The paired objective still failed. The medium-reasoning recovery consumed
1,285,442 input, 1,148,928 cached input, 13,976 output, and 1,139
reasoning-output tokens—more gross input than the comparable v2 high-reasoning
recovery. It produced a crude cylindrical exposed mechanism instead of the
sealed smooth volumetric seed, then its own superficial inspection marked those
pixels as passing. It never persisted the complete product, reached final
preflight, Playtest, Release, or publication. The host stopped after the two
bounded failures and preserved the run.

New runs therefore freeze `deep-economics-v4.md`. Make returns to high
reasoning because medium was neither cheaper nor better in the paired run, but
Make compacts at the runtime's minimum supported 16k while other stages retain
24k. The 12-minute first-proof and 30-minute recovery boundaries remain. Before
detailed CAD, one independent native critic receives only the exact early
blockout images, records the unprompted object/form/control/action/relationship
read, then receives the Wish and concept and checks every positive and negative
held-form constraint. A generic, plaque-like, box-like, container-like, or
exposed-mechanism reading fails and gets one repair at most. This early report
is evidence for native judgment, not a new host aesthetic gate; the existing
hash-bound final signature review, deterministic CAD checks, Playtest, manual,
and publication gates remain unchanged. Fresh paired Quest and Forge production
runs must still prove v4 improves both quality and economics.

The identical Three-Sky Seed Wish then tested v4. Invent's first high-reasoning
turn wrote a complete source but reached its 30-minute boundary; a 2m23s
recovery passed the Invent gate. Make's 12-minute proof turn and 30-minute
recovery made 40 tool calls yet wrote zero Make files. The preserved run never
reached preflight, Playtest, Release, GitHub, or Factory. Local session
diagnostics—not host telemetry—reported the following separate counters:

| Stage / turn | Input | Cached input | Output | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent initial | 945,603 | 835,328 | 13,902 | 1,353 | 30m00s |
| Invent recovery | 231,484 | 190,976 | 2,250 | 238 | 2m23s |
| Make proof | 326,804 | 259,584 | 3,563 | 583 | 12m00s |
| Make recovery | 638,973 | 519,680 | 6,210 | 715 | 30m00s |

Tool-call inspection showed repeated instruction/reference reads, skill-tree
enumeration, help discovery, and interpreter checks before source creation.
The lower raw Make token count was therefore a false economy: it bought no
artifact. Cost optimization is evaluated per completed desirable product.

New runs now freeze `deep-economics-v5.md`. Invent begins high for 20 minutes;
a recoverable continuation gets 10 minutes at medium to seal the strongest
existing source rather than restart. Make begins with an eight-minute medium
proof phase and exact host-supplied CAD commands. Optional references, help,
and delegation wait until proof source, renders, and blind review exist. A
canonical checkpoint-bound `.make-proof-ready.json` ends only that native turn,
then the same Make Goal resumes at high reasoning for its 30-minute final
phase. Every stage compacts at 24k; Playtest and Release remain medium; the
eight-turn command cap remains. The marker is only a liveness hint, never a
quality gate or transition. Existing final CAD, blind-review, Playtest, manual,
publication, and GitHub requirements remain unchanged. A completed Quest and
Forge are still required before v5 deep-route economics can be called proven.

The same Three-Sky Seed then tested v5. Invent persisted its source before the
20-minute boundary and passed during 1m40s of decisive medium recovery, cutting
v4's 32m23s Invent to 21m40s. Make's first eight-minute proof turn wrote no
file; recovery wrote a reusable proof source after about one minute, but no
STEP or render followed. The host stopped after the second bounded Make turn,
preserving a checkpointed run with no downstream or publication claim.

Tool outputs exposed an execution-contract defect. The host prompt invoked the
CAD `scripts/gen` package directory directly and received permission denied.
Recovery improvised `python -m gen`, but its authored source had a top-level
`result` rather than the required module-scope `gen_step()`, so the CAD loader
rejected it. The rest of recovery was spent inspecting internals and retrying.

| Stage / turn | Input | Cached input | Output | Reasoning output | Elapsed |
|---|---:|---:|---:|---:|---:|
| Invent initial | 618,515 | 519,424 | 10,546 | 606 | 20m00s |
| Invent recovery | 117,521 | 76,544 | 1,181 | 142 | 1m40s |
| Make proof | 193,995 | 156,672 | 2,333 | 578 | 8m00s |
| Make proof recovery | 312,328 | 261,888 | 5,178 | 578 | 8m00s |

V5 reduced failed-run exposure from v4's 2,142,864 input and 25,925 output
tokens over roughly 75 minutes to 1,242,359 input and 19,238 output tokens over
roughly 38 minutes, and it left source bytes. That remains failed-run spend,
not product cost.

New runs therefore freeze `deep-economics-v6.md`. Budgets and phase boundaries
stay unchanged; the correction supplies exact `$WORKSHOP_PYTHON`-prefixed
`gen`, `export`, and `render_product` commands and requires one module-scope
`gen_step()` returning the shape. A real acceptance test runs those commands
from a path containing spaces and verifies STEP, STL, held PNG, and signature
PNG outputs. V6 still must complete and publish fresh Quest and Forge products
before deep-route economics are proven.

The same Three-Sky Seed then tested v6 through the regular production CLI.
Invent passed after its 20-minute initial turn and 4m08s recovery. Make's first
eight-minute turn wrote no files. Recovery used the now-correct commands and
produced valid proof source, STEP, STL, a 900×900 held render, and a 2700×900
three-pose signature sheet. The object was fully volumetric and had a captive
halo, but the three distinct skies and action were not unmistakable. No blind
review or proof marker existed when the second bounded Make turn ended, so the
run stopped without Playtest, publication, or GitHub product claim.

The exact execution trace found three remaining leaks: the first generation
attempt could not write `ezdxf`'s user-home font cache; the proof phase loaded
and reread roughly 59.5 KB of root/Workshop/Make/CAD guidance even though the
host supplied the narrow interface; and generate, export, and render occupied
separate reasoning cycles. The critic started only 46 seconds before timeout.

| Root stage / turn | Input | Cached input | Uncached input | Output | Reasoning output |
|---|---:|---:|---:|---:|---:|
| Invent initial | 323,888 | 266,752 | 57,136 | 3,604 | 369 |
| Invent recovery | 184,484 | 149,504 | 34,980 | 5,537 | 200 |
| Make proof | 189,382 | 157,696 | 31,686 | 2,800 | 1,323 |
| Make proof recovery | 197,906 | 161,792 | 36,114 | 2,343 | 91 |
| **Root total** | **895,660** | **735,744** | **159,916** | **14,284** | — |

Three bounded children separately reported 140,197 input and 2,910 output.
Together the observed root and children reported 1,035,857 input and 17,194
output tokens over about 40m15s. V6 cut root input 28% and output 26% versus
the v5 failed run, but this is still failed-run exposure, not product cost.

New runs now freeze `deep-economics-v7.md`. The host binds a private writable
run cache before Codex starts. The broad CAD skill is deferred until final
Make, the blind critic starts before proof generation without seeing the Wish,
and generate/export/render run in one foreground batch. The root performs the
revealed comparison without a second child turn. V7 changes scheduling and
startup only; every final product and publication gate remains unchanged.
Fresh terminal Spark, Forge, and Quest evidence is required before the
cross-effort economics goal is proven.

The identical Quest then tested v7. Invent passed after 20 minutes plus 5m45s
of recovery. Make wrote no product bytes in either eight-minute proof turn.
The first turn used separate native cycles to read root instructions, the
Workshop skill, Make reference, and stage packets, then expired. Recovery used
separate cycles to create the Make Goal, inspect an empty tree, spawn the early
critic, and create an empty directory, then expired before source authoring.

| Root stage / turn | Input | Cached input | Uncached input | Output | Reasoning output |
|---|---:|---:|---:|---:|---:|
| Invent initial | 344,365 | 290,048 | 54,317 | 3,075 | 392 |
| Invent recovery | 166,486 | 125,184 | 41,302 | 4,368 | 149 |
| Make proof | 119,610 | 93,952 | 25,658 | 781 | 154 |
| Make proof recovery | 107,084 | 77,824 | 29,260 | 888 | 94 |
| **Root total** | **737,545** | **587,008** | **150,537** | **9,112** | **789** |

V7 reduced root input about 18% and output 36% versus v6, but produced fewer
durable Make bytes. It is another false economy, not product cost.

New runs then froze `deep-economics-v8.md`. Early Make receives one 16-minute
medium runway. Mandatory reads are one bounded batch; the Manager does not
spend a call on `get_goal`, an empty-tree check, or directory-only work; source
and its directories are the next edit. The exact CAD commands remain one batch
with the private cache. Root inspection owns the cheap early direction check;
the independent blind critic remains mandatory at the final hash-bound review.
Fresh terminal evidence remains required across all three efforts.

New runs now freeze `deep-economics-v9.md`, retaining v8's proof runway and
prompt discipline while raising automatic compaction from 24k to 256k at every
deep stage. Frozen v8 and older runs keep their original 24k ceiling.

### V8 production result: liveness recovered, state evidence and final handoff failed

The next identical Three-Sky Seed Quest,
`wish-20260831-123720-43b4ec40`, proved that v8 fixed the immediate liveness
failure. Early Make wrote proof source after 5m44s and completed the marker in
12m14s. It also proved that the old signature interface answered the wrong
question: `--motion-sheet=-12,0,12` showed one unchanged object from nearby
viewpoints, and the root incorrectly accepted those nearly identical frames as
three skies.

Final Make then used a full 30-minute high turn on documentation and API search
without writing product source. Recovery wrote source after about 9m30s and
generated the three part STEP files, assembled STL, and renders, but strict fit
failed on the upper-shell print datum, disconnected bodies, and missing project
fit audit. The visibly rough, repeated-state product was not Playtested,
released, published, or snapshotted.

| V8 root/child total | Input | Cached input | Uncached input | Output | Reasoning output |
|---|---:|---:|---:|---:|---:|
| Failed Quest | 1,602,623 | 1,265,920 | 336,703 | 25,242 | 2,147 |

These totals were reconstructed from the local root and child Codex turn
telemetry because timeout turns were not all persisted into Workshop's simple
stage counter; the per-turn native log is the source for this diagnostic only.
V8 produced real geometry but spent too long before final source and did not
produce a toy.

New runs therefore freeze `deep-economics-v10.md`. The complete Inventor roster
is first ranked from a compact exact-Taste-header index and only the best three
full agents are opened. Early Make creates three exact state STLs and a
fixed-camera `--state-sheet`; visually indistinguishable frames fail
deterministically, while motion sheets remain viewpoint-only. The host requires
all three state source/STEP/STL families before accepting the proof marker.
Final Make then gets a 15-minute source-first handoff before normal recovery,
preventing another 30-minute documentation-only turn. V10 is still unproven
until a fresh terminal product passes and publishes.

## Quality is comparative evidence, not a model score

Host gates prove contracts, exact bytes, CAD properties, and publication; they
do not prove delight. Compare a challenger against a named baseline without
revealing which workflow produced which toy. Review the exact product renders,
interaction/rules, printable files, and manual on these dimensions:

- Wish fit and emotional promise;
- novelty and an unmistakable anti-generic signature;
- strength of the physical play or transformation moment;
- coherence of form, mechanism, components, and constraints;
- product-render legibility and desirability;
- first-owner clarity and delight of the in-box manual;
- deterministic CAD/printability evidence and truthful limitations.

The “10x quality” shorthand means a clear experience-category leap, not ten
times a self-assigned number: the challenger is strongly preferred on the
signature experience and most other dimensions, loses none of the deterministic
gates, and has no new unsupported claim. Keep the raw comparison and reviewer
notes beside the benchmark; do not turn them into lifecycle gate authority.

## Optimization order

1. Remove retries, timeouts, and repeated passed work.
2. Compact tool-heavy native history while keeping exact state in durable
   workspace files, stage packets, and sealed evidence.
3. Reduce tool calls and tool-output context with bounded inspection and one
   quick-iteration/final-verification funnel.
4. Use the roster once, choose one Inventor, and spend depth on one signature
   interaction instead of broad candidate fan-out.
5. Carry sealed summaries, manifests, and renders forward instead of resurveying
   stable source at every stage.
6. Reuse deterministic CAD, render, and manual layout primitives so native
   reasoning chooses the product rather than repeatedly rebuilding plumbing.
7. Tune frozen runtime policy only from comparable production evidence. A
   cheaper configuration is not a win if blind product preference falls.
