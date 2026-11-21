#!/bin/sh
# Runs every *_test.py against the addon sources with a mocked WoW API (needs: pip install lupa).
# Prints one line per test and exits non-zero if any test fails.
if [ -n "$DK_LIVE" ]; then DK_LIVE=$(cd "$DK_LIVE" && pwd) || exit 1; export DK_LIVE; fi
cd "$(dirname "$0")" || exit 1
out=$(mktemp)
failed=0
for t in *_test.py; do
  if timeout 60 python3 "$t" >"$out" 2>&1 && ! grep -q "FAIL" "$out"; then
    echo "ok   $t"
  else
    echo "FAIL $t"; tail -5 "$out"; failed=1
  fi
done
rm -f "$out"
exit $failed
