## REMOVED Requirements

### Requirement: The artist draws one image per request through OpenRouter
**Reason**: This named one vendor and one model identifier as the contract, and took its drawing instruction from a request object Python composed. Neither the vendor nor the request object exists: the instruction is authored by the native session in the brief, and no provider is assumed.
**Migration**: `workshop/concept-image-integration` draws each image from the drawing instruction the concept already carries for that role, unchanged, and refuses to improvise one for a role that has none. Which provider serves it is configuration, never contract.

### Requirement: Reference images travel inline, never as external URLs
**Reason**: The rule was right; only its owner is gone. There is no artist reading reference paths off a Python request.
**Migration**: Kept verbatim in substance by `workshop/concept-image-integration`: reference bytes are read from the concept tree and carried inline, no path, local-file URL, or public upload location may be sent in their place, and a reference that cannot be read fails the request rather than sending a partial set.

### Requirement: Determinism knobs are never sent
**Reason**: Seed, temperature, and image count are one vendor's request parameters. A capability that assumes no provider cannot require, or forbid, particular fields in a request shape it does not define.
**Migration**: What this protected — that a request carries the concept's instruction and nothing else — is carried by `workshop/concept-image-integration`'s rule that the adapter composes, extends, rewrites, and substitutes nothing, and that no request may carry an envelope, feature, component, or style decision the concept did not state. One image per role survives as the descriptor naming exactly one path per role.

### Requirement: A produced image is written to the request's workspace and returned by relative path
**Reason**: The workspace and the returned relative path were fields of a Python request and return value. Paths now come from the stage packet and the concept's own descriptor, and nothing is returned to a caller — the bytes are written into the concept tree and sealed.
**Migration**: `workshop/concept-image-integration` writes returned bytes unmodified at the path the concept's descriptor names for that role, writes no file for a call that returned no image, and never reports a path to a file the provider did not produce.

### Requirement: Authentication and origin are fixed at construction, not per call
**Reason**: Pinning is stated here against a named vendor's origin and a credential the Python job held while doing cognitive work. Credentials no longer sit alongside the thing that thinks.
**Migration**: Both halves survive and are strengthened. `workshop/concept-image-integration` requires the configured origin to be pinned and refuses a response redirecting to another host, and adds the boundary this predates: the credential is host-only, loaded lazily outside any native turn, and a credential that would reach an agent-readable location fails the run.

### Requirement: Failures are surfaced with the failing role identified, never silently retried into a false success
**Reason**: These were the failure rules of one vendor's HTTP client, phrased in its status codes.
**Migration**: `workshop/concept-image-integration` keeps every one of them provider-agnostically: a non-retryable failure fails immediately naming the role, a retryable one is retried to a bounded limit and then fails naming the role, a malformed response is never read as an image, and no image file is produced for a role from any source other than the provider's own response.

### Requirement: Oversized responses and reference sets are rejected, not silently truncated
**Reason**: The size limit and the reference-count limit were expressed against one provider's documented ceilings.
**Migration**: Kept as configured limits rather than vendor constants: `workshop/concept-image-integration` refuses a response body exceeding its configured maximum rather than accepting a truncated one, and fails a request whose reference count exceeds what the configured provider accepts rather than sending a truncated reference set.
