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
    "boss": "Boss",
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
    elif d == "boss":
        main = f"{Y}Boss:{R} {st.get('name', '')}"
    else:
        main = f"{Y}{VERB[d]}:{R} {st.get('text') or st.get('name', '')}"
    extra = []
    if st.get("where"):
        extra.append(st["where"])
    if st.get("goto"):
        extra.append(f"({st['goto'][1]}, {st['goto'][2]})")
    if st.get("pick"):
        extra.append(f"reward: {st['pick']}")
    lv = f" {LEAF}→ {st['lv']}{R}" if st.get("lv") and d in ("turnin", "complete", "boss", "level") else ""
    return f"- {n}. {main}" + (f" {G}· {' '.join(extra)}{R}" if extra else "") + lv


def main(route_path, guide_path, updated, you_lines, xp_from=None):
    route = load(route_path)
    if xp_from:
        # RULES v18: project level after every step (pessimistic quest + kill XP) and stop on level errors
        import xpsim
        level, xp, done = xp_from
        route, rows, errors, warns = xpsim.run(route_path, level, xp, done)
        for w in warns:
            print("xp: " + w)
        if errors:
            for e in errors:
                print("xp ERROR: " + e)
            sys.exit(2)
    with open(guide_path, encoding="utf-8") as f:
        g = json.load(f)
    g["route"] = route
    items_file = Path(route_path).with_name("items.json")
    if items_file.exists():
        g["route"]["items"] = json.loads(items_file.read_text(encoding="utf-8"))
    vendors_file = Path(route_path).with_name("vendors.json")
    if vendors_file.exists():
        g["vendors"] = json.loads(vendors_file.read_text(encoding="utf-8"))
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
    args = sys.argv[1:]
    xp_from = None
    if "--xp" in args:
        i = args.index("--xp")
        level, xp, done_path = int(args[i + 1]), int(args[i + 2]), args[i + 3]
        xp_from = (level, xp, json.load(open(done_path)))
        del args[i:i + 4]
    main(args[0], args[1], args[2], args[3:], xp_from)
