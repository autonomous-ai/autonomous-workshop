## Purpose

The host-side adapter that turns the drawing instructions a concept authored into the actual image set that concept ships. It is transport and verification only: it carries what the native session specified to an image provider, checks what comes back, and seals it — so the Workshop can visualize a design without the host ever deciding what the design looks like, and without a credential ever reaching the agent.

## Requirements

### Requirement: The adapter transports instructions it did not write

The adapter SHALL draw each image from the drawing instruction the concept's brief already carries for that role. It SHALL NOT compose, extend, rewrite, summarize, or substitute a drawing instruction, and SHALL NOT add design content of its own to a request.

Where a required role carries no drawing instruction, the adapter SHALL fail that concept rather than supply one.

#### Scenario: A request carries the authored instruction unchanged

- **WHEN** the adapter draws a role
- **THEN** the instruction it sends is the one the concept authored for that role, unchanged

#### Scenario: A missing instruction is not improvised

- **WHEN** a required role has no authored drawing instruction
- **THEN** the adapter fails, naming that role
- **AND** it does not draw the role from an instruction of its own

#### Scenario: The adapter adds no design content

- **WHEN** any request is sent
- **THEN** it carries no envelope, feature, component, or style decision that the concept did not state

### Requirement: The adapter runs outside the native turn and its credential never reaches the agent

The adapter SHALL be invoked only by the host, and only while no native turn is in progress. Its credential SHALL be held in host-only storage, loaded lazily at the point of use, and SHALL NOT be written into the run's workspace, the stage packet, the agent's prompt, the agent's process environment, the run's artifacts, or any status output.

#### Scenario: Drawing happens between turns

- **WHEN** the adapter draws a concept's images
- **THEN** no native turn is in progress

#### Scenario: The credential stays on the host

- **WHEN** a run has drawn a concept
- **THEN** the credential appears in no file inside the run workspace, no stage packet, no prompt, no artifact, and no status output
- **AND** it was not present in the environment of any launched agent process

#### Scenario: A leaked credential fails the run

- **WHEN** the credential would be written into any agent-readable location
- **THEN** the run fails rather than completing the effect

### Requirement: No vendor, model, or endpoint is assumed

The adapter SHALL require its provider configuration to be supplied explicitly, and SHALL reject construction without it. No provider, model identifier, or endpoint SHALL be hardcoded as the contract. Every call SHALL target the configured origin and SHALL NOT be redirected to a different host.

#### Scenario: Construction without configuration is rejected

- **WHEN** the adapter is constructed with no provider configuration
- **THEN** construction fails and no adapter is produced

#### Scenario: The configured origin is pinned

- **WHEN** the adapter makes any call
- **THEN** the call targets the configured origin
- **AND** a response attempting to redirect it to a different host is refused

### Requirement: Images are drawn in an order that accumulates references

The adapter SHALL draw the concept's roles in the order the concept specifies, supplying earlier images of the same set as visual references to later ones, so that every image in the set depicts one and the same object. Reference bytes SHALL be read from the concept tree and carried inline; a reference SHALL NOT be uploaded to a public location, and no filesystem path or local-file URL SHALL be sent in place of the bytes.

Where a request's references cannot all be supplied, the adapter SHALL fail that request rather than draw it from a partial reference set.

#### Scenario: Later roles receive earlier images as references

- **WHEN** a role is drawn that the concept declares depends on earlier roles
- **THEN** every one of those earlier images is supplied as a reference, in the order the concept named them

#### Scenario: References travel as bytes

- **WHEN** a request carries references
- **THEN** each is carried as inline image data
- **AND** no path, local-file URL, or public upload location is sent in its place

#### Scenario: An unreadable reference fails closed

- **WHEN** a reference cannot be read from the concept tree
- **THEN** the adapter fails, naming the reference
- **AND** it does not send a partial reference set

#### Scenario: Too many references fails rather than silently drops

- **WHEN** a request's reference count exceeds what the configured provider accepts
- **THEN** the adapter fails, naming the excess
- **AND** it does not send a truncated reference set

### Requirement: Only bytes the provider actually returned are written

On a successful call the adapter SHALL write the returned image bytes unmodified into the concept tree at the path the concept's descriptor names for that role. It SHALL NOT write a file for a call that returned no image, SHALL NOT modify returned bytes, and SHALL NOT return a path to a file the provider did not produce.

The adapter SHALL refuse a response whose body exceeds its configured maximum rather than accept a truncated one.

#### Scenario: A successful call writes exactly what came back

- **WHEN** the provider returns an image for a role
- **THEN** those exact bytes are written at the path the descriptor names for that role

#### Scenario: A response with no image leaves no file behind

- **WHEN** the provider's response contains no image data
- **THEN** the adapter fails, naming the role
- **AND** no file is written for that role

#### Scenario: An oversized response is refused

- **WHEN** a response body exceeds the configured maximum size
- **THEN** the adapter fails that request rather than accepting a truncated body

#### Scenario: A malformed response is not read as an image

- **WHEN** a response is not valid, or is valid without image data in the expected shape
- **THEN** the adapter fails, naming the role and the malformed response
- **AND** it treats no field of that response as an image

### Requirement: A partial set is never sealed

The concept's image set SHALL be complete or absent. Where any required role cannot be drawn, the adapter SHALL fail the concept, and no partial set SHALL be sealed or handed to Make. Where a role a later role depends on cannot be drawn, the dependent roles SHALL NOT be attempted.

#### Scenario: A failed role fails the set

- **WHEN** any required role cannot be drawn
- **THEN** the concept fails
- **AND** no partial image set is sealed

#### Scenario: Dependents of a failed role are not attempted

- **WHEN** a role that later roles reference cannot be drawn
- **THEN** no role depending on it is requested

### Requirement: Failures name the failing role, and transient failures are bounded before failing

A failure SHALL name which role failed to draw. A failure the provider reports as retryable SHALL be retried a bounded number of times before failing; a failure it reports as non-retryable SHALL fail immediately without retry. The adapter SHALL NOT retry a failure into a fabricated success.

#### Scenario: A non-retryable failure fails immediately

- **WHEN** the provider reports a non-retryable failure
- **THEN** the adapter fails that role immediately, naming it, without retrying

#### Scenario: A retryable failure is bounded

- **WHEN** the provider reports a retryable failure on every attempt
- **THEN** the adapter retries up to its configured bound and then fails, naming the role

#### Scenario: No failure becomes a success

- **WHEN** any call fails
- **THEN** no image file is produced for that role from any source other than the provider's own response

### Requirement: Absent configuration parks the run rather than failing it

Where the adapter's configuration is absent, the run SHALL be recorded as waiting with a need naming the image capability and what would satisfy it, on the same terms as any other unperformed host effect. The concept's accepted brief and research SHALL be preserved, so resuming once the configuration exists continues the same run and the same design rather than researching and deciding it again.

An absent configuration SHALL NOT be treated as permission to proceed to Make without images.

#### Scenario: Missing configuration waits with a need

- **WHEN** a concept's brief is accepted and the adapter has no configuration
- **THEN** the run is recorded as waiting, with a need naming the image capability
- **AND** the run does not advance to Make

#### Scenario: The accepted design survives the wait

- **WHEN** a run waiting for image configuration is resumed
- **THEN** it draws the images for the brief it already accepted
- **AND** it does not research or decide the design again

#### Scenario: Waiting is not a licence to skip images

- **WHEN** the adapter has no configuration
- **THEN** no concept is sealed without its image set
