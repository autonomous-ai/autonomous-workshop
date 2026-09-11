"""Independent placed copies for assembly measurements."""

from copy import deepcopy


def placed_subtree_copy(shape, location):
    """Copy a selected node at an absolute pose without copying its ancestors.

    build123d's ``located`` deep-copies the anytree parent link along with the
    shape. An attached leaf therefore copies its entire assembly, and retains
    that copied parent for every subsequent motion sample. Seed the deepcopy
    memo at that boundary instead: selected children and their internal parent
    links are copied normally, while the selected root has no parent.

    The source tree is never detached or relocated, even if copying fails.
    Geometry, labels and other metadata retain build123d's deepcopy semantics.
    """
    if shape._wrapped is None:
        raise ValueError("Cannot locate an empty shape")
    parent = shape.parent
    memo = {} if parent is None else {id(parent): None}
    copied = deepcopy(shape, memo)
    # Color is inherited lazily through the same parent link. Read its stored
    # value: the public getter would populate the source's color cache.
    ancestor = parent
    while copied._color is None and ancestor is not None:
        copied._color = deepcopy(ancestor._color)
        ancestor = ancestor.parent
    return copied.locate(location)
