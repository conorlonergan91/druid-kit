"""Party view: shows only in a party, health in words, heal buttons mirror the bars."""

from lupa.lua51 import LuaRuntime

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
L.execute("local cf=CreateFrame; CreateFrame=function(...) local f=cf(...); f.SetAttribute=function(s,k,v) s.attrs=s.attrs or {}; s.attrs[k]=v end; f.GetAttribute=function(s,k) return s.attrs and s.attrs[k] end; return f end")
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
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
ev=nil for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
ev.on_OnEvent(ev,"PLAYER_LOGIN")
drv1=DRIVER
DruidKit_PartyCommand("test")
c=_G.DruidKitPartyCard2
c.unit="party1"
ev.on_OnEvent(ev,"UNIT_HEALTH")
ev.on_OnEvent(ev,"GROUP_ROSTER_UPDATE")
local acts={} for n,b in ipairs(c.btns) do acts[#acts+1]=tostring(b.slot)..":"..tostring(b.spell)..":"..tostring(b.badge.text) end
info={c.name.text, c.state.text, c.big.text, tostring(c.hots[1].shown), c.hots[1].txt.text, table.concat(acts," "), "portraits="..PORTRAITS}
DruidKit_PartyCommand("size big")
""")
g = L.globals()
print("driver:", g.drv1)
print(list(g.printed.values()))
print(list(g.info.values()))

from expect import check, done

info = list(g.info.values())
check(g.drv1 == "[group:party] show; hide", "party view only shows in a party", g.drv1)
check("!! 25%" in info[1], "low health shown in words, not colour alone", info[1])
check("4:Rejuvenation" in info[5], "heal buttons mirror the action bar", info[5])
L.execute(r"""
local pp = _G["DruidKitPartyPet2"]
petInfo = { pp and pp.heals and #pp.heals or 0, pp and pp.heals and pp.heals[1] and pp.heals[1].attrs and pp.heals[1].attrs.unit or "?",
  pp and pp.attrs and pp.attrs["shift-spell1"] or "?" }
""")
pi = list(L.globals().petInfo.values())
print("pet", pi)
check(pi[0] == 3, "pet bars have their own heal set (3 buttons)", pi)
check(pi[2] == "Regrowth", "pet bar clicks match a person's card (Shift = Regrowth)", pi)
done("party_test")
