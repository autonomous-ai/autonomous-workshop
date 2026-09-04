# ADR 0042: Connect each Inventor through browser authorization

- Status: Accepted
- Date: 2026-09-03
- Owners: Workshop CLI, Autonomous website, Autonomous Toys API

## Decision

- Give every Inventor its own shop account.
- First `create` or `start` without a credential opens
  `https://www.autonomous.ai/toys/inventor/login`.
- `workshop login <inventor-id>` reconnects or switches the account.
- Signed-out users sign in. Signed-in users confirm the active account or use
  **Use another account**.
- CLI creates random state, an in-memory PKCE verifier/challenge, and a one-shot
  `127.0.0.1` callback.
- Website asks the API for a five-minute, single-use authorization code, then
  navigates the browser to the callback with only `code` and `state`.
- Website never fetches, probes, or posts credentials to the loopback address.
- CLI verifies state and exchanges `code` plus the PKCE verifier directly with
  the API. The generated username and password are returned only to the CLI.
- Store username, password, and Inventor id in
  `$WORKSHOP_HOME/credentials/inventors/<inventor-id>.env`; directory `0700`,
  file `0600`, atomic replacement.
- Release uses the stored pair with `/auth/agent/login` and keeps its bearer in
  memory.
- No publishing credential in browser JavaScript, URLs, product workspaces,
  agent environments, artifacts, logs, or receipts.
- Existing host-wide credentials remain compatibility-only.
- Deploy API, then website, then Workshop CLI.

## Result

- Standard browser-to-CLI redirect; no public-page request into the local
  network and no Chrome local-network permission prompt.
- Intercepted codes are short-lived, single-use, and unusable without the PKCE
  verifier.
- Publication remains a host-owned effect.

## Verification

- State, PKCE, purpose separation, expiry, replay, redirect validation, and
  malformed-response tests.
- Private-file permissions, Inventor binding, API login, and bounded re-login
  tests.
- CLI create/start/login tests and browser QA for signed-in, signed-out, and
  account-switch flows.
