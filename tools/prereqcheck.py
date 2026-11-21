"""Usage: python3 tools/prereqcheck.py ROUTE.py DONE.json LOG_IDS(comma list)

Every accept step: its preQuestSingle / preQuestGroup must be done (state) or handed in earlier in the route."""
import sys
from pathlib import Path
PLANNER = Path(__file__).resolve().parent.parent / "planner"
sys.path.insert(0, str(PLANNER))
import json, importlib.util as u, sys
db=json.load(open(PLANNER / 'db.json'))
s=u.spec_from_file_location('r',sys.argv[1]);m=u.module_from_spec(s);s.loader.exec_module(m)
done=set(json.load(open(sys.argv[2]))) if len(sys.argv)>2 else set()
log=set(int(x) for x in sys.argv[3].split(',')) if len(sys.argv)>3 else set()
n=0; bad=0
for sec in m.ROUTE['sections']:
    for st in sec['steps']:
        n+=1; q=st.get('q')
        if st['do']=='turnin' and q: done.add(q)
        if st['do']=='accept' and q and q not in log:
            raw=db['quests'].get(str(q),{})
            single=raw.get('preQuestSingle') or []
            group=raw.get('preQuestGroup') or []
            if single and not any(p in done for p in single): print(n,'NEEDS one of',single,'before',q,st.get('name')); bad+=1
            if group and not all(p in done for p in group): print(n,'NEEDS all of',group,'before',q,st.get('name')); bad+=1
print('prereq problems:',bad)
