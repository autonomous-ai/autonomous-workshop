import sys, time
sys.path.insert(0,'.'); sys.path.insert(0,'../../../skills/cad/scripts')
import clearance_lib as L
NAMES = ["gantry_base","screw_shroud","column_screw","detent_leaf","post_guide",
         "yoke","stop_ring","knob_hood","rail","golden_stub"]
which = sys.argv[1:] or NAMES
fns = {n: getattr(L, f"print_{n}") for n in NAMES}
fns["piece"] = lambda: L.print_piece("piece_a1")
fns["bar"] = L.build_bar
for n in which:
    t=time.time()
    try:
        s=fns[n]()
        bb=s.bounding_box()
        print(f"{n:14s} solids={len(s.solids())} vol={s.volume:9.1f} "
              f"x[{bb.min.X:8.2f},{bb.max.X:8.2f}] y[{bb.min.Y:7.2f},{bb.max.Y:7.2f}] z[{bb.min.Z:7.2f},{bb.max.Z:7.2f}] {time.time()-t:.1f}s")
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"{n}: FAILED {e}")
