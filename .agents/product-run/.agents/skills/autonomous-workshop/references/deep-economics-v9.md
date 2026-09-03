# Frozen Forge and Quest economics profile v9

This immutable marker freezes the v8 single-runway proof profile for new Forge
and Quest runs, with a 256,000-token automatic context-compaction ceiling. One
persistent Codex thread and one active stage Goal remain bound to the complete
profile. A turn boundary never advances a lifecycle stage or weakens a gate.

Invent begins at high reasoning with a 20-minute boundary. If that turn times
out, bounded recovery uses medium reasoning for 10 minutes and must seal the
strongest viable source already developed instead of restarting selection,
research, exploration, or subagents.

Make begins with one 16-minute medium-reasoning proof runway. Create or
continue the Make Goal immediately without a separate `get_goal` call. Batch
every mandatory bounded read into one tool call: root instructions, Workshop
skill, current Make reference, current `STAGE.json`, and only the sealed
concept fields needed to model. Do not inspect an empty product tree or create
an empty directory as separate work.

The broad CAD skill and optional references are deliberately deferred until
the proof marker exists. Author the proof source and parent directories in the
next file edit. The source defines exactly one module-scope `gen_step()` and
returns its build123d shape. The host binds `XDG_CACHE_HOME` to a private
writable directory inside the run.

Generate, export, and render use the exact `$WORKSHOP_PYTHON` and execute in
order in one foreground tool call:

```bash
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/gen <entry.step.py> --write
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/export <entry.step> --stl
"$WORKSHOP_PYTHON" .agents/skills/cad/scripts/render_product <entry.stl> \
  -o <cad-project>/review/early-proof/held.png \
  --motion-sheet <cad-project>/review/early-proof/signature.png \
  --motion-angles=-12,0,12
```

The root Manager directly inspects these early images against the Wish. This is
a cheap direction falsifier, not the canonical blind-review gate. Do not spawn
an early critic. A generic, flat, plaque-like, box-like, container-like,
board-like, exposed-mechanism, or ambiguous proof gets at most one focused
source repair and one repeat batch. Persist a compact root finding beside the
images.

When source, STEP, STL, held/signature images, and the root finding are durable,
write the exact checkpoint-bound `.make-proof-ready.json` described by the host
prompt. The launcher treats it only as voluntary native-turn completion. It
resumes the same Make Goal at high reasoning with a normal 30-minute turn. It
is not a stage proposal, aesthetic gate, lifecycle transition, or evidence
waiver. Only `agent-outcome.json` from the real Make finalizer can propose a
stage transition.

After the marker, load the broad CAD skill and only the exact final-product
references needed. High-reasoning Make reuses the proof parameters and source,
persists the smallest complete product baseline, runs all-printable preflight,
creates final renders, performs the required independent hash-bound blind
review, makes one focused repair at most, runs one integrated final verifier,
and invokes the Make finalizer. The final independent critic remains mandatory.

Every stage compacts at 256,000 tokens. Playtest and Release use medium
reasoning and normal 30-minute turns. One `workshop wish` or `workshop resume`
invocation may launch at most eight native turns across all stages.

After proof, iterative preflight is `"$WORKSHOP_PYTHON"
.agents/skills/cad/scripts/verify_project <cad-project> --print-preflight`
without `--fresh`. The trusted host owns the authoritative isolated fresh
rebuild.

This profile does not waive Wish fidelity, Inventor Taste, full-tier CAD
checks, Quest Playtest, manual quality, authenticated Factory publication, or
GitHub snapshot integrity. Lower spend counts only when the exact product is
distinctive, desirable, truthful, gate-complete, publicly verified, and
archived.
