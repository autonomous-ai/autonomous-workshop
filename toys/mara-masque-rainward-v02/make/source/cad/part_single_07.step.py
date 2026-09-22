"""Printable occurrence single_07; flat base at Z=0."""
from rainward_lib import sun, drop, die, cup
PRINTABLE = True

def gen_step():
    result=drop("single").moved(__import__("build123d").Location())
    result.label="single_07"
    return result
