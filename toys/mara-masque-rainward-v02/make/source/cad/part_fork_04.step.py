"""Printable occurrence fork_04; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=drop("fork").moved(__import__("build123d").Location())
    result.label="fork_04"
    return result
