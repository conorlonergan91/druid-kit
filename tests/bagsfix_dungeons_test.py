"""Dungeon quests: the classic quest log's values after a nil (questID is 8th) still arrive; a burst of
QUEST_LOG_UPDATE events redraws once."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
DruidKitDB = {}
DruidKitDungeonData = { { name = "Test Hold", quests = { { id = 2, name = "In Log", min = 10, level = 15, xp = 2000 } } } }
function GetNumQuestLogEntries() return 1 end
function GetQuestLogTitle(i) return "In Log", 15, nil, false, nil, 1, nil, 2 end
function UnitLevel() return 12 end
function UnitXP() return 1000 end
function UnitXPMax() return 10100 end
TIMERS = {}
C_Timer = { After = function(t, f) TIMERS[#TIMERS + 1] = f end }
""")
L.execute(source("DruidKit/DruidKit_Dungeons.lua"))
L.execute(r"""
ev = nil for _, f in ipairs(frames) do if f.on_OnEvent then ev = f end end
for i = 1, 10 do ev.on_OnEvent(ev, "QUEST_LOG_UPDATE") end
QUEUED = #TIMERS
for _, f in ipairs(TIMERS) do f() end
for _, f in ipairs(allfs) do if type(f.text) == "string" and f.text:find("Quests to hand in") then XPTEXT = f.text end end
TIMERS = {}
ev.on_OnEvent(ev, "QUEST_LOG_UPDATE")
AGAIN = #TIMERS
""")
g = L.globals()
check(g.QUEUED == 1, "10 quest log updates queue one redraw", g.QUEUED)
check(g.AGAIN == 1, "after it ran, the next update queues again", g.AGAIN)
check(
    g.XPTEXT is not None and "Quests to hand in: 1" in g.XPTEXT,
    "classic quest log: questID after nils is read",
    g.XPTEXT,
)
done("bagsfix_dungeons_test")
