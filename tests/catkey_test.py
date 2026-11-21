"""Cat Form goes on G (else Cmd+F); autorun goes on Cmd+W; keys in use are kept unless forced."""

from expect import check, done
from wowenv import runtime, source


def setup(bind, known=True):
    L = runtime("ui")
    L.execute(
        r"""
UISpecialFrames={}; SlashCmdList={}; DruidKitDB={}
GetTime=function() return 1 end
C_Timer={After=function(d,f) f() end, NewTicker=function() end}
IDS={["Cat Form"]=768}
KNOWNCAT=%s
C_Spell={GetSpellInfo=function(n) return IDS[n] and {spellID=IDS[n]} end}
C_SpellBook={IsSpellKnown=function(id) return id==768 and KNOWNCAT end}
IsSpellKnown=function(id) return id==768 and KNOWNCAT end
function SetBinding(k,a) if k=="BAD" then return false end BIND[k]=a return true end
function SetBindingSpell(k,s) BIND[k]="SPELL "..s return true end
function SaveBindings() end function GetCurrentBindingSet() return 1 end
function InCombatLockdown() return false end
StaticPopupDialogs = StaticPopupDialogs or {}; StaticPopup_Show = function(n) RELOAD=(RELOAD or 0)+1 end; ReloadUI=function() end
GetShapeshiftForm=function() return 0 end
function UnitIsDeadOrGhost() return false end
function GetBindingKey() end
BIND=%s
function GetBindingAction(k) return BIND[k] end
"""
        % ("true" if known else "false", bind)
    )
    L.execute(source("DruidKit/DruidKit_Guide.lua"))
    L.execute(source("DruidKit/DruidKit.lua"))
    return L


L = setup("{}")
L.execute("SlashCmdList.DRUIDKIT('catkey')")
L.execute("SlashCmdList.DRUIDKIT('runkey')")
g = L.globals()
check(g.BIND["G"] == "SPELL Cat Form", "G is Cat Form", g.BIND["G"])
check(g.BIND["META-W"] == "TOGGLEAUTORUN", "Cmd+W is autorun", g.BIND["META-W"])
check(any("Cmd+W now toggles autorun" in p for p in g.printed.values()), "Cmd+W message", "")

L = setup('{G="INTERACTTARGET"}')
L.execute("SlashCmdList.DRUIDKIT('catkey')")
g = L.globals()
check(g.BIND["G"] == "INTERACTTARGET", "G kept when in use", g.BIND["G"])
check(g.BIND["META-F"] == "SPELL Cat Form", "falls back to Cmd+F", g.BIND["META-F"])
L.execute("SlashCmdList.DRUIDKIT('catkey G force')")
check(g.BIND["G"] == "SPELL Cat Form", "force takes G", g.BIND["G"])
L.execute("SlashCmdList.DRUIDKIT('runkey cmd+r')")
check(g.BIND["META-R"] == "TOGGLEAUTORUN", "cmd+r typed works", g.BIND["META-R"])

L = setup("{}", known=False)
L.execute("SlashCmdList.DRUIDKIT('keys')")
g = L.globals()
check(g.BIND["G"] is None, "no Cat Form, no G", g.BIND["G"])
check(g.BIND["META-W"] == "TOGGLEAUTORUN", "/dk keys sets Cmd+W", g.BIND["META-W"])
done("catkey_test")
