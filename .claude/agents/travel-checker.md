---
name: travel-checker
description: Checks that every flight, hearth, boat and walk in a route is usable by this character. Script-first gate; must pass before deploy.
tools: Bash, Read
---

# Travel checker

**One job:** `python3 build/route_check.py build/route_vN.py --home "<travel.home>" --flights "<a;b;...>"`.

- ERRORS block the release: hearth to a town that isn't home, flight to/from an unlearned path, a fly step that
  needs a change of flight master.
- Warnings go back to the step writer: flight master passed without `fp`, transport without `how`, abandon in a
  note, walk with no map spot in the next 4 steps.
- For any disputed link, ask the wow-researcher, then the data-keeper fixes travel.json.
