"""Unskip a skipped quest from the step window; rewards are chosen even with no guide pick and on early hand-ins."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, runtime, source

# 1. Bags: reward pick = best upgrade, else highest sell price.
B = runtime("ui")
B.execute("UISpecialFrames={}")
B.execute(source("DruidKit/DruidKit_Style.lua"))
B.execute(source("DruidKit/DruidKit_Bags.lua"))
B.execute(r"""
QCH = { "mail", "robe", "boots" }
function GetQuestItemLink(k, i) return QCH[i] end
R = { DruidKit_RewardPick(3) }
QCH = { "mail", "grey" }
R2 = { DruidKit_RewardPick(2) }
""")
g = B.globals()
check(g.R[1] == 2, "reward pick takes the upgrade (robe), not mail", list(g.R.values()))
check(g.R2[1] == 1, "no upgrade: takes the one that sells for the most", list(g.R2.values()))

# 2. Steps: skip, then < Prev to it and Unskip; early hand-in with no pick still chooses.
SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
LOG = { [89] = { title = "The Everstill Bridge" }, [92] = { title = "Redridge Goulash" } }
DruidKitRoute = { id = "u1", sections = { { title = "S", steps = {
  { ["do"] = "complete", q = 89, name = "The Everstill Bridge", at = { "Redridge Mountains", 19.0, 28.9 } },
  { ["do"] = "complete", q = 92, name = "Redridge Goulash", at = { "Redridge Mountains", 48.1, 42.1 } },
  { ["do"] = "note", text = "later" },
  { ["do"] = "note", text = "later 2" },
  { ["do"] = "note", text = "later 3" },
  { ["do"] = "note", text = "later 4" },
  { ["do"] = "turnin", q = 89, name = "The Everstill Bridge", at = { "Redridge Mountains", 27.1, 48.6 } },
} } } }
DruidKitDB = {}
DruidKit_RewardPick = function(n) return 2, "best upgrade for you" end
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("PLAYER_LOGIN")
R = {}
DruidKit_StepSkip()
R[1] = DruidKitDB.routeStep                         -- 2: Everstill skipped
DruidKit_StepView(-1)
R[2] = tostring(DruidKitSteps.skipBtn and DruidKitSteps.skipBtn.text)              -- "Unskip" on the skipped step
DruidKit_StepSkip()
R[3] = DruidKitDB.routeStep                         -- back to 1
R[4] = DruidKitDB.skipQ[89] == nil
R[5] = tostring(DruidKitSteps.skipBtn and DruidKitSteps.skipBtn.text)
-- hand in Everstill early (route is on step 1, hand-in is step 7), no pick in the route
CURQ = 89; CURTITLE = "The Everstill Bridge"; CHOICES = { "Axe", "Robe" }
fire("QUEST_PROGRESS"); fire("QUEST_COMPLETE")
R[6] = REWARD
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 2, "Skip moves on", r[0])
check(r[1] == "Unskip", "the skipped step shows Unskip", r[1])
check(r[2] == 1, "Unskip brings the route back to the quest", r[2])
check(r[3] is True, "Unskip clears the skip", r[3])
check(r[4] == "Skip", "button is Skip again", r[4])
check(r[5] == 2, "early hand-in with no guide pick still chooses a reward", r[5])
done("unskip_reward_test")
