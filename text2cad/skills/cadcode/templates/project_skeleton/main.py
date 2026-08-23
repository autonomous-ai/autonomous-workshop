"""Project entrypoint.

The runner imports this file with ``project_dir`` on ``sys.path`` and calls
``gen_step()`` to obtain the shape to export.

Order:
    1. Load params.
    2. Validate them — bad params fail loudly here, before geometry.
    3. Build the assembly.
    4. Return an envelope from ``gen_step()`` — the runner exports it as
       STL + STEP. The ``shape`` is a ``cq.Workplane`` / ``cq.Shape`` for a
       single solid, or a ``cq.Assembly`` for a multi-part design (see
       references/assembly.md); the optional ``warnings`` list carries soft
       `functional` checks (assembly feasibility) into validation.warnings.
"""

from __future__ import annotations

from params import Params
from validation import functional_warnings, validate_params
from assemblies.product import make_assembly


def gen_step():
    p = Params()
    validate_params(p)  # hard fit asserts — an impossible fit blocks the build
    # Soft `functional` warnings (assembly feasibility) ride alongside the shape:
    # the build still renders, and the functional-review loop drives them to
    # zero. See references/component-integration.md.
    return {"shape": make_assembly(p), "warnings": functional_warnings(p)}
