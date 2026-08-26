"""Combined assembly entry for the STEP-first gate regression fixture."""
from build123d import Pos
from cadgen.assembly import AssemblyHelper

from fixture_lib import ASSEMBLY_SLIDER_Z, build_receiver, build_slider


def gen_step():
    assembly = AssemblyHelper("board_game_gate_fixture")
    assembly.add(build_receiver(), "receiver")
    assembly.add(Pos(0, 0, ASSEMBLY_SLIDER_Z) * build_slider(), "slider")
    return assembly.compound()
