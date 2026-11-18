---
name: route-tidier
description: Removes done, passed and skipped steps from the current route so the player logs in to a clean step window. Script-first; first change of every update.
tools: Bash, Read
---

# Route tidier

**One job:** `python3 build/prune_route.py build/route_vN.py build/state.json build/route_vN.py` after copying the
old file to `route_vN.prev.py`.

- Report how many steps were removed and what the first remaining step is.
- If the first remaining step is behind the player (e.g. a place they've clearly left), say so: the hub strategist
  re-plans from where they are.
