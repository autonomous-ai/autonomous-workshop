"""Motion proofs require completed, finite, mutually consistent measurements."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch, PropertyMock

from build123d import Box, Compound, Shell, Solid
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid
from OCP.TopoDS import TopoDS_Shape
import OCP.BRepAlgoAPI as operations

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class FakeOperation:
    done = True
    result = None
    error = None

    def SetNonDestructive(self, value):
        self.non_destructive = value

    def SetArguments(self, value):
        self.arguments = value

    def SetTools(self, value):
        self.tools = value

    def Build(self):
        if self.error:
            raise self.error

    def IsDone(self):
        return self.done

    def Shape(self):
        return self.result


class MotionBooleanMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def condition(self, expect='clear'):
        return {'id': 'occupancy', 'check': 'linear_motion_collision', 'expect': expect,
                'inputs': {'moving_part': 'moving', 'obstacle_parts': ['fixed'],
                           'translation': [0, 0, 0], 'steps': 1}}

    def run_pair(self, expect='clear', moving=None, fixed=None):
        return self.tool['run_condition'](
            self.condition(expect),
            {'moving': Box(2, 2, 2) if moving is None else moving,
             'fixed': Box(2, 2, 2) if fixed is None else fixed}, 0)

    def test_actual_intersection_is_still_measured(self):
        actual = self.tool['overlap_volume'](Box(2, 2, 2), Box(2, 2, 2).translate((1, 0, 0)))
        self.assertAlmostEqual(actual, 4)

    def test_touching_and_disjoint_solids_are_clear(self):
        for offset in (2, 20):
            with self.subTest(offset=offset):
                result = self.run_pair(fixed=Box(2, 2, 2).translate((offset, 0, 0)))
                self.assertEqual(result['status'], 'pass', result)

    def test_kernel_failures_cannot_prove_clear_or_blocked(self):
        open_shell = Shell(list(Box(2, 2, 2).faces())[:-1])
        open_solid = Solid(BRepBuilderAPI_MakeSolid(open_shell.wrapped).Solid())
        self.assertFalse(open_solid.is_valid)
        cases = {
            'invalid': {'result': open_solid.wrapped},
            'exception': {'error': RuntimeError('injected Boolean failure')},
            'unfinished': {'done': False},
            'null': {'result': TopoDS_Shape()},
        }
        for name, attributes in cases.items():
            operation = type('BrokenOperation', (FakeOperation,), attributes)
            for expect in ('clear', 'blocked'):
                with self.subTest(case=name, expect=expect):
                    with patch.object(operations, 'BRepAlgoAPI_Common', operation):
                        result = self.run_pair(expect)
                    self.assertEqual(result['status'], 'inconclusive', result)
                    self.assertNotIn('clear', result)

    def test_reported_empty_common_must_agree_with_union(self):
        empty = type('EmptyCommon', (FakeOperation,), {'result': Compound([]).wrapped})
        # Duplicate two 8 mm3 solids: their union still occupies 8 mm3.
        union = type('Union', (FakeOperation,), {'result': Box(2, 2, 2).wrapped})
        for expect in ('clear', 'blocked'):
            with self.subTest(expect=expect):
                with patch.object(operations, 'BRepAlgoAPI_Common', empty), patch.object(operations, 'BRepAlgoAPI_Fuse', union):
                    result = self.run_pair(expect)
                self.assertEqual(result['status'], 'inconclusive', result)
                self.assertIn('inconsistent', result['detail'])

    def test_failed_union_and_differences_do_not_certify_a_positive_common(self):
        # A failed union alone no longer decides: both differences may confirm the
        # intersection instead. When they are unavailable too, nothing certifies it.
        unfinished = type('UnfinishedUnion', (FakeOperation,), {'done': False})
        for expect in ('clear', 'blocked'):
            with self.subTest(expect=expect):
                with patch.object(operations, 'BRepAlgoAPI_Fuse', unfinished), \
                        patch.object(operations, 'BRepAlgoAPI_Cut', unfinished):
                    result = self.run_pair(expect)
                self.assertEqual(result['status'], 'inconclusive', result)

    def test_nonfinite_and_negative_result_volumes_are_inconclusive(self):
        for value in (float('nan'), float('inf'), -1.0):
            for expect in ('clear', 'blocked'):
                with self.subTest(value=value, expect=expect):
                    with patch.object(Solid, 'volume', new_callable=PropertyMock,
                                      side_effect=[8.0, 8.0, value]):
                        result = self.run_pair(expect)
                    self.assertEqual(result['status'], 'inconclusive', result)
                    self.assertNotIn('overlapMm3', result)

    def test_empty_operand_is_not_a_clearance_or_retention_proof(self):
        for expect in ('clear', 'blocked'):
            with self.subTest(expect=expect):
                result = self.run_pair(expect, moving=Compound([]))
                self.assertEqual(result['status'], 'inconclusive', result)
                self.assertIn('no solid', result['detail'])

    def test_measurement_failure_propagates_through_sequence(self):
        operation = type('UnfinishedCommon', (FakeOperation,), {'done': False})
        sequence = {'id': 'assembly', 'check': 'assembly_sequence',
                    'inputs': {'steps': [self.condition('clear')]}}
        with patch.object(operations, 'BRepAlgoAPI_Common', operation):
            result = self.tool['run_condition'](sequence, {'moving': Box(2, 2, 2), 'fixed': Box(2, 2, 2)}, 0)
        self.assertEqual(result['status'], 'inconclusive', result)
        self.assertEqual(result['stepResults'][0]['status'], 'inconclusive', result)

    def test_group_overlap_counts_occupied_material_once(self):
        # The threshold lies between true material volume and a duplicate sum.
        for offset, actual, threshold in [(0, 8, 10), (1, 12, 14), (2, 16, 18), (3, 16, 18)]:
            for as_obstacle in (False, True):
                with self.subTest(offset=offset, as_obstacle=as_obstacle):
                    group = Compound(children=[Box(2, 2, 2), Box(2, 2, 2).translate((offset, 0, 0))])
                    outer = Box(12, 12, 12)
                    a, b = (outer, group) if as_obstacle else (group, outer)
                    self.assertAlmostEqual(self.tool['overlap_volume'](a, b), actual)
                    for expect, status in [('clear', 'pass'), ('blocked', 'fail')]:
                        condition = self.condition(expect)
                        condition['thresholds'] = {'maxOverlapMm3': threshold}
                        result = self.tool['run_condition'](condition, {'moving': a, 'fixed': b}, 0)
                        self.assertEqual(result['status'], status, result)

    def test_group_union_failure_is_inconclusive(self):
        operation = type('UnfinishedGroupUnion', (FakeOperation,), {'done': False})
        for expect in ('clear', 'blocked'):
            with self.subTest(expect=expect):
                group = Compound(children=[Box(2, 2, 2), Box(2, 2, 2)])
                with patch.object(operations, 'BRepAlgoAPI_Fuse', operation):
                    result = self.run_pair(expect, moving=group)
                self.assertEqual(result['status'], 'inconclusive', result)

    def test_group_union_does_not_change_input_instances(self):
        a, b = Box(2, 2, 2), Box(2, 2, 2).translate((1, 0, 0))
        group = Compound(children=[a, b])
        before = [(tuple(s.position), s.volume) for s in group.children]
        self.tool['overlap_volume'](group, Box(12, 12, 12))
        after = [(tuple(s.position), s.volume) for s in group.children]
        self.assertEqual(before, after)

    def test_default_cli_exits_nonzero_with_serializable_inconclusive_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'assembly.step.py').write_text(
                'from build123d import Box, Compound\n'
                'def gen_step():\n'
                '    a, b = Box(2, 2, 2), Box(2, 2, 2)\n'
                '    a.label, b.label = "moving", "fixed"\n'
                '    return Compound(children=[a, b], label="assembly")\n')
            manifest = project / 'motion.json'
            manifest.write_text(json.dumps({'conditions': [self.condition()]}))
            operation = type('NullCommon', (FakeOperation,), {'result': TopoDS_Shape()})
            output = io.StringIO()
            with patch.object(sys, 'argv', [str(CHECK), str(project), '--manifest', str(manifest), '--json']), patch.object(operations, 'BRepAlgoAPI_Common', operation), contextlib.redirect_stdout(output):
                status = self.tool['main']()
            self.assertEqual(status, 1, output.getvalue())
            payload = json.loads(output.getvalue())
            self.assertFalse(payload['ok'])
            self.assertEqual(payload['results'][0]['status'], 'inconclusive')


if __name__ == '__main__':
    unittest.main()
