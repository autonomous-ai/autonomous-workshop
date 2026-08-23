## Outcome

<!-- What inventor or Workshop capability does this PR add or improve? -->

## Change type

- [ ] New inventor
- [ ] Existing inventor
- [ ] Workshop Make or making skills
- [ ] Workshop Inspect or evidence
- [ ] Workshop Pack or Send
- [ ] Workshop Clockwork
- [ ] Workshop Door
- [ ] Documentation or repository tooling

## Inventor contract

<!-- Complete this section for inventor changes. -->

- Inventor ID:
- Display name:
- Niche/customer:
- One-sentence taste summary:
- Signature product moment:
- Explicit rejects:
- [ ] Root `TASTE.md` is canonical and workflow-bound.
- [ ] `inventor.json` claims only exercised capabilities.

## Workshop reuse

<!-- Explain which shared subsystems are composed and any inventor-local code. -->

- Make:
- Inspect:
- Pack:
- Send:
- Clockwork:
- Doors:

- [ ] Shared infrastructure was reused instead of copied into the inventor.
- [ ] The dependency remains one-way: inventor imports Workshop; Workshop
      does not import the inventor.
- [ ] New code and prose use `workshop`, `inventor_workshop`, schema-v3
      `workshop_features`, Wish, Taste, Make, Inspect, Pack, Send, qualified
      Doors, Stamps, and Clockwork.

## Current versus target behavior

<!-- State what works in this PR. List future contract work separately. -->

Implemented now:

-

Still target or held:

-

## Offline demonstration

<!-- Paste commands and summarize results. Never paste credentials or secrets. -->

```text

```

- [ ] The offline path needs no network, credentials, paid provider, CAD
      service, printer, or live Send effect.
- [ ] Fakes and fixtures are clearly distinguished from live readiness.
- [ ] Failure, ambiguity, repair exhaustion, and “no viable product” outcomes
      fail closed where applicable.

## Verification

- [ ] New/changed inventor tests
- [ ] `python -m unittest discover -s workshop/tests -p 'test_*.py' -v`
- [ ] `workshop skills list`
- [ ] `workshop schemas list`
- [ ] `workshop inventors --root inventors --check-entrypoints`
- [ ] `workshop check inventors/your-inventor --run`
- [ ] `python workshop/tools/verify_skill_locks.py`
- [ ] `python workshop/tools/verify_snapshot_locks.py`
- [ ] `python workshop/tools/scan_secrets.py`
- [ ] `git diff --check`

Additional commands and results:

```text

```

## Safety, provenance, and migration safety

- [ ] No credentials, runtime databases, transcripts, private keys, or source
      backups are included.
- [ ] Third-party source/skills record URL, exact commit, import date,
      exclusions, patches, and license status.
- [ ] Existing durable state, artifact identity, receipts, and snapshot locks
      remain readable or have a tested versioned migration.
- [ ] Every external effect is planned before execution, fenced, and
      Stamp-bound; Shop sends begin as private drafts.

## Reviewer notes

<!-- Point reviewers to the most important files, tradeoffs, and known limits. -->
