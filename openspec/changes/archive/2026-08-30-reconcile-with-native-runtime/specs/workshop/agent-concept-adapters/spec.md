## REMOVED Requirements

### Requirement: Each adapter is a faithful, drop-in implementation of Concept's existing port
**Reason**: Drop-in substitutability presupposes that Concept declares a port and that two differently-sourced implementations can be swapped behind it. Concept declares no ports: the native session researches the Wish and authors the brief inside the Concept turn, so there is no seam an adapter could be faithful to.
**Migration**: The invariant this actually protected — that a breakdown is validated on identical terms no matter who produced it — is now the host gate. `workshop/concept-stage` applies the same completeness and attribution rules to every concept, and forms no view on how the design was arrived at.

### Requirement: The wish-research adapter calls the door under its own capability name
**Reason**: The role name existed so a need could be turned back into a dispatch: name the capability, call the door under it. Nothing dispatches on a capability name any more.
**Migration**: Needs survive as typed reasons on a `waiting` outcome that name what is missing and what would satisfy it, but they park the run rather than route a call — see `workshop/concept-stage` and `workshop/concept-image-integration`.

### Requirement: The wish-research adapter sends the same task instructions and attribution rules the deleted HTTP researcher used to send
**Reason**: This existed because a freshly launched process could not be assumed to know the wish-research contract by role name alone, so the contract had to be composed into every request. The host now composes no prompt at all.
**Migration**: The instruction text becomes durable materialized instruction bytes rather than per-call request content: the workflow skill's Concept reference and each Inventor's required `<id>-inventor` skill, hashed at run creation and bound to the run, so a resume fails closed if they changed. The attribution rule itself is no longer carried by the asker but enforced by the reader — `workshop/concept-stage` refuses a fact naming neither a recorded source nor a recorded decision, and refuses a fact naming both.

### Requirement: The shared agent door's environment constructor configures the wish-research role only
**Reason**: This scoped the door's configuration surface to the single role anything still called it under. With no door and no roles, there is no configuration surface to scope.
**Migration**: The fail-closed half survives on the one capability that is still configured out of band: `workshop/concept-image-integration` rejects construction without provider configuration, and where the configuration is absent the run is recorded as waiting with a need naming the image capability rather than proceeding to Make.

### Requirement: Concept keeps taking exactly one implementation per capability
**Reason**: Named the three injected implementations — a researcher, an artist, and an inspector — that Concept was to be wired with. Two of the three no longer exist as separately-supplied things, and Concept takes none of them.
**Migration**: The no-blending guarantee survives more strongly than it was written. One native session does the cognitive work, and `workshop/concept-stage` forbids the host composing, scoring, ranking, or selecting any part of a concept — so there is nothing left inside the stage that could choose between two candidates for the same design.
