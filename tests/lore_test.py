"""Lore: quest text is kept at the quest giver (even with auto-accept), shown on parchment with the Lore button,
follows the step you look at, and shows the next quest on travel steps. Step window uses the Druid panel."""
from lupa.lua51 import LuaRuntime
from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
UISpecialFrames = {}
function UnitName() return "Cu" end
function UnitClass() return "Druid" end
function GetQuestText() return "Greetings, $n. The $c of the grove must help us.$B$BGo." end
function GetObjectiveText() return "Bring 8 Murloc Fins." end
function GetRewardText() return "Thank you, friend." end
DruidKitRoute = { id = "l1", sections = { { title = "S", steps = {
  { ["do"] = "accept", q = 150, name = "Murloc Poachers", at = { "Redridge Mountains", 22.6, 47.4 } },
  { ["do"] = "fly", to = "Stormwind" },
  { ["do"] = "complete", q = 150, name = "Murloc Poachers", at = { "Redridge Mountains", 45.3, 59.3 } },
} } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
function fire(e, a) ev.on_OnEvent(ev, e, a) end
fire("PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
R = {}
R[1] = DruidKitSteps.loreBtn and DruidKitSteps.loreBtn.text
CURQ = 150; CURTITLE = "Murloc Poachers"
fire("QUEST_DETAIL")
R[2] = DruidKitDB.lore[150] and DruidKitDB.lore[150].text
R[3] = DruidKitDB.lore[150] and DruidKitDB.lore[150].obj
R[4] = ACCEPTED
DruidKit_ToggleLore(true)
R[5] = DruidKitLore:IsShown() and true or false
R[6] = DruidKitLore.title:GetText()
R[7] = DruidKitLore.kind:GetText()
R[8] = DruidKitSteps.loreBtn.text
R[9] = DruidKitDB.loreShown
DruidKit_ToggleLore(false)
R[10] = DruidKitLore:IsShown() and true or false
R[11] = DruidKitSteps.crest ~= nil
""")
r = list(L.globals().R.values())
print(r)
check(r[0] == "Lore", "step window has a Lore button", r[0])
check(r[1] == "Greetings, Cu. The Druid of the grove must help us.\n\nGo.", "quest text is kept, with your name and class", r[1])
check(r[2] == "Bring 8 Murloc Fins.", "objectives are kept", r[2])
check(r[3] == 150, "auto-accept still accepts", r[3])
check(r[4] is True, "Lore shows the parchment", r[4])
check(r[5] == "Murloc Poachers", "lore title is the quest", r[5])
check(r[6] == "Next quest on your path", "travel step shows the next quest", r[6])
check(r[7] == "Lore", "button label stays short (fits 64 px)", r[7])
check(r[8] is True, "lore choice is remembered", r[8])
check(r[9] is False, "Hide lore hides it", r[9])
check(r[10] is True, "step window has the Druid crest", r[10])
# Buff button: loaded with the next elixir; hard-fight hint on group steps.
L.execute(r"""
DruidKit_NextBuff = function() return { name = "Elixir of Minor Defense", count = 6, spell = "Lesser Armor" }, { 1 } end
DruidKitBuffButton.SetAttribute = function(s, k, v) s.attr = s.attr or {}; s.attr[k] = v end
DruidKit_StepsEvaluate()
B = { DruidKitBuffButton.attr and DruidKitBuffButton.attr.item, DruidKitBuffButton.attr and DruidKitBuffButton.attr.type, DruidKitBuffButton.tip }
""")
b = list(L.globals().B.values())
check(b[0] == "Elixir of Minor Defense" and b[1] == "item", "Buff button uses the next elixir", b)
done("lore_test")
