# CLI

`cli` is the installed command-line adapter for Autonomous Workshop. It parses
commands, calls the public `workshop.workflow` host API, formats results, and
chooses exit codes. Lifecycle, native-session, gate, and effect behavior stays
in the component that owns it.

Run it from a source checkout with `PYTHONPATH=src python -m cli --help`, or use
the installed `workshop` command.

`workshop wish --workflow spark|forge|quest "..."` freezes the selected route;
Spark is the default. `--agent`, `--model`, and `--effort` freeze the native
runtime, model, and reasoning level. Codex defaults to `gpt-5.6-sol` at high;
Claude Code defaults to `claude-opus-5` at high. Status and resume read those
durable choices rather than accepting replacements.

`workshop wish --inventor <id> "..."` pins the exact Inventor in the immutable
Wish and materializes only that Inventor into the run roster. Without the flag,
the complete eligible roster is materialized and the native Manager chooses the
best match. A Wish created by `workshop start <id>` is pinned automatically to
the Inventor who produced its sealed daydream.

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

`workshop start <inventor-id>` is the front door and a loop: it asks one
Inventor to dream one brand-new idea through `workshop.daydream`, prints the
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

`start` and `wish` accept `--max-tokens N` (default `30000000`) for the whole
Codex product, including all build stages, native children and resumes. The
separate Daydream session is excluded. Input plus output is counted, including
cached input but without counting reasoning output twice. `resume` without the
flag retains the saved cap; an explicit value changes the total, not remaining,
allowance and preserves recovered usage. Older eligible runs explicitly adopt
token accounting this way. The local usage adapter currently requires Codex
0.153.4; other adapters retain their existing policies. Live acceptance passed
for Quiet Arc with Spark/Codex/Astra/medium/Soren, same-session recovery, and
verified publication at 6,893,962 observed tokens. Other combinations retain
their deterministic test coverage, not a claim of live acceptance.
Request-completion reporting allows in-flight overshoot and is not an exact
billing cap.
