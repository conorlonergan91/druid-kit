"""Bags filling up: the step window and chat name the nearest vendor; /dk steps vendor points the arrow there and
the route arrow comes back on arrival. make_guide writes the vendor list."""

import json
import sys
import tempfile
from pathlib import Path

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, ROOT, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
FREE = 10
C_Container = { GetContainerNumFreeSlots = function(bag) return bag == 0 and FREE or 0 end }
function GetTime() return 1000 end
C_Map = C_Map or {}
C_Map.GetBestMapForUnit = function() return 1432 end
C_Map.GetPlayerMapPosition = function() return { GetXY = function() return 0.66, 0.66 end } end
function DruidKit_FindMap(z) return ({ ["Loch Modan"] = 1432, ["Wetlands"] = 1437 })[z] end
function DruidKit_MapYards() return 2758, 1840 end
DruidKitVendors = {
  { "Loch Modan", 34.8, 48.6, "Yanni Stoutheart", "General Supplies", false },
  { "Loch Modan", 64.8, 66.0, "Aldren Cordon", "Clothier", true },
  { "Wetlands", 10.0, 60.0, "Far Away", "", false },
}
DruidKitRoute = { id = "v", sections = { { title = "S", steps = {
  { ["do"] = "goto", text = "Walk somewhere", to = "Nowhere", at = { "Loch Modan", 70.8, 22.8 } },
} } } }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("PLAYER_LOGIN")
R = {}
R[#R+1] = DruidKitSteps.detail.text or ""
FREE = 2; printed = {}; fire("BAG_UPDATE_DELAYED")
R[#R+1] = DruidKitSteps.detail.text
R[#R+1] = printed[#printed] or ""
DruidKit_StepsCommand("vendor")
R[#R+1] = GOTO[#GOTO]
DruidKit_StepsEvaluate()
R[#R+1] = GOTO[#GOTO]                 -- route arrow does not take over before you arrive
DruidKit_OnArrive("Vendor")
R[#R+1] = GOTO[#GOTO]                 -- back to the route
R[#R+1] = DruidKitDB.routeStep        -- arriving at the vendor doesn't tick the goto step
""")
r = list(L.globals().R.values())
print(r)
check("BAGS" not in str(r[0]), "no bag line while there's room", r[0])
check(
    "BAGS: 2 free" in str(r[1]) and "Aldren Cordon" in str(r[1]) and "repairs too" in str(r[1]),
    "low bags: the step window names the nearest vendor in this zone",
    r[1],
)
check("Aldren Cordon" in str(r[2]), "and says it in chat", r[2])
check(r[3] == "Loch Modan 64.8,66", "/dk steps vendor points the arrow at the vendor", r[3])
check(r[4] == "Loch Modan 64.8,66", "the route arrow waits until you reach the vendor", r[4])
check(r[5] == "Loch Modan 70.8,22.8" and r[6] == 1, "after the vendor the arrow goes back to the step", r[5:])

sys.path.insert(0, str(ROOT / "tools"))
import make_guide  # noqa: E402

tmp = Path(tempfile.mkdtemp())
g = json.loads((ROOT / "tools" / "example_guide.json").read_text(encoding="utf-8"))
g["vendors"] = [["Loch Modan", 64.8, 66.0, "Aldren Cordon", "Clothier", True]]
(tmp / "g.json").write_text(json.dumps(g), encoding="utf-8")
make_guide.main(str(tmp / "g.json"), str(tmp / "G.lua"))
G = LuaRuntime()
G.execute((tmp / "G.lua").read_text(encoding="utf-8"))
v = G.globals().DruidKitVendors[1]
check(v[4] == "Aldren Cordon" and v[6] is True, "make_guide writes DruidKitVendors", list(v.values()))
done("vendor_test")
