"""Motion progress survives timeouts without becoming gate evidence."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

from build123d import Box

from tests.make.test_make_round import load_module


CHECK = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts/check_motion'
PREFIX = 'check_motion progress: '


class MotionProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(CHECK))

    def records(self, output):
        return [json.loads(line[len(PREFIX):]) for line in output.splitlines()
                if line.startswith(PREFIX)]

    def condition(self, identifier='escape'):
        return {'id': identifier, 'check': 'linear_motion_collision',
                'inputs': {'moving_part': 'moving', 'obstacle_parts': ['fixed'],
                           'translation': [0, 0, 4], 'steps': 4}}

    def parts(self):
        return {'moving': Box(2, 2, 2), 'fixed': Box(2, 2, 2).translate((20, 0, 0))}

    def test_progress_keeps_exact_results_and_is_silent_without_scope(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            expected = self.tool['run_condition'](self.condition(), self.parts(), 0)
        self.assertEqual(stderr.getvalue(), '')
        with redirect_stderr(stderr), self.tool['progress_scope']('checks', enabled=True):
            actual = self.tool['run_condition'](self.condition(), self.parts(), 0)
        self.assertEqual(actual, expected)
        self.assertEqual(self.records(stderr.getvalue()), [
            {'condition': 'escape', 'phase': 'start'},
            {'condition': 'escape', 'phase': 'sweep', 'step': 0, 'steps': 4},
            {'condition': 'escape', 'phase': 'complete', 'status': 'pass'},
        ])

    def test_failed_condition_reports_completion_without_promoting_evidence(self):
        condition = self.condition()
        condition['inputs']['translation'] = None
        expected = self.tool['run_condition'](condition, self.parts(), 0)
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.tool['progress_scope']('checks', enabled=True):
            result = self.tool['run_condition'](condition, self.parts(), 0)
        self.assertEqual(result, expected)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertNotIn('clear', result)
        self.assertEqual(self.records(stderr.getvalue())[-1],
                         {'condition': 'escape', 'phase': 'complete', 'status': 'inconclusive'})

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
        with redirect_stderr(stderr), self.tool['progress_scope']('checks', enabled=True):
            result = self.tool['run_condition'](condition, parts, 0)
        self.assertEqual(result, expected)
        phases = [record['phase'] for record in self.records(stderr.getvalue())]
        self.assertEqual(phases, ['start', 'coupled-sweep', 'drive-frozen', 'drive-contact', 'complete'])

    def test_nested_condition_diagnostics_restore_parent_and_escape_names(self):
        condition = {'id': 'sequence', 'check': 'assembly_sequence',
                     'inputs': {'steps': [self.condition('child\nwith newline')]}}
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            with self.tool['progress_scope']('outer', enabled=True):
                result = self.tool['run_condition'](condition, self.parts(), 0)
                self.tool['report_progress']('after')
            self.tool['report_progress']('must-stay-silent')
        self.assertEqual(result['status'], 'pass')
        records = self.records(stderr.getvalue())
        self.assertEqual(records[0], {'condition': 'sequence', 'phase': 'start'})
        self.assertEqual(records[1], {'condition': 'child\nwith newline', 'phase': 'start'})
        self.assertEqual(records[-2], {'condition': 'sequence', 'phase': 'complete', 'status': 'pass'})
        self.assertEqual(records[-1], {'condition': 'outer', 'phase': 'after'})
        self.assertEqual(len(stderr.getvalue().splitlines()), len(records))

    def test_samples_are_throttled_and_capped_but_completion_is_always_reported(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr), self.tool['progress_scope']('long-sweep', enabled=True), \
                patch.object(self.tool['time'], 'monotonic', return_value=0) as clock:
            self.tool['report_progress']('start')
            for second in (0, 1, 29, 30, 31, 60):
                clock.return_value = second
                self.tool['report_progress']('sweep', step=second, steps=1000)
            clock.return_value = 60
            for index in range(100):
                self.tool['report_progress']('drive-frozen' if index % 2 else 'drive-contact',
                                             step=index, steps=1000)
            self.tool['report_progress']('complete', status='pass')
        records = self.records(stderr.getvalue())
        self.assertEqual([r['step'] for r in records if r['phase'] == 'sweep'], [0, 30, 60])
        self.assertEqual(sum('step' in record for record in records), self.tool['MAX_SAMPLE_PROGRESS'])
        self.assertEqual(records[-1], {'condition': 'long-sweep', 'phase': 'complete', 'status': 'pass'})

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
            self.assertEqual(set(payload), {'ok', 'project', 'assembly', 'results'})
            self.assertEqual(payload['results'], [self.tool['run_condition'](self.condition(), self.parts(), 0)])
            self.assertTrue(payload['ok'])
            self.assertEqual(self.records(stderr.getvalue())[0], {'condition': 'assembly', 'phase': 'start'})
            self.assertEqual(self.records(stderr.getvalue())[-1],
                             {'condition': 'escape', 'phase': 'complete', 'status': 'pass'})

    def test_real_runner_timeout_retains_flushed_condition_and_sample_progress(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'slow_condition.py'
            script.write_text(
                'import runpy, time\n'
                f'tool = runpy.run_path({str(CHECK)!r})\n'
                'with tool["progress_scope"]("aircraft-separates", enabled=True):\n'
                '    tool["report_progress"]("start")\n'
                '    tool["report_progress"]("sweep", step=7, steps=1060)\n'
                '    time.sleep(10)\n')
            log = root / 'motion.log'
            done = module.run([sys.executable, str(script)], cwd=root, log=log, timeout=2)
            self.assertEqual(done.returncode, 124)
            text = log.read_text()
            self.assertIn('TIMEOUT after 2s', text)
            self.assertIn('"condition": "aircraft-separates"', text)
            self.assertIn('"step": 7', text)
            self.assertIn('"steps": 1060', text)
            self.assertNotIn('"phase": "complete"', text)
            result = module.parse_motion(done.stdout, done.returncode, done.stderr)
            self.assertEqual(result['verdict'], 'fail')
            self.assertEqual(result['returncode'], 124)
            self.assertEqual(result['conditions'], [])


if __name__ == '__main__':
    unittest.main()
