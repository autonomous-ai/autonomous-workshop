"""Sandbox housekeeping refusal must not erase an ordered geometry result."""
import contextlib
import io
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts'
sys.path.insert(0, str(SCRIPTS))
import motion_parallel as parallel


class CleanupTests(unittest.TestCase):
    def test_normal_cleanup_removes_only_owned_scratch(self):
        with parallel._scratch_directory() as path:
            directory = Path(path)
            (directory / 'operand.brep').write_bytes(b'fixture')
        self.assertFalse(directory.exists())

    def test_creation_failure_still_propagates(self):
        with patch.object(parallel.tempfile, 'mkdtemp', side_effect=PermissionError('create denied')):
            with self.assertRaisesRegex(PermissionError, 'create denied'):
                with parallel._scratch_directory():
                    self.fail('unavailable scratch entered')

    def test_worker_manager_exclusively_reaps_cancelled_processes(self):
        for stuck in (False, True):
            with self.subTest(stuck=stuck):
                events = []
                class Manager:
                    def join(self, timeout): events.append('manager join')
                    def is_alive(self): return stuck
                class Process:
                    def join(self, **kwargs):
                        raise AssertionError('concurrent process reaping')
                    def kill(self): events.append('kill')
                class Future:
                    def result(self, **kwargs): return {'hit': {'step': 0}}
                class Executor:
                    def __init__(self, **kwargs):
                        self._processes = {1: Process()}
                        self._executor_manager_thread = Manager()
                    def submit(self, *args): return Future()
                    def terminate_workers(self):
                        events.append('terminate')
                        self._executor_manager_thread = None
                with patch.object(parallel, 'ProcessPoolExecutor', Executor):
                    def run():
                        return parallel.sweep('unused', [], [], 0, 0, .001, 2, None, lambda: None)
                    if stuck:
                        with self.assertRaisesRegex(RuntimeError, 'manager did not terminate'):
                            run()
                        self.assertEqual(events, ['terminate', 'manager join', 'kill', 'manager join'])
                    else:
                        self.assertEqual(run(), {'step': 0})
                        self.assertEqual(events, ['terminate', 'manager join'])

    def test_cleanup_denial_preserves_clear_collision_error_and_deadline(self):
        hit = {'step': 0, 'steps': 0, 'between': ['a', 'b'], 'overlapMm3': 2}
        for outcome in ({'hit': None}, {'hit': hit}, {'error': ('ValueError', 'invalid geometry')}, TimeoutError('deadline')):
            with self.subTest(outcome=outcome):
                class Future:
                    def result(self, timeout=None):
                        if isinstance(outcome, Exception):
                            raise outcome
                        return outcome
                class Executor:
                    _processes = {}
                    def __init__(self, **kwargs): pass
                    def submit(self, *args): return Future()
                    def shutdown(self, **kwargs): pass
                    def terminate_workers(self): pass
                removed = []
                def denied(path):
                    removed.append(path)
                    raise PermissionError('sandbox refused directory removal')
                stderr = io.StringIO()
                try:
                    with patch.object(parallel, 'ProcessPoolExecutor', Executor), \
                         patch.object(parallel.shutil, 'rmtree', side_effect=denied), \
                         contextlib.redirect_stderr(stderr):
                        def run():
                            return parallel.sweep('unused', [], [], 0, 0, .001, 2, None, lambda: None)
                        if isinstance(outcome, TimeoutError):
                            with self.assertRaisesRegex(TimeoutError, 'deadline'): run()
                        elif 'error' in outcome:
                            with self.assertRaisesRegex(parallel.GeometryError, 'invalid geometry'): run()
                        else:
                            self.assertEqual(run(), outcome['hit'])
                    self.assertEqual(len(removed), 1)
                    self.assertTrue(Path(removed[0]).is_dir())
                    self.assertIn('scratch cleanup deferred', stderr.getvalue())
                finally:
                    for path in removed: shutil.rmtree(path)


if __name__ == '__main__':
    unittest.main()
