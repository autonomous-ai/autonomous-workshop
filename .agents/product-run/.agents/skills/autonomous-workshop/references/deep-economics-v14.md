# Frozen Forge and Quest economics profile v14

This immutable profile keeps v13's 256,000-token compaction, action-first
Invent recovery, exact-state proof, proof-sealing handoff, final-source
handoff, one native Codex thread, and one Goal per active stage. It removes
two recovery costs observed in production Forge
`wish-20260831-182830-9cbbe7b0` without weakening a gate.

Invent and initial proof behavior are unchanged. Invent begins with 20 minutes
at high reasoning and its 10-minute medium recovery finalizes existing source
first. Initial Make proof retains one 16-minute medium runway and v12 recovery
still seals current fresh exact-state evidence before any new design work.

After the proof marker, the first final-product continuation retains the
15-minute high-reasoning source handoff followed by normal 30-minute recovery.
If an operator later runs `workshop resume` while that same Make Goal is still
checkpointed and its proof marker remains valid, the host starts directly in
normal recovery. It does not replay another 15-minute source phase. The exact
session, stage subject, product bytes, and deterministic gates are unchanged.

Final-product recovery reads no unrelated optional references, and v14 removes
the one evidence-triggered exception v13 carried: there is no print preflight,
no wall-thickness report and no `references/print-optimisation.md` to route a
repair into. The CAD toolchain writes STEP alone.

The host continues to require fresh proof STEP/render/finding bytes, strict
fit, exact-state renders, the final hash-bound blind review, integrated
verification, Playtest for Quest, manual quality, authenticated Factory
publication, and GitHub snapshot integrity. It no longer requires — and can no
longer obtain — any mesh, overhang or wall-thickness evidence, so no stage may
call a product print-ready. Later stages use medium reasoning, every deep stage compacts at
256,000 tokens, and one invocation launches at most eight turns.
