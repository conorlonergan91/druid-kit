"""Bag check forgets what it read about skills, spells and quests when they change (skill-up, new spell, quest log
update), so a profession item stops being listed as "needs a higher rank" without a bag update."""

from expect import check, done
from wowenv import runtime, source

L = runtime("ui")
L.execute(r"""
UISpecialFrames = {}
DruidKitDB = {}
ITEMS.gog = {"Flying Goggles","gog",1,20,10,"","",1,"INVTYPE_HEAD",1,300,4,1}
C_TooltipInfo = { GetHyperlink = function(l) return { lines = { { leftText = "Requires Engineering (150)" } } } end }
RANK = 100
function GetNumSkillLines() return 2 end
local cf = CreateFrame
CreateFrame = function(...) local f = cf(...); f.RegisterEvent = function(s, e) s.events = s.events or {}; s.events[e] = true end; return f end
function GetSkillLineInfo(i) if i == 1 then return "Professions", true, true end return "Engineering", false, false, RANK end
""")
L.execute(source("DruidKit/DruidKit_Style.lua"))
L.execute(source("DruidKit/DruidKit_Bags.lua"))
L.execute(r"""
ev = frames[1]
R = {}
for _, e in ipairs({ "SKILL_LINES_CHANGED", "LEARNED_SPELL_IN_TAB", "QUEST_LOG_UPDATE" }) do
  RANK = 100; ev.on_OnEvent(ev, "BAG_UPDATE_DELAYED")
  local before = DruidKit_ItemRestriction(LINK("gog"))
  RANK = 150; if ev.events[e] then ev.on_OnEvent(ev, e) end
  R[e] = tostring(before ~= nil and DruidKit_ItemRestriction(LINK("gog")) == nil)
end
""")
R = dict(L.globals().R.items())
check(set(R.values()) == {"true"}, "skill, spell and quest log events refresh what Bag check knows", R)
done("r3_bags_events_test")
