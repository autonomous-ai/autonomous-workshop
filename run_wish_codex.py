#!/usr/bin/env python3
"""Codex runner: Astra medium, Spark; delegates execution to run_wish.py.

python run_wish_codex.py --wish 'make a beherit from berserk' --yes
python run_wish_codex.py --resume <wish-id> --yes
python run_wish_codex.py --dry-run

--workflow selects Spark/Forge/Quest; --effort selects model reasoning.
Resume uses the host's frozen model and effort, regardless of CONFIG.
"""
import sys
import run_wish

CONFIG = {
    "wish": "a minecraft sword",
    "agent": "codex",
    "model": "gpt-6-astra",
    "workflow": "spark",
    "effort": "medium",
    "max_tokens": None,
}


def main() -> int:
    if CONFIG["agent"] != "codex":
        print("Dùng run_wish.py cho runtime khác Codex.", file=sys.stderr)
        return 2
    run_wish.CONFIG = CONFIG
    return run_wish.main()


if __name__ == "__main__":
    sys.exit(main())
