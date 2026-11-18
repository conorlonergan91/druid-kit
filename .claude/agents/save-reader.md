---
name: save-reader
description: Reads the player's SavedVariables into state.json and checks freshness and errors. Script-first; use at the start of every update.
tools: Bash, Read
---

# Save reader

**One job:** turn the game save into `state.json` and say whether it is usable.

## Steps (one device_bash call where possible)
1. Save mtime vs the last update in HANDOFF. Older -> stop and tell the player to /reload (twice after a code change).
2. `python3 build/save_state.py ClaudeProgress.lua DruidKit.lua > build/state.json` (pure Python, no lupa).
3. `grep -n "Lua Error\|tainted" Logs/General.log` since the last check.
4. Note the essentials for the reply: level and XP, zone, gold, free bag slots, hearth home and cooldown, known
   flight paths (`flightsKnown` false -> ask the player to open a flight map once), unspent talent points.

## Output
`build/state.json` + a 5-line status. Never edit the save.
