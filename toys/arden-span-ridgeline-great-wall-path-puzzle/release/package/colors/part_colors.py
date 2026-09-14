"""Compatibility entry point: preserve the grid while applying part colors."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parents[1]/'board/revise_board.py'), run_name='__main__')
