"""Quests under a collapsed zone header still reach the save (ClaudeProgress) and the step window (IsOnQuest)."""

from lupa.lua51 import LuaRuntime

from expect import check, done
from wowenv import HERE

L = LuaRuntime(unpack_returned_tuples=True)
src = (HERE.parent / "ClaudeProgress" / "ClaudeProgress.lua").read_text(encoding="utf-8")
L.execute(r"""
ROWS = { { title = "Duskwood", isHeader = true }, { title = "Eight-Legged Menaces", questID = 245 },
         { title = "Stormwind City", isHeader = true, isCollapsed = true, kids = { { title = "Underground Assault", questID = 2040 } } } }
local function visible()
  local out = {}
  for _, r in ipairs(ROWS) do
    out[#out + 1] = r
    if r.isHeader and not r.isCollapsed then for _, k in ipairs(r.kids or {}) do out[#out + 1] = k end end
  end
  return out
end
C_QuestLog = {
  GetNumQuestLogEntries = function() return #visible() end,
  GetInfo = function(i) return visible()[i] end,
  ExpandQuestHeader = function(i) visible()[i].isCollapsed = false end,
  CollapseQuestHeader = function(i) visible()[i].isCollapsed = true end,
  IsComplete = function() return false end, GetQuestObjectives = function() return {} end,
}
""")
# Pull snapshotQuests out of the addon file and run it.
body = src[src.index("local function expandAll()") : src.index("local function snapshotQuests()")]
fn = src[src.index("local function snapshotQuests()") :]
fn = fn[: fn.index("\nend\n") + 5]
helpers = "local function safe(f, ...) if not f then return nil end local ok, a, b, c, d, e, g, h, k = pcall(f, ...) if ok then return a, b, c, d, e, g, h, k end end\n"
helpers += "local function objectivesClassic() return {} end\n"
# The full snapshot (logout, /claude) opens the headers around it.
L.execute(helpers + body + fn + "\nlocal closed = expandAll(); Q = snapshotQuests(); collapseAgain(closed)")
g = L.globals()
titles = [q.title for q in g.Q.values()]
print(titles)
check("Underground Assault" in titles, "a quest under a collapsed header is in the snapshot", titles)
check(g.ROWS[3].isCollapsed is True, "the header is collapsed again afterwards", g.ROWS[3].isCollapsed)
done("questlog_test")
