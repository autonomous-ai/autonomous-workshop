# Make contract

Read `STAGE.json`. It binds the exact sealed upstream artifacts, universal
blueprint, canonical output paths, current round, and any host rejection
feedback. Verify those bytes before acting. Host checkpoints bound the work;
Codex performs the reasoning and repair.

If `STAGE.json` contains `host_make_proposal_rejection` or
`host_cad_gate_rejection`, the previous Make finalizer did not pass the host
gate. Read the complete rejection and its bounded diagnostics, repair the
exact cited defect, rerun the relevant checks, and verify that the rejected
product or evidence bytes changed before invoking the finalizer again. A
completed Goal for the earlier subject is not completion for this new
rejection-bound attempt. Do not merely regenerate and resubmit the same Made
contract.

## Make Goal and improvement loop

Create one native Codex Goal for the current Make attempt. Its objective is to
produce the exact ready-to-print, inspectable product artifact required by the
sealed Invent output. Its stopping condition is a successful `make` finalizer
for the current checkpoint.

The sealed Invent result is the primary reference for form, proportion,
construction, component breakdown, and intended interaction. Read both its
selected `concept` and its `research`; preserve its explicit dimensions and
constraints, and do not reinterpret the Wish from scratch. Realize every
component and interface the selected concept names in the actual product tree.

While pursuing the Goal:

1. **Observe:** Inspect the sealed Invent concept and research, the selected
   Inventor instructions, universal blueprint, current revision workspace,
   deterministic tool policy, and every current host rejection.
2. **Act:** Use native editing and the materialized `cad`, `image-to-cad`,
   `design-reference`, `electromechanical-integration`, and `step-parts`
   skills under `.agents/skills/` to
   create or repair the actual product artifact. Use native subagents for bounded mechanism, CAD, or
   review tasks when useful.
3. **Evaluate:** Build the artifact, run narrow deterministic checkers, inspect
   actual STEP/STL and rendered outputs, and compare observed behavior with the
   concept, dimensions, materials, tolerances, assembly, and prior feedback.
   Use an independent native reviewer for subjective or adversarial inspection
   where it adds evidence.
4. **Improve:** Fix the largest concrete failure, rebuild, rerun the checks,
   and reinspect the artifact. Keep changes focused enough to know whether the
   evidence improved. Continue within the host-provided round.

Codex owns the build/check/inspect/repair loop. Python tools may generate CAD,
measure exact geometry, or validate a contract; they do not plan repairs,
score Taste, route agents, or control the loop.

Leave the product tree at the exact `product_root` in `STAGE.json`. It must
include the required root product metadata, CAD project, assembled STEP/STL
outputs, and deterministic CAD verification file. Map mechanisms, rules,
dimensions, materials, tolerances, and limitations to real artifact bytes
rather than prose assertions.

The root `product.json` must be a JSON object containing at least these exact
metadata keys (additional product-specific fields are allowed):

```json
{
  "title": "Moon Nook",
  "summary": "A tiny lunar observatory built for tabletop play."
}
```

Both `title` and `summary` must be strings with non-whitespace content and no
more than 2,000 characters. Do not substitute aliases such as `name` or
`description`; the Make finalizer and trusted host require the exact keys.

Then run:

```bash
"$WORKSHOP_PYTHON" .agents/skills/autonomous-workshop/scripts/stage_proposal.py \
  --run-root . make \
  --product-root <STAGE product_root> \
  --cad-project-path <path inside product root> \
  --cad-verification-path <path inside product root>
```

The deterministic finalizer hashes the complete tree and writes the canonical
Made contract. Complete the Make Goal only after it succeeds, then return to
the host. The host copies the exact tree into an isolated verifier, reruns the
trusted CAD gate, compares bytes, and seals the accepted revision. Narrative
or model confidence never overrides a failed or absent measurement.

The direct-Release protocol does not accept the lower digital-only tier. The
host requires the full verifier, including wall thickness and print-ready
eligibility, before Make can advance. Playtest is intentionally deferred and
must not be simulated or claimed during Make; Release records that it was not
run.
