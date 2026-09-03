# Design vault

The design vault is a typed-link graph of game-design knowledge — mechanisms
link to their known risks, risks to anti-patterns, anti-patterns to the fixes
that worked, and every shipped wish adds its own `games/<wish-id>` page. The
graph is maintained outside this repository and served by an ops dashboard at
`/api/gamevault/*` behind one bearer token. The Workshop host is a client of
that API (`workshop.invent.gamevault`); product runs never talk to it — the
Codex sandbox has no network, so the host hands each phase a hash-bound,
read-only snapshot (`VAULT.json`, bound in `STAGE.json`) plus the leads it
computed from that snapshot.

## What a run does with it

- **Invent** must resolve each concept mechanism to a vault node or declare it
  novel; declared conflicts and unmet requirements are refused on both the
  finalizer and host sides.
- **Make** and **Playtest** packets carry `vault_leads` — recorded risks for
  the mechanisms the concept uses. Playtest must answer every lead: confirm it
  (naming the feedback item that repairs it) or dismiss it in one sentence.
- After a sealed Playtest, the host writes back: confirmed leads bank evidence
  on the matching vault nodes, dismissals queue for review, and the product's
  own page (mechanisms used, verdict, median scores, lessons) is posted.

## Configuration

The host resolves the vault URL and token in this order:

1. `WORKSHOP_GAMEVAULT_URL` and `WORKSHOP_GAMEVAULT_TOKEN` in the process
   environment;
2. the private file `$WORKSHOP_HOME/credentials/gamevault.env` —
   `NAME=value` lines, mode `0600` inside a `0700` directory. See
   [`gamevault.env.example`](gamevault.env.example).

There is no default URL. Ask the vault operator for the origin and a token;
neither value belongs in the repository or in a product run's environment
(the host never forwards them to Codex).

## Running without the vault

A host with no URL, no token, or an unreachable vault **bypasses the vault for
that checkpoint**: the phase runs exactly like a run without a vault (no
snapshot, no leads, queued write-backs) and the next checkpoint tries again.
Nothing fails; you just build without recorded design knowledge.

For offline work:

- `workshop vault lint` and `workshop vault check <paths>` accept
  `--root <dir>` to read a local vault checkout instead of the API.
- Tests never reach the network: `tests/invent/fake_gamevault.py` installs an
  in-memory transport at the module's single HTTP seam (`_TRANSPORT`).
