"""Only a host-bound opt-out may omit final review; omission stays explicit."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / 'src/workshop/make/skills/cad/scripts'
FINALIZER = Path(__file__).resolve().parents[2] / '.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py'


class FinalReviewPolicyTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        scripts = self.root / '.agents/skills/cad/scripts'
        scripts.mkdir(parents=True)
        shutil.copyfile(SCRIPTS / 'final_review_policy.py', scripts / 'final_review_policy.py')
        self.policy = runpy.run_path(str(scripts / 'final_review_policy.py'))
        self.project = self.root / 'product/cad'
        (self.project / 'snap').mkdir(parents=True)
        for file in ('toy.step.py', 'snap/iso.png', 'snap/signature.png'):
            (self.project / file).write_bytes(b'synthetic fixture')
        self.options = self.root / 'FINAL-REVIEW-OPTIONS.json'

    def select(self, value):
        self.options.write_text(json.dumps({'schema_version': 1, 'check_final_review': value}))

    def marker(self):
        value = self.policy['omission'](self.project)
        (self.project / self.policy['MARKER']).write_text(json.dumps(value))
        return value

    def test_default_and_legacy_require_review(self):
        self.assertTrue(self.policy['enabled']())
        self.assertTrue(runpy.run_path(str(SCRIPTS / 'final_review_policy.py'))['enabled']())
        with self.assertRaisesRegex(ValueError, 'required'):
            self.marker()

    def test_opt_out_requires_bound_sources_and_images_and_honest_status(self):
        self.select(False)
        marker = self.marker()
        self.assertEqual(marker['status'], 'not-run')
        self.assertEqual(len(self.policy['validate'](self.project)), 64)
        for relative in ('toy.step.py', 'snap/iso.png', 'snap/signature.png'):
            path = self.project / relative
            original = path.read_bytes()
            path.write_bytes(b'drift')
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, 'stale'):
                self.policy['validate'](self.project)
            path.write_bytes(original)
        self.select(True)
        with self.assertRaises(ValueError):
            self.policy['validate'](self.project)

    def test_malformed_and_symlink_policy_cannot_disable_review(self):
        for value in ('false', None, 0):
            self.select(value)
            with self.assertRaises(ValueError):
                self.policy['enabled']()
        self.options.rename(self.root / 'other.json')
        self.options.symlink_to(self.root / 'other.json')
        with self.assertRaises(ValueError):
            self.policy['enabled']()

    def test_stale_passing_review_cannot_coexist_with_omission(self):
        self.select(False)
        (self.project / 'snap/SIGNATURE-REVIEW.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'archive prior'):
            self.marker()

    def test_finalizer_requires_disclosure_and_valid_omission(self):
        tool = runpy.run_path(str(FINALIZER))
        self.select(False)
        self.marker()
        document = self.root / 'product/product.json'
        document.write_text(json.dumps({'summary': 'Looks good'}))
        def validate():
            tool['_validate_signature_review'](self.root, product_root_value='product',
                                               cad_project_path=Path('cad'), concept_sha256='a' * 64)
        with self.assertRaisesRegex(tool['ProposalError'], 'must disclose'):
            validate()
        document.write_text(json.dumps({'summary': self.policy['DISCLOSURE']}))
        validate()
        (self.project / 'snap/iso.png').write_bytes(b'new')
        with self.assertRaisesRegex(tool['ProposalError'], 'stale'):
            validate()

    def test_verifier_omission_reaches_engineering_but_not_critic(self):
        tool = runpy.run_path(str(SCRIPTS / 'verify_project'))
        self.select(False)
        project = tool['_sc_project'](self.root)
        # Use the actual omission helper with the frozen operator policy.
        self.project = project
        (project / "snap/SIGNATURE-REVIEW.json").unlink()
        (project / 'snap').mkdir(exist_ok=True)
        for name in ('iso.png', 'signature.png'):
            (project / 'snap' / name).write_bytes(b'fixture render')
        self.marker()
        original = runpy.run_path
        def load(path, *a, **kw):
            return self.policy if Path(path).name == 'final_review_policy.py' else original(path, *a, **kw)
        called = []
        namespace = tool['main'].__globals__
        with patch.object(runpy, 'run_path', load), patch.dict(namespace, {
            '_required_signature_review': lambda *_: self.fail('critic gate called during opt-out'),
            '_run_or_stop': lambda *a, **kw: called.append(a) or False,
        }), contextlib.chdir(self.root), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            tool['main']([str(project)])
        self.assertTrue(called, 'engineering checks must still execute')
