#!/usr/bin/env python3
"""Build and exercise the installed Workshop CLI outside its source tree."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


SCHEMA_OWNERS = {
    "artifact-manifest.schema.json": "artifacts",
    "inventor.schema.json": "contributors",
    "cad-project.schema.json": "make",
    "maker-mark.schema.json": "make",
    "validator-policy.schema.json": "make",
    "verification-receipt.schema.json": "make",
    "gate-result.schema.json": "playtest",
    "inspection-result.schema.json": "playtest",
    "playtest-result.schema.json": "playtest",
    "receipt.schema.json": "runtime",
    "stamp.schema.json": "runtime",
}


def _run(command, *, cwd: Path, environment=None) -> subprocess.CompletedProcess:
    completed = subprocess.run(
        [str(part) for part in command],
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "command failed (%d): %s\nstdout:\n%s\nstderr:\n%s"
            % (
                completed.returncode,
                " ".join(str(part) for part in command),
                completed.stdout,
                completed.stderr,
            )
        )
    return completed


def _python_path(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _workshop_path(venv: Path) -> Path:
    return venv / ("Scripts/workshop.exe" if os.name == "nt" else "bin/workshop")


def _build_wheel(repository: Path, root: Path) -> Path:
    source = root / "source"
    shutil.copytree(
        repository,
        source,
        symlinks=True,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            ".workshop",
            ".pytest_cache",
            "__pycache__",
            "*.egg-info",
            "build",
            "dist",
        ),
    )
    wheelhouse = root / "wheelhouse"
    wheelhouse.mkdir()
    _run(
        (
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-build-isolation",
            "--no-deps",
            "--wheel-dir",
            wheelhouse,
            source,
        ),
        cwd=source,
    )
    wheels = tuple(wheelhouse.glob("autonomous_workshop-*.whl"))
    if len(wheels) != 1:
        raise AssertionError("expected exactly one Workshop wheel")
    return wheels[0]


def _audit_wheel(wheel: Path, repository: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        infos = {item.filename: item for item in archive.infolist()}
        members = set(infos)

        generated_bytecode = sorted(
            name
            for name in members
            if "/__pycache__/" in name or name.endswith((".pyc", ".pyo"))
        )
        if generated_bytecode:
            raise AssertionError(
                "wheel contains generated Python bytecode: %r" % generated_bytecode
            )
        misplaced_cli_tests = sorted(
            name
            for name in members
            if name.startswith("cli/")
            and name.endswith(".py")
            and (
                name.rsplit("/", 1)[-1].startswith("test_")
                or name.rsplit("/", 1)[-1].endswith("_test.py")
            )
        )
        if misplaced_cli_tests:
            raise AssertionError(
                "wheel contains misplaced CLI tests: %r" % misplaced_cli_tests
            )

        code_roots = {
            name.split("/", 1)[0]
            for name in members
            if name.endswith(".py") and ".dist-info/" not in name
        }
        if code_roots != {"cli", "workshop"}:
            raise AssertionError("unexpected wheel Python packages: %r" % sorted(code_roots))
        for forbidden in (
            "autonomous_workshop/",
            "inventor_core/",
            "inventor_foundation/",
            "inventor_workshop/",
            "workshop_cli/",
            "tests/",
            "cli/tests/",
        ):
            if any(name.startswith(forbidden) for name in members):
                raise AssertionError("wheel contains removed tree %s" % forbidden)
        for forbidden in (
            "workshop/__main__.py",
            "workshop/cli.py",
            "workshop/jobs.py",
            "workshop/models.py",
            "workshop/workflow/creation.py",
        ):
            if forbidden in members:
                raise AssertionError("wheel contains removed flat module %s" % forbidden)
        for required in (
            "cli/__init__.py",
            "cli/main.py",
            "workshop/__init__.py",
            "workshop/make/skills/LOCK.json",
            "workshop/runtime/_agent_assets/.agents/product-run/AGENTS.md",
            "workshop/runtime/_agent_assets/.agents/skills/autonomous-workshop/SKILL.md",
        ):
            if required not in members:
                raise AssertionError("wheel is missing %s" % required)

        skills = repository / "src" / "workshop" / "make" / "skills"
        for source in skills.rglob("*"):
            if not source.is_file() or "__pycache__" in source.parts:
                continue
            member = "workshop/make/skills/%s" % source.relative_to(skills).as_posix()
            if member not in infos:
                raise AssertionError("wheel is missing skill asset %s" % member)
            if archive.read(member) != source.read_bytes():
                raise AssertionError("wheel skill bytes differ for %s" % member)
            source_mode = source.stat().st_mode & 0o777
            wheel_mode = (infos[member].external_attr >> 16) & 0o777
            if wheel_mode != source_mode:
                raise AssertionError(
                    "wheel skill mode differs for %s: %o != %o"
                    % (member, wheel_mode, source_mode)
                )

        agent_asset_sources = (
            repository / ".agents" / "product-run",
            repository / ".agents" / "skills" / "autonomous-workshop",
        )
        for source_root in agent_asset_sources:
            for source in source_root.rglob("*"):
                if not source.is_file() or source.is_symlink():
                    continue
                relative = source.relative_to(repository / ".agents")
                member = (
                    "workshop/runtime/_agent_assets/.agents/%s"
                    % relative.as_posix()
                )
                if member not in infos:
                    raise AssertionError("wheel is missing agent asset %s" % member)
                if archive.read(member) != source.read_bytes():
                    raise AssertionError("wheel agent asset bytes differ for %s" % member)
                source_mode = source.stat().st_mode & 0o777
                wheel_mode = (infos[member].external_attr >> 16) & 0o777
                if wheel_mode != source_mode:
                    raise AssertionError(
                        "wheel agent asset mode differs for %s: %o != %o"
                        % (member, wheel_mode, source_mode)
                    )

        expected_schemas = {
            "workshop/%s/schemas/%s" % (owner, name)
            for name, owner in SCHEMA_OWNERS.items()
        }
        observed_schemas = {
            name
            for name in members
            if "/schemas/" in name and name.endswith(".schema.json")
        }
        if observed_schemas != expected_schemas:
            raise AssertionError(
                "wheel schema inventory differs: expected %r, observed %r"
                % (sorted(expected_schemas), sorted(observed_schemas))
            )
        for member in expected_schemas:
            relative = Path(member).relative_to("workshop")
            source = repository / "src" / "workshop" / relative
            if archive.read(member) != source.read_bytes():
                raise AssertionError("wheel schema bytes differ for %s" % member)


def _install_wheel(wheel: Path, root: Path) -> tuple[Path, Path]:
    venv = root / "venv"
    _run((sys.executable, "-m", "venv", venv), cwd=root)
    python = _python_path(venv)
    _run((python, "-m", "pip", "install", "--no-deps", wheel), cwd=root)
    return python, _workshop_path(venv)


def _install_fake_codex(python: Path, root: Path) -> Path:
    helper = root / "fake-codex.py"
    helper.write_text(
        """\
import json
import os
import sys
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    print("codex-cli 1.0.0")
    raise SystemExit(0)

run_root = Path.cwd()
stage = json.loads((run_root / "STAGE.json").read_text(encoding="utf-8"))
wish = json.loads((run_root / "WISH.json").read_text(encoding="utf-8"))
prompt = sys.stdin.read()
proposal = {
    "schema_version": 1,
    "kind": "autonomous-workshop.agent-outcome-proposal",
    "checkpoint_sha256": stage["checkpoint_sha256"],
    "subject_sha256": stage["subject_sha256"],
    "outcome": {
        "schema_version": 1,
        "stage": stage["stage"],
        "status": "waiting",
        "artifacts": [],
        "needs": ["installed fixture stops after one native turn"],
        "proposed_transition": None,
    },
}
(run_root / "agent-outcome.json").write_text(
    json.dumps(proposal, sort_keys=True, separators=(",", ":")) + "\\n",
    encoding="utf-8",
)
(run_root / "installed-native-probe.json").write_text(
    json.dumps(
        {
            "arguments": sys.argv[1:],
            "factory_visible": "FACTORY_PASSWORD" in os.environ,
            "objective": wish["objective"],
            "prompt": prompt,
            "stage": stage["stage"],
        },
        sort_keys=True,
    ) + "\\n",
    encoding="utf-8",
)
print(json.dumps({"type": "thread.started", "thread_id": "12345678-1234-5678-9234-567812345678"}))
print(json.dumps({"type": "item.completed", "item": {"id": "message-1", "type": "agent_message", "text": "fixture complete"}}))
""",
        encoding="utf-8",
    )
    if os.name == "nt":
        executable = root / "codex.cmd"
        executable.write_text(
            '@echo off\r\n"%s" "%s" %%*\r\n' % (python, helper),
            encoding="utf-8",
        )
    else:
        executable = root / "codex"
        executable.write_text(
            "#!%s\n%s" % (python, helper.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        executable.chmod(0o700)
    return executable


def _json_command(command, *, cwd: Path, environment) -> dict | list:
    return json.loads(_run(command, cwd=cwd, environment=environment).stdout)


def acceptance(wheel: Path, repository: Path) -> None:
    _audit_wheel(wheel, repository)
    with tempfile.TemporaryDirectory(prefix="workshop-installed-wheel-") as temporary:
        root = Path(temporary).resolve()
        away = root / "unrelated-cwd"
        away.mkdir()
        python, workshop = _install_wheel(wheel, root)
        home = root / "workshop-home"
        fake_codex = _install_fake_codex(python, root)
        environment = {
            name: os.environ[name]
            for name in (
                "HOME",
                "LANG",
                "LC_ALL",
                "LC_CTYPE",
                "PATH",
                "SYSTEMROOT",
                "TMPDIR",
            )
            if os.environ.get(name)
        }
        environment["WORKSHOP_CODEX_BIN"] = str(fake_codex)
        environment["WORKSHOP_HOME"] = str(home)
        environment["FACTORY_PASSWORD"] = "must-not-reach-native-codex"

        identity = _run(
            (
                python,
                "-c",
                "import importlib.metadata as m, importlib.util as u; "
                "import workshop, cli.main; "
                "assert m.version('autonomous-workshop') == workshop.__version__; "
                "assert u.find_spec('inventor_workshop') is None; "
                "assert u.find_spec('inventor_core') is None; "
                "assert u.find_spec('inventor_foundation') is None; "
                "assert u.find_spec('workshop_cli') is None; "
                "assert u.find_spec('autonomous_workshop') is None; "
                "print(workshop.__version__)",
            ),
            cwd=away,
            environment=environment,
        ).stdout.strip()
        if not identity:
            raise AssertionError("installed distribution identity was empty")

        skill_inventory = _json_command(
            (workshop, "skills", "list", "--json"), cwd=away, environment=environment
        )
        if [item["name"] for item in skill_inventory] != [
            "cad",
            "product-to-cad",
            "step-parts",
        ]:
            raise AssertionError("installed skill inventory is incomplete")
        schema_inventory = set(
            _run(
                (workshop, "schemas", "list"), cwd=away, environment=environment
            ).stdout.splitlines()
        )
        if schema_inventory != set(SCHEMA_OWNERS):
            raise AssertionError("installed schema inventory is incomplete")

        skill_launcher = Path(
            _run(
                (
                    python,
                    "-c",
                    "from workshop.make.skill_registry import discover_skills; "
                    "print(next(s for s in discover_skills() if s.name == 'cad').root "
                    "/ 'scripts' / 'check_fit')",
                ),
                cwd=away,
                environment=environment,
            ).stdout.strip()
        )
        _run((skill_launcher, "--help"), cwd=away, environment=environment)

        empty = _json_command(
            (workshop, "status", "--json"), cwd=away, environment=environment
        )
        if empty != {"schema_version": 1, "status": "ok", "count": 0, "wishes": []}:
            raise AssertionError("fresh installed status was not empty")
        if home.exists():
            raise AssertionError("read-only status initialized WORKSHOP_HOME")

        inventors = _json_command(
            (workshop, "inventors", "--json"), cwd=away, environment=environment
        )
        if [item["id"] for item in inventors] != ["alice", "bob", "eve", "ivy", "leo"]:
            raise AssertionError("installed no-root Inventor discovery is incomplete")
        if home.exists():
            raise AssertionError("read-only Inventor discovery initialized WORKSHOP_HOME")

        wish_completed = _run(
            (
                workshop,
                "wish",
                "a chess set shaped by our mountain memories",
                "--draft",
                "--json",
            ),
            cwd=away,
            environment=environment,
        )
        wish = json.loads(wish_completed.stdout)
        product_id = wish["wish"]["product_id"]
        if (
            wish.get("kind") != "native-agent-run"
            or wish.get("status") != "waiting"
            or wish.get("stage") != "match"
            or wish.get("native_turns") != 1
        ):
            raise AssertionError(
                "installed native Wish stopped at the wrong boundary: %s"
                % json.dumps(
                    {"receipt": wish, "stderr": wish_completed.stderr},
                    sort_keys=True,
                )
            )
        if wish["publication"]["status"] != "not-created":
            raise AssertionError("installed native Wish fabricated a publication")
        workspace = home / "runs" / product_id / "workspace"
        probe = json.loads(
            (workspace / "installed-native-probe.json").read_text(encoding="utf-8")
        )
        if probe["objective"] != "a chess set shaped by our mountain memories":
            raise AssertionError("installed native subprocess read a different Wish")
        if probe["stage"] != "match" or "current match stage" not in probe["prompt"]:
            raise AssertionError("installed native subprocess received the wrong stage")
        if probe["objective"] in probe["prompt"]:
            raise AssertionError("installed native prompt duplicated private Wish text")
        if probe["factory_visible"]:
            raise AssertionError("installed native subprocess received an effect secret")
        if "--search" not in probe["arguments"] or "workspace-write" not in probe["arguments"]:
            raise AssertionError("installed native subprocess lacked declared capabilities")
        if (workspace / "agent-outcome.json").exists():
            raise AssertionError("host did not consume the installed native proposal")

        current = Path(
            _run(
                (
                    python,
                    "-c",
                    "from workshop.runtime.package_data import "
                    "materialize_bundled_inventors; print(materialize_bundled_inventors())",
                ),
                cwd=away,
                environment=environment,
            ).stdout.strip()
        )
        packaged = Path(
            _run(
                (
                    python,
                    "-c",
                    "from workshop.runtime.package_data import "
                    "packaged_inventors_root; print(packaged_inventors_root())",
                ),
                cwd=away,
                environment=environment,
            ).stdout.strip()
        )
        taste = packaged / "alice" / "TASTE.md"
        taste.write_bytes(taste.read_bytes() + b"\n<!-- simulated package upgrade -->\n")
        upgraded = Path(
            _run(
                (
                    python,
                    "-c",
                    "from workshop.runtime.package_data import "
                    "materialize_bundled_inventors; print(materialize_bundled_inventors())",
                ),
                cwd=away,
                environment=environment,
            ).stdout.strip()
        )
        if upgraded == current:
            raise AssertionError("changed installed identity reused the old catalog root")

        status = _json_command(
            (workshop, "status", product_id, "--json"),
            cwd=away,
            environment=environment,
        )
        if status["product_id"] != product_id:
            raise AssertionError("installed status returned a different Wish")
        if status["kind"] != "native-agent-run" or status["stage"] != "match":
            raise AssertionError("installed status did not read the native checkpoint")
        if status["session_status"] != "checkpointed":
            raise AssertionError("installed status lost the native session binding")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheel",
        type=Path,
        help="prebuilt Workshop wheel (default: build the current checkout)",
    )
    args = parser.parse_args(argv)
    repository = Path(__file__).resolve().parents[2]
    if args.wheel is not None:
        acceptance(args.wheel.resolve(strict=True), repository)
    else:
        with tempfile.TemporaryDirectory(prefix="workshop-wheel-build-") as temporary:
            acceptance(_build_wheel(repository, Path(temporary)), repository)
    print("installed-wheel-cli: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
