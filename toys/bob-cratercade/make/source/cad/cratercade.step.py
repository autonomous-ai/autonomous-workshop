"""Cratercade assembled geometry; separate pieces are printed individually."""
from assemblies.product import build_product
PRINTABLE=False

def gen_step():
    return build_product()
