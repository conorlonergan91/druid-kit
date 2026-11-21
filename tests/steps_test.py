"""Step tracker: auto-skip finished steps, auto accept/hand-in with reward pick, zone arrival, Done/Back."""

from lupa.lua51 import LuaRuntime

from wowenv import source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
printed = {}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
local function obj()
  local o = { shown=false, text="" }
  return setmetatable(o, { __index = function(t, k)
    if k=="Show" then return function(s) s.shown=true end end
    if k=="Hide" then return function(s) s.shown=false end end
    if k=="IsShown" then return function(s) return s.shown end end
    if k=="SetText" then return function(s,v) s.text=v end end
    if k=="GetStringHeight" then return function() return 14 end end
    if k=="CreateFontString" or k=="CreateTexture" then return function() return obj() end end
    if k=="GetText" then return function(s) return s.text end end
    if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
    if k=="RegisterEvent" then return function(s,e) s.events=s.events or {}; s.events[e]=true end end
    if type(k)=="string" and k:match("^%u") then return function() end end
  end })
end
frames = {}
function CreateFrame(kind, name) local f=obj(); frames[#frames+1]=f; if name then _G[name]=f end; return f end
UIParent = obj(); GameTooltip = obj()
C_Timer = { After = function(d, f) f() end }
LOG = {}       -- questID -> { title=, done= }
DONE = {}      -- questID -> true
LEVEL = 18; ZONE = "Westfall"; SUB = "Sentinel Hill"
function UnitLevel() return LEVEL end
function GetZoneText() return ZONE end
function GetSubZoneText() return SUB end
function GetMinimapZoneText() return SUB end
function GetRealZoneText() return ZONE end
function IsShiftKeyDown() return SHIFT end
C_QuestLog = {
  GetLogIndexForQuestID = function(q) return LOG[q] and 1 or nil end,
  IsQuestFlaggedCompleted = function(q) return DONE[q] == true end,
  IsComplete = function(q) return LOG[q] and LOG[q].done or false end,
  GetQuestObjectives = function(q) return LOG[q] and { { text = LOG[q].obj or "0/1", finished = LOG[q].done } } or nil end,
  GetNumQuestLogEntries = function() local n=0 for _ in pairs(LOG) do n=n+1 end return n end,
  GetInfo = function(i) local k=0 for id,v in pairs(LOG) do k=k+1 if k==i then return { questID=id, title=v.title } end end end,
  GetTitleForQuestID = function(q) return TITLES[q] end,
}
TITLES = { [500] = "Named Only" }
CURQ = nil; CURTITLE = nil; CHOICES = {}
function GetQuestID() return CURQ end
function GetTitleText() return CURTITLE end
function AcceptQuest() ACCEPTED = CURQ; LOG[CURQ] = { title = CURTITLE } end
function IsQuestCompletable() return true end
function CompleteQuest() COMPLETED = CURQ end
function GetNumQuestChoices() return #CHOICES end
function GetQuestItemInfo(kind, i) return CHOICES[i] end
function GetQuestReward(i) REWARD = i; if CURQ then DONE[CURQ] = true; LOG[CURQ] = nil end end
GOTO = {}
function DruidKit_GoTo(z, x, y, label, quiet) GOTO[#GOTO+1] = z .. " " .. x .. "," .. y; return true end
DruidKitRoute = { id = "t1", sections = {
  { title = "A", steps = {
    { ["do"] = "turnin", q = 14, name = "Militia", npc = "Gryan", at = { "Westfall", 56.2, 47.6 }, pick = "Fist" },
    { ["do"] = "accept", q = 214, name = "Bandanas", npc = "Riell", at = { "Westfall", 56.6, 47.4 } },
    { ["do"] = "fly", to = "Stormwind" },
    { ["do"] = "note", text = "Library book" },
    { ["do"] = "turnin", name = "Named Only", npc = "Baros" },
    { ["do"] = "goto", text = "Walk to Lakeshire", to = "Lakeshire", at = { "Redridge Mountains", 26, 46 } },
    { ["do"] = "complete", q = 142, name = "Messenger", text = "Kill him" },
    { ["do"] = "level", level = 20 },
  } } } }
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
ev = nil
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
function cur() return DruidKitDB.routeStep end
LOG[14] = { title = "Militia", done = true }
fire("PLAYER_LOGIN")
R = {}
R[#R+1] = cur()                                        -- 1: hand-in not done yet
CURQ = 14; CURTITLE = "Militia"; CHOICES = { "Edge", "Fist", "Spark" }
fire("QUEST_PROGRESS"); fire("QUEST_COMPLETE"); fire("QUEST_TURNED_IN", 14)
R[#R+1] = COMPLETED; R[#R+1] = REWARD; R[#R+1] = cur()  -- 14, 2, 2
CURQ = 214; CURTITLE = "Bandanas"; fire("QUEST_DETAIL")
R[#R+1] = ACCEPTED; R[#R+1] = cur()                     -- 214, 3
ZONE = "Stormwind City"; SUB = "Trade District"; fire("ZONE_CHANGED_NEW_AREA")
R[#R+1] = cur()                                        -- 4 (note waits)
DruidKit_StepDone()
R[#R+1] = cur()                                        -- 5
CURQ = 500; CURTITLE = "Named Only"; CHOICES = {}; fire("QUEST_COMPLETE"); fire("QUEST_TURNED_IN", 500)
R[#R+1] = cur()                                        -- 6
R[#R+1] = GOTO[#GOTO]                                  -- Redridge arrow
DruidKit_OnArrive("x")
R[#R+1] = cur()                                        -- 7
SHIFT = true; CURQ = 142; CURTITLE = "Messenger"; fire("QUEST_DETAIL"); SHIFT = false
R[#R+1] = ACCEPTED                                     -- still 214: Shift held
LOG[142] = { title = "Messenger", done = true }; fire("QUEST_LOG_UPDATE")
R[#R+1] = cur()                                        -- 8 (level 20 waits)
DruidKit_StepBack()
R[#R+1] = cur()                                        -- 7
LEVEL = 20; fire("PLAYER_LEVEL_UP")
R[#R+1] = cur()                                        -- 9 (finished)
""")
from expect import check, done

r = list(L.globals().R.values())
check(r[0] == 1, "starts at the first unfinished step", r[0])
check(r[1] == 14 and r[2] == 2, "hand-in completes and picks the guide's reward (Fist = choice 2)", r[1:3])
check(r[3] == 2, "advances after the hand-in", r[3])
check(r[4] == 214 and r[5] == 3, "auto-accepts the next guide quest and advances", r[4:6])
check(r[6] == 4, "fly step ticks off on arriving in Stormwind; note waits", r[6])
check(r[7] == 5, "Done button moves on", r[7])
check(r[8] == 6, "title-only quest hand-in is recognised", r[8])
check("Redridge" in str(r[9]), "arrow points at the current step", r[9])
check(r[10] == 7, "arriving at the spot ticks the step off", r[10])
check(r[11] == 214, "Shift held: no automatic accept", r[11])
check(r[12] == 8 and r[13] == 7 and r[14] == 9, "objectives done, Back, and level step", r[12:15])
done("steps_test")
