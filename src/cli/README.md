# CLI

`cli` is the installed command-line adapter for Autonomous Workshop. It parses
commands, calls the public `workshop.workflow` host API, formats results, and
chooses exit codes. Lifecycle, native-session, gate, and effect behavior stays
in the component that owns it.

Run it from a source checkout with `PYTHONPATH=src python -m cli --help`, or use
the installed `workshop` command.

`workshop wish --effort spark|forge|quest "..."` freezes the selected route;
Spark is the default. Status and resume read that durable choice rather than
accepting a new effort value.

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
`workshop start <inventor-id> --idea <daydream-id>` builds a saved,
sealed idea. The CLI never edits the idea or predicts its downstream success;
novelty, Taste fit, pre-commit falsification, and exact outcome learning are
the Daydream component's job.
