"""Motion progress survives timeouts without becoming gate evidence."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from build123d import Box

from tests.make.test_make_round import load_module


CHECK = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts/check_motion'


class MotionProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def setUp(self):
        environment = patch.dict(os.environ, {'WORKSHOP_PROGRESS': '1',
                                               'WORKSHOP_PROGRESS_INTERVAL': '0'})
        environment.start()
        self.addCleanup(environment.stop)

    def condition(self, identifier='escape'):
        return {'id': identifier, 'check': 'linear_motion_collision',
                'inputs': {'moving_part': 'moving', 'obstacle_parts': ['fixed'],
                           'translation': [0, 0, 4], 'steps': 4}}

    def parts(self):
        return {'moving': Box(2, 2, 2), 'fixed': Box(2, 2, 2).translate((20, 0, 0))}

    def test_progress_keeps_exact_results_and_can_be_silenced(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), patch.dict(os.environ, {'WORKSHOP_PROGRESS': '0'}):
            expected = self.tool['run_condition'](self.condition(), self.parts(), 0)
        self.assertEqual(stderr.getvalue(), '')
        with redirect_stderr(stderr):
            actual = self.tool['run_condition'](self.condition(), self.parts(), 0)
        self.assertEqual(actual, expected)
        self.assertIn('[escape] sweep: 5/5 (100%)', stderr.getvalue())

    def test_failed_condition_reports_completion_without_promoting_evidence(self):
        condition = self.condition()
        condition['inputs']['translation'] = None
        expected = self.tool['run_condition'](condition, self.parts(), 0)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = self.tool['run_condition'](condition, self.parts(), 0)
        self.assertEqual(result, expected)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertNotIn('clear', result)
        self.assertNotIn('100%', stderr.getvalue())

    def test_coupled_sweep_and_drive_phases_are_identified_without_changing_results(self):
        condition = {'id': 'contact-cycle', 'check': 'coupled_motion_collision',
                     'inputs': {'steps': 3, 'obstacle_parts': [], 'movers': [
                         {'part': 'driver', 'translation': {'vector': [3, 0, 0]}},
                         {'part': 'follower', 'driven': True,
                          'translation': {'vector': [3, 0, 0]}}]}}
        parts = {'driver': Box(2, 2, 2), 'follower': Box(2, 2, 2).translate((2, 0, 0))}
        expected = self.tool['run_condition'](condition, parts, 0)
        self.assertEqual(expected['status'], 'pass', expected)
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            result = self.tool['run_condition'](condition, parts, 0)
        self.assertEqual(result, expected)
        self.assertIn('[contact-cycle] coupled sweep:', stderr.getvalue())
        self.assertIn('[contact-cycle] drive evidence:', stderr.getvalue())

    def test_nested_condition_diagnostics_restore_parent(self):
        condition = {'id': 'sequence', 'check': 'assembly_sequence',
                     'inputs': {'steps': [self.condition('child')]}}
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            with self.tool['progresslib'].scope('outer'):
                result = self.tool['run_condition'](condition, self.parts(), 0)
                self.tool['progresslib'].write('after')
            self.tool['progresslib'].write('unscoped')
        self.assertEqual(result['status'], 'pass')
        self.assertIn('[child] sweep:', stderr.getvalue())
        self.assertEqual(stderr.getvalue().splitlines()[-2:], ['[outer] after', 'unscoped'])

    def test_samples_are_throttled_but_completion_is_always_reported(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.tool['progresslib'].scope('long-sweep'), \
                patch.object(self.tool['progresslib'].time, 'monotonic', return_value=0) as clock:
            reporter = self.tool['progresslib'].Progress('sweep', 1000, interval=30)
            for second in (0, 1, 29, 30, 31, 60):
                clock.return_value = second
                reporter.advance()
            reporter.finish()
        lines = stderr.getvalue().splitlines()
        self.assertEqual(len(lines), 5)
        for line, count in zip(lines[1:4], (1, 4, 6)):
            self.assertIn(f'sweep: {count}/1000', line)
        self.assertIn('sweep: 6 done in', lines[-1])

    def test_json_cli_keeps_evidence_on_stdout_and_progress_on_stderr(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / 'assembly.step.py').write_text(
                'from build123d import Box, Compound\n'
                'def gen_step():\n'
                '    moving = Box(2, 2, 2)\n'
                '    fixed = Box(2, 2, 2).translate((20, 0, 0))\n'
                '    moving.label, fixed.label = "moving", "fixed"\n'
                '    return Compound(children=[moving, fixed], label="assembly")\n')
            manifest = project / 'motion.json'
            manifest.write_text(json.dumps({'conditions': [self.condition()]}))
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(sys, 'argv', [str(CHECK), str(project), '--manifest', str(manifest), '--json']), \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                status = self.tool['main']()
            self.assertEqual(status, 0, stderr.getvalue())
            payload = json.loads(stdout.getvalue())
            self.assertEqual(set(payload), {'ok', 'project', 'assembly', 'results', 'deadlineSeconds'})
            self.assertEqual(payload['results'], [self.tool['run_condition'](self.condition(), self.parts(), 0)])
            self.assertTrue(payload['ok'])
            self.assertIn('building assembly.step.py', stderr.getvalue())
            self.assertIn('[escape] sweep: 5/5 (100%)', stderr.getvalue())

    def test_real_runner_timeout_retains_flushed_condition_and_sample_progress(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'slow_condition.py'
            script.write_text(
                'import runpy, time\n'
                f'tool = runpy.run_path({str(CHECK.with_name("progresslib.py"))!r})\n'
                'with tool["scope"]("aircraft-separates"):\n'
                '    reporter = tool["Progress"]("sweep", 1060)\n'
                '    reporter.advance()\n'
                '    time.sleep(10)\n')
            log = root / 'motion.log'
            done = module.run([sys.executable, str(script)], cwd=root, log=log, timeout=2)
            self.assertEqual(done.returncode, 124)
            text = log.read_text()
            self.assertIn('TIMEOUT after 2s', text)
            self.assertIn('[aircraft-separates] sweep: 1/1060', text)
            self.assertNotIn('done in', text)
            result = module.parse_motion(done.stdout, done.returncode, done.stderr)
            self.assertEqual(result['verdict'], 'fail')
            self.assertEqual(result['returncode'], 124)
            self.assertEqual(result['conditions'], [])


if __name__ == '__main__':
    unittest.main()
