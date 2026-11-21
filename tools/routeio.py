"""Load a route file (tools/example_route.py format: a Python module with ROUTE and a docstring).

Route files are Python and run as code: only load routes you wrote or reviewed.
"""

import importlib.util


def load_module(path):
    spec = importlib.util.spec_from_file_location("route", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_route(path):
    return load_module(path).ROUTE
