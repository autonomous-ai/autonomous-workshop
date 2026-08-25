#!/usr/bin/env python3
"""Build and exercise the installed Workshop CLI outside its source tree."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
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
            repository,
        ),
        cwd=repository,
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


def _install_offline_boundary(python: Path, root: Path, marker: Path) -> None:
    purelib = Path(
        _run(
            (
                python,
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ),
            cwd=root,
        ).stdout.strip()
    )
    source = """\
import importlib
from pathlib import Path

cli_module = importlib.import_module("cli.main")
from workshop.invent.agent import (
    InventResearchUnavailable,
    PublicHTTPResearchProvider,
)
from workshop.match.service import TasteFit, create_shortlist


class AcceptanceSemanticManager:
    judge_identity = "installed-wheel-acceptance-manager"
    judge_version = "1.0.0"
    judge_config_sha256 = "a" * 64

    def retrieve(self, context):
        return create_shortlist(
            context,
            ("alice", "bob"),
            retriever=self.judge_identity,
            retriever_version=self.judge_version,
            rationale="Deterministic installed-wheel routing boundary.",
        )

    def judge(self, context):
        finalists = {item.card.inventor_id: item for item in context.finalists}
        return (
            TasteFit(
                inventor_id="alice",
                taste_sha256=finalists["alice"].taste.sha256,
                score=99,
                accepted=True,
                explanation="The fixture Wish is a personalized known classic.",
            ),
            TasteFit(
                inventor_id="bob",
                taste_sha256=finalists["bob"].taste.sha256,
                score=12,
                accepted=False,
                explanation="The Wish preserves a classic rather than inventing a mechanism.",
                tensions=("Bob's Taste calls for an original moving mechanism.",),
            ),
        )


def offline_research(self, context):
    del self
    Path(%r).write_text(context.wish.product_id + "\\n", encoding="utf-8")
    raise InventResearchUnavailable("deterministic installed-wheel offline boundary")


cli_module.CodexSemanticManager = AcceptanceSemanticManager
PublicHTTPResearchProvider.__call__ = offline_research
""" % str(marker)
    (purelib / "workshop_acceptance_boundary.py").write_text(
        source, encoding="utf-8"
    )
    (purelib / "workshop_acceptance_boundary.pth").write_text(
        "import workshop_acceptance_boundary\n", encoding="utf-8"
    )


def _json_command(command, *, cwd: Path, environment) -> dict | list:
    return json.loads(_run(command, cwd=cwd, environment=environment).stdout)


def acceptance(wheel: Path, repository: Path) -> None:
    _audit_wheel(wheel, repository)
    with tempfile.TemporaryDirectory(prefix="workshop-installed-wheel-") as temporary:
        root = Path(temporary)
        away = root / "unrelated-cwd"
        away.mkdir()
        python, workshop = _install_wheel(wheel, root)
        marker = root / "offline-research-called"
        _install_offline_boundary(python, root, marker)
        home = root / "workshop-home"
        fake_codex = root / ("codex.cmd" if os.name == "nt" else "codex")
        if os.name == "nt":
            fake_codex.write_text(
                "@echo off\r\nif \"%1\"==\"--version\" (echo codex 1.0.0 & exit /b 0)\r\nexit /b 97\r\n",
                encoding="utf-8",
            )
        else:
            fake_codex.write_text(
                "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'codex 1.0.0'; exit 0; fi\nexit 97\n",
                encoding="utf-8",
            )
            fake_codex.chmod(0o700)
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

        boundary = _run(
            (
                python,
                "-c",
                "import importlib; c = importlib.import_module('cli.main'); "
                "print(c.CodexSemanticManager.__name__)",
            ),
            cwd=away,
            environment=environment,
        ).stdout.strip()
        if boundary != "AcceptanceSemanticManager":
            raise AssertionError(
                "installed offline boundary did not load: %r" % boundary
            )

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
        match = wish.get("match")
        if not isinstance(match, dict) or match.get("inventor_id") != "alice":
            raise AssertionError(
                "offline installed Wish was routed incorrectly: %s"
                % json.dumps(
                    {"receipt": wish, "stderr": wish_completed.stderr},
                    sort_keys=True,
                )
            )
        if wish["result"]["status"] != "waiting" or wish["result"]["job"] != "invent":
            raise AssertionError("offline installed Wish crossed its research boundary")
        if marker.read_text(encoding="utf-8").strip() != product_id:
            raise AssertionError("installed profile subprocess did not reach shared Invent")

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
        profile = packaged / "alice" / "profile.py"
        profile.write_bytes(profile.read_bytes() + b"\n# simulated package upgrade\n")
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
        if Path(status["catalog_root"]) != current.resolve():
            raise AssertionError("status did not find the exact retained catalog")


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
