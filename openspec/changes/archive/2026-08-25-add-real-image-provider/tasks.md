## 1. Shared HTTP transport helper

- [x] 1.1 Extract `HttpResponse`, `Transport`, and `urllib_transport` from `src/inventor_workshop/shop.py` into a new `src/inventor_workshop/_http.py`, parameterizing `urllib_transport`'s max response size (currently the hardcoded `MAX_RESPONSE_BYTES = 2 MiB`) so callers can pass a larger cap
- [x] 1.2 Update `shop.py` to import these from `_http.py` and re-export them under their existing names; keep its own 2 MiB cap and existing behavior unchanged
- [x] 1.3 Run the existing Shop test suite and confirm no behavior change from the extraction

## 2. OpenRouter concept artist

- [x] 2.1 Add `src/inventor_workshop/concept_artist_openrouter.py` with `OpenRouterConceptArtist`, constructed with a required `api_key`, an image-response byte cap, a request timeout, and a bounded retry count — all with sane defaults but overridable
- [x] 2.2 Implement request building: `model="openai/gpt-image-2"`, `prompt=request.prompt`, `n=1`, no `seed`/`temperature`, `input_references` built from `request.references`
- [x] 2.3 Implement reference encoding: read each reference file, sniff its actual image format from magic bytes (reject anything unrecognized), base64-inline it as a `data:` URL
- [x] 2.4 Reject requests whose reference count exceeds the provider's supported per-call limit, naming the excess, instead of truncating
- [x] 2.5 Implement response handling: parse the returned image bytes, write them unmodified to `request.workspace / request.filename`, return `request.filename`
- [x] 2.6 Implement failure handling: immediate failure on non-429 4xx; bounded retry with backoff on 429/5xx; clear error naming the failed role for a malformed/empty response or an oversized response body
- [x] 2.7 Implement construction-time validation: reject an empty/missing API key
- [x] 2.8 Implement origin pinning: requests always target OpenRouter's HTTPS origin regardless of any redirect

## 3. OpenAI-compatible explode inspector

- [x] 3.1 Add `src/inventor_workshop/concept_explode_inspector.py` with `OpenAICompatibleExplodeInspector`, constructed with required `base_url`, `api_key`, and `model`, plus a response byte cap, request timeout, and bounded retry count
- [x] 3.2 Implement construction-time validation: reject a missing/empty base URL, API key, or model
- [x] 3.3 Implement request building: POST to the configured base URL's chat-completions path, naming the configured model, with a prompt listing every brief component's key and name and instructing the endpoint to answer in JSON using only those keys
- [x] 3.4 Encode the exploded image inline (base64 data URL) in the vision content of the request, never by URL
- [x] 3.5 Implement strict response parsing: extract and parse the endpoint's JSON answer into a set of keys; raise on anything unparseable rather than returning an empty result; raise if the answer names a key that was not offered
- [x] 3.6 Implement failure handling: immediate failure on non-429 4xx; bounded retry with backoff on 429/5xx; reject an oversized response body

## 4. Tests

- [x] 4.1 Unit tests for `OpenRouterConceptArtist` against an injected fake transport: no-reference draw, reference-attached draw, reference encoding/content-sniffing, missing-reference failure, no-seed/n=1 assertion on every call, successful write-and-return, empty-image-data failure, 4xx immediate failure, 429/5xx retry-then-fail, oversized-response rejection, too-many-references rejection, missing-API-key construction failure, pinned-origin behavior
- [x] 4.2 Unit tests for `OpenAICompatibleExplodeInspector` against an injected fake transport: request lists every component, image sent inline, well-formed subset parsed correctly, unparseable answer raises, unknown-key answer raises, request targets configured base URL/model/credential, 4xx immediate failure, 429/5xx retry-then-fail, oversized-response rejection, missing-config construction failures
- [x] 4.3 Confirm both classes satisfy the `ConceptArtist`/`ExplodeInspector` callable contracts by running each through `DefaultConcept` with a fake transport end-to-end (mirroring `tests/test_concept_pipeline.py`'s fixture-based tests, but using these real adapters with a faked HTTP layer instead of the swatch fixture)

## 5. Exports

- [x] 5.1 Export `OpenRouterConceptArtist` and `OpenAICompatibleExplodeInspector` from `src/inventor_workshop/__init__.py`

## 6. `.env` configuration (added after initial apply, per follow-up request)

- [x] 6.1 Add `src/inventor_workshop/env.py::load_dotenv`, a dependency-free `.env` parser matching `inventors/bob/bob.py`'s `_load_dotenv` convention (comments/blank lines skipped, `setdefault` so a real env var always wins, missing file is not an error)
- [x] 6.2 Add `OpenRouterConceptArtist.from_env(dotenv_path=None, **overrides)`, reading `OPENROUTER_API_KEY` (required), `OPENROUTER_IMAGE_MODEL` and `OPENROUTER_API_BASE` (optional)
- [x] 6.3 Add `OpenAICompatibleExplodeInspector.from_env(dotenv_path=None, **overrides)`, reading `CONCEPT_EXPLODE_INSPECTOR_BASE_URL`, `CONCEPT_EXPLODE_INSPECTOR_API_KEY`, `CONCEPT_EXPLODE_INSPECTOR_MODEL` (all required)
- [x] 6.4 Export `load_dotenv` from `src/inventor_workshop/__init__.py`
- [x] 6.5 Unit tests: `load_dotenv` parsing/precedence/missing-file, both `from_env()` methods reading a `.env` file, real-env-wins-over-file, explicit overrides win over environment, missing-required-variable errors naming the variable
