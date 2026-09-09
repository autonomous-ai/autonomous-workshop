"""Color-preserving exact-part STL presentation; VTK depth-buffered orthographic camera."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from cybercab_lib import assembly
from build123d import export_stl
import vtk
from PIL import Image
OUT=ROOT.parents[1]/'research'/'colored-final';OUT.mkdir(parents=True,exist_ok=True)
def render(kw,name,opened=False):
 model=assembly(**kw)
 ren=vtk.vtkRenderer();ren.SetBackground(.94,.95,.97)
 for i,p in enumerate(model.children):
  path=OUT/f'{name}-{i}.stl';export_stl(p,str(path),tolerance=.05,angular_tolerance=.1)
  reader=vtk.vtkSTLReader();reader.SetFileName(str(path));reader.Update()
  mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(reader.GetOutputPort())
  actor=vtk.vtkActor();actor.SetMapper(mapper)
  color=(.87,.27,.08) if p.label=='elastic' else ((.065,.07,.075) if 'wheel' in p.label or 'window' in p.label else (.67,.53,.31))
  actor.GetProperty().SetColor(*color);actor.GetProperty().SetAmbient(.35);actor.GetProperty().SetDiffuse(.65);actor.GetProperty().SetSpecular(.12)
  ren.AddActor(actor)
 win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(800,800);win.SetMultiSamples(8);win.AddRenderer(ren)
 cam=ren.GetActiveCamera();cam.SetPosition(290,-360,290);cam.SetFocalPoint(90,0,55 if opened else 30);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(110 if opened else 100)
 ren.ResetCameraClippingRange();win.Render()
 capture=vtk.vtkWindowToImageFilter();capture.SetInput(win);capture.ReadFrontBufferOff();capture.Update()
 writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/f'{name}.png'));writer.SetInputConnection(capture.GetOutputPort());writer.Write();win.Finalize()
render({},'held')
render(dict(body_shift=-4,body_lift=55,latch_deflection=1.9,angle=0),'relaxed',True)
render(dict(body_shift=-4,body_lift=55,latch_deflection=1.9,angle=-90),'wound',True)
Image.open(OUT/'held.png').convert('RGB').save(ROOT/'snap/iso.png')
sheet=Image.new('RGB',(2400,800),(240,242,247))
for i,n in enumerate(('relaxed','wound','held')): sheet.paste(Image.open(OUT/f'{n}.png').convert('RGB'),(800*i,0))
sheet.save(ROOT/'snap/signature.png')
print('Wrote exact-colored canonical hero/signature',flush=True)
