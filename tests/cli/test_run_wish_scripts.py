import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
from cli.main import parser

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('wish_script', ROOT / 'run_wish.py')
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RunWishScriptsTest(unittest.TestCase):
    def config(self):
        return dict(wish='test object', agent='codex', model='gpt-6-astra',
                    workflow='spark', effort='medium', max_tokens=None,
                    turn_minutes=None)

    def test_pinned_binary_is_used_without_overriding_explicit_selection(self):
        with mock.patch.dict(runner.os.environ, {}, clear=True), mock.patch.object(runner, "PINNED_CODEX_BINARY", Path(__file__)):
            self.assertEqual(runner.runtime_environment()["WORKSHOP_CODEX_BIN"], str(Path(__file__)))
        with mock.patch.dict(runner.os.environ, {"WORKSHOP_CODEX_BIN": "/explicit/codex"}, clear=True):
            self.assertEqual(runner.runtime_environment()["WORKSHOP_CODEX_BIN"], "/explicit/codex")

    def test_new_commands_match_current_cli_for_both_runtimes(self):
        for agent, model, effort in [('codex','gpt-6-astra','medium'),('claude','sonnet','high')]:
            with self.subTest(agent=agent):
                command = runner.build_command({**self.config(), 'agent':agent,'model':model,'effort':effort}, None)
                args = parser().parse_args(command[3:])
                self.assertTrue(args.strict)
                self.assertEqual(args.agent, agent)
                self.assertEqual(args.model, model)
                self.assertEqual(args.workflow, 'spark')
                self.assertEqual(args.effort, effort)

    def test_astra_ultra_commands_accept_alias_and_full_model_id(self):
        for model in ('astra', 'gpt-6-astra'):
            with self.subTest(model=model):
                command = runner.build_command(
                    {**self.config(), 'model': model, 'effort': 'ultra',
                     'max_tokens': 100_000_000}, None
                )
                args = parser().parse_args(command[3:])
                self.assertEqual(args.agent, 'codex')
                self.assertEqual(args.model, model)
                self.assertEqual(args.effort, 'ultra')
                self.assertEqual(args.max_tokens, 100_000_000)

    def test_ultra_rejects_other_models_and_managers_before_launch(self):
        selections = [
            ('codex', model)
            for model in ('sol', 'gpt-5.6-sol', 'terra', 'gpt-5.6-terra',
                          'luna', 'gpt-5.6-luna')
        ] + [('claude', 'opus'), ('claude', 'gpt-6-astra'), ('grok', 'grok-4.6')]
        for agent, model in selections:
            with self.subTest(agent=agent, model=model):
                config = {**self.config(), 'agent': agent, 'model': model,
                          'effort': 'ultra'}
                with self.assertRaises(runner.SetupError):
                    runner.build_command(config, None)
                with mock.patch.object(runner, 'CONFIG', config), \
                     mock.patch.object(sys, 'argv', ['run_wish.py', '--yes']), \
                     mock.patch.object(runner.subprocess, 'run') as launch, \
                     contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(runner.main(), 2)
                launch.assert_not_called()

    def test_resume_only_passes_id_and_explicit_total_budget(self):
        for limit in (None, 12_000_000):
            # Even a currently invalid CONFIG selection cannot replace frozen settings.
            command = runner.build_command(
                {**self.config(), 'model': 'sol', 'effort': 'ultra',
                 'max_tokens': limit}, 'wish-test'
            )
            args = parser().parse_args(command[3:])
            self.assertEqual(args.product_id, 'wish-test')
            self.assertEqual(args.max_tokens, limit)
            self.assertNotIn('--model', command)
            self.assertNotIn('--effort', command)
            self.assertTrue(args.strict)

    def test_resume_rejects_explicit_runtime_overrides_before_launch(self):
        for option, value in [('--model','sol'),('--workflow','forge'),('--effort','high'),('--effort','ultra'),('--reasoning-effort','ultra'),('--agent','claude')]:
            with self.subTest(option=option, value=value), mock.patch.object(sys,'argv',['run_wish.py','--resume','wish-test',option,value]), mock.patch.object(runner.subprocess,'run') as launch, contextlib.redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as e:runner.main()
                self.assertEqual(e.exception.code,2)
                self.assertIn('Resume dùng cấu hình đã đóng băng', error.getvalue())
                launch.assert_not_called()

    def test_resume_does_not_adopt_config_token_limit(self):
        with mock.patch.object(runner,'CONFIG',{**self.config(),'max_tokens':20_000_000}), mock.patch.object(sys,'argv',['run_wish.py','--resume','wish-test','--yes']), mock.patch.object(runner.subprocess,'run',return_value=mock.Mock(returncode=1)) as launch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(),1)
            self.assertNotIn('--max-tokens',launch.call_args.args[0])

    def test_invalid_budgets_and_removed_provider_are_rejected(self):
        for extra in [{'max_tokens':999},{'max_tokens':True},{'max_tokens':100_000_001},{'agent':'claude','max_tokens':10000},{'use_openrouter':True}]:
            with self.subTest(extra=extra),self.assertRaises(runner.SetupError):runner.build_command({**self.config(),**extra},None)

    def test_turn_boundary_reaches_both_wish_and_resume_commands(self):
        for value, expected in ((240, 240 * 60), ('none', 'none')):
            with self.subTest(value=value):
                config = {**self.config(), 'turn_minutes': value}
                wish_args = parser().parse_args(
                    runner.build_command(config, None)[3:]
                )
                resume_args = parser().parse_args(
                    runner.build_command(config, 'wish-test')[3:]
                )
                self.assertEqual(wish_args.turn_minutes, expected)
                self.assertEqual(resume_args.turn_minutes, expected)

    def test_no_turn_boundary_leaves_the_flag_off_both_commands(self):
        for resume_id in (None, 'wish-test'):
            with self.subTest(resume=resume_id):
                command = runner.build_command(self.config(), resume_id)
                self.assertNotIn('--turn-minutes', command)
                self.assertIsNone(parser().parse_args(command[3:]).turn_minutes)

    def test_invalid_turn_boundaries_are_rejected_before_launch(self):
        for value in (0, 361, 'forever', 3.5, True):
            with self.subTest(value=value), self.assertRaises(runner.SetupError):
                runner.build_command(
                    {**self.config(), 'turn_minutes': value}, None
                )

    def test_dry_run_never_executes_or_prompts(self):
        with mock.patch.object(runner,'CONFIG',self.config()), mock.patch.object(sys,'argv',['run_wish.py','--dry-run']), mock.patch.object(runner.subprocess,'run') as launch, mock.patch.object(runner,'confirm_publication_risk') as confirm, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(),0)
        launch.assert_not_called();confirm.assert_not_called()

    def test_yes_launches_current_cli_and_preserves_exit_status(self):
        with mock.patch.object(runner,'CONFIG',self.config()), mock.patch.object(sys,'argv',['run_wish.py','--yes']), mock.patch.object(runner.subprocess,'run',return_value=mock.Mock(returncode=1)) as launch, mock.patch.object(runner,'confirm_publication_risk') as confirm, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.main(),1)
        confirm.assert_not_called()
        args=parser().parse_args(launch.call_args.args[0][3:]);self.assertEqual(args.effort,'medium')

    def test_both_script_entrypoints_dry_run_and_real_cli_help(self):
        for script in ('run_wish.py','run_wish_codex.py'):
            result=subprocess.run([sys.executable,str(ROOT/script),'--dry-run'],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('--workflow spark',result.stdout)
            self.assertNotIn('--reasoning-effort',result.stdout)
        command=runner.build_command(self.config(),None)
        result=subprocess.run(command[:3]+['wish','--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--max-tokens',result.stdout)

    def test_both_script_entrypoints_parse_ultra_without_installed_package(self):
        for script in ('run_wish.py', 'run_wish_codex.py'):
            for model in ('astra', 'gpt-6-astra'):
                with self.subTest(script=script, model=model):
                    result = subprocess.run(
                        [sys.executable, '-S', str(ROOT / script), '--dry-run',
                         '--agent', 'codex', '--model', model, '--effort', 'ultra',
                         '--max-tokens', '100000000'],
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('--effort ultra', result.stdout)
                    self.assertIn('--max-tokens 100000000', result.stdout)
