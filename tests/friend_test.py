"""Catch-up tracker: finds a named friend's level and works out the target."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import source

L = LuaRuntime(unpack_returned_tuples=True)
L.execute(r"""
printed = {}
function print(...) local t={} for i=1,select('#',...) do t[#t+1]=tostring(select(i,...)) end printed[#printed+1]=table.concat(t," ") end
NOW=1000
function GetTime() return NOW end
local function mkobj()
  local o = {shown=false, text="", h=10}
  return setmetatable(o, {__index=function(t,k)
    if type(k)=="string" and k:match("^%u") then
      if k=="Show" then return function(s) s.shown=true end end
      if k=="Hide" then return function(s) s.shown=false end end
      if k=="SetText" then return function(s,v) s.text=v end end
      if k=="SetMinMaxValues" or k=="SetValue" then return function(s,a,b) if a==SECRET or b==SECRET then s.gotSecret=true end end end
      if k=="GetStringHeight" then return function() return 30 end end
      if k=="GetPoint" then return function() return "CENTER",nil,"CENTER",5,6 end end
      if k=="CreateFontString" or k=="CreateTexture" then return function() local o=mkobj(); frames[#frames+1]=o; return o end end
      if k=="SetScript" then return function(s,e,f) s["on_"..e]=f end end
      return function() end
    end
  end})
end
frames={}
function CreateFrame(...) local f=mkobj(); frames[#frames+1]=f; return f end
UIParent=mkobj()
BackdropTemplateMixin={}
C_Timer={After=function(d,f) f() end, NewTicker=function() end}
XP=500; XPMAX=10100; LVL=12; HP=100; HPMAX=100; MP=100; MPMAX=100; COMBAT=false
function UnitLevel() return LVL end
function UnitXP() return XP end
function UnitXPMax() return XPMAX end
SECRET={}
function issecretvalue(v) return v==SECRET end
function UnitHealth() return SECRET end function UnitHealthMax() return HPMAX end
function UnitPower() return SECRET end function UnitPowerMax() return MPMAX end
function InCombatLockdown() return COMBAT end
function UnitIsDeadOrGhost() return false end
function BreakUpLargeNumbers(n) return tostring(n) end
BUFFS={}
C_UnitAuras={GetAuraDataBySpellName=function(u,n) return BUFFS[n] end}
C_Spell={GetSpellInfo=function(n) return {spellID=#n} end, GetSpellTexture=function() return 1 end}
C_SpellBook={IsSpellKnown=function(id) return id ~= #"Rejuvenation" or true end}
C_FriendList={GetNumFriends=function() return 1 end, GetFriendInfoByIndex=function() return {name="Aoife",level=23} end, ShowFriends=function() end}
function IsInGuild() return false end
C_QuestLog={GetNumQuestLogEntries=function() return 3 end, GetInfo=function(i) return ({{level=5},{level=12},{isHeader=true,level=0}})[i] end}
DUR={[1]={100,100},[5]={30,100}}
function GetInventoryItemDurability(s) local d=DUR[s] if d then return d[1],d[2] end end
C_Container={GetContainerNumFreeSlots=function() return 0 end}
shouts={}
UIErrorsFrame={AddMessage=function(_,m) shouts[#shouts+1]=m end}
""")
L.execute(source("DruidKit/DruidKit_Helpers.lua"))
L.execute(r"""
ev=frames[1]
ev.on_OnEvent(ev,"PLAYER_LOGIN")
NOW=1600; XP=2500; ev.on_OnEvent(ev,"PLAYER_XP_UPDATE")
NOW=1900; XP=4000; ev.on_OnEvent(ev,"PLAYER_XP_UPDATE")
LVL=14
function trackerText() for _,f in ipairs(frames) do if type(f.text)=="string" and f.text:find("Catch") then return f.text end end end
DruidKit_HelperCommand("catchup","")
DEFAULT = trackerText()
DruidKit_HelperCommand("catchup","25")
TARGET = trackerText()
DruidKit_HelperCommand("catchup","aoi")
NAMED = trackerText()
DruidKit_HelperCommand("catchup","niamh")
MISSING = trackerText()
""")
g = L.globals()
check(g.DruidKitDB.friends.Aoife == 23, "a friend's level is saved", g.DruidKitDB.friends.Aoife)
check("Aoife 23: 9 levels behind" in g.DEFAULT, "no target set: catch up to your highest friend", g.DEFAULT)
check("Target 25: 11 levels behind" in g.TARGET, "/dk catchup 25: a level target", g.TARGET)
check(
    "Aoife 23: 9 levels behind" in g.NAMED and "Big gap" in g.NAMED,
    "/dk catchup aoi: the named friend, with advice",
    g.NAMED,
)
check("Niamh not on your friends list" in g.MISSING, "a name not on the list says how to add them", g.MISSING)
done("friend_test")
