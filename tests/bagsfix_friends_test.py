"""Catch-up tracker: guild members are never saved as friends, and saved friends are never removed (even one who is
only in the guild now). A guildie can still be named with /dk catchup."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
printed = {}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
function GetTime() return 1000 end
local function mkobj()
  local o = { shown = false, text = "" }
  return setmetatable(o, { __index = function(t, k)
    if type(k) == "string" and k:match("^%u") then
      if k == "Show" then return function(s) s.shown = true end end
      if k == "Hide" then return function(s) s.shown = false end end
      if k == "SetText" then return function(s, v) s.text = v end end
      if k == "GetStringHeight" then return function() return 30 end end
      if k == "CreateFontString" or k == "CreateTexture" then return function() local o = mkobj(); frames[#frames+1] = o; return o end end
      if k == "SetScript" then return function(s, e, f) s["on_" .. e] = f end end
      return function() end
    end
  end })
end
frames = {}
function CreateFrame() local f = mkobj(); frames[#frames+1] = f; return f end
UIParent = mkobj()
C_Timer = { After = function(d, f) f() end, NewTicker = function() end }
function UnitLevel() return 20 end
function UnitXP() return 0 end
function UnitXPMax() return 1000 end
function UnitHealth() return 1 end function UnitHealthMax() return 1 end
function UnitPower() return 1 end function UnitPowerMax() return 1 end
function InCombatLockdown() return false end
function UnitIsDeadOrGhost() return false end
function BreakUpLargeNumbers(n) return tostring(n) end
C_FriendList = { GetNumFriends = function() return 1 end, GetFriendInfoByIndex = function() return { name = "Aoife", level = 23 } end }
function IsInGuild() return true end
GUILD = { { "Oldtimer-Realm", 59 }, { "Aoife-Realm", 23 }, { "Guildie-Realm", 60 } }
function GetNumGuildMembers() return #GUILD end
function GetGuildRosterInfo(i) local m = GUILD[i]; return m[1], nil, nil, m[2] end
DruidKitDB = { friends = { Oldtimer = 59, Aoife = 22 } }
""")
L.execute(source("DruidKit/DruidKit_Helpers.lua"))
L.execute(r"""
ev = frames[1]
ev.on_OnEvent(ev, "PLAYER_LOGIN")
ev.on_OnEvent(ev, "FRIENDLIST_UPDATE")
ev.on_OnEvent(ev, "GUILD_ROSTER_UPDATE")
function trackerText() for _, f in ipairs(frames) do if type(f.text) == "string" and f.text:find("Catch") then return f.text end end end
DEFAULT = trackerText()
DruidKit_HelperCommand("catchup", "guil")
NAMED = trackerText()
""")
g = L.globals()
friends = dict(g.DruidKitDB.friends.items())
check(friends.get("Oldtimer") == 59, "a saved friend now only in the guild is never removed", friends)
check(friends.get("Aoife") == 23, "a friend who is also in the guild stays", friends)
check("Guildie" not in friends, "a guild member is never saved as a friend", friends)
check(
    "Oldtimer 59" in g.DEFAULT and "Guildie" not in g.DEFAULT,
    "default target is the highest saved friend, never an unsaved guildie",
    g.DEFAULT,
)
check(g.DruidKitDB.friendsMigrated is None, "no one-time friends migration", g.DruidKitDB.friendsMigrated)
check("Guildie 60" in g.NAMED, "a guildie can still be named with /dk catchup", g.NAMED)
done("bagsfix_friends_test")
