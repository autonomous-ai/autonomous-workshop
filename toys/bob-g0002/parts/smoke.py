"""Build every part builder once and print solids / volume / bounding box.

    $BOB_CAD_PY smoke.py                 # all of them
    $BOB_CAD_PY smoke.py lever latch     # just these
"""
import sys, time, traceback

sys.path.insert(0, '.')
sys.path.insert(0, '../../../skills/cad/scripts')
import repin_lib as L

ALL = ["plug", "shell", "cap", "hood", "latch", "lever", "slug", "key",
       "case", "lid", "tray", "board", "peg", "gp1_plug", "gp1_shell"] \
    + [f"pin{r}" for r in range(1, L.RUNGS + 1)]


def build(n):
    if n.startswith("pin") and n[3:].isdigit():
        return L.bed(L.build_pin(int(n[3:])))
    return getattr(L, f"print_{n}")()


names = sys.argv[1:] or ALL
bad = 0
for n in names:
    t = time.time()
    try:
        s = build(n)
        bb = s.bounding_box()
        print(f"{n:10s} solids={len(s.solids()):2d} vol={s.volume:10.1f} "
              f"env={bb.max.X - bb.min.X:6.2f} x{bb.max.Y - bb.min.Y:6.2f} "
              f"x{bb.max.Z - bb.min.Z:6.2f}  z0={bb.min.Z:6.2f}  {time.time() - t:5.1f}s",
              flush=True)
    except Exception as e:
        bad += 1
        traceback.print_exc()
        print(f"{n}: FAILED {e}", flush=True)
sys.exit(1 if bad else 0)
