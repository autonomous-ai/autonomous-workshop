#!/usr/bin/env python3
"""doctor.py must run to completion on any machine and tell the truth about it.

    python3 tests/test_doctor.py
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def case(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  <- {detail}"))
    return ok


def main() -> int:
    r = []
    # 1. on THIS machine, the rules half must be green or the doctor is lying
    p = subprocess.run([sys.executable, str(HERE / "doctor.py"), "--phase", "discover,1"],
                       capture_output=True, text=True, timeout=300)
    r.append(case("doctor runs and reports on discover+1",
                  "text2game doctor" in p.stdout and "providers:" in p.stdout,
                  p.stdout[-300:] + p.stderr[-300:]))
    # 2. a deliberately broken machine view must exit 1 and name the gap
    env = dict(os.environ, TEXT2CAD_DIR="/nonexistent/text2cad",
               TEXT2CAD_PY="/nonexistent/python")
    p2 = subprocess.run([sys.executable, str(HERE / "doctor.py"), "--phase", "2"],
                        capture_output=True, text=True, timeout=300, env=env)
    r.append(case("a missing text2cad checkout is MISSING, not opt",
                  p2.returncode == 1 and "TEXT2CAD_DIR = /nonexistent/text2cad" in p2.stdout
                  and "MISSING" in p2.stdout, p2.stdout[-400:]))
    r.append(case("the fix line names the clone command",
                  "git clone https://github.com/nohope88/text2cad.git" in p2.stdout))
    # 3. unknown phase is a usage error, not a crash
    p3 = subprocess.run([sys.executable, str(HERE / "doctor.py"), "--phase", "9"],
                        capture_output=True, text=True, timeout=60)
    r.append(case("unknown phase exits 2", p3.returncode == 2, p3.stdout[-200:]))
    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
