"""Export named, bed-oriented production solids from the same part builders."""
from pathlib import Path
import hashlib
import json
import shutil
import re
from build123d import export_step, import_step
from periastra_lib import build_base, build_roof, build_counter

# build123d's export_step stamps the wall clock into the STEP header, which makes
# otherwise identical geometry hash differently on every run. cadgen zeroes it; do
# the same here so a delivered part's sha256 identifies its geometry, not its date.
STAMP = re.compile(r"(FILE_NAME\('[^']*',')[^']*(')")


def export_deterministic(shape, path):
    export_step(shape, path)
    path.write_text(STAMP.sub(r"\g<1>1970-01-01T00:00:00\g<2>", path.read_text(), count=1))

def main():
    cad = Path(__file__).resolve().parent
    root = cad.parent
    package = cad / '__cadgen__/models/periastra.step.py/assembly.json'
    occurrences = json.loads(package.read_text())['occurrences']
    shapes = {'base': build_base(), 'roof': build_roof(),
              'single': build_counter(False), 'forked': build_counter(True)}
    parts = root / 'parts'
    parts.mkdir(exist_ok=True)
    rows = []
    for occurrence in occurrences:
        name = occurrence['name']
        shape = shapes[name.split('_')[0]]
        shape.label = name
        path = parts / f'{name}.step'
        export_deterministic(shape, path)
        actual = import_step(path)
        assert len(actual.solids()) == 1, name
        bounds = actual.bounding_box()
        assert abs(bounds.min.Z) < 1e-6, name
        assert max(bounds.size.X, bounds.size.Y) <= 220, name
        rows.append({'name': name, 'path': str(path.relative_to(root)),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'solids': 1, 'bounds_mm': list(bounds.size),
                     'bed_z_mm': bounds.min.Z, 'srgb': occurrence['color'][:3]})
    assert len(rows) == 26
    shutil.copyfile(cad / 'periastra.step', root / 'assembled.step')
    shutil.copyfile(package, root / 'assembled.step.json')
    (cad / 'measure/production-inventory.json').write_text(json.dumps(rows, indent=2)+'\n')
    print('PASS: 26 named one-solid production STEP files, all bed-oriented; delivery assembly copied.')

if __name__ == '__main__':
    main()
