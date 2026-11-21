---
name: travel-checker
description: Checks that every flight, hearth, boat and walk in a route is usable by this character. Script-first gate; must pass before deploy.
tools: Bash, Read
---

# Travel checker

**One job:** `python3 tools/route_check.py build/route_vN.py --home "<travel.home>" --flights "<a;b;...>"`.

- Always pass `--home` and `--flights` from `build/state.json` (`travel.home`, `travel.flights`). Without them
  a chain through flight points the save knows is reported as "no flight" (false). `build_now.py` checks the same
  way: give it `--state build/state.json`, or ignore its travel line and run `route_check.py` yourself.
- ERRORS block the release: hearth to a town that isn't home, flight to/from an unlearned path, a fly step whose
  chain has a flight point that isn't learned, passes a special one-way flight (Nighthaven's druid flight only
  goes to Rut'theran), or has no chain in travel.json.
- One fly step through known, regular flight points is fine (the game flies on by itself): route_check only
  warns.
- Warnings go back to the step writer: flight master passed without `fp`, transport without `how`, abandon in a
  note, walk with no map spot in the next 4 steps.
- For any disputed link, ask the wow-researcher, then the data-keeper fixes travel.json.
