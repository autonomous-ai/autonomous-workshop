"""cadgen accepts the optional `instance` keyword make_round's issue #80 path
builds (`gen_step(instance=N)`), and still refuses every other argument."""
import importlib.util
import sys
from pathlib import Path

import pytest

METADATA = (Path(__file__).resolve().parents[2]
            / "src/workshop/make/skills/cad/scripts/packages/cadgen/src/cadgen/metadata.py")


def metadata_module():
    spec = importlib.util.spec_from_file_location("test_vendored_cadgen_metadata", METADATA)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def entry(tmp_path: Path, signature: str) -> Path:
    path = tmp_path / "part_shell.step.py"
    path.write_text(
        "from build123d import Box\n\n"
        f"def gen_step({signature}):\n"
        "    return Box(10, 10, 10)\n",
        encoding="utf-8")
    return path


@pytest.mark.parametrize("signature", ["", "instance=1", "*, instance=None", "*, instance=1"])
def test_no_argument_or_optional_keyword_instance_is_a_generator(tmp_path, signature):
    metadata = metadata_module().parse_generator_metadata(entry(tmp_path, signature))
    assert metadata is not None and metadata.has_gen_step


@pytest.mark.parametrize("signature, message", [
    ("*, instance", "must not require arguments"),
    ("instance=1, /", "must not require arguments"),
    ("instance", "must not require arguments"),
    ("size", "must not require arguments"),
    ("*, size=1", "must not require arguments"),
    ("*, instance=None, size=1", "must not require arguments"),
    ("*args", "must not accept variadic arguments"),
    ("**kwargs", "must not accept variadic arguments"),
])
def test_any_other_argument_is_refused(tmp_path, signature, message):
    with pytest.raises(ValueError, match=message):
        metadata_module().parse_generator_metadata(entry(tmp_path, signature))
