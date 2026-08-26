## REMOVED Requirements

### Requirement: The researcher is fully configured by its caller, with no vendor built in

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: Construction without a base URL, key, or model is rejected

- **WHEN** the researcher is constructed missing a base URL, an API key, or a model name
- **THEN** construction fails and no researcher instance is produced

#### Scenario: Two researchers call only their own configured endpoint

- **WHEN** two researchers are constructed with different base URLs and models
- **THEN** each one's calls target only its own configured base URL and model, never the other's

### Requirement: The request carries the Wish, the Taste, and the lane, and asks for a sourced breakdown

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: The request states what is being researched

- **WHEN** the researcher is asked to break down a Wish
- **THEN** the outgoing request carries that Wish's objective and constraints, the Taste description, and the lane category

#### Scenario: The request asks for sourced facts

- **WHEN** the researcher makes a call
- **THEN** the request instructs the endpoint to attribute each stated fact to a source it read, and to say so explicitly where it had none

#### Scenario: Web search is requested

- **WHEN** the researcher makes a call
- **THEN** the request enables the endpoint's web search facility

### Requirement: The response is parsed strictly into a breakdown and its sources

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted. The strict-parsing posture itself survives — it moves into the agent-backed adapter along with the parsing logic it was built on.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: A well-formed answer becomes a breakdown

- **WHEN** the endpoint returns an answer stating the object, category, envelope, wall thickness, features, print stance, components, and their sources
- **THEN** the researcher returns exactly those facts and exactly those sources

#### Scenario: An unparseable answer fails rather than returning an empty breakdown

- **WHEN** the endpoint's answer cannot be parsed into a breakdown
- **THEN** the researcher raises an error rather than returning a breakdown with nothing decided

#### Scenario: A missing field fails rather than being defaulted

- **WHEN** the endpoint's answer omits a fact the breakdown must state
- **THEN** the researcher raises an error naming the missing fact, rather than filling it in

#### Scenario: A cited source with no returned material fails

- **WHEN** the answer attributes a fact to a source for which the endpoint returned no origin or excerpt
- **THEN** the researcher raises an error rather than recording a source it cannot show

### Requirement: Requests follow the OpenAI-compatible chat completions contract

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: A request targets the configured endpoint and model

- **WHEN** the researcher makes a call
- **THEN** the request goes to the configured base URL's chat-completions path and names the configured model

#### Scenario: A request carries the configured credential

- **WHEN** the researcher makes a call
- **THEN** the request carries the configured API key as a bearer credential

### Requirement: Failures are surfaced, never silently swallowed into a false result

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: A non-retryable client error fails immediately

- **WHEN** the configured endpoint returns a 4xx error other than 429
- **THEN** the researcher fails immediately, without retrying

#### Scenario: A rate-limit or server error is retried then fails

- **WHEN** the configured endpoint returns 429 or a 5xx error on every attempt
- **THEN** the researcher retries up to its configured bound and then fails

#### Scenario: An oversized response is rejected

- **WHEN** the configured endpoint's response body exceeds the researcher's configured maximum size
- **THEN** the researcher fails that request rather than accepting a truncated body

### Requirement: The researcher is constructed by an operator, never wired in by default

**Reason**: `wish-research` is settled on the agent-backed researcher; the OpenAI-compatible HTTP researcher this capability describes is deleted. The surviving agent-backed researcher continues this same never-wired-by-default posture, now specified under `workshop/agent-concept-adapters`.
**Migration**: Configure `wish-research` through the agent door instead — see `workshop/agent-concept-adapters` and `workshop/concept-capability-wiring`.

#### Scenario: Importing the adapter changes no Workshop

- **WHEN** the adapter module is imported but no researcher is constructed and installed
- **THEN** every Workshop still reports the wish-research capability as missing
