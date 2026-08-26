# Effects, authorization, and recovery

Read this reference on resume, retry, an effect-related wait, ambiguous result,
or recovery. The durable workspace and host state are the source of truth;
neither chat text nor model memory proves an effect. The product-run agent does
not perform authenticated external operations itself.

## Authorization boundary

Codex never receives or reads Factory, payment, manufacturing, carrier, or
other effect credentials. It may prepare local artifacts and a compact effect
request for the host.

The host may execute an effect only when the run's recorded authorization
covers that exact action and target. Explicit human authorization is required
before public publication, spending or purchasing, starting manufacture,
buying postage, shipment, or another irreversible/customer-visible action.
Private draft creation also stays behind the host boundary and occurs only
when the recorded run policy permits it.

The CLI defaults to private output. `--publish` records a prospective public
publication request in host-only state; it never exposes authority or
credentials to Codex and does not authorize manufacture or delivery.

Authorization is narrow and prospective. Approval for one artifact hash,
environment, account, price, or shipment does not cover changed bytes, another
target, a higher cost, or an ambiguous retry.

## Effect protocol

The trusted host, not Codex:

1. Revalidates all upstream contracts and exact artifact hashes.
2. Stores an effect intent and stable idempotency token before crossing the
   external boundary.
3. Supplies credentials only to the narrow adapter performing that effect.
4. Reconciles by authenticated readback and binds the receipt to the exact
   request and artifact hashes.
5. Commits the verified receipt and next checkpoint atomically enough that a
   restart can distinguish pending, known-complete, rejected, and unknown.

Codex can inspect a redacted receipt and respond to a typed failure. It cannot
declare success from a command exit code, URL, prose, or unverified response.

## Ambiguous external outcomes

Never blindly repeat an effect after a timeout, disconnect, crash, or malformed
response. First reconcile using the stored intent, idempotency token, account,
remote identifier, and exact hashes. Then:

- record success only when readback proves the requested state;
- retry only when reconciliation proves the effect did not occur and host
  policy still authorizes it;
- otherwise checkpoint an unknown/needs-human state without changing the
  artifact or claiming completion.

## Codex session recovery

Resume the same native Codex session id for the Wish. On every resume, inspect
the durable checkpoint, manifests, working tree, and only the redacted effect
state or receipts the host explicitly provides. Durable intents themselves are
host-only and outside the product workspace. If session memory conflicts with
sealed files or host-provided receipts, follow the durable evidence and note
the discrepancy.

If a Match, Invent, Make, Playtest, or Release Goal is active for that exact
checkpoint, continue it instead of creating a duplicate. Reestablish its
objective, proof artifacts, and stopping condition from `STAGE.json`, then
resume the observe -> act -> evaluate -> improve work. Goal state is not
recovery authority: if it names another checkpoint or contradicts sealed
bytes, stop and report the mismatch rather than continuing stale work. Never
create a Deliver Goal or a Goal whose objective is to retry an external
effect.

For an explicitly classified provider transport interruption that occurred
before any effect boundary, the host may make at most one bounded reconnect or
resume attempt. Do not retry authentication failures, policy denials, invalid
or oversized output, schema/contract failures, deterministic gate failures, or
unknown external effects. Never accept a partial chat response as a stage
artifact; inspect any partial workspace writes and rerun their gates.

## Artifact recovery and invalidation

- Preserve the last sealed upstream artifact. Repair in a new revision or
  attempt directory rather than mutating evidence already cited by a receipt.
- Recompute manifests after every material change. A stale hash or receipt is a
  failure, not a warning.
- A new Make revision invalidates Playtest, Release, and Deliver evidence
  for the prior bytes. Run those gates again in order.
- Respect the host's exclusive mutation lock and bounded Make–Playtest round
  budget. Concurrent work must stop at a typed need instead of racing the
  checkpoint.
- Keep research, judging, repair, and feedback iteration inside the active
  native Codex Goal. Do not create a Python retry, reward, judge, or loop
  controller during recovery.
- Keep diagnostics bounded and redacted. Record safe failure categories and
  evidence references, never prompts, credentials, authorization headers, or
  large provider streams.
