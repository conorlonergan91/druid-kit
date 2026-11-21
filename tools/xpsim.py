"""Walk a route and project XP and level after every step (pessimistic).

Usage: python3 tools/xpsim.py ROUTE.py LEVEL XP [--done DONE.json]
(build_now.py --xp LEVEL XP DONE.json runs it and writes the projected level into every step: field lv)
- Quest XP: QuestieDB value (Classic) with the grey-quest cut; Forever values where known (FOREVER_XP).
- Kill XP: only the kills the quest needs, Classic formula, no rested XP. Solo steps get it all; group steps
  (party=True) are split 3 ways. Boss steps (dungeon runs): 1.25% of the level bar each (about one bubble per run).
- Errors: an accept whose quest needs a higher level than projected. Warnings: a 'level' step already reached.
"""
import sys
from pathlib import Path
PLANNER = Path(__file__).resolve().parent.parent / "planner"
sys.path.insert(0, str(PLANNER))
import importlib.util, json, sys
import rk

# Quest XP comes from Questie's own tables (planner/data/xpDB-classic.lua + xpDB-traces.lua, the traces are
# measured on Forever). These Forever dungeon quests are not traced yet: published values (method.gg, wow.gg).
PUBLISHED_XP = {95646: (31, 6150), 95772: (31, 6150), 95795: (31, 6150), 98824: (31, 6150)}
QUESTIE_XP = {}


def load_questie_xp():
    """quest id -> (quest level, xp); the Forever traces file overrides the Classic file, like Questie does."""
    import re
    if QUESTIE_XP:
        return QUESTIE_XP
    for f in ("xpDB-classic.lua", "xpDB-traces.lua"):
        path = PLANNER / "data" / f
        if path.exists():
            for m in re.finditer(r"\[(\d+)\]\s*=\s*\{(-?\d+),\s*(\d+)\}", path.read_text(encoding="utf-8")):
                QUESTIE_XP[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
    return QUESTIE_XP


def questie_xp(xp, q_level, char_level):
    """Questie's getAdjustedXP (QuestieXP.lua): full XP up to 5 levels above the quest, then -20% a level, 10% floor."""
    mult = min(10, max(1, 2 * (q_level - char_level) + 20))
    xp = xp * mult / 10
    if xp <= 100:
        xp = 5 * int((xp + 2) / 5)
    elif xp <= 500:
        xp = 10 * int((xp + 5) / 10)
    elif xp <= 1000:
        xp = 25 * int((xp + 12) / 25)
    else:
        xp = 50 * int((xp + 25) / 50)
    return int(xp)
GROUP_SPLIT = 3
BOSS_SHARE = 0.0125

def total_of(level, xp):
    return sum(rk.XP_TO_LEVEL[1:level]) + xp

def run(route_path, level, xp, done=()):
    done = set(done)
    spec = importlib.util.spec_from_file_location('r', route_path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    total = total_of(level, xp)
    rows, errors, warns, missing = [], [], [], []
    n = 0
    for sec in m.ROUTE['sections']:
        for st in sec['steps']:
            n += 1
            lv = rk.level_of(total)
            gain, why = 0, ''
            d = st['do']; q = st.get('q')
            if q in done and d in ('accept', 'turnin', 'complete'):
                rows.append((n, sec['title'], d, st.get('name'), 0, 'done', lv)); continue
            f = rk.quest(q) if q else None
            if d == 'accept' and f and f['min'] > int(lv):
                errors.append(f"step {n}: {st.get('name')} needs level {f['min']}, projected {lv:.2f}")
            if d == 'turnin' and f:
                qx = load_questie_xp()
                ql, raw = qx.get(q) or PUBLISHED_XP.get(q) or (0, 0)
                why = 'questie' if q in qx else ('published' if q in PUBLISHED_XP else 'no data')
                if not raw:
                    missing.append(f"step {n}: {st.get('name')} ({q}) has no XP in Questie's data: counted as 0")
                gain = questie_xp(raw, ql if ql > 0 else (f['level'] or int(lv)), int(lv)) if raw else 0
            elif d == 'complete' and f and f['kills']:
                k = rk.kill_xp(f, int(lv), GROUP_SPLIT if st.get('party') else 1)
                gain = int(k); why = 'kills' + (' (group)' if st.get('party') else '')
            elif d == 'boss':
                gain = int(rk.XP_TO_LEVEL[int(lv)] * BOSS_SHARE); why = 'boss run'
            elif d == 'level':
                need = total_of(st['level'], 0) - total
                if need <= 0:
                    warns.append(f"step {n}: level {st['level']} step not needed (projected {lv:.2f})")
                else:
                    gain = need; why = f'grind {need} XP'
            total += gain
            rows.append((n, sec['title'], d, st.get('name') or st.get('text') or st.get('to'), gain, why, rk.level_of(total)))
            st['lv'] = round(rk.level_of(total), 1)
    warns.extend(missing)
    return m.ROUTE, rows, errors, warns

if __name__ == '__main__':
    done = json.load(open(sys.argv[sys.argv.index('--done') + 1])) if '--done' in sys.argv else []
    route, rows, errors, warns = run(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), done)
    last = None
    for r in rows:
        if r[1] != last: print('##', r[1]); last = r[1]
        if r[4]: print(f"  {r[0]:3d} {r[2]:8s} {str(r[3])[:42]:42s} +{r[4]:6d} {r[5]:14s} -> {r[6]:.2f}")
    print('ERRORS:', *errors, sep='\n  ') if errors else print('no level errors')
    print('WARN:', *warns, sep='\n  ') if warns else None
    if '--annotate' in sys.argv:
        json.dump(route, open(sys.argv[sys.argv.index('--annotate') + 1], 'w'))
