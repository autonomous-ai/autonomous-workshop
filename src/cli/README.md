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
Judge-accepted idea. The
CLI never judges or edits the idea; novelty and Taste fit are the Daydream
component's job.
