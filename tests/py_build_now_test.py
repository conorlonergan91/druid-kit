"""tools/build_now.py checks travel with the save's flights (--state), so a known chain is not a false error."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from expect import check, done
from wowenv import ROOT

tmp = Path(tempfile.mkdtemp())
(tmp / "route.py").write_text(
    'ROUTE = {"id": "r1", "sections": [{"title": "T", "steps": ['
    '{"do": "fly", "where": "Stormwind flight master", "to": "Menethil"}]}]}\n',
    encoding="utf-8",
)
shutil.copy(ROOT / "tools/example_guide.json", tmp / "guide.json")
flights = ["Stormwind, Elwynn", "Ironforge, Dun Morogh", "Menethil Harbor, Wetlands"]
(tmp / "state.json").write_text(json.dumps({"travel": {"home": "Stormwind", "flights": flights}}), encoding="utf-8")


def build(*extra):
    args = [sys.executable, str(ROOT / "tools/build_now.py"), str(tmp / "route.py"), str(tmp / "guide.json"), "now"]
    return subprocess.run([*args, "You", *extra], capture_output=True, text=True).stdout


out = build()
check("no flight Stormwind -> Menethil" in out and "WITHOUT the save's flights" in out, "no --state: says so", out)
out = build("--state", str(tmp / "state.json"))
check("no flight" not in out and "WITHOUT" not in out and "1 steps" in out, "--state: chain via Ironforge ok", out)
check(json.loads((tmp / "guide.json").read_text())["tabs"][0]["sections"][-1]["lines"] == ["You"], "You line", out)
done("py_build_now_test")
