#!/usr/bin/env python3
"""Golden-block testbench: build every block (defaults + variants), export STL,
run the same mesh checks as the gate. A block enters/keeps library status only
if every case passes. Run: .venv/bin/python blocks/testbench.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cadquery as cq
import cadblocks as cb
from gate import mesh_stats

CASES = {
    "rounded_box": [dict(w=60, d=40, h=30), dict(w=60, d=40, h=30, top_fillet=2.0),
                    dict(w=20, d=20, h=50, corner_r=5.0)],
    "hollow_box": [dict(w=60, d=40, h=30), dict(w=80, d=80, h=60, wall=2.4, corner_r=6.0)],
    "angled_stand": [dict(), dict(w=90, depth=70, height=90)],
    "snap_hook": [dict(), dict(w=20, arm_l=40, hook_depth=10)],
    # cutter is a NEGATIVE volume — verify solidity AND that a real subtraction works
    "phone_slot_cutter": [dict(), dict(angle_deg=35, phone_t=10)],
}

# PROPOSED blocks (blocks/cadblocks.py PROPOSED_BLOCKS) — testbench-verified
# but NOT yet Tam-approved into BLOCKS.md; kept in a separate set so a passing
# testbench never implies library status. See cadblocks.py for provenance.
PROPOSED_CASES = {
    "bounds_box": [dict(x0=0, x1=40, y0=0, y1=25, z0=0, z1=10),
                   dict(x0=-10, x1=10, y0=-5, y1=5, z0=-3, z1=3)],
    "dovetail_tenon": [dict(), dict(throat=8, depth=4, length=30, angle_deg=20)],
    "dovetail_socket_cutter": [dict(), dict(clearance=0.3)],
}


def check(name, solid) -> dict:
    with tempfile.TemporaryDirectory() as td:
        stl = Path(td) / "t.stl"
        cq.exporters.export(solid, str(stl))
        return mesh_stats(stl)


def main() -> int:
    failures = 0
    for name, cases in CASES.items():
        fn = cb.BLOCKS[name]
        for i, kw in enumerate(cases):
            try:
                m = check(name, fn(**kw))
                ok = m["watertight"] and m["bodies"] == 1
                print(f"{'PASS' if ok else 'FAIL'} {name}[{i}] {kw} -> {m}")
                failures += 0 if ok else 1
            except Exception as e:
                print(f"FAIL {name}[{i}] {kw} -> EXC {e}")
                failures += 1

    for name, cases in PROPOSED_CASES.items():
        fn = cb.PROPOSED_BLOCKS[name]
        for i, kw in enumerate(cases):
            try:
                m = check(name, fn(**kw))
                ok = m["watertight"] and m["bodies"] == 1
                print(f"{'PASS' if ok else 'FAIL'} [PROPOSED] {name}[{i}] {kw} -> {m}")
                failures += 0 if ok else 1
            except Exception as e:
                print(f"FAIL [PROPOSED] {name}[{i}] {kw} -> EXC {e}")
                failures += 1

    # PROPOSED composition case: dovetail_tenon + dovetail_socket_cutter must
    # actually mate — the tenon should fit (near-zero clash) inside a host
    # block once the matching socket is cut, and should clash substantially
    # against the SAME host before the socket is cut (proves the cut is doing
    # real work, not a vacuous fit against empty space).
    try:
        import trimesh
        THROAT, DEPTH, LENGTH, ANGLE = 6.0, 6.0, 20.0, 30.0
        # host's bottom face (z=0) is flush with the socket's mouth plane —
        # the mouth must open to a real face or the cut seals an internal
        # void (trimesh then reports it as a second disconnected body).
        host = cb.bounds_box(-15, 15, -15, 15, 0, 10)
        tenon = cb.dovetail_tenon(THROAT, DEPTH, LENGTH, ANGLE)
        socket = cb.dovetail_socket_cutter(THROAT, DEPTH, LENGTH, ANGLE, clearance=0.15)
        host_cut = host.cut(socket)

        def to_trimesh(solid):
            with tempfile.TemporaryDirectory() as td:
                stl = Path(td) / "s.stl"
                cq.exporters.export(solid, str(stl))
                return trimesh.load(str(stl))

        tm_tenon, tm_host, tm_host_cut = to_trimesh(tenon), to_trimesh(host), to_trimesh(host_cut)
        fit_clash = tm_tenon.intersection(tm_host_cut)
        fit_v = 0.0 if fit_clash.is_empty else abs(fit_clash.volume)
        blocked_clash = tm_tenon.intersection(tm_host)
        blocked_v = 0.0 if blocked_clash.is_empty else abs(blocked_clash.volume)
        m = check("dovetail-fit-host", host_cut)
        ok = m["watertight"] and m["bodies"] == 1 and fit_v < 20 and blocked_v > 500
        print(f"{'PASS' if ok else 'FAIL'} [PROPOSED] composition dovetail-fit "
              f"fit_clash={fit_v:.0f}mm3 pre-cut_clash={blocked_v:.0f}mm3 -> {m}")
        failures += 0 if ok else 1
    except Exception as e:
        print(f"FAIL [PROPOSED] composition dovetail-fit -> EXC {e}")
        failures += 1
    # composition case: THE verified phone-stand recipe (2026-08-11, corrected
    # twice by Tam's review — first version had a buried slot, second had a slot
    # detached from the leaning face). Architecture: steep wedge (device leans ON
    # the slope) + base_ext + front lip bar = retention channel. Asserted with a
    # phone mock FIT-CHECK, not just mesh validity — "looks like a stand" must be
    # machine-checked as "a phone physically fits".
    try:
        import math
        import trimesh
        DEPTH, H, BASE_T, W, CHANNEL, LIP_T, CABLE_W = 45, 80, 4, 90, 16, 5, 20
        stand = cb.angled_stand(w=W, depth=DEPTH, height=H, base_t=BASE_T,
                                nose_t=8, base_ext=CHANNEL + LIP_T)
        lip = (cb.rounded_box(LIP_T, W, 12 + BASE_T, corner_r=2.0, top_fillet=1.5,
                              bottom_chamfer=0)
               .translate((DEPTH + CHANNEL + LIP_T / 2, 0, 0)))
        cable_notch = (cq.Workplane("XY")
                       .box(DEPTH * 0.35 + CHANNEL + LIP_T + 4, CABLE_W, 30,
                            centered=(False, True, False))
                       .translate((DEPTH - DEPTH * 0.35, 0, -1)))
        demo = stand.union(lip).cut(cable_notch)
        m = check("phone-stand-recipe", demo)
        with tempfile.TemporaryDirectory() as td:
            stl = Path(td) / "d.stl"
            cq.exporters.export(demo, str(stl))
            tm = trimesh.load(str(stl))
        lean = math.degrees(math.atan((DEPTH - 8) / (H - BASE_T)))
        phone = trimesh.creation.box((8, 70, 150))
        phone.apply_translation((4, 0, 75))
        phone.apply_transform(trimesh.transformations.rotation_matrix(
            math.radians(-lean), (0, 1, 0)))
        phone.apply_translation((DEPTH + 1.5, 0, BASE_T))
        clash = tm.intersection(phone)
        clash_v = 0.0 if clash.is_empty else abs(clash.volume)
        # charge-while-docked: USB plug mock must pass through the cable notch
        plug = trimesh.creation.box((12, 12, 30))
        plug.apply_translation((DEPTH + 6, 0, BASE_T - 25))
        pclash = tm.intersection(plug)
        pclash_v = 0.0 if pclash.is_empty else abs(pclash.volume)
        ok = (m["watertight"] and m["bodies"] == 1
              and clash_v < 100 and pclash_v < 100)
        print(f"{'PASS' if ok else 'FAIL'} composition phone-stand lean={lean:.0f}deg "
              f"phone_clash={clash_v:.0f} plug_clash={pclash_v:.0f}mm3 -> {m}")
        failures += 0 if ok else 1
    except Exception as e:
        print(f"FAIL composition phone-stand -> EXC {e}")
        failures += 1
    print(f"\ntestbench: {'ALL PASS' if failures == 0 else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
