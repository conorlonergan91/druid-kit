"""Tiny assertion helper shared by the tests: prints a readable FAIL line and exits non-zero."""

import sys

_failures = 0


def check(cond, what, got=None):
    global _failures
    if cond:
        print(f"  pass  {what}")
    else:
        _failures += 1
        print(f"  FAIL  {what}" + (f"  (got: {got!r})" if got is not None else ""))


def done(name):
    if _failures:
        print(f"{name}: {_failures} FAIL")
        sys.exit(1)
    print(f"{name}: all checks passed")
