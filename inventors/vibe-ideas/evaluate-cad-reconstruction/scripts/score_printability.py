#!/usr/bin/env python3
"""CLI wrapper for the evaluate-cad-reconstruction printability scorer."""
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from cad_reconstruction_eval.printability_score import main


if __name__ == "__main__":
    raise SystemExit(main())
