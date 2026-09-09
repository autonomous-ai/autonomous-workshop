"""Knockseed combined entry: one printable seed tumbler."""

from cadgen.assembly import AssemblyHelper

from knockseed_lib import SEED_COLOR, build_knockseed

PRINTABLE = True


def gen_step():
    seed = build_knockseed()
    asm = AssemblyHelper("knockseed")
    asm.add(seed, "knockseed", color=SEED_COLOR)
    return asm.build()
