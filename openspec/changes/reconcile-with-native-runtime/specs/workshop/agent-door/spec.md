## REMOVED Requirements

### Requirement: The door runs one named role per call in a fresh, isolated workspace
**Reason**: The door's unit of work was a per-call agent process that Python launched and bound to a directory it had just created. The runtime starts and resumes exactly one root native session for a whole run and does not schedule agents in Python, so there is no per-call process left to hand a workspace to.
**Migration**: The isolation this protected survives in stronger form and at a different scale: every native turn runs under a host-enforced, workspace-only permission profile that denies reads elsewhere and disables the sandbox network, and each turn is bound to a stage packet naming the only tree it may write — `workshop/concept-stage` refuses output written outside that tree. Per-call workspace freshness is deliberately gone, because one-session continuity across stages is now the thing being preserved.

### Requirement: Only role-appropriate access is granted, and an unconfigured role fails closed
**Reason**: Roles were Python-side seats, each carrying its own tool and file grant, configured before a process was launched. There are no seats: cognitive work is the one native session's, and its specialist children are the agent runtime's own subagents, which the host does not configure per call.
**Migration**: Bounded access is now the host's permission profile plus the declared Inventor bundle — only hash-bound extension trees are materialized into the toy project, none auto-run, and inventor code may not read credentials, perform external effects, or advance a gate. The fail-closed-on-missing-configuration guarantee moves onto the one remaining configured capability: `workshop/concept-image-integration` rejects construction without provider configuration, and an absent credential parks the run with a need rather than proceeding.

### Requirement: The result must be the agent's own structured output, never a guess
**Reason**: This governed a per-role JSON result read back from a process the host had just launched. There is no such call and no such result.
**Migration**: The guarantee is kept as the stage protocol: the native turn runs its own finalizer and returns one compact outcome, the host independently re-validates the exact bytes it finds, and an outcome it cannot parse into the stage's declared shape is refused rather than completed. `workshop/concept-stage` forbids the host authoring any part of what the turn failed to author.

### Requirement: Every call is bounded by wall-clock time and by its budget, and the bound is enforced, not advisory
**Reason**: Enforcement depended on Python owning the process it could terminate mid-call. The host no longer owns per-call agent processes, so it has nothing to kill on a per-role clock.
**Migration**: The run is still bounded, at run scale rather than call scale: the host owns the Make–Playtest round allowance and a hard ceiling on native turns, and a run that exhausts the turn ceiling fails rather than continuing. `workshop/concept-stage` carries the round and round allowance into the stage packet. Per-role wall-clock termination is gone with the roles.

### Requirement: Actual cost and duration are always reported, even on failure
**Reason**: Per-call cost accounting was possible only because each role was a separately metered call the host paid for and measured. Cognitive work is now one session under the operator's own subscription, and the host neither meters nor prices native turns.
**Migration**: This guarantee is genuinely lost, and not replaced. What survives is the auditability the budget served: a run records its stage, its round, and the turns it consumed, and the round allowance and turn ceiling are enforced rather than reported. Spend per agent role is no longer knowable from a run record.

### Requirement: A crashed or misbehaving process fails the call, never a fabricated success
**Reason**: The failure surfaces it names — a non-zero exit status, a timeout, a malformed role result — belong to a launched process the host no longer launches.
**Migration**: The never-fabricate rule is kept at every boundary that replaced it. A native turn that cannot complete yields a `waiting` or `failed` outcome carrying typed needs, and neither can advance a gate; `workshop/concept-stage` forbids substituting a placeholder design for one that was never decided; `workshop/concept-image-integration` requires that no failed request produce an image file from any source other than the provider's own response.

### Requirement: Construction requires an explicit, caller-supplied agent process, never a hardcoded one
**Reason**: There is no door to construct, and the engine is chosen once by the host's session start-and-resume boundary rather than supplied per call.
**Migration**: The assume-no-vendor rule carries onto the host effect that still calls out: `workshop/concept-image-integration` rejects construction without explicit provider configuration and hardcodes no provider, model, or endpoint. Engine choice for the native session is a portability property of the start/resume adapter, stated in the runtime documentation rather than as a per-call configuration contract.

### Requirement: The process launcher is an injectable seam
**Reason**: An injected seam whose substitute performs cognitive work is exactly the second Python agent framework the repository forbids by name. A seam like this exists only if Python schedules the agent, and it no longer does.
**Migration**: Deterministic testing without a network survives as seams over the host's own boundaries, not over cognitive work: a substitute session adapter and substitute host effects drive a whole run end to end, and the image adapter is asserted against — as the publishing adapter already is — for never letting a credential reach a launcher argument.
