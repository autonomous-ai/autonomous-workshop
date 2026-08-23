import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
loader = SourceFileLoader("t2c", "/root/text2cad/text2cad")
spec = importlib.util.spec_from_loader("t2c", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
m.load_env()
ok = m.render_fresh("arc-coil-blaster-prop", Path("/root/text2cad/out/arc-coil-blaster-prop"))
print("RENDER_FRESH:", "OK" if ok else "FAILED")
