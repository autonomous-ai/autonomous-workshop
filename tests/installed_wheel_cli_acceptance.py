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
            "--no-deps",
            "--wheel-dir",
            wheelhouse,
            repository,
        ),
        cwd=repository,
    )
    wheels = tuple(wheelhouse.glob("inventor_workshop-*.whl"))
    if len(wheels) != 1:
        raise AssertionError("expected exactly one Workshop wheel")
    return wheels[0]


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
import os
from pathlib import Path

import inventor_workshop.cli as workshop_cli
from inventor_workshop.agent_invent import (
    InventResearchUnavailable,
    PublicHTTPResearchProvider,
)
from inventor_workshop.manager import TasteFit, create_shortlist
from inventor_workshop.jobs import Need, WaitingFor


class AcceptanceSemanticManager:
    judge_identity = "installed-wheel-acceptance-manager"
    judge_version = "1.0.0"
    judge_config_sha256 = "a" * 64

    def retrieve(self, context):
        if os.environ.get("WORKSHOP_ACCEPTANCE_MATCH_WAIT") == "1":
            raise WaitingFor(
                Need(
                    "wish",
                    "semantic-inventor-retriever",
                    "The installed acceptance Manager is deliberately unavailable.",
                    "Restore the semantic Manager and resume this exact Wish.",
                )
            )
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


workshop_cli.CodexSemanticManager = AcceptanceSemanticManager
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


def acceptance(wheel: Path) -> None:
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

        boundary = _run(
            (
                python,
                "-c",
                "import inventor_workshop.cli as c; print(c.CodexSemanticManager.__name__)",
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

        waiting_environment = dict(environment)
        waiting_environment["WORKSHOP_ACCEPTANCE_MATCH_WAIT"] = "1"
        first_wait = subprocess.run(
            (
                str(workshop),
                "wish",
                "a patient clockwork moon for my desk",
                "--draft",
                "--strict",
                "--json",
            ),
            cwd=str(away),
            env=waiting_environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if first_wait.returncode != 1:
            raise AssertionError(
                "installed strict Match wait returned %d: %s"
                % (first_wait.returncode, first_wait.stderr)
            )
        first_wait_receipt = json.loads(first_wait.stdout)
        waiting_product_id = first_wait_receipt["wish"]["product_id"]
        waiting_status = _json_command(
            (workshop, "status", waiting_product_id, "--json"),
            cwd=away,
            environment=waiting_environment,
        )
        if (
            waiting_status.get("status") != "waiting"
            or waiting_status.get("needs") != first_wait_receipt.get("needs")
            or waiting_status.get("match_attempt")
            != first_wait_receipt.get("match_attempt")
        ):
            raise AssertionError(
                "installed status lost its durable Match wait: %s"
                % json.dumps(waiting_status, sort_keys=True)
            )
        resumed_wait = subprocess.run(
            (
                str(workshop),
                "resume",
                waiting_product_id,
                "--strict",
                "--json",
            ),
            cwd=str(away),
            env=waiting_environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        resumed_wait_receipt = json.loads(resumed_wait.stdout)
        if (
            resumed_wait.returncode != 1
            or resumed_wait_receipt.get("status") != "waiting"
            or resumed_wait_receipt.get("match_attempt", {}).get(
                "attempt_number"
            )
            != 2
            or resumed_wait_receipt.get("match_attempt", {}).get("attempt_id")
            == first_wait_receipt.get("match_attempt", {}).get("attempt_id")
        ):
            raise AssertionError(
                "installed strict Match resume was not a new durable wait: %s"
                % json.dumps(resumed_wait_receipt, sort_keys=True)
            )

        batch_input = away / "wishes.txt"
        batch_input.write_text(
            "a checkers set shaped by our mountain memories\n"
            "a tiny hand-cranked creature for my desk\n",
            encoding="utf-8",
        )
        batch = _json_command(
            (
                workshop,
                "batch",
                "submit",
                batch_input,
                "--draft",
                "--json",
            ),
            cwd=away,
            environment=environment,
        )
        if batch.get("count") != 2 or batch.get("status") != "ready":
            raise AssertionError("installed batch did not stage every exact Wish")
        batch_status = _json_command(
            (
                workshop,
                "batch",
                "status",
                batch["batch_id"],
                "--json",
            ),
            cwd=away,
            environment=environment,
        )
        if (
            batch_status.get("plan_sha256") != batch.get("plan_sha256")
            or [item["position"] for item in batch_status.get("items", [])]
            != [1, 2]
        ):
            raise AssertionError("installed batch status lost its exact saved plan")
        resumed_batch = _json_command(
            (
                workshop,
                "batch",
                "resume",
                batch["batch_id"],
                "--concurrency",
                "2",
                "--json",
            ),
            cwd=away,
            environment=environment,
        )
        if (
            resumed_batch.get("plan_sha256") != batch.get("plan_sha256")
            or resumed_batch.get("status") != "needs-attention"
            or [
                item.get("launch", {}).get("status")
                for item in resumed_batch.get("items", [])
            ]
            != ["succeeded", "succeeded"]
            or [
                item.get("status", {}).get("job")
                for item in resumed_batch.get("items", [])
            ]
            != ["invent", "invent"]
        ):
            raise AssertionError(
                "installed batch resume did not run the exact wheel module: %s"
                % json.dumps(resumed_batch, sort_keys=True)
            )

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
                    "from inventor_workshop._package_data import "
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
                    "from inventor_workshop._package_data import "
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
                    "from inventor_workshop._package_data import "
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
    repository = Path(__file__).resolve().parents[1]
    if args.wheel is not None:
        acceptance(args.wheel.resolve(strict=True))
    else:
        with tempfile.TemporaryDirectory(prefix="workshop-wheel-build-") as temporary:
            acceptance(_build_wheel(repository, Path(temporary)))
    print("installed-wheel-cli: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
