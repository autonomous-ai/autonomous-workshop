import sys, time
sys.path.insert(0,'.'); sys.path.insert(0,'../../../skills/cad/scripts')
import clearance_lib as L
which = sys.argv[1:] or ["column_screw","detent_leaf","golden_stub"]
fns = {"gantry_base":L.build_gantry_base,"column_screw":L.build_column_screw,
 "detent_leaf":L.build_detent_leaf,"post_guide":L.build_post_guide,"yoke":L.build_yoke,
 "stop_ring":L.build_stop_ring,"knob_hood":L.build_knob_hood,"rail":L.build_rail,
 "piece":lambda: L.build_piece(32.75,4),"golden_stub":L.build_golden_stub,"bar":L.build_bar}
for n in which:
    t=time.time()
    try:
        s=fns[n]()
        bb=s.bounding_box()
        print(f"{n:14s} solids={len(s.solids())} vol={s.volume:9.1f} "
              f"x[{bb.min.X:8.2f},{bb.max.X:8.2f}] y[{bb.min.Y:7.2f},{bb.max.Y:7.2f}] z[{bb.min.Z:7.2f},{bb.max.Z:7.2f}] {time.time()-t:.1f}s")
    except Exception as e:
        import traceback; traceback.print_exc(); print(f"{n}: FAILED {e}")
