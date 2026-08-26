"""Where ABO's imported harness finds this repository, and on what printer.

The tree under ``harness/`` came from another repository and still believes it
lives there: it resolves a repository root two directories above itself, looks
for an interpreter in a ``.venv`` beside that root, and carries a bed envelope
that disagrees with the printer its own documentation names.  None of that is
edited in place — the vendored bytes are locked by ``snapshots.lock.json`` and
proved on every check.  It is corrected here instead, in ABO's own code, by
rebinding the module constants the harness reads at call time.

See `UPSTREAM.md` and design decision D7.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


INVENTOR_ROOT = Path(__file__).resolve().parent
HARNESS_ROOT = INVENTOR_ROOT / "harness"
AGENTS_ROOT = INVENTOR_ROOT / "agents"

# Bambu Lab P2S.  Upstream `gate.py` states the envelope three times over: a
# 256 mm nominal constant, a 5 mm margin subtracted from it, and the literal
# string "246x246x251" passed to `check_mesh`.  The three agree today, which is
# precisely why a printer change would break them apart silently — and a bed
# constant that has drifted from the bed only shows up at Deliver.  ABO states
# the usable envelope once, here, and every bed-fit measurement reads it.
PRINTER_NAME = "Bambu Lab P2S"
BED_X_MM = 246.0
BED_Y_MM = 246.0
BED_Z_MM = 251.0

# ABO-scoped names for the model-seat endpoint.  Upstream reads the unscoped
# `PLAYTEST_*` names from a repository `.env`; here they are read through the
# Workshop's own `load_dotenv`, under names that say which inventor they
# belong to, so two inventors can hold two endpoints without collision.
ENV_MODEL_SEAT_BASE_URL = "ABO_PLAYTEST_BASE_URL"
ENV_MODEL_SEAT_API_KEY = "ABO_PLAYTEST_API_KEY"
ENV_MODEL_SEAT_MODEL = "ABO_PLAYTEST_MODEL"
MODEL_SEAT_ENV_NAMES = (
    ENV_MODEL_SEAT_BASE_URL,
    ENV_MODEL_SEAT_API_KEY,
    ENV_MODEL_SEAT_MODEL,
)


class ConfigurationError(RuntimeError):
    """The harness cannot be pointed at this repository."""


def workshop_root() -> Path:
    """The repository root that owns the locked CAD skill.

    Resolved by looking for the locked skill rather than by counting parent
    directories, so moving the inventor deeper or shallower does not silently
    repoint the gate at nothing.
    """

    for candidate in (INVENTOR_ROOT, *INVENTOR_ROOT.parents):
        if (candidate / "skills" / "cad" / "scripts" / "verify_project").is_file():
            return candidate
    raise ConfigurationError(
        "cannot locate this repository's locked skills/cad above %s; ABO builds "
        "through the locked skill and never vendors a second copy"
        % INVENTOR_ROOT
    )


def cad_scripts_root() -> Path:
    return workshop_root() / "skills" / "cad" / "scripts"


def interpreter() -> Path:
    """The interpreter already running us.

    Upstream prefers a `.venv/bin/python` beside its repository root.  There is
    no such directory here and inventing one would run the gate under an
    interpreter nobody chose.
    """

    return Path(sys.executable)


def usable_bed_mm() -> tuple:
    return (BED_X_MM, BED_Y_MM, BED_Z_MM)


def install_harness_paths(gate_module) -> None:
    """Rebind the imported gate's repository, interpreter, and bed constants.

    Every one of these is read inside a function body at call time, so
    rebinding the module attribute is enough and no vendored line changes.
    """

    root = workshop_root()
    gate_module.ROOT = root
    gate_module.PYTHON = interpreter()
    gate_module.CAD = cad_scripts_root()
    gate_module.BUDGET = gate_module.CAD / "with_budget"
    gate_module.BED_X_MM = BED_X_MM
    gate_module.BED_Y_MM = BED_Y_MM
    gate_module.BED_Z_MM = BED_Z_MM
    # `BED` is computed once at import from the nominal size and a margin.
    # ABO configures the usable envelope directly, so the margin is already
    # in the numbers above and must not be subtracted a second time.
    gate_module.BED_MARGIN_MM = 0.0
    gate_module.BED = usable_bed_mm()


def load_harness(name: str):
    """Import one vendored harness module by path, under a namespaced name.

    Never `import playtest`. The harness carries modules whose bare names —
    `playtest`, `gate`, `preview` — are ordinary enough to collide with ABO's
    own, with each other's, and with the standard library, and a collision here
    would silently hand a vendored file the wrong module. Loading by explicit
    file location under an `abo_harness_` prefix removes the question.

    The one exception is `table_run`, which inserts its own directory at the
    front of `sys.path` and then does `import playtest` itself. That resolves to
    the vendored file because its own directory wins, and it is left alone.
    """

    import importlib.util
    import sys

    module_name = "abo_harness_%s" % name
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = HARNESS_ROOT / ("%s.py" % name)
    if not path.is_file():
        raise ConfigurationError("the imported harness has no module %r" % name)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ConfigurationError("cannot load the imported harness module %r" % name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        del sys.modules[module_name]
        raise
    if name == "gate":
        install_harness_paths(module)
    return module


def load_model_seat_environment(dotenv_path: Optional[str] = None) -> dict:
    """Read the model-seat endpoint through the Workshop's own loader.

    Returns whichever of the three settings are configured.  A real environment
    variable always wins over the file, and a missing file is not an error —
    Playtest turns an absent endpoint into a typed `Need`, never into a
    scripted stand-in.
    """

    from inventor_workshop.env import load_dotenv

    load_dotenv(dotenv_path)
    found = {}
    for name in MODEL_SEAT_ENV_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            found[name] = value
    return found


def missing_model_seat_settings(dotenv_path: Optional[str] = None) -> tuple:
    configured = load_model_seat_environment(dotenv_path)
    return tuple(name for name in MODEL_SEAT_ENV_NAMES if name not in configured)


__all__ = [
    "AGENTS_ROOT",
    "BED_X_MM",
    "BED_Y_MM",
    "BED_Z_MM",
    "ConfigurationError",
    "ENV_MODEL_SEAT_API_KEY",
    "ENV_MODEL_SEAT_BASE_URL",
    "ENV_MODEL_SEAT_MODEL",
    "HARNESS_ROOT",
    "INVENTOR_ROOT",
    "MODEL_SEAT_ENV_NAMES",
    "PRINTER_NAME",
    "cad_scripts_root",
    "install_harness_paths",
    "interpreter",
    "load_harness",
    "load_model_seat_environment",
    "missing_model_seat_settings",
    "usable_bed_mm",
    "workshop_root",
]
