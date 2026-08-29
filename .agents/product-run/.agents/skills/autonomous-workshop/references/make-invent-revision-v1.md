# Make-to-Invent revision capability

This immutable file enables an evidence-bound `Make -> Invent` repair edge for
new Forge and Quest runs. Its presence in the frozen product-run input manifest
is the capability marker; older runs without these exact bytes retain their
original lifecycle.

Use this edge only when the exact sealed Invent concept is internally
contradictory, omits a decision required for any conforming build, or otherwise
prevents Make from producing truthful product bytes. Do not use it for an
ordinary CAD mistake, a merely difficult build, a preference, or an issue Make
can repair while preserving the sealed concept.

Make must preserve deterministic or independently inspected evidence under the
canonical `revision_evidence_root` from `STAGE.json`, then author feedback whose
every item:

- has severity `block`;
- cites one or more exact files in that evidence tree;
- explains the contradiction and the concrete Invent change required; and
- uses `invalidates: ["invent", "make", "playtest", "release"]`.

Finalize with:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make-revision \
  --source <make-revision-source.json> \
  --evidence-root <STAGE revision_evidence_root>
```

Successful finalization completes the current Make Goal truthfully; it does
not pass Make. The host rehashes the evidence, verifies the exact upstream
bindings and shared round budget, records a failed Make gate, invalidates the
old concept and downstream work, and starts a new Invent Goal with the request.
Make never edits or replaces sealed Invent bytes itself.
