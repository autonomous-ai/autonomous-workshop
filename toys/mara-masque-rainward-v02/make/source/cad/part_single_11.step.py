"""Printable occurrence single_11; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=drop("single").moved(__import__("build123d").Location())
    result.label="single_11"
    return result
