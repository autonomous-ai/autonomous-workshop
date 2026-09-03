# Frozen Forge and Quest economics profile v11

This immutable profile keeps v10's 256,000-token compaction ceiling, exact-state
Make proof, 15-minute final-source handoff, one native Codex thread, and one
Goal per active stage. It corrects the Invent finalization delay observed in
production Quest `wish-20260831-153128-dde436ba`.

Complete-roster routing remains index-first. `STAGE.json` contains the compact
`inventor_discovery_index`; Invent ranks it, opens only the best three full
custom-agent TOMLs, selects one, and loads that Inventor's method. The initial
Invent turn remains high reasoning for 20 minutes.

Invent recovery is a source handoff, not another creative pass. Its first
action checks only whether the routed `invent-source.json` already exists. If
it exists, Codex invokes the exact Invent finalizer immediately, before reading,
editing, planning, researching, waiting on children, or reviewing the source;
deterministic errors may then drive the smallest repair. If it does not exist,
Codex performs no new research, comparison, delegation, or refinement: its
first edit writes the smallest contract-complete source from the strongest
decision already in context, and its next action invokes the finalizer. The
10-minute medium boundary is repair reserve, not a synthesis allowance.

Make evidence distinguishes product state from camera angle. The 16-minute
medium proof turn creates shared `review/early-proof/proof.py` plus
`state-0.step.py`, `state-1.step.py`, and `state-2.step.py`. It generates and
exports all three exact states, then uses `render_product --state-sheet` with
the three state STLs at one fixed view. The deterministic renderer rejects
visually indistinguishable frames. A `--motion-sheet` rotates one unchanged
mesh and is never evidence of a mechanism state transition.

The proof turn batches mandatory reads once, writes the helper and three state
entries in the next edit, runs the deterministic CAD commands in one foreground
call, inspects every exact state, and permits at most one focused repair. The
host accepts `.make-proof-ready.json` only when the exact checkpoint marker and
all helper, state-source, STEP, distinct-STL, held-image, state-sheet, and
finding bytes are stable regular files. The marker is a turn boundary, never a
stage proposal or quality waiver.

After proof, the first high-reasoning final-Make continuation has a 15-minute
source-handoff boundary. It writes complete final product source from the proof
before optional references or API search. Normal 30-minute recovery continues
the exact Goal and repairs only concrete verification failures. Final blind
review, strict CAD checks, Quest Playtest, manual quality, authenticated Factory
publication, and GitHub snapshot integrity remain mandatory. Playtest and
Release use medium reasoning, every deep stage compacts at 256,000 tokens, and
one Wish/resume invocation may launch at most eight turns.
