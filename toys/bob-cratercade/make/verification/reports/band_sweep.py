"""Finite current-source band audit; not elastic dynamics or a Workshop gate.

Run with CADGEN_WARM=0 and the materialized CAD scripts on PYTHONPATH.
Only per-case JSON and this audit's summary are written; no CAD is exported.
Existing cases are reused only when their exact evidence fingerprint matches.
"""
import argparse
import hashlib
import json
import math
import runpy
from pathlib import Path
import sys
import time

CAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CAD))
from build123d import Axis, Plane, Pos
from OCP.BOPAlgo import BOPAlgo_ArgumentAnalyzer
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
import params as p
from assemblies.flippers import components as flipper_components
from assemblies.launcher import components as launcher_components
from assemblies.hardware import hardware_parts
from parts.rubber_band import band
from parts.apron_shell import build as apron

SOURCE_FILES = [
    'parts/rubber_band.py', 'assemblies/bands.py', 'assemblies/flippers.py',
    'assemblies/launcher.py', 'assemblies/hardware.py', 'parts/flipper.py',
    'parts/flipper_guard.py', 'parts/flipper_guard_base.py',
    'parts/flipper_pedestal.py', 'parts/flipper_sleeve.py',
    'parts/launcher_housing.py', 'parts/launcher_rod.py',
    'parts/launcher_guide_cap.py', 'parts/launcher_band_guard.py',
    'parts/launcher_anchor.py', 'parts/purchased_hardware.py',
    'parts/apron_shell.py', 'features/primitives.py',
    'ref/countersunk_socket_screw_m4_l0016_simple.step',
    'ref/iso4762_socket_head_cap_screw_m4x25.step',
    'ref/thin_jam_nut_m4_simple.step',
]


def sha(value):
    return hashlib.sha256(value).hexdigest()


def fingerprint(step_deg, step_mm, fresh=False):
    # The end probe executes current parameter source, avoiding a stale imported
    # module when another authorized worker edits unrelated model parameters.
    resolved = runpy.run_path(str(CAD/'params.py')) if fresh else vars(p)
    values = {k: v for k, v in resolved.items()
              if k.startswith(('FLIPPER_', 'LAUNCH_', 'LAUNCHER_', 'BAND_',
                               'M4_', 'NUT_', 'CSK_', 'SOCKET_', 'APRON_',
                               'CANOPY_', 'CUP_DRAIN_'))
              or k in ('DECK_T', 'LAYER')}
    data = {'source_sha256': {f: sha((CAD/f).read_bytes()) for f in SOURCE_FILES},
            'audit_sha256': sha(Path(__file__).read_bytes()),
            'relevant_parameter_values': values,
            'flipper_step_deg': step_deg, 'launcher_step_mm': step_mm,
            'max_overlap_mm3': 0.001}
    raw = json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
    return sha(raw), data


def write_json(path, value):
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def bounds(shape):
    b = shape.bounding_box()
    return [list(b.min), list(b.max)]


def raw_bounds(shape):
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape, b)
    value = b.Get()
    return [list(value[:3]), list(value[3:])]


def box_gap(a, b):
    return math.sqrt(sum(max(0., a[0][i]-b[1][i], b[0][i]-a[1][i])**2
                         for i in range(3)))


def self_interference(shape):
    analyzer = BOPAlgo_ArgumentAnalyzer()
    analyzer.SetShape1(shape.wrapped)
    analyzer.SelfInterMode = True
    analyzer.Perform()
    findings = analyzer.GetCheckResult()
    witnesses = []
    for result in findings:
        if len(witnesses) >= 8:
            break
        witnesses.append({'status': str(result.GetCheckStatus()),
                          'shape1_bounds': [raw_bounds(s) for s in result.GetFaultyShapes1()],
                          'shape2_bounds': [raw_bounds(s) for s in result.GetFaultyShapes2()]})
    return {'execution_errors': bool(analyzer.HasErrors()),
            'has_faulty': bool(analyzer.HasFaulty()),
            'finding_count': findings.Extent(), 'witnesses': witnesses}


def pair_measure(shape, obstacle, a, b, exact_distance=False):
    lower = box_gap(a, b)
    if lower > 2 and not exact_distance:
        return {'bbox_distance_lower_bound_mm': lower, 'overlap_mm3': 0.,
                'basis': 'disjoint exact BRep bounding boxes'}
    common = shape.intersect(obstacle)
    material = [] if common is None else list(common.solids())
    if any(not s.is_valid for s in material):
        raise ValueError('Invalid intersection solid; clearance inconclusive')
    volume = sum(s.volume for s in material)
    if not math.isfinite(volume) or volume < -1e-8:
        raise ValueError('Nonfinite/negative Boolean volume; clearance inconclusive')
    dist = BRepExtrema_DistShapeShape(shape.wrapped, obstacle.wrapped)
    dist.Perform()
    if not dist.IsDone() or not math.isfinite(dist.Value()):
        raise ValueError('Minimum-distance query failed; clearance inconclusive')
    result = {'overlap_mm3': max(0., volume), 'distance_mm': dist.Value(),
              'basis': 'current-source BRep intersection and minimum distance'}
    if dist.NbSolution():
        result['nearest_band_point'] = list(dist.PointOnShape1(1).Coord())
        result['nearest_obstacle_point'] = list(dist.PointOnShape2(1).Coord())
    if material and volume > 0.001:
        result['overlap_bounds'] = [bounds(s) for s in material]
    return result


def fixed_controls():
    result = {name: shape for name, shape, *_ in
            flipper_components()+launcher_components()+hardware_parts()
            if name.startswith(('flipper_', 'launcher_'))}
    result.update({f'apron_{side}': apron(side) for side in ('left', 'right')})
    return result


def case_geometry(family, value, anchor, fixed):
    """Use the production constructor and production placement parameters.

    This repeats only the argument/placement mapping of assemblies/bands.py,
    avoiding construction of two irrelevant bands for every sampled state.
    The exact production constructor and mapping source hashes are recorded.
    """
    obstacles = dict(fixed)
    if family in ('left', 'right'):
        angle = math.radians(value)
        x, y = p.FLIPPER_TAIL_JOINT
        moving = (x*math.cos(angle)-y*math.sin(angle),
                  x*math.sin(angle)+y*math.cos(angle))
        shape = band(p.FLIPPER_FIXED_ANCHORS[family][0], moving,
                     p.FLIPPER_BAND_RADII[family], p.BAND_T, p.BAND_WIDTH,
                     p.FLIPPER_BAND_CENTER_Z, p.FLIPPER_BAND_TURNS[family],
                     p.FLIPPER_BAND_RADIAL_WOBBLE[family],
                     p.FLIPPER_BAND_AXIAL_WOBBLE[family], p.BAND_SAMPLES_PER_LAP)
        if family == 'right':
            shape = shape.mirror(Plane.YZ)
        pivot = p.FLIPPER_PIVOTS[family]
        shape = Pos(*pivot, 0)*shape
        rotor = f'flipper_{family}_rotor'
        direction = 1 if family == 'left' else -1
        obstacles[rotor] = fixed[rotor].rotate(Axis((*pivot, 0), (0, 0, 1)), direction*value)
    else:
        y = p.LAUNCH_ANCHOR_Y[anchor]
        shift = y-p.LAUNCH_ANCHOR_Y[0]
        shape = band((p.LAUNCH_BAND_X, y),
                     (p.LAUNCH_BAND_X, p.LAUNCH_MOVING_POST_Y-value),
                     p.LAUNCHER_BAND_RADIUS, p.BAND_T, p.BAND_WIDTH,
                     p.LAUNCH_BAND_Z, 1, 0, 0, p.BAND_SAMPLES_PER_LAP)
        obstacles['launcher_rod'] = Pos(0, -value, 0)*fixed['launcher_rod']
        for key in ('launcher_anchor', 'launcher_root_2_bolt', 'launcher_root_2_nut'):
            obstacles[key] = Pos(0, shift, 0)*fixed[key]
    return shape, obstacles


def cases(family, step_deg, step_mm):
    for side in ('left', 'right'):
        if family not in ('all', 'flippers', side):
            continue
        count = math.ceil(p.FLIPPER_TRAVEL/step_deg)
        for i in range(count+1):
            yield f'{side}-{i:03d}', side, p.FLIPPER_TRAVEL*i/count, 0
    if family in ('all', 'launcher'):
        count = math.ceil(p.LAUNCH_TRAVEL/step_mm)
        for anchor in range(len(p.LAUNCH_ANCHOR_Y)):
            for i in range(count+1):
                yield f'launcher-{anchor}-{i:03d}', 'launcher', p.LAUNCH_TRAVEL*i/count, anchor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', choices=['all', 'flippers', 'left', 'right', 'launcher'], default='all')
    parser.add_argument('--flipper-step-deg', type=float, default=1.)
    parser.add_argument('--launcher-step-mm', type=float, default=.5)
    parser.add_argument('--output', type=Path, default=CAD.parents[1]/'design/band-sweep')
    args = parser.parse_args()
    if min(args.flipper_step_deg, args.launcher_step_mm) <= 0:
        parser.error('Sample steps must be positive')
    args.output.mkdir(parents=True, exist_ok=True)
    key, provenance = fingerprint(args.flipper_step_deg, args.launcher_step_mm)
    fixed = fixed_controls()
    write_json(args.output/'fixed-obstacles.json', {
        name: {'valid': bool(shape.is_valid), 'solids': len(shape.solids()),
               'volume_mm3': shape.volume, 'bounds': bounds(shape)}
        for name, shape in fixed.items()})
    todo = list(cases(args.family, args.flipper_step_deg, args.launcher_step_mm))
    rows = []
    write_json(args.output/'provenance.json', dict(fingerprint=key, **provenance))
    for case_id, family, value, anchor in todo:
        target = args.output/(case_id+'.json')
        prior = json.loads(target.read_text()) if target.exists() else {}
        if prior.get('fingerprint') == key and prior.get('complete'):
            rows.append(prior)
            print(json.dumps({'case': case_id, 'reused': True, 'passed': prior['passed']}), flush=True)
            continue
        started = time.monotonic()
        row = {'case': case_id, 'fingerprint': key, 'family': family,
               'angle_deg': value if family != 'launcher' else None,
               'pull_mm': value if family == 'launcher' else None,
               'anchor_index': anchor if family == 'launcher' else None,
               'coordinate_frame': 'board local, before 6 degree incline and Z42 stance'}
        write_json(args.output/'pending.json', row)
        try:
            shape, obstacles = case_geometry(family, value, anchor, fixed)
            row.update(valid=bool(shape.is_valid), solids=len(shape.solids()),
                       volume_mm3=shape.volume, bounds=bounds(shape))
            row['self_interference'] = self_interference(shape)
            # Exact gaps to this family's apron, post-carrying base, roof and
            # rotor are always measured, even when bbox separation exceeds2mm.
            exact_names = {f'apron_{family}', f'flipper_{family}_guard_base',
                           f'flipper_{family}_guard', f'flipper_{family}_rotor'}
            row['pairs'] = {name: pair_measure(shape, other, row['bounds'], bounds(other), name in exact_names)
                            for name, other in obstacles.items()}
            row['collisions'] = [name for name, result in row['pairs'].items()
                                 if result['overlap_mm3'] > .001]
            distances = [(r['distance_mm'], name) for name, r in row['pairs'].items()
                         if 'distance_mm' in r]
            row['nearest'] = sorted(distances)[:5]
            si = row['self_interference']
            row['passed'] = (row['valid'] and row['solids'] == 1 and
                             row['volume_mm3'] > 0 and not si['execution_errors'] and
                             not si['has_faulty'] and not row['collisions'])
        except Exception as error:
            row.update(passed=False, inconclusive=True,
                       error=f'{type(error).__name__}: {error}')
        row.update(complete=True, elapsed_seconds=time.monotonic()-started)
        write_json(target, row)
        rows.append(row)
        print(json.dumps({k: row.get(k) for k in ['case', 'passed', 'collisions',
                                                 'error', 'elapsed_seconds']}), flush=True)
    end_key, end_provenance = fingerprint(args.flipper_step_deg, args.launcher_step_mm, fresh=True)
    write_json(args.output/'fresh-source-probe.json', dict(fingerprint=end_key, **end_provenance))
    summary = {'fingerprint': key, 'sources_stable': key == end_key,
               'planned_cases': len(todo), 'completed_cases': len(rows),
               'failed_cases': [r['case'] for r in rows if not r['passed']],
               'passed': key == end_key and all(r['passed'] for r in rows),
               'scope': 'Finite source-deformed nominal geometry only; no physical force, mass conservation, fatigue, elastic dynamics or continuous-between-samples guarantee.',
               'not_included': ['other deforming bands', 'complete-product walls/canopy except the two apron roofs',
                                'static or moving marble contact'],
               'flipper_post_max_step_mm': 2*math.hypot(*p.FLIPPER_TAIL_JOINT)*math.sin(math.radians(args.flipper_step_deg)/2),
               'launcher_post_step_mm': args.launcher_step_mm}
    write_json(args.output/f'summary-{args.family}.json', summary)
    print(json.dumps(summary), flush=True)
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
