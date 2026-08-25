## Why

Concept ships with the seam for a `concept_artist` and an `explode_inspector` (`DefaultConcept`, `src/inventor_workshop/concept.py`) but no real implementation of either — every run without one parks with `WaitingFor(Need("concept", "concept-images", ...))`, and the only artist that exists (`tools/concept_fixture.py`) is explicitly a fixture that draws synthetic swatches, never a picture of anything. Concept cannot do the one thing it exists for — visualize a design before Make builds it — until a real provider is wired in.

## What Changes

- Add `OpenRouterConceptArtist`, a real `ConceptArtist` that calls OpenRouter's unified image API (`POST /api/v1/images`, model `openai/gpt-image-2`) to draw each concept image, passing prior images as base64 `input_references` for the reference-and-edit chain `concept.py` already builds (front → top/bottom → exploded → components), and writing the returned bytes into the request's workspace.
- Add `OpenAICompatibleExplodeInspector`, a real `ExplodeInspector` that sends the exploded view plus the brief's component list to a configurable OpenAI-compatible vision `/chat/completions` endpoint (base URL, API key, and model all caller-supplied, no vendor hardcoded) and parses its answer into the component keys it reports as visible.
- Both adapters reuse the Shop door's transport pattern (`Transport`/`HttpResponse`/`urllib_transport` in `shop.py`): stdlib `urllib`-only HTTP, an injectable transport for tests, pinned HTTPS origins, bounded response sizes (raised for image payloads), and bearer-token auth — no new HTTP dependency.
- Neither adapter is wired into any inventor's `WorkshopTools` by this change; they are constructed explicitly by whoever operates a Workshop, the same way `ShopDoor` is today.

## Capabilities

### New Capabilities
- `workshop/concept-artist-openrouter`: A real `ConceptArtist` backed by OpenRouter's image API — request shape, reference-image encoding, response parsing, and failure behavior.
- `workshop/concept-explode-inspector`: A real `ExplodeInspector` backed by a caller-configured OpenAI-compatible vision endpoint — request shape, component-key parsing, and failure behavior.

### Modified Capabilities
(none — `workshop/concept-images`, `workshop/concept-job`, and `workshop/make-concept-adherence` already specify the `ConceptArtist`/`ExplodeInspector` seam; this change supplies real implementations of it, not new requirements on Concept itself.)

## Impact

- New modules in `src/inventor_workshop/` (adapter code, not wired into `DefaultConcept` by default).
- New runtime dependency: outbound HTTPS calls to OpenRouter and to a caller-configured OpenAI-compatible host. No new Python package dependency — HTTP stays on stdlib `urllib`, matching `shop.py`.
- New required configuration for anyone who wants to use these adapters: an OpenRouter API key, and a base URL / API key / model for the explode-inspector endpoint. Nothing changes for a Workshop that does not construct them — `DefaultConcept` still waits truthfully with no artist configured.
- Tests exercise both adapters against an injected fake transport; no real network calls in the test suite.
