"""Regression tests for Eve's path-independent launchd deployment."""

import os
import plistlib
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OPS = REPO / "ops"
LAUNCHD = OPS / "launchd"
RENDERER = OPS / "render_launchd.py"
MAIN_TEMPLATE = LAUNCHD / "ai.autonomous.eve.plist.in"
WATCHDOG_TEMPLATE = LAUNCHD / "ai.autonomous.eve.watchdog.plist.in"


def _render(template: Path):
    with tempfile.TemporaryDirectory(prefix="eve-plist-render-") as directory:
        root = Path(directory)
        checkout = root / "checkout & launchd test"
        user_home = root / "home & launchd test"
        core_source = root / "Foundation & launchd test" / "src"
        checkout.mkdir()
        user_home.mkdir()
        (core_source / "inventor_core").mkdir(parents=True)
        (core_source / "inventor_core" / "__init__.py").write_text(
            '__version__ = "test"\n', encoding="utf-8"
        )
        output = root / "rendered.plist"
        result = subprocess.run(
            [
                sys.executable,
                str(RENDERER),
                "--template",
                str(template),
                "--output",
                str(output),
                "--repo",
                str(checkout),
                "--home",
                str(user_home),
                "--core-src",
                str(core_source),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            raise AssertionError(result.stderr.decode())
        raw = output.read_bytes()
        return (
            plistlib.loads(raw),
            str(checkout.resolve()),
            str(user_home.resolve()),
            str(core_source.resolve()),
            raw,
            stat.S_IMODE(output.stat().st_mode),
        )


class LaunchdRenderTests(unittest.TestCase):
    def test_main_job_uses_current_checkout_and_one_step_drive(self):
        plist, checkout, user_home, core_source, raw, mode = _render(MAIN_TEMPLATE)
        self.assertEqual(plist["Label"], "ai.autonomous.eve")
        self.assertEqual(
            plist["ProgramArguments"],
            [
                "/usr/bin/python3",
                os.path.join(checkout, "bin/eve"),
                "drive",
                "--steps",
                "1",
            ],
        )
        self.assertEqual(plist["WorkingDirectory"], checkout)
        self.assertEqual(
            plist["StandardOutPath"],
            os.path.join(checkout, "state/logs/tick.log"),
        )
        self.assertTrue(
            plist["EnvironmentVariables"]["PATH"].startswith(
                os.path.join(user_home, ".local/bin") + ":"
            )
        )
        self.assertEqual(
            plist["EnvironmentVariables"]["EVE_CORE_SRC"], core_source
        )
        self.assertEqual(
            plist["EnvironmentVariables"]["PYTHONPATH"], core_source
        )
        self.assertIn(core_source.replace("&", "&amp;").encode(), raw)
        self.assertNotIn(core_source.encode(), raw)
        self.assertEqual(mode, 0o600)
        self.assertIn(b"&amp;", raw)
        self.assertNotIn(b"/Users/d", raw)

    def test_watchdog_job_uses_current_checkout(self):
        plist, checkout, _user_home, _core_source, raw, _mode = _render(WATCHDOG_TEMPLATE)
        self.assertEqual(plist["Label"], "ai.autonomous.eve.watchdog")
        self.assertEqual(
            plist["ProgramArguments"],
            ["/bin/bash", os.path.join(checkout, "ops/watchdog.sh")],
        )
        self.assertEqual(plist["WorkingDirectory"], checkout)
        self.assertEqual(
            plist["StandardErrorPath"],
            os.path.join(checkout, "state/logs/watchdog.log"),
        )
        self.assertNotIn(b"/Users/d", raw)

    def test_renderer_rejects_relative_repository(self):
        with tempfile.TemporaryDirectory(prefix="eve-plist-reject-") as directory:
            root = Path(directory)
            user_home = root / "home"
            core_source = root / "core" / "src"
            user_home.mkdir()
            (core_source / "inventor_core").mkdir(parents=True)
            (core_source / "inventor_core" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            output = root / "rendered.plist"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RENDERER),
                    "--template",
                    str(MAIN_TEMPLATE),
                    "--output",
                    str(output),
                    "--repo",
                    "relative/checkout",
                    "--home",
                    str(user_home),
                    "--core-src",
                    str(core_source),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_renderer_rejects_core_source_without_package(self):
        with tempfile.TemporaryDirectory(prefix="eve-plist-core-reject-") as directory:
            root = Path(directory)
            checkout = root / "checkout"
            user_home = root / "home"
            core_source = root / "core" / "src"
            checkout.mkdir()
            user_home.mkdir()
            core_source.mkdir(parents=True)
            output = root / "rendered.plist"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RENDERER),
                    "--template",
                    str(MAIN_TEMPLATE),
                    "--output",
                    str(output),
                    "--repo",
                    str(checkout),
                    "--home",
                    str(user_home),
                    "--core-src",
                    str(core_source),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"does not contain inventor_core", result.stderr)
            self.assertFalse(output.exists())


class LaunchdInstallTests(unittest.TestCase):
    def test_shell_scripts_parse(self):
        for script in (OPS / "install.sh", OPS / "uninstall.sh", OPS / "watchdog.sh"):
            with self.subTest(script=script.name):
                result = subprocess.run(
                    ["/bin/bash", "-n", str(script)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_installer_renders_validates_and_bootstraps_templates(self):
        text = (OPS / "install.sh").read_text(encoding="utf-8")
        self.assertIn("render_launchd.py", text)
        self.assertIn(".plist.in", text)
        self.assertIn("--repo", text)
        self.assertIn("--home", text)
        self.assertIn("--core-src", text)
        self.assertIn("plutil -lint", text)
        self.assertIn("launchctl bootstrap", text)
        self.assertIn("inventor_core", text)
        self.assertIn("EVE_CORE_SRC", text)
        self.assertIn("PYTHONPATH", text)
        self.assertIn("inventor_core.__file__", text)
        self.assertNotIn('cp "$PLIST_SRC" "$PLIST_DST"', text)

    def test_launchd_docs_name_the_real_command(self):
        paths = (
            OPS / "README.md",
            OPS / "install.sh",
            REPO / "eve" / "cli.py",
            REPO / "eve" / "driver.py",
        )
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertIn("drive --steps 1", text)
        self.assertNotIn("tick --run-agent", text)


if __name__ == "__main__":
    unittest.main()
