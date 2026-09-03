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

`workshop daydream <inventor-id>` asks one Inventor to dream one brand-new idea
through `workshop.daydream` and prints the sealed concept card. `--run` seals
that idea as a Wish and starts the same native session `workshop wish` would,
with Forge as its default effort; `--idea <daydream-id> --run` builds a saved
idea. The CLI never judges or edits the idea; novelty and Taste fit are the
Daydream component's job.
