---
name: step-writer
description: Turns loops into the route file (build/route_vN.py): one action per step with NPC, verified goto, via chains, how, fp/home/abandon steps, sell stops and est. Use after the loop sequencer.
tools: Bash, Read, Write, Edit
---

# Step writer

**One job:** write `build/route_vN.py` (format: `tools/example_route.py`).

## Every step
- Player preferences (RULES v19 lists them with their versions): no collect-from-drops quests over 3 items; no
  packs or fleeing humanoids; solo only near monsters at or below his level (higher only `party=True`); every
  dungeon quest; flights over the tram.
- One action; NPC named; `goto` only from verified data (QuestieDB spawns or research "high").
- `how` when the player needs to *do* something non-obvious: right-click an item that starts a quest, use an item,
  find a cave entrance, board a boat (which pier, which ship, wait, where you land).
- Collect-item steps: `via` chain over every known object spawn in walking order.
- `fp` at every flight master reached for the first time; `home` before any trip that hearths back; `abandon` with
  `qs` for quests to drop; one `fly` step per flight leg.
- A sell stop when the save has < 8 free bag slots, and at the end of each hub.
- `est` from `python3 planner/rk.py minutes ID... --level L` (`quest_minutes`). Set `party=True` on steps the
  sequencer flagged and size their `est` with `--party 3` (`rk.GROUP_SIZE`, the split xpsim uses).
- When quest text and data disagree on the NPC, name both.
- Forever coordinates differ from Classic (Stormwind especially): `tools/coordcheck.py`, never Classic maps.
- Dungeons: `freeBags=20` on the "Find a group" step; inside the run `inside=True` steps (no arrow) in run order and
  `boss` steps with a `tactic` of up to 3 short lines (from dungeon-advisor / combat-coach).

- Levels (RULES v18): run `tools/xpsim.py ROUTE LEVEL XP --done DONE.json`. Fix every ERROR (accept before the
  level is reached). Add a `level` step only where the projection is short, sized to the gap; remove any `level`
  step it reports as not needed. Spots: `tools/coordcheck.py`; danger: `tools/dangercheck.py`; story order:
  `tools/prereqcheck.py`.

Hand the file to travel-checker, bag-advisor and plan-reviewer. Don't deploy.
