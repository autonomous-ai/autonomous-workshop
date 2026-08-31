# Frozen Forge and Quest economics profile v12

This immutable profile keeps v11's 256,000-token compaction, action-first
Invent recovery, exact-state proof, final-source handoff, one native Codex
thread, and one Goal per active stage. It corrects proof-sealing waste observed
in production Quest `wish-20260831-163206-abbea127`.

Invent behavior is unchanged. The initial high-reasoning turn has 20 minutes;
the 10-minute medium recovery checks for existing source and finalizes it first,
or writes the smallest complete source then finalizes before refinement.

Initial Make proof retains one 16-minute medium runway to write shared proof
source and three state entries, generate three distinct STEP/STL states, render
one held image and one fixed-camera state sheet, inspect them, and make at most
one focused repair. Viewpoint rotation is never state evidence.

Proof recovery is now a sealing handoff, not another design turn. Its first
bounded action checks only the required proof files. If current source,
generated states, held render, state sheet, and finding already exist, Codex
does not edit source, generate variants, create measurement meshes, research,
plan, delegate, or refine; it writes the exact checkpoint marker immediately.
If only the finding or marker is missing, those are the next one or two writes.
If generated evidence is missing or stale, it regenerates the current source
without changing geometry, writes the finding, and then writes the marker.
Only a deterministic generation or renderer error permits one focused repair.

The host resolves exactly one real proof directory at either the historical
direct product path or `product/cad/<project>/review/early-proof`, rejecting
symlinks and ambiguity. For v12 it also requires every STEP/STL to be at least
as new as the proof sources, held/state renders to be at least as new as their
STLs, and the finding to be at least as new as the renders before accepting the
marker. This freshness check is deterministic evidence binding, not a quality
judge.

After the marker, final Make keeps its 15-minute high-reasoning source handoff
and normal 30-minute recovery. Final blind review, strict CAD checks, Quest
Playtest, manual quality, authenticated Factory publication, and GitHub
snapshot integrity remain mandatory. Later stages use medium reasoning, every
deep stage compacts at 256,000 tokens, and one invocation launches at most
eight turns.
