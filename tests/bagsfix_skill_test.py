"""Recipes and professions: a collapsed skill header in the skill list must not make a profession look missing
(that sold recipes you can learn); an unreadable skill list means keep, never sell."""

from expect import check, done
from wowenv import runtime, source


def run(skills_lua):
    L = runtime("ui")
    L.execute(
        r"""
UISpecialFrames = {}
function GetTime() return 100 end
ITEMS.stew = {"Recipe: Westfall Stew","stew",1,15,0,"","",1,"",1,100,9,5}
BAG[0] = { "stew" }
C_Container.GetContainerNumSlots = function(b) return b == 0 and 1 or 0 end
C_Container.GetContainerItemQuestInfo = function() return {} end
C_TooltipInfo = { GetHyperlink = function(l) if KEY(l) == "stew" then return { lines = { { leftText = "Requires Cooking (75)" } } } end return { lines = {} } end }
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD + 1] = BAG[b][s] end
function GetMoney() return 0 end
DruidKitDB = {}
"""
        + skills_lua
    )
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute(r"""
verdict = DruidKit_RecipeCheck(LINK("stew"))
frames[1].on_OnEvent(frames[1], "PLAYER_LOGIN")
MerchantFrame.IsShown = function() return true end
frames[1].on_OnEvent(frames[1], "MERCHANT_SHOW")
""")
    return L.globals()


# Classic skill list: the Secondary Skills header is collapsed, Cooking 80 is under it.
g = run(r"""
LINES = { { "Professions", true, true }, { "Secondary Skills", true, false } }
HIDDEN = { { "Cooking", false, false, 80 } }
function GetNumSkillLines() return #LINES end
function GetSkillLineInfo(i) local l = LINES[i]; if l then return l[1], l[2], l[3], l[4] end end
function ExpandSkillHeader(i) if LINES[i][1] == "Secondary Skills" and not LINES[i][3] then LINES[i][3] = true; table.insert(LINES, i + 1, HIDDEN[1]) end end
function CollapseSkillHeader(i) if LINES[i][1] == "Secondary Skills" and LINES[i][3] then LINES[i][3] = false; table.remove(LINES, i + 1) end end
""")
check(g.verdict == "learn", "collapsed header: the recipe is still 'learn'", g.verdict)
check(list(g.SOLD.values()) == [], "and it is never sold", list(g.SOLD.values()))
check(
    len(list(g.LINES.values())) == 2 and g.LINES[2][3] is False,
    "the header is collapsed again afterwards",
    [tuple(x.values()) for x in g.LINES.values()],
)

# Skill list not readable yet (0 lines): unknown, so keep it.
g = run(r"""
function GetNumSkillLines() return 0 end
function GetSkillLineInfo() end
""")
check(g.verdict != "noskill" and g.verdict != "noclass", "unreadable skill list: not 'you don't have it'", g.verdict)
check(list(g.SOLD.values()) == [], "unknown skill: recipe never sold", list(g.SOLD.values()))

# Modern client: GetProfessions knows Cooking.
g = run(r"""
function GetProfessions() return nil, nil, nil, nil, 5 end
function GetProfessionInfo(i) if i == 5 then return "Cooking", nil, 80 end end
""")
check(g.verdict == "learn", "GetProfessions: the recipe is 'learn'", g.verdict)
done("bagsfix_skill_test")
