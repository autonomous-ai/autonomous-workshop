## REMOVED Requirements

### Requirement: The entry point wires images and exploded-view-check to the HTTP adapters and wish-research to the agent door
**Reason**: This named three implementations and assembled them into a callable Concept job. None of the three survives: research is the native session's own work, the exploded-view inspector is deleted, and there is no job object for an entry point to return.
**Migration**: Each concern now reaches Concept by its own route rather than through one assembly point. Research and design are authored in the Concept turn under `workshop/concept-stage`; images are drawn by the host between native turns under `workshop/concept-image-integration`; component correspondence is settled deterministically at the Make boundary under `workshop/make-concept-adherence`. Nothing wires them together, because they are no longer three interchangeable parts of one Python object.

### Requirement: Construction fails closed, naming whichever capability's configuration is missing
**Reason**: Failing closed at construction was only possible because all three capabilities had to be resolved before Concept could be built. Two of them are no longer configured at all, so there is no moment at which all three could be checked together.
**Migration**: Both halves of this guarantee survive, moved from construction time to run time. A missing image credential does not silently proceed: the run is recorded as waiting at `concept` with a need naming the image capability, its accepted brief and research preserved, and Make is not called — see `workshop/concept-image-integration`. And a refusal still names its cause: `workshop/concept-stage` requires every gate refusal to name the rule that refused it.
