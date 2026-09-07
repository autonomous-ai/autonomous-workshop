"""Exercise Release with the canonical interpreter used by native runs."""

import os
from pathlib import Path
import subprocess
import sys
import sysconfig

import pytest

from tests.workflow.test_stage_proposal_tool import TOOL, manual_pdf


def invoke_pdf_checker(tmp_path, package_root, content=None):
    python = str(Path(sys.executable).resolve())
    environment = {
        "PATH": os.defpath,
        "WORKSHOP_PYTHON": python,
        "PYTHONPATH": package_root,
    }
    return subprocess.run(
        [
            python, "-I", "-B", "-c",
            "import runpy,sys; tool=runpy.run_path(sys.argv[1]); "
            "tool['_validate_pdf_manual'](sys.stdin.buffer.read())",
            str(TOOL),
        ],
        input=manual_pdf() if content is None else content,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        timeout=30,
    )


def test_canonical_python_pdf_worker_keeps_dependencies_and_isolation(tmp_path):
    # Neither local modules nor .pth processing may be enabled by the override.
    (tmp_path / "pypdf.py").write_text("raise RuntimeError('local module imported')")
    result = invoke_pdf_checker(tmp_path, str(Path(sysconfig.get_path("purelib")).resolve()))
    assert result.returncode == 0, result.stderr.decode()


@pytest.mark.parametrize("package_root", [".", "/tmp:/usr/lib", "/tmp"])
def test_pdf_worker_refuses_broad_or_relative_dependency_paths(tmp_path, package_root):
    result = invoke_pdf_checker(tmp_path, package_root)
    assert result.returncode != 0
    assert b"PDF package directory" in result.stderr


def test_canonical_python_pdf_worker_still_rejects_malformed_pdf(tmp_path):
    result = invoke_pdf_checker(
        tmp_path, str(Path(sysconfig.get_path("purelib")).resolve()), b"%PDF-1.7\n%%EOF"
    )
    assert result.returncode != 0
    assert b"Release MANUAL.pdf" in result.stderr
