"""Healing / questing mode: bars and gear swap together and toggle back."""

from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
made={}
local b=CreateFrame
CreateFrame=function(k,n,p,t) local f=b(); f.GetFrameLevel=function() return 1 end; f.GetWidth=function() return 400 end; f.GetVerticalScroll=function() return 0 end; f.GetPoint=function() return "CENTER",nil,"CENTER",0,0 end; return f end
""")
L.execute(r"""
UISpecialFrames={}; SlashCmdList={}; DruidKitDB={}
GetTime=function() return 1 end
C_Timer={After=function(d,f) f() end, NewTicker=function() end}
KNOWN={Wrath=true, Maul=true, Rejuvenation=true, Regrowth=true, Moonfire=true}
IDS={Wrath=1,Moonfire=2,Bash=3,Maul=4,["Cure Poison"]=5,Rejuvenation=6,Regrowth=7}
C_Spell={GetSpellInfo=function(n) return IDS[n] and {spellID=IDS[n]} end, PickupSpell=function(id) CUR=id end}
C_SpellBook={IsSpellKnown=function(id) for n,i in pairs(IDS) do if i==id then return KNOWN[n] end end end}
function GetCursorInfo() return CUR end
function ClearCursor() CUR=nil end
PLACED={}
PLACED={[8]="Rejuv",[98]=3}
C_ActionBar={PlaceAction=function(slot) PLACED[slot]=CUR end, HasAction=function(slot) return PLACED[slot]~=nil end, PickupAction=function(slot) PLACED[slot]=nil end, GetActionInfo=function() end}
function SetBinding() end function SaveBindings() end function GetCurrentBindingSet() return 1 end
function GetActionInfo() end function HasAction(s) return PLACED[s]~=nil end
function InCombatLockdown() return false end
StaticPopupDialogs = StaticPopupDialogs or {}; StaticPopup_Show = StaticPopup_Show or function(n) print("POPUP "..n) end; ReloadUI = function() end
GetShapeshiftForm = GetShapeshiftForm or function() return 0 end
function UnitIsDeadOrGhost() return false end
""")
L.execute(source("DruidKit/DruidKit_Guide.lua"))
L.execute(source("DruidKit/DruidKit.lua"))
L.execute(r"""
local ev
for _,f in ipairs(frames) do if f.on_OnEvent then ev=f break end end
ev.on_OnEvent(ev,"ADDON_LOADED","DruidKit")
ev.on_OnEvent(ev,"PLAYER_ENTERING_WORLD")
first=DruidKitDB.knownSpells and DruidKitDB.knownSpells.Wrath
KNOWN.Bash=true
SlashCmdList.DRUIDKIT('bars')
q1={} for k,v in pairs(PLACED) do q1[k]=v end
INV={[5]="item:100:robe"}
function GetInventoryItemLink(_,s) return INV[s] end
SlashCmdList.DRUIDKIT('healset')
h1={} SlashCmdList.DRUIDKIT('heal') for k,v in pairs(PLACED) do h1[k]=v end
SlashCmdList.DRUIDKIT('quest') q2={} for k,v in pairs(PLACED) do q2[k]=v end

""")
g = L.globals()
print("remembered first:", g.first)
print("quest:", dict(g.q1))
print("heal:", dict(g.h1))
print("back:", dict(g.q2))
print("mode:", g.DruidKitDB.barMode)
[print(p) for p in g.printed.values() if "mode" in p.lower() or "saved" in p]

from expect import check, done

check(g.DruidKitDB.barMode == "quest", "mode toggles back to questing", g.DruidKitDB.barMode)
check(any("Healing mode: bars switched" in p for p in g.printed.values()), "healing mode switches bars")
done("mode_test")
