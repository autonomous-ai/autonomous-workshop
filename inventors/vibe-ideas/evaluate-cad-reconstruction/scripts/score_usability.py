#!/usr/bin/env python3
"""Compatibility CLI for the Layer 1 geometry usability scorer."""
from pathlib import Path
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from cad_reconstruction_eval.usability_score import main


if __name__ == "__main__":
    raise SystemExit(main())
