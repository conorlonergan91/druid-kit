"""Party view: P, C and R take clicks for the whole fight (they can appear mid-combat), back to shown-only after
combat; "!" and "T" show only when you know Mark of the Wild / Thorns, not merely when the spell exists."""

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
    "local cf=CreateFrame; CreateFrame=function(...) local f=cf(...); f.SetAttribute=function(s,k,v) s.attrs=s.attrs or {}; s.attrs[k]=v end; f.GetAttribute=function(s,k) return s.attrs and s.attrs[k] end; f.EnableMouse=function(s,on) s.mouse=on end; return f end"
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
L.execute(r"""
KNOWN = {}
C_SpellBook = { IsSpellKnown = function(id) return KNOWN[id] end }
IDS = { ["Mark of the Wild"] = 1126, Thorns = 467 }
C_Spell.GetSpellInfo = function(n) return { spellID = IDS[n] or 1 } end
function UnitGroupRolesAssigned(u) return u == "party1" and "TANK" or "NONE" end
POISON = false
C_UnitAuras.GetAuraDataByIndex = function(u, i) if POISON and u == "party1" and i == 1 then return { dispelName = "Poison" } end end
""")
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
ev=nil for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_PartyCommand("test")
c=_G.DruidKitPartyCard2
c.unit="party1"
ev.on_OnUpdate(ev,1)
R = { motw = tostring(c.motw.mouse), thorns = tostring(c.thorns.mouse), p0 = tostring(c.cureP.mouse) }
KNOWN[1126] = true; KNOWN[467] = true
ev.on_OnEvent(ev,"UNIT_AURA","party1"); ev.on_OnUpdate(ev,1)
R.motw2, R.thorns2 = tostring(c.motw.mouse), tostring(c.thorns.mouse)
ev.on_OnEvent(ev,"PLAYER_REGEN_DISABLED"); COMBAT = true
R.p1, R.c1, R.r1 = tostring(c.cureP.mouse), tostring(c.cureC.mouse), tostring(c.res.mouse)
POISON = true; ev.on_OnEvent(ev,"UNIT_AURA","party1"); ev.on_OnUpdate(ev,1)
R.p2 = tostring(c.cureP.mouse)
POISON = false; ev.on_OnEvent(ev,"UNIT_AURA","party1"); ev.on_OnUpdate(ev,1)
R.p3 = tostring(c.cureP.mouse)
COMBAT = false; ev.on_OnEvent(ev,"PLAYER_REGEN_ENABLED"); ev.on_OnUpdate(ev,1)
R.p4, R.c4, R.r4 = tostring(c.cureP.mouse), tostring(c.cureC.mouse), tostring(c.res.mouse)
""")
R = L.globals().R
check(
    R.motw == "false" and R.thorns == "false", "! and T stay off when Mark of the Wild / Thorns aren't known", dict(R)
)
check(R.motw2 == "true" and R.thorns2 == "true", "! and T show once the spells are known", dict(R))
check(R.p0 == "false", "out of combat a hidden P takes no clicks", R.p0)
check(R.p1 == "true" and R.c1 == "true" and R.r1 == "true", "combat starts: P, C and R take clicks", dict(R))
check(R.p2 == "true" and R.p3 == "true", "in combat P stays clickable as poison comes and goes", dict(R))
check(
    R.p4 == "false" and R.c4 == "false" and R.r4 == "false", "after combat hidden P, C, R stop taking clicks", dict(R)
)
done("r2_party_test")
