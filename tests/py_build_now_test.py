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
    '{"do": "fly", "where": "Stormwind flight master", "to": "Menethil"},'
    '{"do": "note", "text": "Set hearth in Menethil"}]}]}\n',
    encoding="utf-8",
)
shutil.copy(ROOT / "tools/example_guide.json", tmp / "guide.json")
flights = ["Stormwind, Elwynn", "Ironforge, Dun Morogh", "Menethil Harbor, Wetlands"]


def state(name, data):
    (tmp / name).write_text(json.dumps(data), encoding="utf-8")
    return str(tmp / name)


known = state("state.json", {"travel": {"home": "Stormwind", "flights": flights, "flightsKnown": True}})
unseen = state("unseen.json", {"travel": {"home": "Stormwind", "flights": [], "flightsKnown": False}})
notravel = state("notravel.json", {"route": {}})


def build(*extra):
    args = [sys.executable, str(ROOT / "tools/build_now.py"), str(tmp / "route.py"), str(tmp / "guide.json"), "now"]
    return subprocess.run([*args, "You", *extra], capture_output=True, text=True).stdout


out = build()
check("no flight Stormwind -> Menethil" in out and "WITHOUT the save's flights" in out, "no --state: says so", out)
check("--home/--flights" in out, "no --state: hints at route_check with the save's travel", out)
out = build("--state", known)
check("no flight" not in out and "WITHOUT" not in out and "2 steps" in out, "--state: chain via Ironforge ok", out)
check(" notes" in out and "--home/--flights" not in out, "--state: no hint to pass what it already passed", out)
for name, path in (("no flight list yet (flights={})", unseen), ("no travel", notravel)):
    out = build("--state", path)
    check(
        "WITHOUT the save's flights" in out and "no flight Stormwind -> Menethil" in out,
        f"--state with {name}: flights unknown, says so",
        out,
    )
    check("--home/--flights" not in out, f"--state with {name}: no route_check hint", out)
check(json.loads((tmp / "guide.json").read_text())["tabs"][0]["sections"][-1]["lines"] == ["You"], "You line", out)
done("py_build_now_test")
