# CLI

`cli` is the installed command-line adapter for Autonomous Workshop. It parses
commands, calls the public `workshop.workflow` host API, formats results, and
chooses exit codes. Lifecycle, native-session, gate, and effect behavior stays
in the component that owns it.

Run it from a source checkout with `PYTHONPATH=src python -m cli --help`, or use
the installed `workshop` command.

`workshop wish --workflow spark|forge|quest "..."` freezes the selected route;
Spark is the default. `--agent`, `--model`, and `--effort` freeze the native
runtime, model, and reasoning level. Codex defaults to `gpt-6-astra` at medium;
Claude Code defaults to `claude-opus-5` at medium. Status and resume read those
durable choices rather than accepting replacements.

`--agent codex --model astra --effort ultra` enables native Astra Ultra.
Ultra is rejected for other models and agents; the default remains medium.

`workshop wish --inventor <id> "..."` pins the exact Inventor in the immutable
Wish and materializes only that Inventor into the run roster. Without the flag,
the complete eligible roster is materialized and the native Manager chooses the
best match. A Wish created by `workshop start <id>` is pinned automatically to
the Inventor who produced its sealed daydream.

New Spark runs bind that selection in Workshop setup before Make; automatic
selection and Make use the same native session. Publish is then host-owned:
it uploads Make's existing files, derives site metadata, and verifies public
readback. It does not start another native turn, rebuild CAD, review the product,
or require a new PDF. The durable publication checkpoint is still named
`release`. Existing Forge/Quest and historical Release contracts remain readable.

`workshop create inventor` and the first `workshop start <inventor-id>` open
`https://www.autonomous.ai/toys/inventor/login` when that Inventor is not yet
connected. The CLI prints the complete authorization URL, opens the browser,
and waits on a random-state, one-shot loopback callback. The callback receives
only a short-lived code; the CLI exchanges it directly with the Autonomous Toys
API using its in-memory PKCE verifier. It stores the generated Factory
username/password and canonical Inventor id in the owner-only
`$WORKSHOP_HOME/credentials/inventors/<inventor-id>.env`. The stored id must
match the Inventor selected for publication. The publishing credential never
enters browser JavaScript, a URL, run workspace, or native-agent environment.
`workshop login <inventor-id>` explicitly repeats the same flow.

`workshop create inventor <id> --taste <path/TASTE.md> --local-only` creates
and statically checks a local experimental Inventor without connecting an
account. Use this while authoring a new Taste and specialist skill. The flag
does not change publication authentication or grant external-effect authority;
normal `create inventor` and `start` retain their account setup behavior.

`workshop login <target-inventor> --reuse-from <connected-inventor>` connects
another Inventor to an existing saved publishing account. It reads only that
Inventor's private credential, authenticates it, then atomically stores the
target binding. It never falls back to the shared account or environment
credentials. The command prints the connected account name, never its secrets.

`workshop start <inventor-id>` is the front door and a loop: it asks one
Inventor to dream one fresh, Taste-fitting idea through `workshop.daydream`, prints the
sealed concept card, seals it as a Wish, starts the same native session
`workshop wish` would (Spark by default), and then dreams the next idea. It
holds the Inventor's loop lease and checks the stop marker between steps, so
`workshop stop <inventor-id>` ends it after the current step (`--now` also
sends SIGINT) and Ctrl-C ends it at once with the current run resumable.
Three consecutive failures stop it; `--once` and `--max-ideas` bound it.
`workshop daydream <inventor-id>` dreams and prints the card without building;
`workshop start <inventor-id> --idea <daydream-id>` builds a saved idea. The
CLI never judges or edits the idea; novelty and Taste fit are the Daydream
component's job.

The two product commands therefore share one build path but express different
sources and cardinality: `workshop wish` makes one product from a human-provided
idea, while `workshop start` continuously makes products from an Inventor's own
ideas. `workshop start --once` is the bounded autonomous-idea variant.

`start` and `wish` accept `--max-tokens N` (maximum `500000000`, default `30000000`) for the whole
Codex product, including all build stages, native children and resumes. The
separate Daydream session is excluded. All revisions and retries share that
allowance without a native-turn or wall-clock execution cap.
`wish`, `start` and `resume` also accept `--turn-minutes M`, which bounds each
native turn to `M` minutes (1 to 360), or `--turn-minutes none` to run with no
Workshop wall clock at all. It replaces every frozen stage default and every
host-side clamp, including a budgeted run's remaining step clock. Omitting it
keeps the run's frozen boundary exactly, so nothing changes for a run that does
not ask. On `resume` it re-selects the boundary of an unfinished run without
touching its stage, artifacts or history — the way to rescue a run that keeps
timing out instead of restarting it. An untimed run still needs the Manager's
own bound, which today means a Codex token budget: Codex refuses to run untimed
without one, while Claude Code and Grok Build have no token accounting and an
untimed turn there is bounded by nothing Workshop owns. See ADR 0064.

`--max-rounds` remains legacy metadata for token-budget products, not a stop
condition. Engineering gates and failure-closed accounting remain mandatory.
Input plus output includes cached input without counting reasoning output
twice. `resume` without the
flag retains the saved cap; an explicit value changes the total, not remaining,
allowance and preserves recovered usage. Older eligible runs explicitly adopt
token accounting this way. The local usage adapter requires Codex 0.153.4 or
newer; other adapters retain their existing policies. Live acceptance passed
for Quiet Arc with Spark/Codex/Astra/medium/Soren, same-session recovery, and
verified publication at 6,893,962 observed tokens. Other combinations retain
their deterministic test coverage, not a claim of live acceptance.
Request-completion reporting allows in-flight overshoot and is not an exact
billing cap.

For a marked Codex Spark token-budget product with an explicit saved runtime,
`workshop resume ID --effort medium --max-tokens 500000000` changes its saved
reasoning effort and total token cap. Stop the active CLI before resuming.
The host records the effort correction and preserves the original model,
native session, Wish, workflow, tools, artifacts and consumed tokens. Omitting
`--effort` preserves the current saved setting. Other workflows and older
runtime profiles retain their frozen effort.
