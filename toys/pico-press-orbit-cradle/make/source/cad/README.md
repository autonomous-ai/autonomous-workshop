# Orbit Cradle CAD source

`assembled.step.py` is the single combined and printable entry for this CAD
project. It is self-contained so the host can copy this directory in isolation
and run the fresh export and strict-fit verification pipeline without an
explicit `--assembly` override.

Generated STEP, STL, GLB, descriptors, and the verification report are derived
from that entry. The canonical reviewed presentation images and their blind
review are under `snap/`.
