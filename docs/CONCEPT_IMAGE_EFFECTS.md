# Concept image effects

New runs that freeze `invent-concept-v1.md` activate Concept inside Forge or
Quest Invent. This does not add a stage: the native Invent turn authors exact
pre-render source, exits without credentials, and the trusted host renders and
seals the required roles before the Invent gate may advance to Make.

The next `invent-concept-v2.md` boundary is implemented but remains disabled
for ordinary new runs until authenticated Forge and Quest acceptance passes.
Its native turn authors exactly `invent-source.json` and the packet-bound
`visual-plan.json`; the host derives Concept v3 and executes the plan's 2 to 20
ordered adaptive roles. The primary-form role is first, a signature-experience
role is mandatory, and references may name only earlier roles. No fixed view or
per-component image family is implied. Acceptance operators may opt in with
`WORKSHOP_INVENT_CONCEPT_V2_ACCEPTANCE=1`; this freezes v2/v14 into that run and
does not enable other runs.

## Authorization and configuration

Selecting Forge or Quest for a newly marked run records prospective authority
to transmit only drawing-instruction text and exact already-completed
reference-role images to the frozen `openrouter-images-v1` profile. Spark has
no Concept-render authority. Credentials are not inferred as consent and never
enter the workspace or native subprocess.

Set `WORKSHOP_CONCEPT_IMAGE_CREDENTIALS_FILE` to an absolute path for a private
mode-`0600` JSON file:

```json
{
  "schema_version": 1,
  "profile": {
    "profile_id": "openrouter-images-v1",
    "origin": "https://openrouter.ai",
    "model": "openai/gpt-image-2",
    "request_schema_version": "openrouter-images-v1",
    "supports_idempotency": false,
    "supports_operation_readback": false,
    "supports_absence_proof": false
  },
  "api_key": "<private provider key>"
}
```

The profile must exactly match the non-secret profile frozen in the run's
private authorization record. A missing, permissive, linked, or mismatched file
leaves the run waiting at Invent before transmission.

## Durable behavior and recovery

The host validates the complete assignment, Invented source, provenance,
derived Wish, source manifest, and structural rules before creating effect
intent. Each role has a durable private identity binding checkpoint, subject,
pre-render Concept, instruction, output path, ordered reference hashes, profile,
model, and request schema. V1 roles run in their fixed authored dependency
order. V2 intents additionally bind the exact role facts and canonical
normalized constraint block and run in the adaptive plan's declared order.

A proven pre-transmission failure can retry the same intent on `workshop
resume`. A provider rejection remains rejected. If transmission may have
occurred and the configured provider cannot prove completion or absence, the
operation becomes `unknown`; resume does not resend it. Restore authenticated
provider readback or resolve the operation manually before continuing. Status
exposes only a bounded Invent need, never credentials, operation ids, raw
responses, or private diagnostics.

After every role succeeds, the host atomically installs and rehashes exact
image bytes, writes sanitized `sealed.json` and `effect.json`, and applies one
Invent-to-Make gate. These records prove role completeness and byte identity
only—not aesthetic quality, buildability, printability, testing, manufacture,
or delivery.

## Make, Release, and archives

Marked Make receives the complete sealed Concept and sanitized effect record.
Its schema-v2 `made.json` binds both identities, requires exact component-key
correspondence, rehashes the Concept tree again, and rejects any product file
whose bytes copy a Concept image. Playtest and Release carry that Made identity
without treating Concept research or imagery as product evidence.

The private run retains the exact source, images, sanitized effect, and private
ledger. Factory receives only the current product and Release package—never
Concept pixels or provider-private state. A public source snapshot records the
Concept hashes; it copies exact Concept source and images only when the existing
exact-Wish disclosure authority is enabled. Operation ids, raw provider
responses, credentials, and the private ledger are never copied.
