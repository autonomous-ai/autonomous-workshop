#!/bin/bash
# Every test, one summary, one exit code — the pre-flight before a run.
#
# Sweeping tests/ by hand hid a failure once: test_render.py exits non-zero
# under plain python3 because its modules live in another interpreter, and
# `for t in tests/*.py; do python3 $t; done` shows that as a traceback in the
# middle of a wall of PASS. This reports per-file and fails loudly.
cd "$(dirname "$0")/.." || exit 2
fail=0; names=()
for t in tests/test_*.py; do
  out=$(python3 "$t" 2>&1); rc=$?
  line=$(echo "$out" | grep -E '^[0-9]+/[0-9]+ passed$|^SKIP ' | tail -1)
  if [ $rc -ne 0 ]; then
    printf 'FAIL  %-28s %s\n' "$(basename "$t")" "${line:-rc=$rc}"
    echo "$out" | tail -12 | sed 's/^/      /'
    fail=$((fail+1)); names+=("$(basename "$t")")
  else
    printf 'ok    %-28s %s\n' "$(basename "$t")" "${line:-rc=0}"
  fi
done
if [ $fail -ne 0 ]; then
  echo; echo "$fail file(s) FAILED: ${names[*]}"; exit 1
fi
echo; echo "all test files passed"
