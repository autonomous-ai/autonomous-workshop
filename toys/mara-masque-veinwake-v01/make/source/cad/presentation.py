"""Generate exact auxiliary states; no extra buildable entry or printed part."""
from pathlib import Path
from build123d import export_step
from veinwake_lib import make_assembly

def write_states():
    out=Path(__file__).resolve().parents[2]/'presentation/states'
    out.mkdir(parents=True,exist_ok=True)
    for name in ('before','after'):
        export_step(make_assembly(name),out/f'{name}.step')

if __name__ == '__main__':
    write_states()
