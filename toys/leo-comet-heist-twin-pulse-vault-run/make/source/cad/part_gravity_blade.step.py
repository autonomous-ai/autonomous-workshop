from comet_heist_lib import build_blade, on_bed
def gen_step(): return on_bed(build_blade(), (0, 90, 0))
