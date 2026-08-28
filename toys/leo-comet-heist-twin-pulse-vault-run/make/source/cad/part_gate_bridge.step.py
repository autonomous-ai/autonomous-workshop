from comet_heist_lib import build_bridge, on_bed
def gen_step(): return on_bed(build_bridge(), (0, -90, 0))

