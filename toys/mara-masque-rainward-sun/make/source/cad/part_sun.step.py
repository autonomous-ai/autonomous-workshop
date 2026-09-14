"""Printable occurrence sun; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=sun().moved(__import__("build123d").Location())
    result.label="sun"
    return result
