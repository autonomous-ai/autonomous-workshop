# Playtest contract

Quest Playtest independently evaluates the exact sealed Made revision. Create
one Goal with a successful `playtest` finalizer as its stopping condition. A
truthful `pass`, `improve`, or `block` completes the Goal; never reason a failed
check into a pass or edit sealed Made bytes.

Read `STAGE.json` first. It binds the sealed Made product and manifest, the
`required_check_ids`, the exact `evidence_root`, any `vault_leads`, any
`score_dimensions`, the current round, and any host rejection. On the final
lifecycle round the packet sets `final_round: true` and
`backward_transition_allowed: false`: an `improve` or `block` verdict cannot
be finalized because no Make or Invent round remains. Pass only when the
evidence truthfully supports it; otherwise use `need --status failed` with the
concrete failing finding.

## Configs and checks

For every required check id, write
`<evidence_root>/configs/<check-id>.json` with `schema_version: 1`, the exact
`check_id`, and the current product manifest hash under
`product_artifact_sha256` (the legacy `artifact_sha256` key is still accepted
for older runs; when both are present they must agree). Preserve any finite
replay parameters; `seed` must be an integer when present. Each check cites
its canonical config and one stable evidence file inside `evidence_root`; the
finalizer derives and seals their hashes, so do not author hash fields on a
check. Digital evidence cannot prove printing, tactile fit, durability,
comfort, discoverability, or human response.

Use bounded independent reviewers and deterministic tools. Keep transient work
under `work/playtest/rNNNN/`; keep only canonical configs and cited outputs in
the exact evidence root. Write one source with exactly `checks`, `feedback`,
and `verdict`. A host rejection (`host_playtest_proposal_rejection`) must be
repaired with changed, stable regular files; never weaken the check.

`checks` contains each required id exactly once. Every check has exactly:
`check_id`; `passed` (boolean); `evaluator` (bounded text, never
`self-report` or `trust-me`); `evaluator_version` (an exact version, not
`latest`, `main`, `head`, or `snapshot`); `config_ref`
(`configs/<check_id>.json`); `evidence_ref` (evidence-root-relative regular
file); `observed_at` (ISO-8601 with explicit UTC offset); and non-empty
`observations`, using `evidence_class` and `claims` when the result supports a
later Release claim.

`feedback` items have exactly `code`, `area`, `severity` (`note`, `improve`,
or `block`), `finding`, `change`, `evidence_refs`, and `invalidates`.
`verdict` is `pass`, `improve`, or `block`; a `pass` requires every check to
pass and no `improve`/`block` feedback, and any other verdict requires at
least one feedback item plus a failed check or actionable feedback.

## Vault leads and score reads

When `STAGE.json` carries `vault_leads`, the `agent-playtest` check's
`observations` must answer every lead exactly once under `vault_leads`, each
entry exactly `{lead, verdict, why, feedback_code}`: `verdict` is `confirmed`
(then `feedback_code` names the feedback item carrying the repair) or
`dismissed` (then `feedback_code` is `null`), and `why` is one bounded
sentence. Unanswered, duplicated, or never-issued lead ids fail the finalizer.

When `STAGE.json` carries `score_dimensions`, the same observations must carry
`reads`: at least `score_minimum_reads` independent native readers, each
blind to the others, each exactly `{reader, scores, one_change}` scoring the
sealed revision 0 to 10 on exactly those dimensions. The host keeps the median
and spread per dimension and refuses `pass` when any median sits below
`score_floor`. Never invent physical trials, players, or measurements.

## Boundaries

Every failure names a concrete area and one invalidation boundary:

- implementation repair: `["playtest","release"]`, returning to Make;
- concept revision: `["invent","make","playtest","release"]`, returning
  directly to Invent (requires `improve` or `block` severity).

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . playtest \
  --source <playtest-source.json> \
  --evidence-root <STAGE evidence_root>
```

Return after finalization regardless of verdict. Only a host-verified pass
bound to current Made bytes advances to Release.
