# Frozen Forge and Quest economics profile v15

This immutable profile keeps v14's 256,000-token compaction, action-first
Invent recovery, exact-state proof, proof-sealing handoff, final-source
handoff, one native Codex thread, and one Goal per active stage. It restores
the one recovery route v14 removed, on the new evidence the print gates
produce.

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

Final-product recovery reads no unrelated optional references, with one
evidence-triggered exception. `verify_project --print-gates` measures each
printable entry's tessellated B-rep and writes `measure/thickness-<role>.md`
and `measure/overhang-<role>.md`. When a print gate fails, read the failing
report's complete region table and only the CAD reference
`references/print-optimisation.md` before one source repair. Repair all named
regions together; use constant-wall construction for a shell instead of blind
scalar changes or repeated full-gate probes. The gates write no mesh, so
there is nothing to export first and nothing to go stale.

The host requires fresh proof STEP/render/finding bytes, strict fit,
exact-state renders, the final hash-bound blind review, integrated
verification, Playtest for Quest, manual quality, authenticated Factory
publication, and GitHub snapshot integrity. Release additionally requires
full-tier, print-gated CAD evidence at the nozzle the print will use: seal
product status `full-with-thickness` with `print_ready_claim: true`, or seal
`digitally-verified-not-print-ready` with `false` and do not call the product
print-ready. Later stages use medium reasoning, every deep stage compacts at
256,000 tokens, and one invocation launches at most eight turns.
