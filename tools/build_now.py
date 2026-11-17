"""Put the route into guide.json and rebuild the Now tab from it.

Usage: python3 tools/build_now.py tools/example_route.py tools/example_guide.json "updated text" "You line" ...
"""

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import route_check  # noqa: E402

Y, G, R, LEAF = "|cffffd100", "|cff9d9d9d", "|r", "|cff7fd35b"
VERB = {
    "accept": "Accept",
    "turnin": "Hand in",
    "complete": "Do",
    "goto": "Go to",
    "fly": "Fly to",
    "hearth": "Hearth to",
    "train": "Train",
    "level": "Level",
    "note": "Do",
    "fp": "Learn flight path",
    "home": "Set hearth",
    "abandon": "Abandon",
}


def load(path):
    spec = importlib.util.spec_from_file_location("route", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ROUTE


def line(n, st):
    d = st["do"]
    if d in ("accept", "turnin"):
        main = f"{Y}{VERB[d]}:{R} {st['name']}" + (f" ({st['npc']})" if st.get("npc") else "")
    elif d in ("fly", "hearth"):
        main = f"{Y}{VERB[d]}{R} {st.get('to', '')}"
    elif d in ("fp", "home"):
        main = f"{Y}{VERB[d]}:{R} {st.get('to', '')}" + (f" ({st['npc']})" if st.get("npc") else "")
    elif d == "level":
        main = f"{Y}Level {st['level']}{R} {st.get('text', '')}"
    elif d == "train":
        main = f"{Y}Train{R} {st.get('npc', '')}"
    else:
        main = f"{Y}{VERB[d]}:{R} {st.get('text') or st.get('name', '')}"
    extra = []
    if st.get("where"):
        extra.append(st["where"])
    if st.get("goto"):
        extra.append(f"({st['goto'][1]}, {st['goto'][2]})")
    if st.get("pick"):
        extra.append(f"reward: {st['pick']}")
    return f"- {n}. {main}" + (f" {G}· {' '.join(extra)}{R}" if extra else "")


def main(route_path, guide_path, updated, you_lines):
    route = load(route_path)
    with open(guide_path, encoding="utf-8") as f:
        g = json.load(f)
    g["route"] = route
    g["updated"] = updated
    now = g["tabs"][0]
    secs = [
        {
            "title": "How the steps work",
            "short": "How",
            "lines": [
                f"- The {Y}step window{R} (right side of the screen) shows one thing to do. "
                "It ticks itself off when you accept, finish or hand in a quest, reach the place, "
                "or arrive by flight.",
                f"- The arrow follows the current step. {Y}Done{R} skips a step, {Y}Back{R} goes back one.",
                f"- Guide quests are accepted and handed in for you, with the reward picked. "
                f"{Y}Hold Shift{R} at a quest giver to do it yourself.",
                f"- {LEAF}/dk steps{R} shows or hides the window · {LEAF}/dk auto{R} turns auto quests off or on · "
                f"{LEAF}/dk steps reset{R} starts over (finished steps skip themselves).",
            ],
        }
    ]
    n = 0
    for i, sec in enumerate(route["sections"], 1):
        lines = []
        go = None
        for st in sec["steps"]:
            n += 1
            lines.append(line(n, st))
            if go is None and st.get("goto"):
                z, x, y = st["goto"]
                go = {"zone": z, "x": x, "y": y, "label": st.get("npc") or st.get("text") or st.get("name", "")}
        s = {"title": sec["title"], "short": str(i), "lines": lines}
        if go:
            s["go"] = go
        secs.append(s)
    secs.append({"title": "You", "lines": you_lines})
    now["sections"] = secs
    with open(guide_path, "w", encoding="utf-8") as f:
        json.dump(g, f, ensure_ascii=False, indent=1)
    print(f"{n} steps in {len(route['sections'])} sections")
    errors, warnings = route_check.check(route)
    for e in errors:
        print("travel: " + e)
    if warnings:
        print(f"travel: {len(warnings)} notes; run tools/route_check.py with --home/--flights from the save")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])
