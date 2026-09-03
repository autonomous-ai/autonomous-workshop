"""Export exact low and 65-degree CAD states for canonical rendering."""
from build123d import export_stl
from pearlturn_lib import build_assembly, VAULT_DEG

export_stl(build_assembly(0.0), "state-low.stl", tolerance=0.03, angular_tolerance=0.08)
export_stl(build_assembly(VAULT_DEG), "state-tall.stl", tolerance=0.03, angular_tolerance=0.08)
