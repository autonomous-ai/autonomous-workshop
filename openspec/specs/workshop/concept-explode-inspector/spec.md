## Purpose

A real `ExplodeInspector` that checks whether a produced exploded-view image actually separates every component named in a `ConceptBrief`, by asking a caller-configured OpenAI-compatible vision endpoint which components it can see.

## Requirements

### Requirement: The inspector is fully configured by its caller, with no vendor built in

The inspector SHALL require a base URL, an API key, and a model name at construction, and SHALL reject construction if any of them is missing or empty. It SHALL NOT default to, or assume, any particular vendor's endpoint — every call target is exactly what the caller configured.

#### Scenario: Construction without a base URL, key, or model is rejected

- **WHEN** the inspector is constructed missing a base URL, an API key, or a model name
- **THEN** construction fails and no inspector instance is produced

#### Scenario: Two inspectors call only their own configured endpoint

- **WHEN** two inspectors are constructed with different base URLs and models
- **THEN** each one's calls target only its own configured base URL and model, never the other's

### Requirement: The inspector asks which offered components are visible in the exploded image

For a given exploded image and brief, the inspector SHALL send the image inline (not by URL) together with the key and name of every component in the brief, using the OpenAI-compatible chat-completions vision request shape, and SHALL instruct the endpoint to answer only using the component keys it was given.

#### Scenario: The request lists every offered component

- **WHEN** the inspector is asked to check an exploded image against a brief with N components
- **THEN** the outgoing request names all N component keys and their names

#### Scenario: The image is sent inline, not by URL

- **WHEN** the inspector sends its request
- **THEN** the exploded image is embedded as inline image data in the request body, not referenced by a URL

### Requirement: The response is parsed strictly into the reported component keys

The inspector SHALL parse the endpoint's answer and return exactly the subset of offered component keys the answer reports as visible. It SHALL NOT report a key that was not among the components it offered, and SHALL NOT treat an answer it cannot parse as "no components visible."

#### Scenario: A well-formed answer reports exactly the named subset

- **WHEN** the endpoint's answer names some of the offered component keys as visible and omits the rest
- **THEN** the inspector returns exactly the named keys

#### Scenario: An unparseable answer fails rather than reporting zero components

- **WHEN** the endpoint's answer cannot be parsed into a set of component keys
- **THEN** the inspector raises an error rather than returning an empty result that would read as "nothing visible"

#### Scenario: An answer naming an unknown key fails rather than passing it through

- **WHEN** the endpoint's answer names a key that was not among the offered component keys
- **THEN** the inspector raises an error rather than returning that key to its caller

### Requirement: Requests follow the OpenAI-compatible chat completions contract

The inspector SHALL POST to its configured base URL's chat-completions path with the configured model name and an `Authorization` bearer header carrying its configured API key.

#### Scenario: A request targets the configured endpoint and model

- **WHEN** the inspector makes a call
- **THEN** the request goes to the configured base URL's chat-completions path and names the configured model

#### Scenario: A request carries the configured credential

- **WHEN** the inspector makes a call
- **THEN** the request carries the configured API key as a bearer credential

### Requirement: Failures are surfaced, never silently swallowed into a false pass or fail

A non-retryable client error SHALL fail immediately. A rate-limit or server error SHALL be retried a bounded number of times with backoff before failing. An oversized response SHALL be rejected rather than read partially.

#### Scenario: A non-retryable client error fails immediately

- **WHEN** the configured endpoint returns a 4xx error other than 429
- **THEN** the inspector fails immediately, without retrying

#### Scenario: A rate-limit or server error is retried then fails

- **WHEN** the configured endpoint returns 429 or a 5xx error on every attempt
- **THEN** the inspector retries up to its configured bound and then fails

#### Scenario: An oversized response is rejected

- **WHEN** the configured endpoint's response body exceeds the inspector's configured maximum size
- **THEN** the inspector fails that request rather than accepting a truncated body
