"""The combined entry of this workspace: ``gen_step()`` returns the object.

This placeholder is a 20 mm cube standing on the bed. Replace the body of
``gen_step()`` with the object the user asked for; keep the file name
``model.step.py`` -- Harness's 3D pane follows its sibling ``model.step``.
"""

from build123d import Align, Box


def gen_step():
    cube = Box(20, 20, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cube.label = "cube"
    return cube
