"""The client paints an unmet "Requires Engineering (150)" line red. That red line alone must not call the item
unusable: a rank you'll reach is banked, never sold; a profession you don't have at all is still sold."""

from expect import check, done
from wowenv import runtime, source

RED = "{ r = 1, g = 0.1, b = 0.1 }"


def run(extra):
    L = runtime("ui")
    L.execute("UISpecialFrames={}")
    L.execute(source("DruidKit/DruidKit_Style.lua"))
    L.execute(
        r"""
function GetMoney() return 0 end
SOLD = {}
C_Container.UseContainerItem = function(b, s) SOLD[#SOLD+1] = BAG[b][s]; BAG[b][s] = nil end
DruidKitDB = {}
TIP = {}
C_TooltipInfo = { GetHyperlink = function(l) local t = TIP[KEY(l)]
  return { lines = t and { { leftText = t, leftColor = """
        + RED
        + r""" } } or {} } end }
LINES = { { "Professions", true, true }, { "Engineering", false, false, 100 } }
function GetNumSkillLines() return #LINES end
function GetSkillLineInfo(i) local l = LINES[i]; if l then return l[1], l[2], l[3], l[4] end end
"""
        + extra
        + "\nC_Container.GetContainerNumSlots = function(b) return b == 0 and #BAG[0] or 0 end"
    )
    L.execute(source("DruidKit/DruidKit_Bags.lua"))
    L.execute(r"""
MerchantFrame.IsShown = function() return true end
ev = frames[1]; ev.on_OnEvent(ev, 'PLAYER_LOGIN'); ev.on_OnEvent(ev, 'MERCHANT_SHOW')
MerchantFrame.IsShown = function() return false end
DruidKit_ToggleBags()
rows = {} for _, f in ipairs(allfs) do if f.text ~= "" then rows[#rows+1] = f.text end end
""")
    g = L.globals()
    return [g.SOLD[k] for k in g.SOLD], "\n".join(g.rows.values())


sold, text = run(r"""
ITEMS.gog = {"Flying Goggles","gog",1,20,10,"","",1,"INVTYPE_HEAD",1,300,4,1}
ITEMS.hat = {"Tailored Hat","hat",1,20,10,"","",1,"INVTYPE_HEAD",1,200,4,1}
STATS.gog = {ITEM_MOD_STAMINA_SHORT=1}; STATS.hat = {ITEM_MOD_STAMINA_SHORT=1}
TIP.gog = "Requires Engineering (150)"; TIP.hat = "Requires Tailoring (75)"
BAG[0] = {"gog", "hat"}
""")
check("gog" not in sold, "red 'Requires Engineering (150)' at Engineering 100: goggles not sold", sold)
bank = text.split("Bank these")[1].split("Sell at a vendor")[0] if "Bank these" in text else ""
check("Flying Goggles" in bank and "needs engineering 150 (you're 100)" in bank.lower(), "the goggles are banked", text)
check("hat" in sold, "a profession you don't have is still sold", sold)
done("r4_bags_redreq_test")
