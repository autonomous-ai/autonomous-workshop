#!/usr/bin/env python3
"""
render_views.py — offscreen triage renders of a STEP solid, two complementary sets
in ONE pass (one process, one STEP import):

    python render_views.py model.step out_prefix
    # 6 tilted-iso  : out_prefix_iso_{front,back,left,right,top,bottom}.png
    # 6 orthographic: out_prefix_ortho_{FRONT_-Y,BACK_+Y,LEFT_-X,RIGHT_+X,TOP_+Z,BOTTOM_-Z}.png

WHY RENDER. Metrics tell you *that* a rebuild is wrong and roughly where; a picture
tells you *what* it is. The biggest recovery mistakes are mental-model errors
(reconstructing a threaded collar as a smooth dome, an arched cutout as a gabled
one). A render at triage — BEFORE hypothesizing features — catches those in seconds;
rendering each rebuild confirms gross shape alongside the numeric gate.

WHY TWO SETS. They answer different questions, so we emit both every run (they share
the expensive STEP import and tessellation, so the second set is nearly free):

  - ISO (6 tilted ~25 deg off-axis, perspective): the GESTALT. A straight head-on
    view hides all depth along the view axis — a bottle and a flat disk look
    identical. The tilt keeps "which side am I looking at" framing while revealing
    depth. Use these to avoid gross "what is this thing" errors.

  - ORTHO (6 dead-on each +/-X/Y/Z axis, parallel projection, black feature-edge
    overlay): the GEOMETRY of a PRISMATIC / analytic part. A flat side view IS the
    profile you extrude; holes read through-vs-blind (clean circle vs filled); and a
    solid base plate under a webbed body — which the iso views hide as "hollow all the
    way down" — shows immediately in the dead-on BOTTOM view, so you scaffold it
    instead of discovering it later by sectioning. LEFT is the mirror of RIGHT, so
    symmetry is obvious. The feature-edge overlay is NOT optional: a flat shaded face
    is a featureless grey patch; the black sharp+boundary edges are what make the
    internal profile legible as a line drawing.

Uses cadquery's bundled VTK with offscreen rendering (no display needed).
"""
import sys
import cadquery as cq
from vtkmodules.vtkRenderingCore import (
    vtkRenderer, vtkRenderWindow, vtkPolyDataMapper, vtkActor,
    vtkWindowToImageFilter,
)
from vtkmodules.vtkFiltersCore import vtkFeatureEdges
from vtkmodules.vtkIOImage import vtkPNGWriter
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401  registers the GL backend


def render(step_path, prefix, size=900):
    shape = cq.importers.importStep(step_path).val()
    # fine tessellation so the ortho feature edges trace crisp outlines
    pd = shape.toVtkPolyData(0.05, 0.15)

    mapper = vtkPolyDataMapper()
    mapper.SetInputData(pd)
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.78, 0.78, 0.80)
    actor.GetProperty().SetInterpolationToFlat()

    # feature-edge overlay (sharp >30 deg + boundary edges, black). Shown only for the
    # ortho views; hidden for iso (where shading already conveys the 3/4 form).
    fe = vtkFeatureEdges()
    fe.SetInputData(pd)
    fe.BoundaryEdgesOn()
    fe.FeatureEdgesOn()
    fe.SetFeatureAngle(30)
    fe.ManifoldEdgesOff()
    fe.NonManifoldEdgesOff()
    fe.Update()
    em = vtkPolyDataMapper()
    em.SetInputConnection(fe.GetOutputPort())
    edge_actor = vtkActor()
    edge_actor.SetMapper(em)
    edge_actor.GetProperty().SetColor(0, 0, 0)
    edge_actor.GetProperty().SetLineWidth(2)

    ren = vtkRenderer()
    ren.AddActor(actor)
    ren.AddActor(edge_actor)
    ren.SetBackground(1, 1, 1)

    win = vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(size, size)

    b = shape.BoundingBox()
    cx, cy, cz = (b.xmin + b.xmax) / 2, (b.ymin + b.ymax) / 2, (b.zmin + b.zmax) / 2
    diag = (b.xlen ** 2 + b.ylen ** 2 + b.zlen ** 2) ** 0.5
    cam = ren.GetActiveCamera()

    def shoot(name):
        ren.ResetCamera()
        win.Render()
        w2i = vtkWindowToImageFilter()
        w2i.SetInput(win)
        w2i.Update()
        wr = vtkPNGWriter()
        wr.SetFileName(f"{prefix}_{name}.png")
        wr.SetInputConnection(w2i.GetOutputPort())
        wr.Write()
        print(f"wrote {prefix}_{name}.png", flush=True)

    # --- ISO: perspective, tilted ~25 deg off each axis, no edge overlay ---
    # ResetCamera rescales distance to fit, so only direction + view-up matter here.
    cam.ParallelProjectionOff()
    edge_actor.VisibilityOff()
    t = 0.5 * 1.8 * diag
    d = 1.8 * diag
    iso = {
        "iso_front":  ((cx + t, cy - d, cz + t), (0, 0, 1)),
        "iso_back":   ((cx - t, cy + d, cz + t), (0, 0, 1)),
        "iso_left":   ((cx - d, cy + t, cz + t), (0, 0, 1)),
        "iso_right":  ((cx + d, cy - t, cz + t), (0, 0, 1)),
        "iso_top":    ((cx + t, cy + t, cz + d), (0, 1, 0)),
        "iso_bottom": ((cx + t, cy + t, cz - d), (0, 1, 0)),
    }
    for name, (pos, up) in iso.items():
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(*pos)
        cam.SetViewUp(*up)
        shoot(name)

    # --- ORTHO: parallel projection, dead-on each axis, black edge overlay ---
    # Names encode the view axis so a feature maps back to coordinates.
    cam.ParallelProjectionOn()
    edge_actor.VisibilityOn()
    od = 3 * diag  # parallel proj: only direction matters; ResetCamera fits the frame
    ortho = {
        "ortho_FRONT_-Y":  ((cx, cy - od, cz), (0, 0, 1)),
        "ortho_BACK_+Y":   ((cx, cy + od, cz), (0, 0, 1)),
        "ortho_LEFT_-X":   ((cx - od, cy, cz), (0, 0, 1)),
        "ortho_RIGHT_+X":  ((cx + od, cy, cz), (0, 0, 1)),
        "ortho_TOP_+Z":    ((cx, cy, cz + od), (0, 1, 0)),
        "ortho_BOTTOM_-Z": ((cx, cy, cz - od), (0, 1, 0)),
    }
    for name, (pos, up) in ortho.items():
        cam.SetFocalPoint(cx, cy, cz)
        cam.SetPosition(*pos)
        cam.SetViewUp(*up)
        shoot(name)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
