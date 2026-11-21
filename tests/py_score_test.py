"""planner/eval/score.py: hearth binds read from every place field; planner/load_db.py: QuestieDB's Lua runs
without the Python bridge or OS libraries."""

import json
import os
import sys
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT

tmp = Path(tempfile.mkdtemp())
(tmp / "ref.json").write_text(json.dumps({"events": []}), encoding="utf-8")
(tmp / "pack.csv").write_text("id,name,zone,end_zone,level\n", encoding="utf-8")
os.environ["RK_REFERENCE"], os.environ["RK_PACK"] = str(tmp / "ref.json"), str(tmp / "pack.csv")
sys.path.insert(0, str(ROOT / "planner" / "eval"))
sys.path.insert(0, str(ROOT / "planner"))
import score  # noqa: E402

import load_db  # noqa: E402

binds = score.binds(
    [
        {"kind": "home", "at": "Auberdine"},
        {"kind": "home", "text": "Set hearth", "place": "Lakeshire"},
        {"kind": "home", "text": "Bind in Thelsamar"},
    ]
)
check(binds == {"auberdine", "lakeshire", "thelsamar"}, "home events bind at at/text/place", binds)

L = load_db.runtime()
err = L.globals().runchunk(
    "probe = { os = type(os.execute), io = type(io.open), py = type(python.eval), "
    "req = type(require), ls = type(loadstring), dof = type(dofile), pkg = type(package.loadlib) }",
    "probe",
)
probe = dict(L.globals().probe.items()) if L.globals().probe else err
check(isinstance(probe, dict) and "function" not in probe.values(), "no os/io/python/loaders for foreign Lua", probe)
check(L.globals().runchunk("x = 1 + 1", "ok") is None and L.globals().x == 2, "plain data code still runs", "")
done("py_score_test")
