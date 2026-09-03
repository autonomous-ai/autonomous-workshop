# Playtest contract

Quest Playtest independently evaluates the exact sealed Made revision. Create
one Goal with a successful `playtest` finalizer as its stopping condition. A
truthful `pass`, `improve`, or `block` completes the Goal; never reason a failed
check into a pass or edit sealed Made bytes.

For every required check id, write
`<evidence_root>/configs/<check-id>.json` with `schema_version: 1`, the exact
`check_id`, and the current product manifest hash under
`product_artifact_sha256`. Preserve any finite replay parameters; `seed` must
be an integer when present. Each check cites its canonical config and one
stable evidence file. Digital evidence cannot prove printing, tactile fit,
durability, comfort, discoverability, or human response.

Use bounded independent reviewers and deterministic tools. Keep transient work
under `work/playtest/rNNNN/`; keep only canonical configs and cited outputs in
the exact evidence root. Write one source with exactly `checks`, `feedback`,
and `verdict`. A host rejection must be repaired with changed, stable regular
files.

Every failure names a concrete area and one invalidation boundary:

- implementation repair: `["playtest","release"]`, returning to Make;
- concept revision: `["invent","make","playtest","release"]`, returning
  directly to Invent.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

Return after finalization regardless of verdict. Only a host-verified pass
bound to current Made bytes advances to Release.
