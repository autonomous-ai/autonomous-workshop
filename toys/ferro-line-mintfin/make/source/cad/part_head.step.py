"""Printable Mintfin head, flat at Z0; shared source revision1."""
from head_faces import head
PRINTABLE = True

def gen_step():
    return head()
