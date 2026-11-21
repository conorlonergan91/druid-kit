"""Dungeon steps: boss steps show short tactics and tick when the boss dies; inside steps show the next boss."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
DruidKitRoute = { id = "boss", sections = { { title = "Dungeon", steps = {
  { ["do"] = "note", text = "Inside: steps in run order", inside = true, how = "Quest steps tick by themselves." },
  { ["do"] = "boss", name = "Saltspine", level = 28, inside = true, tactic = { "Pull onto the ledges.", "HoT the tank.", "Avoid Dust Storm." } },
  { ["do"] = "note", text = "After", inside = true },
} } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
R = { DruidKitSteps.detail.text }
DruidKitDB.manual[1] = true; DruidKit_StepsEvaluate()
R[2] = DruidKitDB.routeStep; R[3] = DruidKitSteps.main.text; R[4] = DruidKitSteps.detail.text
ev.on_OnEvent(ev, "ENCOUNTER_END", 1234, "Saltspine", 1, 5, 0)   -- a wipe: no tick
DruidKit_StepsEvaluate(); R[5] = DruidKitDB.routeStep
ev.on_OnEvent(ev, "ENCOUNTER_END", 1234, "Saltspine", 1, 5, 1)
DruidKit_StepsEvaluate(); R[6] = DruidKitDB.routeStep
-- no encounter event (not every boss has one): looting the dead boss as your target ticks it
DruidKitDB.bossKilled = nil; DruidKitDB.routeStep = 2; DruidKit_StepsEvaluate()
function UnitName(u) return u == "target" and "Saltspine" or "Me" end
function UnitIsDead(u) return u == "target" end
ev.on_OnEvent(ev, "LOOT_OPENED")
DruidKit_StepsEvaluate(); R[7] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check(
    "Next: Saltspine" in r[0] and "Pull onto the ledges" in r[0] and "HoT the tank" not in r[0],
    "inside step: next boss with its first tactic only",
    r[0],
)
check(r[1] == 2 and "Boss:" in r[2] and "Saltspine" in r[2], "boss step has its own look", r[2])
check(r[3].count("|cffff7040-|r") == 3, "boss step: the 3 tactic lines", r[3])
check(r[4] == 2, "a wipe does not tick the boss", r[4])
check(r[5] == 3, "the boss kill ticks the step", r[5])
check(r[6] == 3, "looting the dead boss (your target) ticks the step", r[6])
import re

from wowenv import ROOT

cleu = [
    f.name
    for f in (ROOT / "DruidKit").glob("*.lua")
    if re.search(r'RegisterEvent[^\n]*COMBAT_LOG_EVENT_UNFILTERED|"COMBAT_LOG_EVENT_UNFILTERED"', f.read_text())
]
check(not cleu, "no file registers the combat log (Forever blocks it: 'only available to the Blizzard UI')", cleu)
done("boss_test")
