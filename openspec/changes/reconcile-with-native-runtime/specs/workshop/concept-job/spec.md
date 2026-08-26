## REMOVED Requirements

### Requirement: Concept is a Workshop job between Wish and Make
**Reason**: The job set this enumerates — `wish`, `concept`, `make`, `playtest`, `instructions`, and `deliver` — is not the run's stage list, and the things it asks to accept `concept` (a blueprint's declared tasks, a job-scoped need, a job-scoped feedback target) are not how a run is sequenced now. Concept's position is right; everything it is positioned within has been replaced.
**Migration**: `workshop/concept-stage` restates the position against the real lifecycle: `concept` sits after `invent` and before `make` in the eight-stage run, appears in the forward transitions, the upstream mapping, the set a new Make revision invalidates, and the stages a run may wait at, and can be left only through its own deterministic gate.

### Requirement: Concept receives the round's context and returns a sealed concept
**Reason**: This specified Concept as a Python callable taking a context object and returning a value, with the context's own construction rules as the validation surface. There is no callable and no context object; the stage's inputs are bytes the host writes and the stage's output is bytes the host re-reads.
**Migration**: `workshop/concept-stage` replaces the context with the stage packet — a read-only binding of the checkpoint, the upstream subject, the canonical output paths, and the round and round allowance — which the turn may read and may not edit. The workspace-containment rule survives as the requirement that every file the turn produces resolve inside the concept tree the packet named; the malformed-context refusal becomes the refusal of a proposal bound to a stale checkpoint or subject.

### Requirement: Concept does its work in one order: research, then brief, then images
**Reason**: The ordering was enforceable only because Python called each capability in turn and could observe that the artist had not yet been called. The host no longer sees inside the turn, and ordering the native session's own internal work is exactly the prompt-chaining the runtime forbids.
**Migration**: The ordering guarantee becomes a set of facts the gate can actually check. No fact may stand without a recorded source or a recorded decision, so nothing can be locked ahead of the research that decided it, and images are drawn by the host only after the brief has been accepted, so nothing is drawn against a brief that does not exist — see `workshop/concept-stage` and `workshop/concept-image-integration`. The refining round's reuse of standing research survives explicitly in `workshop/concept-stage`.

### Requirement: Concept waits truthfully when it cannot draw
**Reason**: The waiting was right; its mechanism and its inventory of capabilities were not. It raises a Python exception carrying a need per missing capability, and enumerates three capabilities of which only one is still separately configured.
**Migration**: `workshop/concept-stage` keeps the whole principle — no invented, placeholder, or approximated design, a run recorded as waiting at `concept` with a need naming what is missing and what would satisfy it, Make not called for that round, and the round and accepted work preserved across the wait. `workshop/concept-image-integration` carries the specific case of an absent image configuration, including that a partial image set is never sealed.

### Requirement: Later rounds refine the concept rather than restart it
**Reason**: Phrased around a feedback object arriving in a Python context and a concept returned from the previous call. Rounds now revise a standing sealed concept that the host carries forward, and a round may not run a Concept turn at all.
**Migration**: `workshop/concept-stage` restates it, and sharpens it: build-only feedback leaves the standing concept in force with no Concept turn for that round, design feedback revises the standing concept while preserving every feature the feedback did not challenge, and revision beyond the refine allowance re-anchors on the design's locked facts rather than refining a drifting design further.

### Requirement: A run records which concept its build came from
**Reason**: This recorded a concept hash and a derived Wish as fields a Python job returned alongside a round's evidence. Identity is now a sealed, content-addressed contract chained onto the stage that follows it, not a value handed back by a caller.
**Migration**: `workshop/concept-stage` carries the traceability: one `concept_sha256` over the whole concept tree, recorded on the run, named in Make's stage packet and in the sealed Make result, restored identically on resume, with a restored state naming a different concept refused. The derived-Wish half moves to `workshop/wish-research`, where the researched constraints are a host-validated record that names the routed Wish it was derived from, leaving the words a person actually wished untouched.
