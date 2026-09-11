"""Exact world-placed appearance leaves without copying the assembly graph."""


def colored_leaves(shape, parent_location=None, inherited_color=None):
    """Yield detached geometry wrappers and effective colors in source order.

    Shape.moved() deep-copies Python attributes (including assembly parents),
    then replaces the copied geometry with the original wrapped.Moved result.
    Use that same non-mutating OCCT placement directly. The new wrapper has no
    parent/joint graph; the complete topology, local placement and orientation
    remain intact, including every solid in a bare compound leaf.
    """
    from build123d import Compound

    color = getattr(shape, "color", None)
    if color is None:
        color = inherited_color
    children = list(getattr(shape, "children", ()) or ())
    if children:
        location = shape.location
        if parent_location is not None:
            location = parent_location * location
        for child in children:
            yield from colored_leaves(child, location, color)
        return

    wrapped = shape.wrapped
    if wrapped is None:
        if parent_location is not None:
            raise ValueError("Cannot move an empty shape")
        placed = Compound()
    else:
        wrapped = (wrapped.Located(wrapped.Location()) if parent_location is None
                   else wrapped.Moved(parent_location.wrapped))
        placed = Compound.cast(wrapped)
    placed.label = getattr(shape, "label", "")
    placed.color = color
    yield placed, color
