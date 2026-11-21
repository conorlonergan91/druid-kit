"""Bars and keys: combat queue, macro layouts by name, Cat Form key, key backup, herb button, guide tab reuse."""

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


# 11: actions queued in combat all run afterwards, in order, once each.
L, g = setup()
L.execute(r"""
DruidKitDB.layouts.mine = {}
COMBAT = true
SlashCmdList.DRUIDKIT('bars'); SlashCmdList.DRUIDKIT('bars'); SlashCmdList.DRUIDKIT('load mine')
before = said("bars set")
COMBAT = false; fire("PLAYER_REGEN_ENABLED")
""")
check(
    g.before == 0 and L.eval('said("bars set")') == 1,
    "queued /dk bars runs once after combat",
    L.eval('said("bars set")'),
)
check(L.eval("said(\"loaded 'mine'\")") == 1, "a later queued action doesn't replace the earlier one")
check(L.eval('(firstSaid("bars set") or 1/0) < (firstSaid("loaded \'mine\'") or 0)'), "queued actions run in order")

# 12: macros are saved by name and found again by name; old saves with only an index still load.
L, g = setup()
L.execute(r"""
MACROS = { [5] = { n = "DK Maul" } }
ACTIONS = { [99] = { "macro", 5 } }
SlashCmdList.DRUIDKIT('save m')
MACROS = { [7] = { n = "DK Maul" }, [5] = { n = "Other" } }
SlashCmdList.DRUIDKIT('load m')
first = PICKED[#PICKED]
DruidKitDB.layouts.old = { [99] = { kind = "macro", id = 5 } }
SlashCmdList.DRUIDKIT('load old')
second = PICKED[#PICKED]
""")
check(g.DruidKitDB.layouts.m[99].name == "DK Maul", "the macro's name is saved", g.DruidKitDB.layouts.m[99].name)
check(g.first == 7, "the macro is found by name after its index moved", g.first)
check(g.second == 5, "old saves with only an index still load", g.second)

# 10: /dk bars binds Cat Form by spell on G, keeps a /dk catkey choice, and /dk load backup restores the keys.
L, g = setup()
L.execute(r"""
BIND = { R = "JUMP", F = "MOVEFORWARD" }
SlashCmdList.DRUIDKIT('bars')
g1, r1, k1 = BIND.G, BIND.R, DruidKitDB.catKeySet
SlashCmdList.DRUIDKIT('load backup')
k2 = DruidKitDB.catKeySet
""")
check(g.g1 == "SPELL Cat Form" and g.k1 == "G", "G is bound to the Cat Form spell", (g.g1, g.k1))
check(g.r1 == "MULTIACTIONBAR1BUTTON1", "R bound by the layout", g.r1)
check(
    g.BIND["R"] == "JUMP" and g.BIND["F"] == "MOVEFORWARD" and g.BIND["G"] is None,
    "/dk load backup puts the old keys back",
    dict(g.BIND),
)
L.execute("SlashCmdList.DRUIDKIT('bars')")
check(
    g.k2 is None and g.BIND["G"] == "SPELL Cat Form",
    "after the backup, /dk bars binds Cat Form again",
    (g.k2, g.BIND["G"]),
)
L, g = setup()
L.execute(r"""
DruidKitDB.catKeySet = "META-F"; BIND = { G = "INTERACTTARGET" }
SlashCmdList.DRUIDKIT('bars')
""")
check(g.BIND["G"] == "INTERACTTARGET", "a /dk catkey choice keeps G as it was", g.BIND["G"])

# 16: Alt+H twice in combat toggles the queued mode back, not the same mode twice.
L, g = setup()
L.execute(r"""
COMBAT = true
DruidKit_ToggleMode(); DruidKit_ToggleMode()
COMBAT = false; fire("PLAYER_REGEN_ENABLED")
""")
check(g.DruidKitDB.barMode in (None, "quest"), "two toggles in combat cancel out", g.DruidKitDB.barMode)

# 15: healing/questing swap fills learned melee spells as /startattack macros.
L, g = setup()
L.execute(r"""
DruidKitDB.layouts.mode_heal = {}
SlashCmdList.DRUIDKIT('heal')
""")
check(isinstance(g.PLACED[99], str) and g.PLACED[99].startswith("macro"), "Maul comes back as a macro", g.PLACED[99])

# 14: the secure herb button is only hidden out of combat.
L, g = setup()
L.execute(r"""
herb = made[1]; herb.shown = true
COMBAT = true
SlashCmdList.DRUIDKIT('herbs')
inCombat = herb.shown
COMBAT = false; fire("PLAYER_REGEN_ENABLED")
""")
check(
    g.inCombat is True and g.herb.shown is False,
    "herb button hides after combat, not in it",
    (g.inCombat, g.herb.shown),
)

# 13: opening the guide again reuses its tab buttons.
L, g = setup()
L.execute(r"""
function tabCount() local n=0 for _,f in ipairs(made) do if f.edge then n=n+1 end end return n end
DruidKit_ToggleGuide(); first = tabCount()
DruidKit_ToggleGuide(); DruidKit_ToggleGuide(); DruidKit_OpenTab(2); DruidKit_OpenTab(3)
again = tabCount()
""")
check(g.first == 8 and g.again == 8, "tab buttons are built once", (g.first, g.again))
done("core_bars_test")
