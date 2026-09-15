"""Exact qualified catalog solids; craft axle uses its documented cut-stock spec."""
from functools import lru_cache
from pathlib import Path
import cadmount
from build123d import Solid
from OCP.BRepBuilderAPI import BRepBuilderAPI_NurbsConvert

REF=Path(__file__).resolve().parents[1]/'ref'

@lru_cache(maxsize=3)
def screw_csk():
    return cadmount.load(str(REF/'countersunk_socket_screw_m4_l0016_simple.step'))

@lru_cache(maxsize=3)
def screw_socket():
    return cadmount.load(str(REF/'iso4762_socket_head_cap_screw_m4x25.step'))

@lru_cache(maxsize=3)
def nut():
    catalog = cadmount.load(str(REF/'thin_jam_nut_m4_simple.step'))
    # Preserve the supplier solid while avoiding analytic plane/cone validity
    # failures after the inclined assembly transforms. Qualified against all
    # 199 actual placements and STEP reloads; supplier bytes remain unchanged.
    return Solid.cast(BRepBuilderAPI_NurbsConvert(catalog.wrapped, True).Shape())
