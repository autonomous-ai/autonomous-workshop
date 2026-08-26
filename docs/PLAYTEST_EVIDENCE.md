# Playtest evidence

Playtest is a native-agent review of one exact Made revision plus deterministic
evidence. It is not a Python role process, a model score, a human test, or proof
that a physical product exists.

## Exact input

The host writes the current Playtest `STAGE.json` with:

- the complete sealed Made contract and product manifest;
- the universal toy blueprint;
- the current Make–Playtest round;
- every required check id;
- the canonical evidence root and contract path;
- checkpoint and gate-subject hashes.

The selected Manager must inspect that exact product tree. Evidence from a
prior Make revision cannot be carried forward.

The universal baseline check ids are `agent-playtest`, `mechanical-check`, and
`printability-check`, derived by the host from
`ToyBlueprint.required_playtest_checks()`. The current `STAGE.json` is
authoritative for the exact required set.

These are Manager-authored digital assessments unless host-replayed evidence
or an authenticated physical receipt explicitly proves more. They do not prove
a successful print, physical fit, durability, hands-on use, or human response.

## Native Playtest Goal, deterministic envelope

The root session creates one native Goal through the selected Manager's goal
control for this Playtest attempt. Its objective is independent evaluation of
the exact sealed Made revision, and its stopping condition is a successful
Playtest finalizer with reproducible evidence and a truthful verdict. A
well-supported `improve` or `block` verdict satisfies the Playtest Goal; the
Manager must not reason a failure into a pass.

The native session may use first-time, optimizing, exploratory, and adversarial
player perspectives; independent native subagents; native search; CAD/render
inspection; domain skills; and seeded simulations. While pursuing the Goal,
the Manager observes the baseline, acts by running inspections, evaluates exact
evidence, and improves missing or weak test coverage. This loop is native
Manager behavior, not a Python program. It records substantive evidence as
files, not chat claims.

The authored Playtest source contains exactly:

```text
checks, feedback, verdict
```

Every required check id appears once. Each check records a real evaluator and
exact version, cites a config file and evidence file inside the Playtest
evidence tree, records an explicit UTC observation time, and includes non-empty
observations. `self-report` and `trust-me` are not evaluators.

The session reads `skill_directory` from immutable `MANAGER.json` and then
runs:

```bash
python <skill_directory>/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

Replace `<skill_directory>` with the exact `MANAGER.json` value; do not type the
angle brackets literally. The finalizer hashes the entire evidence tree,
validates exact check coverage, and writes the canonical Playtested contract
and bound `agent-outcome.json`. It cannot pass the gate or run the improvement
loop. After it succeeds, the Manager completes the native Playtest Goal and
returns to the host. That return does not complete durable host state: the host
validates the exact checkpoint-bound proposal, acknowledges any adapter Goal
sidecar, then rereads the tree, validates the contract, and reruns the trusted
CAD verifier on an isolated copy of the Made product.

## Verdicts and feedback

- `pass` requires every check to pass and no actionable feedback.
- `improve` or `block` requires at least one failed check or actionable finding
  plus evidence-linked feedback.
- Every feedback item identifies its area, severity, observed finding, concrete
  next change, evidence references, and invalidated stages.

A failed Playtest proposes a return to Make. The host preserves that exact
Playtested contract as feedback, advances the bounded round, and invalidates
downstream evidence. The host does not interpret or repair the product. The
Manager reads the evidence and runs the build/check/repair work inside the next
Make Goal; it does not edit previously sealed Made or Playtest files until they
appear to pass.

Reaching the configured round limit stops truthfully. It never lowers required
checks or converts an incomplete result into Release.

## Claim boundaries

| Evidence class | May support | Must not be stated as |
|---|---|---|
| Seeded rules simulation | termination, trace counts, balance/pacing proxies, observed strategies | “people had fun” |
| Native/model inspection | a recorded prediction about clarity, novelty, or Taste fit | human preference or physical fact |
| CAD/kernel check | exact computed topology, dimensions, clearances, interfaces | successful printing or durability |
| Slicer check | predicted output under an exact printer/material/profile | a successful print |
| Render inspection | visible properties of an exact digital render | a photograph of a manufactured object |

Claims must stay attached to their exact evidence class, source file, version,
configuration, and artifact hash. Unknown, missing, stale, malformed, or
mismatched evidence fails closed.

## Release remains bound

Release starts only after Playtest passes for the current Made artifact. Its
canonical `product.json` repeats the exact product artifact hash and Playtest
evidence artifact hash, and its claim map is derived exactly from the passing
checks. Release may write a manual and complete page-ready product content,
but it cannot turn simulation into customer response or CAD verification into
manufacture.

Deliver owns real print, hands-on QA, packing, and carrier evidence. A Factory
page—even a public one—is not delivery evidence.
