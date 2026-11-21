"""Catch-up tracker: saved friends are never deleted, whatever the friend list or guild roster say (an unloaded list
at login, an offline Battle.net friend, a saved friend who is in the guild)."""

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
FRIENDS = 0
C_FriendList = { GetNumFriends = function() return FRIENDS end, GetFriendInfoByIndex = function() return { name = "Aoife", level = 23 } end }
function IsInGuild() return true end
GUILD = { { "Oldtimer-Realm", 59 }, { "Aoife-Realm", 23 } }
function GetNumGuildMembers() return #GUILD end
function GetGuildRosterInfo(i) local m = GUILD[i]; return m[1], nil, nil, m[2] end
DruidKitDB = { friends = { Oldtimer = 59, Aoife = 22 } }
""")
L.execute(source("DruidKit/DruidKit_Helpers.lua"))
L.execute(r"""
ev = frames[1]
ev.on_OnEvent(ev, "PLAYER_LOGIN")
ev.on_OnEvent(ev, "GUILD_ROSTER_UPDATE")
EARLY = DruidKitDB.friends.Aoife
FRIENDS = 1; ev.on_OnEvent(ev, "FRIENDLIST_UPDATE"); ev.on_OnEvent(ev, "GUILD_ROSTER_UPDATE")
KEPT, MIGRATED = DruidKitDB.friends.Oldtimer, DruidKitDB.friendsMigrated
FRIENDS = 0; ev.on_OnEvent(ev, "FRIENDLIST_UPDATE"); ev.on_OnEvent(ev, "GUILD_ROSTER_UPDATE")
LATER = DruidKitDB.friends.Aoife
""")
g = L.globals()
check(g.EARLY == 22, "guild roster before the friend list loads: the friend stays", g.EARLY)
check(g.KEPT == 59 and g.MIGRATED is None, "a saved friend in the guild is never pruned", (g.KEPT, g.MIGRATED))
check(g.LATER == 23, "a friend later missing from the list (offline) is not deleted", g.LATER)
done("r3_bags_friends_test")
