"""Printable occurrence die_1; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=die().moved(__import__("build123d").Location())
    result.label="die_1"
    return result
