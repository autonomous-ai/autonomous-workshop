from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "cad"))
from moon_lib import inlay_datum, named
def gen_step():
    return named(inlay_datum(),'inlay',(0.92,0.94,0.87))
