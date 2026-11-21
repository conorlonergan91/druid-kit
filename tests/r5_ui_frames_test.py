"""Window positions: the step window, lore, list windows and the party view take their spot from DruidKitPos and save
drags there; /dk party reset uses the same reset as /dk resetpos."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE, source

STUB = r"""
CALLS = {}
DruidKitPos = {
  place = function(f, name) CALLS[#CALLS+1] = "place " .. tostring(name or f.myname) end,
  save = function(f, name) CALLS[#CALLS+1] = "save " .. tostring(name or f.myname) end,
  saved = function() end,
  reset = function(name) CALLS[#CALLS+1] = "reset " .. tostring(name) end,
}
function SEEN(s) for _, c in ipairs(CALLS) do if c == s then return true end end return false end
"""

# Step window and lore
SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(STUB)
L.execute(r"""
DruidKitRoute = { id = "p", sections = { { title = "S", steps = { { ["do"] = "accept", q = 7, name = "Q", npc = "N" } } } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
DruidKit_ToggleSteps(true)
DruidKitSteps.on_OnDragStop(DruidKitSteps)
DruidKit_ToggleLore(true)
""")
g = L.globals()
check(g.SEEN("place steps"), "the step window takes its spot from the table", list(g.CALLS.values()))
check(g.SEEN("save steps"), "dragging the step window saves its spot", list(g.CALLS.values()))
check(g.SEEN("place lore"), "the lore parchment takes its spot from the table", list(g.CALLS.values()))

# List windows (Style) and the party view
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(
    (HERE / "mocks" / "ui.lua")
    .read_text(encoding="utf-8")
    .replace(
        "function CreateFrame() local f=mkobj(); frames[#frames+1]=f; return f end",
        "function CreateFrame(k,n) local f=mkobj(); f.myname=n; frames[#frames+1]=f; if n then _G[n]=f end; return f end",
    )
)
L.execute(STUB)
L.execute("UISpecialFrames = {}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
local w = DruidKitStyle.window("DruidKitGoTo", "Go to", "icon", 400, 470)
w.on_OnDragStop(w)
""")
check(L.globals().SEEN("place DruidKitGoTo"), "list windows take their spot from the table")
check(L.globals().SEEN("save DruidKitGoTo"), "dragging a list window saves its spot")

PARTY = (HERE / "r2_party_test.py").read_text(encoding="utf-8")
L = LuaRuntime(unpack_returned_tuples=True)
setup = PARTY.split('L.execute(source("DruidKit/DruidKit_Party.lua"))', 1)[0].split(
    "L = LuaRuntime(unpack_returned_tuples=True)", 1
)[1]
exec(setup, {"L": L, "mock": __import__("wowenv").mock, "source": source})
L.execute(STUB)
L.execute(source("DruidKit/DruidKit_Party.lua"))
L.execute(r"""
ev=nil for _,f in ipairs(frames) do if f.on_OnEvent then ev=f end end
ev.on_OnEvent(ev,"PLAYER_LOGIN")
DruidKit_PartyCommand("reset")
""")
p = L.globals()
check(p.SEEN("place party"), "the party view takes its spot from the table", list(p.CALLS.values()))
check(p.SEEN("reset party"), "/dk party reset is /dk resetpos party", list(p.CALLS.values()))
done("r5_ui_frames_test")
