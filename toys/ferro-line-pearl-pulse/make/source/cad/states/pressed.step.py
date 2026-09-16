"""Authored pressed still; this is not a motion verification."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemblies.pearl import assembly
PRINTABLE = False

def gen_step():
    return assembly(depression=4.0)
