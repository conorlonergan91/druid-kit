"""/dk load backup returns to the bars and keys from before the first /dk bars: a second /dk bars and a newly
learned spell don't overwrite it (new-spell placement saves to "autosave"), and the backup keeps its keys."""

from expect import check, done
from wowenv import runtime, source


def setup(extra=""):
    L = runtime("ui")
    L.execute(
        r"""
made={}
local base=CreateFrame
CreateFrame=function(k,n,p,t) local f=base(); f.kind=k; f.parent=p
  f.GetFrameLevel=function() return 1 end; f.GetWidth=function() return 400 end; f.GetVerticalScroll=function() return 0 end
  f.GetPoint=function() return "CENTER",nil,"CENTER",0,0 end; f.GetStringHeight=function() return 10 end
  made[#made+1]=f; return f end
UISpecialFrames={}; SlashCmdList={}; DruidKitDB={}
GetTime=function() return 1 end
C_Timer={After=function(d,f) f() end, NewTicker=function() end}
KNOWN={Wrath=true, Maul=true, ["Cat Form"]=true, ["Find Herbs"]=true}
IDS={Wrath=1,Moonfire=2,Bash=3,Maul=4,["Cure Poison"]=5,["Cat Form"]=768,["Find Herbs"]=2383}
C_Spell={GetSpellInfo=function(n) return IDS[n] and {spellID=IDS[n]} end, PickupSpell=function(id) CUR=id end}
C_SpellBook={IsSpellKnown=function(id) for n,i in pairs(IDS) do if i==id then return KNOWN[n] end end end}
function GetCursorInfo() return CUR end
function ClearCursor() CUR=nil end
PLACED={}
ACTIONS={}
C_ActionBar={PlaceAction=function(slot) PLACED[slot]=CUR end, HasAction=function(slot) return PLACED[slot]~=nil end,
  PickupAction=function(slot) PLACED[slot]=nil end, GetActionInfo=function(s) local a=ACTIONS[s]; if a then return a[1], a[2] end end}
BIND={}
function SetBinding(k,a) BIND[k]=a; return true end
function SetBindingSpell(k,s) BIND[k]="SPELL "..s; return true end
function SaveBindings() end function GetCurrentBindingSet() return 1 end
function GetBindingAction(k) return BIND[k] end
function GetBindingKey() end
COMBAT=false
function InCombatLockdown() return COMBAT end
function UnitIsDeadOrGhost() return false end
MACROS={}
function GetMacroIndexByName(n) for i,m in pairs(MACROS) do if m.n==n then return i end end return 0 end
function GetMacroInfo(i) return MACROS[i] and MACROS[i].n end
function CreateMacro(n,i,b,pc) MACROS[#MACROS+1]={n=n,b=b}; return #MACROS end
function EditMacro() end
PICKED={}
function PickupMacro(i) PICKED[#PICKED+1]=i; CUR='macro'..i end
TRACK={active=true}
C_Minimap={GetNumTrackingTypes=function() return 1 end, GetTrackingInfo=function() return {name="Find Herbs", active=TRACK.active} end,
  SetTracking=function() end}
"""
        + extra
    )
    L.execute(source("DruidKit/DruidKit_Guide.lua"))
    L.execute(source("DruidKit/DruidKit.lua"))
    L.execute(r"""
for _,f in ipairs(made) do if f.on_OnEvent then ev=f break end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("ADDON_LOADED","DruidKit")
function said(s) local n=0 for _,p in ipairs(printed) do if p:find(s,1,true) then n=n+1 end end return n end
function firstSaid(s) for i,p in ipairs(printed) do if p:find(s,1,true) then return i end end end
""")
    return L, L.globals()


L, g = setup()
L.execute(r"""
BIND = { R = "JUMP" }
ACTIONS = { [1] = { "spell", 42 } }
SlashCmdList.DRUIDKIT('bars')
ACTIONS = { [1] = { "spell", 1 } }
SlashCmdList.DRUIDKIT('bars')
fire("PLAYER_ENTERING_WORLD")
KNOWN.Moonfire = true
fire("LEARNED_SPELL_IN_TAB", 1)
""")
b = g.DruidKitDB.layouts.backup
check(b[1] and b[1].id == 42, "backup still holds the bars from before the first /dk bars", b[1] and b[1].id)
keys = b["keys"]
check(keys is not None and keys["R"] == "JUMP", "backup still holds the keys from before the first /dk bars", keys)
auto = g.DruidKitDB.layouts.autosave
check(auto is not None and auto[1].id == 1, "new-spell placement saves the old bars as autosave", auto)
L.execute("SlashCmdList.DRUIDKIT('load backup')")
check(g.BIND["R"] == "JUMP", "/dk load backup restores the pre-/dk-bars keys", g.BIND["R"])
done("r2_bars_backup_test")
