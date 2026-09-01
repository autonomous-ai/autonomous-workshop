## ADDED Requirements

### Requirement: Concept provider execution remains unavailable while dormant

No Concept image adapter SHALL be executable in this change. Importing, parsing, or evaluating Concept contracts MUST NOT load provider configuration, read a credential, open a network connection, transmit private bytes, write effect state, or invoke an external effect. A future adapter may run only through a durable authorized host-effect boundary implemented before the compound creative-stage Concept boundary is activated.

#### Scenario: Dormant evaluation runs with provider credentials configured
- **WHEN** the contract parser or structural evaluator is invoked
- **THEN** it does not inspect or use those credentials
- **AND** it performs no provider request

#### Scenario: Rendering is requested before the effect boundary exists
- **WHEN** a caller attempts to execute Concept rendering through Workshop
- **THEN** the capability is unavailable and no transmission occurs

## REMOVED Requirements

### Requirement: The adapter transports instructions it did not write
**Reason**: No provider adapter is restored in the dormant contract slice.
**Migration**: Preserve authored instructions in pre-render contracts; implement transmission only in the later durable image-effect change.

### Requirement: The adapter runs outside the native turn and its credential never reaches the agent
**Reason**: The adapter itself remains unavailable; non-execution is stronger than credential-isolated execution in this slice.
**Migration**: The future executor must run host-side and keep credentials outside the native process.

### Requirement: No vendor, model, or endpoint is assumed
**Reason**: Provider selection and configuration are outside this contract-only change.
**Migration**: The later durable image-effect change must define explicit provider capability and origin pinning before transmission.

### Requirement: Images are drawn in an order that accumulates references
**Reason**: Dormant validation checks declared ordering but does not execute image requests.
**Migration**: A later effect executor must consume the validated ordering without rewriting it.

### Requirement: Only bytes the provider actually returned are written
**Reason**: No provider call or output write is authorized by this change.
**Migration**: The durable effect boundary must bind authenticated receipts to exact returned bytes before sealing.

### Requirement: A partial set is never sealed
**Reason**: Provider execution is deferred; sealed-contract validation already rejects incomplete exact trees.
**Migration**: The future effect coordinator must keep incomplete or ambiguous role sets outside the sealed form.

### Requirement: Failures name the failing role, and transient failures are bounded before failing
**Reason**: Inline retry behavior from the feature branch is unsafe and is not restored.
**Migration**: The future effect ledger must reconcile idempotently and represent unknown outcomes instead of blindly retrying.

### Requirement: Absent configuration parks the run rather than failing it
**Reason**: There is no active Concept lifecycle state to park and credential presence is not transmission authorization.
**Migration**: A later durable effect implementation must define authorized waits and resume behavior against the owning Invent or Make checkpoint, without introducing a Concept lifecycle state.
