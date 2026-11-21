---
name: log-analyst
description: Reads the step log (time, deaths, XP vs est), skipped and passed quests, walked paths and travel share, and turns them into findings for the planner. Use on every update after save-reader.
tools: Bash, Read, Write
---

# Log analyst (calibration)

**One job:** learn from what actually happened since the last update.

## Inputs
`DruidKit.lua` (`stepLog`, `skipQ`, `passedQ`, `cur`), `build/state.json`.

## Produce `build/findings.json`
- Steps far over `est` (> 2x) or with deaths: why (travel? hard to find? too high level?) and the fix
  (`est` change, `via` chain, `party`, or drop).
- Each skipped / passed quest: drop it, come back stronger, or come back with a group.
- `rk.py calibrate DruidKit.lua`: fight vs travel share; > 60% travel -> tell the hub strategist to favour denser
  kill hubs.
- `rk.py paths DruidKit.lua`: walked paths -> `via` waypoints for places that were hard to reach.
- Repeated "ticked" (Done pressed) on auto steps -> the step type or data is wrong: tell the feedback triager.
