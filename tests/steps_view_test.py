"""Prev/Next look through the route without marking anything; Go points the arrow at the step you're looking at and
the route arrow comes back on arrival or with Now; the Vendor button always works and the bags message can be
turned off."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
FREE = 1
C_Container = { GetContainerNumFreeSlots = function(bag) return bag == 0 and FREE or 0 end }
function GetTime() return 1000 end
C_Map = C_Map or {}
C_Map.GetBestMapForUnit = function() return 1432 end
C_Map.GetPlayerMapPosition = function() return { GetXY = function() return 0.66, 0.66 end } end
function DruidKit_FindMap(z) return ({ ["Loch Modan"] = 1432 })[z] end
function DruidKit_MapYards() return 2758, 1840 end
DruidKitVendors = { { "Loch Modan", 64.8, 66.0, "Aldren Cordon", "Clothier", true } }
DruidKitRoute = { id = "v", sections = { { title = "S", steps = {
  { ["do"] = "note", text = "One", at = { "Loch Modan", 10, 10 } },
  { ["do"] = "note", text = "Two", at = { "Loch Modan", 20, 20 } },
  { ["do"] = "note", text = "Three", at = { "Loch Modan", 30, 30 } },
} } } }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
R = {}
DruidKit_StepView(1); DruidKit_StepView(1)
R[#R+1] = DruidKitSteps.head.text
R[#R+1] = DruidKitSteps.main.text
R[#R+1] = DruidKitDB.routeStep
R[#R+1] = DruidKitDB.manual[1] == true
DruidKit_StepGo()
R[#R+1] = GOTO[#GOTO]
DruidKit_StepsEvaluate()
R[#R+1] = GOTO[#GOTO]            -- route arrow doesn't take over
DruidKit_StepView(0)
R[#R+1] = GOTO[#GOTO]            -- Now: back to step 1's spot
R[#R+1] = DruidKitSteps.head.text
DruidKit_StepView(-1)
R[#R+1] = DruidKitSteps.head.text  -- can't go before step 1
R[#R+1] = DruidKitSteps.detail.text
DruidKit_StepsCommand("vendorprompt")
DruidKit_StepsEvaluate()
R[#R+1] = DruidKitSteps.detail.text
DruidKit_StepsCommand("vendor")
R[#R+1] = GOTO[#GOTO]
""")
r = list(L.globals().R.values())
print(r)
check("Viewing 3/3 (you're on 1)" in str(r[0]) and "Three" in str(r[1]), "Next shows a later step", r[:2])
check(r[2] == 1 and r[3] is False, "looking ahead marks nothing done", r[2:4])
check(r[4] == "Loch Modan 30,30" and r[5] == "Loch Modan 30,30", "Go points at the viewed step and keeps it", r[4:6])
check(r[6] == "Loch Modan 10,10" and "Step 1/3" in str(r[7]), "Now returns to the current step and arrow", r[6:8])
check("Step 1/3" in str(r[8]), "Prev stops at the first step", r[8])
check("Aldren Cordon" in str(r[9]) and "Aldren Cordon" not in str(r[10]), "the bags message can be turned off", r[9:11])
check(r[11] == "Loch Modan 64.8,66", "the Vendor command still works with the message off", r[11])
done("steps_view_test")
