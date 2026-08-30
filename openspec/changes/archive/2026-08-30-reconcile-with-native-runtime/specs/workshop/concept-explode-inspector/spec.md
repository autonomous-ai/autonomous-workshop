## REMOVED Requirements

### Requirement: The inspector is fully configured by its caller, with no vendor built in
**Reason**: This configured a second model credential and endpoint whose only purpose was to buy an opinion about an image. The Workshop no longer pays a model to judge its own pixels, so there is no inspector to configure.
**Migration**: The no-vendor-built-in discipline carries onto the one host model call that remains: `workshop/concept-image-integration` requires provider configuration to be supplied explicitly, rejects construction without it, hardcodes no vendor, model, or endpoint, and pins every call to the configured origin.

### Requirement: The inspector asks which offered components are visible in the exploded image
**Reason**: The question it asked — is every component the brief names actually there — was put to a vision model because there was no other way to ask it of a picture. Asking a model to grade the Workshop's own image is semantic judging in the host, which the runtime forbids, and the sandboxed native session cannot reach such an endpoint in any case.
**Migration**: The guarantee moves to where the host can settle it in bytes rather than in an opinion: `workshop/make-concept-adherence` requires the built part set to correspond one-to-one with the brief's declared components, which is a comparison of two recorded sets rather than a reading of pixels. Whether the drawn view actually separates what it should is the native session's own render inspection, inside the turn. The inline-image rule this requirement also carried survives in `workshop/concept-image-integration`, where reference bytes travel inline and never as a path or URL.

### Requirement: The response is parsed strictly into the reported component keys
**Reason**: Strict parsing existed to stop a model's answer from smuggling in a component nobody offered, or from reading an unparseable reply as "nothing visible". With no model answer, there is nothing to parse strictly.
**Migration**: The failure mode is designed out rather than defended against. Component correspondence compares the brief's declared components against the built part set, so a name that was in neither set cannot enter through a parse, and an ambiguous result cannot be misread as an empty one — the check either matches or names the mismatch, under `workshop/make-concept-adherence`.

### Requirement: Requests follow the OpenAI-compatible chat completions contract
**Reason**: This fixed one vendor's request shape, path, and bearer-header convention as the contract. No such request is made, and naming a vendor's wire format as a requirement is precisely what this change stops doing.
**Migration**: The credential handling it specified survives, and is stricter for it: `workshop/concept-image-integration` keeps its credential in host-only storage, loads it lazily at the point of use outside any native turn, and requires that it never appear in the run workspace, the stage packet, the prompt, the agent's process environment, the artifacts, or any status output.

### Requirement: Failures are surfaced, never silently swallowed into a false pass or fail
**Reason**: These were the failure rules of an HTTP call the Workshop no longer makes.
**Migration**: They survive essentially unchanged on the one host call that remains. `workshop/concept-image-integration` fails a non-retryable failure immediately, bounds retries on a retryable one before failing, refuses a response body over its configured maximum rather than accepting a truncated one, and forbids any failure becoming a fabricated success.
