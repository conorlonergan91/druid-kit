"""Walk a route and project XP and level after every step (pessimistic).

Usage: python3 tools/xpsim.py ROUTE.py LEVEL XP [--done DONE.json] [--annotate OUT.json]
(build_now.py --xp LEVEL XP DONE.json runs it and writes the projected level into every step: field lv)
- Quest XP: Questie's tables (planner/data, Forever traces over Classic) with the grey-quest cut; Forever values
  where published (rk.PUBLISHED_XP). Loader and formula live in planner/rk.py.
- Kill XP: only the kills the quest needs, Classic formula, no rested XP. Solo steps get it all; group steps
  (party=True) are split 3 ways. Boss steps (dungeon runs): 1.25% of the level bar each (about one bubble per run).
- Errors: an accept whose quest needs a higher level than projected. Warnings: a 'level' step already reached.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "planner"))
import rk  # noqa: E402
from routeio import load_route  # noqa: E402

GROUP_SPLIT = rk.GROUP_SIZE
BOSS_SHARE = 0.0125


def total_of(level, xp):
    return sum(rk.XP_TO_LEVEL[1:level]) + xp


def run(route_path, level, xp, done=()):
    done = set(done)
    route = load_route(route_path)
    total = total_of(level, xp)
    rows, errors, warns, missing = [], [], [], []
    n = 0
    for sec in route["sections"]:
        for st in sec["steps"]:
            n += 1
            lv = rk.level_of(total)
            gain, why = 0, ""
            d, q = st["do"], st.get("q")
            if q in done and d in ("accept", "turnin", "complete"):
                rows.append((n, sec["title"], d, st.get("name"), 0, "done", lv))
                continue
            f = rk.quest(q) if q else None
            if d == "accept" and f and f["min"] > int(lv):
                errors.append(f"step {n}: {st.get('name')} needs level {f['min']}, projected {lv:.2f}")
            if d == "turnin" and f:
                ql, raw = rk.quest_xp_entry(q) or (0, 0)
                why = "questie" if q in rk.load_questie_xp() else ("published" if q in rk.PUBLISHED_XP else "no data")
                if not raw:
                    missing.append(f"step {n}: {st.get('name')} ({q}) has no XP in Questie's data: counted as 0")
                gain = rk.questie_xp(raw, ql if ql > 0 else (f["level"] or int(lv)), int(lv)) if raw else 0
            elif d == "complete" and f and f["kills"]:
                gain = int(rk.kill_xp(f, int(lv), GROUP_SPLIT if st.get("party") else 1))
                why = "kills" + (" (group)" if st.get("party") else "")
            elif d == "boss":
                gain, why = int(rk.XP_TO_LEVEL[int(lv)] * BOSS_SHARE), "boss run"
            elif d == "level":
                need = total_of(st["level"], 0) - total
                if need <= 0:
                    warns.append(f"step {n}: level {st['level']} step not needed (projected {lv:.2f})")
                else:
                    gain, why = need, f"grind {need} XP"
            total += gain
            name = st.get("name") or st.get("text") or st.get("to")
            rows.append((n, sec["title"], d, name, gain, why, rk.level_of(total)))
            st["lv"] = round(rk.level_of(total), 1)
    warns.extend(missing)
    return route, rows, errors, warns


def main(argv):
    done = json.loads(Path(argv[argv.index("--done") + 1]).read_text(encoding="utf-8")) if "--done" in argv else []
    route, rows, errors, warns = run(argv[1], int(argv[2]), int(argv[3]), done)
    last = None
    for r in rows:
        if r[1] != last:
            print("##", r[1])
            last = r[1]
        if r[4]:
            print(f"  {r[0]:3d} {r[2]:8s} {str(r[3])[:42]:42s} +{r[4]:6d} {r[5]:14s} -> {r[6]:.2f}")
    if errors:
        print("ERRORS:", *errors, sep="\n  ")
    else:
        print("no level errors")
    if warns:
        print("WARN:", *warns, sep="\n  ")
    if "--annotate" in argv:
        Path(argv[argv.index("--annotate") + 1]).write_text(json.dumps(route), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv)
