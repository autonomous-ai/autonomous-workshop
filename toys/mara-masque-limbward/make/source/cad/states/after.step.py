"""View-only exact after state from shared piece geometry."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from states import build_scene
PRINTABLE = False
def gen_step():
    return build_scene("after")
