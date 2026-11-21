# Task: plan the fastest solo levelling route for a Night Elf Druid, level 1 to 30, on WoW Forever (Classic-era quests).

Inputs (only these):
- rules file given to you (follow it; it is the planning method being tested)
- quests.csv: every quest a Night Elf Druid can do up to level ~34 in nearby zones: id, name, level, min_level, zone,
  start NPC + zone + x,y, end NPC + zone + x,y, prerequisite quest ids, next in chain, XP reward, objectives.
- XP needed per level (1->2 ... 19->20): 400 900 1400 2100 2800 3600 4500 5400 6500 7600 8800 10100 11400 12900 14400 16000 17700 19400 21300, then (20->21 ... 29->30) 23400 25700 28100 30500 33100 35400 38200 41000 43900 46800 (approx above 25).
  Roughly 35-45% of levelling XP comes from kills while questing; the rest from quests.
- Facts: Night Elves start in Shadowglen (Teldrassil). Dolanaar is the Teldrassil hub; Darnassus has the druid trainer;
  Rut'theran Village (Teldrassil coast) has the boat to Auberdine (Darkshore hub) and a flight master. Druids learn
  Teleport: Moonglade at 10 (Bear Form quest at 10). No dungeons: play solo. Flight paths must be discovered on foot first.

Rules for this test:
- You may run planner/rk.py (and write small scripts of your own in this folder). Do NOT look up existing levelling guides (RestedXP, Joana, Questie routes, wowhead guides, etc.) or any file outside
  this folder. Plan from the data and the rules only. Do not use web search.
- Simulate XP as you go so quests are done near their level (min_level is a hard gate).

Output: write plan.json in this folder:
{"start": {"home": "Shadowglen", "flights": []},
 "events": [ {"kind": "accept"|"turnin"|"abandon", "q": <quest id>} |
             {"kind": "home", "at": "<town>"} (set hearthstone) | {"kind": "hearth", "text": "Hearth to <town>"} |
             {"kind": "fp", "at": "<town>"} (learn its flight path; needed before any flight to or from it) |
             {"kind": "train"} | {"kind": "grind", "to": <level as number>, "text": "<where>"} |
             {"kind": "travel", "text": "<how>"} ... in order],
 "summary": "<= 15 lines: zone order with level ranges and the main decisions"}
Every turnin must come after its accept, and after its prerequisites are turned in. A hearth needs an earlier
"home" in that town; a flight ("travel" text "Fly to <town>") needs both ends learned with "fp" first. You start
with no flight paths and the hearthstone set to Shadowglen.

Plan all the way to 30. Choices before 20 should already account for where you will be levelling at 20-30.
