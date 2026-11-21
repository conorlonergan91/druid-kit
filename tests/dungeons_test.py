"""Dungeon quests window (/dk dq), quest share helper and quest XP over the XP bar."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute("UISpecialFrames={}")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(r"""
DruidKitDB = {}
DruidKitDungeonData = {
  { name = "Test Hold", quests = {
    { id = 1, name = "Old One", min = 10, level = 15, xp = 1000, giver = "A", at = {"Wetlands", 10, 20} },
    { id = 2, name = "In Log", min = 10, level = 15, xp = 2000, giver = "B", at = {"Wetlands", 11, 21} },
    { id = 3, name = "Open", min = 10, level = 15, xp = 1500, giver = "C", at = {"Wetlands", 12, 22} },
    { id = 4, name = "Too High", min = 30, level = 32, xp = 4000, giver = "D", at = {"Wetlands", 13, 23} },
    { id = 7, name = "Fresh", min = 10, level = 15, xp = 1100, giver = "F", at = {"Wetlands", 15, 25} },
    { id = 5, name = "Chain Two", min = 10, level = 15, xp = 900, giver = "E", at = {"Wetlands", 14, 24}, pre = {6} },
  } },
}
DONE = { [1] = true }
LOG = { { questID = 2, isComplete = true }, { questID = 3, isComplete = false } }
C_QuestLog = {
  IsQuestFlaggedCompleted = function(id) return DONE[id] == true end,
  GetNumQuestLogEntries = function() return #LOG end,
  GetInfo = function(i) return LOG[i] end,
  IsUnitOnQuest = function(u, id) return id == 3 end,
  IsPushableQuest = function() return true end,
  SetSelectedQuest = function(id) SELECTED = id end,
}
PUSHED = {}
function QuestLogPushQuest() PUSHED[#PUSHED + 1] = SELECTED end
function UnitExists(u) return u == "party1" end
function UnitName(u) return "Thig" end
function IsInRaid() return false end
function UnitLevel() return 12 end
function UnitXP() return 1000 end
function UnitXPMax() return 10100 end
function GetTime() return 100 end
GOTO = nil
function DruidKit_GoTo(z, x, y, label) GOTO = { z, x, y, label } end
""")
L.execute(source("DruidKit/DruidKit_Dungeons.lua"))
L.execute(r"""
DruidKit_DungeonQuests()
local w = DruidKitDungeonQuests or nil
R = {}
-- collect the item rows of the dungeon window: find frames created with name text
local names, details = {}, {}
for _, fs in ipairs(allfs) do if type(fs.text) == "string" then names[#names + 1] = fs.text end end
R.all = table.concat(names, "\n")
DruidKit_QuestShare()
R.pushedBefore = #PUSHED
-- press "Share all": the header button's OnClick
for _, f in ipairs(frames) do if f.on_OnClick and f.text == "Share all" then f.on_OnClick() end end
R.pushed = table.concat(PUSHED, ",")
DruidKit_QuestXPBar()
R.xp = DruidKitQuestXP and DruidKitQuestXP.t and DruidKitQuestXP.t.text or ""
for _, fs in ipairs(allfs) do if type(fs.text) == "string" and fs.text:find("Quests to hand in") then R.xp = fs.text end end
""")
R = L.globals().R
allt = R["all"]
print(allt[:2000])
check("Old One" not in allt, "a done quest is not listed", "")
check("In Log" in allt and "ready to hand in" in allt, "a finished quest in the log: ready to hand in", "")
check("Open" in allt and "in your log" in allt, "a quest in the log, not finished: in your log", "")
check("Fresh" in allt and "|cff7fd35bavailable" in allt, "a quest you can take: available", "")
check("Too High" in allt and "needs level 30" in allt, "level-locked quest says the level", "")
check("Chain Two" in allt and "first:" in allt, "chain quest says what comes first", "")
check(R["pushed"] == "2", "Share all pushes the quest the party member lacks (only that one)", R["pushed"])
check("+2000 XP" in R["xp"], "XP bar line sums the finished quests", R["xp"])
done("dungeons_test")
