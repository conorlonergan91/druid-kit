"""ClaudeProgress: the minute timer never touches the quest log (no expanding headers, no selecting quests); the full
pass runs at logout and on /claude, never in combat, and puts the selection back (even 'nothing selected').
Uncached completed-quest titles are requested once per session."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
SlashCmdList = {}
C_Timer = { After = function(t, f) end, NewTicker = function(t, f) TICK = f end }
frames = {}
function CreateFrame() local f = {} function f:RegisterEvent() end function f:SetScript(k, fn) f[k] = fn end frames[#frames+1] = f return f end
function UnitName() return "Cu" end function GetRealmName() return "R5" end
function date() return "x" end function time() return 1 end
function UnitXPMax() return 1000 end function GetMoney() return 0 end
C_Container = { GetContainerNumSlots = function(b) return b == 0 and 16 or 0 end, GetContainerNumFreeSlots = function() return 4 end }
COMBAT = false; function InCombatLockdown() return COMBAT end
LOG = { { title = "Elwynn", isHeader = true, isCollapsed = true }, { title = "Kobolds", questID = 7 } }
SHOWN = { LOG[1] }
EXPANDS, SELECTS, LOADS = 0, {}, 0
SELECTED = nil
C_QuestLog = {
  GetNumQuestLogEntries = function() return #SHOWN end,
  GetInfo = function(i) return SHOWN[i] end,
  ExpandQuestHeader = function() EXPANDS = EXPANDS + 1; LOG[1].isCollapsed = false; SHOWN = LOG end,
  CollapseQuestHeader = function() LOG[1].isCollapsed = true; SHOWN = { LOG[1] } end,
  GetSelectedQuest = function() return SELECTED end,
  SetSelectedQuest = function(q) SELECTS[#SELECTS + 1] = q; SELECTED = q end,
  IsComplete = function() return false end, GetQuestObjectives = function() return {} end,
  GetAllCompletedQuestIDs = function() return { 11, 12 } end,
  GetTitleForQuestID = function(id) if id == 11 then return "Done" end end,
  RequestLoadQuestByID = function() LOADS = LOADS + 1 end,
}
function GetNumQuestLogChoices() return 1 end
function GetQuestLogItemLink() return "|Hitem:5|h[Staff]|h" end
function fire(e) for _, f in ipairs(frames) do if f.OnEvent then f.OnEvent(f, e) end end end
""")
L.execute(source("ClaudeProgress/ClaudeProgress.lua"))
L.execute(r"""
TICK(); TICK()
R = { EXPANDS, #SELECTS, LOADS }
COMBAT = true; SlashCmdList.CLAUDEPROGRESS()
R[4] = EXPANDS; R[5] = #SELECTS
COMBAT = false; fire("PLAYER_LOGOUT")
R[6] = EXPANDS; R[7] = SELECTS[#SELECTS] or "none"; R[8] = #ClaudeProgressDB["Cu-R5"].questRewards
R[9] = #ClaudeProgressDB["Cu-R5"].quests; R[10] = LOG[1].isCollapsed; R[11] = LOADS
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 0 and r[1] == 0, "minute timer: no header expanding, no quest selecting", r[0:2])
check(r[2] == 1, "uncached quest titles: requested once, not every minute", r[2])
check(r[3] == 0 and r[4] == 0, "/claude in combat: no quest-log pass", r[3:5])
check(r[5] == 1 and r[7] == 1 and r[8] == 1, "logout: full pass with headers opened and rewards read", r[5:9])
check(r[6] == 0, "logout: 'nothing selected' is restored", r[6])
check(r[9] is True, "logout: the collapsed header is collapsed again", r[9])
check(r[10] == 1, "logout: still no second title request", r[10])
done("bagsfix_progress_test")
