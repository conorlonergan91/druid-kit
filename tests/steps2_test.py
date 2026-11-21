"""Skip, hide/show with the arrow, deaths -> struggling advice, and the projected-vs-actual log."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
NAVCLEARED = 0
function DruidKit_NavTarget() return true end
function DruidKit_NavClear() NAVCLEARED = NAVCLEARED + 1 end
DruidKitRoute = { id = "t2", sections = { { title = "Redridge", steps = {
  { ["do"] = "accept", q = 20, name = "Blackrock Menace", npc = "Marris", at = { "Redridge Mountains", 28.4, 49 } },
  { ["do"] = "complete", q = 20, name = "Blackrock Menace", est = 10, party = true, at = { "Redridge Mountains", 59, 53 } },
  { ["do"] = "turnin", q = 20, name = "Blackrock Menace", npc = "Marris" },
  { ["do"] = "accept", q = 92, name = "Goulash", npc = "Breanna" },
} } } }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
ev = nil
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
function cur() return DruidKitDB.routeStep end
fire("PLAYER_LOGIN")
R = {}
LOG[20] = { title = "Blackrock Menace", done = false }; fire("QUEST_LOG_UPDATE")
R[#R+1] = cur()
fire("PLAYER_DEAD"); fire("PLAYER_DEAD")
R[#R+1] = DruidKitDB.cur.deaths
DruidKit_StepsEvaluate()
R[#R+1] = DruidKitSteps.detail.text
DruidKit_StepSkip()
R[#R+1] = cur()
R[#R+1] = DruidKitDB.skipQ[20] and DruidKitDB.skipQ[20].deaths or -1
R[#R+1] = DruidKitDB.stepLog[#DruidKitDB.stepLog].how
DruidKit_ToggleSteps(false)
R[#R+1] = DruidKitSteps:IsShown()
R[#R+1] = NAVCLEARED
R[#R+1] = DruidKitStepsShow:IsShown()
DruidKit_ToggleSteps(true)
R[#R+1] = DruidKitSteps:IsShown()
DruidKit_StepsCommand("unskip")
R[#R+1] = cur()
C_QuestLog.GetLogIndexForQuestID = C_QuestLog.GetLogIndexForQuestID or function(q) return LOG[q] and 1 or nil end
function SelectQuestLogEntry() end
function GetQuestLogQuestText() return "desc", "Raise the banner you found in the cave to call out Headsplitter." end
DruidKit_StepsEvaluate()
R[#R+1] = DruidKitSteps.detail.text
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 2, "on the kill step", r[0])
check(r[1] == 2, "deaths counted on the current step", r[1])
check("Struggling" in str(r[2]) and "LFG" in str(r[2]), "2 deaths -> struggling advice with group-up", r[2])
check(r[3] == 4, "Skip leaves every step of that quest", r[3])
check(r[4] == 2 and r[5] == "skipped", "skip recorded with deaths for the re-plan", r[4:6])
check(
    r[6] is False and r[7] >= 1 and r[8] is True, "Hide hides steps, clears the arrow, shows the Route button", r[6:9]
)
check(r[9] is True, "Route/Alt+N shows it again", r[9])
check(r[10] == 2, "unskip puts the quest back", r[10])
check("Quest says: Raise the banner" in str(r[11]), "kill steps show the quest's own how-to text", r[11])
done("steps2_test")
