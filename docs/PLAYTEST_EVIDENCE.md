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

Codex must inspect that exact product tree. Evidence from a prior Make revision
cannot be carried forward.

The universal baseline check ids are `agent-playtest`, `mechanical-check`, and
`printability-check`, derived by the host from
`ToyBlueprint.required_playtest_checks()`. The current `STAGE.json` is
authoritative for the exact required set.

These are Codex-authored digital assessments unless host-replayed evidence or
an authenticated physical receipt explicitly proves more. They do not prove a
successful print, physical fit, durability, hands-on use, or human response.
The normative public levels and optional manifest contract are defined in
[Product verification](PRODUCT_VERIFICATION.md).

## Native Playtest Goal, deterministic envelope

The root session creates one native Codex Goal for this Playtest attempt. Its
objective is independent evaluation of the exact sealed Made revision, and its
stopping condition is a successful Playtest finalizer with reproducible
evidence and a truthful verdict. A well-supported `improve` or `block` verdict
satisfies the Playtest Goal; Codex must not reason a failure into a pass.

The native session may use first-time, optimizing, exploratory, and adversarial
player perspectives; independent native subagents; native search; CAD/render
inspection; domain skills; and seeded simulations. While pursuing the Goal,
Codex observes the baseline, acts by running inspections, evaluates exact
evidence, and improves missing or weak test coverage. This loop is Codex
behavior, not a Python program. It records substantive evidence as files, not
chat claims.

The authored Playtest source contains exactly:

```text
checks, feedback, verdict
```

Every required check id appears once. Each check records a real evaluator and
exact version, cites a config file and evidence file inside the Playtest
evidence tree, records an explicit UTC observation time, and includes non-empty
observations. `self-report` and `trust-me` are not evaluators.

Temporary replay work belongs under `work/playtest/rNNNN/`, outside both the
sealed Made tree and the sealed evidence tree. Treat Made as strictly read-only
and default to copying only the exact inputs needed into the work area before
executing or importing them. Read a sealed file in place only with a tool known
not to write beside its input. Python and CAD commands must use
`PYTHONDONTWRITEBYTECODE=1` and redirect `XDG_CACHE_HOME`, `TMPDIR`, `TMP`, and
`TEMP` into the work area so `__pycache__`, `__cadgen__`, locks, progress files,
and scene caches cannot alter Made. A canonical config records the sealed Made
path and hash, copied-input hash, exact command, seed, and tool version. The
evidence tree contains only canonical configs and final static outputs cited by
checks—not copied source trees, caches, transcripts, or JSONL streams. The
authored three-field proposal stays under `drafts/`.

The session then runs:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

The finalizer hashes the entire evidence tree, validates exact check coverage,
and writes the canonical Playtested contract and bound `agent-outcome.json`.
It cannot pass the gate or run the improvement loop. After it succeeds, Codex
completes the Playtest Goal and returns to the host. The host rereads the tree,
validates the contract, and reruns the trusted CAD verifier on an isolated copy
of the Made product.

## Verdicts and feedback

- `pass` requires every check to pass and no actionable feedback.
- `improve` or `block` requires at least one failed check or actionable finding
  plus evidence-linked feedback.
- Every feedback item identifies its area, severity, observed finding, concrete
  next change, evidence references, and invalidated stages.

A failed Playtest chooses its repair boundary explicitly through those
structured invalidations. `["playtest", "release"]` returns an implementation
defect to Make. `["invent", "make", "playtest", "release"]` returns a
fundamental concept defect to Invent. If actionable findings use both scopes,
the broader Invent revision wins. The host follows these authored markers
mechanically; it never classifies the prose or decides how the product should
change.

Both routes consume the same bounded round. For re-Invent, the host preserves
and exposes the exact prior Invented contract, failing Playtested contract, and
canonical feedback bytes with independent hashes. Codex therefore revises a
traceable design lineage rather than restarting from the Wish. Previously
sealed Made and Playtest files remain immutable evidence.

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
checks. Release may turn those supported facts into a self-contained printable
`MANUAL.pdf` and secondary website metadata, but it cannot turn simulation into
customer response or CAD verification into manufacture. A well-formed or
beautiful PDF is not physical evidence.

After Release succeeds, the host may derive
`artifacts/release/VERIFICATION.json` as a best-effort public projection. The
current schema can emit only **Digitally Verified**. It publishes bounded check
identities and hashes while keeping raw evidence private. Failure to create
this optional projection does not weaken or block the underlying Release; it
means no public verification badge was recorded. A future **Physically
Verified** level requires a trusted host receipt proving that the exact
released bytes were built and checked. Model-authored evidence cannot raise it.

After Workshop publishes the verified Release, Operations owns printing,
hands-on QA, packing, delivery, and the customer-review loop. A public page is
the handoff, not evidence that those physical steps happened.
