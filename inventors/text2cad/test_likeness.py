import importlib.util, json
from importlib.machinery import SourceFileLoader
from pathlib import Path
loader = SourceFileLoader("t2c", "/root/text2cad/text2cad")
spec = importlib.util.spec_from_loader("t2c", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
m.load_env()
out_dir = Path("/root/text2cad/out/arc-coil-blaster-prop")
run_log = json.loads((out_dir / "run.json").read_text())
r = m.run_phase("lens-likeness", m.lens_prompt("arc-coil-blaster-prop", out_dir, "likeness"),
                out_dir, 20, run_log, timeout_s=2400)
print("FINAL VERDICT:", m.lens_verdict(out_dir, "likeness", r, None))
