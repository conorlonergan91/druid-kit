"""Forever secret values: the step window's OnUpdate must not test UnitIsAFK when it is secret (19 Nov errors)."""
from lupa.lua51 import LuaRuntime
from expect import check, done
from wowenv import HERE, source

SRC = (HERE / "steps_test.py").read_text(encoding="utf-8")
OPEN = "L.execute(r" + '"' * 3
MOCKS = SRC.split(OPEN, 1)[1].split("DruidKitRoute = {")[0]
L = LuaRuntime(unpack_returned_tuples=True)
L.execute(MOCKS)
L.execute(r"""
SECRET = setmetatable({}, { __index = function() error("secret") end })
function issecretvalue(v) if v == SECRET then CHECKED = true end return v == SECRET end
function UnitIsAFK() return SECRET end
DruidKitRoute = { id = "s", sections = { { title = "S", steps = { { ["do"] = "note", text = "x" } } } } }
DruidKitDB = {}
""")
L.execute(source("DruidKit/DruidKit_Steps.lua"))
L.execute(r"""
for _, f in ipairs(frames) do if f.events and f.events.QUEST_DETAIL then ev = f end end
ev.on_OnEvent(ev, "PLAYER_LOGIN")
ok, err = pcall(ev.on_OnUpdate, ev, 0.5)
secs = DruidKitDB.cur and DruidKitDB.cur.secs
""")
g = L.globals()
check(g.ok is True, "OnUpdate runs with a secret UnitIsAFK", g.err)
check(g.secs == 0.5, "play time still counts", g.secs)
check(g.CHECKED is True, "the AFK value is checked for secrecy before any test", g.CHECKED)
done("secret_test")
