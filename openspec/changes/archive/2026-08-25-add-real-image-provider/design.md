## Context

`DefaultConcept` (`src/inventor_workshop/concept.py`) already defines the seam: `ConceptArtist = Callable[[ConceptImageRequest], str]` and `ExplodeInspector = Callable[[Path, ConceptBrief], Sequence[str]]`. The only existing implementations are `tools/concept_fixture.py`'s synthetic-swatch pair, deliberately kept out of `src/` because it is not, and must never look like, a real provider. No HTTP client for either capability exists anywhere in the repo today.

The repo has one precedent for exactly this shape of problem: `ShopDoor` in `shop.py` — an authenticated HTTPS integration built on stdlib `urllib` only (no `requests`/`httpx` dependency), with an injectable `Transport` callable for tests, a pinned-origin check, a bearer `Authorization` header, and a capped, non-redirecting response reader (`HttpResponse`, `urllib_transport`, `MAX_RESPONSE_BYTES = 2 MiB`, `HTTP_TIMEOUT_SECONDS = 120`). See proposal.md for why real providers are needed now.

## Goals / Non-Goals

**Goals:**
- A real `ConceptArtist` that draws through OpenRouter's `openai/gpt-image-2`.
- A real `ExplodeInspector` that checks exploded-view completeness through a caller-configured OpenAI-compatible vision endpoint — no vendor assumed, since the user will supply that endpoint later.
- Both adapters testable without any real network call.
- No new third-party HTTP dependency.

**Non-Goals:**
- Wiring either adapter into any inventor's `WorkshopTools` or into `DefaultConcept` by default. This change ships the adapters; activating one for a specific inventor (env vars, secret storage, `WorkshopTools.concept = DefaultConcept(OpenRouterConceptArtist(...), OpenAICompatibleExplodeInspector(...))`) is a separate, inventor-scoped follow-up.
- Streaming image generation. OpenRouter's image API supports SSE partial frames; Concept only ever consumes the finished bytes, so the adapter always requests the buffered (non-streaming) response.
- Cost/budget enforcement (`BudgetExceeded`-style limits). Bounded retries keep a single failing call from looping, but per-run spend accounting is out of scope here — the existing per-component-count cap in `ConceptBrief` (design of `add-concept-job`) is the accepted cost control.
- Changing anything about `ConceptImageRequest`, prompt text, or the generation order — those are `concept.py`'s contract and are untouched.

## Decisions

### D1 — Two adapters, not one

`OpenRouterConceptArtist` and `OpenAICompatibleExplodeInspector` are separate classes in separate modules (`concept_artist_openrouter.py`, `concept_explode_inspector.py`).

*Why.* They are two different external contracts — image generation vs. vision chat-completions — configured independently (the artist is pinned to OpenRouter; the inspector's endpoint is entirely caller-supplied, per the user's explicit direction that its vendor is not yet known). A Workshop operator may want one without the other, or may swap the inspector's endpoint without touching the artist.

*Alternative rejected.* One `RealConceptProvider` bundling both — smaller diff, but couples two independently-configured integrations and contradicts the "no vendor hardcoded" requirement on the inspector, since a bundled class would need the OpenRouter key even where only inspection is wanted.

### D2 — Extract the Shop Door's HTTP plumbing into a shared internal helper

`HttpResponse`, `Transport`, and `urllib_transport` move from `shop.py` into a new internal module (`src/inventor_workshop/_http.py`); `shop.py` imports them back so its public names and behavior are unchanged. The new adapters import the same helper, with the maximum response size and timeout as constructor parameters rather than the module-level constants `shop.py` uses today, because image payloads (base64 PNG) routinely exceed Shop's 2 MiB cap.

*Why.* This is the established pattern for exactly this problem (pinned-origin HTTPS, injectable transport, capped non-redirecting reads) and reusing it keeps the two new adapters consistent with `ShopDoor` instead of re-deriving the same ~40 lines of `urllib` boilerplate with subtly different edge-case handling. Parameterizing the cap avoids silently inheriting a limit that was sized for JSON API responses, not images.

*Alternative rejected.* Add `requests` or `httpx` as a dependency — would simplify the adapter code somewhat, but the repo has deliberately stayed on stdlib `urllib` for its one existing HTTP integration, and introducing a second HTTP stack for no functional gain is not worth the new dependency surface.

### D3 — Credentials and endpoint are constructor arguments; `from_env()` is an opt-in convenience, not a default

Both adapters take `api_key` (and the inspector additionally takes `base_url` and `model`) as required constructor arguments, and the primary `__init__` never reads an environment variable itself.

*Why.* Mirrors `ShopDoor(token=...)`. It keeps the adapters trivially testable (no environment mutation in tests), and it leaves the choice of *how* a secret reaches the constructor — env var, secret manager, per-inventor config file — to whoever wires up a Workshop.

*Addendum — `.env` support.* Each class also gets a `from_env(dotenv_path=None, **overrides)` classmethod: it loads a `.env` file via a new dependency-free `src/inventor_workshop/env.py::load_dotenv` (matching the parsing convention already used by `inventors/bob/bob.py`'s `_load_dotenv` — comments/blank lines skipped, `os.environ.setdefault` so a real environment variable always wins over the file, a missing file is not an error), then reads fixed variable names (`OPENROUTER_API_KEY`/`OPENROUTER_IMAGE_MODEL`/`OPENROUTER_API_BASE`; `CONCEPT_EXPLODE_INSPECTOR_BASE_URL`/`_API_KEY`/`_MODEL`) and calls the ordinary constructor. This is additive, not a reversal of D3: the constructor itself still takes plain arguments and still does no I/O; `from_env()` is one more way to produce those arguments, alongside calling `OpenRouterConceptArtist(...)` directly. No third-party `dotenv` package was added — the core Workshop package ships with zero dependencies, and the hand-rolled parser is already the repo's own precedent.

### D4 — Reference images are content-sniffed and base64-inlined, never sent as file:// or local URLs

Each reference path is read from disk, its format is verified from its magic bytes (not trusted from the filename suffix), and it is sent as a `data:` URL in `input_references`.

*Why.* `jobs.py`'s `_safe_concept_image` already treats a filename suffix as untrusted for exactly this reason (path safety, not content safety) — sniffing bytes before calling them "png" is the same discipline applied to content. Sending inline data rather than a URL is also required by OpenRouter's `input_references` shape for local, non-hosted files, and avoids ever exposing an unsealed concept image at a public URL.

### D5 — The inspector asks for a small, strictly-parsed JSON answer; a response the parser can't trust is a failure, not a pass or an empty result

The inspector's prompt instructs the endpoint to answer with only the visible component keys, in JSON, using exactly the keys it was offered. The adapter extracts and parses that JSON itself (not relying on an OpenAI-specific `response_format` field, since the endpoint's exact capabilities are unknown); anything it cannot parse into a set of offered keys is a raised error, never treated as "zero components visible."

*Why.* Per the spec, an unparseable answer must not silently read as "the exploded view is empty" — that would make a flaky endpoint look like a real completeness failure and could send the concept into an unnecessary regenerate-then-fail path (`concept.py::_complete_explode`). Not depending on a specific structured-output field keeps the adapter compatible with a not-yet-known "custom OpenAI-compatible" endpoint, per the user's direction.

### D6 — Bounded retry only for 429 and 5xx; everything else fails on the first attempt

Both adapters retry a rate-limit or server error a small, fixed number of times with backoff, and fail immediately on any other 4xx or a response that doesn't parse.

*Why.* 429/5xx are the only cases where retrying the identical request is plausibly going to succeed. Retrying a 4xx (bad request, bad auth) would just repeat a request that cannot succeed, burning an image-generation call's cost for nothing — and OpenRouter's own billing note says a failed generation is not charged, so failing fast has no cost downside here.

## Risks / Trade-offs

**The inspector's real endpoint doesn't exist yet.** The user will supply the actual OpenAI-compatible host later. → The adapter's contract (D5: strict JSON, offered-keys-only, fail-don't-guess) is deliberately endpoint-agnostic; tests exercise it against a fake transport. The exact prompt wording may need a follow-up tweak once run against the real endpoint, but that is a prompt change, not a spec or design change.

**`openai/gpt-image-2` is the model name given, and may not (yet) exist as a real OpenRouter catalog entry.** → The request shape (`POST /api/v1/images`, `model`, `input_references`, `n=1`) is OpenRouter's general image-API contract, not specific to that one model string; if the exact model id needs to change later, it is a one-constant edit, not a design change.

**Bigger response cap invites a genuinely huge payload.** → The cap is still enforced and configurable, just sized for images instead of inheriting Shop's JSON-sized 2 MiB; a response larger than the configured cap is rejected outright (per spec), not read into memory unbounded.

**Extracting `shop.py`'s HTTP helper touches an existing, working module.** → The move is a pure relocation with re-export for compatibility; `shop.py`'s existing tests are the regression check that its behavior is unchanged.

## Migration Plan

1. Extract `HttpResponse`, `Transport`, and `urllib_transport` from `shop.py` into `src/inventor_workshop/_http.py`; `shop.py` re-imports them. Run the existing Shop test suite to confirm no behavior change.
2. Add `OpenRouterConceptArtist` in `src/inventor_workshop/concept_artist_openrouter.py`, built on the shared transport helper.
3. Add `OpenAICompatibleExplodeInspector` in `src/inventor_workshop/concept_explode_inspector.py`, built on the same helper.
4. Add unit tests for both against an injected fake transport, covering every scenario in the two new specs.
5. Export both classes from `src/inventor_workshop/__init__.py` so an inventor can construct them without reaching into internal modules.
6. Do not touch `workshop.py`, `scaffold.py`, or any `inventors/*` profile — activation is a separate, later change.

**Rollback.** Both adapters are new, additive, and unused by default; nothing constructs them until an inventor explicitly does. Rollback is deleting the two new modules and their exports and reverting the `shop.py` extraction; no persisted state or running Workshop depends on them.
