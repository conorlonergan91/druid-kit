"""/dk bars: places known spells on the right keys and clears stale buttons."""

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
KNOWN={Wrath=true, Maul=true}
IDS={Wrath=1,Moonfire=2,Bash=3,Maul=4,["Cure Poison"]=5}
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
""")
g = L.globals()
print("remembered first:", g.first)
print("placed:", dict(g.PLACED))
[print(p) for p in g.printed.values() if "keys" in p or "bars set" in p]

from expect import check, done

placed = dict(g.PLACED)
check(placed.get(99) == 4 and placed.get(102) == 3, "known bear spells placed on keys 3 and 6", placed)
check(placed.get(2) == 1, "Wrath placed on caster key 2", placed)
check(placed.get(61) == 6603, "Attack placed on R", placed)
check(8 not in placed and 98 not in placed, "stale buttons cleared", placed)
done("bars_test")
