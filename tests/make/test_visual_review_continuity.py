"""Visual errors cannot disappear when local repairs or missing renders intervene."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import subprocess

from tests.make.test_make_round import load_module, fake_visual_render


class VisualContinuityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = self.enterContext(tempfile.TemporaryDirectory())
        self.project = Path(self.tmp).resolve()
        self.module = load_module()
        self.entry = self.project / 'toy.step.py'
        self.entry.write_text('shape = "cone"')
        self.previous = None
        self.round = 0

    def prepare(self, render_error=False):
        self.round += 1
        out = self.project / 'measure/rounds' / ('r%04d' % self.round)
        out.mkdir(parents=True)
        def render(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, '', '') if render_error else fake_visual_render(command)
        with mock.patch.object(self.module, 'run', side_effect=render):
            visual = self.module.prepare_visual(self.project, self.entry, out, self.project, [], self.previous)
        summary = {'round': self.round, 'scope': 'assembly', 'visual': visual, 'checks_ok': True, 'ok': False}
        (out / 'summary.json').write_text(json.dumps(summary))
        (self.project / 'measure/make-round-state.json').write_text(json.dumps({'last_out': str(out)}))
        self.previous = out
        return summary

    def feedback(self, summary, *, status='pass', findings=None, resolutions=None, form='pass'):
        packet = summary['visual']
        value = {'packet_sha256': packet['packet_sha256'], 'status': status,
                 'observation': 'Compared current and prior views against reference.',
                 'findings': findings or [], 'resolutions': resolutions or [],
                 'assessments': {k: {'status': form if k == 'form' else 'pass',
                                     'observation': 'Synthetic assessment for regression.'}
                                 for k in ('form', 'assembly')}}
        path = self.project / 'measure/feedback.json'
        path.write_text(json.dumps(value))
        return self.module.record_visual(self.project, path)

    def fail_form(self):
        return self.feedback(self.prepare(), status='fail', form='fail', findings=[{
            'part': 'cape', 'defect': 'Overall cape reads as a lampshade',
            'evidence': 'Front silhouette flares as a rigid cone', 'repair': 'Reconstruct draped shoulders and hem'}])

    def resolution(self, summary, **overrides):
        packet = json.loads(Path(summary['visual']['packet']).read_text())
        return dict({'id': 'r1-f1', 'image': next(iter(packet['images'])),
                     'change': 'Shoulder folds replace the former cone silhouette in the same front view.'}, **overrides)

    def test_local_pass_cannot_erase_global_form_issue(self):
        self.fail_form()
        summary = self.prepare()
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.feedback(summary)
        self.assertFalse(json.loads((self.previous / 'summary.json').read_text())['ok'])
        result = self.feedback(summary, resolutions=[self.resolution(summary)])
        self.assertTrue(result['ok'])
        self.assertEqual(result['visual']['open_findings'], [])

    def test_pending_and_render_errors_preserve_backlog(self):
        self.fail_form()
        self.prepare()  # Unreviewed round cannot clear the backlog.
        self.prepare(render_error=True)
        summary = self.prepare()
        self.assertEqual(summary['visual']['open_findings'][0]['id'], 'r1-f1')
        with self.assertRaisesRegex(ValueError, 'unresolved'):
            self.feedback(summary)

    def test_unknown_duplicate_and_old_image_closures_are_refused(self):
        self.fail_form()
        old_image = next(iter(json.loads((self.previous / 'visual-packet.json').read_text())['images']))
        summary = self.prepare()
        for changes in ({'id': 'invented'}, {'image': old_image}, {'change': ''}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.feedback(summary, resolutions=[self.resolution(summary, **changes)])
        with self.assertRaises(ValueError):
            self.feedback(summary, resolutions=[self.resolution(summary)] * 2)

    def test_assembly_pass_cannot_override_form_inconclusive(self):
        summary = self.prepare()
        with self.assertRaisesRegex(ValueError, 'both form and assembly'):
            self.feedback(summary, form='inconclusive')

    def test_history_edit_after_new_packet_is_refused(self):
        self.fail_form()
        old = self.previous / 'summary.json'
        summary = self.prepare()
        old.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'history changed'):
            self.feedback(summary, resolutions=[self.resolution(summary)])

    def test_wish_references_are_bound_without_explicit_likeness_option(self):
        (self.project / 'WISH.json').write_text('{}')
        (self.project / 'wish-references').mkdir()
        ref = self.project / 'wish-references/reference.png'
        ref.write_bytes(b'reference')
        summary = self.prepare()
        packet = json.loads(Path(summary['visual']['packet']).read_text())
        self.assertIn(str(ref), packet['references'])
        ref.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'stale images or references'):
            self.feedback(summary)
