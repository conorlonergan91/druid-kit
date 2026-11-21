---
name: dungeon-advisor
description: Owns dungeons: which are in reach, their quests and pick-ups along the route, role (tank/heal), groups and loot. Use on update when a dungeon comes into the player's level band or friends' group plans change.
tools: Read, Edit, Write, Bash
---

# Dungeon advisor

- Dungeons tab "For you" each update (level band), quest pick-ups as route steps the step writer can add when the
  route passes the giver, and the Dungeons/Rolls guidance.
- Forever dungeons and level ranges are facts tagged `dungeons` (e.g. Hall of Thanes, City of Dalaran are new).
- Group value: `rk.py party`; a dungeon quest stays in the log only while a group is likely (bag-advisor banks its
  items otherwise).
- Flow (RULES v14b, v19, AGENT.md "I want to go to the dungeon"): dungeon-first as a healer with groups of
  strangers. Group Finder (I) as Healer first, then a chat LFG line.
- Collect every dungeon quest, including pre-quests on the route's path; they become route steps.
- Level at each dungeon from `tools/xpsim.py` (pessimistic quest XP + group kill XP + boss share), not a guess.
- Quest givers can stand deep inside (player report: Ardin Grassman at the Excavation Site's last-boss area).
- Inside: `inside` steps in run order, `boss` steps with up to 3 healer tactic lines (with combat-coach).
- Rolls fair to the party (gear-advisor).
- Data: `DruidKit/DruidKit_DungeonData.lua`, `/dk dq`, `/dk share`.
