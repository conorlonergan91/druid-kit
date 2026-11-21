"""Party view: hidden fix buttons (P / C / ! / T / R) don't take clicks, changed after combat if needed; unit
events for units that aren't on a card don't redraw anything, and bursts of events draw once."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import mock, source

L = LuaRuntime(unpack_returned_tuples=True)
base = mock("ui").replace('if k=="GetStringHeight" then return function() return 10 end end\n      ', "")
base = base.replace('if k=="GetFrameLevel"', "x")
base = base.replace(
    'if k=="CreateTexture" or k=="CreateFontString"',
    'if k=="CreateAnimationGroup" or k=="CreateAnimation" or k=="CreateMaskTexture" then return function() return mkobj() end end\n      if k=="GetFrameLevel" then return function() return 1 end end\n      if k=="CreateTexture" or k=="CreateFontString"',
)
base = base.replace(
    "function CreateFrame() local f=mkobj(); frames[#frames+1]=f; return f end",
    "function CreateFrame(k,n) local f=mkobj(); frames[#frames+1]=f; if n then _G[n]=f end; return f end",
)
L.execute(base)
L.execute("local mt=getmetatable(CreateFrame()) ")
L.execute(
    "PROTECTED={}; function protect(n) if COMBAT then PROTECTED[#PROTECTED+1]=n; error(n..' called in combat') end end "
    "local cf=CreateFrame; CreateFrame=function(...) local f=cf(...); f.SetAttribute=function(s,k,v) protect('SetAttribute'); s.attrs=s.attrs or {}; s.attrs[k]=v end; f.GetAttribute=function(s,k) return s.attrs and s.attrs[k] end; f.EnableMouse=function(s,on) protect('EnableMouse'); s.mouse=on end; return f end"
)
L.execute(r"""
DruidKitDB={}
C_Timer={After=function(t,f) f() end}
function GetTime() return 100 end function RegisterUnitWatch() end function UnregisterUnitWatch() end
DRIVER=nil
function RegisterStateDriver(f,s,v) DRIVER=v end function UnregisterStateDriver() DRIVER=nil end
SECRET={}
function issecretvalue(v) return v==SECRET end
function UnitExists(u) return u=="player" or u=="party1" end
function UnitName(u) if u=='player' then return SECRET end return 'Tank' end
function UnitClass(u) return "Druid","DRUID" end
function UnitIsVisible() return true end
PORTRAITS=0
function SetPortraitTexture(t,u) PORTRAITS=PORTRAITS+1 end
RAID_CLASS_COLORS={DRUID={r=1,g=0.49,b=0.04}}
function UnitHealth(u) return u=="party1" and 25 or SECRET end
function UnitHealthMax(u) return u=="party1" and 100 or SECRET end
function UnitPower() return 50 end function UnitPowerMax() return 100 end function UnitLevel() return 16 end function UnitPowerType() return 0 end
function UnitIsDeadOrGhost() return false end
function UnitInRange() return true end
function UnitThreatSituation() return 0 end
function UnitGroupRolesAssigned() return "NONE" end
function UnitIsUnit() return false end
SLOTS={[4]=774,[5]=8936,[6]=5185,[30]=8946}
NAMES={[774]="Rejuvenation",[8936]="Regrowth",[5185]="Healing Touch",[8946]="Cure Poison"}
C_ActionBar={GetActionInfo=function(s) if SLOTS[s] then return "spell",SLOTS[s] end end,
  GetActionTexture=function(s) return "tex"..s end,
  GetActionCooldown=function(s) return {startTime=SECRET,duration=SECRET} end}
function IsUsableAction(s) return SECRET, SECRET end
C_UnitAuras={GetAuraDataBySpellName=function(u,n,f) if n=="Rejuvenation" and u=="party1" then return {icon=1, expirationTime=110} end end,
  GetAuraDataByIndex=function(u,i,f) if u=="party1" and i==1 then return {dispelName="Poison", icon=2} end end}
C_Spell={GetSpellInfo=function(n) return {spellID=1} end, GetSpellName=function(id) return NAMES[id] end}
""")
L.execute("COMBAT=false; function InCombatLockdown() return COMBAT end")
L.execute(r"""
local uh = UnitHealth
HEALTH_READS = 0
function UnitHealth(u) HEALTH_READS = HEALTH_READS + 1; return uh(u) end
""")
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
ev=nil for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_PartyCommand("test")
c=_G.DruidKitPartyCard2
c.unit="party1"
ev.on_OnUpdate(ev,1)
R = { tostring(c.cureP.mouse), tostring(c.res.mouse) }
-- in combat the poison is cured: the button fades now, stops taking clicks after combat
C_UnitAuras.GetAuraDataByIndex = function() end
COMBAT = true; ev.on_OnEvent(ev,"UNIT_AURA","party1"); ev.on_OnUpdate(ev,1)
R[3] = tostring(c.cureP.mouse)
COMBAT = false; ev.on_OnEvent(ev,"PLAYER_REGEN_ENABLED"); ev.on_OnUpdate(ev,1)
R[4] = tostring(c.cureP.mouse)
HEALTH_READS = 0
for i = 1, 20 do ev.on_OnEvent(ev,"UNIT_HEALTH","nameplate" .. i); ev.on_OnEvent(ev,"UNIT_AURA","target") end
R[5] = HEALTH_READS
for i = 1, 20 do ev.on_OnEvent(ev,"SPELL_UPDATE_COOLDOWN"); ev.on_OnEvent(ev,"UNIT_HEALTH","party1") end
R[6] = HEALTH_READS
ev.on_OnUpdate(ev,0.15)
R[7] = HEALTH_READS > 0 and HEALTH_READS <= 20
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == "true", "poison on the card: the P button takes clicks", r[0])
check(r[1] == "false", "nobody dead: the hidden R button takes no clicks", r[1])
check(r[2] == "true", "in combat: the secure button can't change yet", r[2])
check(r[3] == "false", "after combat: the faded P button stops taking clicks", r[3])
check(r[4] == 0, "events for other units (nameplates, target) draw nothing", r[4])
check(r[5] == 0, "events only mark the cards: nothing drawn inside the event", r[5])
check(r[6] is True, "the next frame draws the cards once", r[6])
check(
    len(L.globals().PROTECTED) == 0,
    "no protected call (EnableMouse/SetAttribute) in combat",
    list(L.globals().PROTECTED.values()),
)
done("bagsfix_party_test")
