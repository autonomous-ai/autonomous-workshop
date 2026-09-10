"""Input-connected contact is necessary evidence, never a dynamics proof.

The numeric class isolates decision logic. The CAD class repeats the same
counterexamples with actual solids, transforms, and kernel measurements.
"""
from contextlib import redirect_stdout
from dataclasses import dataclass
from copy import deepcopy
from io import StringIO
import math
import json
import sys
import tempfile
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"
CYCLE = (0, 1, 2, 3, 2, 1, 0, -1, -2, -3, -2, -1, 0)


class DriveEvidenceContract:
    def setUp(self):
        self.tool = runpy.run_path(str(CHECK))
        self.globals = self.tool['check_coupled'].__globals__

    def fixture(self, positions, driven, cycle=CYCLE, size=1):
        parts = {name: self.box(x, size) for name, x in positions.items()}
        parts['__toplevel__'] = list(positions)
        parts['__ambiguous__'] = []
        condition = {
            'id': 'contact', 'check': 'coupled_motion_collision', 'expect': 'clear',
            'inputs': {'steps': len(cycle) - 1, 'obstacle_parts': [], 'movers': [
                {'part': name, 'driven': name in driven,
                 'translation': {'offsets_mm': [[x, 0, 0] for x in cycle]}}
                for name in positions]},
            'thresholds': {'maxOverlapMm3': .001, 'maxStepMm': 2.0},
        }
        return parts, condition

    def run_pair(self, parts, condition):
        result = self.tool['run_condition'](condition, parts, 0)
        # These names incorrectly implied a physical conclusion from geometry.
        self.assertNotIn('transmits', result)
        self.assertNotIn('transmitDetail', result)
        return result

    def test_input_paths_and_nominal_contact_are_both_required(self):
        cases = [
            ('disconnected mutual outputs', {'input': 100, 'a': 0, 'b': 2}, {'a', 'b'}, 'fail'),
            ('no input', {'a': 0, 'b': 2}, {'a', 'b'}, 'fail'),
            ('constant gap', {'input': 0, 'a': 2}, {'a'}, 'fail'),
            ('unreachable', {'input': 100, 'a': 0}, {'a'}, 'fail'),
            ('contact', {'input': 0, 'a': 1}, {'a'}, 'pass'),
            ('contact chain', {'input': 0, 'a': 1, 'b': 2}, {'a', 'b'}, 'pass'),
            ('independent inputs', {'input': 0, 'a': 1, 'input2': 20, 'b': 21}, {'a', 'b'}, 'pass'),
            ('isolated contact island', {'input': 0, 'a': 1, 'b': 20, 'c': 21}, {'a', 'b', 'c'}, 'fail'),
            ('no drive claim', {'input': 0, 'a': 2}, set(), 'pass'),
        ]
        for name, positions, driven, status in cases:
            for reverse in (False, True):
                with self.subTest(case=name, reverse=reverse):
                    ordered = dict(reversed(list(positions.items()))) if reverse else positions
                    result = self.run_pair(*self.fixture(ordered, driven))
                    self.assertEqual(result['status'], status, result)
                    # Missing drive evidence must not turn a clear path into a collision.
                    self.assertTrue(result['clear'], result)
                    if driven:
                        self.assertEqual(result['driveContactEvidencePassed'], status == 'pass')
                    else:
                        self.assertNotIn('driveContactEvidencePassed', result)

    def test_repeated_names_aliases_and_overlapping_groups_are_inconclusive(self):
        for case in ('same_name', 'aliases', 'parent_child'):
            for expect in ('clear', 'blocked'):
                for reverse in (False, True):
                    with self.subTest(case=case, expect=expect, reverse=reverse):
                        parts, condition = self.fixture({'shared': 0}, {'shared'}, range(4))
                        first = deepcopy(condition['inputs']['movers'][0])
                        second = deepcopy(first)
                        first['driven'] = False
                        first['translation']['offsets_mm'] = [[i - 1, 0, 0] for i in range(4)]
                        if case != 'same_name':
                            second['part'] = 'root.shared'
                            parts['root.shared'] = parts['shared']
                            parts['__node_keys__'] = {
                                'shared': (0,),
                                'root.shared': (0,) if case == 'aliases' else (0, 0)}
                        movers = [first, second]
                        condition['inputs']['movers'] = list(reversed(movers)) if reverse else movers
                        condition['expect'] = expect
                        result = self.run_pair(parts, condition)
                        self.assertEqual(result['status'], 'inconclusive', result)
                        self.assertIn('once', result['detail'])
                        self.assertNotIn('driveEvidence', result)

    def test_distinct_sibling_nodes_remain_allowed(self):
        parts, condition = self.fixture({'input': 0, 'output': 1}, {'output'})
        parts['__node_keys__'] = {'input': (0, 0), 'output': (0, 1)}
        result = self.run_pair(parts, condition)
        self.assertEqual(result['status'], 'pass', result)

    def test_original_self_check_constant_ten_mm_gap_is_rejected(self):
        # Preserve the exact former positive fixture as a negative regression.
        result = self.run_pair(*self.fixture(
            {'input': 0, 'output': 20}, {'output'},
            cycle=[15 * i / 10 for i in range(11)], size=10))
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(result['clear'])
        self.assertFalse(result['driveContactEvidencePassed'])

    def test_a_static_wall_cannot_supply_drive_evidence(self):
        parts, condition = self.fixture({'input': 100, 'output': 0}, {'output'}, range(13))
        parts['wall'] = self.box(0, 1)
        condition['inputs'].update(obstacle_parts=['wall'], allow_seated_contact=True)
        result = self.run_pair(parts, condition)
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(result['clear'])
        self.assertEqual(result['driveEvidence']['edges'], [])

    def test_missing_drive_cannot_be_recast_as_a_blocked_condition(self):
        parts, condition = self.fixture({'input': 100, 'output': 0}, {'output'})
        condition['expect'] = 'blocked'
        result = self.run_pair(parts, condition)
        self.assertEqual(result['status'], 'fail', result)
        self.assertIn('No input-connected', result['detail'])

    def test_edge_records_both_actual_and_frozen_pose_witnesses(self):
        result = self.run_pair(*self.fixture({'input': 0, 'output': 1}, {'output'}))
        self.assertEqual(result['driveEvidence']['inputParts'], ['input'])
        self.assertEqual(result['driveEvidence']['unreachedDrivenParts'], [])
        edge, = result['driveEvidence']['edges']
        self.assertEqual((edge['from'], edge['to']), ('input', 'output'))
        self.assertEqual(edge['frozenWitness']['step'], 1)
        self.assertAlmostEqual(edge['frozenWitness']['overlapMm3'], 1)
        self.assertAlmostEqual(edge['nominalWitness']['distanceMm'], 0)

    def test_one_contact_does_not_claim_sustained_coupling(self):
        parts, condition = self.fixture({'input': 0, 'output': 1}, {'output'}, range(4))
        condition['inputs']['movers'][1]['translation']['offsets_mm'] = [
            [x, 0, 0] for x in (0, 2, 3, 4)]
        result = self.run_pair(parts, condition)
        # This satisfies only the necessary evidence: later nominal gaps are 1 mm.
        self.assertEqual(result['status'], 'pass', result)
        self.assertIn('not a dynamics or physical transmission proof', result['detail'])

    def test_invalid_distance_cannot_certify_clear_or_blocked(self):
        for value in (float('nan'), float('inf'), -1.0):
            for expect in ('clear', 'blocked'):
                with self.subTest(value=value, expect=expect):
                    parts, condition = self.fixture({'input': 0, 'output': 1}, {'output'})
                    condition['expect'] = expect
                    with patch.dict(self.globals, surface_distance=lambda a, b: value):
                        result = self.run_pair(parts, condition)
                    self.assertEqual(result['status'], 'inconclusive', result)


@dataclass(frozen=True)
class NumericBox:
    center: float
    size: float


class NumericDriveEvidenceTests(DriveEvidenceContract, unittest.TestCase):
    def setUp(self):
        super().setUp()

        def pose_table(spec, steps, field):
            offsets = spec['translation']['offsets_mm']
            self.assertEqual(len(offsets), steps + 1)
            self.assertNotIn('rotation', spec)

            def place(shape, index):
                return NumericBox(shape.center + offsets[index][0], shape.size)

            place.angles = [0.] * (steps + 1)
            place.offsets = offsets
            place.axis_point = (0., 0., 0.)
            place.axis_direction = (0., 0., 1.)
            return place

        def overlap(a, b):
            width = max(0., min(a.center + a.size / 2, b.center + b.size / 2)
                        - max(a.center - a.size / 2, b.center - b.size / 2))
            return width * min(a.size, b.size) ** 2

        self.globals.update(
            overlap_volume=overlap,
            surface_distance=lambda a, b: max(0., abs(a.center - b.center) - (a.size + b.size) / 2),
            resolve_parts=lambda names, parts, field: [
                (name, parts[name]) for name in ([names] if isinstance(names, str) else names)],
            _pose_table=pose_table, _reach=lambda shape, point, direction: 0.)

    @staticmethod
    def box(center, size):
        return NumericBox(center, size)


class CadDriveEvidenceTests(DriveEvidenceContract, unittest.TestCase):
    @staticmethod
    def box(center, size):
        from build123d import Box
        return Box(size, size, size).translate((center, 0, 0))

    def test_real_assembly_aliases_and_group_selections_cannot_duplicate_leaves(self):
        from build123d import Compound
        pin = self.box(0, 1)
        pin.label = 'pin'
        module = Compound(children=[pin], label='module')
        root = Compound(children=[module], label='root')
        parts = self.tool['index_parts'](root)
        for first_name, second_name in (
            ('pin', 'root.module.pin'), ('module', 'pin'),
            ('root.module', 'root.module.pin')):
            with self.subTest(first=first_name, second=second_name):
                _, condition = self.fixture({'pin': 0}, {'pin'}, range(4))
                first = deepcopy(condition['inputs']['movers'][0])
                second = deepcopy(first)
                first.update(part=first_name, driven=False)
                first['translation']['offsets_mm'] = [[i - 1, 0, 0] for i in range(4)]
                second['part'] = second_name
                condition['inputs']['movers'] = [first, second]
                result = self.run_pair(parts, condition)
                self.assertEqual(result['status'], 'inconclusive', result)
                self.assertIn('once', result['detail'])

    def test_real_distinct_assembly_occurrences_remain_allowed(self):
        from build123d import Compound, Location
        prototype = self.box(0, 1)
        first = prototype.moved(Location((0, 0, 0)))
        second = prototype.moved(Location((1, 0, 0)))
        first.label, second.label = 'input', 'output'
        parts = self.tool['index_parts'](Compound(children=[first, second], label='root'))
        _, condition = self.fixture({'input': 0, 'output': 1}, {'output'})
        result = self.run_pair(parts, condition)
        self.assertEqual(result['status'], 'pass', result)

    def test_distance_preserves_ancestor_placements_for_groups_and_leaves(self):
        from build123d import Box, Compound, Location
        pin = self.box(2, 1)
        pin.label = 'pin'
        module = Compound(children=[pin], label='module')
        module.location = Location((10, 0, 0), (0, 0, 90))
        root = Compound(children=[module], label='root')
        root.location = Location((0, 20, 0), (0, 0, 90))
        parts = self.tool['index_parts'](root)
        for alias in ('pin', 'module', 'root.module.pin', 'root.module'):
            for y, expected in ((31, 0), (32, 1)):
                with self.subTest(alias=alias, y=y):
                    other = Box(1, 1, 1).translate((-2, y, 0))
                    self.assertAlmostEqual(self.tool['surface_distance'](parts[alias], other), expected)

    def test_distance_rejects_failed_and_nonfinite_kernel_results(self):
        class Measurement:
            def __init__(self, *args):
                pass

            def Perform(self):
                pass

            def IsDone(self):
                return True

            def NbSolution(self):
                return 1

            def Value(self):
                return 0.

        for name, overrides in [
            ('unfinished', {'IsDone': lambda self: False}),
            ('no solutions', {'NbSolution': lambda self: 0}),
            ('nan', {'Value': lambda self: math.nan}),
            ('infinite', {'Value': lambda self: math.inf}),
            ('negative', {'Value': lambda self: -1.}),
        ]:
            with self.subTest(case=name):
                fake = type('FailedMeasurement', (Measurement,), overrides)
                with patch('OCP.BRepExtrema.BRepExtrema_DistShapeShape', fake):
                    with self.assertRaises(self.tool['ManifestError']):
                        self.tool['surface_distance'](self.box(0, 1), self.box(1, 1))

    def test_distance_rejects_empty_material(self):
        from build123d import Compound
        for empty_first in (True, False):
            with self.subTest(empty_first=empty_first):
                operands = (Compound([]), self.box(0, 1))
                if not empty_first:
                    operands = operands[::-1]
                with self.assertRaisesRegex(ValueError, 'no solid'):
                    self.tool['surface_distance'](*operands)

    def test_cli_distinguishes_contact_evidence_from_a_clear_gap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'assembly.step.py').write_text(
                'from build123d import Box, Compound\n'
                'def gen_step():\n'
                '    driver = Box(10, 10, 10)\n'
                '    driver.label = "input"\n'
                '    output = Box(10, 10, 10).translate((20, 0, 0))\n'
                '    output.label = "output"\n'
                '    return Compound(children=[driver, output], label="root")\n')
            for following in (False, True):
                with self.subTest(following=following):
                    _, condition = self.fixture(
                        {'input': 0, 'output': 20}, {'output'},
                        cycle=[15 * i / 10 for i in range(11)], size=10)
                    if following:
                        condition['inputs']['movers'][1]['translation']['offsets_mm'] = [
                            [max(0, 15 * i / 10 - 10), 0, 0] for i in range(11)]
                    manifest = root / 'motion.json'
                    manifest.write_text(json.dumps({'conditions': [condition]}))
                    output = StringIO()
                    with patch.object(sys, 'argv', [
                            str(CHECK), str(root), '--manifest', str(manifest), '--json',
                            '--allow-inconclusive']), redirect_stdout(output):
                        code = self.tool['main']()
                    result = json.loads(output.getvalue())
                    self.assertEqual(code, 0 if following else 1)
                    self.assertEqual(result['ok'], following)
                    row, = result['results']
                    self.assertTrue(row['clear'])
                    self.assertEqual(row['driveContactEvidencePassed'], following)
                    self.assertEqual(row['status'], 'pass' if following else 'fail')
                    self.assertNotIn('transmits', row)
                    self.assertNotIn('transmitDetail', row)

    def test_builtin_self_check(self):
        output = StringIO()
        with redirect_stdout(output):
            status = self.tool['_self_check']()
        self.assertEqual(status, 0, output.getvalue())
        self.assertIn('constant-gap output fails', output.getvalue())


if __name__ == '__main__':
    unittest.main()
