"""Vendor button: a menu of vendor kinds in this zone (nearest of each); a click points the arrow there."""

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
DruidKitRoute = { id = "vm", sections = { { title = "S", steps = { { ["do"] = "note", text = "x" } } } } }
DruidKitDB = {}
DruidKitVendors = {
  { "Wetlands", 10.4, 60.6, "Kersok Prond", "Tradesman", false },
  { "Wetlands", 10.7, 61.0, "Innkeeper Helbrek", "Innkeeper", false },
  { "Wetlands", 11.5, 59.9, "Brahnmar", "Armorer", true },
  { "Wetlands", 8.3, 56.5, "Falkan Armonis", "Reagent Vendor", false },
  { "Dun Morogh", 47.4, 52.5, "Innkeeper Belm", "Innkeeper", false },
}
C_Map = { GetBestMapForUnit = function() return 56 end,
  GetPlayerMapPosition = function() return { GetXY = function() return 0.105, 0.605 end } end }
function DruidKit_FindMap(z) return z == "Wetlands" and 56 or 27 end
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_VendorMenu(nil)
ROWS = {}
for _, r in ipairs(DruidKitVendorMenu.rows) do if r.shown then ROWS[#ROWS + 1] = r.text end end
GOTO = {}
for _, r in ipairs(DruidKitVendorMenu.rows) do if r.text:find("^Repair") then r.on_OnClick() end end
""")
rows = list(L.globals().ROWS.values())
goto = list(L.globals().GOTO.values())
print(rows, goto)
txt = "\n".join(rows)
check("Repair: Brahnmar" in txt, "repair row names the armorer who repairs", txt)
check("Food and drink: Innkeeper Helbrek" in txt, "food row: the innkeeper", txt)
check("Reagents: Falkan Armonis" in txt, "reagents row", txt)
check("Belm" not in txt, "only vendors in this zone", txt)
check("Bags" not in txt, "no row for a kind with no vendor here", txt)
check(goto == ["Wetlands 11.5,59.9"], "clicking Repair points the arrow at Brahnmar", goto)
done("vendormenu_test")
