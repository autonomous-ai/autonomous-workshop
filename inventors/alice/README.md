# Alice

Alice is an autonomous inventor for original **3D-printable** board games. She runs as
a restartable multi-agent service, not one endless chat. Every research claim,
design change, playtest, print, decision, and publication is an immutable event.

[`TASTE.md`](TASTE.md) defines Alice's creative choices and explicit rejects.
Alice loads it through Workshop, places its exact content and SHA-256 in every
creative agent request, and rejects a result if Taste changes during the call.

Alice follows the same short promise as every inventor in the Workshop:

```text
CUSTOMER          WISH --------------- WAIT ------------- RECEIVE
                                          |
ALICE              Taste + workflow + Alice's higher inspection bar
                                           |
WORKSHOP            MAKE -> INSPECT -> PACK -> SEND
```

`BOX` means the physical thing the customer receives. It is not a ZIP file or
a database state. Today Alice implements the guarded backstage work; direct
Wish intake and automatic delivery remain future Doors.

The target is **one genuinely good game per week**. Alice may work every day;
she does not publish on a clock. A game ships only when independent blind human
playtests, physical production evidence, safety/IP review, and unit economics
all pass the pinned policy.

## What is implemented

- Crash-safe SQLite task leases, retries, candidates, evaluations, experiences,
  publications, and a hash-chained append-only event ledger.
- A bounded role organization with interacting book, history, invention,
  simulation, human, physical, market, send, learning, and meta loops.
- A concrete locked-down Codex app-server provider with isolated credentials,
  strict structured output, process-group deadlines, and deterministic fixture
  mode for tests.
- Hard publication gates plus an evidence-weighted multi-objective quality
  score that same-model grading cannot unlock.
- A Workshop Pack boundary: Alice's `pack.product` task passes the exact
  inspected production manifest to
  `pack_artifact()`, records `_workshop_pack`, and calls `inspect_pack()` again
  immediately before any Shop Door send. Alice's existing production-manifest
  hash remains authoritative and must equal the packed `product.json` entry.
  Older `publish.*` task rows remain replayable but are never newly scheduled.
- The always-on service folds the explicit, clean
  `workshop/src/inventor_workshop` checkout into Alice's runtime identity and sealed
  execution snapshot. Every worker identity check hashes that mutable checkout,
  while a scheduled child can only import the owner-only Workshop bytes that were
  verified and sealed for its installed identity. Sealed processes use
  `python -I -S`, disabling site packages and executable `.pth` startup hooks
  before the release source is added.
- A contextual Thompson-sampling learner for choosing improvement actions from
  verified held-out outcomes. Alice cannot edit or activate her own gates.
- Strict command-adapter contracts for corpus, playtest, human, CAD, market,
  order, print, and outcome systems, plus built-in adapters for the existing
  board-game Shop Door operator and Vibe public flip. They are disabled and
  uncredentialed by default.
- A connected text2game CAD/DFM runtime and deterministic Vibe exporter. It
  requires clean text2game and text2cad checkouts at exact Git commits plus
  byte-pinned Git, Codex, CAD-Python, slicer, slicer-profile, and printer-
  calibration inputs. It copies only an explicit reviewed runtime allowlist
  into a private per-operation workspace—never either legacy publisher or a
  credential-like backup—and runs the pinned deterministic
  consistency check before any model call, then runs phases 1, 2, and 3 behind
  durable reconciliation fences. The export preserves the exact accepted rules,
  source/CAD hashes, storefront idea, and complete project lineage. Peter-
  derived calibrated-fit, strict STL-topology, and fail-closed motion validators
  independently check its output.
- Dry-run, draft, and live effect modes with immutable inputs and durable
  operation keys. The first operational milestone is `draft`: Alice creates the
  complete private Shop Door product page, then stops for Dee's one-click review
  and public flip. Automatic public release is a separate, disabled `live`
  capability. Alice reuses the existing Vibe page pipeline; it does not recreate
  its visuals, copy, or video work.
- A paid-order orchestration contract that verifies the confirmed publication
  product hash, SKU, profile, material specification, BOM, and packing recipe; creates
  one durably keyed print job per order; then binds QA, shipment, and tracking
  to that exact job and recipe. No operational order, print, QA, or shipping
  adapter is included in this checkout.

## Activation status

The Workshop runtime and offline safety suite are implemented, but this checkout is
not a live inventor or a completed deployment. No service has been installed
and no real Shop Door draft has been created by Alice. The connected text2game
adapter is disabled by default and still needs an authenticated dedicated Codex
home, its exact external CAD/slicer toolchain, a measured printer calibration,
and the other real evidence boundaries. The default fixture cannot invent or
provide external evidence and is rejected in `draft` and `live`. No production
token or operational fulfillment adapter is checked in.

Alice's first shipped game, **Blindcap: Duel**, is preserved under
[`games/blindcap-duel`](games/blindcap-duel). It was completed through the
manual Vibe/CAD handoff while the unattended runtime remained disabled, so it
is evidence of the product workflow rather than evidence that the 24/7 service
is activated.

`auto_publish_when_eligible` is false by default: a verified **private** Shop Door
draft is the current release boundary, and Dee publishes it manually after
review. Future automatic public publishing remains fail-closed until the Shop Door
advertises and enforces atomic revision/packet, SKU/price/currency, and
rich-page contracts described in
[INTEGRATIONS.md](INTEGRATIONS.md). `alice doctor` accepts an effectful mode only
after every required boundary returns an authenticated, version-matched,
read-only diagnostic; having a command in config is not readiness.

## Quick start

```bash
cd inventors/alice
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e ../../workshop -e .
python -m unittest discover -s tests -v
alice init
alice status
alice doctor
alice tick
```

`alice run` is the persistent worker. Fixture mode exercises the harness but is
deliberately unable to create publication evidence. See
[OPERATIONS.md](OPERATIONS.md) for the future activation runbook and adapter
contracts; it does not describe a currently operational deployment.

## Read in this order

1. [ARCHITECTURE.md](ARCHITECTURE.md) — system, loops, roles, and invariants.
2. [EVALUATION.md](EVALUATION.md) — publication gates, reward, and learning.
3. [INTEGRATIONS.md](INTEGRATIONS.md) — Workshop, Shop Door, CAD, and simulation.
4. [RESEARCH.md](RESEARCH.md) — source review and rejected designs.
5. [OPERATIONS.md](OPERATIONS.md) — running the service safely.

## Definition of done for a game

“Perfect” is not a score Alice can honestly prove. The operational target is a
publishable game: no critical gate failure, every quality dimension above its
floor, enough independent evidence, three or more blind groups who can teach
and finish it without coaching, spontaneous replay demand, a successful real
print, and viable landed economics. Published outcomes continue feeding the
learner; a published game can be revised or retired, but its evidence history
cannot be rewritten.

The pre-Alice market context is real but deliberately narrow: two distinct
3D-printable chess-set designs received purchases before Alice existed; San
Francisco is one of them. Unit counts are not yet recorded. This context cannot
unlock a release or train Alice's learner; it only says the category has an
early willingness-to-pay signal.

An improvement to a published game always appends a version to the same exact
Shop Door design ID and slug. Alice must block if that revision-only operation is
unavailable; she may never fall back to a first import or create a duplicate
listing. Every Alice-authored Shop Door description ends with the exact suffix
`By Alice.`.
