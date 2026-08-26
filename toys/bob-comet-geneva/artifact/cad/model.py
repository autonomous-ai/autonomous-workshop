#!/usr/bin/env python3
"""Rebuild this exact declarative CAD design through the shared Workshop tool."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

source = Path(__file__).resolve()
builder = next(
    (parent / "tools" / "build_showcase_products.py"
     for parent in source.parents
     if (parent / "tools" / "build_showcase_products.py").is_file()),
    None,
)
if builder is None:
    raise SystemExit("run this source inside an autonomous-workshop checkout")
spec = importlib.util.spec_from_file_location("showcase_product_builder", builder)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load the shared Workshop builder")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
destination = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else source.parent / "rebuilt"
module.rebuild_from_design(source.parent / "design.json", destination)
print(destination)
