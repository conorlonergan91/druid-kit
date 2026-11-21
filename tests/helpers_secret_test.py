"""Helper panels cope with hidden ('secret') values the client returns in combat."""

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
# Record every error a pcall swallows, so "no errors" is checked, not just "not 5 errors".
L.execute(r"""
ERRS = {}
local raw = pcall
function pcall(f, ...)
  local r = { raw(f, ...) }
  if not r[1] then ERRS[#ERRS + 1] = tostring(r[2]) end
  return unpack(r, 1, table.maxn(r))
end
""")
L.execute(r"""
ev=frames[1]
ev.on_OnEvent(ev,"PLAYER_LOGIN")
LOGIN_OK = DruidKitDB.trackerOn and DruidKitDB.friends.Aoife==23
NOW=1600; XP=2500; ev.on_OnEvent(ev,"PLAYER_XP_UPDATE")
NOW=1900; XP=4000; ev.on_OnEvent(ev,"PLAYER_XP_UPDATE")
HP=50; MP=30; ev.on_OnUpdate(ev,1)
HP=100; MP=100; BUFFS["Mark of the Wild"]={} ; ev.on_OnUpdate(ev,1)
for _,f in ipairs(frames) do if type(f.text)=="string" and f.text:find("ready") then HUD=f.text end end
ev.on_OnEvent(ev,"UPDATE_INVENTORY_DURABILITY")
ev.on_OnEvent(ev,"BAG_UPDATE_DELAYED")
LVL=14; ev.on_OnEvent(ev,"PLAYER_LEVEL_UP",14)
SlashOK = DruidKit_HelperCommand("catchup","25")
Bad = DruidKit_HelperCommand("zzz","")
DruidKit_HelperCommand("unlock",""); DruidKit_HelperCommand("hud","off"); DruidKit_HelperCommand("lock","")
DruidKit_HelperCommand("tracker","on")
for _,f in ipairs(frames) do if type(f.text)=="string" and f.text:find("Catch") then CT=f.text end end
for i=1,10 do ev.on_OnUpdate(ev,1) end
hb=false for _,f in ipairs(frames) do if f.gotSecret then hb=true end end
""")
g = L.globals()
shouts = list(g.shouts.values())
printed = list(g.printed.values())
check(g.LOGIN_OK is True, "login: panels on and a friend's level read", g.LOGIN_OK)
check(g.hb is True, "secret health and mana go straight to the bars (the game draws them)", g.hb)
check(g.HUD is not None and "HP " not in g.HUD and "MP " not in g.HUD, "no HP/MP percent from secret values", g.HUD)
errs = list(g.ERRS.values())
check(errs == [] and not [p for p in printed if "paused" in p], "no errors in any handler", errs)
check(
    shouts == ["Gear below 50%: repair in town", "Bags full!", "Level 14!"],
    "durability, bags and level-up shouts",
    shouts,
)
check(
    g.SlashOK is True and g.Bad is False and g.DruidKitDB.catchupTarget == 25,
    "/dk catchup 25; unknown commands fall through",
    (g.SlashOK, g.Bad, g.DruidKitDB.catchupTarget),
)
check(g.DruidKitDB.hudOn is False, "/dk hud off", g.DruidKitDB.hudOn)
check("Lv 14, 39%" in g.CT and "Target 25: 11 levels behind" in g.CT, "tracker: level, percent and target", g.CT)
done("helpers_secret_test")
