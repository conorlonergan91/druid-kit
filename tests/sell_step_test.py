"""Sell steps: say how many items the vendor autopilot would sell (or that there's nothing), and tick themselves once
you talk to a vendor."""
from lupa.lua51 import LuaRuntime
from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
DruidKitRoute = { id = "s1", sections = { { title = "S", steps = {
  { ["do"] = "note", text = "Sell and repair at Dorin Songblade", at = { "Redridge Mountains", 25.8, 46.4 } },
  { ["do"] = "note", text = "next" },
} } } }
DruidKitDB = {}
SELLN = 0
DruidKit_SellCount = function() return SELLN end
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
R = { DruidKitSteps.detail.text }
SELLN = 4; DruidKit_StepsEvaluate()
R[2] = DruidKitSteps.detail.text
ev.on_OnEvent(ev, "MERCHANT_SHOW")
R[3] = DruidKitDB.routeStep
""")
r = list(L.globals().R.values())
print(r)
check("Nothing to sell right now" in r[0], "sell step says when there's nothing to sell", r[0])
check("4 items to sell" in r[1], "sell step says how many items the vendor visit sells", r[1])
check(r[2] == 2, "talking to a vendor ticks the sell step", r[2])
done("sell_step_test")
