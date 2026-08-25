## Purpose

A real `ConceptArtist` that draws every image `Concept` asks for by calling OpenRouter's image-generation API, so a Workshop can produce an actual visualized design instead of waiting on the `concept-images` need forever.

## ADDED Requirements

### Requirement: The artist draws one image per request through OpenRouter

For every `ConceptImageRequest` it receives, the artist SHALL call OpenRouter's image-generation API with the request's `prompt` as the drawing instruction and model `openai/gpt-image-2`, and SHALL request exactly one image.

#### Scenario: A request with no references draws from the prompt alone

- **WHEN** the artist receives a request whose `references` are empty
- **THEN** it calls OpenRouter with that request's prompt and no reference images

#### Scenario: A request with references draws with those images attached

- **WHEN** the artist receives a request whose `references` are non-empty
- **THEN** the call includes every one of those images as reference input, in the same order they were supplied

### Requirement: Reference images travel inline, never as external URLs

The artist SHALL read each reference file's bytes from local disk and encode them as inline (base64 data URL) reference input. It SHALL NOT upload a concept image to a public location or pass a filesystem path or `file://` URL to the API.

#### Scenario: References are encoded inline

- **WHEN** a request carries one or more reference paths
- **THEN** the outgoing call carries each one as inline image data, not a URL pointing back at local storage

#### Scenario: An unreadable reference fails closed

- **WHEN** a reference path cannot be read from disk
- **THEN** the artist raises an error naming the missing reference and does not call OpenRouter with a partial reference set

### Requirement: Determinism knobs are never sent

The artist SHALL NOT send a seed or a temperature to OpenRouter, and SHALL always request exactly one image (`n = 1`).

#### Scenario: No seed is ever sent

- **WHEN** any request is drawn, including a retry of the same role
- **THEN** the call carries no seed parameter

#### Scenario: Exactly one image is requested

- **WHEN** any request is drawn
- **THEN** the call asks for exactly one image

### Requirement: A produced image is written to the request's workspace and returned by relative path

On a successful call, the artist SHALL write the returned image bytes unmodified to `request.workspace / request.filename` and SHALL return `request.filename`, matching the `ConceptArtist` contract Concept already relies on.

#### Scenario: A successful call writes the file and returns its relative path

- **WHEN** OpenRouter returns exactly one image for a request
- **THEN** the artist writes those exact bytes to the request's filename inside its workspace
- **AND** it returns that filename

#### Scenario: A response with no image leaves no file behind

- **WHEN** OpenRouter's response contains no image data
- **THEN** the artist raises an error naming the requested role
- **AND** it does not write a file for that request

### Requirement: Authentication and origin are fixed at construction, not per call

The artist SHALL require a non-empty OpenRouter API key at construction and SHALL reject construction without one. Every call SHALL carry that key as a bearer credential and SHALL target the pinned OpenRouter HTTPS origin; no call may be redirected to a different host.

#### Scenario: Construction without an API key is rejected

- **WHEN** the artist is constructed with no API key or an empty one
- **THEN** construction fails and no artist instance is produced

#### Scenario: Every call is authenticated and pinned

- **WHEN** the artist makes any OpenRouter call
- **THEN** the call carries the configured bearer credential
- **AND** it targets the pinned OpenRouter origin regardless of any redirect the response attempts

### Requirement: Failures are surfaced with the failing role identified, never silently retried into a false success

A non-retryable client error SHALL fail immediately. A rate-limit or server error SHALL be retried a bounded number of times with backoff before failing. In every failure case the artist SHALL raise an error that names which image role failed to draw, and SHALL NOT return a path to a file that was not actually produced by OpenRouter.

#### Scenario: A non-retryable client error fails immediately

- **WHEN** OpenRouter returns a 4xx error other than 429
- **THEN** the artist fails immediately for that request, naming the role, without retrying

#### Scenario: A rate-limit or server error is retried then fails

- **WHEN** OpenRouter returns 429 or a 5xx error on every attempt
- **THEN** the artist retries up to its configured bound and then fails, naming the role

#### Scenario: A malformed response fails clearly

- **WHEN** OpenRouter's response is not valid JSON, or is valid JSON without image data in the expected shape
- **THEN** the artist raises an error identifying the role and the malformed response, rather than treating any field as an image

### Requirement: Oversized responses and reference sets are rejected, not silently truncated

The artist SHALL reject a response whose body exceeds a defined maximum size rather than reading part of it. It SHALL reject a request whose reference count exceeds the provider's supported limit rather than sending only the first N and silently dropping the rest.

#### Scenario: An oversized response is rejected

- **WHEN** OpenRouter's response body exceeds the artist's configured maximum size
- **THEN** the artist fails that request rather than accepting a truncated body

#### Scenario: Too many references fails rather than drops images silently

- **WHEN** a request's reference count exceeds the number of references OpenRouter's image API accepts per call
- **THEN** the artist fails that request naming the excess, rather than sending a truncated reference set
