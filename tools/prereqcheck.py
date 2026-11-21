"""Every accept step: its preQuestSingle / preQuestGroup must be done (state) or handed in earlier in the route.

Usage: python3 tools/prereqcheck.py ROUTE.py [DONE.json] [LOG_IDS (comma list)]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_route  # noqa: E402


def check(route, done=(), log=()):
    done, problems, n = set(done), [], 0
    for sec in route["sections"]:
        for st in sec["steps"]:
            n += 1
            q = st.get("q")
            if st["do"] == "turnin" and q:
                done.add(q)
            if st["do"] == "accept" and q and q not in log:
                raw = rk.db()["quests"].get(str(q), {})
                single = raw.get("preQuestSingle") or []
                group = raw.get("preQuestGroup") or []
                if single and not any(p in done for p in single):
                    problems.append(f"{n} NEEDS one of {single} before {q} {st.get('name')}")
                if group and not all(p in done for p in group):
                    problems.append(f"{n} NEEDS all of {group} before {q} {st.get('name')}")
    return problems


def main(argv):
    done = json.loads(Path(argv[2]).read_text(encoding="utf-8")) if len(argv) > 2 else []
    log = {int(x) for x in argv[3].split(",")} if len(argv) > 3 else set()
    problems = check(load_route(argv[1]), done, log)
    for p in problems:
        print(p)
    print("prereq problems:", len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
