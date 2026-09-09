"""Project-specific dimensional, connector and assembly service fit audit."""
import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'check_spec.py'),run_name='__main__')
runpy.run_path(str(p/'check_landmarks.py'),run_name='__main__')
runpy.run_path(str(p/'check_service.py'),run_name='__main__')
print('PASS project base dimensions, axle/journal connectors, latch and assembly order')
