"""Key map: forms, each form's bar, the bottom bars and Druid Kit keys, read live from bindings and buttons."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
BIND = { SHAPESHIFTBUTTON1 = "F", SHAPESHIFTBUTTON3 = "CTRL-F3", ACTIONBUTTON3 = "3", ACTIONBUTTON9 = "9",
         MULTIACTIONBAR1BUTTON3 = "SHIFT-1", DRUIDKIT_STEPS = "ALT-N" }
function GetBindingKey(b) return BIND[b] end
FORMS = { "Bear Form", "Aquatic Form", "Cat Form" }
function GetNumShapeshiftForms() return #FORMS end
function GetShapeshiftFormInfo(i) return "icon" .. i, FORMS[i] end
SLOTS = { [3] = { "spell", 1 }, [9] = { "spell", 2 }, [75] = { "macro", 7 }, [99] = { "spell", 3 }, [63] = { "spell", 4 } }
SPELLS = { "Moonfire", "Omen of Clarity", "Maul", "Mark of the Wild" }
C_ActionBar = { HasAction = function(s) return SLOTS[s] ~= nil end,
                GetActionInfo = function(s) local x = SLOTS[s]; if x then return x[1], x[2] end end }
C_Spell = { GetSpellName = function(id) return SPELLS[id] end }
function GetMacroInfo(id) return id == 7 and "DK Claw" or nil end
function GetActionTexture(s) return "tex" .. s end
BINDING_NAME_DRUIDKIT_STEPS = "Show / hide route steps and arrow"
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute("""
DATA = DruidKit_KeymapData()
DruidKit_ShowKeymap()
""")
data = {sec[1]: [(row[1], row[2]) for row in sec[2].values()] for sec in L.globals().DATA.values()}
print(data)
check(
    ("F", "Bear Form") in data["Forms (shapeshift)"] and ("Ctrl+F3", "Cat Form") in data["Forms (shapeshift)"],
    "forms with their keys",
    data["Forms (shapeshift)"],
)
check(("no key", "Aquatic Form") in data["Forms (shapeshift)"], "a form with no key says so", "")
check(
    ("3", "Moonfire") in data["Caster (no form)"] and ("9", "Omen of Clarity") in data["Caster (no form)"],
    "caster bar keys",
    data["Caster (no form)"],
)
check(("3", "Claw (keeps auto attack on)") in data["Cat Form"], "Cat bar shows the melee macro as its spell", "")
check(("3", "Maul") in data["Bear Form"], "Bear bar", "")
check(("Shift+1", "Mark of the Wild") in data["Bottom left bar"], "bottom-left bar with Shift keys", "")
check(("Alt+N", "Show / hide route steps and arrow") in data["Druid Kit and movement"], "Druid Kit keys", "")
opened = L.eval("""(function() for _, f in ipairs(frames) do
  if f.sub and f.sub.text and f.sub.text:find("Read live") then return f.shown end end end)()""")
check(opened is True, "the window opens", opened)
done("keymap_test")
