"""One-file runtime corrections are recoverable and never reset a run."""
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from workshop.errors import ContractError, StateConflict
import workshop.workflow.agent_run as module
from workshop.workflow.agent_run import AgentRun, MANAGER_EFFORT_CHANGE_FILE
from workshop.workflow.effort import EFFORT_ROUTE_CAPABILITY_PATH


class ManagerEffortTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.skill = self.root / 'skill'
        (self.skill / 'references').mkdir(parents=True)
        (self.skill / 'SKILL.md').write_text('# Native Workshop\n')
        for name in (Path(EFFORT_ROUTE_CAPABILITY_PATH).name, 'token-budget-v1.md', 'budgets-v1.md'):
            (self.skill / 'references' / name).write_text('Frozen capability\n')
        self.constitution = self.root / 'source' / '.agents' / 'product-run' / 'AGENTS.md'
        self.constitution.parent.mkdir(parents=True)
        self.constitution.write_text('# Native product run\n')
        self.workspace, self.state = self.root / 'run', self.root / 'state'

    def create(self, workflow='spark'):
        wish = json.dumps({'schema_version': 1, 'product_id': 'effort-test', 'objective': 'Make a mechanical toy.',
                           'constraints': {}, 'context': {'source': 'test'}}, sort_keys=True, separators=(',', ':')).encode()
        return AgentRun.create(self.workspace, host_state_root=self.state, product_id='effort-test',
                               wish_bytes=wish, product_run_constitution_source=self.constitution,
                               skill_root=self.skill, effort=workflow, manager_id='codex',
                               manager_model='astra', manager_reasoning_effort='ultra')

    def recover(self):
        AgentRun.recover_manager_effort_change(self.workspace, self.state)

    def assert_medium(self):
        run = AgentRun.open(self.workspace, host_state_root=self.state)
        self.assertEqual(run.snapshot().manager_reasoning_effort, 'medium')
        self.assertEqual(run.snapshot().revision, 1)
        self.assertFalse((self.state / MANAGER_EFFORT_CHANGE_FILE).exists())
        self.assertEqual(stat.S_IMODE((self.workspace / 'MANAGER.json').stat().st_mode), 0o400)
        ledger = (self.state / 'host-corrections.jsonl').read_text().splitlines()
        self.assertEqual(len(ledger), 1)
        self.assertEqual(json.loads(ledger[0])['correction'], 'manager-reasoning-effort')
        return run

    def interrupt_after_write(self, run, filename):
        original = module._atomic_private_write
        def stop(path, content, **kwargs):
            original(path, content, **kwargs)
            if path.name == filename:
                raise KeyboardInterrupt
        with patch.object(module, '_atomic_private_write', side_effect=stop), self.assertRaises(KeyboardInterrupt):
            run.set_manager_reasoning_effort('medium', reason='User requested medium')

    def test_only_manager_and_checkpoint_change(self):
        run = self.create()
        original = run._load()
        for name in ('codex-session.json', 'native-budget.json'):
            (self.state / name).write_bytes(b'exact existing private state\n')
        (self.workspace / 'artifacts' / 'toy.txt').write_bytes(b'unchanged product\n')
        before = {str(p.relative_to(self.workspace)): p.read_bytes() for p in self.workspace.rglob('*') if p.is_file()}
        result = run.set_manager_reasoning_effort('medium', reason='User requested medium')
        self.assertTrue(result['changed'])
        updated = self.assert_medium()._load()
        for key in set(original) - {'inputs', 'revision', 'previous_checkpoint_sha256', 'checkpoint_sha256'}:
            self.assertEqual(updated[key], original[key], key)
        for old, new in zip(original['inputs'], updated['inputs']):
            if old['path'] != 'MANAGER.json':
                self.assertEqual(old, new)
        for name, content in before.items():
            if name != 'MANAGER.json':
                self.assertEqual((self.workspace / name).read_bytes(), content)
        for name in ('codex-session.json', 'native-budget.json'):
            self.assertEqual((self.state / name).read_bytes(), b'exact existing private state\n')
        self.assertEqual(run.snapshot().manager_model, 'gpt-6-astra')

    def test_noop_same_effort_writes_nothing(self):
        run = self.create()
        before = (self.state / 'agent-run.json').read_bytes()
        self.assertFalse(run.set_manager_reasoning_effort('ultra', reason='same choice')['changed'])
        self.assertEqual((self.state / 'agent-run.json').read_bytes(), before)
        self.assertFalse((self.state / 'host-corrections.jsonl').exists())

    def test_recovery_after_journal_write(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        self.recover()
        self.assert_medium()

    def test_failure_before_journal_write_leaves_original_run_openable(self):
        run = self.create()
        with patch.object(module, '_atomic_private_write', side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            run.set_manager_reasoning_effort('medium', reason='requested')
        self.recover()
        self.assertEqual(AgentRun.open(self.workspace, host_state_root=self.state).snapshot().manager_reasoning_effort, 'ultra')

    def test_no_pending_recovery_does_not_open_or_create_missing_roots(self):
        self.recover()
        self.assertFalse(self.workspace.exists())
        self.assertFalse(self.state.exists())

    def test_recovery_after_manager_write_and_open_never_mutates(self):
        self.interrupt_after_write(self.create(), 'MANAGER.json')
        with self.assertRaises(StateConflict):
            AgentRun.open(self.workspace, host_state_root=self.state)
        self.assertTrue((self.state / MANAGER_EFFORT_CHANGE_FILE).exists())
        self.recover()
        self.assert_medium()

    def test_recovery_after_checkpoint_write(self):
        self.interrupt_after_write(self.create(), 'agent-run.json')
        self.recover()
        self.assert_medium()

    def test_recovery_after_ledger_write_is_idempotent(self):
        self.interrupt_after_write(self.create(), 'host-corrections.jsonl')
        self.recover()
        before = (self.state / 'host-corrections.jsonl').read_bytes()
        self.recover()
        self.assertEqual((self.state / 'host-corrections.jsonl').read_bytes(), before)
        self.assert_medium()

    def test_recovery_rejects_altered_manager(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        module._atomic_private_write(self.workspace / 'MANAGER.json', b'{}\n', mode=0o400)
        with self.assertRaises(StateConflict):
            self.recover()
        self.assertEqual((self.workspace / 'MANAGER.json').read_bytes(), b'{}\n')

    def test_recovery_rejects_altered_journal_identity(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        path = self.state / MANAGER_EFFORT_CHANGE_FILE
        data = json.loads(path.read_text())
        data['product_id'] = 'another-product'
        path.write_text(json.dumps(data))
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_rejects_model_change_even_with_recomputed_target_hash(self):
        run = self.create()
        self.interrupt_after_write(run, MANAGER_EFFORT_CHANGE_FILE)
        path = self.state / MANAGER_EFFORT_CHANGE_FILE
        journal = json.loads(path.read_text())
        manager = json.loads(journal['manager'])
        manager['model'] = 'gpt-5.5'
        after = module._canonical_json(manager) + b'\n'
        journal['manager'] = after.decode()
        journal['checkpoint_sha256'] = AgentRun._manager_effort_checkpoint(run._load(), after)['checkpoint_sha256']
        path.write_text(json.dumps(journal))
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_rejects_journal_mode(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        (self.state / MANAGER_EFFORT_CHANGE_FILE).chmod(0o644)
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_rejects_journal_symlink(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        path = self.state / MANAGER_EFFORT_CHANGE_FILE
        target = self.state / 'journal-copy'
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_rejects_manager_mode(self):
        self.interrupt_after_write(self.create(), MANAGER_EFFORT_CHANGE_FILE)
        (self.workspace / 'MANAGER.json').chmod(0o600)
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_rejects_ledger_mode_before_accepting_existing_record(self):
        self.interrupt_after_write(self.create(), 'host-corrections.jsonl')
        (self.state / 'host-corrections.jsonl').chmod(0o644)
        with self.assertRaises(StateConflict):
            self.recover()
        self.assertTrue((self.state / MANAGER_EFFORT_CHANGE_FILE).exists())

    def test_recovery_rejects_new_checkpoint_with_old_manager(self):
        run = self.create()
        original = (self.workspace / 'MANAGER.json').read_bytes()
        self.interrupt_after_write(run, 'agent-run.json')
        module._atomic_private_write(self.workspace / 'MANAGER.json', original, mode=0o400)
        with self.assertRaises(StateConflict):
            self.recover()

    def test_recovery_checks_other_inputs_before_finishing(self):
        self.interrupt_after_write(self.create(), 'MANAGER.json')
        module._atomic_private_write(self.workspace / 'AGENTS.md', b'changed', mode=0o400)
        with self.assertRaises(StateConflict):
            self.recover()
        self.assertTrue((self.state / MANAGER_EFFORT_CHANGE_FILE).exists())
        self.assertFalse((self.state / 'host-corrections.jsonl').exists())

    def test_unsupported_workflow_refused(self):
        run = self.create('forge')
        with self.assertRaises(ContractError):
            run.set_manager_reasoning_effort('medium', reason='wrong workflow')

    def test_missing_budget_profile_refused(self):
        (self.skill / 'references' / 'budgets-v1.md').unlink()
        run = self.create()
        with self.assertRaises(ContractError):
            run.set_manager_reasoning_effort('medium', reason='missing profile')

    def test_invalid_effort_or_reason_refused_before_write(self):
        run = self.create()
        for effort, reason in (('unknown', 'requested'), (None, 'requested'), ('medium', '')):
            with self.subTest(effort=effort, reason=reason), self.assertRaises(ContractError):
                run.set_manager_reasoning_effort(effort, reason=reason)
        self.assertFalse((self.state / MANAGER_EFFORT_CHANGE_FILE).exists())


if __name__ == '__main__':
    unittest.main()
