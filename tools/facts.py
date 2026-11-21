"""The WoW Forever facts registry (knowledge/facts.json): what we believe, where from, when checked, and which files
depend on it. forever-watch keeps it current; every other agent records the facts it relies on here.

Usage:
  python3 tools/facts.py stale [--level L] [--today YYYY-MM-DD]   facts past their review date (optionally only
                                                                 those that matter within ~5 levels of L)
  python3 tools/facts.py find WORDS...                            facts whose id, topic or statement match
  python3 tools/facts.py usedby TEXT                              facts a file or rule depends on
  python3 tools/facts.py low                                      facts still low confidence (unverified)
"""

import datetime
import json
import sys
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "knowledge" / "facts.json"


def load(path=FILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def stale(data, today=None, level=None, window=5):
    today = today or datetime.date.today()
    out = []
    for f in data["facts"]:
        due = datetime.date.fromisoformat(f["verified"]) + datetime.timedelta(days=f.get("review_days", 30))
        if due > today:
            continue
        lv = f.get("levels")
        if level is not None and lv and not (lv[0] - window <= level <= lv[1] + window):
            continue
        out.append({**f, "due": due.isoformat()})
    return sorted(out, key=lambda f: f["due"])


def find(data, words):
    w = [x.lower() for x in words]
    return [
        f for f in data["facts"] if all(x in (f["id"] + " " + f["topic"] + " " + f["statement"]).lower() for x in w)
    ]


def used_by(data, text):
    t = text.lower()
    return [f for f in data["facts"] if any(t in u.lower() for u in f.get("used_by", []))]


def low(data):
    return [f for f in data["facts"] if f.get("confidence") == "low"]


def main(argv):
    data = load()
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "stale":
        today = datetime.date.fromisoformat(argv[argv.index("--today") + 1]) if "--today" in argv else None
        level = float(argv[argv.index("--level") + 1]) if "--level" in argv else None
        rows = stale(data, today, level)
    elif cmd == "find":
        rows = find(data, argv[2:])
    elif cmd == "usedby":
        rows = used_by(data, " ".join(argv[2:]))
    elif cmd == "low":
        rows = low(data)
    else:
        print(__doc__)
        return
    for f in rows:
        print(f"{f.get('due', f['verified'])}  {f['confidence']:<6} {f['id']}: {f['statement']}")
        print(f"      used by: {', '.join(f.get('used_by', []))}")
    print(f"{len(rows)} fact(s)")


if __name__ == "__main__":
    main(sys.argv)
