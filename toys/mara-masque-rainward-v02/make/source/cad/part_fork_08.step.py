"""Printable occurrence fork_08; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=drop("fork").moved(__import__("build123d").Location())
    result.label="fork_08"
    return result
