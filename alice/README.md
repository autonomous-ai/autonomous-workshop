# Alice

Alice is an autonomous inventor for original **3D-printable** board games. She runs as
a restartable multi-agent service, not one endless chat. Every research claim,
design change, playtest, print, decision, and publication is an immutable event.

The target is **one genuinely good game per week**. Alice may work every day;
she does not publish on a clock. A game ships only when independent blind human
playtests, physical production evidence, safety/IP review, and unit economics
all pass the pinned policy.

## What is implemented

- Crash-safe SQLite task leases, retries, candidates, evaluations, experiences,
  publications, and a hash-chained append-only event ledger.
- A bounded role organization with interacting book, history, invention,
  simulation, human, physical, market, publishing, learning, and meta loops.
- A concrete locked-down Codex app-server provider with isolated credentials,
  strict structured output, process-group deadlines, and deterministic fixture
  mode for tests.
- Hard publication gates plus an evidence-weighted multi-objective quality
  score that same-model grading cannot unlock.
- A contextual Thompson-sampling learner for choosing improvement actions from
  verified held-out outcomes. Alice cannot edit or activate her own gates.
- Strict command-adapter contracts for corpus, playtest, human, CAD, market,
  order, print, and outcome systems, plus built-in adapters for the existing
  board-game rich-draft operator and Vibe public flip. They are disabled and
  uncredentialed by default.
- Dry-run, draft, and live effect modes with immutable inputs and durable
  operation keys. Release authorization and packets are live-only. The public
  path reuses the validated Vibe design and existing downstream rich-page
  pipeline; Alice does not recreate its visuals, copy, or video work.
- A paid-order orchestration contract that verifies the confirmed publication
  packet, SKU, profile, material specification, BOM, and packing recipe; creates
  one durably keyed print job per order; then binds QA, shipment, and tracking
  to that exact job and recipe. No operational order, print, QA, or shipping
  adapter is included in this checkout.

## Activation status

The core runtime and offline safety suite are implemented, but this checkout is
not a live inventor or a completed deployment. The default fixture cannot
invent or provide external evidence and is rejected in `draft` and `live`. No
credentials, production evidence commands, or operational fulfillment adapters
are checked in. Public publishing remains fail-closed until Factory advertises
and enforces atomic revision/packet, SKU/price/currency, and rich-page contracts
described in
[INTEGRATIONS.md](INTEGRATIONS.md). `alice doctor` accepts an effectful mode only
after every required boundary returns an authenticated, version-matched,
read-only diagnostic; having a command in config is not readiness.

## Quick start

```bash
cd alice
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
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
3. [INTEGRATIONS.md](INTEGRATIONS.md) — Panda, Vibe, Factory, CAD, and simulation.
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
