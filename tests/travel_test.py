"""Flight paths and hearthstone: fp/home steps tick themselves, hearth/fly steps warn when the hearth or the
flight path isn't there, and ClaudeProgress exports the known flight paths and the hearth location."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
BIND = "Stormwind"
function GetBindLocation() return BIND end
function UnitName() return "Cu" end
function GetRealmName() return "R5" end
DruidKitRoute = { id = "tr", sections = { { title = "Loch Modan", steps = {
  { ["do"] = "fp", to = "Thelsamar", npc = "Thorgrum Borrelson", at = { "Loch Modan", 33.9, 51.0 } },
  { ["do"] = "home", to = "Thelsamar", npc = "Innkeeper Hearthstove", at = { "Loch Modan", 35.5, 48.4 } },
  { ["do"] = "note", text = "Kill things" },
  { ["do"] = "hearth", to = "Thelsamar" },
  { ["do"] = "fly", to = "Menethil Harbor" },
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
DruidKit_StepsEvaluate()
R[#R+1] = cur()                                  -- 1: fp step waits
function NumTaxiNodes() return 1 end
function TaxiNodeGetType() return "CURRENT" end
function TaxiNodeName() return "Thelsamar, Loch Modan" end
fire("TAXIMAP_OPENED")
for _, t in ipairs(timers or {}) do pcall(t) end
DruidKit_StepsEvaluate()
R[#R+1] = cur()                                  -- 2: talking to the flight master ticks it
R[#R+1] = DruidKitSteps.main.text
BIND = "Thelsamar"; fire("CHAT_MSG_SYSTEM"); DruidKit_StepsEvaluate()
R[#R+1] = cur()                                  -- 3: hearth set ticks the home step
DruidKit_StepDone()
BIND = "Stormwind"; DruidKit_StepsEvaluate()
R[#R+1] = DruidKitSteps.detail.text              -- hearth step warns: hearth is elsewhere
ClaudeProgressDB = { flights = { ["Cu-R5"] = { ["Thelsamar, Loch Modan"] = true } } }
BIND = "Thelsamar"; DruidKit_StepDone(); DruidKit_StepsEvaluate()
R[#R+1] = DruidKitSteps.detail.text              -- fly step warns: Menethil not learned
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == 1, "fp step waits until you meet the flight master", r[0])
check(r[1] == 2, "opening the flight map ticks the fp step", r[1])
check("Set hearth" in str(r[2]), "home step reads 'Set hearth'", r[2])
check(r[3] == 3, "binding the hearthstone ticks the home step", r[3])
check("WARNING: your hearth is set to Stormwind" in str(r[4]), "hearth step warns when hearth is elsewhere", r[4])
check("not learned the Menethil Harbor flight path" in str(r[5]), "fly step warns about an unknown flight path", r[5])

# ClaudeProgress: flight map -> known flights; snapshot carries travel.
P = LuaRuntime(unpack_returned_tuples=True)
P.execute(r"""
SlashCmdList={}
timers={}
C_Timer={After=function(t,f) table.insert(timers,f) end, NewTicker=function() end}
frames={}
function CreateFrame() local f={} function f:RegisterEvent() end function f:SetScript(k,fn) f[k]=fn end table.insert(frames,f) return f end
function UnitName() return "Cu" end function GetRealmName() return "R5" end
function date() return "x" end function time() return 1 end function GetTime() return 70 end
function GetBindLocation() return "Thelsamar" end
function GetItemCooldown(id) return 40, 60, 1 end
NODES = { {"Thelsamar, Loch Modan","CURRENT"}, {"Ironforge, Dun Morogh","REACHABLE"}, {"Menethil Harbor, Wetlands","DISTANT"} }
function NumTaxiNodes() return #NODES end
function TaxiNodeName(i) return NODES[i][1] end
function TaxiNodeGetType(i) return NODES[i][2] end
""")
P.execute(source("ClaudeProgress/ClaudeProgress.lua"))
P.execute(r"""
for _, f in ipairs(frames) do if f.OnEvent then f.OnEvent(f, "TAXIMAP_OPENED") end end
""")
known = P.eval('ClaudeProgressDB.flights["Cu-R5"]')
check(
    known["Thelsamar, Loch Modan"] and known["Ironforge, Dun Morogh"] and not known["Menethil Harbor, Wetlands"],
    "only learned flight paths are recorded",
    dict(known),
)
P.execute(r"""
function UnitXPMax() return 100 end
C_Container={GetContainerNumSlots=function() return 16 end, GetContainerItemInfo=function() return nil end,
 GetItemCooldown=function(id) return 40, 60, 1 end}
NUM_BAG_SLOTS=4
SlashCmdList["CLAUDEPROGRESS"]()
""")
t = P.eval('ClaudeProgressDB["Cu-R5"] and ClaudeProgressDB["Cu-R5"].travel')
print(dict(t) if t else t)
check(
    t is not None
    and t["home"] == "Thelsamar"
    and t["hearthCooldown"] == 30
    and list(t["flights"].values()) == ["Ironforge, Dun Morogh", "Thelsamar, Loch Modan"],
    "snapshot exports hearth location, cooldown and known flight paths",
    t and dict(t),
)
done("travel_test")
