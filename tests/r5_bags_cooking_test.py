"""Cooking ingredients are kept while Cooking is below its cap (or not learned), or while an unlearned, not-grey
recipe you can learn now uses them: never sold by the autopilot, never in the sell or drop lists, never stored by Bank
check. At the cap with no such recipe they go like any unused material. Bag check's footer counts food by item."""

from expect import check, done
from wowenv import runtime, source


def run(cooking, bag):
    L = runtime("ui")
    L.execute("UISpecialFrames={}")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(
        r"""
function GetMoney() return 0 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
C_Container.GetContainerItemQuestInfo = function() return {} end
DruidKitDB = { reagentsFixed = true, reagents = {}, reagentsAll = { Cooking = { ["Mild Spices"] = "Herb Baked Egg" } } }
ITEMS.boar = {"Chunk of Boar Meat","boar",1,5,0,"","",10,"",1,10,7,8}
ITEMS.crawler = {"Crawler Meat","crawler",1,15,0,"","",10,"",1,12,7,8}
ITEMS.fish = {"Raw Brilliant Smallfish","fish",1,5,0,"","",20,"",1,1,0,5}
ITEMS.cheese = {"Dalaran Sharp","cheese",1,15,5,"","",20,"",1,25,0,5}
ITEMS.bread = {"Tough Hunk of Bread","bread",1,5,1,"","",20,"",1,1,0,5}
ITEMS.water = {"Refreshing Spring Water","water",1,5,1,"","",20,"",1,1,0,5}
LINES = { { "Secondary Skills", true, true } """
        + cooking
        + r""" }
function GetNumSkillLines() return #LINES end
function GetSkillLineInfo(i) local l = LINES[i]; if l then return l[1], l[2], l[3], l[4], 0, 0, l[5] end end
BankFrame = { IsShown = function() return false end }
BAG[0] = """
        + bag
        + r"""
BAG[-1] = {}
C_Container.GetContainerNumSlots = function(b) if b == 0 then return #BAG[0] elseif b == -1 then return 1 end return 0 end
"""
    )
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute(source("DruidKit/DruidKit_Bank.lua"))
    L.execute(r"""
function fire(e) for _, f in ipairs(frames) do if f.on_OnEvent then f.on_OnEvent(f, e) end end end
function shown() local t = {} for _, f in ipairs(allfs) do if f.text ~= "" then t[#t+1] = f.text end end return table.concat(t, "\n") end
fire('PLAYER_LOGIN')
allfs = {}; fire('BANKFRAME_OPENED'); BANKTEXT = shown(); fire('BANKFRAME_CLOSED')
allfs = {}; DruidKit_ToggleBags(); BAGTEXT = shown()
MerchantFrame.IsShown = function() return true end
fire('MERCHANT_SHOW')
""")
    g = L.globals()
    return [g.SOLD[k] for k in g.SOLD], g.BAGTEXT, g.BANKTEXT


def section(text, head):
    if head not in text:
        return ""
    rest = text.split(head)[1]
    for nxt in (
        "Bank these",
        "Quest items to check",
        "Auction House",
        "Sell at a vendor",
        "Bags full?",
        "Never suggests",
    ):
        rest = rest.split(nxt)[0]
    return rest


COOK = "Cooking ingredients you're keeping"
BAG = '{ "boar", "fish", "crawler" }'

sold, text, bank = run(', { "Cooking", false, false, 40, 75 }', BAG)
kept = section(text, COOK)
check(sold == [], "Cooking 40/75: the autopilot sells no raw meat or fish", sold)
check(
    all(n in kept for n in ("Chunk of Boar Meat", "Raw Brilliant Smallfish", "Crawler Meat"))
    and "Cooking 40/75: cook it for skill" in kept,
    "below the cap: listed as kept with the reason",
    text,
)
check(
    "Chunk of Boar Meat" not in section(text, "Sell at a vendor") + section(text, "Bags full?"),
    "never in the sell or drop lists",
    text,
)
check("Chunk of Boar Meat" not in bank, "Bank check doesn't offer to store it", bank)

sold, text, bank = run("", BAG)
check(
    sold == [] and "Cooking not learned: train it, then cook this for skill" in section(text, COOK),
    "no Cooking yet: kept, train it",
    (sold, text),
)

sold, text, bank = run(', { "Cooking", false, false, 150, 150 }', BAG)
kept = section(text, COOK)
check(sold == ["boar"], "at the cap, no learnable non-grey recipe: sold as before", sold)
check("Chunk of Boar Meat" in bank, "and Bank check offers to store it as before", bank)
check(
    "Crawler Meat" in kept and "Trainable recipe Crab Cake uses it" in kept,
    "at the cap, a trainable recipe that still gives skill uses it: kept",
    text,
)
check("Crawler Meat" not in bank, "Bank check leaves it in your bags", bank)

sold, text, _ = run(', { "Cooking", false, false, 40, 75 }', '{ "cheese", "bread", "water" }')
check(
    "your best 2 food and 2 drink items" in text and "drink stacks" not in text,
    "footer says items, not stacks",
    text,
)
done("r5_bags_cooking_test")
